# Foods and units

Applies to `foods` and `units` alike - both have a real merge endpoint. Two
tasks, never in the same plan: **filling gaps** is harmless, **merging
duplicates** is destructive.

## Phase 1 - Analysis

    audit foods          # or: audit units

Report: total count, distribution of gaps, unused entries, duplicate groups
with recipe counts. Then ask where to start.

The duplicate suspicion is a coarse normal-form heuristic. It finds
tomato/tomatoes, but not mouse/mice or scallion/spring onion. Check the
groups on their merits and add pairs the heuristic misses.

## Phase 2a - Fill gaps

    ctx foods --limit 25

Plan as a table `food | missing | addition`. Only add missing fields, never
overwrite existing values.

- `name`: singular, everyday term ("chickpea", not "canned chickpeas"). If
  the name is wrong, show it in the plan and correct it.
- `pluralName`: correct plural form in ${CONTENT_LANG}.
- `description`: 2-4 wiki-style sentences - what it is, origin/variety,
  culinary use, storage or a common substitute. Factual, no first person, no
  marketing language, no amounts.
- `labelId`: a matching label from the list you were given. If none exists,
  create one (name + hex color), modelled on supermarket aisles: Fruit &
  Vegetables, Meat & Fish, Dairy, Dry Goods & Baking, Cans & Jars, Spices &
  Herbs, Oils & Vinegars, Frozen, Drinks, Other.
- `aliases`: synonyms, regional names, spelling variants without diacritics
  and the English term.

For units instead: `name`, `pluralName`, `abbreviation`,
<!-- agent-only -->
`useAbbreviation`. Units have no label and no description; the tool only
reports plural, aliases and abbreviation as gaps there.
<!-- standalone: `useAbbreviation`. No label. -->

## Phase 2b - Merge duplicates

    ctx foods --group "tomato"

The target is the food used by the most recipes; on a tie, the better one
(description, label, plural set). If its name is wrong, fix it with
`update_food` first, then merge.

Plan per group:

    Group: tomato
      KEEP    tomato (3f2a…) – 14 recipes, label set
      MERGE   tomatoes (91bc…) – 2 recipes  -> becomes an alias
      MERGE   Tomato (55de…) – 0 recipes    -> becomes an alias
      THEN    update_food: aliases += tomatoes, Tomato

The merge rewrites the affected recipes and deletes the source food. It
cannot be undone - state that explicitly in the plan, with the recipe count.

After every merge, attach the names of the deleted objects to the target as
`aliases`, otherwise the same duplicate appears again on the next import.

**Do not merge** when there is a real difference despite a similar name:
tomato/cherry tomato, milk/buttermilk, sugar/powdered sugar, pepper
(vegetable)/ground pepper, onion/spring onion, tbsp/tsp. When in doubt leave
it and list it under QUESTIONS.

## Unused entries

`audit` lists foods and units no recipe uses. They are mostly harmless
(leftovers of old imports), but they make good merge sources: an unused
duplicate can be removed without touching a recipe. Do not delete unasked -
propose it and give a reason.

## Phase 3 - Execution

    apply actions.json

Report: UPDATED (object - which fields) · MERGED (from -> to, number of
rewritten recipes) · ALIASES ADDED · OPEN (deliberately not merged, with a
reason).

Keep batches small: at most 25 gaps or 5 duplicate groups per run.
