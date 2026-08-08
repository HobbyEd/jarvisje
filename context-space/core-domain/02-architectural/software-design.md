---
type: Software Design
title: "Software design — Sogyo Kennis-Chatbot"
description: "High-level architectuur en componenten (wat & waarom)."
tags: [architecture, design]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
  - /core-domain/02-architectural/bounded-contexts.md
---

# Software Design: Sogyo Kennis-Chatbot

## 1. Inleiding en Doel

Dit document beschrijft de software architectuur voor een domein-specifieke chatbot op [www.sogyo.nl](https://www.sogyo.nl).

De chatbot helpt twee doelgroepen:
- **Sollicitanten** (starters): Inzicht krijgen in de filosofie, werkwijze en waarden van Sogyo (traineeship, software engineering craft).
- **Bedrijven**: Inzicht krijgen in AI-adoptie, talentontwikkeling, kennis-elicitatie en hoe Sogyo-achtige engineers werken.

De chatbot is **geen algemene AI-assistent**. Hij fungeert als gids binnen een specifiek kennisdomein en verwijst actief naar de bestaande content op de volgende bronnen:
- sogyo.nl
- jeroenteunisse.nl
- edwinvandillen.nl
- augmentedorganisation.nl
- intentdriven.nl
- augmentedengineering.nl

**Kernuitgangspunten** (vastgelegd op 26 juni 2026):
- Hoofdzakelijk Nederlands.
- Gematigde guardrails: alles wat met software engineering en engineers te maken heeft mag, alles wat daar ver buiten ligt wordt uitgesloten.
- Uitgebreide chat-sessies zijn toegestaan.
- Her-ingestie van kennisbasis elke 4-6 uur.
- Er komt een evaluatieset om kwaliteit (in-domein + citations) te meten.
- De DGX is momenteel niet direct bereikbaar vanuit de hosting. De oplossing wordt eerst gebouwd, connectiviteit komt later.

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
- Twee doelgroep-tonen (sollicitant vs bedrijf).

### Out of scope (guardrails handhaven)
- Algemene programmeerhulp / code schrijven.
- Algemene AI-adviezen, andere modellen of bedrijven.
- Persoonlijke coaching, loopbaanadvies buiten het Sogyo-domein.
- Politiek, ethiek in brede zin, niet-gerelateerde onderwerpen.
- Alles wat niet gerelateerd is aan software engineering en het ontwikkelen van engineers.

## 3. Requirements en Constraints

### Functioneel
- Conversational interface met goede UX (bij voorkeur streaming).
- Actieve verwijzingen naar bronnen met directe links.
- Ondersteuning voor lange gesprekken (meerdere turns).
- Mogelijkheid om context te geven over doelgroep (sollicitant / bedrijf).

### Niet-functioneel
- **Guardrails**: Gematigd maar effectief. Blijft binnen "software engineering + engineers".
- **Grounding**: Antwoorden moeten gebaseerd zijn op de content. Hallucinaties buiten de bronnen worden geminimaliseerd.
- **Taal**: Hoofdzakelijk Nederlands.
- **Onderhoud**: Kennisbasis wordt elke 4-6 uur ververst.
- **Evalueren**: Er komt een testset met vragen + verwachte gedrag (in-domein + citations).
- **Technisch**: Lokaal draaien op NVIDIA DGX waar mogelijk. Python op de web-hosting.

## 4. High-Level Architecture

```
┌─────────────────────────────┐
│   sogyo.nl (Website)        │
│   + Chat Widget (JS)        │
└──────────────┬──────────────┘
               │ HTTPS + streaming
┌──────────────▼──────────────┐
│  FastAPI Backend            │
│  (Python hosting)           │
│  - API endpoints            │
│  - Conversation orchestration│
│  - Guardrail checks         │
└──────────────┬──────────────┘
               │ (later: netwerk)
               │ (nu: dev via lokale/DGX toegang)
┌──────────────▼──────────────┐
│  DGX (Inference & Storage)  │
│  - vLLM (of equivalent)     │
│  - Embeddings model         │
│  - Vector DB (Qdrant)       │
│  - Ingestion pipeline       │
└─────────────────────────────┘
```

**Tijdelijke realiteit**: Omdat de DGX niet direct bereikbaar is, starten we met een setup waarbij de backend en/of volledige stack lokaal of op de DGX zelf ontwikkeld en getest kan worden. De split tussen hosting en DGX wordt later gerealiseerd.

## 5. Kerncomponenten

### 5.1 Ingestion Pipeline
- Periodiek (4-6 uur) ophalen van content van de 6 bronnen.
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
- Hoofdmodel op DGX via OpenAI-compatibele API (vLLM aanbevolen).
- Ondersteuning voor lange context / history.
- Structured output voor citations.

### 5.5 Chat Backend (FastAPI)
- Beheert sessies.
- Roept retriever + LLM aan.
- Stroomt antwoorden terug.
- Houdt minimale state.

### 5.6 Frontend Widget
- Lichtgewicht JavaScript widget.
- Embedded op sogyo.nl.
- Toont bronverwijzingen netjes.
- Ondersteunt lange gesprekken.

## 6. Data & Kennisbasis

- Primaire bron: De 6 websites.
- Vector DB met metadata-rijke chunks.
- Geen fine-tuning in eerste versie (RAG-first).
- Herlaadcyclus: 4-6 uur (zie ADR-07).

## 7. Guardrails (Gematigd)

Zie ADR-02 voor details.

Kort samengevat:
- In-domein: Software engineering, engineers ontwikkelen, AI-augmentatie in dit vakgebied, intent-driven werkwijzen, IT-landschap, veranderkracht binnen engineering context, Sogyo-traineeship en bijbehorende filosofie.
- Uitgesloten: Algemene codehulp, andere AI-tools, persoonlijke coaching, ongerelateerde onderwerpen.
- Strategie: Gelaagd (classifier + retrieval-only + citation forcing + optionele validator).

## 8. Technologie Stack (Initiële Richting)

- **Backend**: FastAPI (Python)
- **LLM Serving**: vLLM (OpenAI compatibele endpoint) op DGX
- **Embeddings**: Lokale sentence-transformers / BGE of vergelijkbaar (Nederlands-competent)
- **Vector DB**: Qdrant (sterke metadata support)
- **Orchestration**: Lichtgewicht custom (Pydantic + httpx) of minimale LangChain/LlamaIndex indien nuttig
- **Frontend**: Custom JS widget met Server-Sent Events / streaming
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

- Netwerktoegang DGX → later oplossen (ADR-05).
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

## 12. Volgende Stappen (voorstel)

1. ADRs reviewen en accorderen.
2. Eerste versie van de ingestion pipeline bouwen.
3. Vector DB vullen + retrieval testen.
4. Eenvoudige FastAPI + LLM endpoint prototypen (eerst lokaal/DGX).
5. Guardrails implementeren en testen met de evaluatieset.
6. Widget prototypen.
7. Connectiviteitsoplossing later toevoegen.

---

*Dit document is de centrale beschrijving. Details en rationale staan in de individuele ADRs.*
