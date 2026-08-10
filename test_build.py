#!/usr/bin/env python3
"""Tests for build.py — plain asserts, run with: python3 test_build.py."""
import json
import os
import re
import sys
import tempfile
import types

import build


class FakeRequestException(Exception):
    """Stand-in for requests.RequestException, the base of every HTTP error."""


class FakeHTTPError(FakeRequestException):
    """Stand-in for requests.HTTPError, which carries the response."""

    def __init__(self, *args, response=None):
        """Store the response the way requests does.

        Args:
            *args: Passed to Exception.
            response: The object with the status_code.
        """
        super().__init__(*args)
        self.response = response


def load_ctx():
    """Import mealie_ctx from skill/scripts without requests installed.

    Returns:
        The imported module; its HTTP calls are never exercised here.
    """
    stub = types.ModuleType("requests")
    stub.HTTPError = FakeHTTPError    # type: ignore[attr-defined]
    stub.RequestException = FakeRequestException  # type: ignore[attr-defined]
    sys.modules.setdefault("requests", stub)
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
    mealie_ctx.CHANGELOG = os.path.join(tmp, "changelog.jsonl")
    args = types.SimpleNamespace(file=plan, slug="fallback-recipe", dry_run=False)
    mealie_ctx.cmd_apply(args)
    logged = [json.loads(x) for x in
              open(mealie_ctx.CHANGELOG, encoding="utf-8")]

writes = [p for m, p in calls if m != "GET"]
assert writes[0] == "/recipes/lentil-curry", calls         # slug from the payload
assert writes[1] == "/recipes/pumpkin-soup", calls         # a second recipe
assert writes[2] == "/recipes/fallback-recipe", calls      # falls back to --slug
# the rename is followed: the image lands on the new slug, not on a 404
assert writes[3] == "/recipes/red-lentil-curry/image", calls
assert args.slug == "fallback-recipe"                      # never renamed itself
# every patch reads the recipe first, so the changelog holds what it overwrote
assert calls[0] == ("GET", "/recipes/lentil-curry"), calls
assert [r["op"] for r in logged] == ["patch_recipe"] * 3 + ["set_image"]
assert logged[1]["before"] == {"description": None}, logged[1]
assert logged[1]["target"] == {"slug": "pumpkin-soup"}, logged[1]

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

# 12b. writes are sanitized, reads paginate only on collections, and a
#      rename into a name another food holds aborts before the first write.
dirty = {"name": "Flour", "description": "", "createdAt": "2024-01-01",
         "label": {"id": "l1"}, "labelId": "l1",
         "aliases": [{"name": "wheat flour", "updatedAt": "2024-01-01"}]}
clean = mealie_ctx.sanitize(dirty)
assert "createdAt" not in clean and "label" not in clean, clean
assert clean["labelId"] == "l1"                  # the id survives, the object goes
assert clean["description"] == ""                # empty is an answer, not noise
assert clean["aliases"] == [{"name": "wheat flour"}], clean["aliases"]

seen: list = []


def spy_mreq(method, path, **kw):
    """Record method, path and params, and answer with an empty envelope."""
    seen.append((method, path, kw.get("params")))
    return {"items": []}


mealie_ctx.mreq = spy_mreq
mealie_ctx.mget("/foods")
mealie_ctx.mget("/foods/f-1")
assert seen[0][2] == {"perPage": 200}, seen[0]   # a collection paginates
assert seen[1][2] == {}, seen[1]                 # a single object does not

# a page is not the table: an instance with 225 foods answers 200 and says
# so, and every audit worked on the subset until this followed the rest
pages: list = []


def paged_mreq(method, path, **kw):
    """Serve two pages of a 225-entry collection."""
    page = (kw.get("params") or {}).get("page", 1)
    pages.append(page)
    items = [{"id": f"f{i}"} for i in range(25 if page == 2 else 200)]
    return {"items": items, "total": 225, "total_pages": 2, "page": page}


