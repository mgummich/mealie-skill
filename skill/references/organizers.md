# Categories, tags, tools

Unlike foods, there is **no merge endpoint**. Resolving a duplicate means:
retag every affected recipe (`retag_recipe`), then delete the object that
has become empty (`delete_organizer`). The ACTIONS order enforces that
sequence.

- **Categories** are the shelf: what kind of dish is this? Closed set,
  10-20, one per recipe and at most two.
- **Tags** are the stickers: everything else, for filtering. Open but
  controlled, 40-120, at most eight per recipe.
- **Tools** are gating equipment only: without it the recipe cannot be
  made. Zero to four per recipe, and zero is a normal answer.

## Phase 1 - Analysis

    audit categories        # or: audit tags / audit tools

Per object the recipe count plus four findings: possible duplicates,
unused, rare (one or two recipes), largest. Propose an order - duplicates
first, then rare, then unused.

Two numbers say whether the taxonomy itself is broken: recipes carrying
more than two categories, and the average categories per recipe. Above 1.5
the axis has collapsed.

## Categories: one axis

Every category must answer the same question. Two axes compete: **dish
type** (Starter, Main, Side, Soup, Salad, Dessert, Baking, Bread, Sauce &
Dip, Drink, Basics) and **meal** (Breakfast, Lunch, Dinner, Snack). Pick
one, record it in the house rules, hold to it. Recommended: dish type - the
same soup is a main at lunch and a starter at dinner, so meal is a property
of use and becomes a tag.

Everything off the axis is **moved, not deleted**: cuisine, diet, effort,
occasion, method, source and status all become tags; an ingredient
(`Chicken`) becomes nothing, because ingredient search covers it.

Create a category only when it sits on the axis, will hold at least 15
recipes within a year, and you want to **browse** it rather than filter by
it. Browsing is a category, filtering is a tag. In doubt make it a tag: a
tag can be promoted later, a superfluous category clutters the shelf
permanently. A category under five recipes after a year becomes a tag; a
tag over 15 on the axis is worth promoting.

Naming: noun, singular, title case, no emoji, no source or brand names.

## Tags: one facet each

Every tag belongs to exactly one facet, and the facet table lives in the
house rules, not in the name:

| Facet | Examples |
|---|---|
| Cuisine | italian, thai, levantine |
| Diet | vegetarian, vegan, gluten-free |
| Occasion | christmas, barbecue, breakfast |
| Effort | quick, involved, weeknight |
| Method | oven, one-pot, air fryer, sous-vide |
| Season | summer, asparagus season |
| Keeping | freezable, meal prep, uses leftovers |
| Audience | kid-friendly, dinner-party |
| Source | nan's recipes, own recipe |

A concept that fits no facet is not a tag - check the entity instead. Scan
the facet before creating: most duplicates arise because someone created
`quick` without having seen `weeknight`. One concept per tag: `quick and
easy` is two.

**Never a tag:** anything Mealie has a field for (`30 minutes`,
`serves 4`, `5 stars`), an ingredient, a duplicate of the category, gating
equipment, a rating like `tasty`, a working status like `TODO`.

**No `no X` tags.** `gluten-free` and `dairy-free` are search aids, not
assurances - they say nothing about traces or the brand used. A tag phrased
as a negative reads as a guarantee and is not one; the plan lint warns.

Naming: lowercase where the language allows, singular, one concept, no
emoji, no `#`, hyphenation decided once.

## Tools: the gating test

One question: **does a functioning average kitchen already have it?**

Yes → not a tool: knife, board, saucepan, pan, bowl, sieve, baking tray,
whisk, grater, oven, hob.

No → tool: air fryer, ice cream maker, sous-vide circulator, food
processor, stand mixer, mincer, waffle iron, pestle and mortar, pasta
machine, sugar thermometer, springform tin, tagine, wok, muffin tin.

Borderline: does its absence **prevent** the dish or merely inconvenience
it? A stick blender inconveniences the soup. In doubt, not a tool.

Tools have **no aliases**, so every differing spelling is a second record
that nobody notices - `Springform Tin`, `Springform 23cm`, `Cake Tin
(springform)`. Look at the list before creating anything. Generic English
term, singular, title case, no brands (`Thermomix` → `Food Processor`),
unless the brand has genuinely become the generic term (`Slow Cooker`).

Sizes only where they determine the outcome (`Springform Tin 23 cm` - a
20 cm tin overflows), always metric, rounded to standard tin sizes: 8 inch
→ 20 cm, 9 → 23, 10 → 26.

`air fryer` as both a tool and a Method tag is correct, not a duplicate:
the tool answers "can I make this", the tag answers "show me all air fryer
recipes". They must be spelled identically.

`onHand` is the household inventory, not a wishlist. Set deliberately, or
"what can I cook tonight" answers nothing.

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

List the affected slugs - `retag_recipe` needs them individually anyway,
and the user should see what gets touched.

The survivor here is the object with the **compliant name**, not
automatically the one with the most recipes: unlike foods, relinking is
cheap and the naming decides future consistency.

Retagging is reversible, deleting the object is not. Mark both. Rename
instead of dissolving when only the spelling is off and no second variant
exists - `update_organizer` keeps every assignment. Check that first.

Work synonyms **facet by facet** rather than pairwise; clusters sit inside
one facet and checking that way is orders of magnitude faster.

## Unused, rare, oversized

Unused objects can be deleted without touching a recipe - still propose it.
Rare ones usually belong to a larger object or simply have not been
assigned yet. A tag on over 90 % of recipes filters nothing and goes. A
category holding over 40 % of the corpus wants splitting.

Recipes over the caps (eight tags, two categories, four tools) are trimmed
last, when the merges have already shrunk the list. Keep Cuisine, Diet and
Occasion first - they are filtered most; Source and Audience go first.

## Phase 3 - Execution

    apply actions.json

Report: RENAMED · RETAGGED (recipe - from -> to) · DELETED (object, was
empty) · MOVED (object -> destination entity) · OPEN (deliberately kept,
with a reason).

The integrity check: every object moved to another entity must have left
the same count behind there. Deleting `Vegetarian` as a category without
first tagging its 60 recipes loses 60 assignments irretrievably.

Keep batches small: at most five groups per run.
