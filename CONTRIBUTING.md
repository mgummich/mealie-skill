# Contributing

Thanks for looking. This is a small project with a few load-bearing rules —
most of a review will be about these.

## The one rule that matters

`skill/` is the single source of truth. `dist/` and the standalone prompts
are **rendered** from it. If you fix wording in a rendered file, your change
is gone on the next build. Edit `skill/` instead.

The only hand-maintained prompt file is `standalone/prompts/common.txt`
(principles and output style).

## Before opening a pull request

    python3 test_build.py        # plain asserts, no framework
    python3 build.py             # renders all four targets into dist/
    ruff check .                 # config in ruff.toml, or: uvx ruff check .
    mypy                         # config in mypy.ini, needs types-requests

All four have to pass. CI runs the same commands plus a dry run of the
ACTIONS guard.

Or let git run them for you:

    pip install pre-commit && pre-commit install   # or: uvx pre-commit install

The hooks are ruff, mypy, the tests, whitespace fixers and a guard that
refuses to commit `.env` or `.mealie.env` — both hold the API token in clear
text. All of it is dev-only; nothing is added to the runtime dependencies.

## Conventions

- English everywhere: output, prompts, comments, docstrings.
- Docstrings in Google style (`Args:`/`Returns:`/`Raises:`).
- Line length 88.
- No dependencies beyond `requests`.
- Never hardcode a content language. Use the `${CONTENT_LANG}` placeholder;
  it is substituted from `--lang` or `$MEALIE_LANG`.

## Adding an operation

A new write operation needs all four of these, or the plans the model
produces will hit the order guard:

1. an entry in `ORDER` in `skill/scripts/mealie_ctx.py`, at the right
   position — create before reference, retag before delete
2. a branch in `cmd_apply`
3. a row in the table in `skill/references/actions.md`
4. a check with `apply --dry-run`

## Adding an audit

Audits write nothing and read from `.mealie_index.json` rather than fetching
recipes one by one. If you need a field the index does not have, extend
`build_index` — do not add a second pass over the API.

## Testing without a Mealie instance

An artificial index covers everything except HTTP:

    MEALIE_INDEX=/tmp/.mealie_index.json \
      python3 skill/scripts/mealie_ctx.py audit recipes

For `apply` always use `--dry-run`. It writes nothing and still checks
order, `$ref` resolution and payload structure.

## Things that are deliberate, not oversights

- There is no operation for deleting recipes. Duplicates are presented, a
  human deletes them in the UI.
- The duplicate heuristic is coarse and tuned for German and English data.
  It is meant to produce candidates for the model to review, not verdicts.
- Common rules and mode rules form one prompt cache block. Splitting them
  looks cleaner but drops the common part below the 1024 token minimum.

## Reporting a bug

Endpoint paths differ between Mealie versions — please include your Mealie
version and the output of the endpoint check in the README. For anything
touching writes, the output of `apply --dry-run` is the most useful thing
you can attach.
