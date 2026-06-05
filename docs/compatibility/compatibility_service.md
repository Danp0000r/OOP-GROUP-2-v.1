# Compatibility Service Reference

This file is the **main controller** of the entire compatibility system.

Think of it as the **manager** that coordinates all other compatibility modules.

It does not load components itself.
It does not match components itself.
It does not check compatibility itself.
It does not calculate FPS itself.

Instead, it tells the other modules what to do and combines their results into one final report.

---

## Big picture

Every other file has one job:

```text
ComponentLoader
↓
Loads components

ComponentMatcher
↓
Finds components

CompatibilityChecker
↓
Checks compatibility

PerformanceAnalyzer
↓
Analyzes performance
```

Somebody needs to coordinate them.
That is:

```text
CompatibilityService
```

---

## Main function

```python
evaluate_build(parts_input)
```

This is usually the only function the frontend needs to call.

Example:

```python
CompatibilityService.evaluate_build(
    "Ryzen 7 5700X, RTX 4060, B550M"
)
```

---

## Step 1: Detect components

First the service determines what kind of input it received.

### Case A: User text

Example:

```text
"Ryzen 7 5700X, RTX 4060"
```

The service calls:

```python
ComponentMatcher.detect_components(parts_input)
```

Flow:

```text
User Input
      ↓
Component Matcher
      ↓
Database Match
```

Result:

```json
[
  { "component": Ryzen5700X },
  { "component": RTX4060 }
]
```

### Case B: Components already loaded

Example:

```python
[
    cpu_component,
    gpu_component
]
```

The service skips matching because the components are already known.

---

## Why this matters

This makes the system flexible.
It can work with:

```text
Raw User Text
or
Database Components
```

---

## Step 2: Find unknown components

After matching the service identifies unmatched inputs:

```python
unknown = [
    i["input"]
    for i in detected
    if i["component"] is None
]
```

Example input:

```text
Ryzen 7 5700X
RTX 4060
Magic GPU 99999
```

Result:

```python
unknown = [
    "Magic GPU 99999"
]
```

The service creates a warning:

```text
Component not found:
Magic GPU 99999
```

Important:

Unknown parts do NOT immediately fail the build.
The system still tries to analyze the parts it understands.

---

## Step 3: Group components

The compatibility checker expects grouped components:

```python
groups = {
   "CPU": cpu,
   "GPU": gpu,
   "RAM": ram,
   "PSU": psu
}
```

Not a random list.

Example before grouping:

```json
[
 CPU,
 GPU,
 RAM,
 PSU
]
```

After grouping:

```python
groups = {
    "CPU": cpu,
    "GPU": gpu,
    "RAM": ram,
    "PSU": psu
}
```

Storage is special:

```python
"Storage": [
    SSD1,
    SSD2
]
```

Why group?

Because later checks need easy access.

Example:

```python
cpu = groups["CPU"]
gpu = groups["GPU"]
```

instead of searching a list every time.

---

## Step 4: Run compatibility checks

Now the service calls:

```python
CompatibilityChecker.check(groups)
```

This is where the actual compatibility logic runs.

The checker returns:

```python
issues
passed
recommendations
watt_est
rec_psu
```

Example feedback:

```text
✓ Socket Match
✓ GPU Fits
✗ PSU Too Weak
```

The service then adds unknown component warnings.

Result:

```text
Issues:
- Unknown Component
- PSU Too Weak
```

---

## Step 5: Determine overall status

Now the service decides:

```text
Compatible?
Warning?
Incompatible?
```

Check for critical issues:

```python
has_crit = any(
  i["severity"] == "critical"
  for i in issues
)
```

Check for unknown parts:

```python
has_unknown = len(unknown) > 0
```

### Compatible

No critical issues.
No unknown parts.

Result:

```text
COMPATIBLE
```

### Warning

No critical issues.
Unknown parts exist.

Result:

```text
WARNING
```

Example:

```text
Build looks okay
but some components
could not be verified
```

### Incompatible

Any critical issue exists.

Result:

```text
INCOMPATIBLE
```

Example:

```text
AM4 CPU
LGA1700 Motherboard
```

Important:

```text
Warning ≠ Failure
```
Only critical issues fail the build.

---

## Step 6: Calculate build price

The service totals component prices.

Example:

```text
CPU = ₱10,000
GPU = ₱18,000
RAM = ₱3,000
```

Calculation:

```text
10000 +
18000 +
3000
```

Result:

```text
₱31,000
```

The service uses:

```python
Utils.num()
```

to safely extract numbers.

Example:

```text
₱10,500
```

becomes:

```text
10500
```

Result:

```text
totalBuildPrice
```

---

## Step 7: Performance analysis

If the build is not incompatible:

```python
if status != "incompatible":
```

the service runs the `PerformanceAnalyzer`.

It calculates:

- CPU Score
- GPU Score
- Build Tier
- Gaming Resolution
- FPS Estimates
- Bottleneck Analysis
- Upgrade Suggestions

Example:

```text
CPU Score = 80
GPU Score = 58
```

Result:

```text
Midrange Build
1080p Ultra
1440p High
```

```text
Cyberpunk:
99 FPS
```

If there is:

```text
CPU
No GPU
```

the analyzer still runs.
Useful for:

- Office PCs
- APUs
- Budget Builds

---

## Step 8: Build output list

The service creates a user-friendly component list.

Example `detectedParts` entry:

```json
{
  "name": "Ryzen 7 5700X",
  "type": "CPU",
  "source": "database",
  "verified": true,
  "price": 10500
}
```

Why?

Because the frontend needs display-ready data.

Example:

```text
Detected Components

CPU
Ryzen 7 5700X

GPU
RTX 4060
```

---

## Step 9: Create final report

Finally everything is packaged together.

The service returns:

```python
{
    compatible,
    status,
    summary,

    buildTier,

    totalBuildPrice,

    wattageEstimate,
    recommendedPsuWattage,

    detectedParts,

    issues,
    passedChecks,

    recommendations,

    bottleneckAnalysis,

    gamingResolution,

    estimatedFps,

    upgradeSuggestions
}
```

---

## Example final output

```text
Compatible: Yes

Status:
Compatible

Build Tier:
Midrange

Total Price:
₱42,000

Estimated Wattage:
350W

Recommended PSU:
550W

Gaming Resolution:
1080p Ultra
1440p High

Issues:
None

Passed Checks:
Socket Match
RAM Match

Estimated FPS:
Cyberpunk:
99 FPS

Upgrade Suggestions:
Upgrade to RTX 4070
```

---

## Complete system flow

```text
User Input
      ↓
CompatibilityService
      ↓
ComponentMatcher
      ↓
Detected Components
      ↓
Group Components
      ↓
CompatibilityChecker
      ↓
Compatibility Results
      ↓
PerformanceAnalyzer
      ↓
Performance Results
      ↓
Calculate Price
      ↓
Create Final Report
      ↓
Return To Frontend
```

---

## Why this file is the most important

Without `compatibility_service.py`, all the other modules would work independently but never connect together.

```text
ComponentMatcher
     ↓
CompatibilityChecker
     ↓
PerformanceAnalyzer
```

would have no coordinator.

`compatibility_service.py` is the **brain of the system** because it manages the entire workflow and produces the single final compatibility report that your frontend displays to the user.
