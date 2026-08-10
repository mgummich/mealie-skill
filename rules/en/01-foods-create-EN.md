# Mealie Food Rules (EN): Parsing & Creation

## Purpose
These rules govern what happens when a **food string** arrives — from a recipe import, a manual entry, or a bulk clean-up. The job is, in order:

1. **Match** the string to a food that already exists.
2. If it does not match, decide whether it **should** exist.
3. Only then **create** it, using the naming rules in §8.

The default outcome is *match*, not *create*. Every unnecessary new food is a permanent duplicate that fragments shopping lists and breaks recipe aggregation.

> **Prime directive:** never create a food that differs from an existing one only by plural, casing, punctuation, diacritics, preparation wording, or a stripped qualifier.

---

## 0. Locale decision (set once, never mix)

Pick **one** English vocabulary as canonical for the whole database:

- **en-GB**: aubergine, courgette, coriander, rocket, prawn, mince, spring onion, plain flour
- **en-US**: eggplant, zucchini, cilantro, arugula, shrimp, ground beef, scallion, all-purpose flour

The variant you did not pick is an **alias** on the canonical food — it is never a second food, and never a reason to create. This file assumes en-GB; swap the columns if you choose en-US.

---

## 1. The food record

A food record is the unit both matching and creation operate on:

- `name` (string): canonical name (EN, singular, lowercase)
- `pluralName` (string): common plural, or equal to `name` for mass nouns
- `description` (string): `definition; use/preparation.`
- `aliases` (array): always present, at least `[]`, items as `{ "name": "..." }`
- `label` (string): exactly one label from §9

`name`, `pluralName` and every alias are **lookup keys**. Aliases are not decoration — they are the mechanism that makes matching work, so every resolved mismatch should feed back into them (§11).

---

## 2. What is a food string?

The food string is what remains of a recipe line after quantity, unit and instruction are removed. It is **not** the recipe line.

```
"2 tbsp finely chopped fresh coriander, plus extra to serve"
 └ quantity ┘ └ prep ────┘ └ FOOD ──────┘ └ serving note ──┘
                                 ↓
                         coriander [fresh]
```

A single line may contain **more than one** food string. Split on `and`, `or`, `/` and commas separating whole foods:
- `"salt and pepper to taste"` → two strings: `salt`, `pepper`
- `"olive oil, for frying"` → one string: `olive oil`

---

## 3. Normalisation pipeline (lookup only)

Apply in this exact order. The output is a **lookup key**, never something you write to the database — the stored `name` always keeps its proper form.

1. Unicode NFC; trim; collapse runs of whitespace
2. Fold case to lowercase
3. Strip wrapping punctuation, trailing commas/full stops, and bracketed asides — `(about 200g)`, `(optional)` — asides go to the recipe note, never the food
4. Fold diacritics: `é→e`, `ñ→n`, `î→i`
5. Strip leading articles and vague quantifiers: `a`, `an`, `the`, `some`, `a few`, `a little`
6. Strip quantities and units (§4.1)
7. Strip preparation modifiers (§4.2)
8. Strip marketing and provenance adjectives (§4.3)
9. Singularise (§4.4)
10. Extract qualifiers (§5) — **extract, do not discard**

The remainder is the **candidate base**.

> **Strip last, match longest first.** Run the full matching cascade against the *raw* string before stripping anything, then re-run it after each stripping stage. `smoked salmon`, `spring onion`, `double cream` and `clotted cream` all die if you strip adjectives before you look them up.

---

## 4. What gets stripped

### 4.1 Quantities and units
Numbers, fractions (`½`, `1/2`), ranges (`2-3`), and: `g, kg, mg, ml, l, tsp, tbsp, cup, oz, lb, fl oz, pinch, dash, knob, splash, handful, bunch, sprig, clove, stick, slice, rasher, punnet, packet, pack, tin, can, jar, bottle, x`

**Unit/food collisions.** Several unit words are also foods. Treat as a unit only when followed by `of` or immediately preceding a known food:
- `2 cloves of garlic` → unit — but `1 tsp cloves` → the spice `clove`
- `2 sticks celery` → unit — but `1 cinnamon stick` → `cinnamon [stick]`
- `a knob of butter` → unit — `stock` is never a unit

