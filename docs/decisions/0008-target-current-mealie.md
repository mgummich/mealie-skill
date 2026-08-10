---
title: "0008 — Target current Mealie, and refuse outdated payload shapes"
description: One supported API version, and a guard for every field the API silently ignores.
---

# 0008 — Target current Mealie, and refuse outdated payload shapes

**Status:** accepted · **Recorded:** 2026-08-10

## Context

Mealie's API moves. Between 1.x and 2.0, cookbooks moved from the group to
the household and their filter model was replaced entirely — three name lists
and their `requireAll*` switches became one `queryFilterString`.

The first change fails loudly: a 404 on a path that no longer exists. The
second fails silently, because Mealie's schemas **ignore unknown fields
rather than rejecting them**. A cookbook created from the old shape is
accepted, has no filter, and matches every recipe in the library. Nobody
opens a cookbook to check that it is *smaller* than expected.

## Decision

Two parts.

**Target the current release.** Endpoint paths are the ones Mealie 3.22.0
serves, verified against its OpenAPI specification and route sources. Older
instances are supported by editing the `EP` dictionary, which the README and
HOWTO document — not by version detection in the tool.

**Guard the shapes the API ignores.** Where an outdated payload would be
accepted and do the wrong thing, `apply` refuses it before the first write
and names the replacement. `COOKBOOK_LEGACY` and `_guard_cookbooks` are the
first instance.

## Consequences

- One code path, no capability probing, no per-version branches. A tool that
  supported four Mealie versions would be tested against none of them.
- Version drift is caught by re-checking against the OpenAPI spec when
  Mealie releases, not by users discovering it in their data.
- Every future field the API retires needs the same treatment: a guard, not a
  hope that the server complains.
- Users on older Mealie get a 404 and a documented dictionary to edit. That
  is a worse experience than automatic support and a much better one than a
  silent wrong write.

## Alternatives rejected

**Probe and fall back.** For cookbooks it would have restored the endpoint
and not the filter model — the tool would have talked successfully to a
1.x instance and created filterless cookbooks on it. Working halfway is the
failure mode this decision exists to prevent.

**Detect the version once and branch.** Two payload builders, two sets of
guards, one of them exercised by nobody's tests.

## Revisit if

A future Mealie makes a breaking change that a large share of users cannot
upgrade past quickly. Then the answer is a documented compatibility branch,
not silent dual support.
