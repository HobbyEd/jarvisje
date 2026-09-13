---
type: Success Criteria
title: "Definition of Done — Jarvisje"
description: "Meetbare en kwalitatieve succescriteria."
tags: [quality, jarvisje]
timestamp: 2026-09-13T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
  - /core-domain/04-delivery/roadmap.md
  - /core-domain/02-architectural/decisions/12-ADR-jarvisje-rebrand.md
---

# Succescriteria (Definition of Done)

## Functioneel

Klaar als:

1. Werkende chat (standalone + embed-iframe).
2. Binnen-domein: relevante antwoorden + concrete [citations](/core-domain/03-technical/ubiquitous-language.md) naar edwinvandillen.nl of jeroenteunisse.nl.
3. Buiten-domein: beleefde weigering of redirect.
4. Geen antwoorden grounded in sogyo.nl of andere geschrapte bronnen.
5. Dark én light mode volgens *Edwin Blog*; embed volgt het parent-thema.
6. Nieuwe content handmatig toevoegbaar via [ingestion](/core-domain/04-delivery/use-cases/bronnen-indexeren.md) (reset na bronwijziging).
7. Stack op `.15` (app + Ollama + data), publiek via jarvisje.com.

## Niet-functioneel

- Elke bewering: minstens één concrete bron met link op een toegestaan host.
- Responstijd acceptabel op `.15` (geen harde SLA).
- Geen Sogyo-productreferenties in UI, prompts, package of infra-namen (na cutover).

## Kwalitatief

- Voelt als de blogs, niet als generieke AI.
- Ondertitel is een knipoog, geen Iron Man-cosplay in de antwoorden.

## Development guardrails

Tijdens de bouw valideert de [Software Designer Agent](/core-domain/03-technical/aannames.md) ADR-compliance en complexiteit; findings in [harnessing/](/harnessing/).
