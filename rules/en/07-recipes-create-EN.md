# Recipes: Creating & Importing (EN)

> The integrating rule set. All the others converge here: *Parse §x* points to **Food Rules (EN): Parsing & Creation**, *Units §x* / *Categories §x* / *Tags §x* / *Tools §x* to the respective creation documents.

## Principle

A recipe is not a text document but a **structured assembly**: ingredient lines with linked foods and units, numbered steps, metadata. Only the structure makes shopping lists, scaling and search possible. A recipe whose ingredients sit there as raw text is a picture made of letters.

> **Prime directive:** check whether the recipe already exists first. Duplicates cost more here than in any other entity, because ratings, notes and `lastMade` split across both copies and neither holds the truth any more.

---

## 1. Before creating

### 1.1 Duplicate check
Search by dish name and by two or three characteristic ingredients. A hit does not automatically mean a duplicate:

| Case | Action |
| --- | --- |
| Same dish, same source | **do not create** — open the existing recipe |
| Same dish, different source, clearly different method | create, and state the distinction in `description` |
| Same dish, small variation (different herbs, more heat) | **do not create** — add as a note (§8) to the existing recipe |
| Same base recipe, different final dish | create, and link the base as a sub-recipe (§5.6) |

The third row is the most common. A variation is a note, not a recipe.

### 1.2 Source
When importing from the web, **always** set `orgURL`. It is the only way to later check conversions, amounts or unclear steps against the original.

For recipes from books or people: put the source in a note titled `Source` (§8). Other people's recipe text belongs in your own collection, not in a public share — keep `settings.public` at `false` for text you did not write.

---

## 2. Required fields

Nothing is saved without these:

- `name`
- at least one ingredient line with a linked `food`
- at least one step in `recipeInstructions`
- `recipeServings`
- exactly one `category` (Categories §2)

Everything else is optional — but a recipe with no times never appears in an effort-based search.

---

## 3. Name and description

### 3.1 `name`
- The **dish name** as you would say it: `Lentil Soup with Bacon`
- No judgement, no superlative: not `Nan's Absolute Best Lentil Soup`
- No emoji, no source in the title, no numbering
- No amount or time in the title: `Lentil Soup`, not `30-Minute Lentil Soup` — that is what `prepTime` and tags are for
- Distinctions belong in the title when two recipes for one dish coexist: `Lentil Soup (Swabian)` and `Lentil Soup (Turkish)`

`slug` is generated automatically and never set by hand.

### 3.2 `description`
One or two sentences: **what it is** and **when you cook it**. No cookbook prose, no method, no ingredient list.

> Hearty stew with brown lentils and bacon; needs little attention and tastes better reheated.

---

## 4. Amounts and times

### 4.1 Servings and yield
Mealie separates three fields:

| Field | Meaning | Example |
| --- | --- | --- |
| `recipeServings` | number of portions — the basis for scaling | `4` |
| `recipeYieldQuantity` | amount of the finished product | `12` |
| `recipeYield` | unit of the yield, as text | `muffins`, `jars of 250 ml` |

For main dishes `recipeServings` is enough. For baking, preserves and base recipes fill the yield as well — otherwise nobody knows whether "1 serving" is one muffin or the whole tray.

**Normalise servings to an even, everyday number**: 2 or 4. A source `recipeServings: 6` may stay, but never rescale amounts to awkward values — Mealie scales on its own.

### 4.2 Times
These are free-text fields, so agree a **single format** and hold to it: `25 min`, `1 hr 30 min`.

- `prepTime` — active preparation
- `cookTime` — time on the hob or in the oven
- `performTime` — active work while cooking
- `totalTime` — set only when it is **not** the sum, i.e. when there is waiting: proving, marinating, chilling

No ranges (`20–25 min`) — take the lower figure and put the range in a step. Never hide waiting time in `prepTime`; it corrupts every effort-based search.

---

## 5. Ingredients — the core

### 5.1 The structure of a line
Every line splits into four fields, and each belongs in its place:

| Field | Content | Example |
| --- | --- | --- |
| `quantity` | the number | `2` |
| `unit` | the unit (Units §1) | `tbsp` |
| `food` | the food (parse rules) | `olive oil` |
| `note` | preparation, state, alternatives, original amounts | `plus extra for frying` |

