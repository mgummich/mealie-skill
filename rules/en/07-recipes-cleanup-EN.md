# Recipes: Cleaning Up the Existing Corpus (EN)

> Companion to **Recipes: Creating & Importing**. *Create §x* points there, *Cleanup §x* to **Food Rules (EN): Cleaning Up the Existing Corpus**.

## Principle

Recipes are the only entity carrying **content** rather than just structure. A deleted tag is annoying; a deleted recipe is gone — along with its rating, its notes, and five years of experience.

> **Default action: add, don't replace.** Before the first write: full export including images, changelog, dry-run (Cleanup §1).

Unlike the master data, a **corpus-wide sweep is not worth it here**. The set is too large and the work too manual. Prioritise by impact instead:

1. Recipes actually cooked (`lastMade` set, high `rating`)
2. Recipes with broken ingredient lines — they break shopping lists and scaling
3. Everything else, occasionally

---

## 1. Pass order

| # | Pass | Nature | Risk |
| - | ---- | ------ | ---- |
| 0 | Inventory | read-only | none |
| 1 | Duplicates | **destructive** | high |
| 2 | **Repairing ingredient lines** | structural | medium |
| 3 | Converting units to metric | changes amounts | **high** |
| 4 | Steps and sections | editorial | low |
| 5 | Metadata | non-destructive | low |
| 6 | Times, servings, source | non-destructive | low |
| 7 | Verification | read-only | none |

Pass 2 before 3, because an amount can only be converted once the food and unit are recognised at all.

---

## 2. Pass 0 — Inventory

- Total recipes; with `lastMade`; with `rating`
- **Share of ingredient lines with a linked `food`** — the single most important metric in this document
- Ingredient lines with no `unit` but a number in the `note` field
- Recipes using non-metric units (worklist from *Units: Cleaning Up* §2)
- Recipes with exactly one method step, or more than 15
- Recipes with no category, no steps, no ingredients
- Recipes with more than eight tags, more than two categories, more than four tools
- Recipes with neither `orgURL` nor a source note
- Notes with free-form titles, no title, or more than five notes on one recipe
- Name duplicates and near-duplicates

---

## 3. Pass 1 — Duplicates

**Signals:** identical or near-identical `name`; the same `orgURL`; the same ingredient count with overlapping foods; the same image.

**Do not merge** the same dish from different cuisines or with a clearly different method (Create §1.1). Two lentil soups may coexist — but sharpen the titles so the distinction is visible.

**Merge procedure:**
1. The survivor is the recipe with **more content** — more structured ingredient lines, more notes, `lastMade` and `rating` set. Not the older one, not the prettier one.
2. **Take everything unique** from the loser: notes, comment content, the better image, a differing method as a `Variation` note (Create §8)
3. Rating: keep the one from the more frequently cooked recipe; never average them
4. Delete the loser, log it

Step 2 is why this pass stays manual. What sits in the loser is usually exactly the experience worth keeping.

---

## 4. Pass 2 — Repairing ingredient lines

The highest-yield pass. Typical damage from old imports:

| Damage | Detection | Repair |
| --- | --- | --- |
| Line is raw text | no `food` linked | re-parse via the parse rules, link `food` and `unit` |
| Preparation inside the food | `food` reads `onions, finely chopped` | preparation to `note`, fix the food (Parse §4.2) |
| Amount in the note field | `note` contains `about 200 g` | move into `quantity` and `unit` |
| Several foods on one line | `salt and pepper` | split into two lines (Create §5.2) |
| Invented amount | `1 piece salt` | `quantity: 0`, clear the unit, `note: to taste` |
| Homemade component as a food | `food` reads `pizza dough` | convert to `referencedRecipe` (Create §5.6) |
| Unit contains a food | `unit` reads `garlic clove` | `unit: clove`, `food: garlic` |

**Hard rule:** `originalText` stays **untouched**. In every repair it is the only evidence of what was originally there. Overwriting it makes the next error unfindable.

Where `originalText` is missing — common in older corpora — write the current `display` value into it before repairing. Then repair.

---

## 5. Pass 3 — Converting units to metric

Runs against the worklist from *Units: Cleaning Up* §6 and follows its guards exactly:

- **never in bulk** — the conversion factor depends on the food
- **never without a note** — `Original: …` on every changed line (Units §3.6)
- **never guess** — with no density value the line stays untouched and goes to review
- **never backwards** — a line carrying `Original:` is never converted again
- **baking recipes first and individually**

