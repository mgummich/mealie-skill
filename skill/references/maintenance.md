# Maintenance

Corpus-wide checks. Each gets its own plan.

**A corpus-wide sweep of the recipes is not worth it**, unlike the master
data: the set is too large and the work too manual. Prioritise by impact -
recipes actually cooked (`lastMade`, a high `rating`) first, then recipes
with broken ingredient lines, since those break shopping lists and scaling,
then the rest, occasionally.

Run the master data first - foods, units, tags - or you tag with tags that
are merged away afterwards.

The headline number for the whole library is the **share of ingredient
lines with a linked `food`**. `audit recipes` reports it; above 95 % is the
target, and it is the one figure that says whether the library works as a
database or only as a set of texts.

## Duplicate recipes

    audit recipes

Two sources of suspicion:

- **Name duplicates** - same normal form ("Lentil curry" / "Lentil Curry").
  Usually genuine double imports.
- **Ingredient similarity** - Jaccard score over the food ids from 0.6 up.
  Finds double imports with a different title, but also legitimate variants.

A high score is not proof. Before proposing anything, compare the recipes
themselves with `ctx recipe <slug>` and look at: number of steps, servings,
source URL, image, completeness.

Recommendation in the plan:

    Pair: lentil-curry <-> lentilcurry (0.67)
      KEEP    lentil-curry – 8 steps, image, source, notes
      DELETE  lentilcurry – 3 steps, no image, same source
      OR      keep both: different heat level, a variant

The script does not delete recipes - there is deliberately no operation for
it. Present the pairs to the user and let them delete in the UI. What can be
automated: mark the weaker recipe as a variant with `patch_recipe`, or move
content into the better one.

Do not treat legitimate variants as duplicates: same base with a different
preparation (oven/pan), serving sizes, a vegan version.

## Stubs

The same audit ends with `STUBS` - recipes with neither ingredients nor
steps. Usually an import that failed silently: the title is there, the
content is not.

Check each one with `ctx recipe <slug>` before saying anything - a recipe
that keeps everything in the notes is not a stub. For a genuine stub there
are two routes:

1. A source URL exists: reimport it (MCP mode can, see `references/mcp.md`)
   or fill the recipe by hand from the page.
2. Nothing to work from: present it for deletion. The script deletes no
   recipes, that happens in the UI.

List stubs as a table `recipe | source URL | recommendation`. Never delete
silently and never fill a stub with invented content - that is the same rule
as everywhere else.

## Dead images and source URLs

<!-- agent-only -->
    audit links                 # recipes without image, without source
    audit links --check-urls    # check source URLs for reachability
<!-- standalone:     audit links --check-urls    # check source URLs for reachability -->

`--check-urls` sends one HEAD request per recipe - with a large instance
that takes a while and puts load on other people's servers. Run it once,
note the result, do not repeat it routinely.

The result comes in two blocks. `DEAD SOURCE URLS` is 404, 410, 451 and a
refused connection - the page is gone. `UNVERIFIED` is everything else,
403 and 429 above all: recipe sites block bots and rate-limit, and those
pages open fine in a browser. **Never treat an unverified URL as dead.**
Present that block as a list to check by hand, and change nothing on it.

For a dead source URL:

1. Check whether the page moved (search for the domain plus the recipe
   name). Found: `patch_recipe` with the new `orgURL`.
2. Otherwise look for an archived version and use that.
3. Nothing found: clear `orgURL` and note it in the report. The recipe
   itself stays - the content is there.

Recipes without an image can be handled in recipe mode; see
`references/recipes.md`, section Image.

## Repairing ingredient lines

The highest-yield pass on the recipes themselves, and the one that raises
the headline number. Typical damage from old imports:

| Damage | Detection | Repair |
|---|---|---|
| line is raw text | no `food` linked | parse it, link `food` and `unit` |
| preparation inside the food | `food` reads `onions, finely chopped` | preparation to `note` |
| amount in the note | `note` reads `about 200 g` | into `quantity` and `unit` |
| several foods on one line | `salt and pepper` | two lines |
| invented amount | `1 piece salt` | `quantity: 0`, no unit, `note: to taste` |
| homemade component as a food | `food` reads `pizza dough` | `referencedRecipe` |
| unit contains a food | `unit` reads `garlic clove` | `unit: clove`, `food: garlic` |

`originalText` stays untouched - in every repair it is the only evidence of
what was there. Where it is missing, fill it from the current display value
first, then repair.

Converting the amounts comes **after** this: a line can only be converted
once its food and unit are recognised at all. See `references/units.md`.

Because these are whole-list writes, the one-recipe-per-plan rule applies;
see `references/recipes.md`.

## Deriving diet tags from ingredients

    ctx diet --limit 25

Returns the ingredient list and the already assigned tags per recipe.

Only **exclusion criteria** can be derived, and only when the ingredients
are fully parsed. Unparsed ingredients mean: cannot be judged, skip and show
it in the report.

- **vegetarian** - no meat, no fish, no seafood
- **vegan** - additionally no dairy, eggs or honey
- **gluten-free** - no wheat, spelt, rye, barley, oats (unless declared
  gluten-free), no beer, soy sauce, couscous, bulgur, seitan
- **lactose-free** - no milk, cream, butter, cream cheese; hard cheese and
  ghee are borderline, do not assign automatically

Pitfalls that lead to wrong tags: fish sauce and anchovies in Asian pastes,
Worcestershire sauce, gelatine in desserts, lard in pastry, parmesan with
animal rennet for "vegetarian", soy sauce for "gluten-free", stock of
unknown kind.

When in doubt, **do not tag**. A missing tag is a minor annoyance, a wrong
"gluten-free" is a health risk. List uncertain cases under QUESTIONS, naming
the ingredient that decides it.

Plan as a table `recipe | existing tags | new | reason`. The reason names
the deciding ingredient, not the whole list. Execution via `retag_recipe`
with `add`.
