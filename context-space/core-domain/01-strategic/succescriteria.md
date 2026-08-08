---
type: Success Criteria
title: "MVP Definition of Done"
description: "Meetbare en kwalitatieve succescriteria voor de MVP."
tags: [mvp, quality]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
  - /core-domain/04-delivery/roadmap.md
---

# Succescriteria (Definition of Done)

## Functioneel

De MVP is klaar als:

1. Er is een werkende chat interface waarmee je kunt praten.
2. Bij vragen binnen het domein: relevante antwoorden + concrete [citations](/core-domain/03-technical/ubiquitous-language.md) met links.
3. Bij duidelijk buiten-domein vragen: beleefde weigering of redirect.
4. Evaluatieset van minimaal 20–30 vragen (in-domein, grijs, out-of-domein) meet:
   - % antwoorden in domein
   - % antwoorden met correcte citations
5. End-to-end stack op DGX of lokale dev-omgeving.
6. Nieuwe content handmatig toevoegbaar via [ingestion](/core-domain/04-delivery/use-cases/bronnen-indexeren.md).

## Niet-functioneel

- Elke bewering in een antwoord: minstens één concrete bron met link.
- Herkenbaar in het Sogyo-domein bij de meeste vragen.
- Redelijke responstijd op DGX (geen harde SLA).
- DGX-centric zonder externe hosting-afhankelijkheid.

## Kwalitatief

- Voelt als "onze content", niet generieke AI.
- Bekenden van de content herkennen filosofie en verwijzingen.

## Development guardrails (bouwfase)

Tijdens de bouw valideert de [Software Designer Agent](/core-domain/03-technical/aannames.md) ADR-compliance en complexiteit; findings in [harnessing/](/harnessing/).