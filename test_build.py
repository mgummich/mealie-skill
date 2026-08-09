#!/usr/bin/env python3
"""Tests for build.py — plain asserts, run with: python3 test_build.py."""
import os
import sys
import tempfile
import types

import build


def load_ctx():
    """Import mealie_ctx from skill/scripts without requests installed.

    Returns:
        The imported module; its HTTP calls are never exercised here.
    """
    sys.modules.setdefault("requests", types.ModuleType("requests"))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "skill", "scripts"))
    import mealie_ctx
    return mealie_ctx

# 1. Tool lines disappear in the standalone rendering, the rest stays line for line.
src = "Head\n\n    audit foods          # or: audit units\n\nText\n"
assert build.render_standalone(src) == "Head\n\n\nText\n"
assert build.render_agent(src) == src

# 2. Region markers: the agent keeps the content without markers, standalone
#    replaces it.
src = ("Before\n<!-- agent-only -->\nLine A\nLine B\n"
       "<!-- standalone: Replacement. -->\nAfter\n")
assert build.render_agent(src) == "Before\nLine A\nLine B\nAfter\n"
assert build.render_standalone(src) == "Before\nReplacement.\nAfter\n"

# 3. Unpaired markers abort.
for bad in ("<!-- agent-only -->\nx\n", "x\n<!-- standalone: y -->\n"):
    try:
        build.render_standalone(bad)
        raise AssertionError("no abort for: " + bad)
    except SystemExit:
        pass

# 4. rewrite: single pass, no cascading, longest key first.
m = build.MAPPINGS["cursor"]
line = "python .agents/skills/mealie/scripts/mealie_ctx.py apply"
assert build.rewrite(line, m) == "python mealie/scripts/mealie_ctx.py apply"
assert build.rewrite("scripts/mealie_ctx.py", m) == "mealie/scripts/mealie_ctx.py"
assert build.rewrite("references/foods.md", m) == ".cursor/rules/mealie-foods.mdc"
assert (build.rewrite("references/foods.md", build.MAPPINGS["agents-md"])
        == "mealie/references/foods.md")

# 5. AGENTS.md merge: idempotent, foreign content survives.
block = "Router v1\n"
fresh = build.merge_agents_md(None, block)
assert fresh == "<!-- mealie:begin -->\nRouter v1\n<!-- mealie:end -->\n"
assert build.merge_agents_md(fresh, block) == fresh          # idempotent
with_context = "# Project\n\n" + fresh + "\nFooter\n"
v2 = build.merge_agents_md(with_context, "Router v2\n")
assert "Router v2" in v2 and "Router v1" not in v2
assert v2.startswith("# Project\n") and v2.rstrip().endswith("Footer")
without_markers = "# Project\n"
appended = build.merge_agents_md(without_markers, block)
assert appended.startswith("# Project\n")
assert appended.rstrip().endswith("<!-- mealie:end -->")

# 6. AGENTS.md merge edge cases: empty, begin without end, marker in prose.
assert build.merge_agents_md("", block) == fresh
assert build.merge_agents_md("  \n", block) == fresh
try:
    build.merge_agents_md("<!-- mealie:begin -->\nbroken\n", block)
    raise AssertionError("no abort for begin without end")
except SystemExit:
    pass
prose = ("Everything between <!-- mealie:begin --> and the end belongs to the "
         "skill.\n\n" + fresh + "\nFooter\n")
v3 = build.merge_agents_md(prose, "Router v3\n")
assert v3.startswith("Everything between")        # prose untouched
assert "Router v3" in v3 and "Router v1" not in v3
assert v3.rstrip().endswith("Footer")

# 7. Standalone markers can keep a tool line (--check-urls and the like).
src = ("<!-- agent-only -->\n    audit links\n    audit links --check-urls\n"
       "<!-- standalone:     audit links --check-urls -->\n")
assert build.render_standalone(src) == "    audit links --check-urls\n"

# 8. Content language: the placeholder is substituted in both renderings and
#    inside a standalone replacement, and the default applies without --lang.
src = ("All content in ${CONTENT_LANG}.\n<!-- agent-only -->\nx\n"
       "<!-- standalone: Prose in ${CONTENT_LANG}. -->\n")
assert build.render_agent(src, "Deutsch") == "All content in Deutsch.\nx\n"
assert (build.render_standalone(src, "Deutsch")
        == "All content in Deutsch.\nProse in Deutsch.\n")
assert build.set_language("in ${CONTENT_LANG}") == "in " + build.DEFAULT_LANG
assert build.DEFAULT_LANG
assert build.LANG_TOKEN not in build.render_agent(src)

# 9. No placeholder survives into a rendered target.
for name in ("SKILL.md", "workflow.md"):
    assert build.LANG_TOKEN not in build.render_agent(build._read(name), "X")
for ref, _ in build.MODES:
    text = build._read("references", ref)
    assert build.LANG_TOKEN not in build.render_agent(text, "X")
    assert build.LANG_TOKEN not in build.render_standalone(text, "X")

# 10. Credentials: env file parsing, .env fallback and precedence.
mealie_ctx = load_ctx()

parsed = mealie_ctx.parse_env(
    "# comment\n\nexport MEALIE_URL=https://m.example.org/ \n"
    'MEALIE_TOKEN="tok=en"\nOTHER=ignored\nbroken line\n')
assert parsed == {"MEALIE_URL": "https://m.example.org/",
                  "MEALIE_TOKEN": "tok=en"}, parsed

with tempfile.TemporaryDirectory() as tmp:
    own = os.path.join(tmp, ".mealie.env")
    dotenv = os.path.join(tmp, ".env")
    with open(own, "w", encoding="utf-8") as fh:
        fh.write("MEALIE_TOKEN=own-token\n")
    with open(dotenv, "w", encoding="utf-8") as fh:
        fh.write("MEALIE_URL=https://from-dotenv\nMEALIE_TOKEN=dotenv-token\n")
    mealie_ctx.ENV_FILE, mealie_ctx.ENV_FALLBACK = own, dotenv
    for key in ("MEALIE_URL", "MEALIE_TOKEN"):
        os.environ.pop(key, None)

    cfg = mealie_ctx.read_cfg()                       # .mealie.env wins over .env
    assert cfg == {"MEALIE_URL": "https://from-dotenv",
                   "MEALIE_TOKEN": "own-token"}, cfg

    os.environ["MEALIE_TOKEN"] = "env-token"          # the environment wins
    assert mealie_ctx.read_cfg()["MEALIE_TOKEN"] == "env-token"

    mealie_ctx.ENV_FILE = os.path.join(tmp, "gone")   # a .env alone is enough
    del os.environ["MEALIE_TOKEN"]
    assert mealie_ctx.read_cfg()["MEALIE_TOKEN"] == "dotenv-token"

    mealie_ctx.ENV_FALLBACK = os.path.join(tmp, "gone-too")
    try:
        mealie_ctx.conn()
        raise AssertionError("conn() did not abort without credentials")
    except SystemExit as e:
        assert "setup" in str(e), e

print("ok")
