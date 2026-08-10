# Cookbooks: Cleaning Up the Existing Corpus (EN)

> Companion to **Cookbooks: Creating**.

## Principle

Cookbooks are the only entity that **breaks silently**. A merged tag, a deleted category, a renamed tool — and the filter grasps at nothing. The cookbook does not disappear, it just empties, and nobody notices, because you do not open an empty cookbook.

> **So: after every cleanup of categories, tags or tools, the cookbook filters get checked.** This pass is not its own project but the closing step of the others.

---

## 1. Pass order

| # | Pass | Nature |
| - | ---- | ------ |
| 0 | Inventory | read-only |
| 1 | **Repairing broken filters** | non-destructive |
| 2 | Empty and overfull cookbooks | destructive |
| 3 | Resolving overlaps | destructive |
| 4 | Descriptions and ordering | non-destructive |
| 5 | Checking visibility | non-destructive |
| 6 | Verification | read-only |

---

## 2. Pass 0 — Inventory

- **Hit count per cookbook** — the only metric that matters
- Cookbooks with **zero** hits
- Cookbooks with more than 50 hits, or more than 30 % of the corpus
- Filters referencing a name or ID that no longer exists
- Cookbooks with no `description`
- Cookbooks with `public: true`
- Pairs of cookbooks with largely the same hit set

---

## 3. Pass 1 — Broken filters

For every cookbook at zero hits or with a conspicuously collapsed count:

| Cause | Repair |
| --- | --- |
| tag was merged | rewrite the filter onto the survivor |
| tag was moved to another entity | rewrite the filter onto the destination entity |
| category was demoted to a tag | change the condition from category to tag |
| tool was deleted (gating test) | drop the condition, or switch to the method tag |
| filter references an ID | switch to the name (*Create §4.3*) |
| the vocabulary is gone entirely | delete the cookbook — do not revive the tag |

The last row matters: if a tag was rightly removed, the cookbook built on it was not viable either. Never bring vocabulary back to rescue a cookbook.

---

## 4. Pass 2 — Empty and overfull

| Case | Action |
| --- | --- |
| zero hits, filter intact | delete — the need evidently was not one |
| under 5 hits, persistently | delete or loosen the condition |
| over 50 hits | tighten the condition or split into two cookbooks |
| over 30 % of the corpus | delete — that is the corpus with an extra click |
| `All Recipes`, `Miscellaneous` | delete |

Deleting cookbooks is safe: **no recipe** is lost, only a saved filter. This is the one entity in the whole rule set where deletion is nearly consequence-free — so be generous.

---

## 5. Pass 3 — Overlaps

Two cookbooks with largely the same hit set are one. Keep whichever has the clearer filter and the better name; delete the other.

Subsets are fine, though: `Vegetarian` and `Vegetarian Mains` may coexist as long as both get used. If only one gets opened, the other goes.

---

## 6. Pass 4 — Descriptions and ordering

- Give every cookbook a `description` restating the filter **in one sentence** (*Create §5*). Without it, every later repair is guesswork.
- Reset `position`: the actually-used ones to the top. After the cleanup the list is short enough to order in one go.
- Check names: do they state the result or the filter? `Weeknight Cooking`, not `quick + main`.

---

## 7. Pass 5 — Visibility

Check every cookbook at `public: true` individually: is **every** recipe currently in it your own text and your own image? Since contents shift with the vocabulary, a cookbook that was fine yesterday may contain someone else's recipe today.

When in doubt, `false`. A public cookbook whose contents change automatically is a standing duty of care.

---

## 8. Pass 6 — Verification

- Cookbooks with zero hits: **zero**
- Filters referencing vocabulary that no longer exists: **zero**
- Cookbooks with no `description`: **zero**
- Filters on IDs rather than names: **zero**
- Every cookbook between roughly 5 and 50 hits
- Spot check: open each cookbook and look for a recipe that ought to be missing — the gaps found are tagging errors, not filter errors

That last check is the real return: cookbooks are the best available test of whether recipes are cleanly tagged.

---

## 9. Checklist

- [ ] Is this pass running **after** the cleanup of categories, tags and tools?
- [ ] Hit count per cookbook recorded and compared with the previous value?
- [ ] Broken filters rewritten onto the new vocabulary?
- [ ] No vocabulary revived just to rescue a cookbook?
- [ ] Empty, tiny and overfull cookbooks cleared out?
- [ ] Overlapping cookbooks merged, genuine subsets kept?
- [ ] Does every `description` restate the filter in one sentence?
- [ ] `position` set by actual use?
- [ ] Every public cookbook checked for third-party content?
