"""Chat orchestrator that combines retrieval + prompt + LLM call + structured output."""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any

from pydantic import ValidationError

from ..config import settings
from ..ingestion.status import read_status
from ..retrieval.retriever import nearest_hit, retrieve
from .citations import align_answer_citations
from .models import ChatResponse
from .prompts import build_system_prompt, build_user_prompt
from .source_fit import assess_source_fit, best_distance

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

    def _parse_llm_response(self, raw: str) -> ChatResponse:
        """Parse model JSON; never show raw JSON as the chat answer."""
        data = _extract_json_object(raw)
        if data:
            hints = data.get("hints") or []
            if isinstance(hints, str):
                hints = [hints]
            data["hints"] = [str(h) for h in hints][:5]
            try:
                return ChatResponse(**data)
            except ValidationError as e:
                logger.warning("LLM JSON failed schema: %s", e)
                answer = str(data.get("answer") or "").strip()
                if answer:
                    return ChatResponse(
                        answer=answer[:4000],
                        citations=[],
                        hints=data["hints"],
                        role_context="onbekend",
                    )
        logger.warning("LLM output was not usable JSON")
        return ChatResponse(
            answer="Ik kon het antwoord niet goed formatteren. Stel de vraag gerust opnieuw.",
            citations=[],
            hints=[
                "Welk artikel op edwinvandillen.nl sluit hierbij aan?",
                "Hoe beschrijft Jeroen Teunisse dit?",
            ],
            role_context="onbekend",
        )

    def _call_llm(self, system: str, user: str) -> str:
        """Call the OpenAI-compatible LLM endpoint and return raw content."""
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

        raw = self._call_llm(system, user_prompt)
        response = self._parse_llm_response(raw)

        response.answer, response.citations = align_answer_citations(
            response.answer, response.citations, retrieved
        )
        response.source_fit = _source_fit(response, retrieved)

        if ingest_running:
            response.answer = INGEST_INCOMPLETE_NOTE + "\n\n" + response.answer

        # Update internal history
        self.session.turns.append(ChatTurn(role="user", content=user_message))
        self.session.turns.append(ChatTurn(role="assistant", content=response.answer))

        response.role_context = "onbekend"

        return response


def _source_fit(response: ChatResponse, retrieved: List[Dict[str, Any]]):
    question_distance = best_distance([hit.get("distance") for hit in retrieved])
    answer_distance = None
    nearest_title = None
    try:
        answer_distance, nearest_title = nearest_hit(response.answer)
    except Exception as exc:
        logger.warning("Bronpassing van het antwoord lukte niet: %s", exc)
    return assess_source_fit(
        question_distance=question_distance,
        answer_distance=answer_distance,
        source_count=len(response.citations),
        nearest_title=nearest_title,
    )


def _extract_json_object(raw: str) -> dict | None:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    blobs = [text]
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        blobs.append(text[start : end + 1])
    for blob in blobs:
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                continue
        if isinstance(data, dict) and "answer" in data:
            return data
    return None
