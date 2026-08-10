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
| Is this dish already in the library? | `search_recipes(query="lentil curry")` — free-text over the recipe list, before an import |
| Which source links are dead? | `check_recipe_links()` — `broken_sources`, plus `unverified_sources` for hosts that refuse the probe, plus recipes with no image |
| Which recipes use this food/tag/category/tool? | `search_recipes(foods=[...])`, `tags=[...]`, `categories=[...]`, `tools=[...]` — the `usage` command of the script |
| What does one recipe look like? | `get_recipe(slug, fields=[...])`, `full=True` for the unabridged record |
| Survey a field across the library | `search_recipes(fields=["slug", "tags", "rating"], limit=100)` |
| What exists in a taxonomy right now? | `manage_taxonomy(resource, "list", search=...)` |
| Which cookbooks exist, with their ids? | `list_cookbooks()` |

`foods` and `units` are the slow rollups — they need each recipe's
ingredients, so that sweep is one request per recipe and honors
`max_recipes`. Tags, categories and tools come off the recipe list in a
handful of requests.

`find_duplicate_recipes` and `check_recipe_links` take `max_recipes` too, and
both say in a `note` when they stopped short of the library — read that line
before reporting a count as complete.

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

Tagging many recipes has its own batch:

    bulk_tag_recipes(slugs=[...], tags=["Quick"], categories=["Dinner"])

Names are plain text and are created if they do not exist yet. It **only
adds** — the recipes keep what they already carry. Removing a tag, or setting
one recipe's list exactly, is `update_recipe` with `replace_tags` /
`replace_categories` (there is no bulk form for tools).

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

An entry set wrongly is removed with `delete_meal_plan_entry(entry_id)`; the
id comes from `get_meal_plan`. There is no update — delete the slot and add
it again. Deleting an entry is a write like any other: it belongs in the plan
and needs approval, even though nothing but the schedule changes.

## Import a recipe from a URL

Also MCP only.

**Let Mealie scrape first, then repair.** Never read the page yourself to
build the recipe — the scraper is one server-side call and gets title,
ingredients, steps, times and photo off any site with usable markup, while
a recipe page costs thousands of tokens of navigation, comments and ads to
pull through the model. Import, look at the result, and spend the tokens
only on what is actually missing.

That makes it a patch job, not an authoring job: keep the scraper's values
where they are right, and touch a field only to fix it. Fetching the page is
the fallback for step 2, not the starting point.

0. Is it already there? `search_recipes(query="lentil curry")` on the dish
   name, spelling variants included. A second import of the same page is the
   most common source of duplicate recipes, and the script cannot delete the
   loser afterwards.
1. `import_recipe_from_url(url, include_tags=False, include_categories=False)`
   — Mealie scrapes it and returns the recipe. Both flags default to `True`
   and let the site's own tags into the taxonomy: "dinner-party-favourites",
   a cuisine as a category, the blog's tag cloud. That is exactly the mixed
   taxonomy `references/organizers.md` then has to clean up. Import bare and
   file it deliberately in step 3.
2. Read what the scraper produced and list what is wrong with it. Sites
   vary: usually the ingredients and steps are there and the times, yield,
   description or an unparsed ingredient line are not. Everything in
   `references/recipes.md` about fields, ingredients and steps applies to the
   result — including the language: a page in another language is imported as
   it stands and has to be translated to ${CONTENT_LANG} like any other
   recipe.

   Gaps that the recipe itself answers (times from the steps, yield from the
   amounts, an ingredient line for `parse_ingredients`) need no page. Read
   the page only for what is genuinely not in the import, and say in the plan
   that you are doing it.

   Empty ingredients or steps mean the scraper got nothing and the import
   left a stub behind — that is the one case where the page is the only
   source. The result says so itself in a `note` ("the scraper found no
   ingredients …"); trust that line over the placeholder text, which reads
   like content. Typical cause: the site
   renders its recipe in the browser and ships no data in the HTML, so
   nothing is there to find. Retrying does not help, and neither does
   another scraper; transcribe the page and set the fields with one
   `update_recipe`. Fill it from the page or tell the user, who removes the stub
   in the UI; see `references/maintenance.md`, section Stubs. Do not import
   the same URL a second time hoping for a better run.
3. `update_recipe(slug, tags=[...], categories=[...], tools=[...])` files it.
   All three **merge** with what is already there and create names that do
   not exist yet — the response says which, so read that line back to the
   user before a typo becomes a permanent tag. `replace_tags=True` (or
   `replace_categories` / `replace_tools`) overwrites instead.
4. If the scraper missed the photo, `set_recipe_image(slug, url)` fetches one
   from an image URL and replaces whatever is there.
   `upload_recipe_image(slug, path)` does the same from a file on disk — for
   a photo the user points at locally, never for a URL.

Ingredients, instructions and notes **replace** on update — read the recipe
first and pass the whole list back, not just the new items. Notes are
`{"title": ..., "text": ...}` objects; a plain string becomes an untitled
note.

`create_recipe` takes free text directly and runs ingredient lines through
Mealie's parser — for a recipe the user pastes or dictates, not for a URL.
A recipe Mealie creates starts with one placeholder ingredient ("1 Cup
Flour"). Since the ingredient list replaces rather than merges, pass the
complete list on the next update and the placeholder is gone; append to it
and it stays in the recipe.
Anything with a URL goes through the scraper. `parse_ingredients` shows how Mealie would read a line
without writing anything — useful to check a parse before committing it.

## Renaming a recipe changes its slug

Mealie derives the slug from the name. An `update_recipe` carrying `name`
therefore invalidates the slug you called it with, and every later call on
the old one gets a 404 — including `set_recipe_image` and a second
`update_recipe` for the remaining fields.

Consequences for the plan:

- Set **all** fields in one `update_recipe` call, rename included. Two calls
  where the first renames is the failure case.
- Take the new slug from `slug` in the response of that call, do not derive
  it from the name yourself; Mealie's slugification is its own. A response
  carrying `renamed_from` is the server saying the recipe moved, and
  `renamed_from` is the **old** slug — the dead one, not the one to use next.
- Set the image after the rename with the new slug, or before it with the
  old one — not with a slug noted earlier in the session.

## When a write half-landed

A 404 or a 500 in the middle of a sequence leaves the recipe partly updated:
new name, old ingredients, missing image. Recover in this order:

1. Find it again. After a rename `get_recipe(<new slug>)`, otherwise
   `search_recipes(query=<name>)` — the recipe is still there, only under a
   different address.
2. Read what actually landed and say so, field by field. What the call
   intended is not evidence.
3. Set the rest with **one** `update_recipe` on the current slug.

Do not re-import the URL to repair a recipe. That creates a second recipe
next to the damaged one, and this workflow deletes neither — one broken
state becomes a duplicate pair plus a broken state. Re-importing is only
right after the user has removed the damaged recipe in the UI.

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
