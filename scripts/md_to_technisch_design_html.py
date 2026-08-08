"""Convert technisch-design.md to styled HTML in projections/output."""
import html as h
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "context-space" / "projections" / "technisch-design" / "technisch-design.md"
OUT_PATH = ROOT / "context-space" / "projections" / "output" / "technisch-design.html"


def inline(s: str) -> str:
    s = h.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(
        r"`([^`]+)`",
        r'<code class="text-sm bg-slate-100 px-1 py-0.5 rounded">\1</code>',
        s,
    )
    s = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" class="text-blue-600 underline">\1</a>',
        s,
    )
    return s


def parse_table(lines: list[str], i: int) -> tuple[str | None, int]:
    rows = []
    while i < len(lines) and lines[i].strip().startswith("|"):
        row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
        rows.append(row)
        i += 1
    if len(rows) < 2:
        return None, i
    header, body = rows[0], rows[2:]
    ths = "".join(
        f'<th class="px-4 py-2 text-left text-sm font-semibold text-[#003366] border-b border-slate-200">{inline(c)}</th>'
        for c in header
    )
    trs = ""
    for r in body:
        tds = "".join(
            f'<td class="px-4 py-2 text-sm text-slate-600 border-b border-slate-100">{inline(c)}</td>'
            for c in r
        )
        trs += f"<tr>{tds}</tr>"
    tbl = (
        '<div class="overflow-x-auto mb-4">'
        '<table class="w-full bg-white border border-slate-200 rounded-lg">'
        f"<thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>"
    )
    return tbl, i


SECTION_IDS = {
    "Doel en scope": "doel",
    "Executive summary": "summary",
    "1. Logical View": "logical",
    "2. Process View": "process",
    "3. Development View": "development",
    "4. Physical View": "physical",
    "5. Kruisconcerns": "kruisconcerns",
    "6. Scenarios (+1 View)": "scenarios",
    "7. Samenhang tussen views": "samenhang",
    "8. Bijlagen": "bijlagen",
}


def convert_md_to_body(md: str) -> str:
    lines = md.splitlines()
    parts: list[str] = []
    i = 0
    in_code = False
    code_buf: list[str] = []
    code_lang = ""
    open_sections = 0

    def close_sections():
        nonlocal open_sections
        out = "</section>" * open_sections
        open_sections = 0
        return out

    while i < len(lines):
        line = lines[i]

        if line.startswith("```"):
            if not in_code:
                in_code = True
                code_lang = line[3:].strip()
                code_buf = []
                i += 1
                continue
            content = "\n".join(code_buf)
            if code_lang == "mermaid":
                parts.append(
                    '<div class="bg-white border border-slate-200 rounded-2xl p-6 mb-6">'
                    f'<div class="mermaid">{content}</div></div>'
                )
            elif code_lang == "json":
                parts.append(
                    '<pre class="bg-slate-900 text-emerald-300 p-4 rounded-lg text-xs overflow-auto mb-4">'
                    f"<code>{h.escape(content)}</code></pre>"
                )
            else:
                parts.append(
                    '<pre class="bg-slate-100 p-3 rounded-lg text-xs overflow-auto mb-4">'
                    f"<code>{h.escape(content)}</code></pre>"
                )
            in_code = False
            code_lang = ""
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if line.strip() == "---":
            parts.append('<hr class="my-8 border-slate-200">')
            i += 1
            continue

        if line.startswith("# "):
            parts.append(close_sections())
            parts.append(
                f'<h1 class="text-4xl font-semibold text-[#003366] mb-2">{inline(line[2:])}</h1>'
            )
            i += 1
            continue

        if line.startswith("## "):
            parts.append(close_sections())
            title = line[3:]
            sid = SECTION_IDS.get(
                title, re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            )
            parts.append(
                f'<section id="{sid}" class="mb-14">'
                f'<h2 class="section-title text-3xl mb-4">{inline(title)}</h2>'
            )
            open_sections += 1
            i += 1
            continue

        if line.startswith("### "):
            parts.append(
                f'<h3 class="font-semibold text-lg text-[#003366] mt-6 mb-3">{inline(line[4:])}</h3>'
            )
            i += 1
            continue

        if line.startswith("#### "):
            parts.append(
                f'<h4 class="font-medium text-base text-slate-700 mt-4 mb-2">{inline(line[5:])}</h4>'
            )
            i += 1
            continue

        if line.strip().startswith("|"):
            tbl, i = parse_table(lines, i)
            if tbl:
                parts.append(tbl)
            continue

        if re.match(r"^\d+\. ", line):
            parts.append(
                f'<li class="text-slate-600 text-sm mb-1">{inline(re.sub(r"^\d+\. ", "", line))}</li>'
            )
            i += 1
            continue

        if line.strip().startswith("- "):
            parts.append(
                f'<li class="text-slate-600 text-sm mb-1">{inline(line.strip()[2:])}</li>'
            )
            i += 1
            continue

        if (
            line.strip().startswith("*")
            and line.strip().endswith("*")
            and not line.strip().startswith("**")
        ):
            parts.append(
                f'<p class="text-sm text-slate-500 italic mt-6">{inline(line.strip().strip("*"))}</p>'
            )
            i += 1
            continue

        if line.strip() == "":
            i += 1
            continue

        parts.append(f'<p class="text-slate-600 mb-3">{inline(line)}</p>')
        i += 1

    parts.append(close_sections())
    content = "\n".join(parts)
    content = re.sub(
        r"((?:<li[^>]*>.*?</li>\s*)+)",
        r'<ul class="list-disc pl-5 mb-4 space-y-1">\1</ul>',
        content,
        flags=re.S,
    )
    return content


