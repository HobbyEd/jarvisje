---
type: Playbook
title: "Projection generation rules"
description: "Hoe core-domain wordt vertaald naar human-readable HTML (geen bron van waarheid)."
tags: [projections, harnessing]
timestamp: 2026-07-05T00:00:00Z
---

# Projection generation rules

Projecties zijn **geen** onderdeel van de Context Space. Ze zijn gegenereerd of handmatig bijgehouden HTML voor mensen (operators, onboarding).

## Anti-corruption boundary

- **Read-only:** `context-space/core-domain/` mag niet worden gewijzigd tijdens het bijwerken van projecties.
- **Bron van waarheid:** altijd `core-domain/`; HTML in `output/` is afgeleid.
- **Infra-details** (poorten, SSH, compose): uit `infra/runbooks/`, niet dupliceren als beleid in HTML.

## Output

| Bestand | Bron | Onderhoud |
|---------|------|-----------|
| `output/index.html` | Handmatig | Links naar andere projecties |
| `output/platform-overzicht.html` | Handmatig + core-domain | Zie [platform-overzicht/rules.md](platform-overzicht/rules.md) |
| `output/technisch-design.html` | `technisch-design/technisch-design.md` | `python scripts/md_to_technisch_design_html.py` |

## Wanneer bijwerken

Na elke stap die architectuur, deploy of start-instructies raakt ([werkwijze](../core-domain/04-delivery/werkwijze.md)):

1. Controleer of `core-domain/` al up-to-date is (ADR, scope).
2. Werk `platform-overzicht.html` bij (diagram, stappen, links).
3. Regenereer `technisch-design.html` indien `technisch-design.md` wijzigde.
4. Bump UI-versie in `web/index.html` indien van toepassing.

## Linkconventie vanuit `output/`

- Core-domain: `../../core-domain/...`
- Infra runbooks: `../../../../infra/runbooks/...`
- Repo-root docs: `../../../../development-setup.md`