---
type: ADR
title: "Secrets & security guidelines"
description: "Geen secrets in git/image; .env lokaal + host; rotatie bij lek."
status: accepted
tags: [security, secrets, env, ingest-token]
timestamp: 2026-08-08T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
  - /core-domain/02-architectural/decisions/09-ADR-image-compose-deployment.md
  - /core-domain/02-architectural/decisions/10-ADR-async-ingestion-worker.md
  - /core-domain/04-delivery/werkwijze.md
---

# ADR-011: Secrets handling & security guidelines

## Status
Accepted

## Datum
2026-08-08

## Context

De chatbot is (deels) publiek bereikbaar (`jarvisje.com`). Beheerdersacties zoals **indexering starten/stoppen** zijn beschermd met een shared secret (ingest/index-token).

Incident: een default `INGEST_TOKEN` stond **hardcoded in broncode** (`config.py`) en is daarmee in de git-geschiedenis terechtgekomen. Iedereen met repo-toegang kon theoretisch indexering starten via de publieke API.

Dat schendt fundamentele securityhygiëne en is onacceptabel, ook voor een MVP.

### Eisen
1. **Geen secrets in git** (bron, docs, commits, voorbeelden met echte waarden).
2. **Geen secrets in container images** (Dockerfile mag `.env` niet `COPY`-en).
3. Lokaal en op de server: secrets via **omgevingsvariabelen** / **`.env` buiten de image**.
4. Duidelijke agent- en developer-richtlijnen (voorkomen herhaling).
5. Bij lek: **roteren** van het secret; optioneel history-rewrite is out of band.

## Decision

### 1. Secrets policy (normatief)

| Mag wel | Mag niet |
|---------|----------|
| `.env` op developer machine (gitignored) | Secrets in `src/`, `web/`, ADRs, README, scripts |
| `.env` op de app-host naast compose (mode `600`) | Default-waarden met echte tokens in code |
| `.env.example` met **placeholders** | `.env` in Docker image layers |
| Env vars via compose `env_file` / `environment` | Tokens in UI-HTML hardcoden of in git hooks logs |
| Documentatie: *welke* keys bestaan | Documentatie: *echte* key-waarden |

### 2. Ingest / index-token

- Server-side verwachte waarde komt **uitsluitend** uit environment:
  - primair: `INGEST_TOKEN`
  - alias: `INDEX_TOKEN` (zelfde betekenis)
- Geen fallback-default in code. Ontbreekt het token → start/stop indexering **weigert** (401 / “niet geconfigureerd”).
- Client (browser) stuurt het token mee in `POST /ingest/start|stop` (gebruiker vult het in of gebruikt lokale wachtwoordmanager). Het token hoort **niet** in de statische frontend.
- CLI/cron op de host heeft **geen** publieke token nodig (worker-entrypoint lokaal); token blijft voor de **HTTP-API**.

### 3. `.env` lifecycle

**Lokaal (repo-root):**

```bash
cp .env.example .env
# vul INGEST_TOKEN=... (sterk, uniek secret)
```

App laadt `.env` via `python-dotenv` bij start (`config.py`), daarna `os.environ`.

**Productie (`.15`):**

- Bestand: `/home/evdillen/sogyo-chatbot/.env` (naast `docker-compose.yaml`)
- Rechten: eigenaar `evdillen` (of root), mode **`600`**
- Compose: `env_file: .env` op de `app`-service (injecteert in container-proces, niet in image)
- Deploy-script (`scripts/deploy-to-15.sh`) kopieert **alleen** een lokaal bestaande `.env` via `scp` naar die host-locatie — **niet** via rsync van de build-context, **niet** in de Docker build

### 4. Git & tooling

- `.gitignore` bevat `.env` en `.env.*`, met uitzondering `!.env.example`
- Agents en mensen: **nooit** gevraagde secrets echoën in commits, PR’s, of ADR-body
- Pre-commit / review: zoek naar JWT-achtige prefixes (`eyJ…`), `password=`, `TOKEN=` met lange waarden in tracked files

### 5. Rotatie bij lek

1. Genereer nieuw token (lang, willekeurig).
2. Zet in lokale `.env` en server-`.env`.
3. Herstart/recreate app-container.
4. Behandel oude token als gecompromitteerd (git history kan het nog bevatten).
5. Optioneel: history rewrite / secret scanning — niet verplicht voor MVP, wel documenteren.

### 6. Overige secrets (zelfde patroon)

- Cloudflare tunnel token: blijft op host onder `/etc/cloudflared/` (root-only) — niet in deze repo.
- Toekomstige API-keys (LLM cloud, etc.): alleen env / host secret store, zelfde ADR-regels.

## Consequences

### Positief
- Gepubliceerde repo lekt geen start-rechten voor indexering.
- Images zijn herbruikbaar/shareable zonder ingebakken credentials.
- Één duidelijk contract voor agents: secrets = `.env` / host, nooit source defaults.

### Negatief / aandacht
- Nieuwe omgevingen starten niet “out of the box” met ingest: `.env` is verplicht voor UI-indexering.
- Deploy faalt of waarschuwt zonder lokale `.env` (bewust).
- Oude commits kunnen historical secrets bevatten → rotatie is de snelle mitigatie.

## Alternatives Considered

| Alternatief | Oordeel |
|-------------|---------|
| Hardcoded default “alleen voor demo” | Verworpen — eindigt in publieke git. |
| Secret alleen in Docker secrets/Swarm | Overkill voor huidige single-host compose. |
| Basic auth op hele app | Later optioneel; lost token-in-git niet op. |

## Implementation notes

1. `config.py`: `load_dotenv` + `INGEST_TOKEN`/`INDEX_TOKEN`, lege default.
2. `.env.example` met `INGEST_TOKEN=` placeholder.
3. Compose `env_file: .env` voor `app`.
4. `deploy-to-15.sh`: scp `.env` → host, `chmod 600`.
5. Docs: README, development-setup, infra README, AGENTS.md.
6. Version bump bij doorvoeren; UI-badge.

## Gerelateerde ADRs
- ADR-009 Image + Compose Deployment  
- ADR-010 Async Ingestion Worker  
- ADR-002 Guardrails (inhoudelijk; dit ADR is operationele security)

## Besloten door
Edwin + architectuur review (na lek van hardcoded ingest token)
