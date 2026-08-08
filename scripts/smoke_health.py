#!/usr/bin/env python3
"""Minimal smoke test: GET /health on local or LAN API.

Usage:
  python scripts/smoke_health.py
  API_BASE_URL=http://192.168.165.15:8080 python scripts/smoke_health.py
"""
from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request

BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8001").rstrip("/")


def main() -> int:
    url = f"{BASE}/health"
    print(f"GET {url}")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            print(f"status={resp.status}")
            print(body[:500])
            if resp.status != 200:
                return 1
            if '"status"' in body and "ok" not in body.lower():
                return 1
            return 0
    except urllib.error.URLError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
