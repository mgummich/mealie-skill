---
title: CLI reference
description: Every command and flag of mealie_ctx.py, the only thing in the project that talks to Mealie.
---

# CLI reference

`skill/scripts/mealie_ctx.py` is the only place with HTTP access to Mealie.
The agent calls it, `standalone/optimize.py` calls it as a subprocess, and
you can call it directly. It has no dependencies at all.

The installed path depends on the target — see
[Build and install](build-and-install.md). Examples here shorten it to
`.../mealie_ctx.py`.

```
setup [--check]
index [--refresh]
ctx <what> [slug] [--search T ...] [--limit N] [--group G] [--full]
audit <what> [--limit N] [--refresh] [--check-urls] [--lang L]
usage <kind> <id>
rules [--init] [--force] [--lang L]
seed <what> [--out FILE] [--all] [--lang L]
convert "<line>" ["<line>" ...] [--fan] [--lang L]
apply <file> [--slug S] [--dry-run] [--lang L]
```

## setup

Checks the connection and stores credentials in `.mealie.env` in the working
directory.

| Flag | Effect |
|---|---|
| `--check` | probe the existing configuration only, ask nothing |

The probe calls `GET /api/users/self`. A 401 means the token is wrong or
expired; a connection error in a sandboxed environment means the sandbox,
not the credentials.

## index

Builds `.mealie_index.json`: one pass over every recipe, one summary record
each.

| Flag | Effect |
|---|---|
| `--refresh` | rebuild even if the file exists |

Every audit reads from the index rather than looping over the API. Recipes
the instance fails to serialise are skipped, counted and named — a single
unserialisable recipe used to cost the whole index.

The index is deleted after every writing `apply`. Rebuild it manually after
changing something in the Mealie UI.

## ctx

Fetches a work package: filtered, slimmed, ready to reason about.

```
ctx recipe <slug> [--search TERM ...] [--full]
ctx foods|units|categories|tags|tools|cookbooks|diet [--limit N] [--group G]
```

| Argument | Meaning |
|---|---|
| `recipe <slug>` | the recipe, slimmed, plus foods matching each `--search` term and the available organizers |
| `--full` | unabridged recipe JSON instead of the slim view |
| `--search T ...` | food candidates per term, for repairing ingredient lines |
| `--limit N` | cap on rows, default 25 |
| `--group G` | for organizer views: the recipes in one duplicate group |
| `foods`, `units` | the table with usage counts |
| `categories`, `tags`, `tools` | the vocabulary with recipe counts |
| `cookbooks` | every cookbook as `id\|name\|hits\|filter\|description`, then the organizers with counts |
| `diet` | recipes with fully parsed ingredients, for deriving diet tags |

## audit

Reads. Writes nothing. Everything comes from the index except the object
lists themselves.

```
audit foods|units|labels|categories|tags|tools|recipes|links|extras
```

| Flag | Effect |
|---|---|
| `--limit N` | how many duplicate groups and examples to print, default 25 |
| `--refresh` | rebuild the index first |
| `--check-urls` | `links` only: actually request every source URL |
| `--lang L` | content language for the vocabularies and the conversion table |

What each one reports is in the guides:
[foods and units](../guides/foods-and-units.md),
[organizers](../guides/organizers.md), [recipes](../guides/recipes.md).

## usage

```
usage food|unit|category|tag|tool <id>
```

The recipes referencing one object, read from the index. Free, and worth
running before every merge or deletion.

## rules

The per-instance decisions the rule set wants recorded once — locale,
category axis, container assumptions, default resolutions for bare food
names.

| Flag | Effect |
|---|---|
| `--init` | write the template to `.mealie.rules.json` |
| `--force` | overwrite an existing file |
| `--lang L` | content language of the template |

The tool reads this file and never changes it. See
[Data packs](data-packs.md).

## seed

Emits the fixed vocabularies as an actions file, skipping what already
exists.

```
seed labels|units|all [--out actions.json] [--all]
```

| Flag | Effect |
|---|---|
| `--out FILE` | write the actions file here instead of stdout |
| `--all` | emit the whole pack without asking the instance what exists |
| `--lang L` | content language of the pack |

## convert

Non-metric amounts to metric, with the `Original:` note that records what was
there. Needs no instance.

```console
$ python3 .../mealie_ctx.py convert "1 cup plain flour" "8 oz butter" "350 F"
120 g plain flour   [note: Original: 1 cup plain flour]
230 g butter   [note: Original: 8 oz butter]
175 °C   [note: Original: 350 F]
```

| Flag | Effect |
|---|---|
| `--fan` | temperatures: also give the fan oven figure |
| `--lang L` | content language of the food names |

Volumes use a per-food density table, so a cup of flour and a cup of water
differ. Temperatures snap to the steps on a real dial.

## apply

The only writing path.

| Flag | Effect |
|---|---|
| `--slug S` | default slug for `patch_recipe` and `set_image`; a slug in the payload wins |
| `--dry-run` | print what would happen, write nothing |
| `--lang L` | content language for the plan lint |

Before the first write it checks: unknown operations, the execution order,
name collisions a rename would cause, list fields a patch would shorten,
cookbook payloads written for an older Mealie, deletions of objects still in
use, and the mechanical rules in `lint.json`. A findings list is printed;
anything at `ERROR` stops the run.

`--dry-run` runs the same checks. Without configured credentials it says
which of them it could not perform rather than passing over them in silence.

## Environment

| Variable | Meaning |
|---|---|
| `MEALIE_URL` | instance URL — `MEALIE_BASE_URL` is read too |
| `MEALIE_TOKEN` | API token — `MEALIE_API_TOKEN` (the `mcp-mealie` name) and `MEALIE_API_KEY` are read too |
| `MEALIE_ENV` | path of the env file, default `.mealie.env` |
| `MEALIE_INDEX` | path of the index, default `.mealie_index.json` |
| `MEALIE_CHANGELOG` | path of the changelog, default `.mealie.changelog.jsonl` |
| `MEALIE_RULES` | path of the house rules, default `.mealie.rules.json` |
| `MEALIE_LANG` | default content language at build time |

Precedence per variable: environment → `.mealie.env` → `.env`. The canonical
names win when both are set. Details in [State files](state-files.md).

## Rate limits and failures

A 429 is retried up to five times, honouring `Retry-After` and otherwise
backing off. Every other status is left to the caller: a failing write aborts
the run, and the actions already applied stay applied, on record.

## Testing without an instance

Point the index at a hand-written file — every audit reads from it, so
everything except HTTP can be exercised offline:

```bash
MEALIE_INDEX=/tmp/.mealie_index.json python3 mealie_ctx.py audit recipes
```
