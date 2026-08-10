# Units: Creating & Mapping During Recipe Creation (EN)

> Part of the Mealie rule set. References in the form *Parse §x* point to **Food Rules (EN): Parsing & Creation**.

## Principle

Units are a **closed set** of roughly 25–40 entries. Importing a recipe almost never creates a unit — an unknown unit token is nearly always a spelling variant, a food, or a non-metric unit that needs converting.

> **Hard rule 1 — metric.** The database contains **only metric units** plus dimensionless count and container measures. Cup, ounce, pound, fluid ounce, pint, quart, stick and gallon are **never created as units**, in any language version.

> **Hard rule 2 — preserve the original.** When an amount is converted, the original figure must be recorded as a **note on the ingredient line**. A conversion without a note is data loss: it cannot be checked, cannot be corrected, and cannot be recognised on the next import.

---

## 1. The permitted set

### 1.1 Mass
`milligram (mg)`, `gram (g)`, `kilogram (kg)`

### 1.2 Volume
`millilitre (ml)`, `litre (l)`, `teaspoon (tsp)`, `tablespoon (tbsp)`

Teaspoon and tablespoon are permitted because they are metrically defined: **1 tsp = 5 ml, 1 tbsp = 15 ml**. Put that definition in the unit's `description`.

`cup` is **not** a permitted unit. Depending on origin it is 200, 237 or 250 ml, so it is always converted (§3).

### 1.3 Count and container measures
`piece`, `pinch`, `dash`, `bunch`, `sprig`, `clove`, `stick` *(of celery, not butter)*, `slice`, `leaf`, `head`, `handful`, `splash`, `packet`, `tin`, `jar`, `bottle`, `punnet`, `rasher`

These are dimensionless and are **not** converted. For variable containers, put the house assumption in `description`: `tin` → `Assume 400 g unless stated otherwise.`

### 1.4 The empty unit
`2 eggs`, `1 lemon` have no unit. That is correct and is never forced to `piece`.

---

## 2. Mapping on import

Stop at the first hit:

| Tier | Test | Action |
| --- | --- | --- |
| 0 | Token equals a unit's `abbreviation` | link |
| 1 | Token equals `name` or `pluralName` | link |
| 2 | Token is in the variant list (§2.1) | link |
| 3 | Token is a non-metric unit | **convert** (§3) |
| 4 | Token is really a food or a size | §2.2 |
| 5 | No hit | **review — do not create** |

### 2.1 Variant list
Units have no alias list in Mealie, so variants belong in the parser configuration:

| Target | Variants |
| --- | --- |
| tablespoon | `tbsp, tbs, T, Tbsp, tablespoons, tablespoonful` |
| teaspoon | `tsp, t, teaspoons, teaspoonful` |
| gram | `g, gr, gm, grams, grammes` |
| kilogram | `kg, kilo, kilos, kilogrammes` |
| millilitre | `ml, mL, millilitres, milliliters` |
| packet | `pkt, pkg, packet, package` |
| piece | `pc, pcs, piece, pieces` |

`T` and `t` appear here only as **inputs to recognise**. They are never used as a stored abbreviation (§4) — the `T`/`t` convention for tablespoon/teaspoon is a well-known cause of ruined recipes.

### 2.2 Not a unit token
| Detected | Why | Result |
| --- | --- | --- |
| `garlic clove` | food inside the token | unit `clove` + food `garlic` (Parse §4.1) |
| `large`, `medium`, `small` | size, not a measure | ingredient note |
| `to taste`, `a little` | not an amount | empty unit + note |
| `serving` | Mealie recipe field | use the servings field |
| `2 tbsp` | quantity inside the token | quantity goes in the amount field |

---

## 3. Converting non-metric amounts

### 3.1 Procedure
1. Detect the non-metric unit
2. **Determine the type:** liquid, mass, or dry volume
3. Convert (§3.2–3.4)
4. **Round sensibly** (§3.5)
5. **Write the note** (§3.6)
6. Link the metric unit

If step 2 or 3 is uncertain: **do not guess.** Leave the amount, put the original in the note, send the line to review. A wrong conversion in a baking recipe is worse than an open question.

### 3.2 Direct mass and volume
| Original | Metric | Practical value |
| --- | --- | --- |
| 1 oz | 28.35 g | **28 g** |
| 1 lb | 453.6 g | **450 g** |
| 1 fl oz | 29.57 ml | **30 ml** |
| 1 pint (US) | 473 ml | **475 ml** |
| 1 pint (UK) | 568 ml | **570 ml** |
| 1 quart (US) | 946 ml | **950 ml** |
| 1 gallon (US) | 3.785 l | **3.8 l** |
| 1 stick butter | 113.4 g | **115 g** |
| 1 inch | 2.54 cm | **2.5 cm** |

