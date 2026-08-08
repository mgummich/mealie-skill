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


def _read(*parts):
    with open(os.path.join(SKILL, *parts), encoding="utf-8") as f:
        return f.read()


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _split_frontmatter(text):
    """(frontmatter_roh, body) — Frontmatter nur fuer description gelesen."""
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def _mdc_frontmatter(desc):
    return ('---\ndescription: "' + desc.replace('"', r'\"')
            + '"\nalwaysApply: false\n---\n')


def mode_descriptions():
    """Beschreibung je Referenzdatei aus SKILL.md ableiten.

    Die fuenf Modi stehen in der Router-Tabelle, actions.md in der
    Prosazeile danach. Fehlt eine Referenz, bricht der Build ab.
    """
    body = _split_frontmatter(_read("SKILL.md"))[1]
    descs = {ref: desc for desc, ref in re.findall(
        r"^\| (.+?) \| `references/([^`]+)` \|$", body, re.M)}
    m = re.search(r"^(.+?): `references/actions\.md`", body, re.M)
    if m:
        descs["actions.md"] = m.group(1)
    for ref, _ in MODES:
        if ref not in descs:
            sys.exit("keine Beschreibung in SKILL.md fuer " + ref)
    return descs


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


def agents_md_block():
    """Router aus SKILL.md, Pfade auf mealie/…, ohne Frontmatter."""
    _, body = _split_frontmatter(_read("SKILL.md"))
    return rewrite(render_agent(body), MAPPINGS["agents-md"]).rstrip() + "\n"


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
