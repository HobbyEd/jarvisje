---
type: Software Design
title: "Software design — Jarvisje"
description: "High-level architectuur en componenten (wat & waarom)."
tags: [architecture, design]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
  - /core-domain/02-architectural/bounded-contexts.md
---

# Software Design: Jarvisje

## 1. Inleiding en Doel

Dit document beschrijft de software-architectuur voor **Jarvisje**: een chatbot rondom de wereld van AI. Hij wordt ingebed op [edwinvandillen.nl](https://edwinvandillen.nl/) en verwijst naar twee blogs ([ADR-012](/core-domain/02-architectural/decisions/12-ADR-jarvisje-rebrand.md)).

Doelgroep: lezers van die blogs. Geen sollicitant/bedrijf-modes.

De chatbot is **geen algemene AI-assistent**. Hij verwijst alleen naar:
- edwinvandillen.nl
- jeroenteunisse.nl

**Kernuitgangspunten** (vastgelegd op 26 juni 2026, geactualiseerd 2026-09):
- Hoofdzakelijk Nederlands.
- Gematigde guardrails: alles wat met software engineering en engineers te maken heeft mag, alles wat daar ver buiten ligt wordt uitgesloten.
- Uitgebreide chat-sessies zijn toegestaan.
- Her-ingestie van kennisbasis (UI/worker; doel 4-6 uur).
- Er komt een evaluatieset om kwaliteit (in-domein + citations) te meten.
- Alles draait op **één host `.15`**: app, embeddings, Chroma en Ollama. NVIDIA Spark DGX is geen deploydoel (historisch: ADR-005).

## 2. Domein en Scope

### In scope
- Kennis uit de genoemde blogs en tools over:
  - Intent-Driven Engineering / Kennis-elicitatie
  - Augmented Organisation (canvases, governance, maturity, roles, harnessing, adoptie)
  - Veranderkracht in AI-transities
  - Grip op IT-landschap en sourcing
  - Harness Engineering
  - AI als collega / Socratische partner
  - Lokale / self-hosted AI
  - Software engineering craft en vakmanschap
- Verwijzen naar specifieke blogposts, tools en canvases.
- Natuurlijke gesprekken binnen het domein.
- Eén toon: gids door de twee blogs.

### Out of scope (guardrails handhaven)
- Algemene programmeerhulp / code schrijven.
- Algemene AI-adviezen, andere modellen of bedrijven.
- Persoonlijke coaching, loopbaanadvies buiten de blogs.
- Politiek, ethiek in brede zin, niet-gerelateerde onderwerpen.
- Alles wat niet gerelateerd is aan software engineering en het ontwikkelen van engineers.

## 3. Requirements en Constraints

### Functioneel
- Conversational interface met goede UX (bij voorkeur streaming).
- Actieve verwijzingen naar bronnen met directe links.
- Ondersteuning voor lange gesprekken (meerdere turns).
- Compacte embed-view voor iframe op edwinvandillen.nl.

### Niet-functioneel
- **Guardrails**: Gematigd maar effectief. Blijft binnen "software engineering + engineers".
- **Grounding**: Antwoorden moeten gebaseerd zijn op de content. Hallucinaties buiten de bronnen worden geminimaliseerd.
- **Taal**: Hoofdzakelijk Nederlands.
- **Onderhoud**: Kennisbasis wordt elke 4-6 uur ververst.
- **Evalueren**: Er komt een testset met vragen + verwachte gedrag (in-domein + citations).
- **Technisch**: Lokaal-first op host `.15` (Ollama + FastAPI + Chroma). Geen remote GPU-host.

## 4. High-Level Architecture

```
┌─────────────────────────────────┐
│  edwinvandillen.nl (iframe)     │
│  jarvisje.com (standalone)      │
└──────────────┬──────────────────┘
               │ HTTPS + SSE
┌──────────────▼──────────────────┐
│  Host <host>            │
│  FastAPI (jarvisje-chatbot-app) │
│  - API, orchestratie, guardrails│
│  - BGE-M3 + Chroma (CPU)        │
│  - Ollama gemma3:4b (GPU)       │
└─────────────────────────────────┘
```

**Huidige realiteit**: één host. Geen split naar NVIDIA Spark DGX `<host>`.

## 5. Kerncomponenten

### 5.1 Ingestion Pipeline
- Periodiek ophalen van content van de 2 blogs.
- Schone extractie van tekst + structuur.
- Intelligente chunking met rijke metadata (url, title, section, type, date, audience hints).
- Embedding + opslag in vector DB.

### 5.2 Retriever
- Hybride search (semantisch + keyword).
- Metadata filtering (bijv. per tool of blog).
- Context samenstellen met bronverwijzingen.

### 5.3 Guardrail Layer
- Pre-retrieval check (domein-classificatie).
- Post-generation check (blijf in domein + citeer).
- Strict prompting + retrieval-only beleid.

### 5.4 LLM Orchestration
- Hoofdmodel op `.15` via OpenAI-compatibele API (Ollama `gemma3:4b`).
- Ondersteuning voor lange context / history.
- Structured output voor citations.

### 5.5 Chat Backend (FastAPI)
- Beheert sessies.
- Roept retriever + LLM aan.
- Stroomt antwoorden terug.
- Houdt minimale state.

### 5.6 Frontend Widget
- `web/index.html` (standalone + embed-modus).
- Iframe op edwinvandillen.nl (`/?embed=1`).
- Toont bronverwijzingen netjes.
- Ondersteunt lange gesprekken.

## 6. Data & Kennisbasis

- Primaire bron: de twee blogs (ADR-012).
- Vector DB met metadata-rijke chunks.
- Geen fine-tuning in eerste versie (RAG-first).
- Herlaadcyclus: 4-6 uur (zie ADR-07).

## 7. Guardrails (Gematigd)

Zie ADR-02 voor details.

Kort samengevat:
- In-domein: Software engineering, engineers ontwikkelen, AI-augmentatie in dit vakgebied, intent-driven werkwijzen, IT-landschap, veranderkracht binnen engineering context, inhoud van de twee blogs.
- Uitgesloten: Algemene codehulp, andere AI-tools, persoonlijke coaching, ongerelateerde onderwerpen.
- Strategie: Gelaagd (classifier + retrieval-only + citation forcing + optionele validator).

## 8. Technologie Stack (Initiële Richting)

- **Backend**: FastAPI (Python)
- **LLM Serving**: Ollama (OpenAI-compatibele endpoint) op `.15`
- **Embeddings**: Lokale sentence-transformers / BGE-M3 (CPU tot Blackwell-support)
- **Vector DB**: Chroma (persistente host-volume)
- **Orchestration**: Lichtgewicht custom (Pydantic + httpx)
- **Frontend**: Custom HTML/JS met Server-Sent Events / streaming
- **Ingestion**: Python script (BeautifulSoup / Trafilatura + markdown parsing)

Modelkeuze: Open voor verschillende families. Ervaring aanwezig met Gemma. Sterke Nederlandse modellen hebben voorkeur, maar performance op domein weegt zwaarder.

## 9. Evaluatie

- Handmatige + geautomatiseerde testset.
- Criteria:
  - Blijft het antwoord in domein?
  - Citeert het concrete bronnen met correcte links?
  - Is de toon passend voor de doelgroep?
  - Wordt er onterecht geweigerd binnen domein?

Zie ook ADR-08 over citations.

## 10. Risico's en Open Issues

- Groter lokaal model op `.15` als VRAM/kwaliteit dat toelaat (ADR-004).
- Kwaliteit van retrieval op abstracte/filosofische content.
- Consistentie van Nederlandse antwoorden.
- Onderhoud van de ingestion pipeline bij veranderingen in de bronnen.
- Lange gesprekken → context management en kosten (tokens).

## 11. Gerelateerde ADRs

Alle significante beslissingen worden vastgelegd in losse ADR-bestanden in [decisions/](decisions/):

- `01-ADR-knowledge-strategy.md`
- `02-ADR-guardrails.md`
- `03-ADR-primary-language.md`
- `04-ADR-inference-serving.md`
- `05-ADR-temporary-deployment.md`
- `06-ADR-conversation-management.md`
- `07-ADR-ingestion-cadence.md`
- `08-ADR-citations-grounding.md`
- `09-ADR-image-compose-deployment.md`
- `10-ADR-async-ingestion-worker.md`
- `11-ADR-secrets-handling.md`
- `12-ADR-jarvisje-rebrand.md`

Open werk staat in de [roadmap](/core-domain/04-delivery/roadmap.md), niet in dit ontwerp.

---

*Dit document is de centrale beschrijving. Details en rationale staan in de individuele ADRs.*
