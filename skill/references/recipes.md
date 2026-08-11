# Recipe mode

A recipe is not a text document but a **structured assembly**: ingredient
lines with linked foods and units, steps, metadata. Only the structure
makes shopping lists, scaling and search work. A recipe whose ingredients
sit there as raw text is a picture made of letters.

## Phase 1 - Analysis

<!-- agent-only -->
    ctx recipe <slug>
<!-- standalone: (The context is already in the prompt.) -->

Output: table `field | status` with status from {empty, ok, language,
unparsed, implausible}.
<!-- agent-only -->
The RECIPE block is abridged: ids, timestamps, view settings, comments and
the scraper's rendered ingredient lines are stripped, everything the modes
read or write is there. `--full` gives the unabridged JSON - needed about
once a year, for a field this skill does not know about.

One call per recipe is enough. Everything the plan needs is in that output;
fetching the same recipe again only repeats it.
<!-- standalone: The context is complete: work from it and do not ask for a second copy of the recipe. -->
<!-- agent-only -->
If an ingredient is missing from the FOODS block, look it up specifically
with `ctx recipe <slug> --search "<term>"`.
<!-- standalone: If an ingredient is missing from the FOODS block you were given, first check the block for spelling variants and foreign-language equivalents; otherwise treat it as new. -->

Before **creating** a recipe, check whether it is already there - search by
dish name and by two or three characteristic ingredients. Duplicates cost
more here than anywhere else, because rating, notes and `lastMade` split
across both copies and neither holds the truth any more. Same dish with a
small variation is a `Variation` note on the existing recipe, not a second
recipe. Same dish from a different source with a clearly different method
may coexist - then sharpen both titles.

## Phase 2 - Plan, then stop

    A FIELDS       field | is | should be
    B INGREDIENTS  raw text -> qty|unit|food|note + [EXISTING] / [ALIAS: x->y] / [NEW]
    C NEW          every field that would be created, per object
    D STEPS        sections + number of steps, note on translations
    E IMAGE        source + URL
    F NOTES        titles
    G QUESTIONS
    H RISKS        what gets overwritten

<!-- agent-only -->
Write `actions.json`, check with `--dry-run`, ask for approval, stop.
<!-- standalone: Print the ACTIONS block, then STOP. -->

## Phase 3 - Execution

    apply actions.json --slug <slug>

Report: CHANGED (field - what/why) · CREATED (type - name - id) · REUSED
(found via name/alias) · CONVERTED (old -> new) · ESTIMATED · IMAGE (source
+ license) · CHECK (ingredient not referenced by any step, implausible
values, contradictions) · OPEN (left empty, with a reason)

# Content rules

## Required

`name`, at least one ingredient line with a linked `food`, at least one
step, `recipeServings`, exactly one category. A recipe with no times never
turns up in an effort-based search.

## Ingredients

The ingredient list is written back **whole**: Mealie replaces the field
rather than merging it, so a patch carrying three lines leaves a recipe of
three lines. Same for steps and notes; see `references/actions.md`.

Search the FOODS block you were given first: exact name -> alias ->
singular/plural/spelling variant -> the ${CONTENT_LANG} equivalent of a
foreign-language term. Only then create something new; the full cascade is
in `references/foods.md`.

Structure: `quantity` (number), `unit`, `food`, `note`. `unit` and `food`
are **objects with an id**, not names and not `foodId`/`unitId` — Mealie
takes those off the line and stores null, and the line then renders as
"80 heated" instead of "80 ml milk heated":

```json
{"quantity": 80,
 "unit": {"id": "9c35d9e9-…", "name": "Milliliter"},
 "food": {"id": "d77f8eb4-…", "name": "Milk"},
 "note": "heated", "originalText": "80 ml milk, heated",
 "referenceId": "0e2b1c7a-…"}
```

Keep the `referenceId` a line already has; Mealie mints it client-side and
a null one fails validation. A line without a unit — `2 eggs` — omits the
key rather than sending an empty object.

