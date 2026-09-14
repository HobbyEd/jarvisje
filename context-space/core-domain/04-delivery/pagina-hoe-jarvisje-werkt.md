---
type: Content Design
title: "Pagina — Hoe Jarvisje werkt"
description: "Inhoudelijke opzet voor de publieke uitlegpagina (huidige tab Chatbot Opbouw). Nog niet gebouwd."
tags: [ui, rag, uitleg, delivery]
timestamp: 2026-09-14T00:00:00Z
status: proposed
traces_to:
  - /core-domain/01-strategic/vision.md
  - /core-domain/02-architectural/decisions/01-ADR-knowledge-strategy.md
  - /core-domain/02-architectural/decisions/04-ADR-inference-serving.md
  - /core-domain/02-architectural/decisions/08-ADR-citations-grounding.md
  - /core-domain/02-architectural/decisions/09-ADR-image-compose-deployment.md
  - /core-domain/02-architectural/decisions/10-ADR-async-ingestion-worker.md
  - /core-domain/02-architectural/decisions/12-ADR-jarvisje-rebrand.md
---

# Pagina: Hoe Jarvisje werkt

**Status:** voorstel — nog niet gebouwd. Huidige tab *Chatbot Opbouw* in `web/index.html` wordt bij bouw **geheel vervangen**.

**Doel:** de bezoeker van jarvisje.com meenemen in hoe Jarvisje is opgebouwd: kort functioneel, daarna hoe een vraag tot een antwoord komt, daarna hoe de kennisbank gevuld wordt, daarna de technische stekkerdoos.

**Doelgroep:** lezers en nieuwsgierige bouwers. Geen operators. Beheer (token, reset, cron) blijft op het tabblad Bronnen. In embed-modus (`?embed=1`) blijft deze pagina verborgen.

**Toon:** Nederlands, één idee per blok, jargon (RAG, embedding, chunk) uitleggen op het moment dat het nodig is.

## Pedagogische kern

