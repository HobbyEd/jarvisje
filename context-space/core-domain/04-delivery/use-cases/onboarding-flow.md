---
type: Use Case
title: "Onboarding flow"
description: "Welkom + rolbepaling + interessegebied aan start van gesprek."
tags: [ux, onboarding]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/domein-scope.md
  - /core-domain/02-architectural/decisions/06-ADR-conversation-management.md
---

# Use case: Onboarding flow

## Actor

Sollicitant of bedrijfsvertegenwoordiger (via chat-UI).

## Trigger

Gebruiker opent de chat voor het eerst in een sessie.

## Flow

1. Chatbot heet welkom.
2. **Vraag 1:** Ben je sollicitant/student of kom je vanuit een bedrijf?
3. **Vraag 2:** Waar wil je het vandaag vooral over hebben?
4. Na elk antwoord: 3–5 [hints](/core-domain/03-technical/ubiquitous-language.md) voor vervolgonderwerpen.
5. Normaal gesprek start ([chat-met-citations](chat-met-citations.md)).

## Acceptatie

- Twee onboarding-vragen vóór vrij gesprek
- Hints na elk assistant-antwoord (zelfde LLM-call als antwoord)
- Geen aparte persona-modes in MVP; onboarding bepaalt context en toon

## Gerelateerde beslissingen

[ADR-006](/core-domain/02-architectural/decisions/06-ADR-conversation-management.md), [open-beslissingen.md](/core-domain/01-strategic/open-beslissingen.md).