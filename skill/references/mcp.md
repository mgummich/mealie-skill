# Working alongside the mcp-mealie server

Only relevant when the `mcp-mealie` MCP server is connected. Without it,
ignore this file — `mealie_ctx.py` covers everything the modes need.

Both talk to the same instance over the same API. They are not
interchangeable: the script owns the index and the batch, the MCP owns the
things the script deliberately has no operation for.

## Split of duties

| Job | Use |
|---|---|
| Index, audits, usage counts, duplicate and link-rot reports | `mealie_ctx.py` |
| Every plan written as `actions.json` and executed with `apply` | `mealie_ctx.py` |
| Meal plan: read, fill, random | MCP |
| Import a recipe from a URL | MCP |
| Search or suggest recipes interactively (`search_recipes`, `suggest_recipes`) | MCP |
| Look at one recipe outside a plan (`get_recipe`) | MCP |
| Delete a recipe | neither — see below |

Anything that appears in both — taxonomy edits, merges, retagging, cookbook
creation, recipe patches, images — goes through `mealie_ctx.py` whenever it
is part of a plan. The three-phase rule and the `ORDER` guard live there; an
MCP call bypasses both.

## Rules

**One write path per plan.** A plan is executed either entirely by `apply`
or entirely by MCP calls, never half by each. Mixed execution has no order
guarantee and no dry run over the whole set.

**MCP writes invalidate the index.** `mealie_ctx.py` only discards
`.mealie_index.json` after its own writing `apply`. It cannot see an MCP
write, so usage counts, duplicate groups and gap lists silently keep
describing the state from before. After any MCP write that touches recipes,
foods, units or organizers:

    index --refresh

Do that before the next audit, not after noticing the numbers disagree.

**No recipe deletion.** `delete_recipe` exists on the MCP side. This
workflow still does not delete recipes: duplicates are reported, the user
removes them by hand. Name the tool if the user asks for it, do not call it
inside a maintenance run.

**Read-only mode.** The MCP server can run with writes disabled; a write
tool then fails with "server is in read-only mode". That is configuration,
not a retryable error — fall back to `mealie_ctx.py` for the write, or stop
and say so.

## Differences worth knowing

`update_recipe` **merges** tags, categories and tools unless
`replace_tags`/`replace_categories`/`replace_tools` is set, and creates
names that do not exist yet. `retag_recipe` in `actions.json` works on ids
and removes explicitly. When the plan says "remove tag X from 9 recipes",
that is `retag_recipe`, not `update_recipe`.

`create_cookbook` on the MCP takes one Mealie filter string
(`query_filter`), while `actions.json` takes `categories`/`tags`/`tools`
lists plus `requireAll*`. There is no `update_cookbook` on the MCP side, so
reworking an existing cookbook is a script job.

`manage_taxonomy` lists 200 rows per page and reports the total — a partial
first page is not the whole table. For anything table-wide the index is
cheaper anyway: use `audit`.

`parse_ingredients` shows how Mealie itself would read a line. Useful to
check a parse before committing it; it writes nothing.
