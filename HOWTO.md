# How-to

A walkthrough of the whole thing, from an empty terminal to a cleaned-up
Mealie instance. The [README](README.md) says what the project is; this file
shows what a session actually looks like.

Every example below is illustrative — the numbers and slugs come from a
test instance, yours will differ. The commands are real.

- [Before you start](#before-you-start)
- [Five minutes to the first run](#five-minutes-to-the-first-run)
- [The three phases](#the-three-phases)
- [Walkthrough: clean up one recipe](#walkthrough-clean-up-one-recipe)
- [Walkthrough: merge duplicate foods](#walkthrough-merge-duplicate-foods)
- [Walkthrough: consolidate tags](#walkthrough-consolidate-tags)
- [Walkthrough: a cookbook](#walkthrough-a-cookbook)
- [Walkthrough: maintenance](#walkthrough-maintenance)
- [Standalone, without an IDE](#standalone-without-an-ide)
- [With the MCP server](#with-the-mcp-server)
- [Recipes for common situations](#recipes-for-common-situations)
- [When something goes wrong](#when-something-goes-wrong)

## Before you start

**Take a backup.** Mealie → Site Settings → Backups. Merges and deletions
cannot be undone, and this project has not been run against many instances
yet.

You need three things:

| | |
|---|---|
| A Mealie instance | reachable over HTTP from where you run the tool |
| An API token | Mealie → Profile → API Tokens → Create |
| Python 3.9+ | plus `requests` for the standalone frontend |

```bash
export MEALIE_URL=https://mealie.example.org
export MEALIE_TOKEN=eyJhbGciOi…
```

Already running the `mcp-mealie` server? It uses the same `MEALIE_URL` and
its `MEALIE_API_TOKEN` is read as well, so one env file serves both.
`MEALIE_BASE_URL` and `MEALIE_API_KEY`, the names other Mealie MCP servers
use, work too.

Check that the token works and that your Mealie version uses the endpoint
paths the tool expects — they are the ones Mealie 3.22.0 serves, and
cookbooks in particular moved with Mealie 2.0:

```bash
for p in foods units groups/labels organizers/categories \
         organizers/tags organizers/tools households/cookbooks; do
  printf '%-26s ' "$p"
  curl -s -o /dev/null -w '%{http_code}\n' \
    -H "Authorization: Bearer $MEALIE_TOKEN" "$MEALIE_URL/api/$p?perPage=1"
done
```

All `200`: you are set. A `401` means the token is wrong. A `404` means that
path moved in your version — put the working one into the `EP` dictionary in
`skill/scripts/mealie_ctx.py` (older Mealie uses `/api/categories` instead of
`/api/organizers/categories`).

## Five minutes to the first run

```bash
git clone https://github.com/mgummich/mealie-skill
cd mealie-skill
python3 build.py --install claude-code      # ~/.claude, available everywhere
```

Then, in any Claude Code session:

```
/mealie foods
```

That is the whole setup. Other frontends:

```bash
python3 build.py --install antigravity                 # ~/.gemini/config
python3 build.py --install claude-code --into ~/proj   # this project only
python3 build.py --install cursor      --into ~/proj   # needs --into
python3 build.py --install agents-md   --into ~/proj   # Codex, Zed, …
```

Writing recipe content in a language other than English? Bake it in:

```bash
python3 build.py --install claude-code --lang Deutsch
```

That only changes the language of descriptions, steps and notes. The tool,
its output and this documentation stay English.

## The three phases

Every mode runs the same way, and the middle phase is a hard stop:

```
  ANALYSIS                PLAN                     EXECUTION
  ────────                ────                     ─────────
  audit / ctx      →      actions.json      →      apply
  read only               + --dry-run              writes
                          + your approval
                          ▲
                          └── nothing is written before this
```

What that buys you: the model does the judging (is `tomatoes` the same thing
as `tomato`?), the script does the writing. The script enforces an execution
order, refuses to run out of order, and has no operation for deleting a
recipe at all.

Two rules worth knowing before the first session:

- **One kind of task per plan.** Filling empty fields and merging duplicates
  never go into the same `actions.json`.
- **Small batches.** At most 25 gaps or 5 duplicate groups per run. Long
  plans are hard to review, and reviewing is the point.

## Walkthrough: clean up one recipe

```
/mealie recipe tomato-soup
```

**Phase 1 — analysis.** The skill runs `ctx recipe tomato-soup`, which
returns the recipe plus only the foods matching its ingredients. On the very
first call it builds `.mealie_index.json` — one pass over every recipe, slow
once, then reused by everything else.

```
RECIPE tomato-soup
  description   —
  yield         —
  ingredients   8, parsed 2/8
  instructions  1 block, unsplit
  image         placeholder
  tags          —
```

**Phase 2 — the plan.** It proposes what to fill, and writes `actions.json`
next to you in the workspace:

```
PATCH tomato-soup
  description   2 sentences, what the dish is
  yield         4 servings          (from the ingredient amounts)
  ingredients   8/8 parsed          → food + unit + amount
  instructions  1 block → 6 steps
  image         set from the source page
QUESTIONS
  "1 can tomatoes" — 400 g or 800 g? Assumed 400 g, marked as an estimate.
```

Check it yourself before approving:

```bash
python3 skill/scripts/mealie_ctx.py apply actions.json --dry-run --slug tomato-soup
```

`--dry-run` resolves every `$ref`, validates the payloads and checks the
execution order — and writes nothing.

**Phase 3 — execution.** Only after you approve:

```bash
python3 skill/scripts/mealie_ctx.py apply actions.json --slug tomato-soup
```

Then `actions.json` is deleted and you get a report of what changed.

What it will not do: invent an ingredient, drop one, or overwrite a field
you already filled in. Amounts it had to guess are marked as estimates.

## Walkthrough: merge duplicate foods

The destructive one. Read the plan properly.

```
/mealie foods
```

```
FOODS 312 total
  gaps        184 without description · 91 without plural · 203 without label
  unused       27
  duplicates   14 groups
```

Pick one task. Say duplicates:

```
Group: tomato
  KEEP    tomato (3f2a…)      14 recipes, label set
  MERGE   tomatoes (91bc…)     2 recipes   → becomes an alias
  MERGE   Tomato (55de…)       0 recipes   → becomes an alias
  THEN    update_food: aliases += tomatoes, Tomato

  Destructive: rewrites 2 recipes and deletes 2 foods. Cannot be undone.

QUESTIONS
  cherry tomato — kept separate, a different ingredient despite the name.
```

The resulting `actions.json`:

```json
{"actions": [
  {"op": "merge_food", "payload": {"from": "91bc…", "to": "3f2a…"}},
  {"op": "merge_food", "payload": {"from": "55de…", "to": "3f2a…"}},
  {"op": "update_food", "payload": {"id": "3f2a…",
   "aliases": ["tomatoes", "Tomato"]}}
]}
```

Two details that matter:

- The **aliases are not decoration.** Without them the next recipe import
  recreates the same duplicate.
- `aliases` is a list field, and list fields are **replaced, not extended**.
  Existing aliases have to be listed again — the plan does that for you, but
  check it if you had aliases before.

Filling gaps instead is the harmless half of the same mode: descriptions,
plurals, labels and aliases for foods that have none. Same flow, no merge.

`units` works identically — `name`, `pluralName`, `abbreviation`, no label,
no description.

## Walkthrough: consolidate tags

```
/mealie organizers
```

Categories, tags and tools at once. This is where instances rot fastest:
imports create `Vegetarian`, `vegetarian` and `veggie` as three separate
tags.

```
TAGS 96
  unused        31
  near-dupes    12 groups
```

The plan keeps the most-used one, retags the recipes onto it and only then
deletes the empty ones. That order is not a suggestion — the script enforces
`retag_recipe` before `delete_organizer` and aborts before the first write if
a plan gets it backwards.

Unused organizers are proposed for deletion with a reason, never deleted
unasked.

## Walkthrough: a cookbook

```
/mealie cookbooks
```

Mealie cookbooks are filter rules, not folders — you name the categories,
tags and tools it should match, the plan writes them into one filter string,
and the cookbook fills itself. Give it a purpose:

```
/mealie cookbooks
> Quick weeknight cooking, under 30 minutes
```

```
COOKBOOK "Weeknight, under 30"
  filter      tags.name IN ["quick", "weeknight"]
              AND recipeCategory.name IN ["Main"]
  matches     23 recipes today
```

If the matching tags do not exist yet, the plan creates them and retags the
recipes first — one plan, in the right order.

## Walkthrough: maintenance

```
/mealie maintenance
```

Three read-only audits, each with its own follow-up:

| Audit | Finds | What happens |
|---|---|---|
| duplicate recipes | same name, or ≥ 0.6 ingredient overlap | **presented only** — there is no delete-recipe operation, you delete in the UI |
| links | dead source URLs, missing or broken images | new image proposed, source noted |
| diet tags | vegan/vegetarian/gluten-free from parsed ingredients | tagged only when certain |

The duplicate score is a suspicion, not a verdict: two variants of the same
dish score high on purpose. Diet tags are derived only from fully parsed
ingredients and only as exclusions — when in doubt nothing is tagged,
because a wrong "gluten-free" costs more than a missing one.

## Standalone, without an IDE

Same rules, same `actions` format, but the model call is a script and it
batches. Good for "do this to 200 recipes overnight".

```bash
pip install requests
export ANTHROPIC_API_KEY=sk-ant-…

python standalone/optimize.py recipe tomato-soup --dry-run
python standalone/optimize.py recipe --batch --limit 20
python standalone/optimize.py foods gaps --limit 25
python standalone/optimize.py foods duplicates --limit 5
python standalone/optimize.py units duplicates
python standalone/optimize.py organizers tags
python standalone/optimize.py cookbooks --purpose "Quick weeknight cooking"
python standalone/optimize.py maintenance links
```

The approval gate is still there; `--yes` skips it, `--dry-run` shows the
actions and writes nothing.

Cost: the shared rules and the mode rules are sent as **one** cached block,
so the cache is reused per mode, not across modes. Watch the `[usage]` line —
`cache_creation_input_tokens` on the first call, `cache_read_input_tokens`
afterwards. The cache expires five minutes after the last hit, so let a batch
run finish in one go instead of spreading it over the afternoon.

## With the MCP server

If [`mcp-mealie`](https://github.com/mgummich/mcp-mealie) is connected, the
agent frontend uses it as the primary analysis path and **skips the index
entirely** — `library_stats` is one call where the index is one request per
recipe, and an index that is never built never goes stale.

| Question | Without MCP | With MCP |
|---|---|---|
| What exists, how often used? | `audit foods` (builds index) | `library_stats("foods")` |
| Same recipe twice? | `audit recipes` | `find_duplicate_recipes()` |
| Dead links? | `audit links` | `check_recipe_links()` |
| Meal plan, import from URL | — not supported | MCP only |

The three phases do not change. One rule is added: **one write path per
plan** — either every write is an MCP call, or the plan goes through
`actions.json` and `apply`. Never half by each, because a mixed plan has no
order guarantee and no dry run over the whole set.

Details: [`skill/references/mcp.md`](skill/references/mcp.md).

## Recipes for common situations

**Try it without touching an instance.** Everything except HTTP works off an
artificial index:

```bash
MEALIE_INDEX=/tmp/.mealie_index.json \
  python3 skill/scripts/mealie_ctx.py audit recipes
```

**Use the script on its own,** no model involved:

```bash
python3 skill/scripts/mealie_ctx.py index --refresh
python3 skill/scripts/mealie_ctx.py audit foods
python3 skill/scripts/mealie_ctx.py ctx recipe tomato-soup
python3 skill/scripts/mealie_ctx.py usage tag 4c1e…
python3 skill/scripts/mealie_ctx.py apply actions.json --dry-run
```

**The index is stale** after you edited things in the Mealie UI:

```bash
python3 skill/scripts/mealie_ctx.py index --refresh
```

It is discarded automatically after every writing `apply`, so this is only
needed when the changes came from somewhere else.

**Keep an eye on every write** on the first run: set the terminal to
"Request Review" so each `apply` call needs a confirmation. For image and
source research, allow the domains of your recipe sources plus
`commons.wikimedia.org`, `pexels.com` and `unsplash.com`.

## When something goes wrong

| Symptom | Cause | Fix |
|---|---|---|
| `401` on every call | token wrong or expired | new token in Mealie → Profile → API Tokens |
| `404` on one endpoint | Mealie version uses a different path | adjust `EP` in `mealie_ctx.py` |
| merge endpoint fails | `PUT` vs `POST` differs by version | check `/api/foods/merge` and `/api/units/merge` |
| `422` on a cookbook | Mealie refused the filter string | test it as `queryFilter` on `/api/recipes` first |
| `apply` aborts on order | the plan violates the enforced order | let it rewrite the plan — do not patch by hand |
| the same duplicates come back | aliases missing after a merge | add the old names as `aliases` on the target |
| `/mealie` unknown in the IDE | installed globally, workflow needs a project | `build.py --install <target> --into <project>` |
| the agent reads every recipe one by one | it skipped the index | remind it: audits read `.mealie_index.json` |
| `skipped <slug>: 500 from the instance` | Mealie cannot serialize that recipe | open it in the UI and save it again; `audit recipes` lists them under `UNREADABLE` |
| `429` during the index build | the instance rate-limits | nothing to do, the build waits and retries |

An aborted `apply` stops before or between actions and reports how far it
got. Do not guess at repairs — rerun the audit and let the next plan work
from the real state.

Nothing here deletes a recipe. If a plan ever claims it will, something is
wrong: there is no such operation.
