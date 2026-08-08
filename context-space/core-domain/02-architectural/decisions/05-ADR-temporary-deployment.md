---
type: ADR
title: "Tijdelijke DGX-centric deploy"
description: "Lokaal/DGX eerst, hosting later."
status: superseded
tags: [deployment]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-005: Temporary Deployment Model (Given Limited Connectivity)

## Status
Superseded (Vervangen door [ADR-009](09-ADR-image-compose-deployment.md) — de split tussen API backend en DGX-inferentie is inmiddels volledig geïmplementeerd).

## Datum
2026-06-26

## Context
De NVIDIA DGX is op dit moment **niet echt bereikbaar** vanuit de Python-hosting omgeving van de website.

User-instructie:
> "Niet echt bereikbaar, maar dat is een problem wat ik later wil oplossen. Ik wil eerst de oplossing bouwen. Dan komt dat later wel goed."

We willen dus niet wachten op netwerken/firewall/VPN-oplossingen voordat we kunnen ontwikkelen en testen.

## Decision
We ontwikkelen de oplossing **eerst als een lokale / DGX-centric architectuur**.

### Fase 1 (nu): Ontwikkel- en testfase
- De volledige stack (of een minimale werkende versie) draait primair op of direct bij de DGX.
- FastAPI backend kan lokaal of op de DGX zelf draaien voor ontwikkeling.
- De chat widget kan lokaal getest worden (bijv. via ngrok of lokale proxy).
- Doel: functionerende chatbot met goede retrieval, guardrails, citations en lange conversaties.

### Fase 2 (later): Productie split
- FastAPI backend verplaatst naar de officiële Python-hosting.
- DGX wordt blootgesteld via een veilige endpoint (reverse proxy, VPN, Cloudflare Tunnel, of dedicated API gateway).
- De backend roept de DGX aan via HTTPS (OpenAI-compatibele endpoint).

De architectuur (FastAPI + vLLM + Qdrant) wordt vanaf het begin zo ontworpen dat de split later makkelijk te maken is (losse configuratie voor endpoint URLs, etc.).

## Consequences
### Positief
- We kunnen direct beginnen met bouwen en leren.
- Snellere iteratie en validatie van de functionele eisen (guardrails, citations, domein).
- Vermijdt blokkade door infra-afhankelijkheden.

### Negatief / Risico's
- Tijdelijke dev-omgeving kan afwijken van uiteindelijke productie (performance, networking).
- Er moet later refactoring komen voor de netwerklaag.
- Monitoring en logging moeten al vroeg schaalbaar opgezet worden.

## Alternatives Considered
- Wachten tot de DGX bereikbaar is: Verworpen (te langzaam).
- Alles tijdelijk in de cloud draaien: Verworpen (tegen de wens om lokaal op DGX te draaien).
- Monolithische deploy op DGX als definitieve oplossing: Niet gewenst (website moet op de bestaande hosting).

## Implementation Recommendations
- Maak endpoint configuratie (base URL van LLM en vector DB) makkelijk overschrijfbaar via environment variables.
- Documenteer duidelijk welke componenten waar draaien in de verschillende fasen.
- Bouw een lokale "dev mode" waarin alles op één machine kan draaien.

## Gerelateerde ADRs
- ADR-004: Inference Serving
- ADR-006: Conversation Management

## Besloten door
Edwin + architectuur sessie met Grok
