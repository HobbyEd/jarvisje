---
type: Use Case
title: "Welkomstflow"
description: "Korte begroeting bij start van het gesprek; geen rolvragen."
tags: [ux, welkom]
timestamp: 2026-09-13T00:00:00Z
traces_to:
  - /core-domain/01-strategic/domein-scope.md
  - /core-domain/02-architectural/decisions/06-ADR-conversation-management.md
  - /core-domain/02-architectural/decisions/12-ADR-jarvisje-rebrand.md
---

# Use case: Welkomstflow

## Actor

Lezer (via standalone chat of iframe op edwinvandillen.nl).

## Trigger

Gebruiker opent de chat voor het eerst in een sessie.

## Flow

1. Jarvisje heet welkom (geen sollicitant/bedrijf-vraag).
2. Gebruiker stelt een vraag of kiest een hint.
3. Na elk antwoord: 3–5 [hints](/core-domain/03-technical/ubiquitous-language.md).
4. Normaal gesprek ([chat-met-citations](chat-met-citations.md)).

Welkomstzin (richting):

> Hallo, ik ben Jarvisje — een chatbot rondom de wereld van AI, met een knipoog naar Jarvis. Ik ken de artikelen op edwinvandillen.nl en jeroenteunisse.nl. Waar wil je het over hebben?

## Acceptatie

- Geen rol-onboarding
- Hints na elk assistant-antwoord (zelfde LLM-call als antwoord)
- Embed en standalone delen dezelfde welkomsttoon; embed toont geen beheer-tabs

## Gerelateerde beslissingen

[ADR-006](/core-domain/02-architectural/decisions/06-ADR-conversation-management.md), [ADR-012](/core-domain/02-architectural/decisions/12-ADR-jarvisje-rebrand.md).
