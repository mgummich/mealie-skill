---
title: First run
description: From an empty checkout to a first plan applied, with the checks that make the first run reversible.
---

# First run

Twenty minutes, of which the tool spends most of them reading your recipes
once. Nothing is written until you approve a plan.

## 1. Take a backup

Mealie → Site Settings → Backups → *Create Backup*. Download it.

This is not ceremony. The tool records every write in a changelog and can
put single fields back, but a backup is the only thing that survives a
mistake it never saw — an import you ran in parallel, a container that lost
its volume. Do it before the first run and before any run that merges or
deletes.

## 2. Get a token

Mealie → Profile → API Tokens → *Create*. Copy it once; Mealie does not show
it again.

The token carries your own permissions. If you keep a separate admin user,
create the token as the user whose recipes you are cleaning — households and
groups scope what the API returns, and a token from the wrong user quietly
sees a different corpus.

## 3. Install the skill

Pick the frontend you actually use. `build.py` renders and installs;
[Build and install](../reference/build-and-install.md) has the full matrix.

```bash
git clone https://github.com/mgummich/mealie-skill
cd mealie-skill

python3 build.py --install claude-code                 # global, ~/.claude
python3 build.py --install cursor --into ~/my-project  # per project
```

If your recipes are not in English, bake that in — it decides the language
the model writes descriptions and steps in, not the language of the
interface:

```bash
python3 build.py --install claude-code --lang Deutsch
```

## 4. Store the credentials

```bash
python3 ~/.claude/skills/mealie/scripts/mealie_ctx.py setup
```

It asks for URL and token, checks them against `/api/users/self` and writes
`.mealie.env` in the working directory. Already running `mcp-mealie` or
another Mealie MCP server? Their variable names are read as well, so one env
file serves both — see [State files](../reference/state-files.md).

Check without being asked anything:

```bash
python3 .../mealie_ctx.py setup --check
```

## 5. Build the index

```bash
python3 .../mealie_ctx.py index
```

One pass over every recipe — a few minutes for a large library. Every audit
reads from `.mealie_index.json` afterwards instead of fetching recipes one
by one. A recipe the instance fails to serialise is skipped and named rather
than killing the run.

## 6. Look before you plan

Start with the recipe audit. It is the one that tells you how much of the
library is machine-readable at all:

```console
$ python3 .../mealie_ctx.py audit recipes
2 recipes, 0 name duplicates
LINES WITH A LINKED FOOD: 10 (59 %) of 17 – the headline number, target above 95 %
AMOUNT STRANDED IN THE NOTE: 1 recipes – red-lentil-curry
LINES WITHOUT originalText: 1 recipes – fill it from the display value before repairing them
LINES CARRYING Original:: 2
NOTE TITLES OUTSIDE THE VOCABULARY: Original
ONE SINGLE STEP: 0 · OVER 15 STEPS: 0
COOKED (lastMade set): 1 · RATED: 1 – work these first, they are the ones in use
```

The percentage is the number to watch. Below roughly 95 %, ingredient-level
features — shopping lists, diet tags, duplicate detection — work on a
fraction of your data and quietly under-report.

Then the two that shape everything downstream:

```bash
python3 .../mealie_ctx.py audit foods
python3 .../mealie_ctx.py audit units
```

## 7. Record the house rules

```bash
python3 .../mealie_ctx.py rules --init
```

Writes `.mealie.rules.json` — the decisions the rule set says have to be made
once and held to: locale, what your categories are an axis of, what a `tin`
weighs, whether `pepper` means black ground pepper. The tool never changes
this file. Go through it once; every later run reads it and stops guessing.

## 8. First plan

In your IDE:

```
/mealie foods
```

The agent runs the analysis, then shows a plan. Read it. It should name
every merge, every rename and what it will not touch. Approve, and it writes
`actions.json` and applies it.

Doing it by hand is the same three phases:

```bash
python3 .../mealie_ctx.py apply actions.json --dry-run   # prints, writes nothing
python3 .../mealie_ctx.py apply actions.json
```

`--dry-run` is not a formality: it checks the execution order, resolves the
`$ref` placeholders, refuses a payload written for an older Mealie API and
catches a patch that would shorten a list field. Run it on every plan you did
not write yourself.

## 9. Refresh the index

A writing `apply` deletes the index, because everything it measured has just
changed. The next audit rebuilds it. If you changed something in the Mealie
UI instead, force it:

```bash
python3 .../mealie_ctx.py index --refresh
```

## Where to go next

The dependency order matters — cookbooks filter on tags, recipes point at
foods. Work top down: [foods and units](foods-and-units.md) →
[organizers](organizers.md) → [recipes](recipes.md) →
[cookbooks](cookbooks.md). The [rule set]({{ site.baseurl }}/rules/) explains
why in more detail than any tool documentation should.
