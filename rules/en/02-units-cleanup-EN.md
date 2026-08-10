# Units: Cleaning Up the Existing Corpus (EN)

> Companion to **Units: Creating & Mapping**. *Create §x* points there; *Cleanup §x* points to **Food Rules (EN): Cleaning Up the Existing Corpus**.

## Principle

Units are few, but each hangs off many ingredient lines. A wrongly merged unit silently corrupts hundreds of amounts — and unlike a food error, nobody notices while cooking, because the number still looks plausible.

> **Default action: change nothing without evidence.** Before the first write: full export, reference count per unit, changelog table, dry-run (Cleanup §1).

---

## 1. Pass order

| # | Pass | Nature | Risk |
| - | ---- | ------ | ---- |
| 0 | Inventory | read-only | none |
| 1 | Hygiene | non-destructive | low |
| 2 | Abbreviation collisions | non-destructive | low |
| 3 | Merging | **destructive** | high |
| 4 | **Eliminating non-metric units** | **destructive** | **very high** |
| 5 | Completing fields | non-destructive | low |
| 6 | Pruning | destructive | medium |
| 7 | Verification | read-only | none |

Pass 4 is the largest and riskiest in the whole rule set, because it changes **amounts**, not units. It comes after merging so the same non-metric unit is not converted twice under two duplicate records.

---

## 2. Pass 0 — Inventory

- Reference count per unit
- Units with no `abbreviation`, no `pluralName`, no `description`
- Abbreviations attached to more than one unit — **hard error**
- **Every non-metric unit** and its reference count → the worklist for Pass 4
- Units with zero references
- Ingredient lines using `piece` where the original was probably empty

---

## 3. Pass 1 — Hygiene

Trim, strip punctuation (`grams.` → `gram`), fix casing per Create §4, spot plural duplicates (`tin`/`tins`, `slice`/`slices` as two records), spelling variants (`grammes`/`grams`), `gr` → `g`.

Pairs found here are merge candidates for Pass 3 — flag them, do not merge yet.

---

## 4. Pass 2 — Abbreviation collisions

If the same abbreviation sits on two units, mapping is non-deterministic and the parser picks arbitrarily. This is the equivalent of an alias collision on foods (Cleanup §5) and must be resolved before Pass 3.

Typical cases: `T` on both teaspoon and tablespoon; `l` on both litre and leaf; `pt` on both pint and packet.

Resolution: the established abbreviation stays on one unit, the other gets an unambiguous one or none. Remove every single-letter abbreviation except `g` and `l`.

---

## 5. Pass 3 — Merging

**Candidate signals:** identical normalised names; singular/plural pairs; the same abbreviation; the spelled-out form and the abbreviation existing as two records (`tbsp` and `tablespoon`).

**Merging is forbidden for:**
- `teaspoon` vs `tablespoon` — a factor of three
- US and UK volumes, while both still exist — they genuinely differ
- `packet` vs `tin` vs `jar` — different containers, different house assumptions
- `pinch` vs `dash` — culinarily distinct

**Procedure** (as Cleanup §6.4): survivor by reference count; set the canonical form per Create §4; move the loser's variants into the **parser configuration** (units have no alias list, so this information is otherwise lost); relink every ingredient line; verify the counts add up; delete the loser; log it.

---

## 6. Pass 4 — Eliminating non-metric units

Goal: **zero non-metric units in the corpus.** Cup, ounce, pound, fluid ounce, pint, quart, stick and gallon disappear entirely.

### 6.1 Procedure per unit
1. Pull **every** referencing ingredient line, with its food and amount
2. Sort by type: liquid, mass, dry volume (Create §3.1)
3. Set aside lines whose food is **not** in the density table (Create §3.4) → review, **do not convert**
4. Convert and round the remaining lines individually (Create §3.5)
5. Write the `Original: …` note on each line (Create §3.6), preserving existing notes with `; `
6. Relink to the metric unit
7. Delete the old unit only once its reference count is **zero**
8. Log it, including the number of lines converted

### 6.2 Hard guards
- **Never convert in bulk.** Every line is read, because the factor depends on the food. A blanket "all cups × 240 ml" destroys every baking recipe in the corpus.
- **Never without a note.** A line with no `Original:` can no longer be checked, so the error becomes unfindable.
- **Never guess.** With no density value, the line stays untouched and goes to review. An open line is repairable; a wrong number is not.
- **Never backwards.** An already-converted line is never converted again. The `Original:` note is also the marker for detecting that.
- **Baking recipes first and individually.** A few grams decide the outcome there; savoury recipes forgive rounding.

### 6.3 When conversion is impossible
If a non-metric unit is still referenced at the end, it is **not deleted** but marked `deprecated`: no new assignments, existing lines stay readable. Delete only when the count reaches zero.

---

## 7. Pass 5 — Completing fields

For every remaining unit:
- `abbreviation` set, unambiguous, correctly cased
- `pluralName` correct; `pluralAbbreviation` = `abbreviation`
- `fraction` matching the class
- `description` with the definition (`1 tbsp = 15 ml`) or house assumption (`tin: assume 400 g`)
- Variants in the parser configuration

This is the best effort-to-value pass: it turns future review items into automatic matches and carries no risk.

---

## 8. Pass 6 — Pruning

| Case | Action |
| --- | --- |
| zero references, metric | keep if part of the core set; otherwise delete |
| zero references, non-metric | delete |
| unit contains a food (`garlic clove`) | relink lines to `clove` + food, then delete |
| unit is a size (`large`) | move the value to the ingredient note, empty the unit, then delete |
| `serving` | relink to the recipe servings field, then delete |

---

## 9. Pass 7 — Verification

Against the Pass 0 baseline:

- **non-metric units: zero** (or fully justified as `deprecated`)
- abbreviation collisions: **zero**
- units missing `abbreviation` or `description`: **zero**
- **total ingredient lines unchanged** — any deviation means loss
- Spot check: recalculate 20 converted lines by hand, at least five from baking recipes
- Every converted line carries `Original:` — a shortfall means Pass 4 was incomplete

The spot check is not optional. It is the only test that catches a systematic conversion error before it reaches a thousand lines.

---

## 10. Checklist

**Before starting**
- [ ] Export taken and restore verified?
- [ ] Reference count available per unit?
- [ ] Worklist of non-metric units compiled?

**Per merge**
- [ ] Not a forbidden pair (§5)?
- [ ] Loser's variants moved into the parser configuration?
- [ ] Reference counts add up after relinking?

**Per conversion**
- [ ] Line read individually rather than processed in bulk?
- [ ] Type determined correctly and density table used?
- [ ] Food missing from the table → line left untouched and sent to review?
- [ ] `Original: …` set, existing note preserved?
- [ ] Rounding within 2 %?
- [ ] Old unit deleted only at count zero?

**At the end**
- [ ] Zero non-metric units?
- [ ] Line count unchanged?
- [ ] 20-line spot check recalculated?
