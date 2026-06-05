# Build Finder Diagram

This diagram shows the build finder and repair flow used by the application.

```mermaid
flowchart TD
    A[User starts questionnaire] --> B[Questionnaire Service]
    B --> C[Collect platform, budget, usage, preferences]
    C --> D[Build Fix Service]
    D --> E[Compatibility Service]
    E --> F[Evaluate build compatibility]
    F --> G{Compatible?}
    G -- Yes --> H[Return compatible build]
    G -- No --> I[Identify issues]
    I --> J[Fix PSU / RAM / Cooler / GPU / Socket]
    J --> K[Re-evaluate compatibility]
    K --> G
    H --> L[Performance / recommendation summary]
    K -- Fixed --> H
    K -- Still incompatible --> M[Return failed build suggestions]

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style D fill:#bfb,stroke:#333,stroke-width:2px
    style F fill:#ffd700,stroke:#333,stroke-width:1px
    style M fill:#fcc,stroke:#333,stroke-width:1px
    style L fill:#cfc,stroke:#333,stroke-width:1px
```

## Explanation

1. The user begins a questionnaire flow to capture platform, budget, and usage needs.
2. `Questionnaire Service` gathers answers and passes them to the build finder logic.
3. `Build Fix Service` evaluates the current build through `Compatibility Service`.
4. If the build is compatible, it returns a compatible build summary.
5. If not, it identifies issues and applies repair strategies.
6. The build is re-evaluated until it is fixed or no safe fixes remain.
7. The final result includes either a fixed compatible build or guidance for the user.
