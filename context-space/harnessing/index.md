---
type: Audit
title: "Harnessing — Designer Agent"
description: "Designer Agent output; complexity en ADR-compliance signalen."
tags: [harnessing]
timestamp: 2026-09-14T00:00:00Z
---

# Harnessing findings

Output van de **Software Designer Agent** (`PYTHONPATH=src python -m jarvisje.designer.cli`).

Findings worden lokaal geschreven naar `findings/` en staan in `.gitignore` (geen commit-ruis na elke stap). Ze zijn geen bron van waarheid.

## Wat de agent checkt

- ADR-compliance (heuristieken op code + docs)
- Complexiteit (LOC, imports, functielengte)
- Duplicatie / te grote bestanden

## Standing aandacht

- Grote modules (`app.py`, orchestrator) splitsen als drempels blijven stijgen
- ADR-check blijft in de [werkwijze](../core-domain/04-delivery/werkwijze.md) na elke stap
