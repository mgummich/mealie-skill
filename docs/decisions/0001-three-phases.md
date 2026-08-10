---
title: "0001 — Three phases, and an approval gate"
description: Analysis, plan, execution — separated, with the plan shown before anything is written.
---

# 0001 — Three phases, and an approval gate

**Status:** accepted · **Recorded:** 2026-08-10

## Context

A model editing a recipe database can be wrong in two ways. It can be wrong
about a fact — this food is not that food — and it can be wrong about scope:
asked to fix one ingredient line, it rewrites the whole recipe because the
rest looked improvable.

The second failure is the dangerous one. It is invisible in the answer, which
looks helpful, and visible only in a database that no longer matches what
anybody decided.

## Decision

Every run is three phases: **analysis → plan → execution**. The plan is a
file, it is shown in full, and nothing is written until it is approved.

This holds for changes to the tool as well as changes to a database: an agent
working on this repository shows what would happen before it happens.

## Consequences

- The thing approved is the thing that runs. `apply` executes a file, it does
  not re-derive intent from a conversation.
- Two kinds of task are never mixed in one plan — a merge pass and a recipe
  repair are two plans, so that approving one is not approving the other.
- `--dry-run` exists so a plan can be checked without an approval being
  implied by having run something.
- It costs a round trip. That is the price, and it is small next to a
  library rewritten by an eager assistant.

## Alternatives rejected

**Write immediately, undo afterwards.** Mealie has no undo. A changelog
([0007](0007-changelog-before-write.md)) makes single fields recoverable, but
recovery is a repair, not a substitute for consent.

**Ask per action.** Twenty approval prompts train the reader to say yes. One
readable plan is read; twenty prompts are clicked.

## Revisit if

Mealie grows transactional writes with a real rollback. Even then the scope
failure remains, so the plan would stay — the gate might loosen.
