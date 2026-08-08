"""
CLI entry for ingestion — same worker as UI/cron (ADR-010).

Usage:
    python scripts/ingest.py
    python scripts/ingest.py --max 50
    python scripts/ingest.py --reset
    python scripts/ingest.py --max 0   # hard-cap full crawl per domain
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sogyo_chatbot.ingestion.worker import main as worker_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Sogyo ingestion (async worker entrypoint)")
    parser.add_argument("--max", type=int, default=None, help="Max pages per domain (0 = hard cap)")
    parser.add_argument("--reset", action="store_true", help="Wipe collection first")
    args = parser.parse_args()

    argv: list[str] = []
    if args.max is not None:
        argv.extend(["--max-pages", str(args.max)])
    if args.reset:
        argv.append("--reset")
    return worker_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