### 4.2 Preparation modifiers
`chopped, finely chopped, roughly chopped, diced, cubed, sliced, thinly sliced, minced, grated, finely grated, crushed, mashed, shredded, torn, peeled, deseeded, cored, trimmed, halved, quartered, cooked, cooled, softened, melted, beaten, drained, rinsed, at room temperature, to taste, to serve, plus extra, for greasing, for frying, for dusting, optional, divided`

### 4.3 Marketing and provenance
`good-quality, best, fresh-from-the, ripe, free-range, organic, extra-large, jumbo, baby (except where it names the food: baby corn, baby spinach), local, seasonal, homemade, store-bought, leftover`

### 4.4 Singularisation
Reverse the plural rules: `-ies → -y`, `-oes → -o`, `-ves → -f/-fe`, `-es`, `-s`. Leave **pluralia tantum** alone: `rolled oats`, `breadcrumbs`, `baked beans`, `greens`. If singularising produces no match but the plural did, the plural wins.

---

## 5. Qualifier extraction

These words are **not** stripped. They are lifted out and become bracket qualifiers, because they change which food is meant.

| Detected in the string                    | Qualifier      |
| ----------------------------------------- | -------------- |
| fresh                                     | `[fresh]`      |
| dried, dehydrated                         | `[dried]`      |
| whole (of a spice)                        | `[whole]`      |
| ground, powdered, milled                  | `[ground]`     |
| flaked, crushed (of chilli), flakes       | `[flakes]`     |
| stick, quill                              | `[stick]`      |
| leaf (of gelatine)                        | `[leaf]`       |
| juice of, juiced, freshly squeezed        | `[juice]`      |
| zest of, zested, finely grated zest       | `[zest]`       |
| peel, rind, strips of peel                | `[peel]`       |
| tinned, canned, in a tin, from a can      | `[tinned]`     |
| frozen, from frozen                       | `[frozen]`     |
| pickled, in vinegar, preserved            | `[pickled]`    |
| roasted, toasted                          | `[roasted]`    |
| smoked                                    | `[smoked]`     |

**Extraction rules**

- **One qualifier only.** If two are detected, keep the most defining and drop the other to the recipe note. `finely grated zest of 1 unwaxed lemon` → `lemon [zest]`, not `lemon [zest][fresh]`.
- **Possessive constructions invert.** `juice of 1 lemon`, `the zest of two limes`, `grated rind of an orange` — the head noun is the *qualifier*, the object is the base. Parse right to left.
- **Fixed product names beat qualifiers.** Before treating `smoked` as a qualifier, look up the whole string: `smoked salmon`, `smoked paprika` and `smoked mackerel` are foods in their own right.
- **Powder redirect.** When `[ground]` is extracted, also probe `<base> powder`. `1 tsp ground ginger` → no `ginger [ground]` exists → `ginger powder` matches. Same for `[flakes]` → `<base> flakes`.
- **Fixed word redirect.** When `[whole]` is extracted from a pepper, probe `peppercorn`: `1 tsp whole black pepper` → `black peppercorn`.

---

## 6. Matching cascade

Run tiers in order. **Stop at the first tier that returns exactly one hit.**

| Tier | Test                                                            | Action           |
| ---- | --------------------------------------------------------------- | ---------------- |
| 0    | Raw string equals `name` exactly                                 | Link             |
| 1    | Lookup key equals normalised `name` or `pluralName`              | Link             |
| 2    | Lookup key equals a normalised `alias`                           | Link             |
| 3    | Candidate base + extracted qualifier matches `base [qualifier]`  | Link             |
| 4    | Redirects fired: `<base> powder`, `peppercorn`, other fixed words | Link            |
| 5    | Candidate base matches, qualifier has no entry                   | See §6.1         |
| 6    | Head-noun strip: `<food> paste/purée/pieces/chunks` → `<food>`   | Link if whitelisted, else review |
| 7    | Fuzzy: edit distance ≤ 2 on keys of length ≥ 6                   | **Suggest only** |
| 8    | Nothing                                                          | Go to §7         |

