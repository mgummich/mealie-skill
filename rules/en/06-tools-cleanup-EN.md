# Tools: Cleaning Up the Existing Corpus (EN)

> Companion to **Tools: Creating & Assigning**. *Cleanup §x* points to **Food Rules (EN): Cleaning Up the Existing Corpus**.

## Principle

Tools have **no aliases**. Every differing spelling is therefore its own record, and the corpus doubles more quietly than in any other entity: `Springform Tin`, `Springform 23cm`, `Springform Tin 23 cm` and `Cake Tin (springform)` sit side by side, and nobody notices, because each hangs off only three recipes.

The second typical damage: the list is full of **kitchen fittings** — knives, bowls, saucepans — and therefore no longer answers "what can I cook tonight?"

> Before the first write: export, reference count per tool, changelog (Cleanup §1).

---

## 1. Pass order

| # | Pass | Nature |
| - | ---- | ------ |
| 0 | Inventory | read-only |
| 1 | Hygiene | non-destructive |
| 2 | Merging spelling variants | destructive |
| 3 | **Applying the gating test** | destructive |
| 4 | Brands and sizes | destructive |
| 5 | Checking `onHand` | non-destructive |
| 6 | Unloading recipes | non-destructive |
| 7 | Verification | read-only |

---

## 2. Pass 0 — Inventory

- Reference count per tool
- Records differing only in spelling, spacing or size
- Records containing brand names
- Records failing the gating test — usually the largest group
- **Recipes with more than four tools**
- `onHand` distribution: if everything is `false` or everything is `true`, the flag was never maintained

---

## 3. Pass 1 — Hygiene

Trim, fix casing, plural → singular (`Springform Tins` → `Springform Tin`), unify spacing before units (`23cm` → `23 cm`), remove bracketed asides (`Cake Tin (springform)` → `Springform Tin`).

---

## 4. Pass 2 — Merging spelling variants

With no aliases, this is the highest-yield pass. Candidates:

- Spelling variants: `Airfryer` / `Air Fryer` / `Air-Fryer`
- With and without size: `Springform Tin` / `Springform Tin 23 cm`
- Generic and brand: `Food Processor` / `Thermomix` / `KitchenAid`
- Regional variants: `Stick Blender` / `Immersion Blender`; `Slow Cooker` / `Crockpot`

The **survivor** is the record complying with the naming rule (Create §4) — generic English term, singular, no brand. Reference count decides only on a tie, because relinking is cheap here.

Procedure: pick the survivor, relink recipes, verify the counts add up, delete the loser, log it.

---

## 5. Pass 3 — Applying the gating test

Check every tool against Create §1: **does a functioning average kitchen already have it?**

Where the answer is yes, the tool is **stripped from all recipes** and then deleted. Typical candidates: knife, chopping board, saucepan, frying pan, bowl, sieve, wooden spoon, baking tray, whisk, grater, oven, hob.

This feels like loss and is not: these records carry zero information, because they apply to every recipe. Exactly like a tag on 90 % of recipes, they filter nothing.

Decide **borderline cases** individually: does its absence prevent the dish or merely inconvenience it? When in doubt, remove — a missing tool is easier to add later than an overfull register is to empty.

---

## 6. Pass 4 — Brands and sizes

**Brands** move to the generic term (Create §4). The exception applies only where the brand has genuinely become the generic term with no common alternative.

**Sizes:** where a size sits in the name without determining the outcome, remove it and merge with the generic record. Where it does determine the outcome, it must be **metric** and rounded to a standard tin size — convert inch sizes from source recipes: 8 inch → 20 cm, 9 inch → 23 cm, 10 inch → 26 cm.

---

## 7. Pass 5 — Checking `onHand`

`onHand` is the household inventory. After a cleanup the list is short enough to walk through completely — that takes minutes and makes "what can I cook tonight?" reliably answerable for the first time.

If the whole list sits at one value, the flag was never maintained and the feature was never actually running.

---

## 8. Pass 6 — Unloading recipes

Review recipes with more than four tools. After Pass 3 the list should be largely empty; what remains are recipes that genuinely need special equipment — or recipes where someone copied the method steps into the tool list.

Consumables (`baking paper`, `cling film`, `cocktail sticks`) are not tools and belong in the method steps.

---

## 9. Pass 7 — Verification

- No two records naming the same equipment
- No brand names except the justified exceptions
- No record failing the gating test
- All sizes metric
- Recipes with more than four tools: **zero** or justified
- Average tools per recipe: **under 1.5**
- `onHand` deliberately set on every record

---

## 10. Checklist

- [ ] Spelling variants merged — there are no aliases to catch them?
- [ ] Survivor chosen by naming rule, not by count?
- [ ] Gating test applied to **every** record?
- [ ] Kitchen fittings stripped from all recipes before deletion?
- [ ] Brands moved to generic terms?
- [ ] Sizes kept only where outcome-relevant, and stated metrically?
- [ ] Consumables moved to the method steps?
- [ ] `onHand` walked through completely?
