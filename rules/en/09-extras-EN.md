# Extras: Convention & Maintenance (EN)

> Applies to the `extras` field on **recipes, foods and units**.

This document covers creation and cleanup together, because `extras` is not an entity but a field — and because maintaining it takes exactly one pass.

## Principle

`extras` is a free key-value object with no schema. That is precisely why it is the first place a well-kept database runs wild: everything nobody wants to find a home for lands here, and nobody notices, because the field is barely visible in the interface.

> **Prime directive:** `extras` is the **last** resort, not the easiest one. Anything that fits an existing field goes there — even when that is more work.

> **Second rule:** a key not in the register (§3) does not exist and gets deleted on the next pass.

---

## 1. What `extras` is **not**

| Temptation | Why it is wrong | Correct home |
| --- | --- | --- |
| `extras.prep_time` | `prepTime` exists | recipe field |
| `extras.vegetarian` | classification for filtering | tag |
| `extras.note` | prose for cooking | `notes[]` (Recipes §8) |
| `extras.source` | `orgURL` exists | recipe field |
| `extras.rating` | `rating` exists | recipe field |
| `extras.calories` | `nutrition` exists | recipe field |

**The decisive technical reason:** cookbook filters read recipe fields — categories, tags, tools, `rating`, `lastMade` — and **not `extras`**. Anything you might ever filter by is functionally dead in `extras`. This is the commonest and costliest mistake with this field.

---

## 2. When `extras` is justified

Three cases, and no others:

1. **Foreign-system identifiers.** The ID from an import's source system, a GTIN on a food, a supplier's article number. Data Mealie does not know and never will.
2. **Automation.** Flags for external tools — Home Assistant, n8n, your own scripts. Nothing a human reads in the interface.
3. **Household-specific values with no field.** A food's usual shop, its default price, its shelf in the store cupboard.

All three share one trait: **machines read it, people do not.** The moment a human is meant to see the value while cooking or shopping, `extras` is the wrong home.

---

## 3. Key register (mandatory)

Keep a register listing every permitted key: name, entity, purpose, value format, owning system. Without it `extras` is unmaintainable, because you cannot tell a typo from a new key.

### 3.1 Name form
`namespace.key` — both lowercase, only `a–z`, `0–9`, `.` and `_`. No spaces, no accents, no hyphens.

The namespace names the **system**, not the topic:

| Namespace | Meaning |
| --- | --- |
| `import.` | came from an import |
| `pantry.` | store cupboard and shopping data |
| `automation.` | read or written by external tools |
| `legacy.` | carried over from an old database, for traceability only |

### 3.2 Example register

| Key | Entity | Purpose | Format |
| --- | --- | --- | --- |
| `import.source_id` | recipe | ID in the source system | string |
| `import.imported_at` | recipe | import timestamp | ISO-8601 |
| `pantry.gtin` | food | barcode | 8–14 digits |
| `pantry.shelf` | food | shelf in the store cupboard | string |
| `pantry.default_price` | food | price per unit | decimal as string |
| `automation.print_label` | recipe | read by the label printer | `true` / `false` |
| `legacy.old_unit` | unit | name before metrication | string |

### 3.3 Values
- **Always strings.** The field allows more, but mixed types break every script that walks the corpus.
- Booleans as lowercase `true` / `false`
- Dates as ISO-8601: `2026-08-10`
- Numbers with a full stop as decimal separator and no unit in the value: `2.49`, not `£2.49`
- **No lists, no nested objects.** Anyone needing a list needs an entity.
- **No personal data.** `extras` travels with exports and shares and is nowhere marked confidential.

---

## 4. Maintenance (one pass)

**Step 1 — Inventory.** Read every key occurring across recipes, foods and units, with counts. That is already half the work: usually there are fewer than twenty distinct keys, and half of them are typos.

**Step 2 — Reconcile against the register.**

| Finding | Action |
| --- | --- |
| in the register, format correct | leave it |
| in the register, format wrong | normalise the value |
| typo or spelling variant of a registered key | rename |
| fits a real field (§1) | **move it there**, then delete |
| occurs exactly once and nobody recognises it | delete |
| justified under §2 but unregistered | **register it** — do not delete |

**Step 3 — Verification.** No key outside the register; no value of a type other than string; no personal data; every registered key has an owning system. A key no system claims is a deletion candidate on the next pass.

---

## 5. Checklist

**Before writing an extra**
- [ ] Is there genuinely no suitable field (§1)?
- [ ] Will the value ever be needed for filtering? Then it must **not** go here.
- [ ] Does it fall under one of the three justified cases (§2)?
- [ ] Does a machine read it rather than a person?
- [ ] Is the key in the register — or being added to it now?
- [ ] Name form `namespace.key`, lowercase, no accents?
- [ ] Value as a string, ISO dates, full stop as decimal separator, no unit in the value?
- [ ] No personal data?

**When maintaining**
- [ ] All keys inventoried across all three entities?
- [ ] Keys with a real destination field moved rather than deleted?
- [ ] Single occurrences checked and removed?
- [ ] Does every registered key have an owning system?
