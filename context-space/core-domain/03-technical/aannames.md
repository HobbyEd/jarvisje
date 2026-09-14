---
type: Assumption
title: "Aannames MVP bouwfase"
description: "Expliciete aannames herzienbaar tijdens implementatie."
tags: [assumptions, mvp]
timestamp: 2026-06-27T00:00:00Z
traces_to:
  - /core-domain/01-strategic/domein-scope.md
---

# Aannames & Beslissingen (MVP Bouwfase)

Dit document bevat expliciete aannames die gemaakt zijn tijdens de implementatie zodat ze later herzien kunnen worden.

## Algemene aannames

- Productie-LLM: Ollama `gemma3:4b` op host `.15` (`http://ollama:11434/v1` in compose, `http://<host>:11434/v1` vanaf LAN). Zie `infra/runbooks/infrastructure.md`.
- NVIDIA Spark DGX `<host>` / vLLM is **geen** deploydoel (historisch; ADR-004/005).
- Voor de MVP is er geen persistente user session state nodig; history wordt door de client meegegeven.
- "Hints na ieder antwoord" worden **in dezelfde LLM call** gegenereerd via structured output (zoals besloten in [domein-scope](/core-domain/01-strategic/domein-scope.md)).

## Software Designer Agent

- De agent draait volledig lokaal na een commit (via post-commit hook).
- Harnessing findings worden aangemaakt als Markdown in `context-space/harnessing/findings/` (OKF-type `Finding`).
- De agent checkt op:
  - Voldoen aan vastgelegde ADRs (simpele tekst/zoek checks op code + docs).
  - Basis complexiteitsmetrics: aantal bestanden, LOC, import count, ruwe functie complexiteit via AST (geen zware externe tools zoals radon als default).
  - Verdubbeling / te grote bestanden (eenvoudige heuristics).
- De agent is lightweight en mag optioneel extra deps hebben (maar default werkt zonder).
- Na implementatie van de agent wordt direct de `.git/hooks/post-commit` gezet zodat volgende commits hem triggeren.

## Prompts & Structured Output

- Structured output via instructies + Pydantic (of response_format waar ondersteund door het OpenAI-compatible model).
- Onboarding flow:
  1. Vraag rol (sollicitant/student vs bedrijf)
  2. Vraag interessegebied
- Na **elke** user + assistant beurt worden 3-5 korte hints gegeven voor vervolgvragen/onderwerpen.
- Citations zijn verplicht in de `answer` wanneer claims worden gedaan. Citations bevatten ten minste `title` + `url`.
- Guardrails zijn "gematigd" zoals in [domein-scope](/core-domain/01-strategic/domein-scope.md) beschreven (domein software engineering + engineer development).

## FastAPI + Streaming

- Backend exposeert een `/chat` endpoint die streaming ondersteunt via Server-Sent Events (SSE).
- Voor MVP is er een eenvoudige in-memory conversatie of de client stuurt volledige history mee.
- SSE events gebruiken simpele `data: {...}` formaat met JSON (of `event: message` + data).
- De UI zit in `web/index.html` en wordt door de FastAPI (`/`) geserveerd (zowel lokaal als in container) voor consistente ervaring. De backend biedt SSE `/chat`.
- De orchestrator combineert retrieval (Chroma + BGE-M3) + prompt + LLM call.

## Technische / Implementatie aannames

- Embedding model: BGE-M3 (1024 dim). Collection naam is model-specifiek om dim-conflicten te voorkomen.
- LLM client: `httpx` + OpenAI-compatibele `/chat/completions` (of `openai` library als die al in env zit).
- Geen LangChain/LlamaIndex.
- Voor development kan de LLM tijdelijk gemockt worden (of een lokale Ollama).
- Post-commit hook is een eenvoudige shell script die `python -m jarvisje.designer.cli` aanroept.
- Alle code blijft in `src/jarvisje/`.
- Commits na iedere logische bouwstap.

## Open punten / Later te herzien

- Hoe precies "ADR compliance" automatisch gecheckt wordt (huidig: eenvoudige heuristieken).
- Modelwissel op `.15` (groter Ollama-model) als VRAM/kwaliteit dat toelaat.
- Frontend UX details (wordt basic gehouden).
- Performance / caching van retrieval in de API.

Laatste update: 2026-09-14
