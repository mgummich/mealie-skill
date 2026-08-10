# Mealie Food Rules (EN): Cleaning Up the Existing Corpus

> Companion to **Food Rules (EN): Parsing & Creation**. That document handles strings arriving from outside. This one handles the foods you already have. Section references below in the form *Parse §8* point there.

## Purpose
Take an existing food list — grown organically, imported from several sources, edited by several people — and bring it into compliance without breaking the recipes that depend on it.

The two documents differ in one decisive way:

| | Parse Rules | Cleanup Rules |
| --- | --- | --- |
| Input | one string, no history | a corpus with live recipe links |
| Worst case | a wrong link on one recipe | silent corruption across hundreds of recipes |
| Reversibility | trivial — relink | merges and deletions are effectively permanent |
| Default action | match, don't create | **change nothing without evidence** |

> **Prime directive:** a food is not wrong because it is ugly. It is wrong because it is *ambiguous, duplicated, mislabelled or unreachable*. Cosmetic churn costs link stability and buys nothing.

---

## 1. Preconditions (do not skip)

Before the first write:

1. **Full export** of foods, aliases, labels and recipe-to-food links. Verify the export restores.
2. **Reference count per food** — how many recipes use it. This drives every survivor decision and every priority call.
3. **A changelog table** with one row per operation: timestamp, operation, source ID(s), target ID, affected recipe count, actor, reason (§12).
4. **Dry-run capability.** Every pass produces a diff first, and is applied only after the diff is read. A pass with an unread diff is not a pass.

If you cannot produce a reference count, stop. Merging without knowing what points where is guesswork with permanent consequences.

---

## 2. Pass order (this order, not another)

Passes are ordered so each one runs against data the previous one already cleaned. Running them out of order produces work you have to redo.

| # | Pass | Nature | Risk |
| - | ---- | ------ | ---- |
| 0 | Inventory & metrics | read-only | none |
| 1 | Field hygiene | non-destructive | low |
| 2 | Alias integrity | non-destructive | low |
| 3 | Duplicate detection & merge | **destructive** | high |
| 4 | Ambiguity & split | **restructuring** | high |
| 5 | Naming compliance (rename) | non-destructive if done right | medium |
| 6 | `pluralName` correction | non-destructive | low |
| 7 | Label correction | non-destructive | low |
| 8 | Description format | non-destructive | none |
| 9 | Pruning | **destructive** | medium |
| 10 | Re-parse verification | read-only | none |

Rationale for the two non-obvious placements: **dedupe before split**, because splitting a food that turns out to be a duplicate doubles the work; **rename after merge**, because renaming first creates new near-duplicates that the merge pass would then have to catch.

Run one pass at a time across the whole corpus. Do not fix one food end-to-end and move on — that produces an unreviewable diff.

---

## 3. Pass 0 — Inventory

Read-only. Produce these numbers before and after the whole cleanup, or you cannot tell whether it helped:

- total foods; foods with zero recipe links (**orphans**); foods with exactly one link
- foods with `aliases: []`
- foods whose `name` violates Parse §8 (casing, plural, brackets, brand)
- foods with no label, or label `Other`
- foods with a `description` that is empty or over the character limit
- **alias collisions**: any alias string reachable from more than one food — this is a hard error, not a warning
- recipe lines that currently fail to match at all

Sort every worklist by **descending reference count**. The food used in 40 recipes is worth an hour; the orphan used in none can wait for Pass 9.

---

## 4. Pass 1 — Field hygiene

Purely mechanical, safe to automate:

- trim whitespace; collapse internal runs; normalise Unicode to NFC
- strip trailing punctuation from `name`, `pluralName`, aliases
- fix casing to lowercase per Parse §8.1
- ensure `aliases` exists as an array on every food (`[]` if empty)
- remove aliases identical to their own `name` or `pluralName` (case-insensitive)
- deduplicate aliases within a food, case-insensitively

Automate all of it. If a change here needs a judgement call, it belongs in a later pass.

---

## 5. Pass 2 — Alias integrity

Aliases are lookup keys, so a broken alias is a broken match, not a cosmetic issue.

**Alias collision — hard error.** If the same string is an alias on two foods, matching is non-deterministic and the parser will pick arbitrarily. Every collision must be resolved before Pass 3:

- the two foods are the same thing → merge candidate, hand to Pass 3
- the two foods are different, and the alias belongs to one → delete it from the other
- the two foods are different, and the alias is genuinely ambiguous (`coriander`) → **delete it from both** and add a row to the Parse §6.2 default table instead. An ambiguity belongs in a visible table, not hidden in two alias lists.

**Illegitimate aliases — demote or delete.** An alias that is really a *derived form* (`lemon juice` on `lemon`), a *variety* (`granny smith` on `apple`) or a *different product* (`currants` on `raisins`) is a silent mis-mapping: every recipe using it gets linked to the wrong food. Remove it, and check whether the correct food exists — if not, it is a Pass 4 split or a new food.

