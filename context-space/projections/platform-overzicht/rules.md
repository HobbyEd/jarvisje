---
type: Playbook
title: "Platform-overzicht projection rules"
description: "Richtlijnen voor het onderhouden van platform-overzicht.html."
tags: [projections]
timestamp: 2026-07-05T00:00:00Z
---

# Platform-overzicht — projection rules

**Output:** [../output/platform-overzicht.html](../output/platform-overzicht.html)

## Doel

Levend operationeel overzicht: componentdiagram, lokale dev-setup, Ollama op `.15`, Cloudflare, deploy. Bedoeld voor operators — niet voor agent-beleid.

## Secties (verplicht)

1. **Overzicht** — UI, FastAPI, Chroma, Ollama, ingestion
2. **Architectuur** — ADRs + productiehost
3. **Platform starten** — venv, ingest, `run_api.py`, env vars (Ollama)
4. **Deployment** — ADR-009 + `infra/runbooks/deployment.md` + `.15`

## Bij elke update controleren

- Paden naar `core-domain/` en `infra/` kloppen (vanuit `output/`: `../../` en `../../../../`).
- Poorten en endpoints consistent met `infra/runbooks/infrastructure.md`.
- Geen nieuwe **beslissingen** in HTML — die horen in een ADR.
- Designer Agent / harnessing: verwijs naar `context-space/harnessing/`.

## Styling

- Tailwind via CDN (consistent met `technisch-design.html` en Sogyo-kleuren `#003366`).
- Geen externe frameworks beyond Tailwind CDN.