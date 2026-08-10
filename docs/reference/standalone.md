---
title: Standalone
description: Running the same rules against the Anthropic API, without an IDE or an agent harness.
---

# Standalone

`standalone/optimize.py` does what the skill does, without an IDE: it calls
the Anthropic API directly, shows the plan, asks, and hands the approved
actions to the same script.

It has no API access of its own. Context and execution both go through
`mealie_ctx.py` as a subprocess, so every guard, every changelog entry and
every order check applies exactly as it does under an agent.

## Setup

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export MEALIE_URL=https://mealie.example.com
export MEALIE_TOKEN=...        # or a .mealie.env, see "mealie_ctx.py setup"
```

| Variable | Meaning |
|---|---|
| `ANTHROPIC_API_KEY` | required |
| `MODEL` | model id, default `claude-sonnet-4-6` |
| `MEALIE_LANG` | language of the recipe content, default English |
| `MEALIE_CTX` | path to `mealie_ctx.py`, if it is not the one in this checkout |

## Modes

```
optimize.py recipe <slug> [<slug> ...]
optimize.py recipe --batch [--limit 20]
optimize.py foods gaps|duplicates [--limit N]
optimize.py units gaps|duplicates|metric [--limit N]
optimize.py labels [--limit N]
optimize.py extras
optimize.py organizers categories|tags|tools [--limit N]
optimize.py cookbooks --purpose "Quick weeknight cooking"
optimize.py maintenance duplicates|links|diet [--limit N]
```

| Flag | Effect |
|---|---|
| `--dry-run` | show the plan, write nothing |
| `--yes` | execute without asking |
| `--limit N` | cap the work package |
| `--batch` | recipe mode: work through the library |

`--yes` skips the approval question, not the guards. A plan that violates the
execution order or would shorten a list field still aborts before the first
write.

## What one run looks like

1. `mealie_ctx.py` produces the context for the mode.
2. The prompt is assembled: the common principles, the ACTIONS format and the
   mode rules, as one cacheable block.
3. The model answers with a readable plan and exactly one JSON block.
4. Destructive operations are named with the number of affected recipes.
5. You answer the approval question — an explicit `y`.
6. The actions go to a temporary file and `mealie_ctx.py apply` executes it.

Token usage is printed after each call.

## Where the prompts come from

Only `standalone/prompts/common.txt` is hand-maintained — the principles and
the output style. Everything else is **derived from `skill/references/` at
runtime**, through `build.render_standalone`: the ACTIONS format and the mode
rules are the same text the agent reads, with the agent-only passages swapped
for their standalone equivalents and the tool invocation lines removed.

That is what keeps one rule set behind two frontends. A rule changed in
`skill/references/` reaches the standalone prompts on the next run, with no
copy step and no second place to forget.

## When to use which frontend

| | Agent skill | Standalone |
|---|---|---|
| Needs | an IDE with agent support | a Python process and an API key |
| Approval | in the conversation | a `y` at the prompt |
| Good for | judgement calls, one recipe at a time, following a thread | batches, repeatable passes, cron |
| Cost | your IDE subscription | per token, printed per call |

Both write through the same script, so a library maintained by one is not
strange to the other.
