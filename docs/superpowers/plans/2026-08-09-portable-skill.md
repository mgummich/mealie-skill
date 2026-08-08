# Portabler Mealie-Skill — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eine Quelle unter `skill/`, aus der `build.py` die Ziele claude-code, antigravity, cursor und agents-md rendert und installiert; `standalone/optimize.py` leitet seine Prompts zur Laufzeit aus derselben Quelle ab.

**Architecture:** `skill/` ist die einzige Quelle (SKILL.md, references/, workflow.md, scripts/mealie_ctx.py). `build.py` enthält Rendering (Agent- vs. Standalone-Fassung, Pfad-Umschreibung je Ziel), Zielbauten nach `dist/` und Installation. `optimize.py` importiert die Standalone-Renderfunktion aus `build.py`.

**Tech Stack:** Python 3, stdlib + `requests` (nur bestehend, build.py braucht es nicht). Tests: `test_build.py` mit reinen `assert`s, Aufruf `python3 test_build.py`.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-09-portable-skill-design.md` — bei Widerspruch gewinnt die Spec.
- Zeilenlänge 88, keine externen Abhängigkeiten außer `requests` (build.py: nur stdlib).
- Deutsch in Ausgaben und Kommentaren; Umlaute in Python-Docstrings/`--help` vermeiden (ae/oe/ue), in Markdown verwenden.
- Ohne `--install` schreibt build.py ausschließlich nach `dist/` (gitignored).
- `dist/` wird nie committet; keine abgeleiteten Dateien im Repo.
- Commits einzeln je Task, Messages auf Englisch (bestehender Stil).

### Entscheidungen aus dem Grilling (2026-08-09)

- Cursor-`description`s werden zur Buildzeit aus der Router-Tabelle in
  `SKILL.md` geparst (`mode_descriptions()`), nicht hartkodiert. Fehlt ein
  Modus in der Tabelle, bricht der Build ab. `MODES` schrumpft auf
  `(Referenzdatei, Slug)`-Paare.
- `description` in erzeugter `.mdc`-Frontmatter immer in Anführungszeichen
  (Doppelpunkte im Text, YAML-Sicherheit). Umlaute kommen mit dem Parsen
  automatisch aus der Quelle.
- `.gitignore` bekommt zusätzlich `__pycache__/` (optimize.py importiert
  build und erzeugt Bytecode im Repo-Root).
- `sys.exit` in den Renderfunktionen bleibt; `standalone/` darf vom
  Repo-Checkout abhängen; Antigravity-global installiert nur den Skill und
  druckt den Workflow-Hinweis.

---

### Task 1: Quelle nach `skill/` umziehen

**Files:**
- Move: `antigravity/skills/mealie/` → `skill/` (SKILL.md, references/, scripts/)
- Move: `antigravity/workflows/mealie.md` → `skill/workflow.md`
- Modify: `standalone/optimize.py:31-32` (CTX-Default-Pfad)

**Interfaces:**
- Produces: Verzeichnis `skill/` mit `SKILL.md`, `references/*.md` (6 Dateien), `workflow.md`, `scripts/mealie_ctx.py`. Alle späteren Tasks lesen von dort.

- [ ] **Step 1: Verschieben**

```bash
git mv antigravity/skills/mealie skill
git mv antigravity/workflows/mealie.md skill/workflow.md
rmdir antigravity/skills antigravity/workflows antigravity
```

(`rmdir` schlägt fehl, wenn noch etwas darin liegt — das wäre ein Fehler, dann anschauen.)

- [ ] **Step 2: CTX-Pfad in optimize.py anpassen**

In `standalone/optimize.py` ersetzen:

```python
CTX = os.environ.get("MEALIE_CTX", os.path.join(
    HERE, "..", "antigravity", "skills", "mealie", "scripts", "mealie_ctx.py"))
```

durch:

```python
CTX = os.environ.get("MEALIE_CTX", os.path.join(
    HERE, "..", "skill", "scripts", "mealie_ctx.py"))
```

Ebenfalls im Modul-Docstring die Zeile
`Kontext und Ausfuehrung laufen ueber mealie_ctx.py aus dem Antigravity-Skill;`
ändern zu
`Kontext und Ausfuehrung laufen ueber skill/scripts/mealie_ctx.py;`.

- [ ] **Step 3: Prüfen**

```bash
python3 skill/scripts/mealie_ctx.py --help >/dev/null && echo ok
python3 -c "
import os
p = os.path.join('standalone', '..', 'skill', 'scripts', 'mealie_ctx.py')
assert os.path.isfile(p), p
print('ok')"
```

Erwartet: zweimal `ok`. (`optimize.py --help` braucht `ANTHROPIC_API_KEY` wegen Modul-Level-`AH` — nicht testen, bekannte Eigenheit.)

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: move skill source to skill/ as single source of truth"
```

---

### Task 2: Regionsmarker in den Referenzen

**Files:**
- Modify: `skill/references/recipes.md` (2 Stellen)
- Modify: `skill/references/foods.md` (1 Stelle)

**Interfaces:**
- Produces: Markerpaare `<!-- nur-agent -->` … `<!-- standalone: TEXT -->`, die Task 3 auswertet. Genau 3 Paare im gesamten Baum.

- [ ] **Step 1: recipes.md, Phase-1-Werkzeugzeile**

Aktueller Text (Zeilen 3–5):

```
## Phase 1 - Analyse

    ctx recipe <slug>
```

Neu:

```
## Phase 1 - Analyse

<!-- nur-agent -->
    ctx recipe <slug>
<!-- standalone: (Kontext steht bereits im Prompt.) -->
```

- [ ] **Step 2: recipes.md, Phase-2-Schlusszeile**

Aktuelle Zeile 22:

```
`actions.json` schreiben, mit `--dry-run` prüfen, Freigabe erfragen, anhalten.
```

Neu:

```
<!-- nur-agent -->
`actions.json` schreiben, mit `--dry-run` prüfen, Freigabe erfragen, anhalten.
<!-- standalone: ACTIONS-Block ausgeben, dann STOPP. -->
```

- [ ] **Step 3: foods.md, Einheiten-Absatz**

Aktuelle Zeilen 39–41:

```
Bei Einheiten stattdessen `name`, `pluralName`, `abbreviation`,
`useAbbreviation`. Einheiten haben kein Label und keine Beschreibung; das
Werkzeug meldet dort nur Plural, Aliase und Abkürzung als Lücke.
```

Neu:

```
Bei Einheiten stattdessen `name`, `pluralName`, `abbreviation`,
<!-- nur-agent -->
`useAbbreviation`. Einheiten haben kein Label und keine Beschreibung; das
Werkzeug meldet dort nur Plural, Aliase und Abkürzung als Lücke.
<!-- standalone: `useAbbreviation`. Kein Label. -->
```

- [ ] **Step 4: Prüfen**

```bash
grep -c "nur-agent" skill/references/*.md
```

Erwartet: `foods.md:1`, `recipes.md:2`, alle anderen `0`.

- [ ] **Step 5: Commit**

```bash
git add skill/references
git commit -m "feat: mark agent-only regions with standalone replacements"
```

---

### Task 3: Rendering-Kern in `build.py` + Tests

**Files:**
- Create: `build.py`
- Create: `test_build.py`

**Interfaces:**
- Produces: `render_agent(text) -> str` (entfernt Markerzeilen, Inhalt bleibt), `render_standalone(text) -> str` (ersetzt Regionen, streicht Werkzeugzeilen), `rewrite(text, mapping) -> str` (Single-Pass-Ersetzung, längster Schlüssel zuerst), `MAPPINGS: dict[str, dict[str, str]]`. Task 4–6 bauen darauf auf.

- [ ] **Step 1: Failing Tests schreiben**

`test_build.py`:

```python
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

print("ok")
```

- [ ] **Step 2: Fehlschlag verifizieren**

Run: `python3 test_build.py`
Expected: `ModuleNotFoundError: No module named 'build'`

- [ ] **Step 3: Implementieren**

`build.py`:

```python
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
TOOL_WORDS = ("index", "audit", "ctx", "usage", "apply")

# (Referenzdatei, Slug fuer Cursor-Regeln); Beschreibungen liefert
# mode_descriptions() zur Buildzeit aus der Router-Tabelle in SKILL.md.
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
```

(CLI und Zielbauten kommen in Task 5/6; die Datei ist bis dahin nur Modul.)

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 test_build.py`
Expected: `ok`

- [ ] **Step 5: Zusatzprüfung gegen die echten Alt-Prompts**

Die alten handabgeleiteten Prompts liegen noch — das Rendering muss sie
reproduzieren:

```bash
python3 - <<'EOF'
import build
pairs = [("recipes.md", "recipe.txt"), ("foods.md", "foods.txt"),
         ("organizers.md", "organizers.txt"), ("cookbooks.md", "cookbooks.txt"),
         ("maintenance.md", "maintenance.txt")]
for ref, txt in pairs:
    a = build.render_standalone(
        open("skill/references/" + ref, encoding="utf-8").read())
    b = open("standalone/prompts/" + txt, encoding="utf-8").read()
    if a != b:
        import difflib
        print(ref, "weicht ab:")
        print("".join(difflib.unified_diff(
            b.splitlines(True), a.splitlines(True), txt, "gerendert")))
print("Vergleich fertig")
EOF
```

Erwartet: nur `Vergleich fertig`, keine Diffs. Weicht etwas ab: erst prüfen,
ob die Abweichung eine vergessene Markerstelle ist (dann Task 2 ergänzen)
oder Whitespace-Rauschen der Handableitung (dann ist das Rendering korrekt
und die Abweichung dokumentieren, nicht wegbiegen).

- [ ] **Step 6: Commit**

```bash
git add build.py test_build.py
git commit -m "feat: add rendering core (agent/standalone views, path rewrite)"
```

---

### Task 4: `optimize.py` leitet Prompts zur Laufzeit ab; Alt-Prompts löschen

**Files:**
- Modify: `standalone/optimize.py:40-66` (`PROMPTS`, `system_block`)
- Delete: `standalone/prompts/recipe.txt`, `foods.txt`, `organizers.txt`, `cookbooks.txt`, `maintenance.txt`
- Keep: `standalone/prompts/common.txt`

**Interfaces:**
- Consumes: `build.render_standalone` aus Task 3.
- Produces: `system_block(mode)` unverändert in Signatur und Rückgabeform (Liste mit einem Cache-Block).

- [ ] **Step 1: optimize.py umbauen**

`PROMPTS`-Dict ersetzen:

```python
PROMPTS = {
    "recipe": "recipes.md", "foods": "foods.md", "units": "foods.md",
    "organizers": "organizers.md", "cookbooks": "cookbooks.md",
    "maintenance": "maintenance.md",
}
```

Nach den bestehenden Imports ergänzen:

```python
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import build
```

`system_block` ersetzen:

```python
def system_block(mode):
    """Gemeinsame Regeln + Modusregeln als EIN gecachter Block.

    Die Modusregeln werden zur Laufzeit aus skill/references/ abgeleitet
    (build.render_standalone) — eine Quelle, keine Prompt-Kopien.
    Getrennte Bloecke waeren feiner, aber der gemeinsame Teil liegt unter
    der Cache-Mindestgroesse von 1024 Tokens und wuerde allein nicht greifen.
    """
    common = open(os.path.join(HERE, "prompts", "common.txt"),
                  encoding="utf-8").read()
    ref = open(os.path.join(HERE, "..", "skill", "references", PROMPTS[mode]),
               encoding="utf-8").read()
    text = common + "\n\n" + build.render_standalone(ref)
    return [{"type": "text", "text": text,
             "cache_control": {"type": "ephemeral"}}]
```

- [ ] **Step 2: Alt-Prompts löschen**

```bash
git rm standalone/prompts/recipe.txt standalone/prompts/foods.txt \
       standalone/prompts/organizers.txt standalone/prompts/cookbooks.txt \
       standalone/prompts/maintenance.txt
```

- [ ] **Step 3: Prüfen (ohne API-Key, Modul-Level-AH umgehen)**

```bash
ANTHROPIC_API_KEY=dummy python3 - <<'EOF'
import sys; sys.path.insert(0, "standalone")
import optimize
for mode in optimize.PROMPTS:
    blocks = optimize.system_block(mode)
    assert len(blocks) == 1 and blocks[0]["cache_control"]
    assert len(blocks[0]["text"]) > 4000, (mode, len(blocks[0]["text"]))
print("ok")
EOF
```

Erwartet: `ok`. (>4000 Zeichen ≈ sicher über der 1024-Token-Cache-Grenze.)

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: derive standalone prompts at runtime from skill references"
```

---

### Task 5: Zielbauten nach `dist/`

**Files:**
- Modify: `build.py` (Zielbauten + CLI)
- Modify: `test_build.py` (AGENTS.md-Merge kommt erst Task 6; hier nur Bauten)
- Modify: `.gitignore` (+ `dist/`)

**Interfaces:**
- Consumes: `render_agent`, `render_standalone`, `rewrite`, `MAPPINGS`, `MODES`.
- Produces: `build_target(target, out) -> str` (baut `out/<target>/…`, gibt den Zielpfad zurück), `agents_md_block() -> str` (Router-Block ohne Marker), CLI `python3 build.py [--target T] [--out DIR]`.

- [ ] **Step 1: Zielbauten implementieren**

In `build.py` ergänzen:

```python
def _read(*parts):
    with open(os.path.join(SKILL, *parts), encoding="utf-8") as f:
        return f.read()


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _split_frontmatter(text):
    """(frontmatter_dict_roh, body) — Frontmatter nur description auslesen."""
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def _copy_refs(dst_dir, mapping):
    for ref, _ in MODES:
        _write(os.path.join(dst_dir, ref),
               rewrite(render_agent(_read("references", ref)), mapping))


def _copy_script(root):
    _write(os.path.join(root, "mealie", "scripts", "mealie_ctx.py"),
           _read("scripts", "mealie_ctx.py"))


def build_target(target, out):
    root = os.path.join(out, target)
    if os.path.isdir(root):
        shutil.rmtree(root)
    mapping = MAPPINGS[target]

    if target in ("claude-code", "antigravity"):
        base = ".claude" if target == "claude-code" else ".agents"
        skill_dir = os.path.join(root, base, "skills", "mealie")
        _write(os.path.join(skill_dir, "SKILL.md"),
               rewrite(render_agent(_read("SKILL.md")), mapping))
        _copy_refs(os.path.join(skill_dir, "references"), mapping)
        _write(os.path.join(skill_dir, "scripts", "mealie_ctx.py"),
               _read("scripts", "mealie_ctx.py"))
        wf = rewrite(render_agent(_read("workflow.md")), mapping)
        wf_path = (os.path.join(root, ".claude", "commands", "mealie.md")
                   if target == "claude-code"
                   else os.path.join(root, ".agents", "workflows", "mealie.md"))
        _write(wf_path, wf)

    elif target == "cursor":
        fm, body = _split_frontmatter(_read("SKILL.md"))
        desc = re.search(r"^description: (.+)$", fm, re.M).group(1)
        descs = mode_descriptions()
        _write(os.path.join(root, ".cursor", "rules", "mealie.mdc"),
               _mdc_frontmatter(desc)
               + rewrite(render_agent(body), mapping))
        for ref, slug in MODES:
            _write(os.path.join(root, ".cursor", "rules",
                                "mealie-" + slug + ".mdc"),
                   _mdc_frontmatter(descs[ref])
                   + rewrite(render_agent(_read("references", ref)), mapping))
        _, wf_body = _split_frontmatter(_read("workflow.md"))
        _write(os.path.join(root, ".cursor", "commands", "mealie.md"),
               rewrite(render_agent(wf_body), mapping))
        _copy_script(root)

    elif target == "agents-md":
        _write(os.path.join(root, "AGENTS.md"),
               "<!-- mealie:begin -->\n" + agents_md_block()
               + "<!-- mealie:end -->\n")
        _copy_refs(os.path.join(root, "mealie", "references"), mapping)
        _copy_script(root)

    else:
        sys.exit("unbekanntes Ziel: " + target)
    return root


def _mdc_frontmatter(desc):
    return ('---\ndescription: "' + desc.replace('"', r'\"')
            + '"\nalwaysApply: false\n---\n')


def mode_descriptions():
    """Beschreibung je Referenzdatei aus der Router-Tabelle in SKILL.md.

    Regex an die reale Tabellenform anpassen; fehlt ein Modus aus MODES,
    bricht der Build mit Fehlermeldung ab.
    """
    ...


def agents_md_block():
    """Router aus SKILL.md, Pfade auf mealie/…, ohne Frontmatter."""
    _, body = _split_frontmatter(_read("SKILL.md"))
    return rewrite(render_agent(body), MAPPINGS["agents-md"]).rstrip() + "\n"


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--target", choices=TARGETS)
    p.add_argument("--out", default=os.path.join(HERE, "dist"))
    p.add_argument("--install", choices=TARGETS)
    p.add_argument("--into")
    p.add_argument("--force", action="store_true")
    a = p.parse_args()

    if a.install:
        install(a.install, a.into, a.force)
        return
    for t in ([a.target] if a.target else TARGETS):
        print("gebaut:", build_target(t, a.out))


if __name__ == "__main__":
    main()
```

(`install` kommt in Task 6 — bis dahin einen Platzhalter setzen:
`def install(target, into, force): sys.exit("--install kommt in Task 6")`.)

- [ ] **Step 2: Bauen und Ergebnis prüfen**

```bash
python3 build.py
find dist -type f | sort
```

Erwartet (genau diese Dateien):

```
dist/agents-md/AGENTS.md
dist/agents-md/mealie/references/actions.md
dist/agents-md/mealie/references/cookbooks.md
dist/agents-md/mealie/references/foods.md
dist/agents-md/mealie/references/maintenance.md
dist/agents-md/mealie/references/organizers.md
dist/agents-md/mealie/references/recipes.md
dist/agents-md/mealie/scripts/mealie_ctx.py
dist/antigravity/.agents/skills/mealie/SKILL.md
dist/antigravity/.agents/skills/mealie/references/… (6 Dateien)
dist/antigravity/.agents/skills/mealie/scripts/mealie_ctx.py
dist/antigravity/.agents/workflows/mealie.md
dist/claude-code/.claude/commands/mealie.md
dist/claude-code/.claude/skills/mealie/SKILL.md
dist/claude-code/.claude/skills/mealie/references/… (6 Dateien)
dist/claude-code/.claude/skills/mealie/scripts/mealie_ctx.py
dist/cursor/.cursor/commands/mealie.md
dist/cursor/.cursor/rules/mealie.mdc
dist/cursor/.cursor/rules/mealie-<slug>.mdc (6 Dateien)
dist/cursor/mealie/scripts/mealie_ctx.py
```

Stichproben:

```bash
grep "nur-agent" -r dist && echo "FEHLER: Marker im Rendering" || echo ok
grep -n "\.agents/" dist/claude-code/.claude/commands/mealie.md || echo ok
grep -n "mealie/scripts/mealie_ctx.py" dist/cursor/.cursor/commands/mealie.md
grep -n "mealie/references/recipes.md" dist/agents-md/AGENTS.md
diff dist/antigravity/.agents/skills/mealie/SKILL.md skill/SKILL.md
```

Erwartet: kein Marker im Rendering; Claude-Command ohne `.agents/`-Pfad;
Cursor-Command und AGENTS.md mit umgeschriebenen Pfaden; Antigravity-SKILL.md
identisch zur Quelle bis auf entfernte Markerzeilen (diff zeigt nur die
Markerzeilen).

- [ ] **Step 3: `.gitignore` ergänzen**

`dist/` und `__pycache__/` als Zeilen anhängen.

- [ ] **Step 4: Tests laufen lassen**

Run: `python3 test_build.py`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add build.py test_build.py .gitignore
git commit -m "feat: render all four targets into dist/"
```

---

### Task 6: Installation (`--install`, `--into`, `--force`, AGENTS.md-Merge)

**Files:**
- Modify: `build.py` (`install`, `merge_agents_md`; Platzhalter ersetzen)
- Modify: `test_build.py` (Idempotenz-Tests)

**Interfaces:**
- Consumes: `build_target`, `agents_md_block`.
- Produces: `merge_agents_md(existing: str | None, block: str) -> str`; CLI `--install ZIEL [--into PROJEKT] [--force]`.

- [ ] **Step 1: Failing Tests ergänzen**

In `test_build.py` vor `print("ok")`:

```python
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
```

Run: `python3 test_build.py`
Expected: `AttributeError: … merge_agents_md`

- [ ] **Step 2: Implementieren**

Platzhalter-`install` ersetzen durch:

```python
MARK_BEGIN, MARK_END = "<!-- mealie:begin -->", "<!-- mealie:end -->"


def merge_agents_md(existing, block):
    """Markerblock einsetzen/ersetzen; alles ausserhalb bleibt unberuehrt."""
    wrapped = MARK_BEGIN + "\n" + block.rstrip() + "\n" + MARK_END
    if existing is None:
        return wrapped + "\n"
    if MARK_BEGIN in existing:
        return re.sub(
            re.escape(MARK_BEGIN) + r".*?" + re.escape(MARK_END),
            lambda m: wrapped, existing, count=1, flags=re.S)
    return existing.rstrip() + "\n\n" + wrapped + "\n"


def install(target, into, force):
    if target in ("cursor", "agents-md") and not into:
        sys.exit(target + " ist projektbezogen, es gibt keinen globalen Ort "
                 "dafuer — Zielprojekt mit --into angeben.")
    built = build_target(target, os.path.join(HERE, "dist"))

    if into:
        dest = os.path.abspath(into)
    elif target == "claude-code":
        dest = os.path.expanduser("~")          # Baum beginnt mit .claude/
    else:                                       # antigravity global
        dest = None

    if target == "antigravity" and dest is None:
        src = os.path.join(built, ".agents", "skills", "mealie")
        dst = os.path.expanduser("~/.gemini/config/skills/mealie")
        _install_tree([(src, dst)], force)
        print("Hinweis: Workflow ist projektbezogen; fuer ein Projekt "
              "--into verwenden.")
        return

    pairs, agents_md = [], None
    for dirpath, _, files in os.walk(built):
        for f in files:
            src = os.path.join(dirpath, f)
            rel = os.path.relpath(src, built)
            if rel == "AGENTS.md":
                agents_md = src
            else:
                pairs.append((src, os.path.join(dest, rel)))
    _install_tree(pairs, force)
    if agents_md:
        out = os.path.join(dest, "AGENTS.md")
        old = (open(out, encoding="utf-8").read()
               if os.path.exists(out) else None)
        with open(agents_md, encoding="utf-8") as f:
            raw = f.read()
        block = raw[raw.index(MARK_BEGIN) + len(MARK_BEGIN):
                    raw.index(MARK_END)].strip("\n") + "\n"
        _write(out, merge_agents_md(old, block))
        print("aktualisiert:" if old else "angelegt:", out)


def _install_tree(pairs, force):
    vorhanden = [dst for _, dst in pairs if os.path.exists(dst)]
    if vorhanden and not force:
        sys.exit("existiert bereits (mit --force ueberschreiben):\n  "
                 + "\n  ".join(sorted(vorhanden)))
    for src, dst in pairs:
        if os.path.isdir(src):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        print("installiert:", dst)
```

- [ ] **Step 3: Tests laufen lassen**

Run: `python3 test_build.py`
Expected: `ok`

- [ ] **Step 4: Installation gegen ein Wegwerf-Projekt prüfen**

```bash
T=$(mktemp -d)
python3 build.py --install agents-md --into "$T"
python3 build.py --install agents-md --into "$T" --force
python3 build.py --install cursor --into "$T"
python3 build.py --install cursor --into "$T" 2>&1 | head -2   # muss abbrechen
grep -c "mealie:begin" "$T/AGENTS.md"                          # 1, nicht 2
python3 build.py --install cursor 2>&1 | head -1               # muss abbrechen
ls "$T/.cursor/rules" "$T/mealie/scripts"
rm -rf "$T"
```

Erwartet: zweiter agents-md-Lauf idempotent (AGENTS.md enthält den Block
einmal), zweiter cursor-Lauf bricht mit „existiert bereits" ab, cursor ohne
`--into` bricht mit Erklärung ab.

- [ ] **Step 5: Commit**

```bash
git add build.py test_build.py
git commit -m "feat: add install targets with force guard and AGENTS.md merge"
```

---

### Task 7: Dokumente nachziehen

**Files:**
- Modify: `CLAUDE.md` (Architekturblock, Ableitungsregel)
- Modify: `README.md` (Aufbau, Installation je Werkzeug)
- Modify: `HANDOFF.md` (Abschnitt „Prompts neu ableiten" streichen)

**Interfaces:** keine — reine Doku.

- [ ] **Step 1: CLAUDE.md**

Architekturblock (Zeilen 7–21) ersetzen durch:

```
## Architektur

    skill/                  einzige Quelle der Wahrheit
      SKILL.md              Router: Modus wählen, gemeinsame Regeln
      references/*.md       Details je Modus, nur bei Bedarf gelesen
      workflow.md           Ablauf für /mealie
      scripts/mealie_ctx.py ALLE API-Zugriffe, kein Modellaufruf
    standalone/
      prompts/common.txt    Grundsätze + ACTIONS-Format (handgepflegt)
      optimize.py           Modellaufruf, Freigabe, Batch
    build.py                rendert dist/ für claude-code, antigravity,
                            cursor, agents-md; installiert mit --install
    test_build.py           python3 test_build.py

`mealie_ctx.py` ist die einzige Stelle mit HTTP-Zugriff auf Mealie.
`optimize.py` ruft es als Subprozess auf und leitet die Modusprompts zur
Laufzeit aus `skill/references/` ab (`build.render_standalone`). Neue
Funktionalität gehört ins Skript, nicht in die Prompts.
```

Den Absatz **„Regeln stehen an einer Stelle."** (Zeilen 42–44) ersetzen durch:

```
**Regeln stehen an einer Stelle.** `skill/` ist die Quelle; `dist/` und die
Standalone-Prompts werden gerendert, nie von Hand gepflegt. Drei Stellen in
den Referenzen tragen `<!-- nur-agent -->`/`<!-- standalone: … -->`-Marker
für Text, der je Kontext verschieden sein muss.
```

- [ ] **Step 2: README.md**

Abschnitt „Antigravity" (Zeilen 51–66) ersetzen durch einen Abschnitt
„Installation" mit:

```
## Installation

    python3 build.py --install claude-code           # global, ~/.claude/
    python3 build.py --install antigravity           # global, ~/.gemini/config/
    python3 build.py --install claude-code --into <projekt>
    python3 build.py --install cursor --into <projekt>
    python3 build.py --install agents-md --into <projekt>   # Codex, Zed, …

`cursor` und `agents-md` sind projektbezogen und verlangen `--into`.
Vorhandene Dateien werden nie still überschrieben (`--force`); eine
bestehende `AGENTS.md` wird nur im markierten Block aktualisiert.

Ohne `--install` rendert `python3 build.py` alle Ziele nach `dist/`.
```

Die Antigravity-Bedienhinweise (`/mealie …`-Beispiele, Request-Review-Absatz)
darunter behalten. Im Abschnitt „Aufbau" (Zeilen 93–104) das Layout auf das
neue Schema aus CLAUDE.md umstellen. Im Standalone-Abschnitt nichts ändern
(Bedienung identisch).

- [ ] **Step 3: HANDOFF.md**

Abschnitt „Prompts neu ableiten" (Zeilen 115–121) ersetzen durch:

```
## Prompts

`standalone/prompts/<modus>.txt` gibt es nicht mehr; `optimize.py` leitet die
Modusregeln zur Laufzeit aus `skill/references/` ab. Nach Regeländerungen
nichts nachzuziehen — nur prüfen, dass der kombinierte Block über 1024
Tokens bleibt (Test in `test_build.py` bzw. Längen-Check in optimize.py).
```

- [ ] **Step 4: Querverweise prüfen**

```bash
grep -rn "antigravity/" CLAUDE.md README.md HANDOFF.md && echo PRUEFEN || echo ok
grep -rn "prompts/recipe.txt\|prompts/foods.txt" . --include='*.md' && echo PRUEFEN || echo ok
```

Erwartet: zweimal `ok` (Treffer nur, wenn ein Pfad vergessen wurde).

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md README.md HANDOFF.md
git commit -m "docs: update layout, install instructions and handoff"
```
