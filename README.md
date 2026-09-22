# Jarvisje

> [!IMPORTANT]
> **Aandacht AI-agents / Coders (Cursor, Claude, Grok, Gemini, etc.):**
> Projectregels staan in **[AGENTS.md](AGENTS.md)** (en [CLAUDE.md](CLAUDE.md) voor Claude Code).
> Voordat je iets doet, lees met de file-tool:
> - [context-space/index.md](context-space/index.md)
> - [werkwijze.md](context-space/core-domain/04-delivery/werkwijze.md)
>
> Per stap: commit, designer agent, projecties, UI-versie, ADR-check — zie AGENTS.md + werkwijze.

Domein-specifieke RAG-chatbot rondom de wereld van AI. Kennis alleen uit [edwinvandillen.nl](https://edwinvandillen.nl/) en [jeroenteunisse.nl](https://jeroenteunisse.nl/). Embed op de blog; beheer op https://jarvisje.com.

**Doel (MVP)**  
Natuurlijke gesprekken voeren, altijd met concrete citations naar die twee blogs.

## Productie (actueel)

| Item | Waarde |
|------|--------|
| **Publiek** | https://jarvisje.com (Cloudflare Tunnel) |
| **LAN / SSH** | `DEPLOY_HOST` / `DEPLOY_USER` in gitignored `.env` |
| **GPU** | NVIDIA RTX 5060 Ti 16 GB |
| **LLM** | Ollama `gemma3:4b` (lokaal, OpenAI-compatible op `:11434`) |
| **Embeddings** | BGE-M3 (vraag op CPU, indexeren op GPU; torch 2.11+cu128, sm_120) |
| **Stack** | Docker Compose: `ollama` + `app` |
| **Image / app** | `jarvisje:<tag>` / container `jarvisje-chatbot-app` |
| **Paden** | `~/jarvisje-chatbot`, `~/jarvisje-chatbot-data` |
| **Boot** | systemd: `sogyo-ollama`, `sogyo-chatbot`, `cloudflared` |

```
Browser → Cloudflare (jarvisje.com)
            → cloudflared (host)
              → :8080 → jarvisje-chatbot-app
                          ├─ BGE-M3 + Chroma (data volume)
                          └─ LLM → ollama:11434 (gemma3:4b op GPU)
```

Ollama-container en compose-project heten nog `sogyo-ollama` / `sogyo-chatbot` zodat het bestaande Docker-netwerk van Gemma intact blijft.

Operationeel: [infra/runbooks/infrastructure.md](infra/runbooks/infrastructure.md), [infra/runbooks/deployment.md](infra/runbooks/deployment.md), [infra/ubuntu-x64/README.md](infra/ubuntu-x64/README.md).

## Projectstructuur

```
.
├── context-space/          # Scope, ADRs, werkwijze — start voor AI-agents
├── src/jarvisje/           # Python package (API, chat, ingestion, retrieval)
├── scripts/                # run_api, ingest, deploy-to-15.sh, smoke_health
├── web/                    # UI (geserveerd door FastAPI)
├── infra/
│   ├── ubuntu-x64/         # Productie (compose, Dockerfile, PS1 helpers)
│   └── runbooks/
└── requirements.txt
```

**Deploy (lean):** `./scripts/deploy-to-15.sh` (build op server, geen sudo).

## Snel starten (lokaal)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Secrets + host (ADR-011) — never commit .env
cp .env.example .env
# Zet o.a.: INGEST_TOKEN, DEPLOY_USER, DEPLOY_HOST, HOST_HOME
# LLM: optioneel LLM_BASE_URL=http://$DEPLOY_HOST:11434/v1 in .env

python scripts/run_api.py
# → http://localhost:8001
```

Volledige dev-cyclus: [development-setup.md](development-setup.md).  
Secrets-beleid: [ADR-011](context-space/core-domain/02-architectural/decisions/11-ADR-secrets-handling.md).

**UI:** tab **Bronnen & Meta-data** voor indexering (voortgang live). Vul het **zelfde** token als `INGEST_TOKEN` in `.env`.

## AI-agents & werkwijze

Werkwijze en domeinkennis staan in **`context-space/`**. Start met [`context-space/index.md`](context-space/index.md).

## Principes
- Lightweight: pure Python + minimale deps (geen LangChain/LlamaIndex)
- Retrieval-only + citations verplicht
- Lokaal-first (Ollama + Chroma op de app-host)
- Software Designer Agent bewaakt complexiteit

## Bronnen (MVP)
- edwinvandillen.nl  
- jeroenteunisse.nl  

## Status
Productie met lokaal Gemma 3 4B + Cloudflare. Indexering via UI op de GPU; vraag-embeddings op CPU. Host-identiteit staat in `.env`.

Laatst bijgewerkt: 2026-09-22
