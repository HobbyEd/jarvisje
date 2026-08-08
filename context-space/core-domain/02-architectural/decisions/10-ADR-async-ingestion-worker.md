---
type: ADR
title: "Asynchrone ingestion worker"
description: "Indexering buiten het chat-API-proces; status deelbaar; cron-klaar."
status: accepted
tags: [ingestion, async, worker, availability]
timestamp: 2026-08-08T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
  - /core-domain/02-architectural/decisions/07-ADR-ingestion-cadence.md
  - /core-domain/02-architectural/decisions/09-ADR-image-compose-deployment.md
---

# ADR-010: Asynchronous Ingestion Worker

## Status
Accepted

## Datum
2026-08-08

## Context

### Probleem
Indexering (scrape → chunk → embed → Chroma) is CPU- en I/O-intensief. In de huidige implementatie draait dit als **background task in hetzelfde FastAPI-proces** als de chatbot (`BackgroundTasks` + gedeelde event loop / GIL / zware embedding).

Gevolg in productie:

- Tijdens indexeren reageert de app slecht of helemaal niet (health/chat time-outs).
- Chat en ingest concurreren om één process en om BGE-M3/Chroma.
- UI-feedback hangt af van in-memory state die met de app-process meevalt.

### Eisen
1. **Chat blijft beschikbaar** terwijl indexering loopt (of degradeert alleen mild, niet “plat”).
2. Indexering is startbaar via **UI/API (token)** en later via **cron/systemd timer** zonder code-fork.
3. Status van de run is **zichtbaar** in de web-UI (minimaal: “indexer draait in de achtergrond”).
4. Zelfde data-volume en embedding-model als nu (`sogyo-chatbot-data`, BGE-M3).
5. Lightweight: geen zwaar message-bus product tenzij later nodig.

Gerelateerd: [ADR-007](07-ADR-ingestion-cadence.md) (wanneer), [ADR-009](09-ADR-image-compose-deployment.md) (waar/deploy).

## Decision

We scheiden **chat-API** en **ingestion worker** in **aparte processen** (en bij voorkeur aparte containers in compose).

### 1. Twee rollen

| Rol | Verantwoordelijkheid | Voorbeeld runtime |
|-----|----------------------|-------------------|
| **API (chat)** | UI, `/chat`, `/sources` (read), lichte status-read | `sogyo-chatbot-app` |
| **Worker (ingest)** | scrape/embed/upsert; schrijft status | CLI-module of `sogyo-ingest` service |

De worker deelt **geen** Python-proces met de API. Wel:

- **Zelfde image** mag (entrypoint verschilt), of dunne hergebruik van `src/sogyo_chatbot/ingestion/`.
- **Zelfde volume** voor Chroma/raw (`/home/evdillen/sogyo-chatbot-data`).
- **Status-bestand** (of kleine state store) op het volume of een afgesproken pad, leesbaar door de API.

### 2. Startpaden (één contract)

Alle starts roepen **dezelfde worker entrypoint** aan, bijv.:

```text
python -m sogyo_chatbot.ingestion.worker --max-pages N [--reset]
```

| Trigger | Mechanisme |
|---------|------------|
| UI / `POST /ingest/start` | API **spawn** of **enqueue** (subprocess / `docker compose run` / HTTP naar worker) — **niet** zwaar werk in de request-thread |
| CLI handmatig | Zelfde entrypoint |
| Cron / systemd timer | Zelfde entrypoint |

Token-check blijft op de **API-start** (en optioneel op een interne worker-HTTP); cron gebruikt lokale/system credentials, geen publieke token in crontab.

### 3. Status & UI

- Worker schrijft periodiek status (JSON): `status`, `progress`, `message`, `current_source`, `started_at`, `finished_at`, `pages_scraped`, `chunks_indexed`, `pid`/`run_id`.
- API leest dit via `GET /ingest/status` (file of shared store) — **read-only**, geen blocking compute.
- UI: duidelijke indicator “Indexering loopt op de achtergrond” (banner of bestaande progress-widget), ook op de chat-tab (luxe eis).

### 4. Concurrency & Chroma

- **Eén actieve ingest-run** tegelijk (lock-file of status=running).
- Chat mag Chroma **lezen** tijdens upsert; korte inconsistenties (halverwege update) zijn acceptabel voor MVP.
- Optioneel later: write-side queue of “rebuild side collection + swap” — **niet** in v1 van deze ADR.

### 5. Resource-isolatie (aanbevolen)

In Docker Compose:

- Service `app`: geen zware ingest in-process.
- Service `ingest` (profile of one-shot): CPU-limiet, zelfde volume, `restart: "no"` voor one-shot of dedicated worker die jobs pakt.

Cron kan `docker compose run --rm ingest ...` of host-venv worker tegen het data-volume.

### 6. Expliciet out of scope (deze ADR)

- Distributed queue (Celery/RQ/Kafka)
- Multi-worker parallel scrape over meerdere machines
- Zero-downtime blue/green van de vector index

## Consequences

### Positief
- Chat blijft bruikbaar tijdens (her)indexering.
- Zelfde worker voor UI-start en cron → minder duale code.
- Duidelijke operationele grens (logs, restart, resource limits per service).
- Past bij ADR-007 (cadans) zonder de API te gijzelen.

### Negatief / aandachtspunten
- Extra proces/container en status-contract te onderhouden.
- Chroma concurrent read/write vereist aandacht (één writer).
- Embeddings CPU + Ollama GPU op één host: worker mag LLM niet “verhongeren” (CPU-shares / nice).
- API mag niet per ongeluk weer zware ingest in-process doen (guard in code reviews).

## Alternatives Considered

| Alternatief | Oordeel |
|-------------|---------|
| **FastAPI BackgroundTasks (huidig)** | Blokkeert/platlegt service → verworpen als structureel model. |
| **Threading in-process** | GIL + shared embedder; chat blijft riskant → onvoldoende. |
| **Celery/Redis** | Te zwaar voor huidige schaal; later optioneel. |
| **Apart VM/host alleen voor ingest** | Overkill nu; architectuur verbiedt het niet later. |

## Implementation notes (richting, geen verplicht detail)

1. Extract pure pipeline uit `app.py` naar `ingestion/worker.py` (of hergebruik `scripts/ingest.py` + status writer).
2. Status: bijv. `{data}/ingest_status.json` + lock `{data}/ingest.lock`.
3. `POST /ingest/start`: valideer token → start worker → return 202.
4. `GET /ingest/status`: lees status file.
5. UI: poll status; toon banner op chat + bronnen-tab.
6. Cron voorbeeld: `0 */6 * * * docker compose run --rm ingest python -m sogyo_chatbot.ingestion.worker`

## Gerelateerde ADRs
- ADR-001 Knowledge Strategy  
- ADR-007 Ingestion Cadence  
- ADR-009 Image + Compose Deployment  

## Besloten door
Edwin + architectuur review (async indexeringseisen)
