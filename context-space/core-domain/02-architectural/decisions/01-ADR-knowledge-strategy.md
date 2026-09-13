---
type: ADR
title: "Knowledge Strategy — RAG"
description: "RAG-first zonder fine-tuning."
status: accepted
tags: [rag, knowledge]
timestamp: 2026-06-26T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
---

# ADR-001: Knowledge Strategy - RAG als primaire aanpak

## Status
Accepted — **bronnenlijst superseded** door [ADR-012](12-ADR-jarvisje-rebrand.md) (alleen edwinvandillen.nl en jeroenteunisse.nl). RAG-first zonder fine-tuning blijft.

## Datum
2026-06-26 · reality check 2026-08-08: RAG + Chroma geldig · 2026-09-13: zes sites → twee blogs (ADR-012).

## Context
Oorspronkelijk: chatbot die verwijst naar content op sogyo.nl, jeroenteunisse.nl, edwinvandillen.nl, augmentedorganisation.nl, intentdriven.nl en augmentedengineering.nl. Sinds ADR-012 alleen de twee blogs.

De content bestaat uit:
- Diepgaande blogartikelen (filosofisch/strategisch)
- Tools en canvases (Augmented Organisation, Intent Driven Engineering)
- Modellen en frameworks rond AI-augmentatie in software engineering

Belangrijke eisen:
- Altijd concrete verwijzingen naar specifieke bronnen.
- Makkelijk updaten wanneer er nieuwe blogs of tools verschijnen.
- Geen hallucinaties over onderwerpen buiten de content.
- Beide doelgroepen (sollicitanten en bedrijven) bedienen.

## Decision
We kiezen voor een **Retrieval-Augmented Generation (RAG)** aanpak als primaire strategie.

We starten **zonder fine-tuning** van het taalmodel op de content.

### Rationale
- RAG maakt expliciete citations eenvoudig en betrouwbaar (we kunnen metadata met URL + titel teruggeven).
- Nieuwe content kan direct worden toegevoegd via de ingestion pipeline zonder hertrainen.
- Beter traceerbaar en debugbaar ("waarom gaf het dit antwoord?").
- Lagere complexiteit en kosten in de beginfase.
- Past bij het doel: de bestaande content promoten in plaats van een nieuw "model" bouwen.

## Consequences
### Positief
- Hoge controle over wat er gezegd wordt.
- Eenvoudige update-cyclus (4-6 uur).
- Goede grounding mits retrieval van hoge kwaliteit is.
- Makkelijk te evalueren (welke chunks werden gebruikt?).

### Negatief / Risico's
- Kwaliteit hangt sterk af van chunking en retrieval (moet goed zijn bij abstracte content).
- Grotere context windows nodig bij lange gesprekken.
- Retrieval kan falen bij vage of meta-vragen.

## Alternatives Considered
- **Fine-tuning / Continued pre-training**: Goed voor stijl en domein-kennis, maar citations worden moeilijker, updates kostbaar, en risico op hallucinaties buiten de getrainde data.
- **RAG + lichte LoRA / adapters**: Mogelijk later als experiment. Niet in eerste versie.
- **Pure LLM zonder retrieval**: Volledig onacceptabel omdat het niet verwijst naar de bronnen en buiten domein gaat zweven.

## Gerelateerde ADRs
- ADR-002: Guardrails
- ADR-007: Ingestion Cadence
- ADR-008: Citations and Grounding

## Besloten door
Edwin + architectuur sessie met Grok
