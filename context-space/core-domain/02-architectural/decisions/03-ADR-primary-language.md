---
type: ADR
title: "Primair Nederlands"
description: "Nederlandse taal als default."
status: accepted
tags: [language, nl]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-003: Primary Language - Nederlands

## Status
Accepted — Nederlands blijft default. Voorbeelden/doelgroep in de context hieronder zijn historisch; actueel kader: [ADR-012](12-ADR-jarvisje-rebrand.md).

## Datum
2026-06-26 · reality check 2026-08-08: UI/prompts NL; gemma3:4b · 2026-09-13: bronnen zijn de twee Nederlandstalige blogs.

## Context
De blogs edwinvandillen.nl en jeroenteunisse.nl zijn Nederlandstalig (historisch gold dat ook voor sogyo.nl en de framework-sites). Lezers verwachten een Nederlandstalige ervaring.

## Decision
De chatbot communiceert **hoofdzakelijk in het Nederlands**.

Engels mag ondersteund worden in beperkte mate (bijvoorbeeld als een gebruiker expliciet in het Engels vraagt), maar is geen primaire focus.

## Consequences
### Positief
- Past bij de bestaande content en doelgroep.
- Verhoogt geloofwaardigheid en relevantie.
- Maakt betere verwijzingen mogelijk (bronnen zijn in het Nederlands).

### Negatief / Risico's
- Minder sterke modellen voor Nederlands dan voor Engels (hoewel moderne open modellen dit steeds beter doen).
- Testen van kwaliteit moet expliciet op Nederlands gebeuren.

## Alternatives Considered
- Tweetalig (NL + EN) als primaire ervaring: Verworpen omdat het de focus en complexiteit vergroot zonder duidelijke business value.
- Alleen Engels: Past niet bij de doelgroep en content.

## Implementation Notes
- Kies embeddings en LLM die redelijk tot goed Nederlands beheersen (Gemma, Llama-3.1/4, Qwen2.5, Mistral, Command-R, etc. zijn kandidaten).
- In de evaluatieset expliciet Nederlandse testvragen opnemen.
- System prompt expliciet in het Nederlands.

## Gerelateerde ADRs
- ADR-004: Inference Serving

## Besloten door
Edwin + architectuur sessie met Grok
