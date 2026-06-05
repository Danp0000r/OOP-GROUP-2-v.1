# Compatibility Determination Diagram

This diagram shows how compatibility is determined in the system.

```mermaid
flowchart TD
    A[User Input or Component List] --> B[Compatibility Service]
    B --> C[Component Matcher]
    C --> D[Component Loader]
    D --> E[Component Data Map]
    B --> F[Group Components]
    F --> G[Compatibility Checker]
    G --> H[Compatibility Rules]
    H --> I[Socket Check]
    H --> J[RAM Type Check]
    H --> K[PSU Wattage Check]
    H --> L[Case/GPU/Cooler Check]
    G --> M[Compatibility Summary]
    M --> N[Passed / Failed / Warnings]
    B --> O[Performance Analyzer]
    O --> P[Performance Scores]
    P --> Q[Build Report]

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style G fill:#bfb,stroke:#333,stroke-width:2px
    style H fill:#ffd700,stroke:#333,stroke-width:1px
    style N fill:#fcc,stroke:#333,stroke-width:1px
    style Q fill:#cfc,stroke:#333,stroke-width:1px
```

## Explanation

1. `Compatibility Service` receives either raw user input or a list of loaded components.
2. If the input is text, `Component Matcher` resolves it against the available component data.
3. `Component Loader` provides the normalized component data needed for matching and checking.
4. `Compatibility Service` groups matched components into categories.
5. `Compatibility Checker` applies rules such as socket matching, RAM type validation, PSU wattage, and case/cooler/gpu fit.
6. The checker returns a final compatibility summary with pass/fail status and warnings.
7. `Performance Analyzer` may also run to attach performance scores and build recommendations.
