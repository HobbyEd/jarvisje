"""CLI entry for the Software Designer Agent."""
import argparse
from pathlib import Path

from .agent import run_agent


def main() -> None:
    parser = argparse.ArgumentParser(description="Sogyo Software Designer Agent")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    args = parser.parse_args()

    result = run_agent(args.root)
    print("=== Software Designer Agent ===")
    print(f"Files analyzed: {result['metrics'].get('total_files')}")
    print(f"Total LOC:      {result['metrics'].get('total_lines')}")
    print(f"ADR violations: {len(result.get('adr_violations', []))}")
    if result.get("debt_files"):
        print("\nTech debt created:")
        for p in result["debt_files"]:
            print(" -", p)
    else:
        print("\nNo major issues detected in this run.")


if __name__ == "__main__":
    main()
