okf_version: "0.1"

# Context Space — Sogyo Kennis-Chatbot

> **Agents:** start hier. Lees [werkwijze](core-domain/04-delivery/werkwijze.md), daarna vision/scope/ADRs.  
> Repo-contract: [AGENTS.md](../AGENTS.md).

Single source of truth voor **wat** we bouwen en **waarom**. Inhoud in [core-domain/](core-domain/).

## Ruimtes

| Ruimte | Pad | Inhoud |
|--------|-----|--------|
| Context Space | `context-space/core-domain/` | Domein, ADRs, werkwijze, roadmap |
| Software Space | `src/`, `web/`, `scripts/` | Applicatie |
| Infra | `infra/` | Compose, deploy, runbooks |

## Core domain

* [01 Strategic](core-domain/01-strategic/) — vision, scope, succescriteria  
* [02 Architectural](core-domain/02-architectural/) — ADRs, software design  
* [03 Technical](core-domain/03-technical/) — taal, bronnen, aannames  
* [04 Delivery](core-domain/04-delivery/) — werkwijze, [roadmap](core-domain/04-delivery/roadmap.md), use cases  

## Projecties & harnessing

* [Projecties](projections/) — HTML voor operators (`output/`)  
* [Harnessing](harnessing/) — Designer Agent findings  
* [Log](log.md)  

## Leesvolgorde voor agents

1. [werkwijze.md](core-domain/04-delivery/werkwijze.md)  
2. [vision.md](core-domain/01-strategic/vision.md) + [domein-scope.md](core-domain/01-strategic/domein-scope.md)  
3. [ubiquitous-language.md](core-domain/03-technical/ubiquitous-language.md)  
4. Relevante [ADRs](core-domain/02-architectural/decisions/)  
5. Bij deploy: `infra/runbooks/`  
