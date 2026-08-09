#!/usr/bin/env python3
"""Tests for build.py — plain asserts, run with: python3 test_build.py."""
import json
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

# 11. slim(): the noise goes, everything a write needs survives.
recipe: dict = {
    "id": "r1", "userId": "u1", "groupId": "g1", "householdId": "h1",
    "name": "Lentil curry", "slug": "lentil-curry",
    "description": "Quick weeknight curry.",
    "dateAdded": "2024-01-01", "dateUpdated": "2024-02-02",
    "createdAt": "2024-01-01T10:00:00", "updatedAt": "2024-02-02T10:00:00",
    "lastMade": None, "rating": None, "orgURL": "https://example.org/curry",
    "image": "abc", "totalTime": "PT30M", "prepTime": None,
    "recipeServings": 4, "recipeYield": "4 servings",
    "recipeCategory": [{"id": "c1", "name": "Main course", "slug": "main-course",
                        "groupId": "g1"}],
    "tags": [{"id": "t1", "name": "quick", "slug": "quick", "groupId": "g1"}],
    "tools": [],
    "recipeIngredient": [{
        "quantity": 200, "note": "rinsed", "isFood": True,
        "disableAmount": False, "display": "200 g red lentils, rinsed",
        "title": None, "originalText": "200 g red lentils",
        "referenceId": "ref-1",
        "unit": {"id": "u-g", "name": "gram", "pluralName": "grams",
                 "abbreviation": "g", "useAbbreviation": True,
                 "fraction": True, "aliases": [], "createdAt": "2023-01-01",
                 "updatedAt": "2023-01-01"},
        "food": {"id": "f-1", "name": "red lentils", "pluralName": None,
                 "description": "", "labelId": "l1",
                 "label": {"id": "l1", "name": "Pantry"}, "aliases": [],
                 "householdsWithIngredientFood": [], "onHand": False,
                 "createdAt": "2023-01-01", "updatedAt": "2023-01-01"},
    }],
    "recipeInstructions": [{"id": "s1", "title": "", "summary": "",
                            "text": "Simmer the lentils.",
                            "ingredientReferences": [{"referenceId": "ref-1"}]}],
    "notes": [{"title": "Tip", "text": "Better the next day."}],
    "nutrition": {"calories": "420", "fatContent": None},
    "settings": {"public": True, "showNutrition": False},
    "assets": [], "comments": [], "extras": {}, "isOcrRecipe": False,
}
lean = mealie_ctx.slim(recipe, keep_slug=True)

for gone in ("userId", "groupId", "householdId", "dateAdded", "dateUpdated",
             "createdAt", "updatedAt", "settings", "comments", "extras",
             "isOcrRecipe", "lastMade", "rating", "prepTime", "assets",
             "tools"):
    assert gone not in lean, gone
for kept in ("id", "name", "slug", "description", "orgURL", "image",
             "totalTime", "recipeServings", "recipeYield", "recipeCategory",
             "tags", "recipeIngredient", "recipeInstructions", "notes",
             "nutrition"):
    assert kept in lean, kept

ing = lean["recipeIngredient"][0]
assert ing["referenceId"] == "ref-1"            # instructions link to it
assert ing["originalText"] == "200 g red lentils"
assert "display" not in ing                     # rendered duplicate
assert ing["food"] == {"id": "f-1", "name": "red lentils"}, ing["food"]
assert ing["unit"] == {"id": "u-g", "name": "gram", "pluralName": "grams",
                       "abbreviation": "g"}, ing["unit"]
step = lean["recipeInstructions"][0]
assert step["text"] == "Simmer the lentils." and step["id"] == "s1"
assert "summary" not in step
assert step["ingredientReferences"] == [{"referenceId": "ref-1"}]
assert lean["nutrition"] == {"calories": "420"}   # null entries dropped
assert lean["recipeCategory"] == [{"id": "c1", "name": "Main course"}]

# the point of the exercise
before = len(json.dumps(recipe, ensure_ascii=False, indent=1))
after = len(json.dumps(lean, ensure_ascii=False, indent=1))
assert after < before * 0.55, (before, after)
assert mealie_ctx.slim(recipe)                   # without keep_slug: no slug
assert "slug" not in mealie_ctx.slim(recipe)

# 12. apply: per-action slugs, and a rename carries the new slug forward.
calls: list = []


def fake_mreq(method, path, **kw):
    """Record one API call and answer a PATCH with a re-derived slug.

    Args:
        method: HTTP method.
        path: Path below /api.
        **kw: Ignored request payload.

    Returns:
        The recipe as Mealie would return it after the write.
    """
    calls.append((method, path))
    name = (kw.get("json") or {}).get("name")
    slug = path.rsplit("/", 1)[-1]
    return {"slug": "red-lentil-curry" if name else slug}


with tempfile.TemporaryDirectory() as tmp:
    plan = os.path.join(tmp, "actions.json")
    with open(plan, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"actions": [
            {"op": "patch_recipe",
             "payload": {"slug": "lentil-curry", "name": "Red lentil curry"}},
            {"op": "patch_recipe",
             "payload": {"slug": "pumpkin-soup", "description": "Autumn soup."}},
            {"op": "patch_recipe", "payload": {"totalTime": "PT30M"}},
            {"op": "set_image",
             "payload": {"slug": "lentil-curry", "url": "https://e.example/1.jpg"}},
        ]}))
    mealie_ctx.mreq = fake_mreq
    mealie_ctx.INDEX = os.path.join(tmp, "no-index.json")
    args = types.SimpleNamespace(file=plan, slug="fallback-recipe", dry_run=False)
    mealie_ctx.cmd_apply(args)

paths = [p for _, p in calls]
assert paths[0] == "/recipes/lentil-curry", paths          # slug from the payload
assert paths[1] == "/recipes/pumpkin-soup", paths          # a second recipe
assert paths[2] == "/recipes/fallback-recipe", paths       # falls back to --slug
# the rename is followed: the image lands on the new slug, not on a 404
assert paths[3] == "/recipes/red-lentil-curry/image", paths
assert args.slug == "fallback-recipe"                      # never renamed itself

# an action file without any slug aborts instead of writing to nothing
with tempfile.TemporaryDirectory() as tmp:
    plan = os.path.join(tmp, "actions.json")
    with open(plan, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(
            {"actions": [{"op": "patch_recipe", "payload": {"name": "X"}}]}))
    try:
        mealie_ctx.cmd_apply(
            types.SimpleNamespace(file=plan, slug=None, dry_run=False))
        raise AssertionError("patch_recipe without a slug did not abort")
    except SystemExit as e:
        assert "slug" in str(e), e

print("ok")