`originalText` holds the raw imported line and is **never overwritten** — it is the evidence that lets any parse error be proved.

`display` is calculated and never set by hand.

### 5.2 One food per line
`salt and pepper` is two lines. `2 carrots and 1 stick of celery` is two lines. Only separate lines reach the shopping list correctly.

### 5.3 What belongs in the note
- Preparation: `finely chopped`, `sliced`, `at room temperature`
- State and selection: `as ripe as possible`, `unwaxed`
- Alternatives: `or crème fraîche`
- Part amounts: `1 tbsp of it for sprinkling`
- **Original amounts after conversion**: `Original: 1 cup` (Units §3.6)

Separate multiple entries with `; `: `finely chopped; Original: 1 cup`

### 5.4 What does **not** belong in the note
- Amounts that belong in `quantity`
- Units that belong in `unit`
- Actions that belong in `recipeInstructions` (`fry for 10 minutes`)
- The food itself

### 5.5 Ingredients with no amount
`salt to taste` gets `quantity: 0`, no unit, `food: salt`, `note: to taste`. Never enter an invented amount — it ends up on the shopping list.

Likewise `2 eggs` has **no** unit (Units §1.4).

### 5.6 Sub-recipes instead of catch-all foods
Mealie links recipes through `referencedRecipe` directly on the ingredient line. That is the right home for everything the parse rules exclude as a food:

- `mashed potato`, `homemade pesto`, `pizza dough`, `chicken stock (homemade)`

If the sub-recipe does not exist yet, either create it or put its components straight into the ingredient list — but **do not create a food called "mashed potato"** (Parse §7.1).

### 5.7 Sections
For multi-part recipes, set `title` on the **first line** of a section: `For the dough`, `For the filling`, `To serve`. The remaining lines in that section leave `title` empty.

Use sections only from roughly eight ingredients, or where there are genuine sub-preparations. Four ingredients under three headings is noise.

### 5.8 Order
List ingredients in **order of use**, not by aisle. Anyone reading top to bottom while cooking should not have to jump.

---

## 6. Method steps

### 6.1 One step = one continuous block of action
Not one sentence, not a whole page. Rule of thumb: what you do in one go before touching something else.

- Too fine: `Peel the onion.` / `Dice the onion.` / `Heat the oil.`
- Too coarse: one paragraph containing the entire recipe
- Right: `Peel and finely dice the onion. Heat the oil in a large pan and soften the onion over medium heat for 5 minutes.`

### 6.2 Language
- Imperative, second person: `Dice the onion`, not `The onion should be diced`
- Present tense, no narration
- State cooking times and recognisable cues: `5 minutes, until translucent`
- Temperatures metric with the original in brackets: `175 °C (Original: 350 °F)`

### 6.3 Amounts in step text
**Repeat** an amount in the text when an ingredient is used more than once or split — otherwise do not. `Stir in half the cheese` is necessary; `heat 2 tbsp olive oil in the pan` is redundant when it only occurs once.

Where an amount is repeated it must **match** the ingredient line. Scaling makes text drift, which is why this stays sparing.

### 6.4 `ingredientReferences`
Link ingredients to the step that uses them. This is the best protection against forgotten ingredients: an ingredient with no reference is either superfluous or a hole in the method.

### 6.5 `title` and `summary`
`title` is the step's **section heading** (`Dough`, `Filling`, `To finish`), matching the ingredient sections from §5.7. `summary` is a short form of the step — set it only when it says more than the first few words of the text.

---

## 7. Metadata

| Field | Rule set | Short rule |
| --- | --- | --- |
| `recipeCategory` | Categories §2 | exactly one, at most two |
| `tags` | Tags §2 | at most eight, each mapping to a facet |
| `tools` | Tools §2 | gating equipment only, zero to four |
| `rating` | — | set after cooking, not when creating |
| `nutrition` | — | copy only from the source; never estimate |

An estimated nutrition figure is worse than none, because it looks like a measurement.

---

## 8. Notes (`notes`)

### 8.1 Where text belongs — the boundary
Mealie has four homes for text. The commonest mistake is not badly written text but text in the wrong home: nobody finds it while cooking, and scaling gets it wrong.

