# Cookbooks

A cookbook in Mealie is not a collection of recipes but a **saved filter
rule**. It fills itself: whatever matches the rule appears in it, including
recipes imported later. Almost everything else follows from that.

## Phase 1 - Analysis

    ctx cookbooks

Returns the existing cookbooks - each with its filter and the number of
recipes it currently matches - plus categories, tags and tools with a recipe
count each. From that you can estimate how large a planned cookbook would
be, and see which of the existing ones have run empty.

**Create cookbooks only after categories and tags are cleaned up.**
Otherwise the filter is built on vocabulary that gets merged away in the
next pass, and it quietly empties. A cookbook does not create order, it
consumes it.

Create one only when all three hold: it is **expressible** as a filter on
existing categories, tags, tools, `rating` or `lastMade` (needs
hand-picking → not a cookbook); it is **recurring** (a one-off search is a
search); and it lands between roughly **5 and 50 hits**. Never invent a tag
just to make a filter work - if it fails the tag test, the cookbook fails
with it.

Not cookbooks: one per category (the category view does that), `To Try`
(that is the meal plan), one per person (that is households), `All
Recipes`, `Miscellaneous`, or a single menu (that is a meal plan).

`Never Cooked` - `lastMade` empty - is the most useful cookbook of all and
needs no tags whatsoever.

Ask about the purpose before designing rules. Typical patterns:

- **Everyday** - quick, few ingredients, meal-prep
- **Occasion** - guests, holidays, barbecue
- **Diet** - vegetarian, vegan, gluten-free
- **Course** - desserts, side dishes, breakfast
- **Season** - summer, autumn
- **Pantry** - one-pot, oven dish, leftovers

## Phase 2 - Plan, then stop

Plan per cookbook:

    Cookbook: Quick weeknight cooking
      RULE     tags.name CONTAINS ALL ["Quick", "One-pot"]
      MATCHES  about 18 recipes
      DESCR.   Dishes for under 30 minutes, mostly in a single pot.
      GAP      "quick" has only 6 recipes – check its assignment?

Always give the estimated number of matches. Below about five matches a
cookbook is not worth it; say so and propose assigning the tags more widely
first.

### Designing rules

The rule is a single string in `queryFilterString`. Mealie validates it on
write, so a malformed filter is refused with a 422 rather than saved:

| Pattern | Example |
|---|---|
| Match any of | `tags.name IN ["Dinner", "Lunch"]` |
| Match all of | `tags.name CONTAINS ALL ["Vegan", "Quick"]` |
| Exclude | `tags.name NOT IN ["Dessert"]` |
| Combine | `recipeCategory.name IN ["Dessert"] AND rating > 3` |
| By date | `createdAt > "2026-01-01"` |
| By equipment | `tools.name IN ["Air Fryer"]` |
| Never cooked | `lastMade = null` |

Operators: `IN`, `NOT IN`, `CONTAINS ALL`, `LIKE`, `NOT LIKE`, `=`, `<>`,
`>`, `<`, `>=`, `<=`, joined with `AND` / `OR` and grouped with brackets.
Filterable are the recipe fields and their relations - categories, tags,
tools, `rating`, `lastMade`, `createdAt`, household and user.

The syntax is version-dependent. Where the user can reach the interface,
the safest filter is the one built there and copied out of the cookbook
editor; a hand-written one that a later Mealie stops understanding empties
the cookbook without saying so.

Choose the joining operator deliberately:

- **OR** for collections: desserts = category Dessert OR tag sweets
- **AND** for intersections: quick AND vegetarian

An `IN` list is itself an OR and quickly produces cookbooks containing half
of everything. More than two or three conditions makes a cookbook
unpredictable. Build two cookbooks instead.

An empty `queryFilterString` is not a neutral default: a cookbook without a
filter matches every recipe.

Use only objects that already exist. If the rule needs a new tag, that is a
separate task: create the tag and assign it to recipes first (see
`references/organizers.md`), then the cookbook. A cookbook built on a
freshly created tag that is assigned nowhere is empty.

### Description

One or two sentences naming the purpose, not repeating the rule. Not:
"Recipes tagged quick and one-pot." Instead: "Dishes for under 30 minutes,
mostly in a single pot - for evenings when time is short."

### Public

`public: true` makes the cookbook reachable via the public group link. Ask
instead of setting it.

## Phase 3 - Execution

    apply actions.json

Afterwards check whether the number of matches meets the estimate - if it is
far off, the AND/OR setting is usually wrong. Report: CREATED (name, rule,
matches) · CHANGED · OPEN (discarded ideas with a reason).

## Reworking existing cookbooks

Cookbooks are the only entity that **breaks silently**. A merged tag, a
deleted category, a renamed tool - and the filter grasps at nothing. The
cookbook does not disappear, it empties, and nobody notices, because you do
not open an empty cookbook. So: after every cleanup of categories, tags or
tools, check the filters. This is the closing step of those runs, not a
project of its own.

The hit count per cookbook is the only metric that matters; `ctx cookbooks`
prints it next to the filter. For one at zero or with a collapsed count:

| Cause | Repair |
|---|---|
| tag was merged | rewrite the filter onto the survivor |
| tag moved to another entity | rewrite onto that entity |
| category demoted to a tag | change the condition from category to tag |
| tool deleted by the gating test | drop the condition or use the method tag |
| filter references an id | switch to the name |
| the vocabulary is gone entirely | delete the cookbook |

The last row matters: if a tag was rightly removed, the cookbook built on
it was not viable either. Never bring vocabulary back to rescue a cookbook.

`update_cookbook` changes the rule without recreating the cookbook - links
to it stay valid.

Deleting a cookbook loses **no recipe**, only a saved filter. It is the one
entity in the whole rule set where deletion is nearly consequence-free, so
be generous: zero hits with an intact filter means the need was not one;
over 30 % of the corpus is the corpus with an extra click. Two cookbooks
with largely the same hit set are one.

Filter on **names rather than ids** where possible - names survive a
database rebuild. At most three conditions: a filter you cannot explain in
one sentence will not be maintained. `extras` is not filterable at all, so
anything meant to drive a selection belongs in a tag.

## With the MCP server

`create_cookbook(name=..., tags=[...], categories=[...], tools=[...])` takes
the same name lists and writes the filter itself, matching your names to
Mealie's stored casing. `require_all=True` is the AND/OR switch, one flag for
all three lists instead of three.

`list_cookbooks()` is the analysis call and the only source of the ids the
other three need - names alone address nothing here.

`update_cookbook(cookbook_id, ...)` takes the same arguments and only changes
the fields you pass - never delete and recreate, that throws away the id.
`query_filter=""` clears the filter. `delete_cookbook(cookbook_id)` is for a
cookbook that should not exist at all; it removes the rule, not the recipes,
but any link to the cookbook dies with it - so it belongs in the plan and
needs approval like any other destructive step.

Reach for `query_filter` - the same filter string as above - only for what
the name lists cannot express; the two cannot be combined.

Verify with `get_cookbook_recipes(cookbook_id)` afterwards - an overly narrow
filter matches nothing, which is easy to miss.
