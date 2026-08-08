# Agent instructions — Sogyo Kennis Chatbot

These rules apply to **every** AI coding agent working in this repository
(Grok Build, Claude Code, Cursor, Codex, Gemini, …).

## Mandatory before any work

**Do not start coding, editing docs, deploying, or planning until you have actually read these files with your file-reading tool** (not from memory):

1. [`context-space/index.md`](context-space/index.md) — entry to the Context Space  
2. [`context-space/core-domain/04-delivery/werkwijze.md`](context-space/core-domain/04-delivery/werkwijze.md) — **binding process for every step**

The README “IMPORTANT” banner is not a substitute for reading `werkwijze.md`.

## Process for every step

Repeat for **each** discrete change (code, docs, infra, UI):

1. **Read** `werkwijze.md` again with the read tool.  
2. **Execute** the step.  
3. **After the step**, complete all of:
   - **Git commit** — small, step-oriented message (Dutch or English, clear).  
   - **Software Designer Agent** — run and verify findings under `context-space/harnessing/findings/`:
     ```bash
     PYTHONPATH=src python -m sogyo_chatbot.designer.cli
     # Windows PowerShell:
     # $env:PYTHONPATH="src"; python -m sogyo_chatbot.designer.cli
     ```
   - **Projections** — update `context-space/projections/output/` when architecture, start instructions, or platform overview change (see `context-space/projections/generation-rules.md`).  
   - **UI version** — bump badge in `web/index.html` (semver: patch/minor/major as appropriate; current line is like `v0.8.0`).
   - **ADR check** — if architecture, deployment, guardrails, inference, or fundamentals change: create or update an ADR under `context-space/core-domain/02-architectural/decisions/`.

If you skip any of these, say so explicitly to the user and offer to catch up.

## Spaces (do not mix)

| Space | Path | Contains |
|-------|------|----------|
| Context | `context-space/core-domain/` | What & why (vision, ADRs, werkwijze) |
| Software | `src/`, `web/`, `scripts/` | Implementation |
| Actualization | `infra/` | Deploy scripts, runbooks, compose |

## Project principles

- Lightweight: pure Python where possible; no unnecessary frameworks.  
- Structured LLM output via Pydantic.  
- Production host: `192.168.165.15` — see `infra/runbooks/infrastructure.md` and `README.md`.  
- **Secrets (ADR-011):** never hardcode tokens/passwords in source, docs, or commits. Use gitignored `.env` (`INGEST_TOKEN=…` for indexering). Ship host-`.env` via deploy, not the Docker image. See `.env.example` and `decisions/11-ADR-secrets-handling.md`.

## Quick pointers

- Local dev: `development-setup.md`  
- Deploy (lean): `./scripts/deploy-to-15.sh`  
- Ops: `infra/ubuntu-x64/README.md`, `infra/runbooks/`  
- Production compose: `infra/ubuntu-x64/docker-compose.prod-local.yaml`
