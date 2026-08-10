# Labels

A label hangs off the **food**, not the recipe, and exists for the shopping
list: it groups and orders so you walk the shop once instead of three
times.

**A label answers "where is this in the shop?"** - not "what is this
culinarily" and not "what kind of dish is this". Those are categories and
tags, which hang off recipes.

Closed set, 29 entries, with a fixed zone palette. Growth is a defect
signal.

| Entity | Hangs off | Answers |
|---|---|---|
| Label | food | where in the shop? |
| Category | recipe | what kind of dish? |
| Tag | recipe | what property? |

## Setting the instance up

    seed labels --out actions.json

Writes all 29 with their zone colours; what exists is skipped. The colour
is functional, not decoration: labels of one zone share a hue, so a block
of colour on the shopping list says a new area starts before you read the
text. `Cheese` and `Dairy` looking similar is correct - they stand next to
each other in the shop.

Never leave a label on Mealie's default `#959595`; the plan lint warns. Do
not rely on colour alone - the name sits beside it and the ordering carries
the real structure.

## Phase 1 - Analysis

    audit labels

The numbers that matter, in this order:

- **foods with no label** - they land unsorted at the end of every list
- labels that do not name a product group (see below)
- labels on the default colour, or a hue used twice
- the size of `Other`: over 5 % of the corpus means it is a dumping ground

## Restoring the axis

Check every label: does it name a zone in the shop? If not it belongs to
another entity, and it is **moved, not deleted**:

| Label found | Destination |
|---|---|
| `Vegetarian`, `Vegan`, `Gluten-free` | tag, Diet facet |
| `Main`, `Dessert` | category |
| `Quick`, `Storecupboard` | tag, Effort or Keeping facet |
| `Christmas`, `Barbecue` | tag, Occasion facet |
| `Asian`, `Italian` | tag, Cuisine facet |
| `Favourites`, `Test` | delete outright |

Moving means: create the destination first, link the affected recipes or
foods, compare the counts, **then** delete the label. Give the label's
foods a correct product-group label beforehand, or they end up with none.

`Asian` is the tempting one - some shops really do have a world food aisle.
Soy sauce is still a condiment and rice a dry good: origin is a recipe
property, not a location.

## Merging

Candidates: singular/plural pairs, synonyms (`Dairy`/`Milk Products`),
broader and narrower terms nobody separates, translation duplicates.

**Not** for labels that genuinely sit apart in the shop: `Cheese` and
`Dairy` overlap conceptually and are two trips.

Survivor is the label with the most foods; relink **all** of the loser's
foods first, compare counts, then delete. Deleting a label silently clears
`labelId` on its foods, and that only surfaces on the next shopping trip.

Labels are organizers to the ACTIONS format: `update_organizer` and
`delete_organizer` with `kind: labels`.

## Assigning

Every food gets exactly one label - `labelId` is single-valued. Label by
what a thing **is**, not by its origin or use. The usual mistakes:

| Food | Wrong | Right |
|---|---|---|
| oyster sauce | Fish & Seafood | Sauces & Condiments |
| fish stock | Fish & Seafood | Stock & Flavourings |
| mozzarella | Dairy | Cheese |
| rolled oats | Nuts & Seeds | Breakfast Cereals |
| raisins | Sweets & Spreads | Fruit |
| tofu | Dairy | Legumes |
| peanut butter | Nuts & Seeds | Sweets & Spreads |
| hummus | Legumes | Sauces & Condiments |
| honey | Baking Supplies | Sweets & Spreads |
| coconut milk | Other | Dairy |

Work the unlabelled foods in order of how often they are used. Anything
genuinely unclassifiable gets `Other` - a worklist, not a resting place.

## Ordering

The label order is set per shopping list and is the actual payoff: it
follows the route through the shop, not the alphabet. The seed pack ships a
workable order for a typical supermarket; walk it once in your own shop and
adjust. It matters more than any colour.

Mealie holds this order per shopping list, so it is set in the UI rather
than through this workflow - say so instead of trying to write it.

## Phase 3 - Execution

    apply actions.json

Report: CREATED · RECOLOURED · MOVED (label -> destination entity, foods
relinked) · DELETED (was empty) · OPEN.

Afterwards: no food without a label, no label outside the product-group
axis, no default colour, no duplicate hue, `Other` under 5 %, and every
label moved in the axis pass has its foods findable on another label.