mealie_ctx.mreq = paged_mreq
assert len(mealie_ctx.mget("/foods")) == 225, "second page not followed"
assert pages == [1, 2], pages
pages.clear()
# a caller driving pagination itself keeps control (build_index does)
assert len(mealie_ctx.mget("/foods", page=1)) == 200
assert pages == [1], pages

foods = [{"id": "f-1", "name": "Flour", "aliases": []},
         {"id": "f-2", "name": "Wheat flour",
          "aliases": [{"name": "Type 550"}]}]
mealie_ctx._TAKEN.clear()
mealie_ctx._TAKEN["foods"] = foods
assert mealie_ctx.taken("foods", "f-1", {"name": "wheat FLOUR "}) == "wheat flour"
assert mealie_ctx.taken("foods", "f-1", {"aliases": [{"name": "Type 550"}]})
assert mealie_ctx.taken("foods", "f-2", {"name": "Wheat flour"}) is None  # itself
assert mealie_ctx.taken("foods", "f-1", {"name": "Rye flour"}) is None
# an object an earlier merge removes does not hold its name any more: taking
# the loser's name over as an alias is what the rules ask for
assert mealie_ctx.taken("foods", "f-1", {"aliases": [{"name": "Wheat flour"}]},
                        ignore={"f-2"}) is None

with tempfile.TemporaryDirectory() as tmp:
    plan = os.path.join(tmp, "actions.json")
    with open(plan, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"actions": [
            {"op": "update_food",
             "payload": {"id": "f-1", "name": "Wheat flour"}}]}))
    try:
        mealie_ctx.cmd_apply(
            types.SimpleNamespace(file=plan, slug=None, dry_run=False))
        raise AssertionError("a rename into an existing name did not abort")
    except SystemExit as e:
        assert "Merge" in str(e), e

# 12c. A patch that shortens a list field is a deletion: Mealie replaces the
#      field instead of merging, so the guard stops it before the write.
def run_apply(actions, mreq, tmp, **kw):
    """Run cmd_apply against a fake instance in a temporary directory.

    Args:
        actions: The action list, as it would sit in actions.json.
        mreq: Replacement for mealie_ctx.mreq.
        tmp: Directory for the plan, the index and the changelog.
        **kw: Overrides for the parsed arguments, e.g. dry_run.

    Returns:
        The changelog as a list of decoded records.
    """
    plan = os.path.join(tmp, "actions.json")
    with open(plan, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"actions": actions}))
    mealie_ctx.mreq = mreq
    mealie_ctx.INDEX = kw.pop("index", os.path.join(tmp, "no-index.json"))
    mealie_ctx.CHANGELOG = os.path.join(tmp, "changelog.jsonl")
    args = {"file": plan, "slug": None, "dry_run": False, **kw}
    mealie_ctx.cmd_apply(types.SimpleNamespace(**args))
    if not os.path.exists(mealie_ctx.CHANGELOG):
        return []
    return [json.loads(x) for x in
            open(mealie_ctx.CHANGELOG, encoding="utf-8")]


def three_line_recipe(method, path, **kw):
    """Answer every GET with a recipe of three ingredient lines."""
    calls.append((method, path))
    return {"slug": "curry", "recipeIngredient": [{"a": 1}, {"a": 2}, {"a": 3}]}


shrink = [{"op": "patch_recipe",
           "payload": {"slug": "curry", "recipeIngredient": [{"a": 1}]}}]
with tempfile.TemporaryDirectory() as tmp:
    calls = []
    try:
        run_apply(shrink, three_line_recipe, tmp)
        raise AssertionError("a shortening patch_recipe did not abort")
    except SystemExit as e:
        assert "recipeIngredient" in str(e) and "deleted" in str(e), e
    assert not [m for m, _ in calls if m != "GET"], calls   # nothing was written

