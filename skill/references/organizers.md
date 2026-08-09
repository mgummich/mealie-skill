# Categories, tags, tools

Unlike foods, there is **no merge endpoint**. Resolving a duplicate means:
retag every affected recipe (`retag_recipe`), then delete the object that
has become empty (`delete_organizer`). The order is enforced by the ACTIONS
format.

## Phase 1 - Analysis

    audit categories        # or: audit tags / audit tools

The output shows the recipe count per object plus four findings:

- **possible duplicates** - spelling and plural variants, across languages
- **unused** - zero recipes, dead entries
- **rare** - one or two recipes, usually too specific or a typo
- **largest** - the most frequently assigned ones; catch-all objects show up
  here

Summarize that and propose an order. Almost always sensible: duplicates
first, then rare ones, then unused ones.

## Categories vs. tags

The most common starting state is a mixed taxonomy. Check for it and say so:

- **Categories** are functional and exclusive: what kind of course is this?
  Main course, starter, dessert, side dish, breakfast, drink, baked goods.
  1-2 per recipe. More than about ten categories in total almost always
  means tags have slipped into the categories.
- **Tags** are everything else and freely combinable: cuisine (italian),
  diet (vegetarian, gluten-free), method (oven, one-pot, grill), occasion
  (meal-prep, quick, guests), season (summer).
- **Tools** are special equipment only: blender, 26 cm springform pan,
  thermometer, mortar, ice cream maker. No pots, pans, knives, bowls,
  boards.

If something sits in the wrong bucket ("vegetarian" as a category), the
clean route is: create or reuse a tag, retag the recipes in both fields with
`retag_recipe`, delete the old category.

## Phase 2 - Plan, then stop

<!-- agent-only -->
    ctx tags                    # list with recipe counts
    ctx tags --group "oven"     # recipes in this group
<!-- standalone:     ctx tags --group "oven"     # recipes in this group -->

Plan per group:

    Group: oven
      KEEP     oven (a1b2…) – 23 recipes
      DISSOLVE Oven (c3d4…) – 4 recipes   -> retag, then delete
      DISSOLVE ovenbaked (e5f6…) – 1 recipe -> retag, then delete
      AFFECTED 5 recipes: pumpkin-soup, lasagne, …

List the affected slugs - `retag_recipe` needs them individually anyway, and
the user should see what gets touched.

Retagging is reversible (you can tag again), deleting the object is not.
Mark both.

Rename instead of dissolving when only the spelling is off and no second
variant exists: `update_organizer` changes the name, every recipe keeps its
assignment. That is the gentler route - check it first.

Mind capitalization: tags lowercase, categories and tools in normal
spelling. A run that only unifies spelling is a good first plan.

## Unused and rare

Unused objects can be deleted without touching a recipe - still propose it,
do not just do it. Rare ones are rarely worth deleting: usually they belong
to a larger object, or they simply have not been assigned to more recipes
yet. Ask what is wanted.

## Phase 3 - Execution

    apply actions.json

Report: RENAMED · RETAGGED (recipe - from -> to) · DELETED (object, was
empty) · OPEN (deliberately kept, with a reason).

Keep batches small: at most five groups per run.
