# Context Space Update Log

## 2026-09-15

* **Uitlegpagina gebouwd:** tab *Hoe Jarvisje werkt* vervangt Chatbot Opbouw — zeven blokken, drie CSS-tekeningen, walker, live artikel-aantal. Mermaid verwijderd. UI **v1.1.0**.

## 2026-09-14

* **Host-identiteit uit git:** `DEPLOY_USER`, `DEPLOY_HOST`, `HOST_HOME` in `.env` / `.env.example`. Geen SSH-user of LAN-IP meer in bron/docs. UI **v1.0.9**.
* **Opruimen:** weg `open-beslissingen.md`, `cutover-dirs-on-15.sh`, oude `deploy-artifacts` tarballs; harnessing-index ingekort. vLLM/GB10 uit huidige technisch-design, werkwijze, orchestrator. Roadmap: herindexering af. UI **v1.0.8**.
* **Uitlegpagina (voorstel):** [pagina-hoe-jarvisje-werkt.md](core-domain/04-delivery/pagina-hoe-jarvisje-werkt.md) — inhoudelijke opzet voor vervanging van de tab Chatbot Opbouw; nog niet gebouwd. UI **v1.0.7**.
* **Deploy-descriptors = live:** hostpaden `~/jarvisje-chatbot` + `~/jarvisje-chatbot-data`, image `jarvisje`, container `jarvisje-chatbot-app`. Compose-projectnaam en Ollama blijven `sogyo-*` (Gemma-netwerk). Systemd-unitnamen blijven `sogyo-*` tot sudo-rename; WorkingDirectory → jarvisje.
* **Geen DGX-deploy:** NVIDIA Spark DGX `<legacy-host>` / vLLM uit aannames, ADR-004 current-status, software-design, runbooks. ADR-005 blijft historisch/superseded.

## 2026-08-08

* **Incrementele indexering**: zonder reset alleen nieuw/gewijzigd (sitemap lastmod vs Chroma); reset = full rebuild; UI **v0.8.1**.
* **ADR-011**: secrets policy — geen tokens in git/image; `.env` + `INGEST_TOKEN`; deploy scp host-`.env`; UI **v0.8.0**.
* **ADR review**: 01–09 reality-check; **ADR-010** async ingestion worker.
* **ADR-010 implementatie**: `ingestion/worker.py` + status files; API spawn i.p.v. in-process; UI banner; CLI `scripts/ingest.py` → worker; UI **v0.7.0**.
* **Productie-migratie**: app-host van `.10` naar **`<host>`** ; lokaal **Ollama gemma3:4b**; Cloudflare Tunnel **jarvisje.com**; systemd `sogyo-ollama` + `sogyo-chatbot` + `cloudflared`.
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