**Never auto-accept tier 7.** Fuzzy hits go to the review queue with the candidate attached. Auto-accepting them silently merges `currant`/`current` and `cumin`/`cumin seed`.

**More than one hit at any tier is an ambiguity, not a match** — send it to review (§12) rather than picking the first.

### 6.1 Base matches but the qualifier has no entry
This is the most common real case, and the answer depends on whether the qualifier is a **splitting** one.

- **Splitting qualifiers** — `[fresh]`, `[dried]`, `[whole]`, `[ground]`, `[juice]`, `[zest]`, `[peel]`, `[flakes]`, `[stick]`, `[leaf]`: the food genuinely differs. Do **not** silently fall back to the base. Create the variant (§7) or send to review.
- **Non-splitting qualifiers** — `[tinned]`, `[frozen]`, `[pickled]`, `[roasted]`, `[smoked]`: these are storage or processing states. If no variant exists, link to the base and keep the qualifier as a recipe note. Only promote to its own food when the culinary role actually differs.

### 6.2 Default resolution for bare ambiguous bases
A bare base with no qualifier is not an error — recipes write this way constantly. Resolve with a fixed default table rather than sending every one to review:

| Bare string | Resolves to                | Rationale                    |
| ----------- | -------------------------- | ---------------------------- |
| pepper      | `black pepper [ground]`    | Table pepper is the default  |
| salt        | `salt`                     | Mass noun, no split          |
| garlic      | `garlic [fresh]`           | Fresh is the recipe default  |
| onion       | `onion [fresh]`            | Fresh is the recipe default  |
| ginger      | `ginger [fresh]`           | Fresh is the recipe default  |
| parsley     | `parsley [fresh]`          | Fresh is the herb default    |
| oregano     | `oregano [dried]`          | Dried is the default for this herb |
| cinnamon    | `cinnamon [ground]`        | Ground is the baking default |
| milk        | `whole milk`               | House default                |
| flour       | `plain flour`              | House default                |
| stock       | *review*                   | Genuinely unresolvable       |

Keep this table in the database, not in someone's head, and extend it whenever review resolves the same bare string twice.

---

## 7. Should it exist? (the create gate)

Only reached when the cascade returns nothing. Three questions, in order.

### 7.1 Is it a food at all?
**Yes** — raw materials, semi-finished products used as ingredients (flour, pasta, stock, sauces), condiments, and pre-processed items bought as a base (smoked mackerel, chicken schnitzel, gyros strips).

**No — do not create:**

| The string is…                     | Example                                  | Do this instead                                    |
| ---------------------------------- | ---------------------------------------- | -------------------------------------------------- |
| A brand                            | Philadelphia, Hellmann's, Marmite, Old Bay | Map to the generic (`cream cheese`, `mayonnaise`, `yeast extract`); add the brand as an alias only if it is genuinely generic in speech |
| A preparation you make yourself    | mashed potato, homemade pesto, batter    | Link to its components, or flag as a sub-recipe     |
| A finished dish                    | parfait, sorbet, petit four              | Flag — a dish is not a food                         |
| A leftover or state of a dish      | leftover roast chicken, cooled pasta     | Link to the base food, state goes in the note       |
| Too generic to shop for            | juice, dough, meat, cheese (unqualified) | Review — ask the recipe, don't guess                |
| A blend that is really an instruction | "pasta seasoning (oregano, basil, thyme)" | Split into its named components                  |

> **Exception:** if you **buy it as one product** *and* it has a **fixed, widely used product name** that appears as one recipe line, it may be created: `italian seasoning`, `garam masala`, `chinese five spice`, `herbes de provence`. Brand-to-brand variation is acceptable when the culinary role is constant.

### 7.2 Is it near-duplicate of something that exists?
If tier 7 produced any fuzzy candidate, **do not create** — go to review. This is the single most important guard in the whole document. Duplicate proliferation almost always enters here.

