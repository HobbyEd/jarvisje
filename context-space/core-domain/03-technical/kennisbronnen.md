---
type: Knowledge Source
title: "Kennisbronnen — twee blogs"
description: "Externe contentbronnen voor RAG-indexering."
tags: [rag, sources]
timestamp: 2026-09-13T00:00:00Z
traces_to:
  - /core-domain/02-architectural/decisions/01-ADR-knowledge-strategy.md
  - /core-domain/02-architectural/decisions/12-ADR-jarvisje-rebrand.md
---

# Kennisbronnen

Jarvisje is **geen algemene assistent**. Hij verwijst alleen naar artikelen op deze twee bronnen ([ADR-012](/core-domain/02-architectural/decisions/12-ADR-jarvisje-rebrand.md)):

| Bron | Thema's (indicatief) |
|------|----------------------|
| [edwinvandillen.nl](https://edwinvandillen.nl) | Intentie-gedreven engineering, harnessing, AI-systemen, software-innovatie |
| [jeroenteunisse.nl](https://jeroenteunisse.nl) | Engineering leadership, veranderkracht |

Geen sogyo.nl, augmentedorganisation.nl, intentdriven.nl of augmentedengineering.nl.

## Strategie

- **RAG-first** — geen fine-tuning ([ADR-001](/core-domain/02-architectural/decisions/01-ADR-knowledge-strategy.md))
- **Broad coverage** — zoveel mogelijk pagina's per bron (sitemap-first)
- **Her-ingestie** — handmatig in MVP ([ADR-007](/core-domain/02-architectural/decisions/07-ADR-ingestion-cadence.md)); na bronwijziging **reset** van de vector-index
- **Scraping** — respect robots.txt en sitemaps
- **Hardening** — retrieval en citations beperkt tot deze hosts

## In-scope onderwerpen (samenvatting)

Wat in die twee blogs staat: intentie-gedreven engineering, harnessing, AI als systeem rondom het model, veranderkracht, software-engineeringvakmanschap.

Zie [domein-scope.md](/core-domain/01-strategic/domein-scope.md) voor in/out scope van de chatbot zelf.
