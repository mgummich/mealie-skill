# Tags: Creating & Assigning During Recipe Creation (EN)

## Principle

The tag is the **sticker** on the recipe. It covers everything that is not dish type, and exists for **filtering**, not browsing.

Open set, target size **40–120**. Open does not mean free: without a controlled vocabulary you get `vegetarian`, `Vegetarian`, `veggie`, `meat-free` and `no meat` side by side within months, and none of them filters reliably.

> **Ceiling: at most eight tags per recipe.** Beyond that you are describing rather than filtering.

---

## 1. The facet rule

**Every tag belongs to exactly one facet.** The facet is not part of the name; it lives in a maintained mapping table. A tag that fits no facet is **not created** — it almost always belongs to a different entity (§4).

| Facet | Examples | Note |
| --- | --- | --- |
| Cuisine | italian, thai, levantine, sichuan | adjective, lowercase |
| Diet | vegetarian, vegan, gluten-free, dairy-free, low-carb | see §5 |
| Occasion | christmas, easter, birthday, barbecue, breakfast, dinner | the meal lands here |
| Effort | quick, involved, minimal washing-up, weeknight | no minute counts |
| Method | oven, one-pot, slow cooker, air fryer, sous-vide, grill | appliance as method |
| Season | spring, summer, autumn, winter, asparagus season | |
| Keeping | freezable, meal prep, uses leftovers, storecupboard | |
| Audience | kid-friendly, dinner-party, crowd-pleaser | |
| Source | nan's recipes, bbc good food, own recipe | only if you actually filter by it |

---

## 2. Assigning when creating a recipe

| Tier | Test | Action |
| --- | --- | --- |
| 0 | Tag exists exactly | assign |
| 1 | Tag exists as a spelling or wording variant (`veggie` → `vegetarian`) | assign **the existing one** |
| 2 | Concept fits a facet but does not exist yet | check §3, then create |
| 3 | Concept fits no facet | **do not create** — check the entity (§4) |

Before creating anything, scan the facet the concept would fall into. Most duplicates arise because someone created `quick` without having seen `weeknight`.

---

## 3. The creation test

1. Maps to exactly **one** facet
2. **One** concept — no conjunctions (`quick and easy` is two)
3. You will actually **filter** by it, not merely describe with it
4. It will apply to **more than one** recipe

---

## 4. Never a tag

| Candidate | Why not | Belongs to |
| --- | --- | --- |
| `30 minutes`, `serves 4`, `5 stars` | Mealie has fields — otherwise two sources of truth | recipe field |
| `chicken`, `with pumpkin` | that is what ingredient search is for | ingredient |
| `main`, `dessert` | duplicates the category | category |
| `springform tin 23 cm` | gating equipment | tool |
| `quick and easy` | two concepts | two tags |
| `tasty`, `good` | filters nothing; every recipe qualifies | — |
| `test`, `new`, `TODO` | working status, not a recipe property | — |

---

## 5. Allergens — explicit warning

`gluten-free`, `dairy-free` and `nut-free` are **search aids, not assurances**. They say nothing about traces, cross-contamination, or the specific brand used.

Do not create negative tags of the form `no X` at all: they read as a guarantee while being only as reliable as the care taken tagging one recipe. Anyone managing an allergy reads the ingredient list, not the tag.

---

## 6. Naming

- Lowercase, **singular**, one concept per tag
- Adjective form over noun form: `vegetarian`, not `vegetarian cooking` and not `vegetarianism`
- No emoji, no `#`
- Hyphenate consistently: pick `gluten-free` or `gluten free` once, never both

---

## 7. Checklist

- [ ] Maps to exactly one facet (§1)?
- [ ] Facet scanned for variants before creating?
- [ ] One concept, no conjunction?
- [ ] Not duplicating a Mealie field, a category, an ingredient or a tool?
- [ ] No `no X` phrasing implying an allergen guarantee (§5)?
- [ ] Casing and singular correct?
- [ ] Does the recipe stay under eight tags?