### 7.3 Is it common enough to be worth a record?
Be conservative. A one-off obscure ingredient from a single recipe can sit in review until it appears a second time. **When genuinely in doubt, create a separate food rather than over-merging** — a spurious separate food is fixable by merge; a wrong merge silently corrupts every recipe using either side.

---

## 8. Creating the food

Only now do the naming rules apply.

### 8.1 `name`
- Common English name in the chosen locale, **singular**, **lowercase**
- No brand names
- Anglicise where an English name exists (`chickpea` not `garbanzo`, `beetroot` not `red beet`); keep established loanwords (`tahini`, `miso`, `gochujang`, `crème fraîche`)

### 8.2 Qualifiers
`basename [qualifier]`, lowercase, single word, **maximum one per name**. Whitelist as in §5.

**English-specific exception 1 — powders are two words.** Where `X powder` is the natural product name, that is the `name`, not `x [ground]`: `garlic powder`, `onion powder`, `ginger powder`, `chilli powder`, `mustard powder`, `curry powder`, `cocoa powder`, `baking powder`. Never `garlicpowder`, never hyphenated.

**English-specific exception 2 — real words beat brackets.** English usually has one word where a bracket would be needed. Prefer it: `peppercorn` (→ `black peppercorn`), `bay leaf`, `breadcrumbs`, `rolled oats`, `passata`, `nutritional yeast`, `cornflour`, `icing sugar`.

**No brackets** when the product name is a fixed compound that is not a form or state: `chicken breast`, `chicken thigh`, `egg yolk`, `egg white`, `cottage cheese`, `double cream`, `streaky bacon`.

### 8.3 `pluralName`
- Regular `+s`/`+es`; irregular `leaf → leaves`, `anchovy → anchovies`
- Mass nouns: `pluralName == name` (`rice`, `salt`, `flour`, `butter`, `oregano`)
- Already-plural names: `pluralName == name` (`rolled oats`, `breadcrumbs`)
- Bracket variants pluralise the countable part: `cinnamon [stick]` → `cinnamon [sticks]`; `lemon [juice]` stays unchanged

### 8.4 Seed the aliases immediately
A new food with `"aliases": []` will fail to match the next recipe that phrases it differently. At creation, add:

1. **The string that triggered creation**, if it is a legitimate variant
2. **The other locale**: `eggplant` ↔ `aubergine`, `shrimp` ↔ `prawn`, `scallion` ↔ `spring onion`, `arugula` ↔ `rocket`
3. **Spelling variants**: `-ise`/`-ize`, `yoghurt`/`yogurt`, `chilli`/`chili`/`chile`, `whisky`/`whiskey`, `doughnut`/`donut`
4. **Diacritics dropped**: `creme fraiche`, `jalapeno`, `puree`
5. **Space and hyphen variants**: `spring-onion`, `all purpose flour`
6. **Powder variants**: `garlic-powder`, `powdered garlic` for `garlic powder`

### 8.5 Never an alias — always a separate food
- Varieties: `granny smith`, `maris piper`, `san marzano`
- Derived forms: `lemon [juice]` ≠ `lemon`; `lime [zest]` ≠ `lime`
- Different products: currants ≠ raisins; `cornflour` ≠ `cornmeal`
- Preparations: espresso ≠ coffee; pulled pork ≠ pork shoulder
- Genuinely different products: `buffalo mozzarella` ≠ `mozzarella`; `double cream` ≠ `single cream`
- Fresh vs dried where both exist

> **False-friend warning:** in en-US, *cilantro* is the fresh leaf and *coriander* is the seed. Alias `cilantro` onto `coriander [fresh]`. Do **not** alias bare `coriander` onto `coriander seed` — put it in the §6.2 default table instead, where the ambiguity is visible.

### 8.6 Naming examples
| ❌ Wrong                  | ✅ Right                          |
| ------------------------ | -------------------------------- |
| Philadelphia             | cream cheese                     |
| Marmite                  | yeast extract                    |
| pomme de terre           | potato                           |
| pomodori pelati          | tomato [tinned]                  |
| fromage frais            | soft cheese                      |
| coriander (unqualified)  | coriander [fresh] / coriander seed |
| garbanzo bean            | chickpea (alias: garbanzo bean)  |

