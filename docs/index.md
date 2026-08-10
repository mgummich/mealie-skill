---
title: Documentation
description: Guides, reference, decisions and best practices for the Mealie skill.
---

# Documentation

This tool cleans up a Mealie instance through its REST API. A language model
makes the judgement calls — is `Tomate` and `Tomaten` the same food, does
this tag carry two concepts — and a script does every write, in a fixed
order, with a record of what it overwrote.

These pages cover **using and extending the tool**. What a well-kept Mealie
database looks like is a separate body of work: the
[rule set]({{ site.baseurl }}/rules/), in German and English. Nothing here
restates it — where a question is about the data rather than the tool, the
answer links there.

## Where to start

| You want to | Read |
|---|---|
| Get it running and see it work once | [First run](guides/first-run.md) |
| Understand what it will and will not do | [Overview]({{ site.baseurl }}/) · [Decisions](decisions/) |
| Clean up an existing library | [Foods and units](guides/foods-and-units.md), then [organizers](guides/organizers.md), then [recipes](guides/recipes.md) |
| Build cookbooks that do not silently empty | [Cookbooks](guides/cookbooks.md) |
| Undo something | [Recovering a run](guides/recovering-a-run.md) |
| Look up a command or a payload | [CLI](reference/cli.md) · [Actions format](reference/actions.md) |
| Run it without an IDE | [Standalone](reference/standalone.md) |
| Change the tool | [Development](development.md) · [Decisions](decisions/) |
| Keep the instance itself healthy | [Mealie best practices](best-practices.md) |

## The four layers

The repository is one rule set with several frontends. Knowing which layer
you are in saves reading the wrong file.

| Layer | Lives in | Read by |
|---|---|---|
| The rule set | `rules/` | people; the source the references were written from |
| The skill | `skill/SKILL.md`, `skill/references/` | the agent, one mode at a time |
| The tool | `skill/scripts/mealie_ctx.py` | nothing else touches the API |
| The frontends | `build.py` targets, `standalone/optimize.py` | your IDE, or a bare Python process |

`skill/` is the single source. `dist/` and the standalone prompts are
rendered from it by `build.py` — editing them is editing a build artefact.

## The one thing to know before writing

Every run is three phases: **analysis → plan → execution**, and the plan is
shown before anything is written. `apply` refuses a plan that violates the
execution order, one that would shorten a list field, one that deletes a
food some recipe still uses, and one written against an older Mealie API.
Everything it does write lands in `.mealie.changelog.jsonl` with the state
it replaced, before the next action runs.

There is deliberately no operation for deleting a recipe. See
[decision 0002](decisions/0002-no-recipe-deletion.md).

## Guides

- [First run](guides/first-run.md) — install, token, backup, first audit, first plan
- [Foods and units](guides/foods-and-units.md) — the parsing headline number, merges, aliases, metric conversion
- [Organizers](guides/organizers.md) — categories, tags, tools and the vocabulary they form
- [Recipes](guides/recipes.md) — ingredient lines, fields, images, sources
- [Cookbooks](guides/cookbooks.md) — filter strings, hit counts, repair after a cleanup
- [Recovering a run](guides/recovering-a-run.md) — the changelog, an aborted run, a merge that went wrong

## Reference

- [CLI](reference/cli.md) — every command and flag of `mealie_ctx.py`
- [Actions format](reference/actions.md) — the JSON the model produces and `apply` executes
- [State files](reference/state-files.md) — index, changelog, house rules, env
- [Data packs](reference/data-packs.md) — conversions, lint, labels, units, house template
- [Mealie API](reference/mealie-api.md) — which endpoints are used, and which Mealie versions serve them
- [Build and install](reference/build-and-install.md) — the four targets and what each writes
- [Standalone](reference/standalone.md) — `optimize.py` against the Anthropic API

## Decisions

[Why the tool is shaped this way](decisions/) — three phases, no recipe
deletion, guards that refuse rather than warn, an index instead of loops,
data instead of prose.
