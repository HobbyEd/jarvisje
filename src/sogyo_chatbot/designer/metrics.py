"""Lightweight code metrics (no heavy external dependencies by default)."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class FileMetrics:
    path: str
    lines: int
    functions: int
    classes: int
    avg_function_lines: float
    imports: int


def analyze_python_file(path: Path) -> FileMetrics | None:
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None

    lines = source.splitlines()
    line_count = len(lines)

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return FileMetrics(
            path=str(path), lines=line_count, functions=0, classes=0,
            avg_function_lines=0.0, imports=0
        )

    functions = 0
    function_lines: List[int] = []
    classes = 0
    imports = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
            end = getattr(node, "end_lineno", node.lineno)
            function_lines.append(max(1, end - node.lineno + 1))
        elif isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports += 1

    avg = sum(function_lines) / len(function_lines) if function_lines else 0.0

    return FileMetrics(
        path=str(path),
        lines=line_count,
        functions=functions,
        classes=classes,
        avg_function_lines=round(avg, 1),
        imports=imports,
    )


def collect_python_files(root: Path, max_files: int = 500) -> List[Path]:
    files: List[Path] = []
    for p in root.rglob("*.py"):
        if "site-packages" in str(p) or ".venv" in str(p) or "__pycache__" in str(p):
            continue
        files.append(p)
        if len(files) >= max_files:
            break
    return files


def compute_summary(files: List[FileMetrics]) -> dict:
    total_lines = sum(f.lines for f in files)
    total_functions = sum(f.functions for f in files)
    high_complexity = [f for f in files if f.avg_function_lines > 30 or f.lines > 400]
    return {
        "total_files": len(files),
        "total_lines": total_lines,
        "total_functions": total_functions,
        "files_over_threshold": len(high_complexity),
        "avg_lines_per_file": round(total_lines / max(1, len(files)), 1),
    }
