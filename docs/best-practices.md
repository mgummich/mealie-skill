---
title: Mealie best practices
description: Running the instance well — backups, tokens, imports, households — the operational side the rule set does not cover.
---

# Mealie best practices

The [rule set]({{ site.baseurl }}/rules/) covers what good data looks like:
how a food is named, what a category is an axis of, when a cookbook is worth
creating. This page covers the other half — running the instance so that the
data has somewhere safe to live.

## Backups

Mealie → Site Settings → Backups. Make one before every cleanup run and keep
the file somewhere that is not the same disk as the container volume.

A backup is the only thing that survives a mistake the tool never saw: an
import running in parallel, a volume lost on a container rebuild, a bulk edit
in the UI. The changelog recovers fields; a backup recovers the database.

Test a restore once. An untested backup is a belief.

## Tokens and access

- Create the token as **the user whose recipes you are cleaning**. Households
  and groups scope what the API returns, and a token from the wrong user
  quietly works on a different corpus.
- One token per tool, so that revoking one does not break the others.
- Tokens live in `.mealie.env`, which belongs out of version control. If you
  paste a changelog or an env file into a bug report, read it first.
- If Mealie is reachable from the internet, put it behind authentication that
  is not just Mealie's own, and keep OIDC's `email_verified` requirement on —
  Mealie 3.21 made it mandatory for a reason: an unverified self-asserted
  email address could otherwise match an existing account.

## Importing

Most data problems arrive at import, so most of them are cheaper to prevent
than to clean up:

- **Import one recipe, then look at it** before importing thirty from the
  same site. Sites differ in how much structured data they publish, and a
  site that yields unparsed lines will do it thirty more times.
- **Check the ingredient lines, not the picture.** A recipe that looks
  perfect and has zero linked foods is invisible to shopping lists, diet tags
  and duplicate detection.
- **Convert on the way in.** A cup that becomes 120 g at import never becomes
  a cleanup pass later. The `Original:` note keeps the evidence.
- Mealie 3.22 improved scraper resilience and added optional proxy and
  FlareSolverr support for sites behind bot protection. If a site refuses,
  that is the lever — not manual retyping.

## Households, groups and shared instances

- A **group** is a shared vocabulary: foods, units, labels, categories, tags
  and tools are group-level. Everyone editing them is editing everyone's.
- A **household** is a shared collection: cookbooks and meal plans hang off
  it since Mealie 2.0.
- On a shared instance, agree the vocabulary before running a cleanup.
  `.mealie.rules.json` is where that agreement gets written down — a decision
  nobody recorded gets remade differently next month.

## Labels and shopping lists

Labels are the only thing standing between a shopping list and a wall of
unsorted items. `audit foods` reports the share of foods without one, and
`seed labels` writes the fixed palette as a plan.

Set them once, in the order of your supermarket, and the list sorts itself
forever after.

## A maintenance rhythm

| When | What |
|---|---|
| At import | check the lines of the first recipe from a new site |
| Monthly | `audit recipes` — watch the linked-food percentage |
| Quarterly | foods and units: duplicates, gaps, non-metric leftovers |
| After every organizer cleanup | check cookbook hit counts, the same day |
| Yearly | `audit links --check-urls`, and a restore test of a backup |

The order matters and is not arbitrary: foods and units first, then
organizers, then recipes, then cookbooks. Cookbooks filter on vocabulary;
building them before the vocabulary settles means building on terms that get
merged away.

## Things that quietly cost you later

- **Tags nobody filters by.** They read as information and act as clutter. If
  it would never be a cookbook or a search, it is a note.
- **Two categories per recipe.** Above an average of 1.5, the category axis
  has collapsed into a second tag system. `audit categories` says so.
- **A cookbook with no description.** Six months on, nobody can tell whether
  a missing recipe is a filter bug or a tagging gap.
- **`extras` as a filter key.** It is not filterable. Anything meant to drive
  a selection belongs in a tag.
- **Non-metric units kept "just for this one recipe".** They spread, and the
  rules refuse to create them for exactly that reason.

## When something looks wrong

Start with the audits — they read, they write nothing, and they cost one
index build:

```bash
python3 .../mealie_ctx.py audit recipes
python3 .../mealie_ctx.py audit foods
python3 .../mealie_ctx.py audit links
```

Then [the guides](guides/first-run.md). If a write went somewhere you did not
expect, the changelog says what it replaced:
[Recovering a run](guides/recovering-a-run.md).