# ... unless the plan says the removal is meant.
with tempfile.TemporaryDirectory() as tmp:
    calls = []
    logged = run_apply([{**shrink[0], "replace": True}], three_line_recipe, tmp)
    assert ("PATCH", "/recipes/curry") in calls, calls
    assert len(logged[0]["before"]["recipeIngredient"]) == 3, logged

# 12d. The same guards run under --dry-run. Without a connection the
#      structural checks still pass and what could not be checked is named.
def offline(method, path, **kw):
    """Fail the way requests does when the instance is unreachable."""
    raise mealie_ctx.requests.RequestException("connection refused")


with tempfile.TemporaryDirectory() as tmp:
    assert run_apply(shrink, offline, tmp, dry_run=True) == []   # nothing logged

# 12e. A merge is verified by reading the affected recipes back: Mealie
#      answers a merge that lost references exactly like one that worked.
with tempfile.TemporaryDirectory() as tmp:
    index = os.path.join(tmp, "index.json")
    with open(index, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"built": 0, "failed": [], "recipes": [
            {"slug": "curry", "foods": ["f-old"], "units": [], "tags": [],
             "tools": [], "categories": []}]}))

    def stale_merge(method, path, **kw):
        """Serve the source food, accept the merge, and leave the recipe as is."""
        calls.append((method, path))
        if path.startswith("/recipes/"):
            return {"slug": "curry",
                    "recipeIngredient": [{"food": {"id": "f-old"}}]}
        return {"id": "f-old", "name": "Tomatoes"}

    calls = []
    try:
        run_apply([{"op": "merge_food",
                    "payload": {"from": "f-old", "to": "f-new"}}],
                  stale_merge, tmp, index=index)
        raise AssertionError("an unverified merge did not abort")
    except SystemExit as e:
        assert "still reference the source" in str(e), e
    # the loser's record is in the changelog before the merge runs
    logged = [json.loads(x) for x in
              open(mealie_ctx.CHANGELOG, encoding="utf-8")]
    assert logged[0]["before"]["source"]["name"] == "Tomatoes", logged

# 12f. A failure mid-run reports how far it got instead of unwinding blindly.
with tempfile.TemporaryDirectory() as tmp:
    def die_on_second(method, path, **kw):
        """Answer the first recipe, fail on the second."""
        calls.append((method, path))
        if path.endswith("/pumpkin-soup"):
            raise mealie_ctx.requests.HTTPError("500", response=None)
        return {"slug": "curry"}

    calls = []
    try:
        run_apply([{"op": "patch_recipe",
                    "payload": {"slug": "curry", "totalTime": "PT30M"}},
                   {"op": "patch_recipe",
                    "payload": {"slug": "pumpkin-soup", "totalTime": "PT20M"}}],
                  die_on_second, tmp)
        raise AssertionError("a failing write did not abort the run")
    except SystemExit as e:
        assert e.code == 1, e
    logged = [json.loads(x) for x in
              open(mealie_ctx.CHANGELOG, encoding="utf-8")]
    assert [r["target"]["slug"] for r in logged] == ["curry"], logged

# 12g. convert: the density table decides, and nothing is estimated.
assert mealie_ctx.parse_amount("1 1/2 cups flour")[0] == 1.5
assert mealie_ctx.parse_amount("½ cup sugar")[0] == 0.5
assert mealie_ctx.parse_amount("2-3 cups rice")[0] == 2      # a range: the lower
assert mealie_ctx.parse_amount("a pinch of salt")[0] is None
assert mealie_ctx.match_unit("cups flour", {"cup": ["cup", "cups"]}) == (
    "cup", "flour")
assert mealie_ctx.match_unit("instant yeast", {"inch": ["in"]})[0] is None

conv = mealie_ctx.load_data("conversions.json", "en")
# 8 oz: step 10 stays inside the 2 % limit, 1 oz takes the rules' own figure
assert mealie_ctx.convert_line("8 oz", conv)["text"] == "230 g"
assert mealie_ctx.convert_line("1 oz", conv)["text"] == "28 g"
assert mealie_ctx.convert_line("1 cup plain flour", conv)["text"] == \
    "120 g plain flour"
