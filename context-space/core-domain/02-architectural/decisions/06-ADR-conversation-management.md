---
type: ADR
title: "Conversatiebeheer"
description: "Client-side history; onboarding; consent stretch."
status: accepted
tags: [conversation]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-006: Conversation Management for Extended Sessions

## Status
Accepted

## Datum
2026-06-26

## Context
User-specificatie:
- "Dat mag best lang duren dus een uitgebreide chat sessie worden."

Gesprekken kunnen meerdere turns duren. Gebruikers (vooral bedrijven of geïnteresseerde sollicitanten) willen dieper ingaan op onderwerpen, canvases bespreken, of meerdere gerelateerde vragen stellen.

Tegelijkertijd:
- We willen guardrails behouden.
- We willen sterke citations blijven afdwingen.
- We willen geen onbeperkte context kosten / latency.

## Decision
We ondersteunen **uitgebreide chat-sessies** met de volgende aanpak:

1. **Volledige history** wordt meegestuurd zolang het binnen de context window past.
2. **Context compression / summarization** wordt toegepast wanneer de geschiedenis te lang wordt:
   - Samenvatting van eerdere delen van het gesprek (door het model zelf of een kleiner model).
   - Belangrijke feiten en intenties uit de geschiedenis worden geëxtraheerd.
3. **Session state** wordt beheerd in de backend (in-memory voor dev, later Redis of database).
4. **Per bericht** wordt de relevante retrieved context meegestuurd (niet alleen de history).
5. **Optioneel**: Gebruikers kunnen een "nieuw gesprek" starten of een onderwerp resetten.

De backend houdt een `conversation_id` bij met bijbehorende berichten.

## Consequences
### Positief
- Natuurlijke, diepe gesprekken zijn mogelijk.
- Past bij de aard van de content (diepgaande onderwerpen).
- Goede user experience.

### Negatief / Risico's
- Hogere token kosten / latency bij lange sessies.
- Risico dat de LLM de oorspronkelijke retrieval context "vergeet" en buiten de bronnen gaat zweven (tegen te gaan met goede prompting + citations).
- Complexere state management.

## Alternatives Considered
- **Alleen stateless per vraag**: Verworpen — past niet bij "uitgebreide chat sessie".
- **Volledige history zonder limiet**: Niet realistisch (context window + kosten).
- **Agent-style memory (langetermijn)**: Te complex voor v1. Wordt later overwogen.

## Implementation Notes
- Gebruik Pydantic modellen voor messages.
- Bouw een `ConversationManager` class.
- Voeg een samenvattingsmechanisme toe wanneer `len(history) > N` (bijv. 15-20 berichten).
- Test expliciet lange sessies in de evaluatieset.

## Gerelateerde ADRs
- ADR-002: Guardrails
- ADR-008: Citations and Grounding

## Besloten door
Edwin + architectuur sessie met Grok
