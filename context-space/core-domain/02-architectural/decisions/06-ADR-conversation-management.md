---
type: ADR
title: "Conversatiebeheer"
description: "Client-side + server session history; geen zware memory-stack."
status: accepted
tags: [conversation]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-006: Conversation Management for Extended Sessions

## Status
Accepted (geactualiseerd 2026-08-08)

## Datum
2026-06-26 · update 2026-08-08

## Context
Gesprekken mogen meerdere turns duren. Guardrails en citations moeten blijven gelden zonder onbeperkte contextkosten.

## Decision
We ondersteunen **multi-turn chat** met:

1. **History** meegestuurd vanuit client en/of server-sessie (session_id).
2. **Retrieval per turn** — relevante chunks worden opnieuw opgehaald (niet alleen history).
3. **In-memory session map** in de FastAPI-proces voor MVP (geen Redis vereist).
4. Optioneel later: summarization bij zeer lange history, of externe session store.

### Niet in scope (MVP)
- Langetermijn memory over bezoekers
- Agent-style tools memory

## Reality check (2026-08)

| Besluit | Werkelijkheid |
|---------|----------------|
| Multi-turn + session_id | ✅ in API/UI |
| History in request | ✅ optioneel |
| In-memory sessions | ✅ `app.py` |
| Automatische summarization bij N turns | ❌ nog niet |
| Redis/DB sessions | ❌ nog niet |

## Consequences
### Positief
- Voldoende voor demo en productie-MVP.
- Eenvoudig en lightweight.

### Negatief
- Sessions verdwijnen bij container restart.
- Zeer lange chats kunnen context vullen zonder compressie.

## Alternatives Considered
- Alleen stateless per vraag: te mager voor “uitgebreide chat”.
- Volledige unlimited history: niet realistisch.

## Gerelateerde ADRs
- ADR-002 Guardrails
- ADR-008 Citations

## Besloten door
Edwin + architectuur sessie met Grok
