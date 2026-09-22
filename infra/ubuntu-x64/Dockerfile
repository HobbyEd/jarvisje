FROM python:3.12-slim

WORKDIR /app

# Install system deps if needed for sentence-transformers or chromadb
# curl is required for the Docker healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# CUDA wheels with sm_120 (Blackwell / RTX 50). Verified 2026-09-22 on the
# production host: torch 2.11.0+cu128, capability (12, 0), BGE-M3 encode.
# torchvision and torchaudio are unused. A mismatched torchvision breaks
# transformers' optional vision import, so they stay out of the image.
# Chat keeps EMBEDDING_DEVICE=cpu. The ingest worker sets cuda.
# Must be torch >= 2.6 (transformers CVE-2025-32434).
RUN pip install --no-cache-dir --timeout 600 \
    torch==2.11.0+cu128 \
    --index-url https://download.pytorch.org/whl/cu128

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model so the container needs no internet at runtime.
# This layer is cached as long as requirements.txt + the torch RUN above don't change.
# We use a compact one-liner to avoid any heredoc + Windows CRLF line-ending issues during build.
# Torch is pinned >=2.6 so the transformers CVE check (check_torch_load_is_safe) no longer triggers.
ENV HF_HUB_DISABLE_TELEMETRY=1
ENV TOKENIZERS_PARALLELISM=false
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3'); print('BGE-M3 preloaded successfully into image cache.')"

# Copy source
COPY src ./src
COPY scripts ./scripts
COPY web ./web

ENV PYTHONPATH=/app/src
# Defaults for local Ollama (compose overrides to http://ollama:11434/v1)
ENV LLM_BASE_URL=http://127.0.0.1:11434/v1
ENV LLM_MODEL=gemma3:4b
ENV EMBEDDING_DEVICE=cpu

# Expose the API port
EXPOSE 8001

# Default run the API
CMD ["python", "-m", "uvicorn", "jarvisje.api.app:app", "--host", "0.0.0.0", "--port", "8001"]
