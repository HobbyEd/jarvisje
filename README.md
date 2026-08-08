# Sogyo Kennis Chatbot (MVP)

> [!IMPORTANT]
> **Aandacht AI-agents / Coders (Cursor, Claude, Grok, Gemini, etc.):**
> Projectregels staan in **[AGENTS.md](AGENTS.md)** (en [CLAUDE.md](CLAUDE.md) voor Claude Code).
> Voordat je iets doet, lees met de file-tool:
> - [context-space/index.md](context-space/index.md)
> - [werkwijze.md](context-space/core-domain/04-delivery/werkwijze.md)
>
> Per stap: commit, designer agent, projecties, UI-versie, ADR-check — zie AGENTS.md + werkwijze.

Domein-specifieke RAG-chatbot voor Sogyo en gerelateerde content.

**Doel (MVP)**  
Natuurlijke gesprekken voeren binnen het software engineering + engineer development domein, altijd met concrete citations naar de 6 bronnen.

## Productie (actueel)

| Item | Waarde |
|------|--------|
| **Publiek** | https://jarvisje.com (Cloudflare Tunnel) |
| **LAN** | http://192.168.165.15:8080 |
| **Host** | `evdillen@192.168.165.15` (hostname `enterprise`, Ubuntu 26.04) |
| **GPU** | NVIDIA RTX 5060 Ti 16 GB |
| **LLM** | Ollama `gemma3:4b` (lokaal, OpenAI-compatible op `:11434`) |
| **Embeddings** | BGE-M3 (CPU; Blackwell sm_120 nog niet in PyTorch 2.6+cu124) |
| **Stack** | Docker Compose: `ollama` + `app` |
| **Boot** | systemd: `sogyo-ollama`, `sogyo-chatbot`, `cloudflared` |

```
Browser → Cloudflare (jarvisje.com)
            → cloudflared (host)
              → :8080 → sogyo-chatbot-app
                          ├─ BGE-M3 + Chroma (data volume)
                          └─ LLM → ollama:11434 (gemma3:4b op GPU)
```

Operationeel: [infra/runbooks/infrastructure.md](infra/runbooks/infrastructure.md), [infra/runbooks/deployment.md](infra/runbooks/deployment.md), [infra/ubuntu-x64/README.md](infra/ubuntu-x64/README.md).

## Projectstructuur

```
.
├── context-space/          # Scope, ADRs, werkwijze — start voor AI-agents
├── src/sogyo_chatbot/      # Python package (API, chat, ingestion, retrieval)
├── scripts/                # run_api, ingest, deploy-to-15.sh, smoke_health
├── web/                    # UI (geserveerd door FastAPI)
├── infra/
│   ├── ubuntu-x64/         # Productie .15 (compose, Dockerfile, PS1 helpers)
│   └── runbooks/
└── requirements.txt
```

**Deploy (lean):** `./scripts/deploy-to-15.sh` (build op server, geen sudo).

## Snel starten (lokaal)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Secrets (ADR-011) — never commit .env
cp .env.example .env
# Zet in .env:  INGEST_TOKEN=<lang-willekeurig-secret>
# Nodig om indexering via UI/API te starten.

# LLM: productieserver Ollama of andere OpenAI-compatible endpoint
export LLM_BASE_URL=http://192.168.165.15:11434/v1
export LLM_MODEL=gemma3:4b
export EMBEDDING_DEVICE=cpu

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
- sogyo.nl  
- jeroenteunisse.nl  
- edwinvandillen.nl  
- augmentedorganisation.nl  
- intentdriven.nl  
- augmentedengineering.nl  

## Status
Productie op `.15` met lokaal Gemma 3 4B + Cloudflare. Indexering via UI; embeddings op CPU tot PyTorch Blackwell-support.

Laatst bijgewerkt: 2026-08-08
