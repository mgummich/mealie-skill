---
title: Data packs
description: The per-language JSON the tool reads instead of asking the model to remember numbers.
---

# Data packs

`skill/data/<lang>/` holds what the model must not retype and must not
misread: density tables, rounding rules, the fixed vocabularies, the
mechanical lint thresholds.

The split is deliberate. A rule that can be checked mechanically belongs in
`lint.json` and the dry run, where it is free and enforced. A rule that needs
judgement stays in `skill/references/`, where it costs tokens every session
and is advisory. See
[decision 0006](../decisions/0006-data-not-prose.md).

## Resolution

`load_data` picks the language in this order: an explicit `--lang`, the
`locale` in `.mealie.rules.json`, `$MEALIE_LANG`, then `en`. Only the first
two letters are used, and `en` is the fallback for any language without a
pack. A missing pack is a note, not a failure.

The script resolves the directory as `../data` relative to itself, so
`build.py` keeps `scripts/` and `data/` siblings in every target layout.

Current packs: `en`, `de`.

## conversions.json

Everything needed to get an amount metric without the model doing arithmetic
from memory.

| Key | Holds |
|---|---|
| `cupMl`, `liquidMl` | the volume basis |
| `densityPerCup`, `densityAliases` | grams per cup per food, and the names that map onto them |
| `liquidFoods` | what is measured by volume rather than weight |
| `spoonGrams` | tablespoon and teaspoon weights per substance |
| `direct` | fixed conversions that need no density |
| `oven` | Fahrenheit to the steps a real dial has, with fan figures |
| `tinSizes` | inch tin sizes to centimetres |
| `rounding`, `roundingLimit` | how far a converted figure is rounded, and where rounding stops |
| `unitVariants` | spellings that mean the same unit |
| `forbidden`, `forbiddenAmbiguous` | the units the rules refuse outright, in every language |

`forbidden` is what makes creating a non-metric unit a fatal lint finding
rather than a warning.

## lint.json

The mechanically checkable part of the rule set, as thresholds:

| Key | Default (en) |
|---|---|
| `foodNameCase`, `tagNameCase` | `lower` |
| `foodDescriptionMax` | 100 characters |
| `maxTags` / `maxCategories` / `maxTools` / `maxNotes` | 8 / 2 / 4 / 5 |
| `noteTitles` | the 6 permitted note titles |
| `defaultLabelColor` | `#959595` — a label left on it was never assigned one |
| `singleLetterAbbreviations` | abbreviations allowed to be one letter |
| `toolBrands` | brand names that must not appear in a tool |
| `negativeTagPrefixes` | `no X` phrasings that make a tag unfilterable |
| `conjunctions` | words that reveal a tag carrying two concepts |
| `symbolAbbreviations` | abbreviations written as symbols |
| `everydayEquipment` | 20 items that fail the tool gating test |

Everything here is checked by `lint_actions` on every `apply`, including
`--dry-run`.

## labels.json and units.json

The fixed vocabularies, emitted as actions by `seed`:

```bash
python3 .../mealie_ctx.py seed labels --out actions.json
python3 .../mealie_ctx.py seed all --out actions.json
```

`seed` asks the instance what already exists and skips it, so running it on a
populated instance produces only the gaps. `--all` emits the whole pack
without asking.

The unit packs are the same data as
[`rules/en/02-units-EN.json`]({{ site.baseurl }}/rules/en/02-units-EN.json)
and its German counterpart, validated against the rules: no non-metric unit,
no abbreviation collision, no duplicated alias.

## house.json

The template for `.mealie.rules.json` — see [State files](state-files.md).
It is the only pack that is copied into your working directory rather than
read from the skill, because its content is your decisions, not the
project's.

## Adding a language

1. Copy `skill/data/en/` to `skill/data/<lang>/`.
2. Translate the vocabularies — labels, units, note titles, the tag facets.
   Keep `Original:` in English: it is one detection rule for the whole
   database, in every language version.
3. Adjust `densityAliases` to the food names people actually type in that
   language.
4. Build with `--lang`, and check that a `convert` call resolves the local
   food names.

The language of the recipe data is independent of the project language,
which is English everywhere — output, prompts, comments, docstrings.