assert mealie_ctx.convert_line("1 cup honey", conv)["text"] == "340 g honey"
assert mealie_ctx.convert_line("1 cup water", conv)["text"] == "240 ml water"
assert mealie_ctx.convert_line("9 inch", conv)["text"] == "23 cm"
assert mealie_ctx.convert_line("350 F", conv)["text"] == "175 °C"
assert mealie_ctx.convert_line("350 F", conv, fan=True)["text"] == \
    "175 °C (155 °C fan)"
# every conversion carries the note that makes it checkable and stops a
# second pass converting it again
assert mealie_ctx.convert_line("1 cup plain flour", conv)["note"] == \
    "Original: 1 cup plain flour"
# a food the table does not know is left alone, never estimated
assert "review" in mealie_ctx.convert_line("1 cup quinoa", conv)
# tbsp and tsp are metrically defined, so they are not converted at all
assert "keep" in mealie_ctx.convert_line("2 tbsp olive oil", conv)
# the German pack converts German food names
de = mealie_ctx.load_data("conversions.json", "de")
assert mealie_ctx.convert_line("1 Tasse Mehl", de)["text"] == "120 g Mehl"

# 12h. The plan lint catches the slips the rule set names, and only a
#      non-metric unit is fatal.
found = mealie_ctx.lint_actions([
    {"op": "create_unit", "payload": {"name": "cup", "abbreviation": "c"}},
    {"op": "create_food", "payload": {"name": "Cumin"}},
    {"op": "create_tag", "payload": {"name": "quick and easy"}},
    {"op": "create_label", "payload": {"name": "Spices", "color": "#959595"}},
    {"op": "patch_recipe",
     "payload": {"slug": "curry", "notes": [{"title": "Info", "text": "x"}]}},
], "en")
levels = {level for level, _ in found}
assert levels == {"ERROR", "WARN"}, found
assert sum(1 for level, _ in found if level == "ERROR") == 1, found
assert any("not metric" in m for _, m in found), found
assert any("no label" in m for _, m in found), found
assert any("two concepts" in m for _, m in found), found
assert any("default colour" in m for _, m in found), found
assert any("vocabulary" in m for _, m in found), found
assert mealie_ctx.lint_actions(
    [{"op": "create_food",
      "payload": {"name": "cumin", "labelId": "l1", "description": "Seed.",
                  "aliases": [{"name": "jeera"}]}}], "en") == []

# a plan that creates a non-metric unit is refused outright
with tempfile.TemporaryDirectory() as tmp:
    try:
        run_apply([{"op": "create_unit", "payload": {"name": "cup"}}],
                  fake_mreq, tmp, dry_run=True)
        raise AssertionError("a non-metric unit did not abort the plan")
    except SystemExit as e:
        assert "non-negotiable" in str(e), e

# 12j. The seed packs are the fixed vocabularies of the rule set, and they
#      have to survive the rule set's own lint.
for lang, count in (("en", 25), ("de", 29)):
    labels = mealie_ctx.load_data("labels.json", lang)
    assert len(labels["labels"]) == 29, lang
    assert len({x["color"] for x in labels["labels"]}) == 29, lang
    assert sorted(labels["shopOrder"]) == sorted(
        x["name"] for x in labels["labels"]), lang
    assert len(mealie_ctx.load_data("units.json", lang)["units"]) == count

    seeded, skipped = mealie_ctx.seed_actions("labels", lang)
    assert len(seeded) == 29 and not skipped, lang
    units, _ = mealie_ctx.seed_actions("units", lang)
    problems = [(lvl, m) for lvl, m in
                mealie_ctx.lint_actions(seeded + units, lang)
                if lvl == "ERROR"]
    assert not problems, problems
    # exactly one warning survives, and it is the documented ambiguity
    warns = [m for lvl, m in mealie_ctx.lint_actions(units, lang)
             if lvl == "WARN"]
    assert all("stick" in m.lower() for m in warns), warns

