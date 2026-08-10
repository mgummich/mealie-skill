---
name: mealie
description: Maintains a Mealie instance. Improve recipes (fill empty fields, parse ingredients against the food list, translate steps, convert to metric, set an image), clean up foods and units (description, plural, label, aliases, merge duplicates), consolidate categories/tags/tools, create cookbooks, find duplicate recipes and dead links, derive diet tags, import a recipe from a URL, fill the meal plan. Use whenever the user works on their recipe library: ingredient parsing, foods, duplicates, cookbooks, tagging, planning the week's meals, adding a recipe URL — Mealie need not be named.
---

# Mealie maintenance

Always three phases: **ANALYSIS -> PLAN -> EXECUTION**.
Nothing is written without explicit approval of the plan.
Never mix two kinds of task in one plan.

## Pick a mode and read the matching reference

Read **only** the reference for the current mode, not all of them:

| Task | Reference |
|---|---|
| Clean up a recipe, parse ingredients, fill fields | `references/recipes.md` |
| Foods or units: gaps, duplicates | `references/foods.md` |
| Consolidate categories, tags, tools | `references/organizers.md` |
| Create or rework a cookbook | `references/cookbooks.md` |
| Duplicate recipes, dead images/source URLs, diet tags | `references/maintenance.md` |
| Meal plan, recipe import from a URL, working with the MCP server | `references/mcp.md` |

The ACTIONS format is the same for every mode: `references/actions.md`.
Read that file only once phase 2 is due.

Read `references/mcp.md` whenever the `mcp-mealie` MCP server is connected —
it changes how every other mode gathers its data.

## Tool

`scripts/mealie_ctx.py` wraps every API call. Do not read its source, call
it with `--help`.

The path is relative to this skill directory, not to the working directory —
prefix every call with it, otherwise the command is not found:

    python .agents/skills/mealie/scripts/mealie_ctx.py <command>

    setup [--check]                    check the connection, store credentials
    index [--refresh]                  build the local recipe index
    audit <what> [--limit N]           foods units categories tags tools
                                       recipes links
    ctx recipe <slug> [--search T]     recipe + matching foods + organizers
                      [--full]         unabridged JSON, rarely needed
    ctx <what> [--limit N] [--group G] foods units categories tags tools
                                       cookbooks diet
    usage <kind> <id>                  recipes using a food/unit/category/tag/tool
    convert "<amount>" [...]           non-metric amount -> metric + the
                                       Original: note; also °F and inch
    apply <file> [--slug S] [--dry-run]

The first `audit` call builds the index (one pass over all recipes, takes a
while depending on the size of the instance). Every later audit reads from
it. After each writing `apply` the index is discarded and rebuilt.

Never convert an imperial amount in your head - `convert` holds the density
table and the rounding rules and returns the `Original:` note with it.

`apply` writes every applied action to `.mealie.changelog.jsonl` with the
state it overwrote - the only way back, since neither Mealie nor this tool
has an undo. It refuses a `patch_recipe` that would shorten a list field
(Mealie replaces those instead of merging), and lints the plan, fatally for
a non-metric unit. `--dry-run` runs the same checks and says which it had
to skip without a connection. Details in `references/actions.md`.

Context commands return filtered data already. Never load full tables
unfiltered, never build recipe loops by hand - that is what the index is
for.

Environment variables: `MEALIE_URL`, `MEALIE_TOKEN` — `MEALIE_API_TOKEN` (the
`mcp-mealie` name for the token), `MEALIE_BASE_URL` and `MEALIE_API_KEY` are
read as well. If they are unset, the script
reads them from `.mealie.env` and then from `.env` in the working directory.
Any command that finds neither aborts with a hint to `setup`.

The script needs network access to the instance. In a sandboxed environment
the call fails with a connection error even though URL and token are
correct - that is a permission of the environment, not a bug in the
configuration. Say so and let the user allow the call. Never work around it
with a hand-written HTTP script: `mealie_ctx.py` is the only path to the
API, and a second one has neither the order guard nor the dry run. Where
the MCP server is connected, its calls run through the server and are not
affected.

`setup --check` only probes the configuration and is safe to run yourself -
use it once at the start of a session when the connection is unclear. Plain
`setup` prompts for URL and token and must be run by the user, not by you:
ask for it and wait. Never ask for the token in the chat and never write it
into a file yourself.

If the `mcp-mealie` MCP server is connected, use it instead for analysis: it
answers the audit questions server-side, so the index is not built at all,
and it covers what this script deliberately lacks — meal plan, recipe import
from a URL, interactive recipe search. The script keeps the ordered batch:
plans that need `ORDER` or a dry run over the whole set still go through
`actions.json` and `apply`. Read `references/mcp.md` first.

## Output style: caveman

If the `caveman` skill is available, activate it for this workflow. Audits,
plans and reports are long tabular outputs - exactly the case where
compression pays off. Without the skill: answer normally, but tersely -
tables instead of prose, no repetition of what the tool already printed.

**Only the chat output is compressed** - analysis, plan, report, your interim
comments. Two things stay full ${CONTENT_LANG} prose:

- Everything written to Mealie, i.e. everything in `actions.json`. It is
  database content, not chat; see `references/actions.md`.
- Warnings about destructive operations, questions when unsure and the
  approval question. For a merge that rewrites 14 recipes, being unambiguous
  is worth more than a few saved tokens.

## Rules for every mode

Invent nothing: ingredients, amounts and steps are only structured,
translated and corrected, never added or dropped. Existing correct values
stay.

All content in ${CONTENT_LANG}; established culinary terms (sous-vide, roux,
ganache) stay as they are. Metric units.

Mark estimates in the report. When in doubt leave a field empty instead of
guessing.

Search before creating - for foods, units and organizers alike. Check
spelling variants, singular/plural and foreign-language equivalents too.

Mark destructive operations (`merge_*`, `delete_organizer`, `retag_recipe`)
explicitly in the plan, with the number of affected recipes, and point out
that they cannot be undone.

Keep batches small: at most 25 food/unit gaps or 5 duplicate/organizer
groups per run. Recipes have their own rule - one recipe per plan for
ingredients, steps and notes, any number for field-level changes; see
`references/recipes.md`.

On an abort, no speculative repair attempts - report the state reached and
ask.
