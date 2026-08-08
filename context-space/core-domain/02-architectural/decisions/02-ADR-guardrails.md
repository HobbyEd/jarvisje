---
type: ADR
title: "Guardrails — gematigd domein"
description: "Gematigde guardrails binnen software engineering."
status: accepted
tags: [guardrails]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-002: Guardrails Approach (Gematigd)

## Status
Accepted

## Datum
2026-06-26

## Context
De chatbot moet een natuurlijk gesprek mogelijk maken, maar mag **niet alle kanten op gaan**.

User-specificatie:
- "Gematigd, alles wat met software engineering en engineers te maken heeft, maar alles wat daar ver buiten ligt moet uitgesloten worden."
- Hoofdzakelijk Nederlands.
- Twee doelgroepen: sollicitanten en bedrijven.
- Sterk verwijzen naar de content.

Het domein is breed genoeg voor interessante gesprekken (intent-driven engineering, harnessing, veranderkracht, IT-landschap, AI-adoptie in engineering teams), maar moet wel begrensd blijven.

## Decision
We implementeren een **gelaagde, gematigde guardrail-strategie**:

1. **Pre-filter (snel)**: Eenvoudige classificatie (klein model of embedding similarity) of keyword + intent check om duidelijk off-topic vragen vroeg te weigeren.
2. **Retrieval-only policy**: Het LLM krijgt alleen antwoorden op basis van retrieved context uit de kennisbank. "Als het niet in de bronnen staat, zeg dat je het niet weet en verwijs door."
3. **Strict system prompt + few-shot**: Duidelijke definitie van in-domein vs out-of-domein met voorbeelden.
4. **Citation forcing**: Antwoorden moeten altijd concrete bronnen noemen met links.
5. **Optionele post-validator**: Tweede LLM-call (kleiner model) die controleert of het antwoord in-domein blijft en goed citeert.
6. **UX steering**: Na een antwoord altijd 2-3 suggesties geven die terugleiden naar de content.

### Definitie van het domein (in-domein)
- Software engineering craft en vakmanschap
- Ontwikkelen van engineers (traineeship, rollen, adoptie)
- AI-augmentatie van engineers en engineering processen (Harnessing, Intent-Driven, etc.)
- IT-landschap, bounded contexts, sourcing
- Veranderkracht in de context van software engineering teams
- Kennis-elicitatie, requirements, specificatie
- AI governance, maturity en adoptie specifiek binnen software engineering organisaties
- De tools en modellen van augmentedorganisation.nl, intentdriven.nl, etc.

### Buiten domein (uitgesloten)
- Algemene programmeerhulp / "schrijf code voor mij"
- Algemene AI-adviezen over modellen die niet gerelateerd zijn aan het eigen werk
- Persoonlijke loopbaanadvies buiten de Sogyo-filosofie
- Politiek, maatschappij, ethiek in brede zin
- Medische, juridische of financiële adviezen
- Alles wat duidelijk buiten software engineering en engineer-ontwikkeling valt

## Consequences
### Positief
- Maakt natuurlijke, nuttige gesprekken mogelijk binnen het relevante domein.
- Voorkomt dat de chatbot een "generieke AI" wordt.
- Houdt focus op het promoten van de eigen content.

### Negatief / Risico's
- Er zal altijd een grijs gebied zijn (bijv. "hoe gebruik ik AI voor requirements in mijn project?").
- Over-strenge guardrails kunnen frustrerend zijn voor gebruikers.
- Onderhoud van de domein-definitie is nodig bij nieuwe content.

## Alternatives Considered
- **Zeer strikt** (alleen letterlijk uit de bronnen antwoorden): Te beperkt voor een goed gesprek.
- **Alleen prompting**: Te zwak voor betrouwbare guardrails.
- **Externe guardrail service** (NVIDIA NeMo Guardrails of Llama Guard): Overwogen, maar starten we met eigen gelaagde aanpak om volledige controle te houden.

## Implementation Notes
- De domein-definitie wordt expliciet gedocumenteerd in de system prompt en in een apart "domain-scope.md".
- We bouwen een kleine evaluatieset met "in-domein", "grijs gebied" en "out-of-domein" voorbeelden.

## Gerelateerde ADRs
- ADR-001: Knowledge Strategy
- ADR-008: Citations and Grounding

## Besloten door
Edwin + architectuur sessie met Grok
