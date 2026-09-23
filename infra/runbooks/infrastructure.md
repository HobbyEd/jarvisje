# Runbook: Infrastructure — Jarvisje

**Type:** Runbook (Actualization Space)  
**Gerelateerd:** [deployment.md](deployment.md), ADR-004, ADR-009, ADR-012  
**Laatst bijgewerkt:** 2026-09-14

---

## Productiehost (primair)

| Item | Waarde |
|------|--------|
| Host | `$DEPLOY_HOST` (`.env`) |
| SSH | `$DEPLOY_USER@$DEPLOY_HOST` |
| OS | Ubuntu 26.04 LTS, x86_64 |
| CPU | AMD Ryzen 5 9600X (12 threads) |
| RAM | ~30 GB |
| GPU | NVIDIA GeForce RTX 5060 Ti **16 GB** |
| Driver | nvidia-driver-595-open (595.x), CUDA runtime 13.x |
| Docker | Engine 29.x + Compose + nvidia-container-toolkit |
| Publiek | https://jarvisje.com |
| LAN UI | `http://$DEPLOY_HOST:8080` |

Geen tweede GPU-host. NVIDIA Spark DGX `<legacy-host>` is **geen** deploydoel.

### Runtime-stack op de host

| Component | Hoe | Poort / pad |
|-----------|-----|-------------|
| **Ollama** | Docker service `ollama`, container `sogyo-ollama` | host `11434` |
| **Model** | `gemma3:4b` | `~/sogyo-ollama` |
| **Chatbot app** | Docker service `app`, container `jarvisje-chatbot-app` | host `8080` → container `8001` |
| **Image** | `jarvisje:<tag>` | — |
| **Data** | volume | `~/jarvisje-chatbot-data` |
| **Compose** | projectnaam `sogyo-chatbot` | `~/jarvisje-chatbot/docker-compose.yaml` |
| **Cloudflare Tunnel** | native `cloudflared` | → `http://127.0.0.1:8080` |

**Canonieke compose (productie):**  
`infra/ubuntu-x64/docker-compose.prod-local.yaml`  
(op de server: `~/jarvisje-chatbot/docker-compose.yaml`)

### Systemd (boot)

```
docker.service
  → sogyo-ollama.service    # docker compose up -d ollama
    → sogyo-chatbot.service # docker compose up -d app
  → cloudflared.service     # tunnel naar localhost:8080
```

Units behouden de bestaande namen; WorkingDirectory is `~/jarvisje-chatbot`. Tot de units met sudo zijn herschreven bestaat symlink `~/sogyo-chatbot` → `~/jarvisje-chatbot`.

```bash
sudo systemctl status sogyo-ollama sogyo-chatbot cloudflared
sudo systemctl restart sogyo-ollama
sudo systemctl restart sogyo-chatbot
sudo journalctl -u cloudflared -f
```

Setup-script (herinstall units): `infra/ubuntu-x64/setup-sogyo-service.sh`

### Ollama op de host CLI

Ollama zit **in Docker**, niet als host-binary:

```bash
docker exec sogyo-ollama ollama list
docker exec sogyo-ollama ollama run gemma3:4b "Hallo"
curl -s http://127.0.0.1:11434/api/tags
```

Optioneel in `~/.bashrc`:

```bash
alias ollama='docker exec -it sogyo-ollama ollama'
```

### App-config (env in compose)

| Variable | Productiewaarde |
|----------|-----------------|
| `LLM_BASE_URL` | `http://ollama:11434/v1` |
| `LLM_MODEL` | `gemma3:4b` |
| `OLLAMA_CONTEXT_LENGTH` | `8192` (dubbel de 4k-standaard op deze kaart) |
| `EMBEDDING_DEVICE` | `cpu` in de app; de UI-worker zet `cuda` |
| Data mount | `~/jarvisje-chatbot-data:/app/data` |

**Waar embedden we?**  
Vragen in het API-proces op de CPU (één vector). Indexeren op de GPU: torch 2.11+cu128 bevat sm_120. Ollama gebruikt dezelfde kaart voor Gemma. De app-container heeft de GPU zichtbaar voor dat worker-proces.

### Cloudflare Tunnel

- Connector: host-service `cloudflared` (package + token in `/etc/cloudflared/`, root-only).
- Ingress (dashboard): `jarvisje.com` → `http://localhost:8080`.
- **Niet** in de app-image; image-updates wijzigen de tunnel niet.
- Ollama (`:11434`) niet publiek exposen.

### Andere containers op dezelfde host

TeslaMate (poorten 3000, 4000, 1883) — geen conflict met 8080/11434.

### Health & monitoring

```bash
curl -s http://127.0.0.1:8080/health
curl -s https://jarvisje.com/health
nvidia-smi
docker ps --filter name=jarvisje-chatbot-app
docker ps --filter name=sogyo-ollama
docker stats jarvisje-chatbot-app sogyo-ollama
```

---

## Frontend serving

FastAPI (`src/jarvisje/api/app.py`) serveert `web/index.html` op `/`.

| Omgeving | URL |
|----------|-----|
| Lokaal | http://localhost:8001 |
| LAN | http://<host>:8080 |
| Publiek | https://jarvisje.com |
| Embed | `https://jarvisje.com/?embed=1&theme=dark` (iframe op edwinvandillen.nl) |

API o.a.: `POST /chat`, `POST /chat/sync`, `GET /health`, ingest-endpoints, `/sources`.

---

## Netwerkoverzicht

```
Internet ──HTTPS──► Cloudflare ──tunnel──► cloudflared@productiehost
                                              │
                                              ▼
                                         :8080 app
                                              │
                                    ┌─────────┴─────────┐
                                    ▼                   ▼
                              BGE-M3 + Chroma      ollama:11434
                              (vraag CPU,          gemma3:4b (GPU)
                               index GPU)
```

---

## Toekomst / tech debt

- Eventueel vraag-embeddings ook op GPU als de chatlatentie dat nodig heeft.
- Eventueel groter lokaal model als VRAM/kwaliteit dat toelaat.
- Nightly ingest (cron) i.p.v. alleen UI-trigger.
- Metrics (Prometheus/Grafana) optioneel.
- Systemd-units hernoemen (sudo).

Laatst bijgewerkt: 2026-09-22
