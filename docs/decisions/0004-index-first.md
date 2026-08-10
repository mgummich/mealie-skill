---
title: "0004 — An index, not a loop over the API"
description: One pass over the library, then every evaluation reads the file.
---

# 0004 — An index, not a loop over the API

**Status:** accepted · **Recorded:** 2026-08-10

## Context

Nearly every question worth asking about a library is a question about all of
it. How many ingredient lines link to a food. Which foods nothing uses. Which
recipes look like duplicates. Which source URLs are dead.

Answered naively, each of those is a full pass over the API — and a model
that is allowed to loop over recipes will do exactly that, once per question,
happily, for an hour.

## Decision

One pass builds `.mealie_index.json`: a summary record per recipe. Every
audit, every usage count, every duplicate check reads that file. Nothing
builds its own loop over the API.

The index is built on the first `audit`, deleted after every writing `apply`,
and rebuilt on demand with `--refresh`.

## Consequences

- Audits are instant after the first one, so running three of them before
  planning is normal rather than expensive.
- The index is a snapshot, and a stale one lies. Deleting it after a writing
  run is what keeps the lie short-lived.
- Guards can be checked against it — `delete_food` is refused while the index
  shows a recipe using the object, and refused *without* an index, because
  then the check cannot be made.
- Adding a field to an audit means adding it to the index, which means
  raising `INDEX_VERSION`. An older index is rebuilt rather than audited on
  fields it does not carry, which would report zero and look like a clean
  result.
- A recipe the instance fails to serialise is skipped and recorded, not
  fatal. One unserialisable recipe used to cost the whole build.

## Alternatives rejected

**Query the API per question.** Slow, rate-limited, and it makes the
duplicate check quadratic in requests.

**Cache whole recipes.** Larger than the corpus needs to be for these
questions, and it invites reading stale content into a write.

**Keep the index in memory per run.** Then two consecutive audits pay for it
twice, and the guard on deletions has nothing to consult when the plan is
applied in a later process.
