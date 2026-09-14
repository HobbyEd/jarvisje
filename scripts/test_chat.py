"""
Simple non-streaming test client for Jarvisje.

Usage:
    # Against local API (start with: python scripts/run_api.py)
    python scripts/test_chat.py "Wat is intentie-gedreven engineering?"

    # Against production app on LAN
    API_BASE_URL=http://$DEPLOY_HOST:8080 \
    python scripts/test_chat.py "Hoe ontwikkel je veranderkracht?"

Also:
    curl -X POST http://localhost:8001/chat/sync \
      -H "Content-Type: application/json" \
      -d '{"message": "Hallo, wat is intentie-gedreven engineering?"}'
"""
import os
import sys

import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/test_chat.py "your message"')
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    session_id = "test-cli"

    print(f"Testing against {BASE_URL}/chat/sync")
    print(f"Message: {message}\n")

    try:
        with httpx.Client(timeout=120) as client:
            resp = client.post(
                f"{BASE_URL}/chat/sync",
                json={"session_id": session_id, "message": message},
            )
            resp.raise_for_status()
            data = resp.json()

        if "error" in data:
            print("ERROR:", data["error"])
            if "fallback" in data:
                print("Fallback note:", data["fallback"])
            return

        print("=== ANSWER ===")
        print(data.get("answer", "(none)"))
        print("\n=== CITATIONS ===")
        for c in data.get("citations", []):
            print(f"- {c.get('title')} ({c.get('url')})")
        print("\n=== HINTS ===")
        for h in data.get("hints", []):
            print(f"- {h}")
        print("\nRole context:", data.get("role_context"))

    except httpx.HTTPError as e:
        print(f"Failed to reach API: {e}")
        print("Tip: python scripts/run_api.py  (LLM via Ollama on the production host or local)")


if __name__ == "__main__":
    main()
