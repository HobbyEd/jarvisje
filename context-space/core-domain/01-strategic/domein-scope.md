---
type: Scope
title: "MVP functionele scope"
description: "In/out scope voor de Sogyo Kennis-Chatbot MVP."
tags: [mvp, scope]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# Domein-scope (MVP)

## In scope

### Kennisbasis

- Volledige content van alle 6 [kennisbronnen](/core-domain/03-technical/kennisbronnen.md).
- Broad coverage: geen strenge pre-prioritering van pagina's; indexeren wat we kunnen scrapen.

### Core functionaliteit

- Conversatie via een interface (tekst in/uit).
- [Onboarding flow](/core-domain/04-delivery/use-cases/onboarding-flow.md): welkom + 2 vragen + hints na elk antwoord.
- Retrieval van relevante chunks.
- Generatie met **verplichte citations** (link + titel).
- Basis multi-turn chat (geschiedenis).
- **MVP stretch**: consent voor sessie-deling bij lastige gevallen (zie [ADR-006](/core-domain/02-architectural/decisions/06-ADR-conversation-management.md)).

### Guardrails

- Gematigd: binnen "software engineering en het ontwikkelen van engineers".
- Domeingerelateerde vragen zonder goede bron-match: antwoorden toegestaan mits link naar content/principes.
- Duidelijke weigering buiten domein.
- Retrieval-first, met ruimte voor domein-gerelateerde antwoorden.

### Taal & output

- Nederlands als primair ([ADR-003](/core-domain/02-architectural/decisions/03-ADR-primary-language.md)).
- Structured output voor citations ([ADR-008](/core-domain/02-architectural/decisions/08-ADR-citations-grounding.md)).
- Streaming verplicht voor MVP.

### UI

- Lichte custom HTML + JavaScript (geen Gradio).
- Citations onder het antwoord.
- Multi-turn chat.

## Out of scope

- Geavanceerde gelaagde guardrails (pre-classifier + post-validator).
- Volledige context compression voor lange gesprekken.
- Aparte persona-modes buiten onboarding.
- Productie-widget op sogyo.nl.
- Automatische 4–6 uurs refresh (handmatige ingest OK).
- Evaluatie-dashboard.
- Authenticatie, rate limiting, gesprekslogging.
- Interactieve tools/canvases (alleen beschrijven + linken).
- Engels als primaire taal.

## Beperkingen

- Tijdelijk DGX-centric / lokale setup ([ADR-005](/core-domain/02-architectural/decisions/05-ADR-temporary-deployment.md)).
- RAG-first, geen fine-tuning in MVP ([ADR-001](/core-domain/02-architectural/decisions/01-ADR-knowledge-strategy.md)).
- Lightweight implementatie; kwaliteit iteratief na MVP.

## Beslissingen (archief)

Alle interviewbeslissingen uit de oorspronkelijke scope-sessie staan in [open-beslissingen.md](open-beslissingen.md).