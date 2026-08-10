---
title: "0002 — No operation for deleting a recipe"
description: Duplicate recipes are presented; the deletion happens by hand in the UI.
---

# 0002 — No operation for deleting a recipe

**Status:** accepted · **Recorded:** 2026-08-10

## Context

The duplicate audit is good at finding candidates and bad at being right
about them. It scores name similarity and ingredient overlap, and two
variants of the same dish — the weekday one and the one with wine — score
high on purpose, because a person should look at them.

A recipe is also the only object in Mealie whose loss is not repairable from
anything the tool holds. A merged food can be recreated from the changelog.
A deleted recipe takes its steps, its notes, its rating and its history with
it.

## Decision

There is no `delete_recipe` operation, and there will not be one. Duplicates
are presented. The deletion happens by hand, in the UI, by someone who opened
both.

## Consequences

- The duplicate audit ends in a list, not a plan. That is the finished state
  of that mode, not a missing half.
- No amount of prompting produces a recipe deletion, because the operation
  does not exist. A guard can be argued with; a missing capability cannot.
- Recipe cleanup work is limited to what can be repaired: fields, lines,
  images, tags.

## Alternatives rejected

**Delete behind a confirmation.** Confirmations are the thing people click
through. The failure mode here — one wrong `y` and a recipe is gone — is
exactly what a confirmation does not prevent.

**Delete with an undo window.** It would need to hold the whole recipe,
including its image, and it would still be a rollback nobody tests.

## Revisit if

Never, for practical purposes. The alternative would be Mealie growing a
trash can with a restore path, at which point deletion stops being
destructive and this decision stops being about deletion.
