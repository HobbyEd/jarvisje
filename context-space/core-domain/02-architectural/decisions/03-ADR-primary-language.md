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
Accepted

## Datum
2026-06-26

## Context
De website sogyo.nl is Nederlandstalig. De content op de gekoppelde blogs (jeroenteunisse.nl, edwinvandillen.nl, augmentedorganisation.nl, etc.) is grotendeels of volledig in het Nederlands geschreven.

De primaire gebruikers (sollicitanten en Nederlandse bedrijven) verwachten een Nederlandstalige ervaring.

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
