---
type: Scope
title: "Functionele scope — Jarvisje"
description: "In/out scope na rebrand (ADR-012)."
tags: [jarvisje, scope]
timestamp: 2026-09-13T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
  - /core-domain/02-architectural/decisions/12-ADR-jarvisje-rebrand.md
---

# Domein-scope

## In scope

### Kennisbasis

- Content van de twee [kennisbronnen](/core-domain/03-technical/kennisbronnen.md): edwinvandillen.nl en jeroenteunisse.nl.
- Broad coverage: indexeren wat we kunnen scrapen (artikelen via sitemap-first).

### Core functionaliteit

- Conversatie via standalone UI (`jarvisje.com`) en compacte **embed-view** (`/?embed=1`) voor iframe op edwinvandillen.nl.
- Dark/light volgens tokens van *Edwin Blog*; in embed volgt het parent-thema.
- Retrieval van relevante chunks uit alleen die twee hosts.
- Generatie met **verplichte citations** (link + titel), alleen naar die hosts.
- Basis multi-turn chat (geschiedenis in-sessie).
- Hints na elk antwoord (zelfde LLM-call).

### Guardrails

- Gematigd: binnen software engineering, AI-augmentatie, intentie-gedreven werk en de onderwerpen van de twee blogs.
- Geen match in de bronnen: eerlijk zeggen en verwijzen naar wat wél bekend is.
- Duidelijke weigering buiten domein.
- Retrieval-first.

### Taal & output

- Nederlands als primair ([ADR-003](/core-domain/02-architectural/decisions/03-ADR-primary-language.md)).
- Structured output voor citations ([ADR-008](/core-domain/02-architectural/decisions/08-ADR-citations-grounding.md)).
- Streaming verplicht.

### UI

- Lichte custom HTML + JavaScript (geen Gradio).
- Standalone: header Jarvisje + ondertitel, tabs Chat / Bronnen / Opbouw, theme-toggle.
- Embed: alleen de chatkaart, geen beheer-tabs.

## Out of scope

- Sogyo.nl, augmentedorganisation.nl, intentdriven.nl, augmentedengineering.nl als kennisbron.
- Sollicitant/bedrijf-onboarding en Sogyo-traineeship-toon.
- Zwevende chatbubbel; WordPress-themacode in deze repo.
- Geavanceerde gelaagde guardrails (aparte pre-classifier + post-validator-LLM).
- Volledige context compression voor lange gesprekken.
- Automatische 4–6 uurs refresh (handmatige ingest OK).
- Evaluatie-dashboard, authenticatie, rate limiting, permanente gesprekslogging.
- Interactieve tools/canvases (alleen beschrijven + linken).
- Engels als primaire taal.
- Iron Man-beeldmerk of Marvel-assets.

## Beperkingen

- Eén host `.15`, image + compose ([ADR-009](/core-domain/02-architectural/decisions/09-ADR-image-compose-deployment.md)).
- RAG-first, geen fine-tuning ([ADR-001](/core-domain/02-architectural/decisions/01-ADR-knowledge-strategy.md)).
- Lightweight Python.

## Beslissingen

Productkader: [ADR-012](/core-domain/02-architectural/decisions/12-ADR-jarvisje-rebrand.md). Overige keuzes in [decisions/](/core-domain/02-architectural/decisions/).
