"""Software Designer Agent main entry.

Run after commits to validate ADRs and control accidental complexity.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List, Dict

from .metrics import collect_python_files, analyze_python_file, compute_summary
from .adr_checker import load_adr_titles, check_violations


FINDINGS_DIR = Path("context-space/harnessing/findings")


def _ensure_findings_dir() -> None:
    FINDINGS_DIR.mkdir(parents=True, exist_ok=True)


def _write_finding_file(title: str, content: str) -> Path:
    _ensure_findings_dir()
    stamp = dt.datetime.now().strftime("%Y-%m-%d-%H%M")
    slug = title.lower().replace(" ", "-")[:40]
    path = FINDINGS_DIR / f"{stamp}-{slug}.md"
    iso = dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    if not content.startswith("---"):
        content = (
            f"---\n"
            f"type: Finding\n"
            f'title: "{title}"\n'
            f'description: "Software Designer Agent post-commit report."\n'
            f"tags: [harnessing, complexity]\n"
            f"timestamp: {iso}\n"
            f"---\n\n"
            f"{content}"
        )
    path.write_text(content, encoding="utf-8")
    return path


def run_agent(repo_root: Path | None = None) -> Dict:
    """
    Main entry point for the Software Designer Agent.
    Returns a report dict and writes tech-debt files when issues are found.
    """
    root = repo_root or Path.cwd()
    src_root = root / "src" / "sogyo_chatbot"
    adr_dir = root / "context-space" / "core-domain" / "02-architectural" / "decisions"

    report: Dict = {
        "timestamp": dt.datetime.now().isoformat(),
        "root": str(root),
        "metrics": {},
        "adr_violations": [],
        "debt_files": [],
    }

    # Metrics
    py_files = collect_python_files(src_root)
    file_metrics = [m for m in (analyze_python_file(p) for p in py_files) if m]
    summary = compute_summary(file_metrics)
    report["metrics"] = summary

    # ADR checks
    adr_titles = load_adr_titles(adr_dir)
    violations = check_violations(src_root, adr_titles)
    report["adr_violations"] = violations

    # Generate tech debt if needed
    debt_notes: List[str] = []

    if summary.get("files_over_threshold", 0) > 0:
        debt_notes.append(
            f"High complexity: {summary['files_over_threshold']} files exceed thresholds "
            f"(avg lines per file = {summary.get('avg_lines_per_file')})."
        )

    for v in violations:
        debt_notes.append(f"{v['type']}: {v['file']} - {v['description']}")

    if debt_notes:
        title = "Software Designer Agent findings"
        content = "# " + title + "\n\n"
        content += f"Generated: {report['timestamp']}\n\n"
        content += "## Summary\n\n"
        content += f"- Files analyzed: {summary.get('total_files')}\n"
        content += f"- Total LOC: {summary.get('total_lines')}\n"
        content += f"- Functions: {summary.get('total_functions')}\n\n"
        content += "## Findings\n\n"
        for note in debt_notes:
            content += f"- {note}\n"
        content += "\n## Recommended actions\n\n"
        content += "- Split large modules\n- Reduce average function length\n- Align code with documented ADRs\n"

        path = _write_finding_file(title, content)
        report["debt_files"].append(str(path))

    return report


if __name__ == "__main__":
    result = run_agent()
    print("Software Designer Agent report:")
    print(result)
    if result["debt_files"]:
        print("\nHarnessing findings written to:")
        for f in result["debt_files"]:
            print("  ", f)