# what the instance already holds is skipped, by name and by alias
existing = [{"name": "Vegetables"}]
seeded, skipped = mealie_ctx.seed_actions("labels", "en", existing)
assert len(seeded) == 28 and skipped == ["Vegetables"], skipped
seeded, skipped = mealie_ctx.seed_actions(
    "units", "en", [{"name": "Gramme", "aliases": [{"name": "gr"}]}])
assert any("gram" in s for s in skipped), skipped   # caught on the alias
assert not any(x["payload"]["name"] == "gram" for x in seeded), seeded

# 12m. delete_food is not a merge: it strips the food from every recipe that
#      used it, so it is refused while anything still references it.
with tempfile.TemporaryDirectory() as tmp:
    index = os.path.join(tmp, "index.json")
    with open(index, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"built": 0, "version": mealie_ctx.INDEX_VERSION,
                             "failed": [], "recipes": [
            {"slug": "curry", "foods": ["f-used"], "units": [], "tags": [],
             "tools": [], "categories": []}]}))

    def deleting(method, path, **kw):
        """Serve the object being deleted and record the call."""
        calls.append((method, path))
        return {"id": path.rsplit("/", 1)[-1], "name": "Test artefact"}

    calls = []
    try:
        run_apply([{"op": "delete_food", "payload": {"id": "f-used"}}],
                  deleting, tmp, index=index)
        raise AssertionError("deleting a referenced food did not abort")
    except SystemExit as e:
        assert "still use it" in str(e) and "curry" in str(e), e
    assert not calls, calls                       # aborted before any request

    # an orphan goes, and the record it deleted is in the changelog
    calls = []
    logged = run_apply([{"op": "delete_food", "payload": {"id": "f-orphan"}}],
                       deleting, tmp, index=index)
    assert ("DELETE", "/foods/f-orphan") in calls, calls
    assert logged[0]["before"]["name"] == "Test artefact", logged

    # without an index there is nothing to check against, so it refuses
    try:
        run_apply([{"op": "delete_unit", "payload": {"id": "u-1"}}],
                  deleting, tmp)
        raise AssertionError("deleting without an index did not abort")
    except SystemExit as e:
        assert "index" in str(e), e

# labels are organizers to this format; an unknown kind is named, not a
# KeyError halfway through the run
with tempfile.TemporaryDirectory() as tmp:
    calls = []
    run_apply([{"op": "update_organizer",
                "payload": {"kind": "labels", "id": "l1",
                            "color": "#43A047"}}], deleting, tmp)
    assert ("PUT", "/groups/labels/l1") in calls, calls
    try:
        run_apply([{"op": "delete_organizer",
                    "payload": {"kind": "recipes", "id": "x"}}],
                  deleting, tmp)
        raise AssertionError("an unknown organizer kind did not abort")
    except SystemExit as e:
        assert "unknown kind" in str(e), e

# 12l. Audit metrics: the findings the rule set calls hard errors.
foods = [{"id": "f1", "name": "lentils", "aliases": [{"name": "puy"}]},
         {"id": "f2", "name": "Tomato", "pluralName": "Tomatoes",
          "aliases": [{"name": "PUY"}]},
         {"id": "f3", "name": "tomatoes", "aliases": []}]
clash = mealie_ctx.alias_collisions(foods)
assert clash["puy"] == ["Tomato", "lentils"], clash      # case-insensitive
assert clash["tomatoes"] == ["Tomato", "tomatoes"], clash  # name vs plural
assert "lentils" not in clash

units = [{"id": "u1", "name": "litre", "abbreviation": "l"},
         {"id": "u2", "name": "leaf", "abbreviation": "L"},
         {"id": "u3", "name": "gram", "abbreviation": "g"}]
