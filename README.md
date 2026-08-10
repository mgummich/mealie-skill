<h1 align="center">Mealie skill</h1>

<p align="center">
  Clean up a <a href="https://mealie.io">Mealie</a> instance through its REST
  API — an LLM makes the judgement calls, a script does every write.
</p>

<p align="center">
  <a href="https://github.com/mgummich/mealie-skill/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/mgummich/mealie-skill/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://mgummich.github.io/mealie-skill/"><img alt="Docs" src="https://img.shields.io/badge/docs-github%20pages-blue.svg"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python 3.9+" src="https://img.shields.io/badge/python-3.9%2B-blue.svg">
  <img alt="Dependencies: requests" src="https://img.shields.io/badge/dependencies-requests-lightgrey.svg">
</p>

> [!WARNING]
> This has not yet been run against a live Mealie instance by anyone but its
> author. **Take a backup before the first run** (Mealie → Site Settings →
> Backups).

Two frontends, one set of rules:

| | Agent (Claude Code, Antigravity, Cursor, AGENTS.md) | Standalone |
|---|---|---|
| Model | the one your IDE uses | Anthropic API, prompt caching |
| Usage | `/mealie <mode>` | `optimize.py <mode> …` |
| Strength | browser for image and source research, plan as an artifact | batches over many recipes |

Both share: a local recipe index instead of repeated API loops, a plan
before every write, deterministic execution through an ACTIONS list.

