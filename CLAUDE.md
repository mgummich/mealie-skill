# Mealie skill — project rules

A tool for cleaning up a Mealie instance through its REST API. Two
frontends, one shared set of rules: a portable agent skill and a standalone
script for the Anthropic API.

## Architecture

    skill/                  the single source of truth
      SKILL.md              router: pick a mode, shared rules
      references/*.md       details per mode, read only when needed
      workflow.md           the /mealie procedure
      scripts/mealie_ctx.py ALL API access, no model call
    standalone/
      prompts/common.txt    principles + output style (hand-maintained)
      optimize.py           model call, approval, batch
    build.py                renders dist/ for claude-code, antigravity,
                            cursor, agents-md; installs with --install
    test_build.py           python3 test_build.py

`mealie_ctx.py` is the only place with HTTP access to Mealie. `optimize.py`
calls it as a subprocess and derives the ACTIONS format and the mode prompts
from `skill/references/` at runtime (`build.render_standalone`). New
functionality belongs in the script, not in the prompts.

## Non-negotiable

**Three phases: ANALYSIS -> PLAN -> EXECUTION.** Never write without a plan
that was presented and approved. That applies to you as an agent too: when
changing the tool, show what would happen first.

**The execution order in `ORDER` is enforced** and aborts before the first
write. Changing the order means changing `references/actions.md` with it
(standalone takes it from there), otherwise the model's plans hit the guard.

**No recipe deletion.** There is deliberately no operation for it. Duplicate
recipes are presented; deleting happens by hand in the UI.

**A write that changes nothing is not sent.** Every `update_*` and
`patch_recipe` compares against the current record first and prints
`UNCHANGED` instead — the rule set asks that a second run over a clean
corpus produce zero changes, and comparing is what makes that true. A new
writing operation follows suit.

**A field Mealie ignores is worse than one it rejects.** Writes are
validated against the shape of the current API (3.22.0, checked against its
OpenAPI spec); unknown keys are dropped silently, so a payload in an
outdated shape succeeds and does the wrong thing. Where that is possible -
`COOKBOOK_LEGACY`, `_guard_cookbooks` - the plan is refused before the
first write instead.

**Nothing is overwritten without a record.** Every write in `cmd_apply`
reads the state it is about to replace and calls `log_change` before the
next action runs — `.mealie.changelog.jsonl` is the only rollback path.
A new writing operation is not finished until it logs its before-state.
Mealie replaces list fields instead of merging them, so `patch_recipe`
guards against a shortening list (`RECIPE_LISTS`, `_guard_recipe_lists`);
an intended removal carries `"replace": true` on the action.

**`actions.json` is database content, not chat.** Descriptions, steps, notes
and cookbook texts always in full prose, even when the output style is
compressed (caveman). This rule lives in `SKILL.md` and in
`references/actions.md` — change both if it changes.

**Rules live in one place.** `skill/` is the source; `dist/` and the
standalone prompts are rendered. Only `prompts/common.txt` (principles,
output style) is hand-maintained. Several places in the references carry
`<!-- agent-only -->`/`<!-- standalone: … -->` markers for text that has to
differ per context.

## Data, not prose

`skill/data/<lang>/` holds what the model must not retype or misread:
`conversions.json` (density table, rounding, oven and tin sizes),
`lint.json` (note titles, caps, brand and casing vocabularies),
`labels.json` and `units.json` (the fixed vocabularies, emitted as actions
by `seed`) and `house.json` (the template for `.mealie.rules.json`, the
per-instance decisions the rule set wants recorded). The script
reads it as `../data` relative to itself, so `build._copy_data` keeps the
two directories siblings in every target layout. `en` is the fallback for
any language without a pack.

A rule that can be checked mechanically belongs in `lint.json` and
`lint_actions`, not in a reference: a checklist in the prompt costs tokens
every session and is advisory, the same rule in the dry run is free and
enforced. A rule needing judgement stays in `skill/references/`.

## Conventions

English everywhere: output, prompts, comments, docstrings. Docstrings are
Google style (`Args:`/`Returns:`/`Raises:`).

The language of the recipe data is separate from the project language. It
comes from `${CONTENT_LANG}`, substituted by `build.set_language` from
`--lang` or `$MEALIE_LANG` (default `English`). Never hardcode a content
language into a prompt; the placeholder belongs in `skill/` and
`prompts/common.txt`.

Line length 88, no external dependencies at all: an installed skill is a
copied directory with no install step, so HTTP goes through `fetch()` in
`mealie_ctx.py` — a urllib wrapper with the slice of the requests interface
the tool uses. Adding an import outside the standard library breaks every
install. `ruff check .`
enforces it (config in `ruff.toml`, CI runs it); ruff is dev-only, not a
runtime dependency. CI also runs `mypy` on 3.12 — run it before pushing,
`ruff` passing says nothing about it:

    pip install mypy && mypy

New operations need: an entry in `ORDER`, a branch in `cmd_apply` that logs
its before-state, a row in the table in `references/actions.md`, a test in
the dry run.

New audits write nothing and read from the index instead of fetching one by
one.

## Index

`.mealie_index.json` in the working directory, built on the first `audit`,
deleted after every writing `apply`. One pass over all recipes. Every
evaluation (usage counts, duplicates, link rot) reads from it — never build
your own recipe loops.

Teaching `build_index` a new field means raising `INDEX_VERSION` with it.
An index from an older version is rebuilt rather than audited on fields it
does not carry, which would otherwise report zero and look like a clean
result.

## Testing without an instance

An artificial index covers everything except HTTP:

    MEALIE_INDEX=/tmp/.mealie_index.json python3 mealie_ctx.py audit recipes

For `apply` always use `--dry-run` — it writes nothing and still checks the
order, `$ref` resolution and payload structure.
