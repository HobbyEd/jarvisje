---
type: Audit
title: "Harnessing — open findings samenvatting"
description: "Designer Agent output; complexity en ADR-compliance signalen."
tags: [harnessing]
timestamp: 2026-07-05T00:00:00Z
---

# Harnessing findings

Output van de **Software Designer Agent** (post-commit). OKF-type: `Finding`.

## Terugkerende thema's (jun–jul 2026)

| Thema | Status | Actie |
|-------|--------|-------|
| Bestanden boven complexiteitsdrempel | Open | Grote modules splitsen (`app.py`, orchestrator) |
| ADR-violations | Geen in recente runs | Blijf checken na architectuurwijzigingen |
| Gemiddelde LOC/file ~80 | Acceptabel | Monitor bij nieuwe features |

**Laatste run (2026-07-05):** 22 bestanden, 1769 LOC, **2** bestanden boven drempel.

**Pieken (2026-06-28):** tot **3** bestanden boven drempel — daarna verbeterd naar 2.

## Aanbevolen acties (standing)

- Split grote modules waar LOC/functielengte blijft stijgen
- Houd ADR-check in werkwijze na elke commit
- Review findings wekelijks; sluit af door refactor of expliciete acceptatie in ADR

## Recente findings

* [2026-07-05-1312](findings/2026-07-05-1312-software-designer-agent-findings.md) — 2 files over threshold
* [2026-06-28-1650](findings/2026-06-28-1650-software-designer-agent-findings.md) — 3 files over threshold
* [2026-06-28-1643](findings/2026-06-28-1643-software-designer-agent-findings.md)
* [2026-06-28-1637](findings/2026-06-28-1637-software-designer-agent-findings.md)
* [2026-06-28-1631](findings/2026-06-28-1631-software-designer-agent-findings.md)
* [2026-06-28-1626](findings/2026-06-28-1626-software-designer-agent-findings.md)
* [2026-06-28-1557](findings/2026-06-28-1557-software-designer-agent-findings.md)
* [2026-06-27-1544](findings/2026-06-27-1544-software-designer-agent-findings.md)
* [2026-06-27-1543](findings/2026-06-27-1543-software-designer-agent-findings.md)
* [2026-06-27-1511](findings/2026-06-27-1511-software-designer-agent-findings.md)

## Archief

**35** findings in [findings/](findings/) (2026-06-27 t/m 2026-07-05). Volledige chronologie: sorteer op bestandsnaam.

Nieuwe findings krijgen OKF-frontmatter (`type: Finding`) via de Designer Agent.