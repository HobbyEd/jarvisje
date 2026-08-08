---
type: Context Map
title: "Context map — Sogyo Kennis-Chatbot"
description: "Relaties tussen bounded contexts en externe bronnen."
tags: [ddd, context-mapping]
timestamp: 2026-07-05T00:00:00Z
traces_to:
  - /core-domain/02-architectural/bounded-contexts.md
---

# Context map

```
┌─────────────────────────────────────────────────────────────┐
│  Externe kennisbronnen (6 websites)                          │
│  sogyo.nl · jeroenteunisse.nl · edwinvandillen.nl · …        │
└───────────────────────────┬─────────────────────────────────┘
                            │ upstream (published content)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Content-Ingestion (supporting)                              │
│  scrape → chunk → embed → vector store                       │
└───────────────────────────┬─────────────────────────────────┘
                            │ customer/supplier
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  Kennis-Chatbot (CORE)                                       │
│  onboarding · retrieval · guardrails · citations · hints       │
└───────────────┬─────────────────────────────┬─────────────────┘
                │ conformist                   │ customer/supplier
                ▼                              ▼
┌───────────────────────────┐    ┌────────────────────────────┐
│  Inference-Serving (DGX)    │    │  Chat-UI (gebruiker)        │
│  vLLM OpenAI-compatible     │    │  sollicitant / bedrijf      │
└───────────────────────────┘    └────────────────────────────┘
```

## Relatiepatronen

| Van | Naar | Patroon | Toelichting |
|-----|------|---------|-------------|
| Kennis-Chatbot | Content-Ingestion | Customer/Supplier | Chatbot definieert wat geïndexeerd moet zijn (metadata, bronnen); ingestion levert chunks |
| Kennis-Chatbot | Inference-Serving | Conformist | Volgt OpenAI API-contract; geen eigen LLM-model |
| Kennis-Chatbot | Externe bronnen | Anticorruption (light) | Citations verwijzen naar URLs; geen import van hun domeinmodel |
| Content-Ingestion | Externe bronnen | Conformist | Scraper volgt site-structuur; geen wijziging aan bronnen |

## Grensvlakken (conceptueel)

- **Retrieval API** (intern): query → ranked chunks + metadata
- **LLM API** (extern conformist): messages → structured completion
- **Ingest trigger** (intern): start/status voor her-indexering ([use case](/core-domain/04-delivery/use-cases/bronnen-indexeren.md))

Operationele endpoints en poorten: [infra/runbooks/infrastructure.md](../../../infra/runbooks/infrastructure.md).