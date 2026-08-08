---
type: Playbook
title: "Werkwijze MVP-ontwikkeling"
description: "Verplicht proces per bouwstap inclusief agent-discipline."
tags: [process, delivery]
timestamp: 2026-07-05T00:00:00Z
---

# Werkwijze voor de Sogyo Chatbot MVP ontwikkeling

**Belangrijke regel: Vanaf nu moet je bij iedere stap die je uitvoert deze werkwijze.md eerst lezen.**

**Pad:** `context-space/core-domain/04-delivery/werkwijze.md` (niet in repo-root). Ingang voor agents: [context-space/index.md](../../index.md).

## Context Space vs. Actualization Space

De **Context Space** (`context-space/core-domain/`) bevat alleen **wat & waarom**: scope, ADRs, aannames, werkwijze. Geen implementatiedetails.

| Ruimte | Pad | Voorbeelden |
|--------|-----|-------------|
| Context Space | `context-space/core-domain/` | ADRs, vision, werkwijze |
| Software Space | `src/` | Python-code |
| Actualization Space | `infra/` | compose, runbooks, deploy-scripts |

Navigatie: [index.md](../../index.md).

## Minimale vereisten per stap

Voor **iedere stap** die we uitvoeren (wijziging in code, docs, structuur, etc.):

1. **Lees eerst deze werkwijze.md** (gebruik de read_file tool om de inhoud op te halen voordat je begint met de stap).
2. **Voer de stap uit**.
3. **Na iedere stap**:
   - Voer een git commit uit met een duidelijke message die de stap beschrijft.
   - Check dat de Software Designer Agent is gestart / uitgevoerd (run de designer agent via de CLI of post-commit hook en verifieer de output in `harnessing/findings/`).
   - Werk de projecties bij (in `context-space/projections/output/`) volgens [generation-rules.md](../../projections/generation-rules.md). Update platform-overzicht, diagram, start-instructies.
   - Update de versie in de header van de web UI (in `web/index.html`, semver badge bijv. `v0.6.1`) bij iedere change: patch/minor voor backwards-compatible wijzigingen, major voor breaking changes. Agent-contract: zie repo-root `AGENTS.md`.
   - Check of de wijzigingen die we hebben doorgevoerd moeten leiden tot een nieuwe ADR:
     - Vergelijk met bestaande ADRs in `context-space/core-domain/02-architectural/decisions/`.
     - Als de wijziging architectuur, keuzes, guardrails, deployment, of fundamentele principes raakt: maak een nieuwe ADR aan (of update bestaande) en commit die.
     - Documenteer de check in de commit message of in een update van [aannames.md](/core-domain/03-technical/aannames.md) / projecties.

## Algemene werkwijze

- Werk altijd binnen de workfolder.
- Houd het project lightweight: pure Python waar mogelijk, geen onnodige frameworks.
- Gebruik structured output (Pydantic) voor LLM calls.
- Houd [projections/output/](../../projections/output/) up-to-date als levend document voor "hoe het platform werkt en hoe je het start".
- Designer Agent is verplicht na commits: hij checkt ADRs, complexiteit, duplication, dependencies en maakt [harnessing findings](../../harnessing/) aan.
- Commits zijn klein en stap-gericht.

## Extra richtlijnen

- Voeg geen nieuwe dependencies toe zonder check tegen lightweight principe (en update designer checks indien nodig).
- Test lokaal: start vLLM + Python stack + API.
- Update altijd de visualisatie en start-instructies in projections/output bij architectuurwijzigingen.
- Als er twijfel is over een nieuwe ADR: maak er een aan in `context-space/core-domain/02-architectural/decisions/`.

Dit document is leidend. Lees het bij elke stap.