| Question | Home | Example |
| --- | --- | --- |
| Does it belong to **exactly one ingredient**? | `recipeIngredient[].note` | `finely chopped`, `Original: 1 cup`, `or crème fraîche` |
| Is it an **action in the sequence**? | `recipeInstructions[].text` | `soften the onion for 5 minutes` |
| Does it apply to the **whole recipe but is not an action**? | `notes[]` | `the dough keeps for 2 days in the fridge` |
| Is it the **one-liner on what the dish is for**? | `description` | see §3.2 |

Work top to bottom. Stop at the first yes.

**Comments are not a substitute for notes.** They are conversation and they are ephemeral. Anything durable learned on the third cook goes into an `Experience` note — not into a comment, where it disappears under ten others.

### 8.2 Fixed titles (controlled vocabulary)
`notes` are objects of `title` and `text` — not one lump of text. As with tags, a fixed vocabulary applies, or after two years you have `Info`, `Note`, `Remark` and `Important!` side by side and nobody knows what sits where.

| Title | Content |
| --- | --- |
| `Source` | book, person, page number — only where `orgURL` does not fit |
| `Variation` | changes that do not justify a separate recipe (§1.1) |
| `Get ahead` | what can be done the day before or hours in advance |
| `Storage` | keeping, freezing, reheating |
| `Serve with` | sides, drinks, place in a menu |
| `Experience` | what did not work last time |

**`Experience` is the most valuable note and the most often forgotten.** It is the only place recording that the original was under-salted, or that the dough needs 10 minutes longer than written.

Add a new title only if it fits at least five recipes — otherwise the content belongs under an existing one.

### 8.3 Form
- **One title appears once per recipe.** Two `Variation` notes become one with two paragraphs.
- **At most five notes** per recipe. More nearly always means something belongs elsewhere per §8.1.
- Keep `text` under roughly 400 characters. Anything longer is usually its own recipe or a method step.
- Full sentences, not keywords — notes are read months later.

### 8.4 What does **not** belong in a note
- Actions that belong in `recipeInstructions` — not even as a "tip"
- Anything about a single ingredient, which belongs in that ingredient's `note`
- References like `see step 3` — steps get reordered and the reference silently goes wrong
- Times and servings, which have fields (§4)
- A complete alternative recipe — that is its own recipe
- Allergen assurances (Tags §5): a note reading `contains no nuts` looks like a guarantee and is not one

---

## 9. Image and settings

**Image:** one is enough, of the finished dish, ideally your own photo. Other people's images only with `settings.public: false`.

**Settings:** `public` only for your own recipes or your own wording. `showNutrition` only where `nutrition` is actually filled. `locked` for recipes that are final after being cooked several times.

---

## 10. Check after importing

A web import fills the fields, but rarely correctly. Always check these five:

1. **Did the ingredient lines parse?** Lines with no linked `food` are raw text and work nowhere.
2. **Are the units metric?** Convert cups, ounces and sticks, and put `Original:` in the note (Units §3).
3. **Did preparation land in the food?** Importers often write `2 onions, finely chopped` entirely into `food`.
4. **Are the steps sensibly cut?** Many sources deliver one single block, or sentence-by-sentence fragments.
5. **Were the source's metadata checked?** Imported tags are usually SEO terms and breach Tags §4.

---

## 11. Checklist

**Before creating**
- [ ] Searched for duplicates by name and characteristic ingredients?
- [ ] Is it really its own recipe and not a variation (§1.1)?
- [ ] `orgURL` or a source note set?

**Ingredients**
- [ ] Every line with a linked `food` and a fitting `unit`?
- [ ] One food per line?
- [ ] All units metric, conversions evidenced with `Original:`?
- [ ] Preparation in the note, not in the `food`?
- [ ] `originalText` untouched?
- [ ] Amount-free ingredients at `quantity: 0` rather than an invented number?
- [ ] Homemade components as `referencedRecipe` rather than as foods?
- [ ] Order matches use?

**Method**
- [ ] Steps as blocks of action, not sentences or one lump?
- [ ] Imperative, with cooking times and cues?
- [ ] Temperatures metric with the original given?
- [ ] `ingredientReferences` set — no ingredient without a step?

**Metadata**
- [ ] Exactly one category, at most eight tags, at most four tools?
- [ ] Times in the house format, waiting time in `totalTime` rather than `prepTime`?
- [ ] `recipeServings` set, plus yield for baking?
- [ ] Nutrition only from the source, never estimated?
- [ ] `public` only with your own text and your own image?
