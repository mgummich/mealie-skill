---
description: Maintain Mealie - recipes, foods, categories/tags/tools, cookbooks, maintenance. Asks for the mode and works in three phases with an approval gate.
---

# Maintain Mealie

Optional argument: the mode (`recipe <slug>`, `foods`, `units`,
`organizers`, `cookbooks`, `maintenance`). If it is missing, ask.

Follow the `mealie` skill. Read **only** the reference for the chosen mode,
not all of them.

If the `caveman` skill is available, activate it now for analysis, plan and
report. Not for content written to Mealie, and not for warnings and
questions - see SKILL.md for the boundary.

## Step 0 - Connection

Run once per session, MCP server connected or not:

    setup --check

It writes nothing and asks nothing, and even in MCP mode a plan that needs
`ORDER` or a dry run falls back to `apply` — a configuration that is only
noticed at that point is noticed at the write. If it reports a missing configuration or
a rejected token, stop and ask the user to run

    python .agents/skills/mealie/scripts/mealie_ctx.py setup

themselves - in Claude Code with a leading `!`, because the command prompts
for URL and token. Do not run it yourself and do not ask for the token in
the chat.

## Step 1 - Mode and reference

    recipe       -> references/recipes.md
    foods        -> references/foods.md
    units        -> references/foods.md
    organizers   -> references/organizers.md
    cookbooks    -> references/cookbooks.md
    maintenance  -> references/maintenance.md

Prefix every script call with:

    python .agents/skills/mealie/scripts/mealie_ctx.py

Read only the output, not the source of the script.

## Step 2 - Analysis

Run the `audit` or `ctx` command from the reference and summarize the
result. On the first call the script builds the recipe index - that takes a
while, once.

Then ask which sub-task and which batch size. Never two kinds of task in one
plan.

## Step 3 - Present the plan and stop

Plan as an artifact, structured as the reference describes. Actions go to
`actions.json` in the workspace root, format see `references/actions.md`.

Check with:

    ... apply actions.json --dry-run

Mark destructive operations (merge, delete, retag) in the plan, with the
number of affected recipes. Then ask explicitly for approval and **stop**.
If changes are requested, adjust plan and `actions.json` and present again.

## Step 4 - Execution

Only after approval:

    ... apply actions.json                # without a recipe
    ... apply actions.json --slug <slug>  # recipe mode

If the script aborts, no speculative repair attempts - report the state
reached and ask.

## Step 5 - Report

Print the report structured as the reference describes, delete
`actions.json` and ask whether the next batch should follow.
