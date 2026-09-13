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
| **Jarvisje** | De RAG-chatbot; core bounded context van dit project. Ondertitel: een chatbot rondom de wereld van AI |
| **Kennisbron** | Eén van de twee geïndexeerde blogs (zie [kennisbronnen.md](kennisbronnen.md)) |
| **Chunk** | Een tekstfragment uit een kennisbron met metadata (url, title, section) |
| **Retrieval** | Zoeken van relevante chunks bij een gebruikersvraag (alleen toegestane hosts) |
| **Citation** | Verplichte bronverwijzing (minimaal `title` + `url`) bij een bewering; host moet een kennisbron zijn |
| **Grounding** | Antwoord baseren op opgehaalde chunks; hallucinaties minimaliseren |
| **Hint** | 3–5 korte vervolgvragen of onderwerpen na elk assistant-antwoord |
| **Welkom** | Korte begroeting zonder rolvragen (geen sollicitant/bedrijf) |
| **Guardrail** | Regel die het gesprek binnen het onderwerp van de twee blogs houdt (gematigd) |
| **In-domein** | Vraag over software engineering, AI-augmentatie, intentie-gedreven werk of de blogs |
| **Out-of-domein** | Vraag buiten scope → beleefde weigering of redirect |
| **Grijs gebied** | Randgevallen; antwoord toegestaan mits link naar content |
| **Structured output** | Eén LLM-response met `answer`, `citations`, `suggested_hints` (Pydantic) |
| **Streaming** | Antwoord tikt live binnen via SSE (`/chat`) |
| **Embed** | Compacte chat-only view (`/?embed=1`) voor iframe op edwinvandillen.nl |
| **Standalone** | Volledige UI op jarvisje.com inclusief bronnen/indexering |
| **Sessie-consent** | Optionele toestemming om gesprek te delen voor content-verrijking (stretch) |
| **Designer Agent** | Post-commit agent die ADRs en complexiteit checkt; schrijft harnessing findings |
| **Finding** | OKF-rapport van de Designer Agent in `context-space/harnessing/findings/` |

## Relatie tot ADRs

- Citations → [ADR-008](/core-domain/02-architectural/decisions/08-ADR-citations-grounding.md)
- Guardrails → [ADR-002](/core-domain/02-architectural/decisions/02-ADR-guardrails.md)
- Taal → [ADR-003](/core-domain/02-architectural/decisions/03-ADR-primary-language.md)