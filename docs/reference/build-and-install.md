---
title: Build and install
description: The four targets build.py renders, where each one installs, and what the renderer does to the text on the way.
---

# Build and install

`skill/` is the source. Every target is rendered from it — editing `dist/` is
editing a build artefact that the next build overwrites.

```
build.py [--target TARGET] [--out dist] [--lang LANGUAGE]
build.py --install TARGET [--into PROJECT] [--force] [--lang LANGUAGE]
```

Without `--install` nothing but `dist/` is written.

## The targets

| Target | Installs to | Layout |
|---|---|---|
| `claude-code` | `~` globally, or `--into` a project | `.claude/skills/mealie/`, plus `.claude/commands/mealie.md` |
| `antigravity` | `~/.gemini/config/skills/mealie` globally, or `--into` | `.agents/skills/mealie/`, plus `.agents/workflows/mealie.md` |
| `cursor` | `--into` only | `.cursor/rules/mealie-*.mdc` per mode, `.cursor/commands/mealie.md`, `mealie/scripts/` |
| `agents-md` | `--into` only | a marked block in `AGENTS.md`, plus `mealie/references/` and `mealie/scripts/` |

`cursor` and `agents-md` are project-scoped: there is no global location for
them, so `--into` is required.

For a global `claude-code` install the paths inside the `/mealie` command are
rewritten to absolute `~/.claude/...` paths, so the command works from any
project directory.

`--force` overwrites existing files. `AGENTS.md` is exempt from it in both
directions: only the block between its markers is replaced, whatever else the
file contains. The whole install is checked before the first copy, so a run
installs everything or nothing.

## What the renderer does

**Language substitution.** `${CONTENT_LANG}` is replaced with `--lang`, else
`$MEALIE_LANG`, else `English`. It is the language the model writes recipe
content in — never the project language, which is English everywhere. The
placeholder belongs in `skill/` and in `standalone/prompts/common.txt`; a
hardcoded content language in a prompt is a bug.

**Context markers.** Some passages must differ between an agent that has the
tool and a prompt that does not:

```markdown
<!-- agent-only -->
Run `ctx cookbooks` and read the hit counts.
<!-- standalone: The cookbook list is in the context block above. -->
```

The agent render keeps the enclosed text and drops the marker lines. The
standalone render replaces the region with the text of the `standalone:`
comment, and drops tool invocation lines entirely — the model behind
`optimize.py` calls no tool itself.

**Data placement.** `skill/data/` is copied next to `scripts/` in every
layout, because the script resolves its packs as `../data` relative to
itself.

**Mode descriptions.** The per-mode Cursor rules take their descriptions from
the router table in `SKILL.md`, so the table stays the one place modes are
described.

## Verifying a build

```bash
python3 build.py            # renders every target into dist/
python3 test_build.py       # the whole test suite, no instance needed
```

`test_build.py` checks the rendering as well as the tool: that markers
resolve per target, that the language placeholder is gone, that the
`AGENTS.md` block stays within its size budget, and that the dry run enforces
order, `$ref` resolution and payload shape.

## Uninstalling

Delete the installed tree — `~/.claude/skills/mealie` and
`~/.claude/commands/mealie.md` for a global Claude Code install, the
equivalent paths in a project otherwise. For `agents-md`, remove the block
between the two markers in `AGENTS.md`.

Your working-directory files (`.mealie.env`, the changelog, the house rules)
are untouched by any install and outlive it.
