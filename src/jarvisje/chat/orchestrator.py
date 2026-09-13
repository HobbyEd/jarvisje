"""Chat orchestrator that combines retrieval + prompt + LLM call + structured output."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any

from pydantic import ValidationError

from ..config import settings
from ..ingestion.status import read_status
from ..retrieval.retriever import retrieve
from .models import ChatResponse
from .prompts import build_system_prompt, build_user_prompt

INGEST_INCOMPLETE_NOTE = (
    "De kennisindex wordt nu opnieuw opgebouwd. Antwoorden kunnen daardoor "
    "onvolledig zijn tot de indexering klaar is."
)
INGEST_EMPTY_ANSWER = (
    "De kennisindex wordt nu opnieuw opgebouwd, dus ik heb nog te weinig artikelen "
    "om op te steunen. Probeer het zo dadelijk opnieuw — tot de indexering klaar is "
    "zijn antwoorden onvolledig."
)
EMPTY_INDEX_ANSWER = (
    "Ik heb nog geen geïndexeerde artikelen. Start indexering onder Bronnen, "
    "of wacht tot die klaar is."
)

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class ChatTurn:
    role: str
    content: str


@dataclass
class ChatSession:
    turns: List[ChatTurn] = field(default_factory=list)
    role: str = "onbekend"


class ChatOrchestrator:
    def __init__(self):
        self.session = ChatSession()

    def _filter_citations(self, response: ChatResponse) -> ChatResponse:
        kept = [c for c in response.citations if settings.is_allowed_url(c.url)]
        response.citations = kept
        return response

    def _call_llm(self, system: str, user: str) -> str:
        """Call the OpenAI-compatible vLLM endpoint and return raw content."""
        if httpx is None:
            raise RuntimeError("httpx is required for LLM calls. Please install requirements.")

        url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_tokens,
            "response_format": {"type": "json_object"},  # many modern models support this
        }

        logger.info(f"Calling LLM at {url} with model={settings.llm_model}")
        logger.debug(f"Payload system: {system[:200]}...")
        logger.debug(f"Payload user: {user[:200]}...")

        try:
            with httpx.Client(timeout=settings.llm_timeout) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to call LLM: {e}")
            raise RuntimeError(f"LLM call failed (endpoint not reachable or error): {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error calling LLM: {e}")
            raise RuntimeError(f"LLM call failed: {str(e)}") from e

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.warning(f"LLM did not return expected JSON structure: {data}")
            # Return raw so fallback can handle
            return json.dumps(data) if isinstance(data, dict) else str(data)

    def chat(self, user_message: str, history: List[Dict[str, str]] | None = None) -> ChatResponse:
        """
        Main entry. Returns structured ChatResponse.
        If history is provided, it overrides internal session for this turn.
        """
        role_context = "De gebruiker is een lezer van edwinvandillen.nl of jeroenteunisse.nl."

        ingest_running = False
        try:
            ingest_running = read_status().get("status") == "running"
        except Exception:
            ingest_running = False

        try:
            retrieved = retrieve(user_message, top_k=6)
        except Exception as e:
            logger.warning("Retrieval failed (index may be rebuilding): %s", e)
            retrieved = []

        if not retrieved:
            answer = INGEST_EMPTY_ANSWER if ingest_running else EMPTY_INDEX_ANSWER
            response = ChatResponse(
                answer=answer,
                citations=[],
                hints=["Probeer het zo dadelijk opnieuw"] if ingest_running else [
                    "Open het tabblad Bronnen om te indexeren"
                ],
                role_context="onbekend",
            )
            self.session.turns.append(ChatTurn(role="user", content=user_message))
            self.session.turns.append(ChatTurn(role="assistant", content=response.answer))
            return response

        # Build prompts
        system = build_system_prompt(role_context, retrieved)
        effective_history = history or [{"role": t.role, "content": t.content} for t in self.session.turns]
        user_prompt = build_user_prompt(effective_history, user_message)

        # Call LLM
        raw = self._call_llm(system, user_prompt)

        # Parse structured output
        try:
            data = json.loads(raw)
            response = ChatResponse(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Failed to parse structured output from LLM: {e}")
            # Fallback: wrap the raw answer
            response = ChatResponse(
                answer=raw[:2000] if isinstance(raw, str) else str(raw),
                citations=[],
                hints=[
                    "Welk artikel op edwinvandillen.nl sluit hierbij aan?",
                    "Hoe beschrijft Jeroen Teunisse dit?",
                ],
                role_context="onbekend",
            )

        response = self._filter_citations(response)

        if ingest_running:
            response.answer = INGEST_INCOMPLETE_NOTE + "\n\n" + response.answer

        # Update internal history
        self.session.turns.append(ChatTurn(role="user", content=user_message))
        self.session.turns.append(ChatTurn(role="assistant", content=response.answer))

        response.role_context = "onbekend"  # type: ignore

        return response