### 3.3 Liquids by volume
Density ≈ 1, so convert directly: 1 US cup = 240 ml, 1 UK/metric cup = 250 ml, 1 US tbsp = 14.8 ml ≈ **15 ml**, 1 US tsp = 4.9 ml ≈ **5 ml**.

Spoon measures from US sources therefore simply become `tbsp` and `tsp` — the discrepancy is under 2 % and below kitchen precision.

### 3.4 Dry ingredients by volume — density table
This is the only genuinely error-prone case. A cup of flour and a cup of honey differ by almost a factor of three. **Never route through millilitres and then estimate mass** — use the table.

Values per **1 US cup (240 ml)**:

| Ingredient | Mass |
| --- | --- |
| plain flour | 120 g |
| wholemeal flour | 130 g |
| sugar, white | 200 g |
| sugar, brown (packed) | 220 g |
| icing sugar | 120 g |
| butter | 227 g |
| oil | 218 g |
| milk, water | 240 g |
| plain yoghurt | 245 g |
| honey, syrup | 340 g |
| rolled oats | 90 g |
| rice, raw | 185 g |
| cocoa powder | 85 g |
| nuts, chopped | 120 g |
| breadcrumbs | 108 g |
| chocolate chips | 170 g |
| cheese, grated | 100 g |

Spoon measures of dry ingredients: 1 tbsp flour ≈ 8 g, 1 tbsp sugar ≈ 12 g, 1 tbsp butter ≈ 14 g, 1 tbsp honey ≈ 21 g, 1 tsp salt ≈ 6 g.

**If the ingredient is not in the table:** convert to millilitres, put the original in the note, send the line to review. Extend the table whenever the same ingredient appears twice.

### 3.5 Rounding
| Range | Step |
| --- | --- |
| < 20 g/ml | 1 |
| 20–100 g/ml | 5 |
| 100–1000 g/ml | 10 |
| > 1000 g/ml | 50, or kg/l to one decimal |

Never false precision: `236.588 ml` is wrong, `240 ml` is right. **Limit:** rounding may deviate at most 2 % from the exact value. In baking recipes with raising agents, salt or yeast, round finer when in doubt — a few grams decide the outcome there.

### 3.6 Note format (mandatory)
The note always begins with the same prefix so it can be found mechanically:

```
Original: 1 cup
Original: 2 sticks butter
Original: 8 oz
```

Only the original figure — no explanation and no conversion, since that is already in the line. Existing preparation notes are kept and appended with `; `:

```
finely chopped; Original: 1 cup
```

Keep the prefix as the English word `Original:` in every language version, so one detection rule works across the whole database.

### 3.7 Temperatures
Not units, and they live in the method steps, but they follow the same rule:

| °F | °C conventional | °C fan |
| --- | --- | --- |
| 300 | 150 | 130 |
| 325 | 160 | 140 |
| 350 | 175 | 155 |
| 375 | 190 | 170 |
| 400 | 200 | 180 |
| 425 | 220 | 200 |
| 450 | 230 | 210 |

Fan = conventional minus 20 °C. The original goes in brackets after it: `175 °C (Original: 350 °F)`.

---

## 4. When to create a unit after all

Rarely, and only when **all three** hold:

1. It is metric or dimensionless.
2. It does not already exist under a name, abbreviation or variant.
3. It appears in **more than one** recipe — a one-off stays in review.

When creating:
- `name` spelled out, singular, lowercase
- `abbreviation` in the conventional form with correct casing; **never single-letter** except `g` and `l`; never `gr` for gram; never `T` for tablespoon
- `pluralName` regular (`grams`, `pinches`, `leaves`); `pluralAbbreviation` = `abbreviation`, since abbreviations are never pluralised (`500 g`, not `500 gs`)
- `fraction` on for spoon and count measures, off for grams and millilitres
- `description` carries the definition or house assumption

---

## 5. Checklist

- [ ] Is the token really a unit, and not a food, a size or a quantity?
- [ ] Was the variant list checked?
- [ ] For a non-metric unit: was the type determined correctly (liquid / mass / dry volume)?
- [ ] For dry volume: was the density table used rather than an estimate?
- [ ] Ingredient not in the table → review rather than a guess?
- [ ] Rounded sensibly, deviation under 2 %?
- [ ] **Is the `Original: …` note set?**
- [ ] Was an existing preparation note preserved?
- [ ] Was a new unit avoided where a conversion would do?
