---
title: Decisions
description: Why the tool is shaped this way — one record per decision, with the alternative it rejected.
---

# Decisions

Short records of the choices that shaped the tool, each with the alternative
it rejected and what would have to change for the decision to be revisited.
They are written for whoever changes this next — including a model reading
`CLAUDE.md` — because a constraint whose reason is lost gets removed by the
first person who finds it inconvenient.

<ol class="rail">
  <li><span class="n">0001</span>
    <div><a href="0001-three-phases.html">Three phases, and an approval gate</a>
    <p>Rejected: write immediately and undo afterwards.</p></div></li>
  <li><span class="n">0002</span>
    <div><a href="0002-no-recipe-deletion.html">No operation for deleting a recipe</a>
    <p>Rejected: delete behind a confirmation.</p></div></li>
  <li><span class="n">0003</span>
    <div><a href="0003-one-source-many-frontends.html">One rule set, rendered into every frontend</a>
    <p>Rejected: maintain each frontend by hand.</p></div></li>
  <li><span class="n">0004</span>
    <div><a href="0004-index-first.html">An index, not a loop over the API</a>
    <p>Rejected: query the API once per question.</p></div></li>
  <li><span class="n">0005</span>
    <div><a href="0005-guards-refuse-not-warn.html">Guards refuse; they do not warn</a>
    <p>Rejected: a <code>--force</code> flag.</p></div></li>
  <li><span class="n">0006</span>
    <div><a href="0006-data-not-prose.html">Mechanical rules are data, not prompt text</a>
    <p>Rejected: the whole checklist in the prompt.</p></div></li>
  <li><span class="n">0007</span>
    <div><a href="0007-changelog-before-write.html">The before-state is logged before the next action</a>
    <p>Rejected: a rollback command.</p></div></li>
  <li><span class="n">0008</span>
    <div><a href="0008-target-current-mealie.html">Target current Mealie, refuse outdated shapes</a>
    <p>Rejected: probe the version and fall back.</p></div></li>
  <li><span class="n">0009</span>
    <div><a href="0009-no-dependencies.html">No dependencies, because there is no install step</a>
    <p>Rejected: guard the import and print an install hint.</p></div></li>
</ol>

0001 to 0008 recorded 2026-08-10, describing decisions made over the life of
the project rather than on that date.
