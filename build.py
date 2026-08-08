#!/usr/bin/env python3
"""Rendert den Mealie-Skill fuer die Zielformate und installiert ihn.

  build.py [--target ZIEL] [--out dist]
  build.py --install ZIEL [--into PROJEKT] [--force]

Ziele: claude-code, antigravity, cursor, agents-md

Ohne --install wird nur nach dist/ geschrieben. claude-code und antigravity
installieren ohne --into global (~/.claude bzw. ~/.gemini/config); cursor und
agents-md verlangen --into, weil es kein globales Gegenstueck gibt.
"""
import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "skill")
TARGETS = ("claude-code", "antigravity", "cursor", "agents-md")

RE_AGENT = re.compile(r"^\s*<!-- nur-agent -->\s*$")
RE_STANDALONE = re.compile(r"^\s*<!-- standalone: (.*?) -->\s*$")
TOOL_WORDS = ("index", "audit", "ctx", "usage", "apply", "python")

# (Referenzdatei, Slug fuer Cursor-Regeln); Beschreibungen liefert
# mode_descriptions() aus der Router-Tabelle in SKILL.md.
MODES = [
    ("recipes.md", "recipes"),
    ("foods.md", "foods"),
    ("organizers.md", "organizers"),
    ("cookbooks.md", "cookbooks"),
    ("maintenance.md", "maintenance"),
    ("actions.md", "actions"),
]

_CTX_LONG = ".agents/skills/mealie/scripts/mealie_ctx.py"
MAPPINGS = {
    "claude-code": {".agents/skills/mealie/": ".claude/skills/mealie/"},
    "antigravity": {},
    "cursor": {
        _CTX_LONG: "mealie/scripts/mealie_ctx.py",
        "scripts/mealie_ctx.py": "mealie/scripts/mealie_ctx.py",
        **{"references/" + ref: ".cursor/rules/mealie-" + slug + ".mdc"
           for ref, slug in MODES},
    },
    "agents-md": {
        _CTX_LONG: "mealie/scripts/mealie_ctx.py",
        "scripts/mealie_ctx.py": "mealie/scripts/mealie_ctx.py",
        "references/": "mealie/references/",
    },
}


def render_agent(text):
    """Markerzeilen entfernen, eingeschlossene Zeilen behalten."""
    return "".join(
        line for line in text.splitlines(keepends=True)
        if not RE_AGENT.match(line) and not RE_STANDALONE.match(line))


def _is_tool_line(line):
    words = line.split()
    return (line.startswith("    ") and words
            and words[0] in TOOL_WORDS)


def render_standalone(text):
    """Regionen ersetzen, Werkzeugzeilen streichen."""
    out, lines = [], iter(text.splitlines())
    for line in lines:
        if RE_AGENT.match(line):
            for line in lines:
                m = RE_STANDALONE.match(line)
                if m:
                    out.append(m.group(1))
                    break
            else:
                sys.exit("nur-agent ohne schliessenden standalone:-Kommentar")
            continue
        if RE_STANDALONE.match(line):
            sys.exit("standalone:-Kommentar ohne nur-agent davor")
        if _is_tool_line(line):
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def rewrite(text, mapping):
    """Alle Schluessel in einem Durchlauf ersetzen (laengster zuerst)."""
    if not mapping:
        return text
    pat = re.compile("|".join(
        re.escape(k) for k in sorted(mapping, key=len, reverse=True)))
    return pat.sub(lambda m: mapping[m.group(0)], text)
