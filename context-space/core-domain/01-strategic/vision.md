---
type: Vision
title: "Jarvisje — kernbelofte"
description: "Chatbot rondom de wereld van AI, grounded in twee blogs."
tags: [jarvisje, rag, blogs]
timestamp: 2026-09-13T00:00:00Z
traces_to:
  - /core-domain/01-strategic/domein-scope.md
  - /core-domain/01-strategic/succescriteria.md
---

# Vision

## Doel

Jarvisje is een **chatbot rondom de wereld van AI**. Hij voert een gesprek over de artikelen op [edwinvandillen.nl](https://edwinvandillen.nl/) en [jeroenteunisse.nl](https://jeroenteunisse.nl/) en verwijst altijd naar concrete posts.

**Kernbelofte:**

> Je kunt een natuurlijk gesprek voeren over AI, software-engineering en de ideeën in deze twee blogs, en Jarvisje wijst je naar de artikelen zelf.

Geen algemene assistent, geen Sogyo-traineeship-gids, geen zes-sites-index. Wel: grounded antwoorden met citations, ingebed in de look & feel van edwinvandillen.nl.

## Doelgroepen

- **Primair:** lezers van edwinvandillen.nl (en later dezelfde iframe op andere eigen sites).
- **Secundair:** bezoekers die via jarvisje.com de standalone chat openen.

Geen aparte persona-modes (sollicitant vs bedrijf).

## Strategische doelen

- De blogs actief ontsluiten via gesprek + verplichte [citations](/core-domain/03-technical/ubiquitous-language.md).
- Visueel één geheel met *Edwin Blog* (dark en light).
- Compact iframe in een gereserveerde WordPress-regio; beheer op jarvisje.com.
- Gematigde [guardrails](/core-domain/03-technical/ubiquitous-language.md) binnen het onderwerp van de twee bronnen.
- Draait lokaal op de productiehost (zie [ADR-009](/core-domain/02-architectural/decisions/09-ADR-image-compose-deployment.md), [ADR-012](/core-domain/02-architectural/decisions/12-ADR-jarvisje-rebrand.md)).

Zie [software-design.md](/core-domain/02-architectural/software-design.md) voor architectuur.
