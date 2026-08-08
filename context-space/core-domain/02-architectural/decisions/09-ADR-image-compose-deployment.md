---
type: ADR
title: "Image + Compose deployment"
description: "Image + compose op .15; lokaal Ollama LLM; data buiten image."
status: accepted
tags: [deployment, docker]
timestamp: 2026-06-27T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-009: Image + Compose Deployment Strategy

## Status
Accepted (geactualiseerd 2026-08-08)

## Datum
2026-06-27 · update 2026-08-08

## Context

De bestaande deployment (`infra/deploy.ps1` + build op de server) faalde regelmatig door DNS/pip-problemen op de oude host `.10`, gebruikte geen declaratieve compose-stack, en bood geen heldere scheiding tussen immutable app-image en mutable data (Chroma vector store).

**Oorspronkelijk (2026-06):** app op `.10`, LLM op DGX `.128`.  
**Huidig (2026-08):** app + lokaal LLM (Ollama `gemma3:4b`) op **`192.168.165.15`**, publiek via Cloudflare Tunnel (`jarvisje.com`). Data-persistentie bij image-updates blijft verplicht.

Zie ook ADR-005 (Temporary Deployment) en ADR-004 (Inference Serving).

## Decision

We kiezen voor een **image-first deployment** met **docker-compose** als declaratieve runtime op de app-server:

1. **Image bouwen** — bij voorkeur op de productieserver (amd64) of lokaal + rsync tarball.
2. **Transfer (optioneel)** — Image als `tar.gz` + compose-file naar de server.
3. **Server: load + compose up** — `docker load` gevolgd door `docker compose up -d` (of systemd).
4. **Data buiten image** — Chroma op host-pad `/home/evdillen/sogyo-chatbot-data`.
5. **LLM buiten app-image** — Ollama als aparte compose-service; `LLM_BASE_URL` / `LLM_MODEL` via env.
6. **Boot via systemd** — `sogyo-ollama.service` + `sogyo-chatbot.service` (+ host `cloudflared` voor het domein).

Productie-compose: `infra/ubuntu-x64/docker-compose.prod-local.yaml`.

### Niet in scope

- Container registry / zware CI
- Blue/green zero-downtime
- Tunnel of secrets in de app-image

## Consequences

### Positief

- Server hoeft niet te `pip install` bij elke deploy als image prebuilt is.
- Vector store overleeft image-updates.
- LLM-upgrade (ander Ollama-model) zonder app-image rebuild.
- Cloudflare tunnel onafhankelijk van app-image.
- Rollback = oud image-tag + `compose up` / systemd restart.

### Negatief / aandachtspunten

- Grote images (torch + BGE-M3).
- Embeddings tijdelijk op CPU (Blackwell sm_120 vs. torch cu124).
- Twee compose-services + drie systemd units om te beheren.

## Operationele uitwerking

[`infra/runbooks/deployment.md`](../../../../infra/runbooks/deployment.md) · [`infra/runbooks/infrastructure.md`](../../../../infra/runbooks/infrastructure.md)

## Related

- ADR-005 Temporary Deployment
- ADR-004 Inference Serving
- `infra/ubuntu-x64/docker-compose.prod-local.yaml`, `setup-sogyo-service.sh`