---
type: Scope
title: "MVP scope — beantwoorde open vragen"
description: "Archief van interviewbeslissingen tijdens scope-definitie."
tags: [mvp, decisions]
timestamp: 2026-06-26T00:00:00Z
---

# Open vragen — beantwoord (archief)

- [x] Alle 6 bronnen volledig indexeren voor MVP.
- [x] Streaming is must-have.
- [x] Onboarding i.p.v. aparte modes: welkom + rol + interesse ([onboarding-flow](/core-domain/04-delivery/use-cases/onboarding-flow.md)).
- [x] Gematigde weigering bij randgevallen; consent bij lastige sessies.
- [x] Custom HTML/JS UI (geen Gradio).
- [x] Broad coverage scraping, geen strenge pagina-prioritering.
- [x] Scraper: Python + BeautifulSoup/Trafilatura/Playwright; respect robots.txt.
- [x] Vector store: start Chroma, optioneel Qdrant later.
- [x] Model: sterk NL + lange context (uiteindelijk Gemma-4 op DGX).
- [x] Geen LangChain/LlamaIndex — pure Python + Pydantic + httpx; Software Designer Agent.
- [x] Evaluatieset: 20–25 handmatige vragen.
- [x] Consent/share-session: alleen bij lastige gevallen; opslag in `gebruikers-feedback/`.
- [x] Embeddings: BGE-M3 (multilingual).
- [x] Hints in dezelfde LLM-call via structured output.