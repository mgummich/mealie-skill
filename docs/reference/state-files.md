---
title: State files
description: The four files the tool keeps in your working directory, what each holds, and which of them you should keep.
---

# State files

Everything the tool remembers lives in four files in the working directory.
None of them belongs in a repository — the changelog and the env file in
particular carry your data and your token.

| File | Written by | Keep? |
|---|---|---|
| `.mealie.env` | `setup` | yes, out of version control |
| `.mealie_index.json` | first `audit`, `index` | no, rebuilt on demand |
| `.mealie.changelog.jsonl` | every writing `apply` | yes — the only way back |
| `.mealie.rules.json` | `rules --init`, then you | yes |

Each path is overridable: `MEALIE_ENV`, `MEALIE_INDEX`, `MEALIE_CHANGELOG`,
`MEALIE_RULES`.

## .mealie.env

```
MEALIE_URL=https://mealie.example.com
MEALIE_TOKEN=eyJhbGciOi...
```

Precedence is per variable: environment → `.mealie.env` → `.env`. The `.env`
fallback is read, never written.

Other Mealie tools name the same two values differently, and all of them are
accepted so that one file serves every tool:

| Alias | Canonical |
|---|---|
| `MEALIE_BASE_URL` | `MEALIE_URL` |
| `MEALIE_API_TOKEN` | `MEALIE_TOKEN` — the name `mcp-mealie` uses |
| `MEALIE_API_KEY` | `MEALIE_TOKEN` |

The canonical names win when both are present.

## .mealie_index.json

One pass over every recipe, one summary record each. Built on the first
`audit`, deleted after every writing `apply`.

Per recipe it holds: slug and name, note titles, extras keys, rating and
whether it was ever cooked, the counts that matter for repairs (ingredient
lines, steps, unparsed lines, amounts stranded in a note, lines without
`originalText`, lines carrying `Original:`), the organizer ids, the food and
unit ids plus the food names, whether there is an image and a source URL, and
whether the description is non-empty.

Two things follow from that:

- **Every evaluation reads the index.** Usage counts, duplicate groups, link
  rot, diet candidates. Nothing builds its own loop over the API.
- **The index has a version.** Teaching it a new field raises
  `INDEX_VERSION`; an index from an older version is rebuilt rather than
  audited on fields it does not carry, which would report zero and look like
  a clean result.

Recipes the instance cannot serialise are skipped, listed under `failed`, and
named by `audit recipes` long after the build scrolled past.

## .mealie.changelog.jsonl

One JSON object per applied action, appended before the next action runs.
Mealie has no undo and this tool has no rollback command: this file is the
only path back. Its shape and how to use it are in
[Recovering a run](../guides/recovering-a-run.md).

It grows without bound and is never rotated by the tool. That is deliberate —
a rotation that discards the record of the merge you are trying to undo would
defeat the file's only purpose.

## .mealie.rules.json

The per-instance decisions the rule set says must be made once and held to.
`rules --init` writes the template; the tool reads it and never changes it.

```json
{
  "locale": "en-GB",
  "categoryAxis": "dish type",
  "timeFormat": "25 min, 1 hr 30 min",
  "containerAssumptions": {"tin": "400 g", "packet": "", "jar": ""},
  "defaultResolutions": {"pepper": "black pepper [ground]", "flour": "plain flour"},
  "unitVariants": {},
  "tagFacets": {"Cuisine": [], "Diet": [], "Occasion": [], "Effort": []},
  "extrasRegister": []
}
```

| Key | Decides |
|---|---|
| `locale` | spelling conventions for names and prose |
| `categoryAxis` | what your categories are an axis *of* — the question they all answer |
| `timeFormat` | how times are written, so they sort and read alike |
| `containerAssumptions` | what a `tin` or a `packet` weighs when a recipe does not say |
| `defaultResolutions` | what a bare `pepper` or `flour` resolves to |
| `unitVariants` | local spellings that should map onto a canonical unit |
| `tagFacets` | the facets your tag vocabulary is allowed to grow along |
| `extrasRegister` | the `extras` keys this instance uses on purpose |

Without these, every run re-decides them, and the corpus drifts back into a
mixture within months. `audit` prints a one-line summary of the file when it
exists, so a run that is about to ignore your decisions says so first.
