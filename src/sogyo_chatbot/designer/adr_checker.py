"""Simple ADR compliance checker (heuristic based on documented decisions)."""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict


def load_adr_titles(adr_dir: Path) -> List[str]:
    titles = []
    for md in sorted(adr_dir.glob("*.md")):
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
            for line in text.splitlines():
                if line.startswith("#"):
                    titles.append(line.lstrip("# ").strip())
                    break
        except Exception:
            pass
    return titles


def check_violations(src_root: Path, adr_titles: List[str]) -> List[Dict]:
    """
    Very lightweight checks based on known ADRs under core-domain/02-architectural/decisions.
    Extend this over time.
    """
    issues: List[Dict] = []

    # Example heuristic checks
    py_files = list(src_root.rglob("*.py"))

    # Check 1: No LangChain / LlamaIndex imports (lightweight decision)
    for f in py_files:
        # Skip the designer itself when checking for forbidden frameworks
        if "designer" in str(f):
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore").lower()
            if "langchain" in content or "llamaindex" in content or "from langchain" in content:
                issues.append({
                    "type": "dependency_violation",
                    "file": str(f),
                    "description": "LangChain or LlamaIndex import detected (violates lightweight decision).",
                })
        except Exception:
            pass

    # Check 2: Citations logic should exist in chat-related code (when we add it)
    # For now just a placeholder note.

    # Check 3: Large files
    for f in py_files:
        try:
            if f.stat().st_size > 30_000:  # ~30kB rough
                issues.append({
                    "type": "file_size",
                    "file": str(f),
                    "description": "File is quite large; consider splitting.",
                })
        except Exception:
            pass

    return issues
