# Strategy Architecture

```mermaid
flowchart LR
  A[Bars] --> B[Indicators]
  B --> C[Decimal Features]
  C --> D[Scorer]
  D --> E{A+?}
  E -- Yes --> F[Operator → IBKR]
```