---

## 9. Labels (assigned at creation)

### 9.1 Principles
1. Label by what it **is**, not origin or application — fish stock → Stock & Flavourings, oyster sauce → Sauces & Condiments
2. Cheese is always separate from Dairy
3. Sweets & Spreads covers sweet products including sweet spreads
4. Cured & Deli Meats covers processed meat including spreadable

### 9.2 Common mistakes
| Food              | ❌ Wrong             | ✅ Right                |
| ----------------- | ------------------- | ---------------------- |
| oyster sauce      | Fish & Seafood      | Sauces & Condiments    |
| fish stock        | Fish & Seafood      | Stock & Flavourings    |
| mozzarella        | Dairy               | Cheese                 |
| cappuccino powder | Dairy               | Coffee & Tea           |
| rolled oats       | Nuts & Seeds        | Breakfast Cereals      |
| buckwheat         | Baking Supplies     | Pasta, Rice & Noodles  |
| raisins           | Sweets & Spreads    | Fruit                  |
| tofu              | Dairy               | Legumes                |
| peanut butter     | Nuts & Seeds        | Sweets & Spreads       |
| pâté              | Meat                | Cured & Deli Meats     |
| tzatziki          | Dairy               | Sauces & Condiments    |
| hummus            | Legumes             | Sauces & Condiments    |
| jam               | Sauces & Condiments | Sweets & Spreads       |
| honey             | Baking Supplies     | Sweets & Spreads       |
| coconut milk      | Other               | Dairy                  |

### 9.3 The 29 labels
| #  | Label                  | Examples                                      |
| -- | ---------------------- | --------------------------------------------- |
| 1  | Vegetables             | tomato, onion, carrot, jalapeño               |
| 2  | Fruit                  | apple, banana, raisins                        |
| 3  | Fresh Herbs            | basil, parsley, lemongrass                    |
| 4  | Potatoes & Tubers      | potato, celeriac, radish                      |
| 5  | Meat                   | steak, mince, pork tenderloin                 |
| 6  | Poultry                | chicken, chicken breast, duck, turkey         |
| 7  | Fish & Seafood         | salmon, prawn, mussel, nori                   |
| 8  | Cured & Deli Meats     | ham, bacon, salami, pâté, chorizo             |
| 9  | Dairy                  | milk, yoghurt, cream, coconut milk            |
| 10 | Cheese                 | cheddar, mozzarella, parmesan, cream cheese   |
| 11 | Eggs                   | egg, egg yolk, egg white                      |
| 12 | Bread & Pastry         | bread, croissant, tortilla                    |
| 13 | Baking Supplies        | flour, sugar, baking powder, yeast            |
| 14 | Breakfast Cereals      | rolled oats, muesli, cornflakes               |
| 15 | Pasta, Rice & Noodles  | spaghetti, rice, ramen, udon                  |
| 16 | Legumes                | chickpea, lentils, tofu                       |
| 17 | Nuts & Seeds           | almond, walnut, sesame seed                   |
| 18 | Herbs & Spices         | cinnamon, nutmeg, paprika                     |
| 19 | Oil, Vinegar & Fat     | olive oil, balsamic vinegar, butter           |
| 20 | Sauces & Condiments    | ketchup, soy sauce, sriracha, pesto, mayonnaise |
| 21 | Stock & Flavourings    | chicken stock, fish stock, stock cube         |
| 22 | Snacks                 | crisps, prawn crackers, popcorn               |
| 23 | Sweets & Spreads       | chocolate, sweets, jam, honey, peanut butter  |
| 24 | Drinks                 | cola, orange juice, tonic                     |
| 25 | Wine                   | red wine, sherry, port                        |
| 26 | Beer                   | lager, wheat beer, IPA                        |
| 27 | Spirits & Liqueurs     | rum, whisky, cointreau                        |
| 28 | Coffee & Tea           | coffee, green tea, rooibos                    |
| 29 | Other                  | cannot be classified                          |

---

## 10. Descriptions

