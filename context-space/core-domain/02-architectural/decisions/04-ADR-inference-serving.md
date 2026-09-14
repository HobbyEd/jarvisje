---
type: ADR
title: "Inference OpenAI-compatible lokaal"
description: "Productie: Ollama gemma3:4b op .15. Geen DGX-deploy."
status: accepted
tags: [ollama, vllm, inference]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-004: Inference Serving Strategy

## Status
Accepted (geactualiseerd 2026-09-14)

## Datum
2026-06-26 · update 2026-08-08 · update 2026-09-14

## Context
We willen lokaal infereren: volledige controle, geen cloud-API voor de kern, flexibele modelkeuze, streaming en bruikbare structured output.

Oorspronkelijk (2026-06) was NVIDIA Spark DGX `<host>` de beoogde GPU-host met vLLM.  
Sinds 2026-08 draait **Jarvisje** op host **`<host>`** (RTX 5060 Ti 16 GB). De DGX is **geen** productie- of optioneel deploydoel meer.

## Decision

### Productie (Jarvisje, 2026-08+)
- **Ollama** op dezelfde host als de app (`enterprise` / `.15`).
- Model: **`gemma3:4b`** (OpenAI-compatible API op poort 11434).
- Backend configureert `LLM_BASE_URL` + `LLM_MODEL` via compose-env (niet hard in image).
- Embeddings: **BGE-M3** lokaal in de app-container (CPU tot PyTorch Blackwell-support).
- Client blijft OpenAI-compatible: wissel endpoint/model via env **op `.15`**.

**Constante eis:** OpenAI-compatibele chat-completions API naar de backend.

## Consequences
### Positief
- Volledige controle en privacy (geen cloud-API voor kern).
- Productie-stack op één machine.
- Modelwissel zonder app-image rebuild (Ollama pull).

### Negatief / Risico's
- 4B-model: lagere kwaliteit dan grotere GPU-modellen.
- Resource management GPU (Ollama + eventueel andere containers).
- Embeddings tijdelijk op CPU (torch vs. sm_120).

## Reality check (2026-09)

Productie **draait** op Ollama `gemma3:4b` op `.15`. Structured output werkt via OpenAI-compatible JSON mode + backend parsing. vLLM op `<host>` is geen runtime-afhankelijkheid en geen deploydoel.

## Alternatives Considered
- **Alleen cloud APIs** (OpenAI, Anthropic, Grok, etc.): Verworpen vanwege kosten en controle.
- **vLLM op DGX als primary**: Historisch overwogen; operationeel zwaarder; **niet** de productiestandaard en **niet** meer in de deploy-descriptors.
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
