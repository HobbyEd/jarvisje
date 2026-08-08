---
type: ADR
title: "Ingestion-cadans"
description: "Doel: periodieke refresh; handmatig + later cron. Proces: ADR-010."
status: accepted
tags: [ingestion]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-007: Ingestion Cadence and Knowledge Refresh

## Status
Accepted (geactualiseerd 2026-08-08)

## Datum
2026-06-26 · update 2026-08-08

## Context
De kennisbasis (zes publieke domeinen) verandert incidenteel. Content moet actueel genoeg zijn zonder overkill.

Oorspronkelijke wens: refresh in de orde van **4–6 uur**.

## Decision (cadans — wat wanneer)

1. **Doel-cadans:** periodieke her-indexering (streef 4–6 uur of dagelijks, operationeel te kiezen).
2. **Handmatige trigger blijft:** beheerder kan force re-ingest via UI/API (met token) of CLI.
3. **Idempotent upsert:** zelfde URL/chunk-id → update (geen blinde duplicate-explosie).
4. **Incrementeel (default, `reset=false`):** sitemap vergelijken met URLs in Chroma; alleen **nieuwe** pagina's of pagina's met **nieuwere sitemap-lastmod** scrapen/embedden. Al bekende URLs zonder wijzigingssignaal worden overgeslagen (geen HTTP-fetch).
5. **Volledig (`reset=true`):** collectie wissen, daarna alle pagina's opnieuw ophalen en indexeren.
6. **Logging:** status van laatste run (progress, fouten, counts, skipped) is zichtbaar.

**Hoe** de job procesmatig draait (niet in de request-thread van de chat-API) staat in **[ADR-010](10-ADR-async-ingestion-worker.md)**.

## Reality check (2026-08)

| Besluit | Werkelijkheid |
|---------|----------------|
| 4–6 uur geautomatiseerd | ❌ nog niet (geen cron) |
| Handmatige / UI-ingest | ✅ met token (ADR-011) |
| Idempotent upsert | ✅ Chroma ids op url+chunk |
| Incrementeel (skip known) | ✅ sitemap + known URL/lastmod (v0.8.1+) |
| Status in UI | ✅ shared status file + worker (ADR-010) |

## Consequences
### Positief
- Cadans blijft een producteis, los van implementatietechniek.
- Cron later zonder wijziging aan “elke 4–6 uur”-intentie.

### Negatief
- Zolang geen scheduler: content kan langer verouderd zijn.
- Huidige in-API ingest schaadt chat-beschikbaarheid (opgelost via ADR-010).

## Alternatives Considered
- Real-time crawling: overkill.
- Alleen handmatig forever: te fragiel voor “levende” content.

## Gerelateerde ADRs
- ADR-001 Knowledge Strategy
- ADR-008 Citations
- **ADR-010 Async ingestion worker**

## Besloten door
Edwin + architectuur sessie met Grok
