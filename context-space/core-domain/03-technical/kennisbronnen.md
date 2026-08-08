---
type: Knowledge Source
title: "Kennisbronnen — zes websites"
description: "Externe contentbronnen voor RAG-indexering."
tags: [rag, sources]
timestamp: 2026-06-26T00:00:00Z
resource: https://www.sogyo.nl
traces_to:
  - /core-domain/02-architectural/decisions/01-ADR-knowledge-strategy.md
---

# Kennisbronnen

De chatbot is **geen algemene assistent**. Hij verwijst actief naar content op deze zes bronnen ([ADR-001](/core-domain/02-architectural/decisions/01-ADR-knowledge-strategy.md)):

| Bron | Thema's (indicatief) |
|------|----------------------|
| [sogyo.nl](https://www.sogyo.nl) | Traineeship, filosofie, software craft |
| [jeroenteunisse.nl](https://jeroenteunisse.nl) | Engineering leadership, veranderkracht |
| [edwinvandillen.nl](https://edwinvandillen.nl) | IT-landschap, sourcing, architectuur |
| [augmentedorganisation.nl](https://augmentedorganisation.nl) | Canvases, governance, AI-adoptie |
| [intentdriven.nl](https://intentdriven.nl) | Intent-Driven Engineering, kennis-elicitatie |
| [augmentedengineering.nl](https://augmentedengineering.nl) | Vibe · Spec · Harness, Context Space |

## Strategie

- **RAG-first** — geen fine-tuning in MVP
- **Broad coverage** — zoveel mogelijk pagina's per bron
- **Her-ingestie** — doel 4–6 uur; handmatig in MVP ([ADR-007](/core-domain/02-architectural/decisions/07-ADR-ingestion-cadence.md))
- **Scraping** — respect robots.txt en sitemaps

## In scope onderwerpen (samenvatting)

Intent-Driven Engineering, Augmented Organisation, veranderkracht, IT-landschap, Harness Engineering, AI als collega, lokale/self-hosted AI, software engineering craft.

Zie [domein-scope.md](/core-domain/01-strategic/domein-scope.md) voor in/out scope van de chatbot zelf.