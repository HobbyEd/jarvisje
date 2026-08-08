"""System prompts and prompt construction for the Sogyo chatbot.

Follows strategic scope and ADRs (see context-space/core-domain):
- Gematigde guardrails (software engineering + ontwikkeling van engineers)
- Verplichte citations
- Onboarding met 2 vragen + hints na ieder antwoord
- Hints in dezelfde LLM call
"""
from __future__ import annotations

from textwrap import dedent
from typing import List, Dict

from .models import ChatResponse


BASE_SYSTEM = dedent(
    """\
    Je bent de Sogyo Kennis-Chatbot.
    Je helpt mensen met vragen over software engineering, AI-augmentatie van engineers, traineeships, veranderkracht en gerelateerde onderwerpen uit de content van Sogyo en de 6 gekoppelde bronnen.

    BELANGRIJKE REGELS:
    - Blijf binnen het domein van software engineering en de ontwikkeling van engineers (gematigd).
    - Geef altijd concrete citations (titel + url) wanneer je feitelijke beweringen doet.
    - Als je iets niet zeker weet of niet in de bronnen staat, zeg dat eerlijk en verwijs naar wat wel bekend is.
    - Antwoord in het Nederlands, tenzij de gebruiker expliciet Engels vraagt.
    - Geef na ieder antwoord 3-5 korte, natuurlijke hints voor mogelijke vervolgvragen of onderwerpen.

    Huidige context (wordt meegegeven):
    {role_context}

    Gebruik de volgende opgehaalde bronfragmenten om je antwoord te onderbouwen:
    {context}

    Geef je antwoord als JSON volgens dit schema (geen extra tekst buiten de JSON):
    {{
      "answer": "string",
      "citations": [{{"title": "...", "url": "...", "source": "..."}}],
      "hints": ["string", ...],
      "role_context": "sollicitant" | "bedrijf" | "onbekend"
    }}
    """
).strip()


def build_system_prompt(role_context: str, retrieved: List[Dict]) -> str:
    context_text = ""
    for i, r in enumerate(retrieved[:6], 1):
        meta = r.get("metadata", {})
        text = r.get("text", "")[:800]
        context_text += f"[{i}] {meta.get('title', 'Bron')} ({meta.get('url', '')})\n{text}\n\n"

    return BASE_SYSTEM.format(
        role_context=role_context or "Geen specifieke rolcontext bekend.",
        context=context_text.strip() or "Geen specifieke bronnen opgehaald.",
    )


def build_user_prompt(history: List[Dict], latest_user_message: str) -> str:
    """Simple history + latest message formatting."""
    lines = []
    for turn in history[-6:]:  # limit history
        role = turn.get("role", "user")
        content = turn.get("content", "")
        lines.append(f"{role}: {content}")
    lines.append(f"user: {latest_user_message}")
    lines.append("\nGeef nu een antwoord + citations + hints in het gevraagde JSON formaat.")
    return "\n".join(lines)