**Missing aliases — add.** For each food, check the Parse §8.4 seed list: the other locale, spelling variants, dropped diacritics, space/hyphen variants, powder forms. This is the cheapest quality win in the entire cleanup, because it converts future review items into automatic matches.

---

## 6. Pass 3 — Duplicates and merging

### 6.1 Finding candidates
Run each signal separately and review each list on its own:

1. Identical normalised lookup keys (Parse §3) — near-certain duplicates
2. Alias collisions surviving Pass 2
3. One food's `name` equals another's `pluralName`
4. Fuzzy pairs: edit distance ≤ 2 on keys of length ≥ 6
5. One `name` is a substring of another — catches `oil` / `olive oil` and other over-generic strays
6. Same label + shared head noun

Signals 4–6 produce **candidates, never decisions**.

### 6.2 Merging is forbidden when
These look like duplicates and are not. Merging them corrupts data irreversibly:

- **Derived forms**: `lemon` vs `lemon [juice]` vs `lemon [zest]`
- **Varieties**: `apple` vs `granny smith`
- **Different products**: currants vs raisins; `cornflour` vs `cornmeal`
- **Fresh vs dried**, whole vs ground, and every other splitting qualifier (Parse §6.1)
- **Genuinely different products**: `double cream` vs `single cream`; `buffalo mozzarella` vs `mozzarella`
- **Preparations vs base**: espresso vs coffee; pulled pork vs pork shoulder

If a pair falls here, it is not a merge. Either both are correct as they stand, or one is a Pass 9 prune.

### 6.3 Choosing the survivor
In this order:

1. Highest recipe reference count — minimises relinking and therefore risk
2. On a tie, the one whose `name` already complies with Parse §8
3. On a tie, the older record — stable IDs matter for external integrations

Note that the survivor's **name may still be wrong**. Survivor selection is about which *record* lives; the name is fixed in Pass 5. Do not pick a low-reference record just because its name is prettier.

### 6.4 Merge procedure
1. Set the survivor's `name` to the canonical form (Parse §8) — even if that is neither of the two current names
2. **Add the loser's `name` and `pluralName` as aliases on the survivor.** Non-negotiable: without it, every recipe source that used the old spelling starts failing to match again
3. Union the aliases, then re-run Pass 1 and Pass 2 hygiene on the result
4. Keep the shorter, clearer `description`; if both are bad, rewrite per Parse §10
5. Take the more correct `label` — not automatically the survivor's; check it against the Parse §9.2 mistakes table
6. Repoint every recipe reference from loser to survivor
7. Verify the reference count on the survivor equals the sum of both previous counts
8. Delete the loser and write the changelog row

Step 7 is the guard. If the numbers do not add up, references were lost — roll back.

---

## 7. Pass 4 — Ambiguity and splitting

### 7.1 Recognising an ambiguous food
Bare `cinnamon`, `pepper`, `coriander`, `stock` — foods that different recipes use to mean different things. The signals:

- the name has no qualifier but a splitting qualifier applies to it (Parse §6.1)
- recipe lines pointing at it disagree: some say `stick`, some say `ground`
- its aliases contain derived forms (caught in Pass 2)

### 7.2 Gather evidence first
**Pull the actual recipe lines** referencing the food before deciding anything. A food that 30 recipes all use to mean the same thing is not ambiguous, whatever its name suggests — it needs a Pass 5 rename, not a split. Splitting on suspicion rather than evidence creates variants nobody uses.

### 7.3 Split procedure
1. Create the variant foods per Parse §8 (`cinnamon [stick]`, `cinnamon powder`)
2. **Reassign recipe references one at a time**, reading each line. Never bulk-move.
3. Lines you cannot classify from the text stay on the base food and go to review — a wrong assignment is worse than an unresolved one
4. Move each alias to whichever variant it actually denotes (Parse §8.5)
5. Decide the fate of the original record:
   - it has a legitimate unqualified meaning (`lemon` next to `lemon [juice]`) → **keep it**
   - it was purely ambiguous and now has zero references → delete
   - it still has unclassifiable references → keep it, flag it, revisit
6. Add the bare form to the Parse §6.2 default table so future imports resolve without review

### 7.4 The restraint rule
Every split multiplies shopping-list entries. Split when recipes genuinely disagree — not to make the taxonomy elegant. Non-splitting qualifiers (`[tinned]`, `[frozen]`, `[roasted]`, `[smoked]`) usually do **not** justify a split: keep one food and let the qualifier live in the recipe note, unless the culinary role really differs.

---

## 8. Pass 5 — Naming compliance

