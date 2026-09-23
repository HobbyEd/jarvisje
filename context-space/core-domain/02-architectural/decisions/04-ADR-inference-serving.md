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
2026-06-26 · update 2026-08-08 · update 2026-09-14 · update 2026-09-22 · update 2026-09-23

## Context
We willen lokaal infereren: volledige controle, geen cloud-API voor de kern, flexibele modelkeuze, streaming en bruikbare structured output.

Oorspronkelijk (2026-06) was NVIDIA Spark DGX `<legacy-host>` de beoogde GPU-host met vLLM.  
Sinds 2026-08 draait **Jarvisje** op host **`<host>`** (RTX 5060 Ti 16 GB). De DGX is **geen** productie- of optioneel deploydoel meer.

## Decision

### Productie (Jarvisje, 2026-08+)
- **Ollama** op dezelfde host als de app (de productiehost).
- Model: **`gemma3:4b`** (OpenAI-compatible API op poort 11434).
- Contextvenster: **8192** tokens via `OLLAMA_CONTEXT_LENGTH`. De kaart (16 GB) valt anders in Ollama’s 4096-standaard. Het model zelf kan 131072; 8192 is het dubbele van de standaard, zonder de KV-cache naast Gemma te laten ontsporen.
- Backend configureert `LLM_BASE_URL` + `LLM_MODEL` via compose-env (niet hard in image).
- Embeddings: **BGE-M3** lokaal in de app-image (sentence-transformers, torch **2.11.0+cu128**, sm_120).
  - Vraag-embedding in het API-proces: **CPU** (`EMBEDDING_DEVICE=cpu`). Eén vector per beurt; BGE blijft niet resident naast Gemma.
  - Indexering (UI-worker én compose-profile `ingest`): **GPU** (`EMBEDDING_DEVICE=cuda`). De app-container heeft de kaart zichtbaar alleen zodat dat kindproces hem kan gebruiken.
  - `torchvision` en `torchaudio` zitten niet in de image. De app gebruikt ze niet; een oude torchvision breekt de import van transformers tegen een nieuwere torch.
- Client blijft OpenAI-compatible: wissel endpoint/model via env **op de productiehost**.

**Constante eis:** OpenAI-compatibele chat-completions API naar de backend.

## Consequences
### Positief
- Volledige controle en privacy (geen cloud-API voor kern).
- Productie-stack op één machine.
- Modelwissel zonder app-image rebuild (Ollama pull).

### Negatief / Risico's
- 4B-model: lagere kwaliteit dan grotere GPU-modellen.
- Resource management GPU (Ollama + eventueel andere containers).
- Indexering deelt de GPU met Gemma (BGE-M3 rond 2 GB naast het 4B-model). Een groter chatmodel is het moment om indexering weer te laten wijken.

## Reality check (2026-09)

Productie **draait** op Ollama `gemma3:4b` op de productiehost. Structured output werkt via OpenAI-compatible JSON mode + backend parsing. vLLM op `<legacy-host>` is geen runtime-afhankelijkheid en geen deploydoel.

2026-09-22: torch 2.11.0+cu128 op de productiehost ziet de RTX 5060 Ti als capability (12, 0) en een BGE-M3-encode levert dimensie 1024. De cu124-pin was de blokkade, niet de kaart.

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
