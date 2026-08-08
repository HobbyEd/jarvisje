FROM python:3.12-slim

WORKDIR /app

# Install system deps if needed for sentence-transformers or chromadb
# curl is required for the Docker healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install CUDA-enabled PyTorch for GPU embeddings when the host arch is supported.
# Production LLM is local Ollama (gemma3:4b), not this image.
# On RTX 50 / Blackwell (sm_120), set EMBEDDING_DEVICE=cpu until torch ships sm_120 kernels.
#
# Host needs recent NVIDIA drivers + nvidia-container-toolkit only if using GPU embeddings.
#
# Must be torch >= 2.6 (transformers CVE-2025-32434). Pin cu124 wheels for reproducibility.
RUN pip install --no-cache-dir --timeout 600 \
    torch==2.6.0+cu124 \
    torchvision==0.21.0+cu124 \
    torchaudio==2.6.0+cu124 \
    --index-url https://download.pytorch.org/whl/cu124

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
CMD ["python", "-m", "uvicorn", "sogyo_chatbot.api.app:app", "--host", "0.0.0.0", "--port", "8001"]
