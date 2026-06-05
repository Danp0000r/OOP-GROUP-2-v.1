

## What this file does

`services.compatibility.component_matcher` is responsible for:

- accepting free-form user input
- searching the database for matching components
- returning the best matching database record

> It does not decide whether parts are compatible. That is the job of the compatibility checker.

### High-level flow

```text
User Input
  ↓
ComponentMatcher
  ↓
Database Components
  ↓
CompatibilityChecker
  ↓
PerformanceAnalyzer
  ↓
Final Compatibility Report
```

---

## Example user input

```text
Ryzen 7 5700X
RTX 4060
16GB DDR4
```

Possible database entries:

```text
AMD Ryzen 7 5700X
ASUS Dual RTX 4060 OC Edition
Corsair Vengeance 16GB DDR4
```

The matcher must map the user text to the best database component.

---

## Step 1: Normalize text

Both the user query and component data are normalized with `Utils.norm()` before comparison.

```python
Utils.norm("Ryzen-7_5700X")
```

Produces:

```text
ryzen 7 5700x
```

Normalization removes noise from:

- uppercase vs lowercase
- dashes, underscores, and special characters
- extra spaces

So these all become equivalent:

```text
RYZEN 7 5700X
Ryzen-7-5700X
ryzen_7_5700x
```

---

## Strategy 1: Exact match

The first check is exact normalized matching.

```python
if Utils.norm(c.get("name", "")) == query:
```

Example:

- database name: `AMD Ryzen 7 5700X`
- normalized name: `amd ryzen 7 5700x`
- query: `amd ryzen 7 5700x`

If they are equal, the component is returned immediately.

The matcher also checks a normalized component ID:

```python
if Utils.norm(c.get("id", "")) == query:
```

This covers cases where the user types a known internal identifier.

> Exact match is used first because it is the most reliable way to avoid false positives.

---

## Strategy 2: Contains match

If exact matching fails, the matcher looks for substring matches in the normalized component name.

```python
if query in Utils.norm(c.get("name", "")):
```

Example:

- user input: `RTX 4060`
- database name: `ASUS Dual RTX 4060 OC Edition`

This method matches the query inside longer product names.

If multiple components match, the matcher chooses the shortest normalized name:

```python
return min(contains_matches, key=lambda x: len(Utils.norm(x.get("name", ""))))
```

The idea is that the shortest match is usually the base model.

Example lengths:

```text
ASUS Dual RTX 4060 OC Edition = 29 chars
MSI RTX 4060 Gaming X        = 21 chars
RTX 4060                     =  8 chars
```

> The shortest candidate usually represents the cleanest SKU.

---

## Strategy 3: Fuzzy matching

If substring matching still fails, the matcher uses token-based fuzzy matching.

It builds a searchable string from the component name and brand:

```python
search = Utils.norm(c.get("name", "")) + " " + Utils.norm(c.get("brand", ""))
```

Then it compares the query tokens against the searchable tokens.

Example searchable tokens:

```text
{ "amd", "ryzen", "7", "5700x" }
```

User query:

```text
ryzen 5700
```

Query tokens:

```text
{ "ryzen", "5700" }
```

Score calculation:

```python
matched = sum(1 for t in query_tokens if t in tokens)
score = matched / max(len(query_tokens), 1)
```

Example:

```text
1 / 2 = 0.5
```

A component is accepted only when the score is at least `0.95`.

This allows matching on variants such as:

```text
RTX4060
RTX 4060
Asus RTX 4060
RTX-4060
```

---

## detect_components()

This helper turns multi-line input into individual component queries.

Example input:

```python
parts_input = """
Ryzen 7 5700X
RTX 4060
B550M
"""
```

The code then runs:

```python
parts = Utils.split(parts_input)
```

Result:

```python
["Ryzen 7 5700X", "RTX 4060", "B550M"]
```

Then each part is matched with `get_component(part)`.

### Known component example

For a recognized part like `Ryzen 7 5700X`:

```python
{
  "input": "Ryzen 7 5700X",
  "component": { ... },
  "source": "database",
  "verified": True
}
```

### Unknown component example

For an unrecognized part like `Magic GPU 99999`:

```python
{
  "input": "Magic GPU 99999",
  "component": None,
  "source": "unknown",
  "verified": False
}
```

Unknown parts are preserved so the system can report them without failing completely.

---

## Why this matters

This matcher is the translator that converts free-form text into usable component data.

Without it, the compatibility checker would not know:

- CPU socket information
- RAM type details
- GPU wattage
- Motherboard form factor

So the matcher turns raw text into structured records that the rest of the system can use.

### Final flow

```text
User Input
  ↓
ComponentMatcher
  ↓
Database Components
  ↓
CompatibilityChecker
  ↓
PerformanceAnalyzer
  ↓
Final Compatibility Report
```

Result:

```
[ "Ryzen 7 5700X", "RTX 4060", "B550M" ]
```

Then it loops through each entry and calls `get_component(part)`.

### Known component example

For `Ryzen 7 5700X`:

The matcher returns a result like:

```python
{ component: {...}, source: "database", verified: True }
```
```

### Unknown component example

For `Magic GPU 99999`:

If no match is found, the result becomes:

```python
{
  component: None,
  source: "unknown",
  verified: False
}
```
```

## Why this file is important

Without the matcher, the compatibility checker cannot translate user text into real component records.

The compatibility system needs actual specs like:

- CPU socket
- RAM type
- GPU wattage
- Motherboard form factor

But the user only gives text like:

```
Ryzen 7 5700X
RTX 4060
```

So the matcher acts as a translator:

```
User Text
↓
Real Database Component
↓
Specifications
↓
Compatibility Checker
```

## Overall flow

The full system flow is:

```
User Input
     ↓
ComponentMatcher
     ↓
Database Components
     ↓
CompatibilityChecker
     ↓
PerformanceAnalyzer
     ↓
Final Compatibility Report
```
