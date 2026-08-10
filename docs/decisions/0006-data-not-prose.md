---
title: "0006 — Mechanical rules are data, not prompt text"
description: A checklist in the prompt costs tokens every session and is advisory; the same rule in the dry run is free and enforced.
---

# 0006 — Mechanical rules are data, not prompt text

**Status:** accepted · **Recorded:** 2026-08-10

## Context

A rule set contains two kinds of rule. "A tag carries one concept" needs
judgement — is *quick-vegetarian* one concept or two, and does the answer
change for *sous-vide*? "A food description is at most 100 characters" needs
counting.

Both can be written into a prompt. Only one of them should be.

## Decision

A rule that can be checked mechanically lives in `skill/data/<lang>/lint.json`
and is enforced by `lint_actions` on every `apply`, including `--dry-run`. A
rule that needs judgement stays in `skill/references/`, in prose, and is read
by the model.

The same applies to numbers the model must not recall from memory: densities,
oven temperatures, tin sizes, rounding limits, the fixed label and unit
vocabularies. They are `conversions.json`, `labels.json`, `units.json` —
read by the script, never retyped.

## Consequences

- A checklist in the prompt costs tokens every session and is advisory. The
  same rule in the dry run costs nothing per session and cannot be talked out
  of. The lint is where a rule goes to become true.
- Thresholds are per language, because they are: casing rules and note
  vocabularies differ between the German and English rule sets.
- Conversion arithmetic is not a model task at all. `convert` is a command
  precisely so that no session has to be trusted with a density table.
- The references get shorter, which is the point — an agent reads exactly one
  of them per session, and every line competes with the data it is there to
  reason about.

## Consequences for changes

Adding a mechanical rule means adding a key to `lint.json` and a check to
`lint_actions`, not a paragraph to a reference. If the rule turns out to need
judgement after all — if the check produces false positives that a person
would not — it belongs back in prose, as a `WARN` at most.

## Alternatives rejected

**Everything in the prompt.** Longer, per session, forever, and still only
advisory.

**Everything in code.** Judgement calls hard-coded as heuristics produce
confident wrong answers — the duplicate grouping is deliberately a suspicion
for exactly this reason.
