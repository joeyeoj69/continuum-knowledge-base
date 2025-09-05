# Continuum Knowledge Base

!!! info "Continuum KB"
    Strategies, automation, data, and research — updated automatically on every push.

---

## 📂 Sections

- **Strategies** → Breakout models, Super-Squeeze+, scalping, orchestrator.
- **Playbooks** → Operator execution, IBKR setup, deployment guides.
- **Ops** → Secrets, monitoring, roadmaps, status service.
- **Data** → Feeds, adapters, data lake, research datasets.
- **Research** → GME dossier, BBBY bonds, ETF flows, macro catalysts.
- **Appendix** → Glossary, abbreviations, tools, references.

---

## 🔄 Workflow

```mermaid
flowchart LR
  A[Raw Market Data] --> B[Indicators]
  B --> C[Decimal Features (schema v1)]
  C --> D[Scoring Engines (Super-Squeeze+ etc.)]
  D --> E{A+? ≥ 7.0}
  E -- Yes --> F[Operator → IBKR Execution]
  F --> G[Failsafes & Monitoring]
  E -- No --> X[Ignore / Log Only]
