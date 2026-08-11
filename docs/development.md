---
title: Development
description: How the pieces fit, where a change belongs, and what has to be true before it ships.
---

# Development

The contribution checklist — the commands to run, the conventions, the four
places a new operation has to be registered — is
[CONTRIBUTING.md](https://github.com/mgummich/mealie-skill/blob/main/CONTRIBUTING.md).
This page is the map you want before you open a file.

## The pieces

```
rules/                  the rule set, DE and EN — prose for people, upstream of everything
skill/                  the single source
  SKILL.md              router: pick a mode, shared rules
  references/*.md       one file per mode, read only when needed
  workflow.md           the /mealie procedure
  data/<lang>/*.json    conversions, lint thresholds, fixed vocabularies, house template
  scripts/mealie_ctx.py ALL API access, no model call
standalone/
  prompts/common.txt    principles and output style — the only hand-maintained prompt
  optimize.py           model call, approval, batch
build.py                renders dist/ for four targets; installs with --install
test_build.py           the whole suite: python3 test_build.py
```

Two invariants hold the design together:

- **`mealie_ctx.py` is the only thing that speaks HTTP.** `optimize.py` calls
  it as a subprocess. New functionality belongs in the script, not in a
  prompt — a prompt cannot be tested and cannot refuse.
- **`skill/` is the source; everything else is rendered.**
  [Decision 0003](decisions/0003-one-source-many-frontends.md).

## Where a change belongs

| Change | Goes in |
|---|---|
| A new write operation | `ORDER`, a branch in `cmd_apply`, the table in `references/actions.md`, a dry-run test |
| A new audit | `cmd_audit`, reading from the index — never a second pass over the API |
| A new index field | `build_index` **and** `INDEX_VERSION` |
| A mechanically checkable rule | `data/<lang>/lint.json` and `lint_actions` |
| A rule needing judgement | `skill/references/<mode>.md` |
| A number the model must not recall | `data/<lang>/conversions.json` |
| Anything about what good data looks like | `rules/`, then the reference that summarises it |
| A new agent format | `TARGETS` and `MAPPINGS` in `build.py`, plus a render test |

## The obligations a write carries

A new writing operation is not finished until all four are true:

1. It appears in `ORDER` at the right position — create before reference,
   retag before delete.
2. It reads the state it is about to replace and calls `log_change` before
   the next action runs. [Decision 0007](decisions/0007-changelog-before-write.md).
3. It compares against the current record and prints `UNCHANGED` instead of
   sending a write that changes nothing. The rule set asks that a second run
   over a clean corpus produce zero changes; comparing is what makes that
   true.
4. Anything it can get silently wrong is refused before the first write, not
   warned about. [Decision 0005](decisions/0005-guards-refuse-not-warn.md).

## Testing

`test_build.py` is plain asserts, no framework, no instance:

```bash
python3 test_build.py
```

It covers the renderer (markers per target, language substitution, the
`AGENTS.md` size budget) and the tool (order enforcement, `$ref` resolution,
the list-shortening guard, merge verification, the cookbook guard, changelog
contents) by substituting `mreq` with a fake instance.

Two techniques worth knowing:

**A hand-written index.** Every audit reads from the index, so everything
except HTTP can be exercised offline:

```bash
MEALIE_INDEX=/tmp/.mealie_index.json python3 skill/scripts/mealie_ctx.py audit recipes
```

**`apply --dry-run`.** Writes nothing and still checks order, `$ref`
resolution, payload structure and every guard that does not need the
instance. Use it on any plan you did not write.

## Checking the Mealie API

Before assuming an endpoint or a field, read the specification:

```bash
curl -s https://demo.mealie.io/openapi.json | python3 -m json.tool | less
```

The demo runs `nightly`. For a released version, read the route and schema
sources at the tag — `mealie/routes/`, `mealie/schema/` — because Mealie does
not commit a generated spec. Both matter: the routes give the paths, the
schemas give which fields a write actually accepts.

Remember that Mealie **ignores unknown fields rather than rejecting them**.
An endpoint that returns 200 proves the request was accepted, not that it did
what you meant. [Decision 0008](decisions/0008-target-current-mealie.md).

## Style

English everywhere — output, prompts, comments, docstrings. Google-style
docstrings. Line length 88. No dependencies at all — the skill is a
copied directory with no install step, so `requests` is not available to it
and the standard library is; `ruff` and `mypy` are dev-only. The content language of recipe data is never hardcoded:
that is `${CONTENT_LANG}`, substituted at build time.

Comments explain why, not what. Most of the comments in `mealie_ctx.py` are
there because someone would otherwise remove the line — the pagination
follow-up, the `sanitize` filter, the read-before-write in every branch of
`cmd_apply`.

## Documentation

These pages are Jekyll markdown under `docs/`, published by the Pages
workflow along with `rules/` and the root README and HOWTO. A change to any of
them rebuilds the site.

They cover using and extending the tool. Anything about what a clean database
looks like belongs in `rules/` and is linked, never restated — two documents
saying the same thing in different words is how a rule set stops being one.
