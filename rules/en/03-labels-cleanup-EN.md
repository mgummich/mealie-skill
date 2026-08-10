# Labels: Cleaning Up the Existing Corpus (EN)

> Companion to **Labels: Creating & Assigning**. *Cleanup §x* points to **Food Rules (EN): Cleaning Up the Existing Corpus**.

## Principle

Labels are few, but each hangs off many foods and therefore off every shopping list. The typical damage is not a bad name but a **broken axis**: over time, product groups, diets and uses have grown side by side, and the shopping list no longer sorts anything.

> Before the first write: export, food count per label, changelog (Cleanup §1).

---

## 1. Pass order

| # | Pass | Nature |
| - | ---- | ------ |
| 0 | Inventory | read-only |
| 1 | **Restoring the axis** | restructuring |
| 2 | Merging | destructive |
| 3 | Filling in unlabelled foods | non-destructive |
| 4 | Unifying colours | non-destructive |
| 5 | Ordering by shop route | non-destructive |
| 6 | Verification | read-only |

---

## 2. Pass 0 — Inventory

- Food count per label, descending
- **Foods with no label** — the most important number; they land unsorted at the end of the list
- Labels with fewer than ten foods
- Labels on the default `#959595`, or with no colour set
- Hues used twice
- Labels that do not name a product group (§3)
- Size of `Other` — over 5 % of the corpus means it is being used as a dumping ground

---

## 3. Pass 1 — Restoring the axis

Check each label: does it name a **zone in the shop**? If not, it belongs to another entity — and is **moved, not deleted**:

| Label found | Destination |
| --- | --- |
| `Vegetarian`, `Vegan`, `Gluten-free` | tag on the recipe, *Diet* facet |
| `Main`, `Dessert` | category on the recipe |
| `Quick`, `Storecupboard` | tag, *Effort* or *Keeping* facet |
| `Christmas`, `Barbecue` | tag, *Occasion* facet |
| `Asian`, `Italian` | tag, *Cuisine* facet — **not** a label for "the world food aisle" |
| `Favourite ingredients`, `Test` | delete outright |

**Moving means:** create the destination first, link the affected recipes or foods there, compare counts, then delete the label. Give the label's foods a correct product-group label beforehand — otherwise they end up with none.

`Asian` is the most tempting case: some shops really do have a world food aisle. Even so, soy sauce is a condiment and rice is a dry good — origin is a recipe property, not a product-group location (Food Rules §9.1).

---

## 4. Pass 2 — Merging

**Candidates:** singular/plural pairs (`Spice`/`Spices`), synonyms (`Dairy`/`Milk Products`), broader and narrower terms nobody separates (`Nuts` and `Seeds` as two labels), translation duplicates.

**Merging is forbidden** for labels that genuinely sit apart in the shop. `Cheese` and `Dairy` overlap conceptually but are two trips — which is exactly why the food rules separate them.

**Procedure:** the survivor is the label with the most foods; set the canonical name per *Create §3*; **relink all of the loser's foods**; verify the counts add up; delete the loser; log it.

The count check matters especially here: deleting a label silently clears `labelId` on its foods, and that only surfaces on the next shopping trip.

---

## 5. Pass 3 — Unlabelled foods

Work the Pass 0 list in descending order of how often the food is used across recipes. A food appearing in 30 recipes is worth an hour; one from a single recipe can wait.

Assign per Food Rules §9.1 and §9.2. Anything genuinely unclassifiable gets `Other` — but `Other` is a **worklist, not a resting place**: if it grows past 5 % of the corpus, either a label is missing or assignment is being made too easy.

---

## 6. Pass 4 — Colours

Enforce the zone palette from *Create §4.2*:

- Every label on `#959595` gets its zone colour
- Resolve hues used twice
- Check that each zone reads as a block and that neighbouring zones differ clearly

This pass is risk-free and takes twenty minutes — it changes only `color` and not a single food.

---

## 7. Pass 5 — Ordering

Align the shopping list's label order with the actual route through the shop (*Create §5*). Best done with a real shopping list in hand: wherever you have to double back, the order is wrong.

With several shops, sort by the one you mostly use. Two competing orders are worse than one imperfect one.

---

## 8. Pass 6 — Verification

- **Foods with no label: zero**
- Labels that do not name a product group: **zero**
- Labels on the default colour: **zero**
- Duplicate hues: **zero**
- `Other` under 5 % of the food corpus
- **No label assignment lost** — every label moved in Pass 1 must have its foods findable on another label
- Field test: generate a real shopping list and walk it once

The field test is the only check that shows whether the order works. No metric replaces it.

---

## 9. Checklist

- [ ] Every label checked as a product group, and off-axis ones **moved** rather than deleted?
- [ ] Foods reassigned before deleting their label?
- [ ] Merges only for synonymy, never for conceptual overlap?
- [ ] Unlabelled foods worked in order of use?
- [ ] Zone palette fully enforced, no default colour left?
- [ ] Order checked against the real shop route?
- [ ] `Other` under 5 %?
