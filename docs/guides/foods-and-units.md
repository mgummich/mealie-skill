---
title: Foods and units
description: The two entities every ingredient line points at — how to audit them, merge duplicates and get the library metric.
---

# Foods and units

Foods and units sit under every ingredient line, which makes them the first
thing to clean and the most expensive thing to get wrong. A merge rewrites
every recipe that used the loser. A deletion strips the ingredient from them
instead — which is why the tool refuses one while any recipe still points at
the object.

What a good food or unit looks like is the rule set's subject:
[foods]({{ site.baseurl }}/rules/en/01-foods-create-EN.md) ·
[units]({{ site.baseurl }}/rules/en/02-units-create-EN.md). This page is
about running the passes.

## Audit first

```bash
python3 .../mealie_ctx.py audit foods
python3 .../mealie_ctx.py audit units
```

Both print the same shape: totals, gaps, the hard errors, the unused, then
the duplicate suspicions.

Two lines are **hard errors**, not findings, and everything else waits until
they are cleared:

- **Alias collisions.** The same alias on two foods makes Mealie's matching
  non-deterministic — the same imported line lands on a different food
  depending on nothing you control.
- **Abbreviation collisions** on units, for the same reason.

The rest is a worklist:

| Line | Means |
|---|---|
| `GAPS: description=…, plural=…` | fields the rule set wants filled |
| `WITHOUT LABEL: 40 (18 %)` | those foods land unsorted at the end of every shopping list |
| `NAME NOT LOWERCASE` | the house casing rule, from `lint.json` |
| `NON-METRIC (…, the conversion worklist)` | units that must not exist, sorted by how many recipes are affected |
| `WITHOUT ABBREVIATION` | shopping lists and ingredient displays get long |
| `UNUSED` | candidates for deletion — safe, because nothing points at them |
| `POSSIBLE DUPLICATES: n groups` | suspicion, never a verdict |

## Duplicates are a suspicion

The grouping folds case and umlauts and strips one common plural ending, so
it finds `Tomate`/`Tomaten` and `Kürbis`/`Kuerbis`. It deliberately does not
group `butter`/`buttermilk` or `tomato`/`cherry tomato`. It will still
propose pairs that are not duplicates — `Korinthen` and `Koriander` differ by
two characters and are entirely different things.

Every group is a question for a person, and the agent is required to present
them rather than merge them. See
[decision 0005](../decisions/0005-guards-refuse-not-warn.md) for why the tool
does not decide this itself.

## Merge, do not delete

```json
{"op": "merge_food", "payload": {"from": "<loser-id>", "to": "<survivor-id>"}}
```

A merge repoints every recipe that used the loser and then removes it. The
tool reads the loser's whole record first — the changelog is the only place
it survives — and afterwards reads the affected recipes back to check that
none still points at the merged-away object. Mealie answers a merge that
lost references exactly like one that worked, so this verification is the
only thing standing between you and a silent data loss.

After a merge, **add the old name as an alias on the survivor**. Otherwise
the next import recreates the duplicate you just removed, and the same
groups come back on the next audit.

`delete_food` and `delete_unit` exist for the unused only. `apply` refuses
them while the index shows any recipe using the object, and refuses them
without an index at all, because then it cannot check. Freeing the last
reference and deleting in the same run is refused too — audit again first.

## Getting metric

The rule set is strict: metric units plus dimensionless count and container
measures. Cup, ounce, pound, stick and pint are never created, they are
converted.

The conversion is in the tool, not in the prompt:

```console
$ python3 .../mealie_ctx.py convert "1 cup plain flour" "8 oz butter" "350 F"
120 g plain flour   [note: Original: 1 cup plain flour]
230 g butter   [note: Original: 8 oz butter]
175 °C   [note: Original: 350 F]
```

Volumes go through a density table keyed by food, so a cup of flour and a cup
of water are not the same 240 g. Temperatures come back rounded to the oven
steps that exist on a real dial; `--fan` adds the fan figure.

The `Original:` prefix is fixed English in every language version, on
purpose: it is one detection rule for the whole database, and it does double
duty as evidence for a person and as a marker against converting the same
line twice. `audit recipes` counts the lines carrying it.

Creating a non-metric unit is refused by the plan lint outright, not warned
about.

## Order within the pass

1. Clear alias and abbreviation collisions.
2. Merge duplicates, adding aliases to the survivors.
3. Fill gaps — label, plural, description, abbreviation.
4. Convert non-metric units, then delete them once nothing uses them.
5. Delete what is genuinely unused.

The execution order in an actions file enforces the shape of this: merges run
before creates, updates before deletes. See
[the actions reference](../reference/actions.md).
