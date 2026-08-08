"""
Standalone scrape analysis script.
Run with venv python to inspect quality of the scraper on real sites.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sogyo_chatbot.config import settings
from sogyo_chatbot.ingestion.scraper import scrape_domain

def main():
    print("=== SCRAPER QUALITY ANALYSIS ===\n")
    print(f"Configured sources: {len(settings.sources)}")
    for s in settings.sources:
        print("  -", s)

    # Test on sogyo.nl + one more
    test_urls = ["https://sogyo.nl", "https://jeroenteunisse.nl"]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"SCRAPING: {url}")
        print('='*60)

        docs = scrape_domain(url, max_pages=3, save_raw=True)

        print(f"\nExtracted {len(docs)} documents\n")

        for i, d in enumerate(docs, 1):
            print(f"--- Page {i} ---")
            print(f"Title : {d.get('title', 'N/A')}")
            print(f"URL   : {d.get('url')}")
            print(f"Source: {d.get('source')}")
            print(f"Chars : {d.get('length')}")
            text = d.get("text", "")
            preview = text[:300].replace("\n", " ").strip()
            print(f"Text preview:\n{preview}...\n")

    print("\n=== Analysis complete. Check data/raw/ for saved files ===")


if __name__ == "__main__":
    main()
