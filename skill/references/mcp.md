# Working with the mcp-mealie server

Only relevant when the [`mcp-mealie`](https://github.com/mgummich/mcp-mealie)
MCP server is connected. Without it,
ignore this file — `mealie_ctx.py` covers everything the modes need.

When it is connected it is the primary path. It talks to the same instance
over the same API, but it answers the survey questions server-side, so the
local index is not needed at all:

**Skip `index` and `audit` while the server is connected.** Building the
index is one request per recipe; `library_stats` is one call. An index that
is never built also never goes stale, so no `index --refresh` dance after a
write.

## Which call answers which question

| Question | Call |
|---|---|
| What exists, and how often is it used? | `library_stats(resource)` — `tags`, `categories`, `tools`, `foods`, `units`; every entry with its `recipe_count`, unused ones included, highest first |
| Is this food safe to delete? | `library_stats("foods")` — `recipe_count: 0` |
| Same recipe imported twice? | `find_duplicate_recipes()` — groups by name, punctuation and case ignored |
| Which source links are dead? | `check_recipe_links()` — `broken_sources`, plus `unverified_sources` for hosts that refuse the probe, plus recipes with no image |
| What does one recipe look like? | `get_recipe(slug, fields=[...])` |
| Survey a field across the library | `search_recipes(fields=["slug", "tags", "rating"], limit=100)` |
| What exists in a taxonomy right now? | `manage_taxonomy(resource, "list", search=...)` |

`foods` and `units` are the slow rollups — they need each recipe's
ingredients, so that sweep is one request per recipe and honors
`max_recipes`. Tags, categories and tools come off the recipe list in a
handful of requests.

`search_recipes` does not carry ingredients, instructions or notes; those
still need `get_recipe`. Never build a rollup by hand with one
`search_recipes` per name — that is the pass `library_stats` replaces.

## Writing

The three-phase rule does not change: ANALYSIS -> PLAN -> EXECUTION, nothing
written without approval. Only the execution changes.

**One write path per plan.** Either every write is an MCP call or the plan
goes into `actions.json` and through `apply` — never half by each. Mixed
execution has no order guarantee and no dry run over the whole set.

Execute through MCP when the plan is a flat list of changes. Batch them:

    manage_taxonomy("foods", "update", items=[
      {"item_id": "...", "name": "Scallion"},
      {"item_id": "...", "data": {"labelId": "..."}},
    ])

Every action except `list` takes `items` and runs the whole batch in one
call. The reply splits `results` from `errors`, each error carrying the index
and the item that failed, so one bad id does not strand the rest. Twenty-five
renames are one call, not twenty-five.

Keep `actions.json` and `apply` for what the batch form cannot do:

- **Order matters.** A label or unit must exist before the food that
  references it. `ORDER` in `actions.json` guarantees that; a sequence of MCP
  calls does not.
- **A dry run over the whole plan** before anything is written.
- Any run where the user wants the plan as a reviewable file.

If the plan went through `apply` while both are in use, nothing has to be
refreshed — no index exists in this mode.

## Meal plan

Only the MCP has meal plan operations; the script deliberately has none.

1. `get_meal_plan(start_date, end_date)` for the target week **and the week
   before**. The previous week is what tells you which dinners would repeat.
2. Candidates: `suggest_recipes(foods=[...])` when the user named
   ingredients they have, `search_recipes(tags=["Quick"])` or a cookbook when
   they described a style. Filter server-side rather than pulling fifty
   recipes and sorting them yourself; `search_recipes` takes tags, categories
   and tools, with `require_all` to switch from any-of to all-of.
3. One `add_meal_plan_entry(date, entry_type, recipe_slug)` per slot — there
   is no batch endpoint. Free-text entries need no recipe:
   `add_meal_plan_entry(date, title="Leftovers")`.
4. `random_meal_plan(start_date, end_date)` fills a whole range in one call
   and honors the meal plan rules configured in Mealie. It **adds to**
   existing entries rather than replacing them, so read the plan first if the
   week is partly full. Capped at 14 days per call.

`get_todays_meals` answers "what are we cooking today" without a date range.

## Import a recipe from a URL

Also MCP only.

1. `import_recipe_from_url(url)` — Mealie scrapes it and returns the recipe.
2. Read what the scraper produced. Sites vary; ingredients and times are
   often incomplete. Everything in `references/recipes.md` about fields,
   ingredients and steps applies to the result.
3. `update_recipe(slug, tags=[...], categories=[...], tools=[...])` files it.
   All three **merge** with what is already there and create names that do
   not exist yet — the response says which, so read that line back to the
   user before a typo becomes a permanent tag. `replace_tags=True` (or
   `replace_categories` / `replace_tools`) overwrites instead.
4. If the scraper missed the photo, `set_recipe_image(slug, url)` fetches one
   from an image URL and replaces whatever is there.

Ingredients, instructions and notes **replace** on update — read the recipe
first and pass the whole list back, not just the new items. Notes are
`{"title": ..., "text": ...}` objects; a plain string becomes an untitled
note.

`create_recipe` takes free text directly and runs ingredient lines through
Mealie's parser. `parse_ingredients` shows how Mealie would read a line
without writing anything — useful to check a parse before committing it.

## Differences worth knowing

`update_recipe` merges organizers and creates missing names. `retag_recipe`
in `actions.json` works on ids and removes explicitly. When the plan says
"remove tag X from 9 recipes", that is `retag_recipe`, not `update_recipe`.

`merge` exists for foods and units only and repoints every recipe that used
the loser. Tags and categories have no merge endpoint — re-tag the recipes
first, then delete the leftover. Deleting a duplicate food instead of merging
it strips it from those recipes.

`manage_taxonomy("...", "list")` is paged at 200 and reports the `total`. A
partial first page is not the whole table. For anything table-wide,
`library_stats` is cheaper and carries the counts.

`manage_taxonomy` `update` is a patch: fields you do not mention keep their
value. Get a `labelId` from `manage_taxonomy("labels", "list")`.

**No recipe deletion.** `delete_recipe` exists on the MCP side and is
permanent, needing the slug twice. This workflow still does not delete
recipes: duplicates are reported, the user removes them. Name the tool if the
user asks for it, do not call it inside a maintenance run.

**Read-only mode.** The server can run with writes disabled; a write tool
then fails with "server is in read-only mode". That is configuration, not a
retryable error — fall back to `mealie_ctx.py` for the write, or stop and say
so. The same goes for an auth error on every tool: `MEALIE_API_TOKEN` is
wrong, do not retry.
