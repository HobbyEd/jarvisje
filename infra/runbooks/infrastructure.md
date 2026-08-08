# Runbook: Infrastructure — Sogyo Kennis Chatbot

**Type:** Runbook (Actualization Space)  
**Gerelateerd:** [deployment.md](deployment.md), ADR-004, ADR-009  
**Laatst bijgewerkt:** 2026-08-08

---

## Productiehost (primair)

| Item | Waarde |
|------|--------|
| Host | `enterprise` / `192.168.165.15` |
| SSH | `evdillen@192.168.165.15` (SSH-key) |
| OS | Ubuntu 26.04 LTS, x86_64 |
| CPU | AMD Ryzen 5 9600X (12 threads) |
| RAM | ~30 GB |
| GPU | NVIDIA GeForce RTX 5060 Ti **16 GB** |
| Driver | nvidia-driver-595-open (595.x), CUDA runtime 13.x |
| Docker | Engine 29.x + Compose + nvidia-container-toolkit |
| Publiek | https://jarvisje.com |
| LAN UI | http://192.168.165.15:8080 |

### Runtime-stack op de host

| Component | Hoe | Poort / pad |
|-----------|-----|-------------|
| **Ollama** | Docker service `ollama` | host `11434` |
| **Model** | `gemma3:4b` | `~/sogyo-ollama` |
| **Chatbot app** | Docker service `app` | host `8080` → container `8001` |
| **Data** | volume | `/home/evdillen/sogyo-chatbot-data` |
| **Compose** | | `/home/evdillen/sogyo-chatbot/docker-compose.yaml` |
| **Cloudflare Tunnel** | native `cloudflared` | → `http://127.0.0.1:8080` |

**Canonieke compose (productie):**  
`infra/ubuntu-x64/docker-compose.prod-local.yaml`  
(op de server: `~/sogyo-chatbot/docker-compose.yaml`)

### Systemd (boot)

```
docker.service
  → sogyo-ollama.service    # docker compose up -d ollama
    → sogyo-chatbot.service # docker compose up -d app
  → cloudflared.service     # tunnel naar localhost:8080
```

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
| `EMBEDDING_DEVICE` | `cpu` |
| `CUDA_VISIBLE_DEVICES` | leeg (app) |
| Data mount | `/home/evdillen/sogyo-chatbot-data:/app/data` |

**Waarom embeddings op CPU?**  
PyTorch 2.6+cu124 ondersteunt GPU-arch **sm_120** (Blackwell / RTX 50) nog niet. Ollama gebruikt wél de GPU voor Gemma.

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
docker ps --filter name=sogyo
docker stats sogyo-chatbot-app sogyo-ollama
```

---

## Frontend serving

FastAPI (`src/sogyo_chatbot/api/app.py`) serveert `web/index.html` op `/`.

| Omgeving | URL |
|----------|-----|
| Lokaal | http://localhost:8001 |
| LAN | http://192.168.165.15:8080 |
| Publiek | https://jarvisje.com |

API o.a.: `POST /chat`, `POST /chat/sync`, `GET /health`, ingest-endpoints, `/sources`.

---

## Netwerkoverzicht

```
Internet ──HTTPS──► Cloudflare ──tunnel──► cloudflared@enterprise
                                              │
                                              ▼
                                         :8080 app
                                              │
                                    ┌─────────┴─────────┐
                                    ▼                   ▼
                              BGE-M3 + Chroma      ollama:11434
                              (CPU, volume)        gemma3:4b (GPU)
```

---

## Toekomst / tech debt

- PyTorch met Blackwell (sm_120) → embeddings weer op GPU.
- Eventueel groter lokaal model als VRAM/kwaliteit dat toelaat.
- Nightly ingest (cron) i.p.v. alleen UI-trigger.
- Metrics (Prometheus/Grafana) optioneel.

Laatst bijgewerkt: 2026-08-08
