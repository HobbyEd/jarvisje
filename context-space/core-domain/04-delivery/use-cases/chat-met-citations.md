---
type: Use Case
title: "Chat met citations en hints"
description: "Kerngebruik: vraag stellen, grounded antwoord met bronnen en vervolgsuggesties."
tags: [chat, rag]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
  - /core-domain/01-strategic/succescriteria.md
---

# Use case: Chat met citations

## Actor

Sollicitant of bedrijf (na optionele [onboarding](onboarding-flow.md)).

## Trigger

Gebruiker stuurt een bericht in de chat.

## Hoofdflow

1. Backend ontvangt bericht + gespreksgeschiedenis (client-side state in MVP).
2. [Retrieval](/core-domain/03-technical/ubiquitous-language.md) haalt relevante chunks.
3. LLM genereert structured output: `answer`, `citations`, `suggested_hints`.
4. Antwoord streamt via SSE naar UI.
5. UI toont citations onder het antwoord en hints als suggesties.

## Guardrails

- In-domein: antwoord met minstens één [citation](/core-domain/03-technical/ubiquitous-language.md) bij beweringen.
- Out-of-domein: beleefde weigering ([ADR-002](/core-domain/02-architectural/decisions/02-ADR-guardrails.md)).
- Grijs gebied: antwoord toegestaan mits link naar bronnen/principes.

## Acceptatie

- Streaming zichtbaar in UI
- Citations bevatten werkende URLs
- Multi-turn: geschiedenis wordt meegestuurd

## Stretch: sessie-consent

Bij lastige gesprekken mag chatbot toestemming vragen om sessie te delen ([ADR-006](/core-domain/02-architectural/decisions/06-ADR-conversation-management.md)).