# Categories: Cleaning Up the Existing Corpus (EN)

> Companion to **Categories: Creating & Assigning**. *Cleanup §x* points to **Food Rules (EN): Cleaning Up the Existing Corpus**.

## Principle

Categories are few and carry the navigation structure. The typical damage is not a typo but a **broken axis**: over time, dish type, meal, cuisine and occasion have grown side by side, every recipe has four categories, and none of them sorts anything.

> Before the first write: export, reference count per category, changelog (Cleanup §1).

---

## 1. Pass order

| # | Pass | Nature |
| - | ---- | ------ |
| 0 | Inventory | read-only |
| 1 | Hygiene | non-destructive |
| 2 | **Restoring the axis** | restructuring |
| 3 | Merging | destructive |
| 4 | Pruning and promoting | destructive |
| 5 | Unloading recipes | non-destructive |
| 6 | Verification | read-only |

---

## 2. Pass 0 — Inventory

- Reference count per category
- Categories with fewer than five recipes
- **Recipes with more than two categories** — this is the axis indicator
- Recipes with no category
- Categories in the plural, with emoji, or with source or brand names

If the average exceeds 1.5 categories per recipe, the axis is very likely broken.

---

## 3. Pass 1 — Hygiene

Trim, fix casing, plural → singular (`Mains` → `Main`), remove emoji and numbering.

As always when renaming: the old spelling is lost, because categories have no aliases. External imports using the old spelling must be updated.

---

## 4. Pass 2 — Restoring the axis

The core of the cleanup.

1. **Choose and document the axis** (Create §1). Recommendation: dish type.
2. Assign each existing category to one axis: dish type, meal, cuisine, diet, occasion, effort, method, ingredient, source, status.
3. Everything **not** on the chosen axis is **moved to another entity** — not deleted:

| Category found | Destination |
| --- | --- |
| `Breakfast`, `Dinner` | tag, *Occasion* facet |
| `Italian`, `Asian` | tag, *Cuisine* facet |
| `Vegetarian`, `Vegan` | tag, *Diet* facet |
| `Quick`, `Under 30 Minutes` | tag, *Effort* facet |
| `Christmas`, `Barbecue` | tag, *Occasion* facet |
| `Air Fryer`, `Slow Cooker` | tag *Method* + tool |
| `Chicken`, `Pumpkin` | nothing — ingredient search covers it |
| `Favourites`, `To Try` | tag or cookbook feature |

**Moving means:** create the tag first, tag every recipe in the category, compare the counts, then delete the category. Never the other way round — the assignments are lost otherwise.

---

## 5. Pass 3 — Merging

Candidates: singular/plural pairs, synonyms (`Pudding`/`Dessert`, `Starter`/`Appetiser`), broader and narrower terms nobody distinguishes (`Cake` and `Gateau`).

Procedure as Cleanup §6.4: survivor by reference count, relink recipes, verify the counts add up, delete, log.

**Merging is forbidden** for categories that genuinely differ on the axis — `Side` and `Salad` overlap but are not the same thing. Overlap is not a reason to merge; only synonymy is.

---

## 6. Pass 4 — Pruning and promoting

| Case | Action |
| --- | --- |
| under 5 recipes after a year | convert to a tag (procedure in §4) |
| zero recipes | delete |
| over 40 % of all recipes | check for a sensible split — a category holding almost everything sorts nothing |
| a tag with over 15 recipes that sits on the axis | **promote to a category** — the reverse direction is explicitly intended |

---

## 7. Pass 5 — Unloading recipes

Review every recipe with more than two categories. After Pass 2 the list should be nearly empty; what remains are genuine borderline cases (a soup that is a main).

Rule: keep the **dominant** category, add the second only if the dish genuinely is both. Remove the third and beyond.

---

## 8. Pass 6 — Verification

- Every category sits on **one** axis
- Average categories per recipe: **1.0–1.3**
- Categories with fewer than five recipes: **zero**
- Recipes with no category: known and justified
- **No recipe assignment lost** — every category moved in Pass 2 must have left a tag with the same count

The last point is the integrity check: deleting `Vegetarian` as a category without first tagging 60 recipes loses 60 assignments irretrievably.

---

## 9. Checklist

- [ ] Axis chosen and documented?
- [ ] Every category assigned to an axis?
- [ ] Off-axis categories **moved** rather than deleted — tag first, counts compared, then delete?
- [ ] Merges only for synonymy, never for overlap?
- [ ] Categories under five recipes converted to tags?
- [ ] Tags over 15 recipes checked for promotion?
- [ ] Recipes with more than two categories cleaned up?
- [ ] No assignment lost?
