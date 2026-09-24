---
type: ADR
title: "Bronpassing — indicator naast het antwoord"
description: "De lezer ziet hoe dicht een antwoord bij de artikelen ligt. Afstand weigert niet."
status: accepted
tags: [guardrails, grounding, ui]
timestamp: 2026-09-24T00:00:00Z
traces_to:
  - /core-domain/02-architectural/decisions/02-ADR-guardrails.md
  - /core-domain/02-architectural/decisions/08-ADR-citations-grounding.md
---

# ADR-013: Bronpassing

## Status
Accepted

## Datum
2026-09-24

## Context
Een similarity search heeft altijd een buurman. Ook een vraag die de blogs niet raakt krijgt fragmenten, en die gaan naar Gemma. Twee metingen op de live index (24 september 2026) laten zien wat daaruit komt:

| Tekst | Beste afstand | Bronpassing (1 − afstand) | Bronnen in de UI |
|---|---:|---:|---:|
| Antwoord op intentie-gedreven engineering | 0,13 | 0,87 | 2 |
| Antwoord op "wie is hoxha" | 0,38 | 0,62 | 0 |
| Grap uit het model, niet uit de blogs | 0,52 | 0,48 | 0 |

De Hoxha-vraag zelf zat op 0,56. Het antwoord schoof naar 0,38 omdat het model het dichtstbijzijnde artikel napraatte, zonder bronnummer. Een lege bronnenlijst betekent dus niet dat de tekst losstaat van de artikelen. De grap had ook geen bronnen, en lag wél ver van de index.

ADR-002 noemt een vroeg filter op afstand. Dat filter is niet gebouwd, en één drempel op de vraag scheidt deze gevallen niet: een echte vraag over het chatbot-artikel zat met zijn beste treffer (0,51) tussen de grap (0,49) en Hoxha (0,56).

## Decision
We weigeren een antwoord niet op afstand. Na het antwoord tonen we een indicator, **bronpassing**, en laten we de lezer zien hoe het antwoord zich tot de artikelen verhoudt.

1. **Bronpassing van het antwoord.** De app embedt het antwoord met hetzelfde model als de vraag (CPU) en neemt de cosinusafstand tot het dichtstbijzijnde fragment. Bronpassing is `1 − afstand`, begrensd op 0 tot 1. Hoger is dichter bij een artikel.
2. **Band**, voorlopig, gelegd tussen de drie metingen hierboven:
   - sterk: 0,75 of hoger
   - matig: vanaf 0,55
   - zwak: daaronder
   - onbekend: de afstand van het antwoord kon niet worden berekend
3. **Aantal bronnen** dat de lezer ook echt te zien krijgt, na de citatie-uitlijning. Dat getal staat naast de band. Het is geen bewijs dat de tekst losstaat van de blogs.
4. **Eén extra zin**, alleen als de vraag zelf onder 0,55 zit én het antwoord minstens 0,10 dichter bij een artikel ligt dan de vraag. Dan is het model naar een naburig artikel geschoven. De zin noemt dat, en bij die zin de titel van dat artikel. Het glossarium-antwoord (vraag 0,65, antwoord 0,87) krijgt de zin niet. De grap (antwoord niet dichter dan de vraag) ook niet. Hoxha wel.
5. **Klik** op de indicator opent de sectie Bronpassing op de tab *Hoe Jarvisje werkt*. In de embed-weergave opent die pagina in een nieuw tabblad, omdat die tab in het iframe verborgen is.
6. De indicator is geen kans dat de tekst waar is. Een antwoord zonder retrieval (lege index) krijgt hem niet.

De grenzen 0,75, 0,55 en 0,10 blijven voorlopig tot de evaluatieset uit de roadmap ze kan verschuiven.

## Consequences
- De lezer ziet het verschil tussen een bijna-citaat, een navertelling van een buurartikel, en een antwoord uit het model zelf.
- Eén samengevoegd cijfer doen we niet: een lege bronnenlijst zou Hoxha en de grap op elkaar drukken, terwijl hun bronpassing 0,62 tegen 0,48 is.
- Elke chatbeurt met een modelantwoord doet één extra embedding en één extra zoekopdracht.
- Een goed antwoord waarvan Gemma de bronnummers vergeet, houdt een hoge bronpassing en toont 0 bronnen. Dat is het eerlijke plaatje, geen weigering.

## Alternatives considered
- Vroeg weigeren op de afstand van de vraag. De drie metingen overlappen met een echte lezersvraag.
- Alleen de bronnenlijst. Die was bij Hoxha én bij de grap leeg.
- Alleen de afstand van het antwoord, zonder bronnenaantal. Dan verdwijnt het signaal dat een navertelling geen verwijzing heeft.
- Een vaste disclaimer "dit is algemene kennis" onder elk ver antwoord. Bij Hoxha zou die zin onwaar zijn: dat antwoord is een navertelling van een artikel.

## Gerelateerde ADRs
- ADR-002: gematigde guardrails; de afstand wordt getoond, niet als poort gebruikt
- ADR-008: de bronnen in de indicator zijn de lijst die de lezer ziet
