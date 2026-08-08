# Development Setup — Sogyo Chatbot MVP

Lokale ontwikkeling en testen. Productie-details: [infra/runbooks/infrastructure.md](infra/runbooks/infrastructure.md).

## Snelle ontwikkel- & testcyclus

Docker image build + transfer is **traag** (ML-deps). Gebruik een tiered aanpak:

1. **Dagelijkse dev: lokaal Python** — `python scripts/run_api.py` met LLM naar Ollama op `.15` (of andere endpoint).
2. **Container-validatie** — alleen bij Dockerfile/web-serving/paden.
3. **Server deploy** — alleen stabiele releases (`infra/ubuntu-x64/`).

### Lokale Python (aanbevolen)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Productie-Ollama op .15 (LAN)
export LLM_BASE_URL=http://192.168.165.15:11434/v1
export LLM_MODEL=gemma3:4b
export EMBEDDING_DEVICE=cpu
export LLM_TIMEOUT=180

python scripts/run_api.py
```

Open http://localhost:8001

**Alternatief — LLM op je eigen machine** (als je lokaal Ollama draait):

```bash
export LLM_BASE_URL=http://127.0.0.1:11434/v1
export LLM_MODEL=gemma3:4b
```

### Lokale Docker-test

```bash
docker build -f infra/ubuntu-x64/Dockerfile -t sogyo-chatbot:local-test .

docker run --rm -p 8080:8001 \
  -e LLM_BASE_URL=http://192.168.165.15:11434/v1 \
  -e LLM_MODEL=gemma3:4b \
  -e EMBEDDING_DEVICE=cpu \
  --name sogyo-test sogyo-chatbot:local-test
```

Open http://localhost:8080  
Stop: Ctrl+C of `docker rm -f sogyo-test`.

> Op Apple Silicon: build is arm64; productie-host is **amd64**. Voor image-pariteit: build op de server of `docker buildx --platform linux/amd64`.

### Indexering via de web UI

1. Start app (lokaal of productie).
2. Tab **Bronnen & Meta-data**.
3. Max pagina’s / Reset naar wens.
4. **Start indexering** — progress live.
5. Tabel ververst na afronding.

### Wanneer image rebuilden + deployen?

- Wijzigingen aan Dockerfile, requirements, of packaging.
- Stabiele release naar productie `.15`.

Niet bij elke UI/API-regelwijziging tijdens lokale Python-dev.

## Vereisten

- Python 3.10+ (3.12 zoals in de image)
- Git
- Optioneel: Docker (container-test / deploy)
- LAN-toegang tot `192.168.165.15` voor productiemodel

## Projectstructuur

```
sogyo-chatbot/
├── context-space/
├── src/sogyo_chatbot/
│   ├── api/           # FastAPI + UI serve
│   ├── chat/          # Orchestrator, prompts
│   ├── ingestion/     # Scrape, chunk, embed, chroma
│   └── retrieval/
├── scripts/
├── web/
├── infra/ubuntu-x64/  # Productie
├── data/              # gitignored
├── requirements.txt
└── development-setup.md
```

## Installatie

```bash
pip install --upgrade pip
pip install -r requirements.txt
# of: pip install -e ".[dev]"
```

## Ingest (CLI)

```bash
python scripts/ingest.py
python scripts/ingest.py --max 30
python scripts/ingest.py --reset
```

## Retrieval smoke test

```python
from sogyo_chatbot.retrieval import retrieve

results = retrieve("Hoe werkt intent-driven development?", top_k=5)
for r in results:
    print(r["metadata"]["title"], r["metadata"]["url"])
    print(r["text"][:200], "...\n")
```

## Tips

- `EMBEDDING_DEVICE=cpu` op productie (Blackwell); lokaal mag `cuda` als je GPU + passende torch hebt.
- Ingest blokkeert de event loop deels — health kan tijdens zware scrape traag zijn.
- `data/raw/` en `data/chroma/` voor debugging; op server: `/home/evdillen/sogyo-chatbot-data`.

## Modelkeuzes (productie)

| Rol | Model | Waar |
|-----|--------|------|
| LLM | `gemma3:4b` (Ollama Q4) | Host `.15`, GPU |
| Embeddings | `BAAI/bge-m3` | App-container, CPU |

Laatst bijgewerkt: 2026-08-08
