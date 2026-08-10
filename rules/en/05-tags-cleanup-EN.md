# Tags: Cleaning Up the Existing Corpus (EN)

> Companion to **Tags: Creating & Assigning**. *Cleanup §x* points to **Food Rules (EN): Cleaning Up the Existing Corpus**.

## Principle

Tags run wild faster than any other entity, because they can be created freely and nobody sees the list while creating one. The typical corpus after two years: three hundred entries, half of them used once, a dozen synonym clusters, and a few tags on nearly every recipe.

> Before the first write: export, reference count per tag, changelog (Cleanup §1).

---

## 1. Pass order

| # | Pass | Nature |
| - | ---- | ------ |
| 0 | Inventory | read-only |
| 1 | Hygiene | non-destructive |
| 2 | **Faceting** | restructuring |
| 3 | Merging synonyms | destructive |
| 4 | Correcting the entity | restructuring |
| 5 | Pruning | destructive |
| 6 | Unloading recipes | non-destructive |
| 7 | Verification | read-only |

---

## 2. Pass 0 — Inventory

- Reference count per tag, sorted descending
- Tags with **one** reference — usually the largest group
- Tags on **over 90 %** of recipes
- Tags that fit no facet
- **Recipes with more than eight tags**
- Tags containing numbers, emoji, `#`, or conjunctions

---

## 3. Pass 1 — Hygiene

Trim, fix casing per Create §6, plural → singular, remove emoji and `#`, unify hyphenation (`gluten free`/`gluten-free`).

Note the distinction: pure spelling variants (`Vegetarian`/`vegetarian`) are unified here — genuine synonyms (`veggie`/`meat-free`) belong to Pass 3.

---

## 4. Pass 2 — Faceting

Assign every tag to a facet (Create §1). The result is a table that is then maintained.

Anything that fits **no** facet is a candidate for Pass 4 or 5 — not for a new facet. Create a new facet only if at least five existing tags fall into it.

Faceting is a precondition for Pass 3: synonyms almost always sit within one facet, and checking facet by facet is orders of magnitude faster than checking pairwise.

---

## 5. Pass 3 — Merging synonyms

Work facet by facet. Typical clusters:

- `vegetarian` / `veggie` / `meat-free` / `no meat`
- `quick` / `speedy` / `in 20 minutes` / `weeknight`
- `oven` / `baked` / `oven-baked`
- `meal prep` / `batch cooking` / `mealprep`
- `kid-friendly` / `kids` / `family-friendly`

The **survivor** is the tag that complies with the naming rule — **not** automatically the one with the highest count. Unlike foods, relinking is cheap here, and the naming decides future consistency.

Procedure: pick the survivor, tag all of the loser's recipes, verify the counts, delete the loser, log it.

---

## 6. Pass 4 — Correcting the entity

| Tag found | Destination |
| --- | --- |
| `main`, `dessert` | category — delete the tag if the category is already assigned |
| `springform tin 23 cm`, `ice cream maker` | tool — move, then delete |
| `chicken`, `with pumpkin` | delete outright; ingredient search covers it |
| `30 minutes`, `serves 4` | transfer to the Mealie recipe field, then delete |
| `nut-free`, `no gluten` | **delete** — negative assurance (Create §5); replace with the positive `gluten-free` if appropriate |
| `test`, `TODO`, `new` | delete |

As with categories: **move first, delete second.** Creating a tool and linking the recipes costs ten minutes; the lost assignments cost an afternoon.

---

## 7. Pass 5 — Pruning

| Case | Action |
| --- | --- |
| one reference | merge if a cluster fits; otherwise delete |
| zero references | delete |
| over 90 % of recipes | delete — it filters nothing |
| under 5 references and no facet | delete |

No sentimentality when deleting: a tag that has carried one recipe for two years does not find that recipe better than full-text search does.

---

## 8. Pass 6 — Unloading recipes

Review recipes with more than eight tags. After Passes 3–5 this list usually shrinks on its own.

Priority when cutting: keep the *Cuisine*, *Diet* and *Occasion* facets — they are filtered most. *Source* and *Audience* go first.

---

## 9. Pass 7 — Verification

- Every tag has **exactly one** facet
- Tags with one reference: **zero** or justified
- Tags over 90 %: **zero**
- Recipes with more than eight tags: **zero**
- Total tag assignments may fall — but every cluster moved in Pass 4 must have its assignments findable in the destination entity
- Spot check: look at five recipes per facet — does the facet actually filter usefully?

---

## 10. Checklist

- [ ] Facet table complete, every tag assigned?
- [ ] Synonyms checked facet by facet rather than pairwise?
- [ ] Survivor chosen by naming rule, not by count?
- [ ] Wrong entities **moved** rather than deleted?
- [ ] Negative tags (`no X`) removed?
- [ ] Single references and 90 % tags cleaned up?
- [ ] No recipe over eight tags?
- [ ] Assignments of moved clusters traceable in the destination entity?
