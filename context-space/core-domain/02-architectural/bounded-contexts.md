---
type: Bounded Context
title: "Bounded contexts — Sogyo Kennis-Chatbot"
description: "Domeingrenzen en classificatie van de chatbot en ondersteunende contexten."
tags: [ddd, architecture]
timestamp: 2026-07-05T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# Bounded contexts

Voor de MVP modelleren we één **core** bounded context met twee **supporting** contexten. Geen kunstmatige opsplitsing van retrieval/LLM/UI — dat zijn technische componenten binnen of naast de core.

## Core: Kennis-Chatbot

| Eigenschap | Waarde |
|------------|--------|
| Type | Core domain (MVP) |
| Doel | Gesprek voeren binnen Sogyo-domein met grounded antwoorden en citations |
| Ubiquitous language | [ubiquitous-language.md](/core-domain/03-technical/ubiquitous-language.md) |
| Harnessing | Gematigde guardrails + citation-forcing + Designer Agent |

**Verantwoordelijkheden (wat & waarom):**

- Onboarding en conversatie-orchestratie
- Retrieval + prompt + structured output (answer, citations, hints)
- Domeincontrole (in/out scope)
- Verwijzing naar externe [kennisbronnen](/core-domain/03-technical/kennisbronnen.md)

**Niet:** LLM-serving, scraping-implementatie, container-deploy (supporting/actualization).

## Supporting: Content-Ingestion

| Eigenschap | Waarde |
|------------|--------|
| Type | Supporting (generic) |
| Relatie tot core | Customer/supplier — levert geïndexeerde chunks |
| Cadence | Handmatig MVP; doel 4–6 uur ([ADR-007](/core-domain/02-architectural/decisions/07-ADR-ingestion-cadence.md)) |

Verantwoordelijk voor ophalen, chunken, embedden en vullen van de vector store. De chatbot consumeert het resultaat; kent de scrape-details niet.

## Supporting: Inference-Serving

| Eigenschap | Waarde |
|------------|--------|
| Type | Commodity (black box) |
| Relatie tot core | Conformist — OpenAI-compatible API |
| Beslissing | [ADR-004](/core-domain/02-architectural/decisions/04-ADR-inference-serving.md) |

vLLM op DGX levert completions. De chatbot stuurt prompts en ontvangt structured output; modelkeuze en GPU-config horen in Actualization Space.

## Agent-sturing (AE.nl lens)

| Context | Agent-gedrag |
|---------|--------------|
| Kennis-Chatbot | Diep modelleren; ADR-compliance; projections bij architectuurwijzigingen |
| Content-Ingestion | Respecteer ADR-007; geen chat-guardrails |
| Inference-Serving | Integreer via vast contract; geen wijzigingen aan vLLM zonder ADR |

Zie [context-map.md](context-map.md) voor relaties tussen contexten.