`food` is the plain ingredient without preparation hints; `note` takes
"finely diced", "at room temperature", "drained", "to taste".
"1 can (400 g) tomatoes" becomes `400 | g | tomato | canned`.
Those four fields, never `display`. Mealie composes the displayed line out
of them itself and puts the amount in front of whatever `display` holds, so
a `display` of "500 g flour" shows up as "500 500 g flour".

`originalText` holds the raw imported line and is **never overwritten** -
it is the evidence that lets any parse error be proved. Where it is missing
in an old recipe, write the current display value into it before repairing.

**One food per line.** `salt and pepper` is two lines, `2 carrots and 1
stick of celery` is two lines. Only separate lines reach the shopping list.

`salt to taste` is `quantity: 0`, no unit, `note: to taste` - never an
invented amount, it ends up on the shopping list. `2 eggs` has no unit.

Homemade components - `pizza dough`, `chicken stock (homemade)` - are
`referencedRecipe` on the line, not foods. If the sub-recipe does not exist
yet, create it or list its components; never create a food called "mashed
potato".

Order the lines by **use**, not by aisle. Sections (`title` on the first
line of the section) from about eight ingredients or where there are
genuine sub-preparations.

Metric. A cup of flour and a cup of honey differ by almost a factor of
three, so the density decides and never a single factor.

<!-- agent-only -->
Do not convert by hand - the table lives in the script:

    convert "1 cup plain flour" "8 oz" "350 F"
    120 g plain flour   [note: Original: 1 cup plain flour]

`REVIEW` means the food is not in the density table: leave the line and
list it under QUESTIONS, never estimate. `KEEP` means the unit is metric
already. Details in `references/units.md`.
<!-- standalone: Direct: 1 oz = 28 g, 1 lb = 450 g, 1 fl oz = 30 ml, 1 stick butter = 115 g, 1 inch = 2.5 cm, 1 US cup of liquid = 240 ml. Dry, per US cup: plain flour 120 g, wholemeal flour 130 g, white sugar 200 g, brown sugar 220 g, icing sugar 120 g, butter 227 g, oil 218 g, honey and syrup 340 g, rolled oats 90 g, rice 185 g, cocoa 85 g, breadcrumbs 108 g, grated cheese 100 g. Spoons: 1 tbsp flour 8 g, sugar 12 g, butter 14 g. °F: 350 -> 175 °C, 375 -> 190, 400 -> 200, 425 -> 220. A food that is not listed is NOT converted - leave the line and put it under QUESTIONS. tbsp and tsp are metric already and stay. -->

Write both parts: the converted amount **and** the `Original: …` note on
that ingredient line. The note is the evidence for a human and the marker
that stops a later pass converting the same line twice. Keep an existing
preparation note and append with `; `.

## Steps

${CONTENT_LANG}, imperative, one step = one coherent block of action - what
you do in one go before touching something else. Not one sentence per step,
not the whole recipe in one paragraph. No manual numbering in the text.