HEADER = """<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Technisch Design — Sogyo Kennis-Chatbot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600&display=swap');
        :root { --sogyo-blue: #003366; --sogyo-accent: #00A3E0; }
        body { font-family: 'Inter', system-ui, sans-serif; }
        .logo-font { font-family: 'Space Grotesk', 'Inter', sans-serif; font-weight: 600; }
        .sogyo-header { background: linear-gradient(135deg, #003366 0%, #002244 100%); }
        .section-title { font-weight: 600; color: #003366; }
        .mermaid { background: white; padding: 1rem; border-radius: 0.5rem; }
    </style>
</head>
<body class="bg-slate-50 text-slate-800">
<header class="sogyo-header text-white">
    <div class="max-w-6xl mx-auto px-6 py-5">
        <div class="flex items-center justify-between flex-wrap gap-4">
            <div class="flex items-center gap-x-3">
                <div class="w-10 h-10 bg-white rounded-full flex items-center justify-center">
                    <span class="text-[#003366] font-bold text-2xl logo-font">S</span>
                </div>
                <div>
                    <div class="logo-font text-3xl font-semibold tracking-tight">Sogyo</div>
                    <div class="text-[10px] text-blue-200 -mt-1">SOFTWARE INNOVATORS</div>
                </div>
            </div>
            <div class="flex items-center gap-x-4 text-sm flex-wrap">
                <a href="index.html" class="text-white/90 hover:text-white">Docs</a>
                <a href="platform-overzicht.html" class="text-white/90 hover:text-white">Platform</a>
                <a href="#summary" class="text-white/90 hover:text-white">Summary</a>
                <a href="#logical" class="text-white/90 hover:text-white">Logical</a>
                <a href="#process" class="text-white/90 hover:text-white">Process</a>
                <a href="#development" class="text-white/90 hover:text-white">Development</a>
                <a href="#physical" class="text-white/90 hover:text-white">Physical</a>
                <a href="#scenarios" class="text-white/90 hover:text-white">Scenarios</a>
            </div>
        </div>
    </div>
</header>
<div class="max-w-6xl mx-auto px-6 py-10">
<div class="mb-8">
    <div class="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-[#003366] mb-4">
        <span>4+1 Architectuur — v0.3 MVP</span>
    </div>
</div>
"""

FOOTER = """
<footer class="pt-8 border-t text-xs text-slate-500 mt-8">
    Technisch design Sogyo Kennis-Chatbot (Jarvisje). Zie ook
    <a href="platform-overzicht.html" class="text-blue-600 underline">Platform Overzicht</a>
    voor deploy &amp; infrastructuur.
    <br>Laatste update: 2026-07-01
</footer>
</div>
<script>
mermaid.initialize({
    startOnLoad: true,
    theme: 'base',
    flowchart: { curve: 'basis', useMaxWidth: true },
    sequence: { useMaxWidth: true }
});
</script>
</body>
</html>
"""


def main() -> None:
    md = MD_PATH.read_text(encoding="utf-8")
    body = convert_md_to_body(md)
    OUT_PATH.write_text(HEADER + body + FOOTER, encoding="utf-8")
    print(f"Written {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()