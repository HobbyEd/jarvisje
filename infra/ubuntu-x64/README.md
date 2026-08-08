# Deploy — Ubuntu x64 productie (`192.168.165.15`)

Productiehost voor de Sogyo Chatbot (hostname **enterprise**).

| | |
|--|--|
| SSH | `evdillen@192.168.165.15` |
| UI LAN | http://192.168.165.15:8080 |
| UI publiek | https://jarvisje.com |
| LLM | Ollama `gemma3:4b` op dezelfde host |
| Compose | `docker-compose.prod-local.yaml` → server: `~/sogyo-chatbot/docker-compose.yaml` |

Zie ook: [runbooks/infrastructure.md](../runbooks/infrastructure.md), [runbooks/deployment.md](../runbooks/deployment.md).

---

## One-time setup (server)

1. NVIDIA driver (595-open of nieuwer voor RTX 50) + reboot  
2. Docker + **nvidia-container-toolkit**  
3. Mappen:

```bash
mkdir -p ~/sogyo-chatbot ~/sogyo-chatbot-data ~/sogyo-ollama
```

4. Compose + scripts plaatsen:

```bash
scp infra/ubuntu-x64/docker-compose.prod-local.yaml \
    infra/ubuntu-x64/server-deploy.sh \
    infra/ubuntu-x64/setup-sogyo-service.sh \
    evdillen@192.168.165.15:~/sogyo-chatbot/
# op server:
mv ~/sogyo-chatbot/docker-compose.prod-local.yaml ~/sogyo-chatbot/docker-compose.yaml
```

5. Image bouwen of laden, model pullen:

```bash
docker compose -f ~/sogyo-chatbot/docker-compose.yaml up -d ollama
docker exec sogyo-ollama ollama pull gemma3:4b
# image: build in build-src of docker load tarball
docker compose -f ~/sogyo-chatbot/docker-compose.yaml up -d app
```

6. Systemd:

```bash
sudo bash ~/sogyo-chatbot/setup-sogyo-service.sh
# units: sogyo-ollama.service, sogyo-chatbot.service
```

7. Cloudflare Tunnel (host, **niet** in app-image):

```bash
# cloudflared package + token in /etc/cloudflared/tunnel.token
# dashboard: jarvisje.com → http://127.0.0.1:8080
sudo systemctl enable --now cloudflared
```

---

## Normale release-flow (aanbevolen)

Vanaf de repo-root (Mac/Linux, SSH-key, geen sudo):

```bash
./scripts/deploy-to-15.sh
# of met tag:
./scripts/deploy-to-15.sh 0.8.0
```

Dit rsync’t bronnen, bouwt op de server en herstart alleen de app-container.

### Alternatief: PowerShell + image tarball

```powershell
pwsh -ExecutionPolicy Bypass -File infra/ubuntu-x64/full-deploy.ps1
```

Default target: `evdillen@192.168.165.15`.  
Repo-compose: `docker-compose.prod-local.yaml` → server: `~/sogyo-chatbot/docker-compose.yaml`.

---

## Servicebeheer

```bash
sudo systemctl status sogyo-ollama sogyo-chatbot cloudflared
sudo systemctl restart sogyo-chatbot
sudo systemctl restart sogyo-ollama

cd ~/sogyo-chatbot && docker compose ps
docker logs -f sogyo-chatbot-app
docker exec sogyo-ollama ollama list
```

---

## Secrets / `.env` (ADR-011)

**Nooit** tokens in git of in de Docker image.

1. Lokaal in de repo: `cp .env.example .env` en vul:

   ```bash
   INGEST_TOKEN=<lang-willekeurig-secret>
   ```

2. `./scripts/deploy-to-15.sh` kopieert `.env` naar **`~/sogyo-chatbot/.env`** op de host (`chmod 600`) en **niet** naar de build-context.
3. Compose laadt die file via `env_file: .env` op de `app`-service.
4. UI: zelfde token invullen bij “Indexeringstoken”.

Zonder `INGEST_TOKEN` weigert de API start/stop van indexering.

## Ingest worker (ADR-010)

Indexering draait **buiten** de chat request-thread:

- **UI / API**: `POST /ingest/start` (token = `INGEST_TOKEN`) spawnt `python -m sogyo_chatbot.ingestion.worker` in de app-container; status op volume `ingest_status.json`.
- **CLI op server (zelfde image, one-shot)** — geen HTTP-token nodig:

```bash
cd ~/sogyo-chatbot
docker compose --profile ingest run --rm ingest --max-pages 500
# eventueel: --reset
```

- **Log worker (UI-spawn)**: `~/sogyo-chatbot-data/ingest_worker.log`

Chat blijft beschikbaar tijdens indexeren (aparte proces; embeddings CPU).

---

## Bestanden in deze map

| Bestand | Rol |
|---------|-----|
| `docker-compose.prod-local.yaml` | **Productie:** ollama + app (+ profile `ingest`) → server: `docker-compose.yaml` |
| `Dockerfile` | App-image (Python, torch, BGE-M3 preload) |
| `setup-sogyo-service.sh` | systemd units ollama + chatbot |
| `server-deploy.sh` | load tarball + compose up (server-side) |
| `build-local-image.ps1` | lokale image + tar.gz |
| `deploy.ps1` / `full-deploy.ps1` | transfer + remote deploy |
| `Copy-ToDeployServer.ps1` | copy helpers |

---

## Belangrijke env (app)

```
LLM_BASE_URL=http://ollama:11434/v1
LLM_MODEL=gemma3:4b
EMBEDDING_DEVICE=cpu
```

Laatst bijgewerkt: 2026-08-08
