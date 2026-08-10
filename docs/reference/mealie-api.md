---
title: Mealie API
description: Which endpoints the tool uses, which Mealie versions serve them, and the two places the API moved under it.
---

# Mealie API

Every request goes through `mreq` in `mealie_ctx.py`. Nothing else in the
project makes an HTTP call — `optimize.py` shells out to the script rather
than talking to Mealie itself.

The paths below were checked against the OpenAPI specification and the route
sources of **Mealie 3.22.0** (released 2026-07-28).

## Endpoints used

| Purpose | Method and path |
|---|---|
| Credential check | `GET /api/users/self` |
| Recipe list, index build | `GET /api/recipes` |
| One recipe | `GET /api/recipes/{slug}` |
| Recipe write | `PATCH /api/recipes/{slug}` |
| Recipe image from a URL | `POST /api/recipes/{slug}/image` |
| Cookbook hit count | `GET /api/recipes?cookbook={id}&perPage=1` |
| Foods | `GET/POST /api/foods`, `GET/PUT/DELETE /api/foods/{id}` |
| Food merge | `PUT /api/foods/merge` |
| Units | `GET/POST /api/units`, `GET/PUT/DELETE /api/units/{id}` |
| Unit merge | `PUT /api/units/merge` |
| Shopping-list labels | `GET/POST /api/groups/labels`, `GET/PUT/DELETE /api/groups/labels/{id}` |
| Categories | `GET/POST /api/organizers/categories`, `GET/PUT/DELETE …/{id}` |
| Tags | `GET/POST /api/organizers/tags`, `GET/PUT/DELETE …/{id}` |
| Tools | `GET/POST /api/organizers/tools`, `GET/PUT/DELETE …/{id}` |
| Cookbooks | `GET/POST /api/households/cookbooks`, `GET/PUT/DELETE …/{id}` |

The merge bodies are `{"fromFood": …, "toFood": …}` and
`{"fromUnit": …, "toUnit": …}`. The image body is
`{"url": …, "includeTags": false}`.

## Version requirements

The tool targets current Mealie. Two changes landed in **Mealie 2.0** that it
now assumes:

- **Cookbooks moved from the group to the household.**
  `/api/groups/cookbooks` became `/api/households/cookbooks`.
- **The cookbook filter became one string.** `CreateCookBook` carries
  `name`, `description`, `slug`, `position`, `public` and
  `queryFilterString`. The three name lists and their `requireAll*` switches
  are gone.

On Mealie 1.x both of these fail — the first loudly with a 404, the second
silently, which is the worse one. See below.

Check what your instance serves:

```bash
for p in foods units groups/labels organizers/categories \
         organizers/tags organizers/tools households/cookbooks; do
  printf '%-26s ' "$p"
  curl -s -o /dev/null -w '%{http_code}\n' \
    -H "Authorization: Bearer $MEALIE_TOKEN" "$MEALIE_URL/api/$p?perPage=1"
done
```

Anything answering 404 goes into the `EP` dictionary in `mealie_ctx.py`.

## Mealie ignores what it does not know

Mealie's schemas drop unknown fields instead of rejecting them. A payload
written for an older API therefore **succeeds and does the wrong thing** — a
cookbook created from `tags` plus `requireAllTags` is accepted, has no
filter, and matches every recipe in the library.

That is why `apply` refuses such a payload itself rather than trusting the
API to complain. The same reasoning applies to any future field the API
retires: a guard in the tool, not a hope about the server. See
[decision 0008](../decisions/0008-target-current-mealie.md).

## What the tool sends back

Two filters sit on every write:

- **`WRITE_NOISE`** — fields the API returns but refuses to take back:
  `createdAt`, `updatedAt`, `update_at`, `dateAdded`, `dateUpdated`,
  `householdsWithIngredientFood`, `label`. Every write that starts from a
  `GET` would otherwise carry them, and the backend answers 500 rather than
  422 when it has to validate a shape it never accepts. Stripped recursively
  in `sanitize`, at the single choke point, so no operation can forget.
- **`NOISE`** — fields no mode reads, dropped from what the model sees:
  bookkeeping, per-object timestamps, rendered duplicates of data already
  present. Roughly halves a `ctx recipe` payload; the ratio rises with the
  ingredient count and falls for recipes whose bulk is prose, which is kept
  whole.

## Pagination and rate limits

Collections are fetched with `perPage=200` and every further page is
followed. A page is not the table: an instance with 225 foods answers 200 and
says so in `total_pages`, and an audit that stopped at the first page would
silently work on a subset. Callers that drive pagination themselves — the
index build — pass `page` and keep control.

A 429 is retried up to five times, honouring `Retry-After`, otherwise backing
off. Every other status is raised to the caller.

## Deliberately not used

Shopping lists and their items, meal plan entries, recipe assets and
comments, households, groups and users, and the household stock flags
`householdsWithIngredientFood` / `householdsWithTool`. The rule set names the
same list as out of scope.

Recipe **deletion** is not used and no operation exists for it. See
[decision 0002](../decisions/0002-no-recipe-deletion.md).