assert mealie_ctx.abbrev_collisions(units) == {"l": ["leaf", "litre"]}

conv = mealie_ctx.load_data("conversions.json", "en")
bad = mealie_ctx.non_metric(
    [{"id": "u1", "name": "cup"}, {"id": "u2", "name": "Ounces"},
     {"id": "u3", "name": "gram"}, {"id": "u4", "name": "tin"}], conv)
assert [u["name"] for u in bad] == ["cup", "Ounces"], bad
assert mealie_ctx._share(13, 16) == "13 (81 %)"
assert mealie_ctx._share(0, 0) == "0"

# an index written before the current fields is rebuilt, not audited blind
with tempfile.TemporaryDirectory() as tmp:
    mealie_ctx.INDEX = os.path.join(tmp, ".mealie_index.json")
    with open(mealie_ctx.INDEX, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"built": 0, "recipes": [], "failed": []}))
    rebuilt = {"n": 0}

    def fake_build():
        """Stand in for build_index and count the calls."""
        rebuilt["n"] += 1
        return {"built": 1, "version": mealie_ctx.INDEX_VERSION,
                "recipes": [], "failed": []}

    real_build, mealie_ctx.build_index = mealie_ctx.build_index, fake_build
    mealie_ctx.load_index()                       # no version: rebuilds
    assert rebuilt["n"] == 1
    with open(mealie_ctx.INDEX, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"built": 0, "version": mealie_ctx.INDEX_VERSION,
                             "recipes": [], "failed": []}))
    mealie_ctx.load_index()                       # current version: kept
    assert rebuilt["n"] == 1
    mealie_ctx.build_index = real_build

# 12k. House rules: a decision nobody wrote down is remade differently next
#      month, so the file is the record and the tool never rewrites it.
with tempfile.TemporaryDirectory() as tmp:
    mealie_ctx.HOUSE_FILE = os.path.join(tmp, ".mealie.rules.json")
    assert mealie_ctx.read_house() is None
    assert mealie_ctx.house_line() is None
    mealie_ctx.cmd_rules(types.SimpleNamespace(init=True, force=False,
                                               lang="en"))
    house = mealie_ctx.read_house()
    assert house["locale"] == "en-GB" and house["categoryAxis"] == "dish type"
    assert house["defaultResolutions"]["pepper"] == "black pepper [ground]"
    assert "locale=en-GB" in mealie_ctx.house_line()
    try:
        mealie_ctx.cmd_rules(types.SimpleNamespace(init=True, force=False,
                                                   lang="en"))
        raise AssertionError("init overwrote an existing house file")
    except SystemExit as e:
        assert "--force" in str(e), e
    de = mealie_ctx.load_data("house.json", "de")
    assert de["defaultResolutions"]["Pfeffer"] == "schwarzer Pfeffer [gemahlen]"

# 12i. The data the script reads ships with it: it resolves ../data from its
#      own location, so the two stay siblings in every target layout.
with tempfile.TemporaryDirectory() as tmp:
    for target, script in (
            ("claude-code", ".claude/skills/mealie/scripts/mealie_ctx.py"),
            ("cursor", "mealie/scripts/mealie_ctx.py"),
            ("agents-md", "mealie/scripts/mealie_ctx.py")):
        built = build.build_target(target, tmp)
        beside = os.path.join(os.path.dirname(os.path.join(built, script)),
                              "..", "data", "en", "conversions.json")
        assert os.path.exists(os.path.normpath(beside)), target

# 12n. The standalone frontend: every mode has a prompt, every prompt a
#      mode, and no rendered prompt tells the model to run a tool it has
#      no access to.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "standalone"))
optimize_src = open(os.path.join("standalone", "optimize.py"),
                    encoding="utf-8").read()
prompts = set(re.findall(r'"(\w+)": "([\w.]+\.md)"', optimize_src))
mapped = {ref for _, ref in prompts}
for ref, _ in build.MODES:
    if ref in ("actions.md", "mcp.md"):
        continue                                  # not modes of the frontend
    assert ref in mapped, f"{ref} has no standalone prompt"
