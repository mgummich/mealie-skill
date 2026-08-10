# Tools: Creating & Assigning During Recipe Creation (EN)

## Principle

A tool is equipment that **gates** the recipe: without it, the recipe cannot be made, or the result is a different dish.

Fields: `name`, `slug`, `onHand`. **No aliases.** Naming discipline therefore matters more here than in any other entity — spelled differently a second time is a second tool, and nobody notices.

> **Realistically zero to four tools per recipe.** Zero is a perfectly normal result. A recipe listing eight tools is listing kitchen fittings.

---

## 1. The gating test

One question: **does a functioning average kitchen already have it?**

**Yes → not a tool.**
Knife, chopping board, saucepan, frying pan, bowl, sieve, wooden spoon, baking tray, whisk, grater, peeler, oven, hob, fridge.

**No → tool.**
Air fryer, ice cream maker, sous-vide circulator, smoker, food processor, stand mixer, stick blender, mincer, waffle iron, steamer, pestle and mortar, pasta machine, sugar thermometer, springform tin, loaf tin, tagine, wok, cast-iron casserole, muffin tin, scales with 1 g resolution.

Decide borderline cases by asking whether its absence **prevents** the dish or merely **inconveniences** it. A stick blender inconveniences the soup; it does not prevent it — unless the recipe lives on the texture. When in doubt: not a tool.

---

## 2. Assigning when creating a recipe

| Tier | Test | Action |
| --- | --- | --- |
| 0 | Tool exists exactly | assign |
| 1 | Tool exists under the generic term (`Thermomix` → `Food Processor`) | assign **the existing one** |
| 2 | Tool exists in another size (`Springform Tin 23 cm` vs `20 cm`) | §3 — separate only when the size determines the outcome |
| 3 | Fails the gating test | **do not assign, do not create** |
| 4 | New and gating | create (§4) |

**Look at the list before creating anything.** With no aliases, nothing catches a typo or a differing spelling.

---

## 3. Sizes

Only in the name when the size determines the **outcome**:

- `Springform Tin 23 cm` — yes, a 20 cm tin overflows with the same batter
- `Loaf Tin 900 g` — yes
- `Saucepan 3 l` — no, and generic `saucepan` fails §1 anyway
- `Large Bowl` — no

Format: equipment + number + unit, no brackets, **metric**. Convert inch sizes from source recipes (1 inch = 2.54 cm) and round to standard tin sizes: 8 inch → 20 cm, 9 inch → 23 cm, 10 inch → 26 cm.

---

## 4. Creating

- Generic English term, singular, title case, no plural
- **No brands:** `Thermomix` → `Food Processor`, `KitchenAid` → `Stand Mixer`, `Crockpot` → `Slow Cooker`, `Instant Pot` → `Multi Cooker`
- Exception: where the brand has genuinely become the generic term and no common alternative exists, it is the name. `Slow Cooker` is established; `Thermomix` is not.
- No adjectives that do not gate: `Springform Tin 23 cm`, not `Large Springform Tin (any brand)`
- **Set `onHand` deliberately.** It is the household inventory, not a wishlist. Only if it is accurate does "what can I actually cook tonight?" become answerable.

---

## 5. Relationship to tags

`air fryer` is **both**: the appliance is a tool, the cooking method is a tag in the *Method* facet. Having both is correct and not a duplicate — the tool answers "can I make this?", the tag answers "show me all air fryer recipes".

The condition: both must be spelled **identically**, or it looks like a mistake.

Conversely, `oven` is a tag but not a tool — every kitchen has one, so it does not gate.

---

## 6. Checklist

- [ ] Does it pass the gating test (§1)?
- [ ] Was the list checked first — there are no aliases to catch a typo?
- [ ] Brand removed, generic term used?
- [ ] Size in the name only where it determines the outcome?
- [ ] Size metric and rounded to a standard tin size?
- [ ] Singular, title case, no plural?
- [ ] `onHand` set deliberately?
- [ ] Does the recipe stay at four tools or fewer?
