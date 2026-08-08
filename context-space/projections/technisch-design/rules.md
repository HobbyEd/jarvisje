---
type: Playbook
title: "Technisch design projection rules"
description: "Markdown naar HTML pipeline voor 4+1 architectuurdoc."
tags: [projections]
timestamp: 2026-07-05T00:00:00Z
---

# Technisch design — projection rules

**Bron:** [technisch-design.md](technisch-design.md)  
**Output:** [../output/technisch-design.html](../output/technisch-design.html)

## Generatie

```powershell
python scripts/md_to_technisch_design_html.py
```

Script leest markdown uit `projections/technisch-design/` en schrijft HTML naar `projections/output/`.

## Inhoudsrichtlijnen

- 4+1 views: logical, process, development, physical, scenarios.
- Mermaid-diagrammen in fenced ` ```mermaid ` blocks.
- High-level alleen — implementatiedetails in `src/` en runbooks.
- Cross-links naar [platform-overzicht.html](../output/platform-overzicht.html) voor deploy/infra.

## Na wijziging

1. Edit `technisch-design.md`.
2. Run generator script.
3. Open `output/technisch-design.html` in browser ter controle (Mermaid render).