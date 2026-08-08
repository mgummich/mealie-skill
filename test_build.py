#!/usr/bin/env python3
"""Tests fuer build.py — reine asserts, Aufruf: python3 test_build.py."""
import build

# 1. Werkzeugzeilen entfallen im Standalone-Rendering, Rest bleibt zeilengleich.
src = "Kopf\n\n    audit foods          # oder: audit units\n\nText\n"
assert build.render_standalone(src) == "Kopf\n\n\nText\n"
assert build.render_agent(src) == src

# 2. Regionsmarker: Agent behaelt Inhalt ohne Marker, Standalone ersetzt.
src = ("Vorher\n<!-- nur-agent -->\nZeile A\nZeile B\n"
       "<!-- standalone: Ersatz. -->\nNachher\n")
assert build.render_agent(src) == "Vorher\nZeile A\nZeile B\nNachher\n"
assert build.render_standalone(src) == "Vorher\nErsatz.\nNachher\n"

# 3. Unpaarige Marker brechen ab.
for bad in ("<!-- nur-agent -->\nx\n", "x\n<!-- standalone: y -->\n"):
    try:
        build.render_standalone(bad)
        raise AssertionError("kein Abbruch bei: " + bad)
    except SystemExit:
        pass

# 4. rewrite: Single-Pass, kein Kaskadieren, laengster Schluessel zuerst.
m = build.MAPPINGS["cursor"]
line = "python .agents/skills/mealie/scripts/mealie_ctx.py apply"
assert build.rewrite(line, m) == "python mealie/scripts/mealie_ctx.py apply"
assert build.rewrite("scripts/mealie_ctx.py", m) == "mealie/scripts/mealie_ctx.py"
assert build.rewrite("references/foods.md", m) == ".cursor/rules/mealie-foods.mdc"
assert (build.rewrite("references/foods.md", build.MAPPINGS["agents-md"])
        == "mealie/references/foods.md")

# 5. AGENTS.md-Merge: idempotent, fremder Inhalt ueberlebt.
block = "Router v1\n"
neu = build.merge_agents_md(None, block)
assert neu == "<!-- mealie:begin -->\nRouter v1\n<!-- mealie:end -->\n"
assert build.merge_agents_md(neu, block) == neu          # idempotent
mit_umfeld = "# Projekt\n\n" + neu + "\nFusszeile\n"
v2 = build.merge_agents_md(mit_umfeld, "Router v2\n")
assert "Router v2" in v2 and "Router v1" not in v2
assert v2.startswith("# Projekt\n") and v2.rstrip().endswith("Fusszeile")
ohne_marker = "# Projekt\n"
angehaengt = build.merge_agents_md(ohne_marker, block)
assert angehaengt.startswith("# Projekt\n")
assert angehaengt.rstrip().endswith("<!-- mealie:end -->")

print("ok")