Sections (`title` on the first step of the section) matching the ingredient
sections: Preparation, Dough, Filling, Baking, Finishing. Only from about
five steps upwards. Temperatures in °C with the oven mode and the original
in brackets - `175 °C (Original: 350 °F)`. Times with a cue ("until the
onions are translucent, about 5 min"). Ingredient names consistent with the
ingredient list.

Repeat an amount in the text only when an ingredient is used more than once
or split - "stir in half the cheese" is necessary, "heat 2 tbsp olive oil"
is redundant. Where it is repeated it must match the line.

`ingredientReferences` link an ingredient to the step that uses it. An
ingredient no step references is either superfluous or a hole in the
method - it is the most reliable way to find a broken import.

## Notes

Objects of `title` and `text`, not one lump. **Fixed vocabulary**, or after
two years you have `Info`, `Note`, `Remark` and `Important!` side by side:

| Title | Content |
|---|---|
| `Source` | book, person, page - where `orgURL` does not fit |
| `Variation` | changes that do not justify a separate recipe |
| `Get ahead` | what can be done the day before |
| `Storage` | keeping, freezing, reheating |
| `Serve with` | sides, drinks, place in a menu |
| `Experience` | what did not work last time |

`Experience` is the most valuable and the most often forgotten - the only
place recording that the original was under-salted. Durable knowledge
sitting in a comment belongs here; comments are conversation and ephemeral.

One title once per recipe, at most five notes, text under roughly 400
characters, full sentences.

**Not in a note:** an action (that is a step, not even as a "tip"),
anything about a single ingredient (that is the line's `note`), a reference
like "see step 3" (steps get reordered), times and servings (they have
fields), a complete alternative recipe, or an allergen assurance.

Where text belongs, top to bottom, stop at the first yes: belongs to
exactly one ingredient → the line's `note`; an action in the sequence →
the step; applies to the whole recipe but is not an action → `notes[]`;
the one-liner on what the dish is for → `description`.

## Other fields

`name` concise, max. 60 characters - the dish as you would say it, no
superlative, no source, no time. `description` 1-2 sentences on what it is
and when you cook it, not an echo of the title.

`recipeServings` is the scaling basis; normalise to an everyday number.
Baking and preserves also fill `recipeYieldQuantity` and `recipeYield`
("12 muffins"), otherwise nobody knows whether one serving is one muffin or
the tray.

Times in one house format, resolved from the house rules - no ranges, take
the lower figure and put the range in a step. Waiting time (proving,
marinating, chilling) goes in `totalTime`, never in `prepTime`, or every
effort-based search is wrong.

`nutrition` only from the source, never estimated - an estimated figure is
worse than none, because it looks like a measurement. `rating` after
cooking, not at creation. `settings.public` false for text or images that
are not yours.

Organizers: `recipeCategory` 1-2 functional, `tags` at most eight each
mapping to a facet, `tools` gating equipment only. Always check the
existing lists first; see `references/organizers.md`.

## Image

<!-- agent-only -->
If `orgURL` is present, open the page in the browser and find the main image
(og:image or the image in the recipe schema). Otherwise search for a freely
usable image of the dish, preferably CC0/CC-BY (Wikimedia Commons, Pexels,
Unsplash). Nothing suitable found or the license unclear: no image, note it
in the report. Never the image of a different dish. Always name source and
license.

The instance downloads the URL itself, so it has to be reachable from there
and servable to a bot: a hotlink-protected CDN, a page behind Cloudflare or
a URL on the instance's own host fails. Mealie answers such a failure with
200 and sets the recipe's image token anyway, which would leave a broken
picture - `set_image` therefore checks the stored file and aborts the run
when nothing landed. On that message pick a different image URL, do not
retry the same one.
<!-- standalone: Without browser access, do not look for an image: use `set_image` only if an image URL is already present in the context you were given. Otherwise no image, note it in the report. Never the image of a different dish. -->

## After an import

A web import fills the fields, rarely correctly. Check five things: did the
lines parse (a line with no linked `food` is raw text), are the units
metric, did preparation land inside the food ("2 onions, finely chopped" as
the food), are the steps sensibly cut, and are the source's tags SEO terms
rather than taxonomy.

## Multiple recipes

    audit recipes        # also shows incomplete recipes

One recipe per plan. Batch processing reliably makes ingredients wander
between recipes.

The rule is about ingredients, not about the number of recipes. Split by
what is being changed:

- **Ingredients, steps, notes** - one recipe per plan, no exceptions. These
  are written as whole lists, and holding several recipes' lists at once is
  exactly how a quantity from one lands in another.
- **Field-level changes** (`name`, `description`, times, yield, image,
  tags/categories/tools) - as many recipes in one plan as the user wants.
  Each recipe is its own `patch_recipe`, values come from that recipe alone,
  so nothing can wander.

A user who asks for all 80 recipes at once gets one plan listing all 80 with
their concrete values, one approval, then the run - not 80 questions. What
does not lapse: the plan is shown before the first write, and a batch that
includes ingredients is still split by recipe.

For a long run, report per block of ten (`n/80 done`), collect errors and
show them at the end rather than stopping at the first one - but do stop
when the same error hits twice in a row, because that is a systematic fault
and the remaining 60 will hit it too.