New here? [**HOWTO.md**](HOWTO.md) walks through a full session per mode,
with examples. Both files are also served as a site:
[mgummich.github.io/mealie-skill](https://mgummich.github.io/mealie-skill/).

## Contents

- [Modes](#modes) · [Quickstart](#quickstart) · [Setup](#setup)
- [MCP server](#mcp-server-optional) · [Content language](#content-language)
- [Installation](#installation) · [Standalone](#standalone)
- [The tool on its own](#the-tool-on-its-own) · [Layout](#layout)
- [Output style: caveman](#output-style-caveman) · [Token budget](#token-budget)
- [Safety nets](#safety-nets) · [Heuristics and their limits](#heuristics-and-their-limits)
- [Contributing](#contributing) · [Security](#security) · [License](#license)

## Modes

| Mode | does |
|---|---|
| `recipe` | fill empty fields, parse ingredients, translate steps, convert to metric, set an image |
| `foods` | matching cascade, gaps, merge duplicates, split ambiguous foods |
| `units` | the closed metric set, abbreviation collisions, converting non-metric amounts away |
| `labels` | the 29 shopping-list labels, their zone palette and the shop route |
| `organizers` | consolidate categories, tags and tools; retag recipes, delete empty objects |
| `cookbooks` | create and rework cookbooks as filter rules |
| `maintenance` | duplicate recipes, broken ingredient lines, dead links, diet tags |
| `extras` | the free key-value field on recipes, foods and units |

The rules behind the modes live in [`rules/`](rules/) in two independent
language versions; `skill/references/` is their compressed working form and
`skill/data/` their machine form.

## Quickstart

```bash
export MEALIE_URL=https://mealie.example.org
export MEALIE_TOKEN=<Profile -> API Tokens>

python3 build.py --install claude-code   # then: /mealie recipe my-recipe
```

Prefer it without an IDE? Jump to [Standalone](#standalone). Want to look
around before anything writes? [The tool on its own](#the-tool-on-its-own)
runs without a model.

## Setup

Either export the two variables:

```bash
export MEALIE_URL=https://mealie.example.org
export MEALIE_TOKEN=<Profile -> API Tokens>
```

Or let the script ask, probe the instance and store the answers:

```bash
python3 skill/scripts/mealie_ctx.py setup          # prompts, then offers
                                                   # to write .mealie.env
python3 skill/scripts/mealie_ctx.py setup --check  # probe only, asks nothing
```

`.mealie.env` lives in the working directory, holds the token in clear text,
gets mode 600 and is in `.gitignore`. A plain `.env` in the same directory is
read as well (never written), so an existing one works without any copying.

Precedence: environment → `.mealie.env` → `.env`, per variable. Another path
for the first file: `MEALIE_ENV=/path/to/env`.

`MEALIE_API_TOKEN` works too — the name the `mcp-mealie` server uses for the
token, and it shares `MEALIE_URL`, so one env file serves both.
`MEALIE_BASE_URL` and `MEALIE_API_KEY` are read as well, for the other Mealie
MCP servers. The canonical names win when both are set.

Take a backup before the first run: Mealie → Site Settings → Backups.

Check the endpoint paths, they differ between Mealie versions:

```bash
for p in foods units groups/labels organizers/categories \
         organizers/tags organizers/tools groups/cookbooks; do
  printf '%-26s ' "$p"
  curl -s -o /dev/null -w '%{http_code}\n' \
    -H "Authorization: Bearer $MEALIE_TOKEN" "$MEALIE_URL/api/$p?perPage=1"
done
```

Whatever returns 404 goes into the `EP` dictionary in `mealie_ctx.py`
(`/api/categories` instead of `/api/organizers/categories` on older
versions).

Verify these two as well, they are `PUT` or `POST` depending on the version:
`/api/foods/merge` and `/api/units/merge`.

## MCP server (optional)

If [`mcp-mealie`](https://github.com/mgummich/mcp-mealie) is connected, the
agent frontend uses it as the primary analysis path: `library_stats`,
`find_duplicate_recipes` and `check_recipe_links` answer the survey questions
server-side, so the local index is never built. It also has the meal plan and
recipe-import operations that `mealie_ctx.py` deliberately lacks.

The three phases stay: ANALYSIS → PLAN → EXECUTION. Per plan there is exactly
one write path — either every write is an MCP call or the plan goes through
`actions.json` and `apply`, never half by each. Details in
[`skill/references/mcp.md`](skill/references/mcp.md).

Without the server nothing changes; `mealie_ctx.py` covers every mode on its
own. The standalone frontend never uses MCP.

## Content language

The project is in English; the language of your recipe data is a separate
setting. `MEALIE_LANG` (default `English`) decides what the model writes
into descriptions, steps, notes and cookbook texts:

```bash
python3 build.py --install claude-code --lang Deutsch   # baked into the skill
export MEALIE_LANG=Deutsch                              # standalone
```

The duplicate heuristic is tuned for German and English data: umlaut
folding, German plural endings (which cover the English "s"), a stop word
list holding both languages. Other languages work, but it finds fewer pairs
there - the model still reviews every group, so nothing is merged blindly.

## Installation

```bash
python3 build.py --install claude-code           # global, ~/.claude/
python3 build.py --install antigravity           # global, ~/.gemini/config/
python3 build.py --install claude-code --into <project>
python3 build.py --install cursor --into <project>
python3 build.py --install agents-md --into <project>   # Codex, Zed, …
```

`cursor` and `agents-md` are project-scoped and require `--into`. Existing
files are never overwritten silently (`--force`); an existing `AGENTS.md` is
only updated inside its marked block. That block is a pointer at
`mealie/router.md` rather than the router itself — `AGENTS.md` has no
on-demand loading, so everything in it is paid for in every session.

Without `--install`, `python3 build.py` renders every target into `dist/`.

In Claude Code (global or project-scoped) and in Antigravity after a project
install (`--into`):

```
/mealie recipe my-recipe
/mealie foods
/mealie organizers
/mealie cookbooks
/mealie maintenance
```

A global Antigravity install only places the skill; the `/mealie` workflow
exists there only after an `--into` install in the project.

First run: set the terminal to "Request Review" so you see every `apply`
call. For image and source research, allow the domains of your recipe
sources plus `commons.wikimedia.org`, `pexels.com`, `unsplash.com`.

## Standalone

```bash
export ANTHROPIC_API_KEY=sk-ant-…
pip install requests

python standalone/optimize.py recipe my-recipe --dry-run
python standalone/optimize.py recipe --batch --limit 20
python standalone/optimize.py foods gaps --limit 25
python standalone/optimize.py foods duplicates --limit 5
python standalone/optimize.py units duplicates
python standalone/optimize.py organizers tags
python standalone/optimize.py cookbooks --purpose "Quick weeknight cooking"
python standalone/optimize.py maintenance links
```

## The tool on its own

`mealie_ctx.py` works without a model:

```bash
python .../mealie_ctx.py index --refresh
python .../mealie_ctx.py audit foods|units|labels|categories|tags|tools|recipes|links|extras
python .../mealie_ctx.py ctx recipe <slug>
python .../mealie_ctx.py ctx foods|units|categories|tags|tools|cookbooks|diet
python .../mealie_ctx.py usage tag <id>
python .../mealie_ctx.py convert "1 cup plain flour" "350 F"
python .../mealie_ctx.py rules --init
python .../mealie_ctx.py seed labels|units|all --out actions.json
python .../mealie_ctx.py apply actions.json --dry-run
```

## Layout

```
rules/                  the rule set, DE and EN, the upstream record
skill/                  the single source of truth
  SKILL.md              slim router
  references/*.md       details, read only when needed
  data/<lang>/          conversion, lint, seed and house-rule tables
  workflow.md           the /mealie procedure
  scripts/mealie_ctx.py every API call
standalone/
  prompts/common.txt    principles + output style (hand-maintained)
  optimize.py           model call, approval, batch; ACTIONS format
                        and mode rules from skill/references/
build.py                renders dist/ for the four targets, installs
                        with --install
test_build.py           python3 test_build.py
```

## Output style: caveman

The skill uses [caveman](https://github.com/juliusbrussee/caveman) if it is
installed - a compression of the answer style. Audits, plans and reports are
long tabular outputs here, exactly the case where that pays off.

Installation (Antigravity, skill folder analogous to `mealie`):

```bash
cp -r <caveman-repo>/skills/caveman  <workspace>/.agents/skills/
```

**The boundary matters more than the activation.** Only the chat output is
compressed. Everything that travels into the database through `actions.json`
- recipe and food descriptions, preparation steps, notes, cookbook
descriptions - stays full prose. Someone reads those texts in the Mealie UI
later, without knowing this workflow existed. The rule sits in both
`SKILL.md` and `references/actions.md`, because that is exactly where it
would be violated.

Warnings about destructive operations, clarifying questions and the approval
question stay in whole sentences as well. For a merge that rewrites 14
recipes, being unambiguous is worth more than a few saved tokens - caveman
has its own clarity rule for that.

Without the skill nothing changes: the references ask for terse tabular
output anyway. Standalone has the same rule built into `prompts/common.txt`.

Honest about the savings: caveman only lowers **output** tokens and brings
about 1-1.5 k input tokens per turn with it. For the long plans and reports
of this workflow the maths works out; for short one-off queries it can turn
negative.

## Token budget

Three measures, in order of impact:

**Reference files instead of one large SKILL.md.** The router is about 700
tokens; the mode details (900-1300 each) are read only once the mode is
chosen. Before that, every Mealie request paid for the full rule set.

**Local recipe index.** `audit` and `usage` read `.mealie_index.json`
instead of fetching every recipe individually each time. The index is built
on the first audit and discarded after every writing `apply`.

**Targeted search instead of full tables.** `ctx recipe` only searches for
the foods matching the ingredients of that recipe. With a few hundred foods
that is the difference between 500 and 20,000 tokens of context.

Standalone adds prompt caching. Common rules and mode rules form **one**
block, because the common part alone is below the 1024 token minimum. The
cache is therefore reused per mode, not across modes. Check the `[usage]`
line: `cache_creation_input_tokens` first, `cache_read_input_tokens`
afterwards. The cache lives five minutes from the last hit - let batch runs
finish in one go.

## Safety nets

The execution order is enforced and aborts before the first write if the
ACTIONS violate it:

```
create_label -> merge_food -> merge_unit -> create_food -> create_unit
-> create_category -> create_tag -> create_tool -> update_food
-> update_unit -> update_organizer -> retag_recipe -> delete_organizer
-> create_cookbook -> update_cookbook -> patch_recipe -> set_image
```

Destructive operations are announced before execution. `--dry-run` shows
every action without writing. The tool never deletes recipes - duplicates
are only presented.

Four more, because Mealie has no undo:

- **Nothing is overwritten unrecorded.** Every applied action goes to
  `.mealie.changelog.jsonl` with the state it replaced, written before the
  next action runs. Merges and deletions record the whole object.
- **A shortening list is refused.** Mealie replaces `recipeIngredient`,
  `notes` and the rest instead of merging them, so a patch carrying fewer
  lines than the recipe holds would delete the difference. It aborts unless
  the action says `"replace": true`.
- **Merges are verified.** The affected recipes are read back afterwards;
  if any still points at the merged-away object, the run stops.
- **Plans are linted** against the rules that can be checked mechanically -
  a new food without a label or aliases, a tag carrying two concepts, a
  note title outside the vocabulary. Creating a non-metric unit is refused
  outright.

## Heuristics and their limits

**Duplicates** go through a normal form (lowercased, umlauts folded, common
plural endings removed). It finds tomato/tomatoes and Kürbis/Kuerbis; it
correctly does not group butter/buttermilk or tomato/cherry tomato. It
misses irregular forms (mouse/mice) and true synonyms (scallion/spring
onion) - the model adds those while reviewing the groups.

**Duplicate recipes** via identical names plus Jaccard similarity of the
ingredients from 0.6 up. A high value is a suspicion, not proof: variants of
the same dish naturally score high.

**Diet tags** are derived only from fully parsed ingredients, and only as
exclusion criteria. When unsure, nothing is tagged - a wrong "gluten-free"
costs more than a missing one.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: `skill/` is the
source, everything else is rendered; run `python3 test_build.py` before
opening a PR. By taking part you agree to the
[Code of Conduct](CODE_OF_CONDUCT.md).

Bug reports and feature requests have
[issue templates](.github/ISSUE_TEMPLATE) — for anything touching writes,
attach the output of `apply --dry-run`.

## Security

Please do not open a public issue for a vulnerability. See
[SECURITY.md](SECURITY.md) for the reporting path and for what the tool does
with your Mealie token.

## License

MIT, see [LICENSE](LICENSE).