Jarvisje is een **chatbot rondom de wereld van AI**, grounded in twee blogs ([edwinvandillen.nl](https://edwinvandillen.nl), [jeroenteunisse.nl](https://jeroenteunisse.nl)). Het model is niet getraind op die artikelen. Bij elke vraag zoekt de app eerst fragmenten; pas daarna mag Gemma antwoorden.

**Volgorde die de pagina moet vertellen** (niet omdraaien):

```
vraag → app embedt → kennisbank geeft fragmenten → app bouwt prompt → Gemma antwoordt
```

niet:

```
vraag → Gemma → RAG → antwoord
```

Gemma spreekt de kennisbank niet zelf aan. De orchestrator haalt fragmenten op en geeft alleen die mee. Precies daarom zijn citations afdwingbaar ([ADR-008](../02-architectural/decisions/08-ADR-citations-grounding.md), [ADR-001](../02-architectural/decisions/01-ADR-knowledge-strategy.md)).

Twee bewegingen, zelfde kennisbank, verschillend moment:

| | Vragen (query-time) | Leren (ingest-time) |
|---|---|---|
| Wanneer | Elke chatbeurt | Handmatig via Bronnen, later gepland |
| Wat | embed vraag → zoek → prompt → Gemma | crawl → knip → embed → opslaan |
| Waarom op de pagina | hoe een antwoord ontstaat | hoe de blogs in de kennisbank komen |

## Wat de huidige pagina mist

De bestaande tab vertelt vooral infrastructuur (tunnel, poorten, container-namen) en herhaalt dezelfde flow drie keer (flowchart + stappenkaarten + genummerde lijst). RAG en embeddings worden genoemd, niet uitgelegd. Retrieval en Gemma zitten in één “verwerking”-doos. Operator-jargon (ADR-nummers, volume-paden) hoort niet in het hoofdverhaal.

## Paginastructuur (zeven blokken, drie tekeningen)

Richtlijn: iemand heeft in twee minuten het functionele plaatje, in vijf minuten het technische. Geen mermaid als hoofdvorm — HTML/CSS of SVG in de bestaande UI-taal (kaarten, pijlen, dark/light tokens). Tekening 1 en 2 in verhaalstijl; tekening 3 nuchterder. Op mobiel stapelen de kolommen.

Tab-naam bij bouw: **Hoe Jarvisje werkt** (niet “Chatbot Opbouw”).

### Blok 1 — Wat Jarvisje is (functioneel)

Kort, ~8 regels:

- Chatbot rondom AI, geen algemene assistent.
- Hij kent de artikelen van Edwin en Jeroen.
- Hij verwijst naar concrete posts; hij verzint geen derde bron.
- Hij draait lokaal: de vraag gaat niet naar een cloud-LLM.

Geen poorten, geen ADR-nummers, geen container-namen.

### Blok 2 — Twee bewegingen (oriëntatie)

Eén zin + twee kaarten:

- **Als jij vraagt** — zoeken in wat al gelezen is, daarna Gemma.
- **Als de kennisbank bijwerkt** — crawler leest de blogs, embedding-model legt betekenis vast.

Daarna de tekeningen. Niet alles in één flowchart.

### Blok 3 — Tekening 1: van vraag naar antwoord

Stap voor stap, naast of onder de tekening:

1. Browser opent de webtoepassing (jarvisje.com, of iframe op edwinvandillen.nl).
2. De webapp ontvangt de chat.
3. De vraag wordt een vector (zelfde embedding-model als bij indexeren).
4. Dichtstbijzijnde artikel-fragmenten komen uit de kennisbank.
5. Die fragmenten + de vraag gaan naar Gemma (aparte GPU-container).
6. Gemma antwoordt in een vast formaat; de UI toont tekst, **bronnen** en vervolghints.

Citations zijn een eigen beat, geen bijzaak onder “antwoord”.

### Blok 4 — Mini-uitleg: wat is een embedding?

Kort, visueel, geen wiskunde. Kern: betekenis als ligging — “harnessing” en “AI betrouwbaar maken” liggen dichter bij elkaar dan “harnessing” en “recepten”. Dit blok maakt tekening 2 begrijpelijk.

### Blok 5 — Tekening 2: hoe de crawler de kennisbank vult

Sitemap → artikeltekst → knippen → vector → kennisbank.

Zeg erbij: zonder deze loop heeft Gemma niets om op te steunen (lege-index-melding in de chat). Zelfde embedding-model als bij vragen — anders zou zoeken op betekenis niet werken.

### Blok 6 — Tekening 3: technische stekkerdoos

Kort, voor de bouwer in iedereen:

- Webstack: één pagina, FastAPI, geen zwaar frontend-framework.
- **App-container** (CPU): UI, orchestratie, embeddings, kennisbank.
- **Ollama-container** (GPU, rechtstreeks): alleen Gemma. Niet in de app-container.
- Communicatie: HTTP op het Docker-netwerk, OpenAI-compatibel. Model wisselen zonder app-rebuild ([ADR-004](../02-architectural/decisions/04-ADR-inference-serving.md), [ADR-009](../02-architectural/decisions/09-ADR-image-compose-deployment.md)).
- Publiek: Cloudflare Tunnel op de host, niet in de app-image.

### Blok 7 — Wat je terugkrijgt, en wat bewust ontbreekt

- Citations als eigen lijst, niet alleen in de lopende tekst.
- Hints die terugleiden naar de blogs.
- Geen permanente chatgeschiedenis.
- Geen fine-tuning: nieuwe posts komen binnen via indexeren, niet via hertrainen.

Optioneel één kleine noot, niet in de hoofdstroom: het antwoord komt in de UI binnen in stukjes; het model zelf streamt nog niet token-voor-token.

## Tekening 1 — Vraag → antwoord (query-time)

Verplicht. Gemma staat **na** retrieval.

```
  ┌─────────────┐     HTTPS      ┌──────────────────────────────┐
  │   Browser   │ ─────────────► │  Webtoepassing (FastAPI)     │
  │  jarvisje   │                │  chat-UI + orchestrator      │
  └─────────────┘                └──────────────┬───────────────┘
         ▲                                      │
         │                                      │  1. embed de vraag
         │                                      ▼
         │                           ┌─────────────────────┐
         │                           │  Embedding          │
         │                           │  (CPU, in de app)   │
         │                           └──────────┬──────────┘
         │                                      │  vector van de prompt
         │                                      ▼
         │                           ┌─────────────────────┐
         │                           │  Kennisbank (RAG)   │
         │                           │  alleen 2 blogs     │
         │                           └──────────┬──────────┘
         │                                      │  fragmenten + urls
         │                                      ▼
         │                           ┌─────────────────────┐
         │     3. antwoord,          │  Prompt bouwen      │
         │        bronnen, hints     │  systeem + context  │
         │                           │  + vraag + history  │
         │                           └──────────┬──────────┘
         │                                      │  HTTP chat-completions
         │                                      ▼
         │                           ┌─────────────────────┐
         │                           │  Gemma              │
         │                           │  Ollama · GPU       │
         │                           │  (aparte container) │
         │                           └──────────┬──────────┘
         │                                      │
         └──────────────────────────────────────┘
                    antwoord terug naar de browser
```

Wat deze tekening moet laten voelen: de kennisbank zit tussen jou en Gemma in. Gemma ziet alleen wat de app heeft opgehaald.

## Tekening 2 — Crawler → kennisbank (ingest-time)

Verplicht. Zelfde embedding-model, ander moment.

```
  edwinvandillen.nl          jeroenteunisse.nl
           │                         │
           └──────────┬──────────────┘
                      ▼
           ┌─────────────────────┐
           │  Crawler            │
           │  sitemap-first      │
           │  nette extractie    │
           └──────────┬──────────┘
                      │  schone artikeltekst
                      ▼
           ┌─────────────────────┐
           │  Chunker            │
           │  overlappinge       │
           │  tekststukken       │
           │  + url, titel, datum│
           └──────────┬──────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │  Embedding          │
           │  tekst → vector     │
           └──────────┬──────────┘
                      │  vector + metadata
                      ▼
           ┌─────────────────────┐
           │  Kennisbank         │
           │  = RAG-index        │
           └─────────────────────┘
                      ▲
                      │  later: query-time zoekt hier
                      │  (tekening 1)
```

Optioneel inset bij blok 4 (embedding in één oogopslag):

```
  "harnessing AI"   ●─────────●  "AI betrouwbaar maken"
                         ╲
                          ●  "pasta recepten"     ← ver weg, wordt niet opgehaald
```

## Tekening 3 — Runtime (stekkerdoos)

Aanbevolen derde tekening. Beantwoordt: Gemma zit niet in de app-container.

```
                         internet
                            │
                            ▼
                   ┌─────────────────┐
                   │ Cloudflare      │
                   │ Tunnel (host)   │
                   └────────┬────────┘
                            │
                         host .15
                            │
          ┌─────────────────┴──────────────────┐
          │                                    │
          ▼                                    ▼
 ┌─────────────────────┐            ┌─────────────────────┐
 │  Docker: app        │   HTTP     │  Docker: ollama     │
 │  FastAPI            │ ─────────► │  Gemma              │
 │  UI + orchestrator  │            │  NVIDIA GPU         │
 │  embeddings  CPU    │            │                     │
 │  kennisbank (volume)│            │                     │
 │  ingest-worker *    │            │                     │
 └──────────┬──────────┘            └─────────────────────┘
            │
            ▼
   host-volume: kennisbank
   (overleeft image-updates)

  * worker = apart proces, zelfde app-image;
    chat blijft bereikbaar tijdens indexeren
    ([ADR-010](../02-architectural/decisions/10-ADR-async-ingestion-worker.md))
```

## Wat op de pagina hoort / niet hoort

**Hoofdverhaal**

- Twee blogs als enige bronnen ([ADR-012](../02-architectural/decisions/12-ADR-jarvisje-rebrand.md)).
- Retrieval vóór het taalmodel.
- Citations en hints.
- Lokaal Gemma, embeddings in de app, kennisbank persistent.
- Crawler + embedding als de leer-loop.
- Twee containers: app (CPU) vs Ollama (GPU).

**Inklappen of weglaten** (operators / Bronnen-tab)

- Poorten, volume-paden, systemd-units, ingest-token.
- ADR-nummers in lopende tekst (links in dit document zijn voor bouwers, niet voor bezoekers).
- Indexering starten, reset, max pages.

**Bewust niet vertellen** (klopt niet met de runtime of is te veel keuken)

- Guardrail-classifiers die we niet hebben. Begrenzing is: alleen twee hosts, prompt-regels, citation-filter.
- Fine-tuning, DGX/vLLM als productiestandaard, Qdrant, hybride BM25.
- Live peek van retrieval-endpoints.

## Uitbreidingen

**Kandidaten voor de eerste bouw**

- **Voorbeeldvraag-walker.** Knop “Volg een vraag” (bijv. *Wat is harnessing?*): stappen in tekening 1 lichten één voor één op. Geen live LLM; didactiek.
- **Live cijfer uit de index.** “Nu in de kennisbank: *N* artikelen van 2 blogs.” Maakt het concreet.
- **Twee dieptes in één pagina.** Elke tekening: korte zin voor iedereen, inklapbaar “technisch” met modelnaam en JSON-vorm. Geen tweede pagina.

**Later, niet in v1 van deze pagina**

- Live retrieval-peek.
- Echte token-streaming vanuit Ollama (productwerk, geen uitlegpagina).
- 3D-animatie van vectorruimte.

## Open keuzes bij bouw

- Walker in v1: ja / nee.
- Live artikel-aantal in v1: ja / nee.
- Tab-naam **Hoe Jarvisje werkt** is het voorstel; bevestigen bij bouw.

## Bouwnotitie (wanneer we dit doen)

Implementatie zit in Software Space (`web/index.html`, tab `architecture`). Dit document is de bron voor *wat* die tab moet vertellen. Na bouw: UI-semver bump (minor: nieuwe uitlegpagina), designer agent, projecties alleen als het platform-overzicht de publieke uitleg noemt. Geen nieuwe ADR tenzij de pagina een architectuurkeuze wijzigt — uitleg van bestaande keuzes is geen ADR.
