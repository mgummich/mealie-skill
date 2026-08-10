# Cookbooks: Creating (EN)

> Builds on **Categories**, **Tags** and **Tools**. A cookbook does not create order, it **consumes** it.

## Principle

A cookbook in Mealie is not a folder you put recipes into but a **saved filter**. Recipes fall into it as soon as they satisfy the filter — and fall out again when their tags change.

Fields: `name`, `description`, `slug`, `position`, `public`, `queryFilterString`.

> **Prime directive:** a cookbook is only as good as the vocabulary it filters on. **Create cookbooks only after categories and tags are cleaned up** — otherwise you build on terms that get merged away in the next pass, and the filter quietly empties.

---

## 1. The creation test

Create a cookbook only when **all three** hold:

1. **Expressible.** It can be written entirely as a filter on existing categories, tags, tools, `rating` or `lastMade`. If it needs hand-picking, it is not a cookbook.
2. **Recurring.** You open it regularly. A one-off search is a search, not a cookbook.
3. **Between roughly 5 and 50 hits.** Fewer is pointless; more is no longer a selection but the whole corpus with an extra click.

If a tag is missing for the filter, **check and create it under the tag rules first** — never invent a tag just to make a cookbook work. If it fails the tag test, the cookbook fails too.

---

## 2. Cookbooks worth having

| Cookbook | Filter idea |
| --- | --- |
| Weeknight Cooking | tag `quick` and category `Main` |
| Vegetarian Mains | tag `vegetarian` and category `Main` |
| Never Cooked | `lastMade` is empty |
| Proven | `rating` of 4 or more |
| Air Fryer | tag `air fryer` |
| Storecupboard | tag `storecupboard` |
| Christmas Baking | tag `christmas` and category `Baking` |
| Meal Prep for Work | tags `meal prep` and `freezable` |

`Never Cooked` is the most useful cookbook of all and needs no tags whatsoever — it answers the question of why you collect recipes at all.

---

## 3. Not cookbooks

| Candidate | Why not |
| --- | --- |
| one cookbook per category (`Desserts`) | the category view already does this |
| `To Try` | that is the meal plan, or `Never Cooked` |
| one cookbook per person | that is what households and users are for |
| `All Recipes` | empty filter, no value |
| `Miscellaneous` | a filter you cannot describe is not a filter |
| a cookbook for one menu | that is a meal plan |

---

## 4. `queryFilterString`

### 4.1 How to produce it
**Build the filter in the interface and copy the generated string.** The syntax is version-dependent; hand-written filters break silently on upgrade, and a silent break means an empty cookbook nobody notices.

### 4.2 What is filterable
Recipe fields and their relations: categories, tags, tools, `rating`, `lastMade`, `createdAt`, household and user.

**`extras` is not filterable** (Extras §1). Anything meant to drive a selection therefore belongs in a tag, not in an extra.

### 4.3 Construction
- Combine conditions with `AND` and `OR`, and bracket groups
- **At most three conditions.** A filter you cannot explain in one sentence will not be understood in six months and will not be maintained.
- Use `OR` sparingly: two subjects joined by `OR` are usually two cookbooks.
- Filter on **names** rather than IDs where possible — names survive a database rebuild, IDs do not.

---

## 5. The other fields

**`name`** — a noun phrase stating the result, not the filter: `Weeknight Cooking`, not `vegetarian + quick`. No `My`, no emoji.

**`description`** — one sentence restating the filter **in words**: *Vegetarian mains that are ready in under 30 minutes.* Without it, nobody later knows why a recipe is missing, and the filter gets guessed at instead of read.

**`position`** — the order in the sidebar. Everyday cookbooks at the top, seasonal and rare ones at the bottom. Set it deliberately; creation order is rarely the useful one.

**`public`** — the same rule as for recipes: public only if **every** contained recipe is your own text and your own image. Since a cookbook's contents change automatically, that is hard to guarantee — when in doubt, `false`.

**`slug`** is generated and never set by hand.

---

## 6. Check after creating

1. **Look at the hit count.** Zero or three hits means the filter is wrong or the vocabulary is missing.
2. **Two spot checks.** Open one recipe that is in it and one that ought to be excluded — is both correct?
3. **The reverse check.** Look for a recipe that *should* be in it and is not. Usually the recipe is missing a tag, not the cookbook a condition.

Point 3 is the real value of the whole construct: cookbooks expose gaps in tagging that nothing else finds.

---

## 7. Checklist

- [ ] Categories and tags cleaned up first?
- [ ] Fully expressible as a filter, with no hand-picking?
- [ ] A recurring need rather than a one-off search?
- [ ] Hit count between roughly 5 and 50?
- [ ] No tag invented purely to make the filter work?
- [ ] Filter generated in the interface rather than hand-written?
- [ ] At most three conditions, on names rather than IDs?
- [ ] Does `description` restate the filter in one sentence?
- [ ] `position` set deliberately?
- [ ] `public` only where all content is your own?
- [ ] Hit count and two spot checks done?
