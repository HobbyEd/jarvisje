# Runbook: App Deployment (Image + Compose)

**Type:** Runbook (Actualization Space)  
**Beslissing:** [ADR-009](../../context-space/core-domain/02-architectural/decisions/09-ADR-image-compose-deployment.md)  
**Productiehost:** `evdillen@192.168.165.15`  
**Compose (productie):** `infra/ubuntu-x64/docker-compose.prod-local.yaml`  
**Laatst bijgewerkt:** 2026-08-08

---

## 1. Architectuur (deploy)

- **Immutable image:** `sogyo-chatbot:<tag>` (app + deps + preloaded BGE-M3).
- **Mutable data:** host `/home/evdillen/sogyo-chatbot-data` (Chroma, raw).
- **LLM:** aparte compose-service `ollama` (niet in de app-image); model in `~/sogyo-ollama`.
- **LLM-config via env** in compose: `LLM_BASE_URL`, `LLM_MODEL`, `EMBEDDING_DEVICE`.

Productiestack start via **systemd** (`sogyo-ollama` + `sogyo-chatbot`), niet handmatig elke boot.

---

## 2. Deployment flow

### A. Build op de productieserver (aanbevolen vanaf Mac arm64)

De productie-host is **amd64**. Bouwen op de server vermijdt cross-arch issues.

```bash
ssh evdillen@192.168.165.15
# source in ~/sogyo-chatbot/build-src of rsync verse code
cd ~/sogyo-chatbot/build-src
docker build -t sogyo-chatbot:latest -f Dockerfile .
cd ~/sogyo-chatbot
# compose gebruikt IMAGE_TAG=latest
sudo systemctl restart sogyo-chatbot
# of: IMAGE_TAG=latest docker compose up -d app
```

### B. Build lokaal + transfer (Windows/amd64 of buildx)

```powershell
pwsh -ExecutionPolicy Bypass -File infra/ubuntu-x64/build-local-image.ps1
pwsh -ExecutionPolicy Bypass -File infra/ubuntu-x64/deploy.ps1
# Default server: evdillen@192.168.165.15
```

Op de server laadt `server-deploy.sh` de tarball en start compose (app).  
Zorg dat **`docker-compose.prod-local.yaml`** als `~/sogyo-chatbot/docker-compose.yaml` staat (ollama + app + juiste env).

### C. Alleen compose/env wijzigen

```bash
# na scp van bijgewerkte docker-compose.yaml
cd ~/sogyo-chatbot
docker compose up -d
# of per service via systemd:
sudo systemctl restart sogyo-ollama
sudo systemctl restart sogyo-chatbot
```

---

## 3. Productie compose (samenvatting)

Bestand: `infra/ubuntu-x64/docker-compose.prod-local.yaml`

| Service | Image | Host-poort | GPU |
|---------|-------|------------|-----|
| `ollama` | `ollama/ollama` | 11434 | ja (runtime nvidia) |
| `app` | `sogyo-chatbot:latest` | 8080→8001 | nee (embeddings CPU) |

Belangrijke env app:

- `LLM_BASE_URL=http://ollama:11434/v1`
- `LLM_MODEL=gemma3:4b`
- `EMBEDDING_DEVICE=cpu`

Eerste model-pull (eenmalig):

```bash
docker exec sogyo-ollama ollama pull gemma3:4b
```

---

## 4. Image-ontwerp

- Base: `python:3.12-slim`
- Torch CUDA wheels in image (voor toekomstige GPU-embeddings)
- `PYTHONPATH=/app/src`
- LLM-URL **niet** hard coded als enige optie — runtime env wint
- Image bevat **geen** Chroma-data
- Tagging: `sogyo-chatbot:latest` + optioneel git-SHA

---

## 5. Directory layout (server)

```
/home/evdillen/
├── sogyo-chatbot/
│   ├── docker-compose.yaml      # prod-local stack
│   ├── build-src/               # optioneel: on-server builds
│   └── deploy-artifacts/        # tarballs bij rsync-deploy
├── sogyo-chatbot-data/          # persistent app data
│   ├── chroma/
│   └── raw/
└── sogyo-ollama/                # Ollama model store
```

---

## 6. Data-persistentie & backup

- Host data: `/home/evdillen/sogyo-chatbot-data`
- Backup: `tar`/`rsync` van die map (+ eventueel `sogyo-ollama` voor model-cache)
- Image update raakt data niet als volume gelijk blijft

---

## 7. Update & rollback

**Update app**

1. Nieuw image (`latest` of tagged)
2. `docker compose up -d app` of `systemctl restart sogyo-chatbot`
3. `curl -s http://127.0.0.1:8080/health` en https://jarvisje.com/health

**Rollback**

```bash
docker tag sogyo-chatbot:<oude-tag> sogyo-chatbot:latest
# of: IMAGE_TAG=<oude-tag> docker compose up -d app
sudo systemctl restart sogyo-chatbot
```

**Cloudflare tunnel** hoeft bij app-image updates **niet** te wijzigen.

---

## 8. Smoke checklist na deploy

```bash
systemctl is-active sogyo-ollama sogyo-chatbot cloudflared
docker ps --filter name=sogyo
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:11434/api/tags
curl -s https://jarvisje.com/health
# optioneel chat:
curl -sN -X POST http://127.0.0.1:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Wat is Sogyo?"}' | head
```

---

## 9. Open punten

1. Automatische nightly ingest
2. PyTorch upgrade voor GPU-embeddings op Blackwell
3. Optionele CI image-build (amd64) + registry

Laatst bijgewerkt: 2026-08-08
