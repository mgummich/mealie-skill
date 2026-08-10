# Extras

`extras` is a free key-value object on recipes, foods and units, with no
schema. That is exactly why it is the first place a well-kept database runs
wild: everything nobody found a home for lands here, and nobody notices,
because the field is barely visible in the interface.

**`extras` is the last resort, not the easiest one.** Anything that fits an
existing field goes there, even when that is more work.

**The decisive reason:** cookbook filters read recipe fields - categories,
tags, tools, `rating`, `lastMade` - and **not `extras`**. Anything you
might ever filter by is functionally dead here.

| Temptation | Correct home |
|---|---|
| `extras.prep_time` | `prepTime` |
| `extras.vegetarian` | a tag |
| `extras.note` | `notes[]` |
| `extras.source` | `orgURL` |
| `extras.rating` | `rating` |
| `extras.calories` | `nutrition` |

## When it is justified

Three cases, no others: **foreign-system identifiers** (a source system's
id, a GTIN, an article number), **automation** (flags for Home Assistant,
n8n, your own scripts), and **household values with no field** (a food's
usual shop, its default price, its shelf).

All three share one trait: machines read it, people do not. The moment a
human is meant to see the value while cooking or shopping, `extras` is the
wrong home.

## The register

Every permitted key is listed in the house rules (`rules`), with entity,
purpose, format and owning system. Without it you cannot tell a typo from a
new key. A key not in the register does not exist and goes on the next
pass.

Names are `namespace.key`, both lowercase, only `a-z`, `0-9`, `.` and `_`.
The namespace names the **system**, not the topic: `import.`, `pantry.`,
`automation.`, `legacy.`.

Values are **always strings** - the field allows more, but mixed types
break every script that walks the corpus. Booleans as `true`/`false`, dates
as ISO-8601, numbers with a full stop and no unit in the value. No lists,
no nested objects: anyone needing a list needs an entity. **No personal
data** - `extras` travels with exports and shares and is marked
confidential nowhere.

## Phase 1 - Analysis

    audit extras

Every key across recipes, foods and units, with counts. That is already
half the work: usually there are fewer than twenty distinct keys and half
of them are typos.

## Phase 2 - Reconcile against the register

| Finding | Action |
|---|---|
| registered, format correct | leave it |
| registered, format wrong | normalise the value |
| typo or variant of a registered key | rename |
| fits a real field | **move it there**, then delete |
| occurs once and nobody recognises it | delete |
| justified but unregistered | **register it** - do not delete |

Moving a value into its real field is a `patch_recipe` (or `update_food`)
plus the removal, in that order. Extras is a list field on a recipe, so it
replaces: send the whole object back, not just the surviving keys.

## Phase 3 - Execution

    apply actions.json

Report: MOVED (key -> field, objects touched) · RENAMED · REGISTERED ·
DELETED · OPEN.

Afterwards: no key outside the register, no value of a type other than
string, no personal data, and every registered key with an owning system. A
key no system claims is a deletion candidate next time.
