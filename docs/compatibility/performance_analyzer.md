# performance_analyzer.md

This file acts as the **performance engine** of the system.
It does **not** check compatibility.

The Compatibility Checker answers:

```text
Can these parts work together?
```

The Performance Analyzer answers:

```text
How powerful is this build?
```

It estimates:

- Performance Score
- Gaming Tier
- Recommended Resolution
- Estimated FPS
- Bottlenecks
- Upgrade Suggestions

It uses component data and performance scores to generate practical gaming advice.

---

## Main purpose

Flow:

```text
Compatible Build
        ↓
Performance Analyzer
        ↓
Calculate Scores
        ↓
Determine Tier
        ↓
Estimate FPS
        ↓
Analyze Bottlenecks
        ↓
Suggest Upgrades
```

---

## cpu_score()

This function calculates the CPU performance score.

```python
def cpu_score(name_or_component):
```

### Method 1: Database score

If the input is already a component dictionary:

```python
if isinstance(name_or_component, dict):
```

it returns the stored score:

```python
return component["performance_score"]
```

Example:

```json
{
  "name": "Ryzen 7 5700X",
  "performance_score": 80
}
```

Result:

```text
80
```

### Why?

Because the database already contains a score.
The database is the source of truth.

```text
Database
     ↓
Performance Score
     ↓
Analyzer Uses Score
```

### Method 2: Name matching fallback

If the database cant find the input or now performance score:

```text
"Ryzen 7 5700X"
```

The analyzer uses fallback values.

Example lookup table:

```python
{
    "5700x": 80,
    "7800x3d": 95,
    "14900k": 100
}
```

Example:

```text
Ryzen 7 5700X
```

Check:

```python
if "5700x" in name:
```

Result:

```text
80
```

If nothing matches:

```python
return 50
```

Default score:

```text
50
```

---

## gpu_score() fallback

This works the same way, but for graphics cards.

Example component:

```json
{
  "name": "RTX 4060",
  "performance_score": 58
}
```

Result:

```text
58
```

Fallback examples:

```python
{
    "gtx 1650": 25,
    "rtx 3060": 50,
    "rtx 4060": 58,
    "rtx 4090": 100
}
```

Example:

```text
RTX 4090
```

Result:

```text
100
```

---

## tier(cpu_s, gpu_s)

This function classifies the entire build.

It calculates a weighted score:

```python
s = gpu_s * 0.7 + cpu_s * 0.3
```

Notice:

```text
GPU = 70%
CPU = 30%
```

The GPU matters more because gaming performance is usually GPU-dependent.

Example:

```text
cpu_s = 80
gpu_s = 58
```

Calculation:

```text
58 × 0.7 = 40.6
80 × 0.3 = 24
```

Total:

```text
64.6
```

Then the analyzer compares the score to tiers.

Example result for `s = 58`:

- `1080p Ultra`
- `1440p High`
- `60+ FPS`

Example result for `gpu_s = 75`:

- `1440p High`
- `4K Medium-High`
- `60+ FPS`

Example result for `gpu_s = 25`:

- `1080p Medium`
- `60+ FPS`

### Why GPU only?

Because:

```text
Resolution
↓
Mostly GPU-dependent
```

The graphics card determines how many pixels can be rendered efficiently.

---

## fps_disclaimer()

This function returns a warning message.

```python
def fps_disclaimer():
```

Purpose:

```text
FPS is only an estimate
```

Because FPS depends on:

- Game settings
- Drivers
- Windows version
- Background apps
- DLSS / FSR
- Power limits

This prevents users from thinking:

```text
Estimated FPS = Guaranteed FPS
```

---

## fps(cpu_s, gpu_s)

This is one of the most important functions.
It estimates game performance.

### GPU baselines

The code contains baseline FPS values for games.

Example:

```python
"CS2": {
    58: 340
}
```

Meaning:

```text
GPU Score 58
↓
CS2
↓
340 FPS
```

Other games include:

- CS2
- Valorant
- Fortnite
- GTA V
- Cyberpunk

### CPU modifier

The analysis adjusts FPS based on CPU strength.

First calculate:

```python
ratio = cpu_s / gpu_s
```

Example:

```text
80 / 58
```

Result:

```text
1.38
```

Then the code selects a modifier based on that ratio.

---

## Why this file matters

This file is the performance engine, not the compatibility judge.

It turns a compatible build into an estimated gaming profile.

Without it, the system would know whether a build works, but not how well it performs.
