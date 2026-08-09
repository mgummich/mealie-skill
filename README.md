# Mealie skill

Clean up a [Mealie](https://mealie.io) instance through its REST API, with
an LLM doing the judgement calls and a script doing every write.

Two frontends, one set of rules:

| | Agent (Claude Code, Antigravity, Cursor, AGENTS.md) | Standalone |
|---|---|---|
| Model | the one your IDE uses | Anthropic API, prompt caching |
| Usage | `/mealie <mode>` | `optimize.py <mode> …` |
| Strength | browser for image and source research, plan as an artifact | batches over many recipes |

Both share: a local recipe index instead of repeated API loops, a plan
before every write, deterministic execution through an ACTIONS list.

> Status: this has not yet been run against a live Mealie instance by anyone
> but its author. Take a backup before the first run.

## Modes

| Mode | does |
|---|---|
| `recipe` | fill empty fields, parse ingredients, translate steps, convert to metric, set an image |
| `foods` | foods: description, plural, label, aliases; merge duplicates |
| `units` | the same for units |
| `organizers` | consolidate categories, tags and tools; retag recipes, delete empty objects |
| `cookbooks` | create and rework cookbooks as filter rules |
| `maintenance` | duplicate recipes, dead images and source URLs, diet tags from ingredients |

## Setup

    export MEALIE_URL=https://mealie.example.org
    export MEALIE_TOKEN=<Profile -> API Tokens>

Take a backup before the first run: Mealie -> Site Settings -> Backups.

Check the endpoint paths, they differ between Mealie versions:

    for p in foods units groups/labels organizers/categories \
             organizers/tags organizers/tools groups/cookbooks; do
      printf '%-26s ' "$p"
      curl -s -o /dev/null -w '%{http_code}\n' \
        -H "Authorization: Bearer $MEALIE_TOKEN" "$MEALIE_URL/api/$p?perPage=1"
    done

Whatever returns 404 goes into the `EP` dictionary in `mealie_ctx.py`
(`/api/categories` instead of `/api/organizers/categories` on older
versions).

Verify these two as well, they are `PUT` or `POST` depending on the version:
`/api/foods/merge` and `/api/units/merge`.

## Content language

The project is in English; the language of your recipe data is a separate
setting. `MEALIE_LANG` (default `English`) decides what the model writes
into descriptions, steps, notes and cookbook texts:

    python3 build.py --install claude-code --lang Deutsch   # baked into the skill
    export MEALIE_LANG=Deutsch                              # standalone

The duplicate heuristic is tuned for German and English data: umlaut
folding, German plural endings (which cover the English "s"), a stop word
list holding both languages. Other languages work, but it finds fewer pairs
there - the model still reviews every group, so nothing is merged blindly.

## Installation

    python3 build.py --install claude-code           # global, ~/.claude/
    python3 build.py --install antigravity           # global, ~/.gemini/config/
    python3 build.py --install claude-code --into <project>
    python3 build.py --install cursor --into <project>
    python3 build.py --install agents-md --into <project>   # Codex, Zed, …

`cursor` and `agents-md` are project-scoped and require `--into`. Existing
files are never overwritten silently (`--force`); an existing `AGENTS.md` is
only updated inside its marked block.

Without `--install`, `python3 build.py` renders every target into `dist/`.

In Claude Code (global or project-scoped) and in Antigravity after a project
install (`--into`):

    /mealie recipe my-recipe
    /mealie foods
    /mealie organizers
    /mealie cookbooks
    /mealie maintenance

A global Antigravity install only places the skill; the `/mealie` workflow
exists there only after an `--into` install in the project.

First run: set the terminal to "Request Review" so you see every `apply`
call. For image and source research, allow the domains of your recipe
sources plus `commons.wikimedia.org`, `pexels.com`, `unsplash.com`.

## Standalone

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

## The tool on its own

`mealie_ctx.py` works without a model:

    python .../mealie_ctx.py index --refresh
    python .../mealie_ctx.py audit foods|units|categories|tags|tools|recipes|links
    python .../mealie_ctx.py ctx recipe <slug>
    python .../mealie_ctx.py ctx foods|units|categories|tags|tools|cookbooks|diet
    python .../mealie_ctx.py usage tag <id>
    python .../mealie_ctx.py apply actions.json --dry-run

## Layout

    skill/                  the single source of truth
      SKILL.md              slim router
      references/*.md       details, read only when needed
      workflow.md           the /mealie procedure
      scripts/mealie_ctx.py every API call
    standalone/
      prompts/common.txt    principles + output style (hand-maintained)
      optimize.py           model call, approval, batch; ACTIONS format
                            and mode rules from skill/references/
    build.py                renders dist/ for the four targets, installs
                            with --install
    test_build.py           python3 test_build.py

## Output style: caveman

The skill uses [caveman](https://github.com/juliusbrussee/caveman) if it is
installed - a compression of the answer style. Audits, plans and reports are
long tabular outputs here, exactly the case where that pays off.

Installation (Antigravity, skill folder analogous to `mealie`):

    cp -r <caveman-repo>/skills/caveman  <workspace>/.agents/skills/

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

    create_label -> merge_food -> merge_unit -> create_food -> create_unit
    -> create_category -> create_tag -> create_tool -> update_food
    -> update_unit -> update_organizer -> retag_recipe -> delete_organizer
    -> create_cookbook -> update_cookbook -> patch_recipe -> set_image

Destructive operations are announced before execution. `--dry-run` shows
every action without writing. The tool never deletes recipes - duplicates
are only presented.

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
opening a PR.

## License

MIT, see [LICENSE](LICENSE).
