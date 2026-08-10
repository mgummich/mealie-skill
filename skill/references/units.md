# Units

A closed set, 25-40 entries. An unknown unit token is almost never a new
unit: it is a spelling variant, a food, a size, or a non-metric unit that
needs converting.

**Hard rule 1 - metric only.** Cup, ounce, pound, fluid ounce, pint, quart
and gallon are never stored, in any language version. The plan lint refuses
them outright.

**Hard rule 2 - keep the original.** A converted amount carries
`Original: 1 cup` as a note on the ingredient line. Without it the
conversion cannot be checked, cannot be corrected, and cannot be recognised
as already done - which is how a line gets converted twice.

Permitted: mg, g, kg, ml, l, tsp and tbsp (metrically defined, 5 ml and
15 ml), plus dimensionless count and container measures - piece, pinch,
dash, bunch, sprig, clove, stick (of celery), slice, leaf, head, handful,
splash, packet, tin, jar, bottle. Container assumptions (`tin` = 400 g)
belong in the unit's description and in the house rules.

`2 eggs` and `1 lemon` have **no** unit. That is correct and is never
forced to `piece`.

## Phase 1 - Analysis

    audit units

Report: total, gaps, unused, duplicate groups. Two findings outrank the
rest:

- **every non-metric unit with its recipe count** - the conversion worklist
- **abbreviation collisions** - the same abbreviation on two units makes
  mapping non-deterministic. `T` on both teaspoon and tablespoon, `l` on
  both litre and leaf. A hard error, resolved before any merge. Remove
  every single-letter abbreviation except `g` and `l`.

## Setting the instance up

    seed units --out actions.json

Writes the whole permitted set - names, plurals, abbreviations, aliases,
descriptions and Mealie's `standardQuantity`/`standardUnit` - as a plan.
What the instance already has is skipped, so it is safe to re-run. Never
type this table out by hand.

Standardisation is set for the seven metric units and deliberately null for
count measures: a standardised `pinch` would be added up in shopping lists.

## Converting

    convert "1 cup plain flour" "8 oz" "350 F"
    120 g plain flour   [note: Original: 1 cup plain flour]

Do not convert in your head. A cup of flour and a cup of honey differ by
almost a factor of three, so the density table decides, and it lives in the
script.

- `REVIEW` - the food is not in the density table. Leave the line, list it
  under QUESTIONS. **Never estimate.**
- `KEEP` - the unit is metric already (tbsp, tsp) and the line stays.

Write both parts into the recipe: the converted amount and the `Original:`
note. Keep an existing preparation note and append with `; ` -
`finely chopped; Original: 1 cup`.

Temperatures come along, in the steps: `175 °C (Original: 350 °F)`. A
recipe with metric ingredients and °F in the text is half converted, which
is worse than not converted. Inch tin sizes too: 8 → 20 cm, 9 → 23,
10 → 26.

## Phase 2a - Fill gaps

    ctx units --limit 25

`name`, `pluralName`, `abbreviation` (conventional casing, never `gr` for
gram, never `T` for tablespoon), `pluralAbbreviation` equal to the
abbreviation for metric symbols, `fraction` on for spoon and count
measures, `description` carrying the definition or the house assumption.

Units have no alias list in Mealie for matching purposes beyond what the
seed pack sets, so spelling variants belong in the unit's `aliases` and in
the house rules.

## Phase 2b - Merge duplicates

    ctx units --group "gram"

Candidates: singular/plural pairs, the spelled-out form beside the
abbreviation, spelling variants, the same abbreviation twice.

**Never merge:** teaspoon and tablespoon (a factor of three), US and UK
volumes while both exist, packet/tin/jar (different containers, different
assumptions), pinch and dash.

Survivor by recipe count; move the loser's spellings onto the survivor as
aliases, relink, verify, delete, log. Same procedure as foods.

## Eliminating non-metric units

The largest and riskiest pass in the whole rule set, because it changes
**amounts**, not units. Goal: zero non-metric units.

Per unit, from the worklist:

1. Pull **every** referencing ingredient line with its food and amount.
2. Set aside the lines whose food the density table does not know → review,
   do not convert.
3. Convert the rest **line by line** with `convert`. Never in bulk: the
   factor depends on the food, and a blanket "all cups × 240 ml" destroys
   every baking recipe in the corpus.
4. Write the `Original:` note on each line, preserving an existing note.
5. Relink to the metric unit, then delete the old unit **only** once its
   count is zero. Still referenced at the end: leave it, do not delete.

Baking recipes first and individually - a few grams decide the outcome
there, savoury recipes forgive rounding. A line already carrying
`Original:` is never converted again.

Because this rewrites ingredient lists, it follows the recipe rule: one
recipe per plan for ingredient changes; see `recipes.md`.

## Phase 3 - Execution

    apply actions.json

Report: CREATED · UPDATED · MERGED (from -> to, recipes rewritten) ·
CONVERTED (lines, with the unit they left) · OPEN (left for review, with
the reason).

Afterwards: no non-metric units left or each one justified, no abbreviation
collisions, ingredient line count unchanged, every converted line carrying
`Original:`. Recalculate about 20 converted lines by hand, at least five
from baking recipes - it is the only check that catches a systematic
conversion error before it reaches a thousand lines.
