---
title: "0003 — One rule set, rendered into every frontend"
description: skill/ is the source; dist/ and the standalone prompts are build artefacts.
---

# 0003 — One rule set, rendered into every frontend

**Status:** accepted · **Recorded:** 2026-08-10

## Context

The same rules have to reach four agent formats and a bare API script. Each
wants a different layout — a skill directory, per-mode Cursor rules, a marked
block in `AGENTS.md`, a system prompt — and some passages have to differ:
an agent can run `ctx cookbooks`, a prompt in a single API call cannot.

Copying the text into five places means it stops being the same text within a
month, and the drift is silent: every copy is individually plausible.

## Decision

`skill/` is the single source. `build.py` renders every target from it.
`dist/` is a build artefact. The standalone prompts are derived from
`skill/references/` at runtime, not maintained separately — only
`standalone/prompts/common.txt`, the principles and the output style, is
hand-written.

Where the text genuinely must differ, the difference lives in the source as a
marker:

```markdown
<!-- agent-only -->
Run `ctx cookbooks` and read the hit counts.
<!-- standalone: The cookbook list is in the context block above. -->
```

## Consequences

- Editing `dist/` is editing something the next build overwrites.
- A rule changed in `skill/references/` reaches the standalone prompts on the
  next run, with no copy step.
- `build.py` has to know a little about each target's layout. That knowledge
  is in one file, tested by `test_build.py`.
- The reverse also binds: the execution order lives in the script *and* in
  `references/actions.md`, and changing one without the other means every
  plan the model writes hits the guard.

## The rules themselves are upstream of all of it

`rules/` — the German and English rule sets — is the body of work the
references were written from. It is prose for people, not for a renderer, and
it is not built into anything. When the two disagree, `rules/` is the older,
more considered text and usually right.

## Alternatives rejected

**Maintain each frontend by hand.** Tried implicitly by every project that
supports more than one agent format; it ends in four different rule sets with
the same name.

**Generate the references from the rule set.** The rule set is long-form
prose with rationale. An agent reference has to be short enough to read every
session. The compression is a judgement call, not a transform.
