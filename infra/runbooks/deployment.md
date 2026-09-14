# Runbook: App Deployment (Image + Compose)

**Type:** Runbook (Actualization Space)  
**Beslissing:** [ADR-009](../../context-space/core-domain/02-architectural/decisions/09-ADR-image-compose-deployment.md)  
**Productiehost:** `<user>@<host>`  
**Compose (productie):** `infra/ubuntu-x64/docker-compose.prod-local.yaml`  
**Laatst bijgewerkt:** 2026-09-14

---

## 1. Architectuur (deploy)

- **Immutable image:** `jarvisje:<tag>` (app + deps + preloaded BGE-M3).
- **Mutable data:** host `~/jarvisje-chatbot-data` (Chroma, raw).
- **LLM:** aparte compose-service `ollama` (niet in de app-image); model in `~/sogyo-ollama` (niet hernoemd — Gemma blijft staan).
- **LLM-config via env** in compose: `LLM_BASE_URL`, `LLM_MODEL`, `EMBEDDING_DEVICE`.

Productiestack start via **systemd** (`sogyo-ollama` + `sogyo-chatbot`), niet handmatig elke boot. Compose-dir: `~/jarvisje-chatbot`.

Geen deploydoel naar NVIDIA Spark DGX `<legacy-host>`. Alles (app + embeddings + LLM) draait op de productiehost.

---

## 2. Deployment flow

### A. Build op de productieserver (aanbevolen vanaf Mac arm64)

De productie-host is **amd64**. Bouwen op de server vermijdt cross-arch issues.

```bash
# lean (vanaf repo-root, geen sudo):
./scripts/deploy-to-15.sh 1.0.7

# of handmatig:
ssh <user>@<host>
cd ~/jarvisje-chatbot/build-src
docker build -t jarvisje:latest -f Dockerfile .
cd ~/jarvisje-chatbot
IMAGE_TAG=latest docker compose up -d --no-deps --force-recreate app
# of: sudo systemctl restart sogyo-chatbot
```

### B. Build lokaal + transfer (Windows/amd64 of buildx)

```powershell
pwsh -ExecutionPolicy Bypass -File infra/ubuntu-x64/build-local-image.ps1
pwsh -ExecutionPolicy Bypass -File infra/ubuntu-x64/deploy.ps1
# Default server: <user>@<host>
```

Op de server laadt `server-deploy.sh` de tarball en start de **app** (Ollama blijft staan).  
Zorg dat **`docker-compose.prod-local.yaml`** als `~/jarvisje-chatbot/docker-compose.yaml` staat.

### C. Alleen compose/env wijzigen

```bash
# na scp van bijgewerkte docker-compose.yaml
cd ~/jarvisje-chatbot
docker compose up -d
# of per service via systemd:
sudo systemctl restart sogyo-ollama
sudo systemctl restart sogyo-chatbot
```

---

## 3. Productie compose (samenvatting)

Bestand: `infra/ubuntu-x64/docker-compose.prod-local.yaml`

| Service | Image / container | Host-poort | GPU |
|---------|-------------------|------------|-----|
| `ollama` | `ollama/ollama` / `sogyo-ollama` | 11434 | ja (runtime nvidia) |
| `app` | `jarvisje:latest` / `jarvisje-chatbot-app` | 8080→8001 | nee (embeddings CPU) |

Compose-projectnaam blijft `sogyo-chatbot` (Docker-netwerk van Gemma).

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
- Tagging: `jarvisje:latest` + optioneel git-SHA / UI-semver

---

## 5. Directory layout (server)

```
~/
├── jarvisje-chatbot/            # compose + build-src + .env
│   ├── docker-compose.yaml
│   ├── build-src/
│   └── .env                     # INGEST_TOKEN (mode 600)
├── sogyo-chatbot → jarvisje-chatbot   # symlink tot systemd WorkingDirectory met sudo is bijgewerkt
├── jarvisje-chatbot-data/       # persistent app data (Chroma, raw)
│   ├── chroma/
│   └── raw/
└── sogyo-ollama/                # Ollama model store (Gemma 3 4B)
```

---

## 6. Data-persistentie & backup

- Host data: `~/jarvisje-chatbot-data`
- Backup: `tar`/`rsync` van die map (+ eventueel `sogyo-ollama` voor model-cache)
- Image update raakt data niet als volume gelijk blijft

---

## 7. Update & rollback

**Update app**

1. Nieuw image (`latest` of tagged)
2. `docker compose up -d --no-deps app` of `systemctl restart sogyo-chatbot`
3. `curl -s http://127.0.0.1:8080/health` en https://jarvisje.com/health

**Rollback**

```bash
docker tag jarvisje:<oude-tag> jarvisje:latest
# of: IMAGE_TAG=<oude-tag> docker compose up -d --no-deps app
sudo systemctl restart sogyo-chatbot
```

**Cloudflare tunnel** hoeft bij app-image updates **niet** te wijzigen.

---

## 8. Smoke checklist na deploy

```bash
systemctl is-active sogyo-ollama sogyo-chatbot cloudflared
docker ps --filter name=jarvisje-chatbot-app
docker ps --filter name=sogyo-ollama
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:11434/api/tags
curl -s https://jarvisje.com/health
# optioneel chat:
curl -sN -X POST http://127.0.0.1:8080/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Ben je er?"}' | head
```

---

## 9. Open punten

1. Automatische nightly ingest
2. PyTorch upgrade voor GPU-embeddings op Blackwell
3. Optionele CI image-build (amd64) + registry
4. Systemd-units hernoemen (sudo) — WorkingDirectory staat al op `~/jarvisje-chatbot`

Laatst bijgewerkt: 2026-09-14
