# Foods

Two tasks, never in the same plan: **filling gaps** is harmless, **merging
duplicates** is destructive. Units have their own file, `units.md`.

**Prime directive when something arrives:** match, do not create. A food
differing from an existing one only by plural, casing, punctuation,
diacritics, preparation wording or a stripped qualifier is never a second
food.

**Prime directive when reworking the corpus:** change nothing without
evidence. A food is not wrong because it is ugly - it is wrong when it is
ambiguous, duplicated, mislabelled or unreachable.

The locale (en-GB vs en-US, and the equivalent elsewhere) is decided once
for the whole database and lives in the house rules - `rules`. The variant
you did not pick is an alias, never a second food.

## Phase 1 - Analysis

    audit foods

Report: total, gaps, unused, duplicate groups with recipe counts. Sort every
worklist by **recipe count descending** - the food in 40 recipes is worth an
hour, the orphan can wait.

The duplicate suspicion is a coarse normal-form heuristic. It finds
tomato/tomatoes, not scallion/spring onion. Check the groups on their
merits and add the pairs it misses.

**Alias collisions are a hard error**, not a finding: if one string is an
alias on two foods, matching is non-deterministic and the parser picks
arbitrarily. Resolve them before any merge - same thing → merge; different
things → delete the alias from the one it does not belong to; genuinely
ambiguous (`coriander`) → delete it from both and put a row in the house
rules instead, where the ambiguity is visible.

## Matching a food string

The food string is what remains of a recipe line after quantity, unit and
instruction are removed - not the line. One line can hold two: `salt and
pepper` is two strings.

**Try the raw string first, then strip.** `smoked salmon`, `spring onion`
and `double cream` all die if adjectives are stripped before lookup.

Strip: articles and vague quantifiers, quantities and units, preparation
(`chopped`, `drained`, `at room temperature`, `to taste`, `for frying`),
marketing and provenance (`good-quality`, `ripe`, `free-range`, `organic`,
`leftover`), then singularise. Leave pluralia tantum alone (`rolled oats`,
`breadcrumbs`).

**Extract, do not strip, these** - they change which food is meant:
`[fresh]`, `[dried]`, `[whole]`, `[ground]`, `[flakes]`, `[stick]`,
`[leaf]`, `[juice]`, `[zest]`, `[peel]`, `[tinned]`, `[frozen]`,
`[pickled]`, `[roasted]`, `[smoked]`. One qualifier per name, the most
defining; the rest goes to the ingredient note. `juice of 1 lemon` inverts:
the head noun is the qualifier, so `lemon [juice]`.

Cascade, stopping at the first tier with **exactly one** hit:

| Tier | Test | Action |
|---|---|---|
| 0 | raw string equals a `name` | link |
| 1 | lookup key equals `name` or `pluralName` | link |
| 2 | lookup key equals an alias | link |
| 3 | base + qualifier equals `base [qualifier]` | link |
| 4 | redirect fires: `<base> powder`, `peppercorn` | link |
| 5 | base matches, qualifier has no entry | see below |
| 6 | `<food> paste/purée/pieces` → `<food>` | link or review |
| 7 | fuzzy, edit distance ≤ 2 | **suggest only** |

Two hits at one tier is an ambiguity, not a match. **Never auto-accept a
fuzzy hit**: `cornflower` is a real word and would silently become
`cornflour` about as often as it should.

At tier 5 the answer depends on the qualifier. **Splitting** ones
(`[fresh]`, `[dried]`, `[whole]`, `[ground]`, `[juice]`, `[zest]`,
`[peel]`, `[flakes]`, `[stick]`, `[leaf]`) mean a genuinely different food:
create the variant or ask, never silently fall back to the base.
**Non-splitting** ones (`[tinned]`, `[frozen]`, `[pickled]`, `[roasted]`,
`[smoked]`) are storage states: link to the base and put the qualifier in
the note.

A bare ambiguous base (`pepper`, `flour`, `milk`) is resolved from the
default table in the house rules, not by guessing. Resolved the same bare
string twice? Add the row.

## Creating a food

Only when the cascade returns nothing, and not then if a fuzzy candidate
exists - that is where duplicate proliferation enters.

**Not a food:** brands (map to the generic: Philadelphia → cream cheese),
preparations you make yourself (mashed potato, homemade pesto - those are
sub-recipes, see `recipes.md`), finished dishes, leftovers and states, and
anything too generic to shop for (`juice`, `meat`). A fixed product name
you buy as one thing is fine: `garam masala`, `italian seasoning`.

