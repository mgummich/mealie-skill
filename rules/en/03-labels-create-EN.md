# Labels: Creating & Assigning (EN)

> Companion to **Food Rules (EN): Parsing & Creation**. That document's §9 says *which* label a food gets. This one says what the label itself looks like.

## Principle

A label in Mealie is its own entity (`MultiPurposeLabel`) with exactly two fields: `name` and `color`. It hangs off the **food**, not the recipe, and its one real purpose is the **shopping list**: it groups and orders so you walk the shop once instead of three times.

> **Prime directive:** a label answers *"where is this in the shop?"* — not *"what is this culinarily?"* and certainly not *"what kind of dish is this?"*. Those last two are answered by categories and tags, which hang off recipes.

Closed set, **29 entries**. Growth is a defect signal.

---

## 1. Boundaries

| Entity | Attaches to | Answers |
| --- | --- | --- |
| **Label** | food | Where in the shop is it? |
| Category | recipe | What kind of dish is this? |
| Tag | recipe | What property does the recipe have? |

A label like `Vegetarian` or `Quick` is a category error: both are properties of recipes, not aisles in a supermarket. A label `Christmas` likewise.

---

## 2. The creation test

Create a label only when **all four** hold:

1. It matches a **distinct zone in the shop or store cupboard** — somewhere you make a separate trip to.
2. At least **ten foods** fall into it. Fewer means it belongs inside an existing label.
3. It overlaps with no existing label. On overlap, the existing one wins.
4. It is a place, not a property (§1).

If one fails, the food gets the nearest existing label — or `Other`, which is explicitly a worklist.

---

## 3. Naming

- Noun, title case, as in the fixed list (Food Rules §9.3)
- Plural is **correct** here, because labels name product groups: `Legumes`, `Nuts & Seeds`
- Pairs joined with `&` where the zone covers two things: `Oil, Vinegar & Fat`
- No emoji in `name` — they break sorting and search

---

## 4. Colours

### 4.1 The colour is functional
`color` is not decoration. On the shopping list you see from the block of colour that a new area starts, before you read the text. Random colours make the list less readable than no colours at all.

**Rule: the colour encodes the zone, not the individual label.** Labels in one zone share a hue at different lightnesses. `Cheese` and `Dairy` looking similar is not a bug — they sit next to each other in the shop.

### 4.2 Zone palette

| # | Label | Zone | `color` |
| -- | --- | --- | --- |
| 1 | Vegetables | Fresh (green) | `#43A047` |
| 2 | Fruit | Fresh | `#7CB342` |
| 3 | Fresh Herbs | Fresh | `#1B5E20` |
| 4 | Potatoes & Tubers | Fresh | `#9CCC65` |
| 5 | Meat | Meat & Fish (red) | `#B71C1C` |
| 6 | Poultry | Meat & Fish | `#E53935` |
| 7 | Fish & Seafood | Meat & Fish | `#FF7043` |
| 8 | Cured & Deli Meats | Meat & Fish | `#AD1457` |
| 9 | Dairy | Chilled (blue) | `#1E88E5` |
| 10 | Cheese | Chilled | `#64B5F6` |
| 11 | Eggs | Chilled | `#0D47A1` |
| 12 | Bread & Pastry | Bread & Breakfast (brown) | `#8D6E63` |
| 13 | Baking Supplies | Bread & Breakfast | `#BCAAA4` |
| 14 | Breakfast Cereals | Bread & Breakfast | `#5D4037` |
| 15 | Pasta, Rice & Noodles | Dry goods (yellow/olive) | `#F9A825` |
| 16 | Legumes | Dry goods | `#9E9D24` |
| 17 | Nuts & Seeds | Dry goods | `#827717` |
| 18 | Herbs & Spices | Seasoning (orange) | `#EF6C00` |
| 19 | Oil, Vinegar & Fat | Seasoning | `#FFB300` |
| 20 | Sauces & Condiments | Seasoning | `#F4511E` |
| 21 | Stock & Flavourings | Seasoning | `#BF360C` |
| 22 | Snacks | Snacks & Sweets (pink) | `#EC407A` |
| 23 | Sweets & Spreads | Snacks & Sweets | `#C2185B` |
| 24 | Drinks | Drinks (teal) | `#00ACC1` |
| 25 | Wine | Drinks (alcohol, purple) | `#8E24AA` |
| 26 | Beer | Drinks | `#26C6DA` |
| 27 | Spirits & Liqueurs | Drinks (alcohol) | `#6A1B9A` |
| 28 | Coffee & Tea | Drinks | `#00838F` |
| 29 | Other | Remainder (grey) | `#757575` |

### 4.3 Colour rules
- **Six-digit hex with a leading `#` only.** Mealie's default is `#959595`; a label left on it is unmaintained.
- No hue used twice — not even across zones.
- Dark enough or light enough that the text stays readable; avoid low-contrast mid-greys.
- **Never rely on colour alone.** Red-green deficiency affects roughly one man in twelve, so the name always sits beside it and the ordering (§5) carries the real structure.

---

## 5. Shopping list order

Label ordering is set per shopping list and is the actual payoff of the whole system. **It follows the route through the shop, not the alphabet.**

A workable order for a typical supermarket:

`Vegetables` → `Fruit` → `Fresh Herbs` → `Potatoes & Tubers` → `Bread & Pastry` → `Dairy` → `Cheese` → `Eggs` → `Meat` → `Poultry` → `Cured & Deli Meats` → `Fish & Seafood` → `Pasta, Rice & Noodles` → `Legumes` → `Baking Supplies` → `Breakfast Cereals` → `Nuts & Seeds` → `Herbs & Spices` → `Oil, Vinegar & Fat` → `Sauces & Condiments` → `Stock & Flavourings` → `Snacks` → `Sweets & Spreads` → `Coffee & Tea` → `Drinks` → `Beer` → `Wine` → `Spirits & Liqueurs` → `Other`

Walk it once in your own shop and adjust. It matters more than any colour.

---

## 6. Assigning a label

Every food gets **exactly one** label — `labelId` is single-valued. The assignment rules are in Food Rules §9.1 and §9.2, in particular: label by what it **is**, not by origin or use.

A food with no label lands unsorted at the end of the shopping list. That is the quickest way to make the system useless.

---

## 7. Checklist

- [ ] Does the label answer "where in the shop", not "which property" (§1)?
- [ ] At least ten foods, no overlap with an existing label?
- [ ] Name from the fixed list, plural, no emoji?
- [ ] `color` set, six-digit hex, not the default `#959595`?
- [ ] Hue fits the zone and is not used twice?
- [ ] Shopping list order adjusted to the real route?
- [ ] Does every food have exactly one label?
