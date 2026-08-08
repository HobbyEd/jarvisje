---
type: ADR
title: "Ingestion-cadans"
description: "Her-ingestie elke 4-6 uur als doel."
status: accepted
tags: [ingestion]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-007: Ingestion Cadence and Knowledge Refresh

## Status
Accepted

## Datum
2026-06-26

## Context
De kennisbasis bestaat uit blogposts en tools die af en toe worden aangevuld of aangepast.

User-specificatie:
- "om 4 tot 6 uur is prima."

We willen de content redelijk actueel houden zonder overkill.

## Decision
De ingestion pipeline draait **elke 4 tot 6 uur**.

### Details
- Volledige her-ingestie van de zes bronnen.
- Bestaande chunks worden vervangen of versie-beheerd (bij voorkeur idempotent: zelfde URL + section → update).
- Nieuwe of gewijzigde content wordt automatisch toegevoegd.
- Er wordt een log bijgehouden van de laatste succesvolle ingest (inclusief versie/hash van de bronnen).

## Consequences
### Positief
- Voldoende actueel voor de use case (nieuwe blogs komen niet per uur uit).
- Laag resource gebruik.
- Eenvoudig te implementeren als cron / scheduled job op de DGX.

### Negatief / Risico's
- Tussen runs kunnen nieuwe artikelen een paar uur "onbereikbaar" zijn voor de chatbot.
- Fouten in de pipeline moeten gemonitord worden.

## Alternatives Considered
- **Real-time / event-driven** (webhooks of continue crawling): Overkill en risico op instabiliteit.
- **Dagelijks**: Te traag voor een levendige kennisbasis.
- **Elk uur**: Te vaak, onnodig resource intensief.

## Implementation Notes
- Maak de pipeline idempotent en herstartbaar.
- Voeg health checks en logging toe (bijv. "X documenten verwerkt, Y nieuwe chunks").
- Overweeg een "force re-ingest" endpoint of script voor handmatige updates.
- Sla metadata op over de bronversies (bijv. laatste gewijzigde datum van pagina's).

## Gerelateerde ADRs
- ADR-001: Knowledge Strategy
- ADR-008: Citations and Grounding

## Besloten door
Edwin + architectuur sessie met Grok