Fields, all of them, at creation:

- `name` - everyday term in the chosen locale, singular, the casing the
  language wants. Real words beat brackets: `peppercorn`, `bay leaf`,
  `icing sugar`, `cornflour`. Where `X powder` is the product name, that is
  the name: `garlic powder`, not `garlic [ground]`.
- `pluralName` - mass nouns and already-plural names repeat the name.
  Bracket variants pluralise the countable part: `cinnamon [sticks]`.
- `description` - `definition; use.` Short, factual, under 100 characters,
  no marketing, no amounts.
- `labelId` - exactly one, from the fixed set; see `labels.md`.
- `aliases` - objects, `[{"name": "tomatoes"}]`; **never empty.** Seed with
  the string that triggered creation, the other locale, spelling variants,
  dropped diacritics, space/hyphen variants, powder forms. This is what
  makes the next import match, and the plan lint warns when it is missing.

**Never an alias, always its own food:** varieties (`granny smith`),
derived forms (`lemon [juice]`), different products (currants ≠ raisins,
cornflour ≠ cornmeal), preparations (espresso ≠ coffee), fresh vs dried.

When in doubt create a separate food rather than over-merging: a spurious
food is fixable by merge, a wrong merge corrupts every recipe on both
sides.

## Phase 2a - Fill gaps

    ctx foods --limit 25

Plan as a table `food | missing | addition`. Only add missing fields, never
overwrite existing values. If a name is wrong, show it and correct it -
and add the old name as an alias in the same action.

## Phase 2b - Merge duplicates

    ctx foods --group "tomato"

**Do not merge** - these look alike and are not: derived forms (`lemon` vs
`lemon [juice]`), varieties (`apple` vs `granny smith`), different products
(currants vs raisins, `cornflour` vs `cornmeal`), fresh vs dried and every
other splitting qualifier, `double cream` vs `single cream`, preparation vs
base (espresso vs coffee). Overlap is not a reason to merge; only sameness
is. In doubt, leave it and list it under QUESTIONS.

The survivor is the food with the **most recipes** - that minimises
relinking. On a tie, the compliant name; then the older record. Its name
may still be wrong: fix that with `update_food` first, then merge.

Plan per group:

    Group: tomato
      KEEP    tomato (3f2a…) – 14 recipes, label set
      MERGE   tomatoes (91bc…) – 2 recipes  -> becomes an alias
      MERGE   Tomato (55de…) – 0 recipes    -> becomes an alias
      THEN    update_food: aliases += tomatoes, Tomato

The merge rewrites the affected recipes and deletes the source. It cannot
be undone - say so in the plan, with the recipe count. **Always carry the
loser's `name` and `pluralName` over as aliases**, or every source still
using the old spelling starts failing to match again.

The script reads the affected recipes back afterwards and stops the run if
any still points at the source.

## Splitting an ambiguous food

Bare `cinnamon` used by some recipes as sticks and by others as powder.
**Pull the actual recipe lines first** - a food that 30 recipes all mean
the same way is a rename, not a split.

Create the variants, then reassign **one recipe at a time**, reading each
line. Lines you cannot classify stay on the base and go to QUESTIONS - an
unresolved line is repairable, a wrongly moved one is not. Keep the base
when it has a legitimate unqualified meaning. Add the bare form to the
house rules table afterwards.

Every split multiplies shopping-list entries. Split when recipes genuinely
disagree, not to make the taxonomy elegant.

## Unused entries

`audit` lists foods no recipe uses - mostly harmless leftovers, and good
merge sources, since removing one touches no recipe. Propose, never delete
unasked; `delete_food` is for those orphans, and the script refuses it
while any recipe still uses the food. A food that is still referenced is
kept, not deleted - merge it into the survivor instead.

## Phase 3 - Execution

    apply actions.json

Report: UPDATED (object - fields) · MERGED (from -> to, rewritten recipes) ·
ALIASES ADDED · OPEN (deliberately not merged, with a reason).

Afterwards the numbers have to add up: total recipe-to-food links unchanged
unless a documented split or deletion explains the difference. Any
unexplained drop means references were lost.

Keep batches small: at most 25 gaps or 5 duplicate groups per run.