Plus one recipe-specific addition: **take the temperatures in the steps with you.** A recipe with metric ingredients and `350 °F` in the text is half-converted, which is arguably worse than not converted at all. Format: `175 °C (Original: 350 °F)`.

Same for inch tin sizes in steps and tools: 8 inch → 20 cm, 9 inch → 23 cm, 10 inch → 26 cm.

---

## 6. Pass 4 — Steps, sections and notes

Only for recipes actually cooked. Check:

- **A single step** → split into blocks of action (Create §6.1)
- **More than 15 steps** → usually sentence-by-sentence fragments; combine
- **Ingredients with no `ingredientReferences`** → either link them, or discover that the ingredient is missing from the method. This is the most reliable way to find broken imports.
- **Section headings** in ingredients (§5.7) and steps brought into line with each other
- **Amounts in the text** that no longer match the ingredient line → align or remove (Create §6.3)

Correct the language only where it is unclear. Rewriting a recipe because the style grates is work without return.

### 6.1 Sorting out the notes
Notes are where everything lands over the years that nobody found another home for. Check each note against the boundary in *Create §8.1*:

| Note found | Destination |
| --- | --- |
| describes an action (`preheat the oven first`) | a step in `recipeInstructions` |
| concerns a single ingredient (`use the butter at room temperature`) | the `note` on that ingredient line |
| contains `Original:` or a conversion | the `note` on the affected ingredient line |
| repeats the `description` | delete |
| states a time or servings (`takes about 40 minutes`) | the relevant field, then delete |
| is a complete alternative recipe | create its own recipe, cut the note to a pointer |
| carries a free-form title (`Info`, `Note`, `Important!`) | map onto the vocabulary in *Create §8.2* |
| is one lump of text with no title | split by title |
| claims freedom from an allergen | delete (Tags §5) |

**Two notes with the same title** are combined into one. **More than five notes** nearly always means several rows of the table apply.

Finally, review the **comments**: durable knowledge sitting there — "baked it 10 minutes longer the second time" — moves into an `Experience` note. The comments stay, but the knowledge is then safe.

---

## 7. Pass 5 — Metadata

Run this after the master-data cleanups, not before — otherwise you tag with tags that are then merged away.

- Unload recipes with more than two categories (Categories: Cleaning Up §7)
- Trim recipes over eight tags; keep the *Cuisine*, *Diet* and *Occasion* facets first
- Check tools against the gating test; strip kitchen fittings
- Fill in recipes with no category
- **Remove estimated nutrition** — only source figures stay

---

## 8. Pass 6 — Times, servings, source

- Unify the time format (Create §4.2) and resolve ranges
- Move waiting time out of `prepTime` into `totalTime` — otherwise every effort-based search is wrong
- Check `recipeServings`; add `recipeYieldQuantity` and `recipeYield` for baking and preserves
- Add `orgURL` where known; otherwise a `Source` note
- Check `settings.public`: set to `false` for other people's text or images

---

## 9. Pass 7 — Verification

Against the Pass 0 baseline:

- **Share of ingredient lines with a linked `food`** — must rise substantially; target above 95 %
- Non-metric units in ingredients **and** step text: **zero**
- Every converted line carries `Original:`
- Recipes with no ingredients, no steps or no category: **zero**
- Note titles outside the vocabulary: **zero**; no recipe over five notes
- **Recipe count unchanged**, unless documented merges explain the difference
- **Ingredient line count unchanged**, unless documented splits explain the increase
- Spot check: read five reworked recipes in full and cook them through in your head

The last check finds what no metric finds: steps that, after repair, refer to ingredients that no longer exist.

---

## 10. Checklist

**Before starting**
- [ ] Export including images taken and restore verified?
- [ ] Prioritised by impact rather than sweeping the corpus?
- [ ] Master-data cleanups (foods, units, tags) run first?

**Per merge**
- [ ] Genuinely the same recipe and not a legitimate variation?
- [ ] Survivor chosen by content, not by age?
- [ ] Notes, comments, image and rating taken from the loser?

**Per ingredient repair**
- [ ] `originalText` untouched — or filled from `display` beforehand?
- [ ] `food` and `unit` linked, preparation in `note`?
- [ ] Multi-food lines split, invented amounts removed?
- [ ] Homemade components moved to `referencedRecipe`?

**Per conversion**
- [ ] Line handled individually, density table used?
- [ ] `Original: …` set?
- [ ] Temperatures and tin sizes in the steps taken along?

**At the end**
- [ ] Recipe and line counts explained?
- [ ] Over 95 % of lines with a linked `food`?
- [ ] Five recipes proofread in full?