**Format:** `[Short definition]; [use/preparation].` — maximum 100 characters, one characteristic plus one typical application, no marketing.

- Dark sauce made from oyster extract; savoury flavouring in Asian cooking.
- Oily fish; versatile to cook.
- Cajun spice blend; hot, with paprika and cayenne.

---

## 11. Feedback loop

Matching only improves if resolutions are written back. After **every** manual resolution:

- Resolved to an existing food, and the string was a genuine synonym or spelling variant → **add it as an alias**
- Resolved to an existing food, but the string was a derived form (`lemon juice` → `lemon`) → **do not alias**; either the variant food is missing, or the parse was wrong
- Resolved to a bare ambiguous base twice → **add a row to the §6.2 default table**
- Resolved by stripping a word you had to strip by hand → **add that word to §4**

A resolution that changes nothing in the rules will present itself again next week.

---

## 12. Ambiguity and review

Send to review rather than guessing when:
- two or more foods match at the same tier
- a splitting qualifier was extracted but no variant food exists
- a fuzzy candidate exists (tier 7) — always
- the string looks like a dish, a brand, or an instruction
- the food string is empty after stripping (the parser ate the food — usually a unit/food collision, §4.1)

Review items carry: the raw recipe line, the lookup key, the tier reached, and every candidate considered. Without the raw line, a reviewer cannot tell a parse bug from a missing food.

---

## 13. Worked examples

| Recipe line                                | Lookup key            | Path                            | Result                  |
| ------------------------------------------ | --------------------- | ------------------------------- | ----------------------- |
| `2 tbsp finely chopped fresh coriander`    | `fresh coriander`     | strip prep → extract `[fresh]`  | `coriander [fresh]`     |
| `juice of 1 lemon`                         | `lemon juice`         | possessive inversion            | `lemon [juice]`         |
| `1 x 400g tin chopped tomatoes`            | `tomato`              | extract `[tinned]`, tier 3      | `tomato [tinned]`       |
| `1 tsp ground ginger`                      | `ginger`              | `[ground]` → powder redirect    | `ginger powder`         |
| `2 cloves garlic, crushed`                 | `garlic`              | `clove` = unit → §6.2 default   | `garlic [fresh]`        |
| `salt and pepper to taste`                 | `salt` / `pepper`     | split → §6.2 defaults           | `salt` + `black pepper [ground]` |
| `a good glug of Hellmann's`                | `hellmann's`          | brand → generic                 | `mayonnaise`            |
| `200g leftover roast chicken, shredded`    | `roast chicken`       | leftover/state of a dish        | `chicken` + note        |
| `1 tsp whole black peppercorns`            | `black peppercorn`    | tier 1 on raw string            | `black peppercorn`      |
| `100g cornflower`                          | `cornflower`          | fuzzy hit on `cornflour`        | **review** — not a match |

The last row is the point of the whole document. `cornflower` is a real word, so it will never fail a spellcheck, and auto-accepting the fuzzy hit would be wrong exactly as often as it would be right.

---

## 14. Checklists

**Parsing**
- [ ] Was the raw string tried before any stripping?
- [ ] Were multiple foods in one line split out?
- [ ] Were qualifiers extracted rather than stripped?
- [ ] Did the redirects fire (powder, peppercorn, fixed words)?
- [ ] Was a bare ambiguous base resolved from the default table, not by guessing?
- [ ] Did the cascade stop at the first single hit?
- [ ] Was every fuzzy hit sent to review rather than accepted?

**Creating**
- [ ] Did the full cascade genuinely return nothing?
- [ ] Is it a food, not a brand, dish, preparation or instruction?
- [ ] Was there any near-duplicate? (if yes: review, do not create)
- [ ] Is `name` common English, singular, lowercase, in the chosen locale?
- [ ] Did you use the real English word (`peppercorn`, `garlic powder`) instead of inventing a bracket form?
- [ ] Is `pluralName` right, including mass nouns and pluralia tantum?
- [ ] Are aliases seeded — including the string that triggered creation?
- [ ] Is the label from the fixed list?
- [ ] Is `description` in the fixed format and under 100 characters?
