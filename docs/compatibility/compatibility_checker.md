# Compatibility Checker Reference

This file acts as the **rule engine** of the compatibility system.

Its job is to determine whether the selected PC components can actually work together.

Unlike the Component Loader, which only loads data, and the Component Matcher, which only finds components, this file makes the compatibility decisions.

Think of it as the system's **judge**.

```text
User Components
      ↓
Compatibility Checker
      ↓
Compatible?
      ↓
Yes / No / Warnings
```

---

## Main purpose

The checker receives grouped components and returns a compatibility summary.

Input structure:

```python
groups = {
    "CPU": cpu,
    "Motherboard": mb,
    "RAM": ram,
    "GPU": gpu,
    "PSU": psu,
    "Case": case,
    "Cooling": cooler
}
```

Output tuple:

```python
(
    issues,
    passed,
    recommendations,
    watt_est,
    rec_psu
)
```

Meaning:

- `issues` — compatibility problems found
- `passed` — successful checks
- `recommendations` — suggested improvements
- `watt_est` — estimated system wattage
- `rec_psu` — recommended PSU size

---

## Step 1: Get components

At the beginning, the checker extracts values from the grouped build:

```python
cpu = groups.get("CPU")
mb = groups.get("Motherboard")
ram = groups.get("RAM")
gpu = groups.get("GPU")
psu = groups.get("PSU")
case = groups.get("Case")
cooler = groups.get("Cooling")
storage = groups.get("Storage", [])
```

Example assignment:

```text
cpu = Ryzen 7 5700X
mb = MSI B550M
ram = Corsair DDR4
gpu = RTX 4060
```

Now the checker has all parts needed for comparison.

---

## CPU socket vs motherboard socket

This is one of the most important checks.

### Get sockets

```python
cs = cpu_socket
ms = motherboard_socket
```

Example:

```text
CPU Socket = AM4
Motherboard Socket = AM4
```

### Compare

```python
if cs != ms:
```

Python asks:

```text
AM4 != AM4
```

Result:

```text
False
```

No problem.

### Passed check

```text
✓ Socket: AM4
```

### Bad example

```text
CPU Socket = AM4
Motherboard Socket = LGA1700
```

Check:

```text
AM4 != LGA1700
```

Result:

```text
True
```

Issue created:

```text
CRITICAL:
CPU and motherboard socket mismatch
```

Why?

Because the CPU physically cannot fit.

```text
Wrong Socket
↓
Cannot Install CPU
↓
Build Fails
```

---

## RAM type vs motherboard

The checker verifies that the motherboard supports the chosen RAM type.

Example:

```python
rt = "DDR4"
mr = "DDR4"
```

Check:

```python
if rt != mr:
```

Result:

```text
False
```

Passed.

### Bad example

```python
rt = "DDR5"
mr = "DDR4"
```

Check:

```text
DDR5 != DDR4
```

Result:

```text
True
```

Issue:

```text
CRITICAL:
RAM type mismatch
```

Why?

Because DDR4 and DDR5 use different slots.

```text
DDR5 RAM
↓
DDR4 Motherboard
↓
Cannot Install
```

---

## RAM vs CPU support

Even if the motherboard supports the RAM, the CPU must also support it.

Example:

```python
cr = ["DDR4"]
rt = "DDR5"
```

Check:

```python
if rt not in cr:
```

Becomes:

```python
if "DDR5" not in ["DDR4"]:
```

Result:

```text
True
```

Issue:

```text
CPU does not support DDR5
```

This is a second layer of protection.

```text
Motherboard Check
      +
CPU Check
```

Both must pass.

---

## PSU wattage estimate

The checker estimates power consumption from CPU and GPU.

First it reads power values:

```python
cpu_w = Utils.num(cpu.get("specs", {}).get("tdp", 65))
gpu_w = Utils.num(gpu.get("specs", {}).get("tdp", 100))
```

Example:

```text
CPU = 65W
GPU = 115W
```

Then it calculates:

```python
watt_est = (cpu_w + gpu_w + 100) * 1.25
```

Example:

```text
(65 + 115 + 100) * 1.25
```

```text
280 * 1.25
```

```text
350W
```

Estimated system load:

```text
350W
```

### Why add 100W?

To account for:

- motherboard
- RAM
- storage
- fans
- USB devices

### Why multiply by 1.25?

To add safety headroom.

```text
System Uses 280W
↓
Recommend More Than 280W
↓
350W Estimate
```

---

## Recommended PSU

The checker chooses a recommended PSU size from:

```python
[450, 500, 550, 600, 650, 750, 850, 1000]
```

Example:

```text
watt_est = 350W
```

Recommended result:

```text
450W
```

If the user PSU is too small:

```text
300W
```

Issue:

```text
CRITICAL:
PSU wattage insufficient
```

If the user PSU is large enough:

```text
650W
```

Passed:

```text
✓ PSU sufficient
```

---

## Motherboard vs case size

The checker verifies that the motherboard fits the case.

The fit rules are:

```python
fits = {
    "ATX": ["ATX", "MATX", "MICROATX", "ITX"],
    "MATX": ["MATX", "MICROATX", "ITX"],
    "ITX": ["ITX"]
}
```

Meaning:

```text
Big Case
Can Fit Small Board
```

Example:

```text
ATX Case
MicroATX Board
```

Works.

### Bad example

```text
Mini ITX Case
ATX Motherboard
```

Result:

```text
CRITICAL:
Motherboard does not fit case
```

---

## GPU clearance check

The checker verifies whether the graphics card physically fits the selected case.

Example:

```python
gl = 320
cl = 340
```

Meaning:

```text
GPU Length = 320mm
Case Limit = 340mm
```

If the GPU is shorter than or equal to the case limit, the check passes.

If the GPU is longer, it creates a critical issue.

---

## Why this file matters

This file is the compatibility system's judge.

It takes the translated component data and applies the rules that determine whether a build is valid.

Without it, the app would have components but no way to decide if they can work together.
