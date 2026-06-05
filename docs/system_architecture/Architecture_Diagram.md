# Architecture Diagram

Below is a high-level Mermaid diagram representing core components and data flows.

```mermaid
flowchart LR
  Browser[Frontend\n(templates + static)] -->|HTTP| Routes[Routes\n(routes/)]
  Browser -->|Static Assets| Static[static/]
  Routes --> Services[Services\n(services/)]
  Services --> Models[Models\n(models/)]
  Services --> DB[Database\n(database/ db.py)]
  Services --> Cache[Cache\n(services/cache.py)]
  Services --> External[External APIs\n(pricing, repos)]
  DB -->|reads/writes| DataFiles[data reset/]
  Services -->|logs| Activity[Activity Service\n(services/activity/)]

  subgraph Backend
    Routes
    Services
    Models
    DB
  end

  classDef box stroke:#333,stroke-width:1px,fill:#f8f8f8;
  class Browser,Routes,Services,Models,DB,Static,Cache,External,Activity,DataFiles box;
```

Export notes:
- To convert this to PNG/SVG, use VS Code Mermaid preview or an online Mermaid renderer.

---
Generated on: 2026-06-05
