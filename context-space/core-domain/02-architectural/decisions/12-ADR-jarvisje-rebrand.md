---
type: ADR
title: "Jarvisje — rebrand, twee bronnen, iframe-embed"
description: "Product wordt Jarvisje; kennis alleen edwinvandillen.nl en jeroenteunisse.nl; look & feel van de blog; compact iframe."
status: accepted
tags: [rebrand, sources, embed, ui]
timestamp: 2026-09-13T00:00:00Z
traces_to:
  - /core-domain/01-strategic/vision.md
  - /core-domain/01-strategic/domein-scope.md
  - /core-domain/03-technical/kennisbronnen.md
  - /core-domain/02-architectural/decisions/01-ADR-knowledge-strategy.md
---

# ADR-012: Jarvisje — productrebrand, twee kennisbronnen, embed

## Status
Accepted

## Datum
2026-09-13

## Context

De chatbot is gebouwd als **Sogyo Kennis-Chatbot**: zes websites (sogyo.nl plus blogs en framework-sites), doelgroepen sollicitant/bedrijf, groene Sogyo-UI. De publieke host is al `jarvisje.com`; het chatpaneel heette intern al Jarvisje.

De productintentie verandert: Jarvisje wordt onderdeel van [edwinvandillen.nl](https://edwinvandillen.nl/) (thema *Edwin Blog*, dark/light). De WordPress-template krijgt een gereserveerde regio; de chatbot wordt daar als compact iframe opgenomen. Kennis mag alleen nog artikelen van **edwinvandillen.nl** en **jeroenteunisse.nl** bevatten. Alle Sogyo-productreferenties (UI, prompts, package, docs, live infra-namen) verdwijnen.

RAG, citations, lokale inference op `.15` en de werkwijze (commit, designer, projecties) blijven.

## Decision

1. **Naam.** Het product heet **Jarvisje**. Ondertitel (klein): *een chatbot rondom de wereld van AI*. Geen Iron Man-beeldmerk of Marvel-assets.
2. **Kennisbronnen.** Alleen `https://edwinvandillen.nl` en `https://jeroenteunisse.nl`. Overige domeinen uit de allowlist. Bestaande vector-index wissen en opnieuw opbouwen; retrieval filtert op die hosts; citations van andere hosts worden geweigerd. Incremental ingest is onvoldoende om oude chunks te verwijderen.
3. **Doelgroep.** Lezers van die blogs, niet sollicitanten/bedrijven. Geen rol-onboarding (sollicitant vs bedrijf).
4. **Look & feel.** Design tokens 1-op-1 van *Edwin Blog* (dark default, `[data-theme="light"]`). Geen Sogyo-groen.
5. **Embed.** Compacte chat-only view via `/?embed=1` in een iframe op edwinvandillen.nl. Thema-sync: initiële `?theme=` plus `postMessage` `{ type: "edwin-theme", theme: "dark"|"light" }` van de parent. Standalone `jarvisje.com` blijft voor beheer (bronnen, indexering, opbouw).
6. **Rebrand-diepte.** Inclusief Python-package (`jarvisje`), compose/image/container-namen, systemd-units en hostpaden op `.15`. Cutover is een geplande ops-stap. Git-historie en artikeltekst in de twee blogs worden niet herschreven.
7. **Frame policy.** Alleen `'self'` en `https://edwinvandillen.nl` mogen framen (`Content-Security-Policy: frame-ancestors`).

## Consequences

### Positief
- Eén herkenbaar product op de persoonlijke blog, visueel gelijk aan de site.
- Geen Sogyo- of framework-sites meer in antwoorden.
- Beheer blijft op jarvisje.com, los van de WordPress-pagina.

### Negatief / risico's
- Productie-cutover (paden, units, image) kent korte downtime.
- Geen visuele Iron Man-identiteit; de naam is genoeg.
- Iframe + third-party localStorage: thema móet via postMessage, niet via gedeelde storage.

## Alternatives considered

- Alleen UI-rebrand, package/infra `sogyo_*` laten staan — verworpen; expliciet alle productreferenties weg.
- JS-widget i.p.v. iframe — meer CSS-conflicten met Elementor; iframe isoleert look & feel.
- Zwevende chatbubbel — niet gevraagd; later eventueel.
- Bronnen via `.env` in plaats van code — niet nodig voor twee vaste hosts; allowlist blijft in config.

## Gerelateerde ADRs
- ADR-001: Knowledge Strategy (bronnenlijst superseded)
- ADR-002: Guardrails (doelgroep/domein-framing)
- ADR-003: Primary language (voorbeelden)
- ADR-008: Citations
- ADR-009: Image + compose (paden/unitnamen)
- ADR-011: Secrets (ongewijzigd)

## Besloten door
Edwin (plan 2026-09-13)
