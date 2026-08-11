# Working with the mcp-mealie server

Only relevant when the [`mcp-mealie`](https://github.com/mgummich/mcp-mealie)
MCP server is connected. Without it, ignore this file — `mealie_ctx.py`
covers everything the modes need.

When it is connected it is the primary path: same instance, same API, but
the survey questions are answered server-side.

**Skip `index` and `audit` while it is connected.** Building the index is
one request per recipe; `library_stats` is one call. An index that is never
built also never goes stale.

## Which call answers which question

| Question | Call |
|---|---|
| What exists, and how often is it used? | `library_stats(resource)` — `tags`, `categories`, `tools`, `foods`, `units`; each entry with its `recipe_count`, unused included |
| Is this food safe to delete? | `library_stats("foods")` — `recipe_count: 0` |
| Same recipe imported twice? | `find_duplicate_recipes()` |
| Is this dish already in the library? | `search_recipes(query="lentil curry")` — before an import |
| Which source links are dead? | `check_recipe_links()` — `broken_sources`, `unverified_sources`, plus recipes with no image |
| Which recipes use this food/tag/tool? | `search_recipes(foods=[...])`, `tags=[...]`, `categories=[...]`, `tools=[...]` |
| What does one recipe look like? | `get_recipe(slug, fields=[...])`, `full=True` for everything |
| Survey a field across the library | `search_recipes(fields=["slug", "tags", "rating"], limit=100)` |
| What exists in a taxonomy right now? | `manage_taxonomy(resource, "list", search=...)` |
| Which cookbooks exist, with their ids? | `list_cookbooks()` |

`foods` and `units` are the slow rollups — they need each recipe's
ingredients, so that sweep is one request per recipe and honors
`max_recipes`. Tags, categories and tools come off the recipe list in a
handful of requests.

`library_stats` lists at most `top` used and `top` unused entries, 50 each by
default, and the totals are in `used` and `unused`. A library with more than
50 unused foods hands you fifty of them, so the deletion worklist is a page,
not the list: raise `top` before calling it complete.

`find_duplicate_recipes` and `check_recipe_links` take `max_recipes` too and
say in a `note` when they stopped short — as does `library_stats`. Read that
line before reporting a count as complete.

`search_recipes` carries no ingredients, instructions or notes; those need
`get_recipe`. Never build a rollup by hand with one `search_recipes` per
name — that is the pass `library_stats` replaces.

## Writing

The three-phase rule does not change. Only the execution does.

**One write path per plan.** Either every write is an MCP call or the plan
goes through `actions.json` and `apply` — never half by each. Mixed
execution has no order guarantee and no dry run.

Execute through MCP when the plan is a flat list of changes, and batch it:

    manage_taxonomy("foods", "update", items=[
      {"item_id": "...", "name": "Scallion"},
      {"item_id": "...", "data": {"labelId": "..."}},
    ])

Every action except `list` takes `items` and runs the batch in one call. The
reply splits `results` from `errors`, each error carrying the index and the
item that failed, so one bad id does not strand the rest.

Tagging many recipes has its own batch:

    bulk_tag_recipes(slugs=[...], tags=["Quick"], categories=["Dinner"])

Names are plain text and are created if they do not exist. It **only adds**,
and it covers tags and categories only. Removing one, or setting a recipe's
list exactly, is `update_recipe` with the list plus its switch:

    update_recipe(slug="dip", tags=["Quick"], replace_tags=True)

`replace_tags`, `replace_categories` and `replace_tools` are booleans, not
lists — without them `tags`, `categories` and `tools` merge into what the
recipe already carries. `tags=[]` with `replace_tags=True` empties the
field. Tools have no bulk form at all.

Keep `actions.json` and `apply` for what the batch form cannot do: **order**
(a label must exist before the food referencing it), **a dry run over the
whole plan**, the **plan lint**, the **changelog** that records what each
write overwrote, and any run the user wants as a reviewable file. Nothing
here has an undo, and the MCP path leaves no changelog — that alone decides
most destructive plans in favour of `apply`.

## Meal plan

Only the MCP has these; the script deliberately has none.

1. `get_meal_plan(start_date, end_date)` for the target week **and the week
   before** — the previous week is what tells you which dinners would repeat.
2. Candidates: `suggest_recipes(foods=[...])` when the user named
   ingredients they have, `search_recipes(tags=["Quick"])` or a cookbook when
   they described a style. Filter server-side, with `require_all` to switch
   from any-of to all-of.
3. One `add_meal_plan_entry(date, entry_type, recipe_slug)` per slot — no
   batch endpoint. Free-text entries need no recipe:
   `add_meal_plan_entry(date, title="Leftovers")`.
4. `random_meal_plan(start_date, end_date)` fills a range in one call and
   honors Mealie's own rules. It **adds to** existing entries rather than
   replacing them, so read the plan first. Capped at 14 days.

`get_todays_meals` answers "what are we cooking today". A wrong entry is
removed with `delete_meal_plan_entry(entry_id)`; there is no update. That
delete is a write like any other: it belongs in the plan.

## Import a recipe from a URL

Also MCP only.

**Let Mealie scrape first, then repair.** The scraper is one server-side
call and gets title, ingredients, steps, times and photo off any site with
usable markup, while a recipe page costs thousands of tokens of navigation
and ads to pull through the model. Import, look, and spend tokens only on
what is missing. That makes it a patch job: keep what the scraper got right.

0. Is it already there? `search_recipes(query=...)` on the dish name,
   spelling variants included. A second import of the same page is the most
   common source of duplicate recipes.
1. `import_recipe_from_url(url, include_tags=False, include_categories=False)`.
   Both flags default to `True` and let the site's tag cloud into your
   taxonomy — exactly what `organizers.md` then has to clean up. Import bare
   and file it deliberately in step 3.
2. Read what the scraper produced and list what is wrong. Everything in
   `recipes.md` applies to the result, including the language: a page in
   another language is translated like any other recipe. Gaps the recipe
   itself answers (times from the steps, yield from the amounts) need no
   page — read the page only for what is genuinely missing, and say so.

   Empty ingredients or steps mean the scraper got nothing and left a stub.
   The result says so in a `note`; trust that over the placeholder text,
   which reads like content. Typical cause: the site renders its recipe in
   the browser. Retrying does not help and neither does another scraper —
   transcribe the page and set the fields with one `update_recipe`, or tell
   the user, who removes the stub in the UI.
3. `update_recipe(slug, tags=[...], categories=[...], tools=[...])` files
   it. All three **merge** and create names that do not exist — the response
   says which, so read that back before a typo becomes a permanent tag.
   `replace_tags=True` overwrites instead.
4. If the scraper missed the photo, `set_recipe_image(slug, url)`, or
   `upload_recipe_image(slug, path)` for a local file.

Ingredients, instructions and notes **replace** on update — read the recipe
first and pass the whole list back. Notes are `{"title": ..., "text": ...}`
objects.

`create_recipe` takes free text and runs ingredient lines through Mealie's
parser — for a recipe the user pastes or dictates, never for a URL. What it
creates starts with one placeholder ingredient ("1 Cup Flour"); since the
list replaces, passing the complete list on the next update removes it.
`parse_ingredients` shows how Mealie would read a line without writing.

## Renaming a recipe changes its slug

Mealie derives the slug from the name, so an `update_recipe` carrying `name`
invalidates the slug you called it with; every later call on the old one
404s, `set_recipe_image` included.

- Set **all** fields in one call, rename included. Two calls where the first
  renames is the failure case.
- Take the new slug from `slug` in that response. A response carrying
  `renamed_from` is the server saying the recipe moved, and `renamed_from`
  is the **old** slug — the dead one.

## When a write half-landed

A 404 or 500 mid-sequence leaves the recipe partly updated. Recover in this
order: find it again (`get_recipe(<new slug>)` after a rename, otherwise
`search_recipes(query=<name>)`); read what actually landed and say so, field
by field — what the call intended is not evidence; then set the rest with
**one** `update_recipe`.

Do not re-import the URL to repair a recipe: that creates a second recipe
beside the damaged one, and this workflow deletes neither. Re-importing is
right only after the user has removed the damaged recipe.

## Differences worth knowing

`update_recipe` merges organizers and creates missing names. `retag_recipe`
in `actions.json` works on ids and removes explicitly. "Remove tag X from 9
recipes" is `retag_recipe`, not `update_recipe`.

`merge` exists for foods and units only and repoints every recipe that used
the loser. Tags and categories have no merge — retag first, then delete the
leftover. Deleting a duplicate food instead of merging it strips it from
those recipes.

`manage_taxonomy("...", "list")` is paged at 50 and reports the `total`. A
partial first page is not the whole table — `library_stats` is cheaper and
carries the counts. `update` is a patch: unmentioned fields keep their
value.

**No recipe deletion.** `delete_recipe` exists here and is permanent. This
workflow still does not delete recipes: duplicates are reported, the user
removes them. Name the tool if asked, do not call it in a maintenance run.

**Read-only mode.** The server can run with writes disabled; a write tool
then fails with "server is in read-only mode". That is configuration, not a
retryable error — fall back to `mealie_ctx.py` or stop and say so. Same for
an auth error on every tool: `MEALIE_API_TOKEN` is wrong, do not retry.
