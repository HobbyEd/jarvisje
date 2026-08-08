---
type: ADR
title: "Citations en grounding"
description: "Verplichte bronverwijzingen in antwoorden."
status: accepted
tags: [citations, grounding]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-008: Citations and Grounding Requirements

## Status
Accepted

## Datum
2026-06-26 · reality check 2026-08-08: nog geldig (Pydantic ChatResponse + citations in UI).

## Context
Een van de belangrijkste doelen is dat de chatbot **actief verwijst naar blogposts en tools**.

Zonder sterke citations wordt het een generieke chatbot in plaats van een gids naar de bestaande content.

## Decision
**Citations zijn verplicht** en worden structureel afgedwongen.

### Regels
1. Elk antwoord dat een bewering doet, moet ten minste één concrete bron noemen met een directe link.
2. De bronnen moeten uit de retrieved context komen (retrieval-only).
3. Citations worden gestructureerd teruggegeven (niet alleen in de lopende tekst, maar ook als aparte lijst of metadata).
4. De frontend toont de citations duidelijk (bij voorkeur met titel + URL).

### Technische aanpak
- Chunks in de vector DB bevatten rijke metadata:
  - `url`
  - `title`
  - `section` of `heading`
  - `type` (blogpost, tool, canvas, stelling, vish, etc.)
- Het LLM krijgt instructies + few-shot voorbeelden om te citeren in de vorm:
  > Volgens ["Harnessing: de ingenieursdiscipline die AI-engineering betrouwbaar maakt"](https://edwinvandillen.nl/?p=398)...
- We gebruiken **structured output** (Pydantic model of JSON mode) zodat de backend de citations betrouwbaar kan parsen en valideren.
- Optioneel: Post-validator controleert of er citations aanwezig zijn.

## Consequences
### Positief
- Verhoogt vertrouwen in de antwoorden.
- Drijft verkeer naar de blogs en tools.
- Maakt evaluatie eenvoudiger ("citeerde het de juiste bronnen?").

### Negatief / Risico's
- Kan antwoorden iets formeler of "geciteerder" maken.
- Als retrieval zwak is, kan de chatbot te vaak "Ik weet het niet, zie deze bron" zeggen.

## Alternatives Considered
- **Citations optioneel / alleen in voetnoot**: Verworpen — te zwak voor het doel.
- **Alleen linkjes genereren zonder grounding**: Risico op verkeerde of verzonnen links.

## Implementation Notes
- Definieer een `Citation` Pydantic model.
- Maak de response structuur:
  ```json
  {
    "answer": "...",
    "citations": [
      {"title": "...", "url": "...", "section": "..."}
    ]
  }
  ```
- Test expliciet of citations correct en relevant zijn in de evaluatieset.

## Gerelateerde ADRs
- ADR-001: Knowledge Strategy
- ADR-002: Guardrails

## Besloten door
Edwin + architectuur sessie met Grok