Apply Parse §8 to every non-compliant name. **The old name always becomes an alias.** This is the single most frequently forgotten step in a cleanup, and forgetting it silently breaks every future import from any source still using the old spelling.

Priority order, because renaming has a cost:

1. Names that are **wrong** — brands, dishes, preparations, ambiguous forms
2. Names that break **parsing** — plural instead of singular, invented bracket forms, two qualifiers
3. Names that are merely **inconsistent** — casing, spacing, hyphenation

Do not renumber the world for category 3 alone on a large corpus. Batch it, or fold it into whichever pass already touches those records.

When renaming, update `pluralName` in the same operation — a renamed food with a stale plural is a new mismatch.

---

## 9. Passes 6–8 — Plurals, labels, descriptions

**`pluralName`** — check against Parse §8.3. The common errors: a guessed `+s` on an irregular, a mass noun that was given a plural (`rices`), and a bracket variant that pluralised the base instead of the countable part.

**Labels** — work label by label rather than food by food. Pull everything currently under one label, scan for members that do not belong, and check against the Parse §9.2 mistakes table. `Other` is a worklist, not a label: every food sitting there is either mislabelled or a Pass 9 prune candidate.

**Descriptions** — enforce `definition; use.` and the character limit. This is the only pass with no data-integrity risk, so it can run last and be automated aggressively.

---

## 10. Pass 9 — Pruning

| Kind | Test | Action |
| ---- | ---- | ------ |
| Orphan | zero recipe references | delete, if it is also not a plausible future food — otherwise keep |
| Brand | Parse §7.1 | merge into the generic; the brand becomes an alias only if generic in speech |
| Dish or preparation | Parse §7.1 | if referenced, convert to a sub-recipe or relink to components; delete only when unreferenced |
| Over-generic | `juice`, `dough`, `meat` | keep only if recipes genuinely use it that way; otherwise split or delete |
| Test or import artefact | `test`, `xxx`, empty names | delete |

**Deprecate rather than delete when references exist.** A `deprecated` flag keeps the record reachable for matching and reporting while hiding it from pickers, and it is reversible. Deletion is not. Reserve deletion for records with zero references and no historical value.

---

## 11. Pass 10 — Verification

The cleanup is only real if parsing improved. Re-run the parse rules over the whole recipe corpus and compare against the Pass 0 baseline:

- share of recipe lines matching at tier ≤ 3 — must go **up**
- review-queue size — must go **down**
- alias collisions — must be **zero**
- non-compliant names — must be **zero**
- orphan count — should drop, but a small stable set is fine
- **total recipe-to-food links — must be unchanged**, unless a documented split or deletion accounts for the difference

The last line is the integrity check for the entire operation. Any unexplained drop means references were lost somewhere in Pass 3 or 4.

---

## 12. Changelog, idempotency and rollback

**Log every operation**: timestamp, type (`merge`/`split`/`rename`/`relabel`/`delete`), source and target IDs, previous and new values, affected recipe count, actor, one-line reason. "Because the rules say so" is not a reason; "duplicate of #412, 0 references, alias collision on *scallion*" is.

**Idempotency.** Running the full pass sequence a second time on an already-clean corpus must produce zero changes. If it does not, two rules disagree — find and fix the disagreement rather than living with churn.

**Ping-pong guard.** If a food is renamed A → B in one run and B → A in the next, the rules contain a genuine contradiction. Freeze that record, resolve the rule conflict, then unfreeze. Never let the passes fight each other across runs.

**Rollback.** Merges and deletions are only reversible from the export plus the changelog. Keep both for as long as it takes to be confident, which in practice means at least one full import cycle from every recipe source you use.

---

## 13. Checklist

**Before starting**
- [ ] Export taken and restore verified?
- [ ] Reference count available per food?
- [ ] Changelog table ready?
- [ ] Baseline metrics from Pass 0 recorded?

**Per pass**
- [ ] One pass at a time, across the whole corpus?
- [ ] Diff produced and actually read before applying?
- [ ] Worklist sorted by reference count?

**Per merge**
- [ ] Is it genuinely the same food, and not a §6.2 forbidden pair?
- [ ] Survivor chosen by reference count, not by name aesthetics?
- [ ] Loser's `name` and `pluralName` added as aliases?
- [ ] Label checked against the mistakes table, not just inherited?
- [ ] Reference counts add up after relinking?

**Per split**
- [ ] Actual recipe lines read as evidence?
- [ ] References reassigned individually, never in bulk?
- [ ] Unclassifiable references left on the base and flagged?
- [ ] Bare form added to the default-resolution table?

**Per rename**
- [ ] Old name added as an alias?
- [ ] `pluralName` updated in the same operation?

**At the end**
- [ ] Total recipe-to-food links unchanged or fully explained?
- [ ] Alias collisions at zero?
- [ ] Second full run produces no changes?
