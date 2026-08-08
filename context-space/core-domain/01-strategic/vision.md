---
type: Vision
title: "Sogyo Kennis-Chatbot — kernbelofte"
description: "Domein-specifieke grounded chatbot die actief verwijst naar Sogyo-content."
tags: [mvp, sogyo, rag]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/domein-scope.md
  - /core-domain/01-strategic/succescriteria.md
---

# Vision

## Doel van de MVP

De MVP is de **kleinste versie** van de chatbot die al echte waarde levert voor de twee doelgroepen en de kernbelofte waarmaakt: een gesprek voeren binnen het Sogyo-domein met actieve verwijzingen naar de bestaande content.

**Kernbelofte MVP:**

> Je kunt een natuurlijk gesprek voeren over software engineering, AI-augmentatie van engineers en gerelateerde onderwerpen uit onze content, en de chatbot verwijst je altijd naar concrete blogposts en tools.

De MVP dient als **proof of concept** en als basis om verder te itereren op kwaliteit, guardrails en UX.

## Doelgroepen

- **Primair**: Sollicitanten (starters die overwegen het traineeship te volgen of meer willen weten over de filosofie).
- **Secundair**: Bedrijven (die interesse hebben in talentontwikkeling, AI-adoptie of hoe Sogyo engineers werken).

Voor de MVP hoeven we nog geen sterk verschillende persona's of modes te hebben, maar de antwoorden moeten nuttig zijn voor beide.

## Strategische doelen

- Bewijzen dat een domein-specifieke, grounded chatbot rond onze content mogelijk is.
- Actief doorverwijzen naar de blogs en tools ([citations](/core-domain/03-technical/ubiquitous-language.md) zijn verplicht).
- Goed genoeg [guardrails](/core-domain/03-technical/ubiquitous-language.md) zodat het gesprek niet alle kanten op gaat.
- Werkend op de DGX in een lokale / tijdelijke setup (per [ADR-005](/core-domain/02-architectural/decisions/05-ADR-temporary-deployment.md)).
- Meetbaar via een evaluatieset.

Zie ook [software-design.md](/core-domain/02-architectural/software-design.md) voor de bredere productvisie.