---
type: ADR
title: "Inference OpenAI-compatible lokaal"
description: "Productie: Ollama gemma3:4b op .15; DGX/vLLM optioneel."
status: accepted
tags: [ollama, vllm, inference]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-004: Inference Serving Strategy

## Status
Accepted (geactualiseerd 2026-08-08)

## Datum
2026-06-26 · update 2026-08-08

## Context
We willen lokaal infereren: volledige controle, geen cloud-API voor de kern, flexibele modelkeuze, streaming en bruikbare structured output.

Oorspronkelijk (2026-06) was de DGX de primaire GPU-host met vLLM.  
Sinds 2026-08 draait de **productie-Sogyo-chatbot** op host **`192.168.165.15`** (RTX 5060 Ti 16 GB) met een kleiner model voor latency en operationele eenvoud.

## Decision

### Productie (Sogyo chatbot, 2026-08)
- **Ollama** op dezelfde host als de app (`enterprise` / `.15`).
- Model: **`gemma3:4b`** (OpenAI-compatible API op poort 11434).
- Backend configureert `LLM_BASE_URL` + `LLM_MODEL` via compose-env (niet hard in image).
- Embeddings: **BGE-M3** lokaal in de app-container (CPU tot PyTorch Blackwell-support).

### Optioneel / zware workloads
- **vLLM op de DGX** blijft beschikbaar voor grotere models en experimenten.
- Client blijft OpenAI-compatible: wissel endpoint/model via env.

**Constante eis:** OpenAI-compatibele chat-completions API naar de backend.

## Consequences
### Positief
- Volledige controle en privacy (geen cloud-API voor kern).
- Productie-stack op één machine (eenvoudiger dan app + remote DGX).
- Modelwissel zonder app-image rebuild (Ollama pull).
- DGX optioneel voor zwaardere quality-paden.

### Negatief / Risico's
- 4B-model: lagere kwaliteit dan grote DGX-models.
- Resource management GPU (Ollama + eventueel andere containers).
- Embeddings tijdelijk op CPU (torch vs. sm_120).

## Alternatives Considered
- **Alleen cloud APIs** (OpenAI, Anthropic, Grok, etc.): Verworpen vanwege kosten, controle en het feit dat we de DGX hebben.
- **Alleen Ollama lokaal**: Goed voor ontwikkeling, maar minder geschikt voor productie-grade throughput en structured output dan vLLM.
- **Externe inference + RAG lokaal**: Niet gewenst als primaire oplossing.

## Modelkeuze
- We blijven open voor verschillende families.
- Criteria voor modelselectie:
  - Nederlandse taalvaardigheid
  - Context window grootte (lange gesprekken)
  - Kwaliteit van reasoning binnen abstracte/strategische content
  - Structured output / tool use capaciteit
  - Inference snelheid op beschikbare hardware

Gemma-ervaring is aanwezig en mag gebruikt worden als startpunt.

## Gerelateerde ADRs
- ADR-005: Temporary Deployment Model
- ADR-003: Primary Language

## Besloten door
Edwin + architectuur sessie met Grok
