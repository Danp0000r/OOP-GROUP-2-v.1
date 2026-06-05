# Questionnaire Service Overview

## Purpose

The Questionnaire Service is responsible for converting a user's preferences into a complete and compatible PC build recommendation.

It acts as the bridge between the questionnaire answers and the final recommended computer system.

---

## Main Function

The main function is:

```python
get_build_recommendation(answers)
```

This function:

- Reads the user's questionnaire answers
- Determines the preferred platform, budget, and use case
- Generates possible PC builds
- Selects the most suitable build
- Checks compatibility
- Repairs incompatible builds if necessary
- Returns the final recommendation

The result is cached for 5 minutes to improve performance.

---

## Step 1: Read User Preferences

The service first reads the user's answers, including:

- Intended use (Gaming, Office, Content Creation)
- Budget level
- Preferred platform (AMD or Intel)
- Preferred form factor
- Preferred cooling style

These answers guide all later decisions.

---

## Step 2: Allocate Budget

Based on the selected use case, the system distributes the budget among different components.

### Example Allocations by Use Case

| Use Case | GPU | CPU | Motherboard | RAM | Storage | PSU | Cooling | Case |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Education / Office | 25% | 20% | 15% | 15% | 10% | 8% | 4% | 3% |
| Gaming | 40% | 20% | 10% | 10% | 8% | 9% | 5% | 4% |
| Streaming / Creation | 30% | 25% | 12% | 10% | 8% | 8% | 4% | 3% |

Gaming builds prioritize GPU performance, while streaming and content creation builds allocate more budget to the CPU. Education and office builds are more balanced, with slightly higher shares for motherboard and RAM to ensure stable productivity systems.

---

## Step 3: Generate Candidate Builds

The system generates multiple possible PC configurations.

For every CPU candidate, three build variants are created:

- Minimum (Budget)
- Mid-Range
- Maximum (Premium)

Each build automatically selects:

- Compatible motherboard
- Matching RAM
- Appropriate GPU
- Storage
- Cooling
- Power Supply
- Case

The Compatibility Service is then used to validate every generated build.

---

## Step 4: Rank and Categorize Builds

All generated builds are ranked according to:

1. Compatibility
2. Performance Score

Compatible and higher-performing builds receive higher priority.

The builds are then divided into three price categories:

- Low Cost
- Normal Cost
- High Cost

This classification is based on the current build pool rather than fixed price limits.

---

## Step 5: Select the Best Recommendation

The service selects a build according to the user's chosen budget.

### Example

- Low Cost → Best budget build
- Normal Cost → Best balanced build
- High Cost → Highest-performance build

If no build exists in the requested category, the system automatically selects the closest available alternative.

---

## Step 6: Verify Compatibility

Before returning a recommendation, the selected build is analyzed again using:

```python
CompatibilityService.evaluate_build()
```

This ensures all selected components remain compatible.

The system checks:

- CPU and motherboard socket compatibility
- RAM compatibility
- PSU requirements
- GPU clearance
- Case compatibility
- Cooling compatibility

---

## Step 7: Automatic Build Repair

If incompatibilities are detected, the Build Fix Service attempts to repair the build automatically.

Possible fixes include:

### PSU Fix

Replaces an underpowered PSU with a higher-wattage model.

### RAM Fix

Replaces incompatible RAM with a compatible alternative.

### Cooler Fix

Resolves cooler height and radiator compatibility issues.

### GPU Fix

Replaces oversized GPUs or selects a larger compatible case.

### Socket Fix

Resolves CPU and motherboard socket mismatches.

### Form Factor Fix

Ensures the motherboard fits inside the selected case.

After every repair, compatibility is checked again.

---

## Final Output

The service returns:

- Recommended components
- Component IDs
- Total price
- Compatibility report
- Build score
- Price category
- User questionnaire answers

This information is displayed on the recommendation page.

---

## Importance of the Questionnaire Service

The Questionnaire Service is the core recommendation engine of the system.

It does more than simply select components. It:

- Interprets user requirements
- Generates multiple build candidates
- Chooses the most suitable configuration
- Validates compatibility
- Repairs incompatible builds

Without this service, the questionnaire would not be able to generate reliable PC recommendations.
