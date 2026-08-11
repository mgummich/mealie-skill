---
title: "0009 — No dependencies, because there is no install step"
description: The skill is a copied directory, so its HTTP client is the standard library.
---

# 0009 — No dependencies, because there is no install step

**Status:** accepted · **Recorded:** 2026-08-11

## Context

The skill is installed by copying a directory into a project — that is what
`build.py --install` does, and what unpacking a release archive does. There
is no `pip install`, no virtual environment, no manifest the agent's runtime
reads. The script is then run by whatever `python3` the agent reaches for.

`requests` was a reasonable dependency for a script run from a checkout. For
an installed skill it is a landmine: the first command an agent runs ends in

    ModuleNotFoundError: No module named 'requests'

before a single rule has been read. The user did nothing wrong, the traceback
names nothing they can act on, and the fix — knowing which interpreter the
agent used and installing into it — is harder than the whole task they came
for.

## Decision

No dependencies. All HTTP goes through `fetch()` in `mealie_ctx.py`, a thin
wrapper over `urllib.request` that provides the slice of the `requests`
interface the tool actually uses: `status_code`, `headers`, `text`, `json()`,
`ok`, `raise_for_status()`, and `RequestError`/`ConnectError`/`Timeout`/
`HTTPError` in place of the `requests` exception hierarchy.

A 4xx or 5xx stays an answer rather than an exception, the way `requests`
has it — the callers that turn a failing read into `"?"` or into a skipped
recipe depend on that.

CI installs nothing, and both the CI run and the release smoke test invoke
the script with `python3 -I`, which ignores `PYTHONPATH` and the user site
directory. An import that only works because something else on the machine
supplied it fails there instead of on a user's install.

## Consequences

- Any Python 3.9 runs the skill. Nothing to install, nothing to explain in
  the setup instructions.
- `fetch()` is about a hundred lines this project now maintains, including
  the parts `requests` gets right for free: the charset of a response body,
  a URL with no scheme, a timeout that arrives wrapped in `URLError` on a
  connect and bare on a read.
- Anything `requests` does that is not in that hundred lines has to be
  written before it can be used — sessions, retries beyond the 429 loop,
  multipart uploads, certificate pinning.

## Alternatives rejected

**Guard the import and print an install hint.** Turns a traceback into a
sentence, and still leaves the user to work out which interpreter the agent
used. Every install remains a two-step install.

**Vendor `requests` into the skill directory.** Its own dependency tree
(`urllib3`, `certifi`, `charset-normalizer`, `idna`) ships with it, and the
release archive grows by an order of magnitude to save a wrapper that fits
on one screen.

## Revisit if

The tool needs something the standard library genuinely does not do —
multipart uploads or connection pooling across thousands of requests. Then
the answer is still not a required dependency, but an optional one that
`fetch()` uses when it is importable.
