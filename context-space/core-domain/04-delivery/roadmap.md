---
type: Roadmap
title: "Product roadmap"
description: "Huidige staat en volgende stappen — lean delivery."
tags: [delivery, roadmap]
timestamp: 2026-08-08T00:00:00Z
traces_to:
  - /core-domain/01-strategic/succescriteria.md
  - /core-domain/01-strategic/vision.md
---

# Product roadmap — Sogyo Kennis-Chatbot

## Huidige staat (2026-08)

| Item | Status |
|------|--------|
| RAG chat + citations + SSE UI | Live |
| Productiehost | `192.168.165.15` (enterprise) |
| Publiek | https://jarvisje.com (Cloudflare Tunnel) |
| LLM | Ollama `gemma3:4b` (GPU, lokaal) |
| Embeddings | BGE-M3 (CPU tot Blackwell/torch-support) |
| Indexering | ADR-010 async worker; ADR-011 `INGEST_TOKEN` via `.env`; sitemap-first |
| Deploy | Docker Compose + systemd (`sogyo-ollama`, `sogyo-chatbot`, `cloudflared`) |
| UI-versie | zie badge in `web/index.html` |

MVP end-to-end is **operationeel**. Verdere fasen zijn kwaliteit, onderhoud en schaal — geen “from scratch” meer.

## Afgeronde foundation (was fase 0–3)

- Ingestion (scrape → chunk → embed → Chroma)
- Chat orchestrator + structured output
- Guardrails / domain framing (prompts + ADRs)
- Demo UI (chat, bronnen, architectuur-tab)
- Image + compose deployment (ADR-009)

## Open / volgende stappen

### P0 — stabiliteit & operatie
- [x] **ADR-010**: ingestion worker buiten chat-API-proces + status in UI
- [ ] Herindexering alle bronnen (hoge max / full crawl) en controleren page counts
- [ ] Geplande ingest (cron/systemd timer) via dezelfde worker-entrypoint
- [ ] Backup van `sogyo-chatbot-data` documenteren/automatiseren

### P1 — kwaliteit
- [ ] Evaluatieset (20–25 vragen) + handmatige scoring
- [ ] PyTorch met sm_120 → embeddings weer op GPU
- [ ] Eventueel groter lokaal model als VRAM/kwaliteit dat toelaat

### P2 — engineering hygiene
- [ ] Minimale automated smoke tests (health + chat/sync mock of live)
- [ ] Designer agent alleen bij architectuur-commits (optioneel verlichten werkwijze)

## Out of scope (bewust)

- Fine-tuning eigen model in deze fase
- Multi-tenant / cloud SaaS
- Terugkeer naar aparte DGX-build pipeline in deze repo

## Gerelateerd

- Runbooks: `infra/runbooks/infrastructure.md`, `deployment.md`
- ADRs: `core-domain/02-architectural/decisions/`
- Werkwijze: [werkwijze.md](werkwijze.md)
