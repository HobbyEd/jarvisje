# Context Space Update Log

## 2026-08-08

* **Productie-migratie**: app-host van `.10` naar **`192.168.165.15`** (enterprise); lokaal **Ollama gemma3:4b**; Cloudflare Tunnel **jarvisje.com**; systemd `sogyo-ollama` + `sogyo-chatbot` + `cloudflared`.
* **Docs**: README, development-setup, infra runbooks, ubuntu-x64 README, ADR-004/009; UI; config → Ollama.
* **Opschoning**: verwijderd `actualization/`, `infra/dgx-arm64/`, legacy compose, proxy-script, agent-stubs; projecties; UI **v0.6.2**.
* **Lean A–E**: weg `terminals/`, redirect-stubs, lege `tests/`; roadmap → `04-delivery/roadmap.md`; `scripts/deploy-to-15.sh` + `smoke_health.py`; UI **v0.6.3**.

## 2026-07-05

* **Migration (Fase 4–5)**: `projections/` met output HTML + generatieregels; `harnessing/findings/` (34 archief); Designer Agent → harnessing + OKF frontmatter op nieuwe findings.
* **Migration (Fase 2)**: `core-domain/` met 01-strategic t/m 04-delivery; nieuwe artefacten bounded-contexts, context-map, ubiquitous-language, kennisbronnen, use-cases; OKF-frontmatter op ADRs en kernconcepten; Designer Agent ADR-pad bijgewerkt.
* **Migration (Fase 0–1)**: Context Space opgeschoond volgens augmentedengineering.nl + OKF-voorbereiding.
* **Creation**: `index.md`, `log.md`, `MIGRATIE-VOORSTEL.md`.
* **Move**: `vllm-model/` → `infra/vllm-model/`.
* **Move**: `infrastructure.md` → `infra/runbooks/infrastructure.md`.
* **Split**: `design-deployment.md` → ADR-009 + `infra/runbooks/deployment.md`.
* **Move**: `overdracht.md` → `actualization/sessions/2026-06-27-overdracht.md`.
* **Update**: `werkwijze.md` — regel context vs. actualization.

## 2026-06-27

* **Creation**: `design-deployment.md`, `overdracht.md`, uitgebreide `infrastructure.md`.
* **Update**: Designer Agent tech-debt pipeline actief.

## 2026-06-26

* **Initialization**: MVP scope, roadmap, ADRs 01–08, `werkwijze.md`, `aannames.md`.