# every mode of the CLI resolves to a prompt, and units gets its own -
# it ran on the foods prompt until units.md existed
cli = set(re.search(r"choices=\[(.*?)\]", optimize_src, re.DOTALL).group(1)
          .replace('"', "").replace("\n", " ").replace(" ", "").split(","))
by_mode = dict(prompts)
for mode in cli - {""}:
    assert mode in by_mode, f"CLI mode {mode} has no prompt"
assert by_mode["units"] == "units.md", by_mode

for ref, _ in build.MODES:
    raw = build._read("references", ref)
    # a standalone replacement may name a command on purpose (test 7); what
    # must not survive is a tool line the agent-only text left behind
    kept = {build.set_language(m.group(1), "X")
            for m in (build.RE_STANDALONE.match(line)
                      for line in raw.splitlines()) if m}
    rendered = build.render_standalone(raw, "X")
    for line in rendered.splitlines():
        words = line.split()
        assert not (line.startswith("    ") and words
                    and words[0] in build.TOOL_WORDS
                    and line not in kept), (ref, line)
# the density figures survive into the standalone prompt, which has no
# convert command to fall back on
units_prompt = build.render_standalone(build._read("references", "units.md"))
assert "plain flour 120 g" in units_prompt
assert "Never estimate a density." in units_prompt

# 13. AGENTS.md carries a pointer, not the router: the block is what every
#     session pays for, so it stays small and names the file to read.
block = build.agents_md_block("X")
assert len(block) < 800, len(block)
assert build.ROUTER_FILE in block
assert "## Pick a mode" not in block                 # the router itself is not
assert build.LANG_TOKEN not in block
router = build.agents_md_router("X")
assert "## Pick a mode" in router                    # ... it is here
assert "mealie/references/recipes.md" in router      # paths rewritten
assert build.LANG_TOKEN not in router

# 14. Credentials: the mcp-mealie names work, the canonical ones outrank them.
parsed = mealie_ctx.parse_env(
    "MEALIE_BASE_URL=https://mcp.example\nMEALIE_API_KEY=mcp-token\n")
assert parsed == {"MEALIE_URL": "https://mcp.example",
                  "MEALIE_TOKEN": "mcp-token"}, parsed
parsed = mealie_ctx.parse_env(
    "MEALIE_BASE_URL=https://mcp.example\nMEALIE_URL=https://own.example\n")
assert parsed["MEALIE_URL"] == "https://own.example", parsed

# 15. build_index: one unreadable recipe costs that recipe, not the index.
broken = {"pages": 0}


def fake_mget(path, **params):
    """Serve two recipes, one of which the instance cannot render.

    Args:
        path: Path below /api.
        **params: Query parameters; page drives the pagination.

    Returns:
        The recipe list for the collection, a recipe for a detail path.

    Raises:
        requests.HTTPError: 500 for the recipe that fails to serialize.
    """
    if path == mealie_ctx.EP["recipes"]:
        broken["pages"] += 1
        if broken["pages"] > 1:
            return []
        return [{"slug": "good"}, {"slug": "bad"}]
    if path.endswith("/bad"):
        response = types.SimpleNamespace(status_code=500)
        raise mealie_ctx.requests.HTTPError("500", response=response)
    return {"slug": "good", "name": "Good", "recipeIngredient": [],
            "recipeInstructions": [], "description": "x"}


with tempfile.TemporaryDirectory() as tmp:
    mealie_ctx.mget = fake_mget
    mealie_ctx.INDEX = os.path.join(tmp, ".mealie_index.json")
    idx = mealie_ctx.build_index()

assert [r["slug"] for r in idx["recipes"]] == ["good"], idx["recipes"]
assert idx["failed"] == ["bad"], idx["failed"]

print("ok")
