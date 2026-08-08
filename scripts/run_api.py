"""
Run the Sogyo Chatbot API locally (RAG backend + web/index.html UI at /).

Usage:
    # Default: Ollama on production host (.15) — must be reachable from your machine
    python scripts/run_api.py

    # Explicit production Ollama
    LLM_BASE_URL=http://192.168.165.15:11434/v1 \
    LLM_MODEL=gemma3:4b \
    EMBEDDING_DEVICE=cpu \
    python scripts/run_api.py

    # Local Ollama on this machine
    LLM_BASE_URL=http://127.0.0.1:11434/v1 \
    LLM_MODEL=gemma3:4b \
    python scripts/run_api.py

Open http://localhost:8001 — same UI as production (host :8080 / jarvisje.com).
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

if __name__ == "__main__":
    import uvicorn
    from sogyo_chatbot.api.app import app

    base_url = os.getenv("LLM_BASE_URL", "http://192.168.165.15:11434/v1")
    model = os.getenv("LLM_MODEL", "gemma3:4b")

    print("Starting Sogyo Kennis Chatbot API on http://localhost:8001")
    print(f"LLM endpoint: {base_url}")
    print(f"Model: {model}")
    print("Open http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
