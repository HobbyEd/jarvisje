---
type: Ubiquitous Language
title: "Ubiquitous language — Kennis-Chatbot"
description: "Gedeelde domeinbegrippen voor mens, code en agents."
tags: [ddd, language]
timestamp: 2026-07-05T00:00:00Z
traces_to:
  - /core-domain/02-architectural/bounded-contexts.md
---

# Ubiquitous language

Termen in de **Kennis-Chatbot** bounded context. Gebruik deze definities in prompts, ADRs, code-comments en agent-instructies.

| Term | Definitie |
|------|-----------|
| **Kennis-Chatbot** | De Sogyo RAG-chatbot; core bounded context van dit project |
| **Kennisbron** | Eén van de zes geïndexeerde websites (zie [kennisbronnen.md](kennisbronnen.md)) |
| **Chunk** | Een tekstfragment uit een kennisbron met metadata (url, title, section) |
| **Retrieval** | Zoeken van relevante chunks bij een gebruikersvraag |
| **Citation** | Verplichte bronverwijzing (minimaal `title` + `url`) bij een bewering in het antwoord |
| **Grounding** | Antwoord baseren op opgehaalde chunks; hallucinaties minimaliseren |
| **Hint** | 3–5 korte vervolgvragen of onderwerpen na elk assistant-antwoord |
| **Onboarding** | Welkomstflow met 2 vragen: rol (sollicitant/bedrijf) + interessegebied |
| **Guardrail** | Regel die het gesprek binnen het Sogyo-domein houdt (gematigd in MVP) |
| **In-domein** | Vraag over software engineering, engineer-ontwikkeling, Sogyo-filosofie |
| **Out-of-domein** | Vraag buiten scope → beleefde weigering of redirect |
| **Grijs gebied** | Randgevallen; antwoord toegestaan mits link naar content/principes |
| **Structured output** | Eén LLM-response met `answer`, `citations`, `suggested_hints` (Pydantic) |
| **Streaming** | Antwoord tikt live binnen via SSE (`/chat`) |
| **Sollicitant** | Primaire doelgroep: starter/traineeship-kandidaat |
| **Bedrijf** | Secundaire doelgroep: organisatie geïnteresseerd in talent/AI-adoptie |
| **Sessie-consent** | Optionele toestemming om gesprek te delen voor content-verrijking (stretch) |
| **Designer Agent** | Post-commit agent die ADRs en complexiteit checkt; schrijft harnessing findings |
| **Finding** | OKF-rapport van de Designer Agent in `context-space/harnessing/findings/` |

## Relatie tot ADRs

- Citations → [ADR-008](/core-domain/02-architectural/decisions/08-ADR-citations-grounding.md)
- Guardrails → [ADR-002](/core-domain/02-architectural/decisions/02-ADR-guardrails.md)
- Taal → [ADR-003](/core-domain/02-architectural/decisions/03-ADR-primary-language.md)