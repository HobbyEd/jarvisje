---
type: Use Case
title: "Bronnen indexeren"
description: "Kennisbasis vullen of verversen via ingestion pipeline."
tags: [ingestion, rag]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/02-architectural/decisions/07-ADR-ingestion-cadence.md
  - /core-domain/03-technical/kennisbronnen.md
---

# Use case: Bronnen indexeren

## Actor

Operator (ontwikkelaar) of gebruiker via UI-tab "Bronnen & Meta-data" (MVP).

## Trigger

- Handmatige start via UI (`/ingest/start`) of CLI `scripts/ingest.py`
- Toekomst: scheduled elke 4–6 uur

## Flow

1. Scraper haalt content van [zes kennisbronnen](/core-domain/03-technical/kennisbronnen.md) op.
2. Tekst wordt gechunked met metadata (url, title, section).
3. Embeddings (BGE-M3) + opslag in Chroma.
4. Status beschikbaar via `/ingest/status` (live voortgang in UI).

## Acceptatie

- Alle zes bronnen indexeerbaar
- Chroma persistent buiten container-image
- UI toont per bron: aantal pagina's + last_updated

## Bounded context

Valt onder **Content-Ingestion** (supporting); zie [bounded-contexts.md](/core-domain/02-architectural/bounded-contexts.md).