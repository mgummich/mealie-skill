# Recipe mode

## Phase 1 - Analysis

<!-- agent-only -->
    ctx recipe <slug>
<!-- standalone: (The context is already in the prompt.) -->

Output: table `field | status` with status from {empty, ok, language,
unparsed, implausible}.
<!-- agent-only -->
If an ingredient is missing from the FOODS block, look it up specifically
with `ctx recipe <slug> --search "<term>"`.
<!-- standalone: If an ingredient is missing from the FOODS block you were given, first check the block for spelling variants and foreign-language equivalents; otherwise treat it as new. -->

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

## Ingredients

Search the FOODS block you were given first: exact name -> alias ->
singular/plural/spelling variant -> the ${CONTENT_LANG} equivalent of a
foreign-language term. Only then create something new.

Structure: `quantity` (number), `unit`, `food`, `note`.
`food` is the plain ingredient without preparation hints; `note` takes
"finely diced", "at room temperature", "drained", "to taste".
"1 can (400 g) tomatoes" becomes `400 | g | tomato | canned`.

Metric. Convert imperial and show it in the report: cup flour 125 g, cup
sugar 200 g, cup liquid 240 ml, stick butter 113 g, oz 28 g, lb 454 g,
°C = (°F-32)*5/9 rounded to 5. Mind densities, do not convert by a single
factor.

Units from the existing list; new ones only with `name`, `pluralName`,
`abbreviation`. For multi-part recipes, group ingredient sections via
`title`.

## New foods

`name` (singular, everyday term), `pluralName`, `description` (2-4
wiki-style sentences: what it is, origin/variety, culinary use, storage or a
common substitute - factual, no first person, no marketing language, no
amounts), `labelId`, `aliases` (synonyms plus the English term, so future
parsing matches).

If no suitable label exists, create one (name + hex color), modelled on
supermarket aisles: Fruit & Vegetables, Meat & Fish, Dairy, Dry Goods &
Baking, Cans & Jars, Spices & Herbs, Oils & Vinegars, Frozen, Drinks, Other.

## Steps

${CONTENT_LANG}, imperative, one step = one coherent action, no manual
numbering in the text. Sections (`title` on the first step of the section)
matching the ingredient sections: Preparation, Dough, Filling, Baking,
Finishing. Only form sections from about five steps upwards. Temperatures in
°C with the oven mode, times with a cue ("until the onions are translucent,
about 5 min"). Ingredient names consistent with the ingredient list.

## Notes

At most four, each with a title: storage and shelf life, freezing and
thawing, preparing ahead, substitutions (including vegan/gluten-free),
common pitfalls, suitable side dishes. Only what you can support.

## Image

<!-- agent-only -->
If `orgURL` is present, open the page in the browser and find the main image
(og:image or the image in the recipe schema). Otherwise search for a freely
usable image of the dish, preferably CC0/CC-BY (Wikimedia Commons, Pexels,
Unsplash). Nothing suitable found or the license unclear: no image, note it
in the report. Never the image of a different dish. Always name source and
license.
<!-- standalone: Without browser access, do not look for an image: use `set_image` only if an image URL is already present in the context you were given. Otherwise no image, note it in the report. Never the image of a different dish. -->

## Organizers

Always check the existing list first, including spelling variants and
language versions. `recipeCategory`: 1-2, functional (main course, dessert,
side dish, breakfast). `tags`: 3-8, lowercase - cuisine, diet (only when
supported by the ingredients), method, occasion; no duplication of the
category. `tools`: special equipment only (blender, 26 cm springform pan,
thermometer, mortar), no pots, pans, knives, bowls.

## Other fields

`name` concise, max. 60 characters. `description` 1-2 sentences on the dish,
flavour profile, occasion - not an echo of the title.
`recipeYield`/`recipeServings` derived from the amounts.
`prepTime`/`performTime`/`totalTime` as ISO-8601 ("PT25M"), resting times go
into `totalTime`. `nutrition` per serving, only when all main ingredients
come with amounts.

## Multiple recipes

    audit recipes        # also shows incomplete recipes

One recipe per plan. Batch processing reliably makes ingredients wander
between recipes.
