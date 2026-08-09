#!/usr/bin/env python3
"""Render the Mealie skill for the target formats and install it.

  build.py [--target TARGET] [--out dist] [--lang LANGUAGE]
  build.py --install TARGET [--into PROJECT] [--force] [--lang LANGUAGE]

Targets: claude-code, antigravity, cursor, agents-md

Without --install nothing but dist/ is written. claude-code and antigravity
install globally when --into is omitted (~/.claude and ~/.gemini/config);
cursor and agents-md require --into, as they have no global counterpart.

--lang sets the language the model writes recipe content in, baked into the
rendered skill. Default: $MEALIE_LANG, or English.
"""
import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "skill")
TARGETS = ("claude-code", "antigravity", "cursor", "agents-md")

RE_AGENT = re.compile(r"^\s*<!-- agent-only -->\s*$")
RE_STANDALONE = re.compile(r"^\s*<!-- standalone: (.*?) -->\s*$")
TOOL_WORDS = ("setup", "index", "audit", "ctx", "usage", "apply", "python")

# Placeholder for the content language in SKILL.md, references and prompts.
# The project language is English; this is the language of the recipe data.
LANG_TOKEN = "${CONTENT_LANG}"
DEFAULT_LANG = os.environ.get("MEALIE_LANG") or "English"

# (reference file, slug for cursor rules); descriptions come from
# mode_descriptions(), which reads the router table in SKILL.md.
MODES = [
    ("recipes.md", "recipes"),
    ("foods.md", "foods"),
    ("organizers.md", "organizers"),
    ("cookbooks.md", "cookbooks"),
    ("maintenance.md", "maintenance"),
    ("actions.md", "actions"),
    ("mcp.md", "mcp"),
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


def set_language(text, lang=None):
    """Substitute the content language placeholder.

    Args:
        text: Text possibly containing LANG_TOKEN.
        lang: Language name, e.g. "English" or "Deutsch". Defaults to
            DEFAULT_LANG.

    Returns:
        The text with every placeholder replaced.
    """
    return text.replace(LANG_TOKEN, lang or DEFAULT_LANG)


def render_agent(text, lang=None):
    """Render reference text for an agent target.

    Drops the marker lines themselves and keeps everything they enclose:
    an agent has the tool, so the agent-only passages apply.

    Args:
        text: Raw markdown from skill/.
        lang: Content language for the placeholder.

    Returns:
        The markdown without marker lines.
    """
    return set_language("".join(
        line for line in text.splitlines(keepends=True)
        if not RE_AGENT.match(line) and not RE_STANDALONE.match(line)), lang)


def _is_tool_line(line):
    """Report whether a line is an indented mealie_ctx invocation.

    Args:
        line: Single line without trailing newline.

    Returns:
        True if the line is indented and starts with a word from
        TOOL_WORDS, which standalone renders without.
    """
    words = line.split()
    return (line.startswith("    ") and words
            and words[0] in TOOL_WORDS)


def render_standalone(text, lang=None):
    """Render reference text for the standalone prompt.

    Each agent-only region is replaced by the text of its closing
    "standalone:" comment, and tool invocation lines are dropped: the model
    behind optimize.py calls no tool itself.

    Args:
        text: Raw markdown from skill/references/.
        lang: Content language for the placeholder.

    Returns:
        The rendered markdown with a trailing newline.

    Raises:
        SystemExit: On an unpaired marker in either direction.
    """
    out, lines = [], iter(text.splitlines())
    for line in lines:
        if RE_AGENT.match(line):
            for line in lines:
                m = RE_STANDALONE.match(line)
                if m:
                    out.append(m.group(1))
                    break
            else:
                sys.exit("agent-only without a closing standalone: comment")
            continue
        if RE_STANDALONE.match(line):
            sys.exit("standalone: comment without a preceding agent-only")
        if _is_tool_line(line):
            continue
        out.append(line)
    return set_language("\n".join(out) + "\n", lang)


def rewrite(text, mapping):
    """Apply all path replacements in a single pass.

    One regex with the longest key first, so a replacement result is never
    rewritten again by a shorter key.

    Args:
        text: Text to rewrite.
        mapping: Source path to target path; an empty mapping is a no-op.

    Returns:
        The rewritten text.
    """
    if not mapping:
        return text
    pat = re.compile("|".join(
        re.escape(k) for k in sorted(mapping, key=len, reverse=True)))
    return pat.sub(lambda m: mapping[m.group(0)], text)


def _read(*parts):
    """Read a UTF-8 file below skill/.

    Args:
        *parts: Path segments relative to skill/.

    Returns:
        The file contents.

    Raises:
        OSError: If the file does not exist or cannot be read.
    """
    with open(os.path.join(SKILL, *parts), encoding="utf-8") as f:
        return f.read()


def _write(path, text):
    """Write a UTF-8 file, creating missing parent directories.

    Args:
        path: Target path.
        text: Contents to write; an existing file is overwritten.

    Raises:
        OSError: If the file cannot be written.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _split_frontmatter(text):
    """Split YAML frontmatter from the body.

    The frontmatter is only ever read for its description, so it is
    returned raw instead of parsed.

    Args:
        text: Markdown, with or without frontmatter.

    Returns:
        Tuple (raw frontmatter, body). The first element is an empty string
        if there is no frontmatter.
    """
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def _mdc_frontmatter(desc):
    """Build the frontmatter of a Cursor .mdc rule.

    Args:
        desc: Single-line description; quotes are escaped.

    Returns:
        The frontmatter block including both delimiters and a trailing
        newline. alwaysApply is false, the rule loads on demand.
    """
    return ('---\ndescription: "' + desc.replace('"', r'\"')
            + '"\nalwaysApply: false\n---\n')


def mode_descriptions():
    """Derive one description per reference file from SKILL.md.

    The five modes come from the router table, the files that are not modes
    (actions.md, mcp.md) from the prose lines below it: "<description>:
    `references/<file>`". Descriptions live in SKILL.md only, so they cannot
    drift apart from the router.

    Returns:
        Mapping of reference filename to its description.

    Raises:
        SystemExit: If SKILL.md has no description for a file in MODES.
        OSError: If SKILL.md cannot be read.
    """
    body = _split_frontmatter(_read("SKILL.md"))[1]
    descs = {ref: desc for desc, ref in re.findall(
        r"^\| (.+?) \| `references/([^`]+)` \|$", body, re.MULTILINE)}
    for desc, ref in re.findall(r"^(.+?): `references/([^`]+)`", body, re.MULTILINE):
        descs.setdefault(ref, desc)
    for ref, _ in MODES:
        if ref not in descs:
            sys.exit("no description in SKILL.md for " + ref)
    return descs


def _copy_refs(dst_dir, mapping, lang=None):
    """Render every reference file into a target directory.

    Args:
        dst_dir: Target directory; the filenames from MODES are kept.
        mapping: Path replacements for this target.
        lang: Content language for the placeholder.

    Raises:
        OSError: If a file cannot be read or written.
    """
    for ref, _ in MODES:
        _write(os.path.join(dst_dir, ref),
               rewrite(render_agent(_read("references", ref), lang), mapping))


def _copy_script(root):
    """Copy mealie_ctx.py to mealie/scripts/ below a target root.

    Copied verbatim: the script is identical for every target, only the
    paths pointing at it differ.

    Args:
        root: Root directory of the target.

    Raises:
        OSError: If the script cannot be read or written.
    """
    _write(os.path.join(root, "mealie", "scripts", "mealie_ctx.py"),
           _read("scripts", "mealie_ctx.py"))


def build_target(target, out, lang=None):
    """Render one target into out/<target>/, replacing what is there.

    Layout per target: claude-code and antigravity get a skill directory
    plus a workflow, cursor gets .mdc rules and a command, agents-md gets a
    marked block in AGENTS.md plus references beside it.

    Args:
        target: One of TARGETS.
        out: Output directory; out/<target> is deleted beforehand.
        lang: Content language baked into the rendered skill.

    Returns:
        Path of the rendered target directory.

    Raises:
        SystemExit: On an unknown target, a missing or multi-line
            description in SKILL.md, or an unpaired marker.
        OSError: If a file cannot be read or written.
    """
    root = os.path.join(out, target)
    if os.path.isdir(root):
        shutil.rmtree(root)
    mapping = MAPPINGS[target]

    if target in ("claude-code", "antigravity"):
        base = ".claude" if target == "claude-code" else ".agents"
        skill_dir = os.path.join(root, base, "skills", "mealie")
        _write(os.path.join(skill_dir, "SKILL.md"),
               rewrite(render_agent(_read("SKILL.md"), lang), mapping))
        _copy_refs(os.path.join(skill_dir, "references"), mapping, lang)
        _write(os.path.join(skill_dir, "scripts", "mealie_ctx.py"),
               _read("scripts", "mealie_ctx.py"))
        wf = rewrite(render_agent(_read("workflow.md"), lang), mapping)
        wf_path = (os.path.join(root, ".claude", "commands", "mealie.md")
                   if target == "claude-code"
                   else os.path.join(root, ".agents", "workflows", "mealie.md"))
        _write(wf_path, wf)

    elif target == "cursor":
        fm, body = _split_frontmatter(_read("SKILL.md"))
        m = re.search(r"^description:[ \t]*(.+)$", fm, re.MULTILINE)
        desc = m.group(1).strip() if m else ""
        if not desc or desc in (">", ">-", "|", "|-"):
            sys.exit("SKILL.md: description missing or not on one line")
        descs = mode_descriptions()
        _write(os.path.join(root, ".cursor", "rules", "mealie.mdc"),
               _mdc_frontmatter(desc)
               + rewrite(render_agent(body, lang), mapping))
        for ref, slug in MODES:
            _write(os.path.join(root, ".cursor", "rules",
                                "mealie-" + slug + ".mdc"),
                   _mdc_frontmatter(descs[ref])
                   + rewrite(render_agent(_read("references", ref), lang),
                             mapping))
        _, wf_body = _split_frontmatter(_read("workflow.md"))
        _write(os.path.join(root, ".cursor", "commands", "mealie.md"),
               rewrite(render_agent(wf_body, lang), mapping))
        _copy_script(root)

    elif target == "agents-md":
        _write(os.path.join(root, "AGENTS.md"),
               "<!-- mealie:begin -->\n" + agents_md_block(lang)
               + "<!-- mealie:end -->\n")
        _copy_refs(os.path.join(root, "mealie", "references"), mapping, lang)
        _copy_script(root)

    else:
        sys.exit("unknown target: " + target)
    return root


def agents_md_block(lang=None):
    """Build the AGENTS.md block: the router from SKILL.md, without frontmatter.

    Paths are rewritten to mealie/..., since AGENTS.md sits in the project
    root rather than in a skill directory.

    Args:
        lang: Content language for the placeholder.

    Returns:
        The block with a trailing newline, without the marker lines.

    Raises:
        OSError: If SKILL.md cannot be read.
    """
    _, body = _split_frontmatter(_read("SKILL.md"))
    return rewrite(render_agent(body, lang),
                   MAPPINGS["agents-md"]).rstrip() + "\n"


MARK_BEGIN, MARK_END = "<!-- mealie:begin -->", "<!-- mealie:end -->"
_RE_BEGIN = re.compile("^" + re.escape(MARK_BEGIN) + r"[ \t]*$", re.MULTILINE)
_RE_END = re.compile("^" + re.escape(MARK_END) + r"[ \t]*$", re.MULTILINE)


def merge_agents_md(existing, block):
    """Insert or replace the marked block; everything outside stays untouched.

    Markers only count on a line of their own, so a mention in running text
    stays text. A begin without an end aborts instead of silently doing
    nothing. Idempotent: merging the same block twice changes nothing.

    Args:
        existing: Current AGENTS.md contents, or None if there is no file.
        block: Block contents without markers.

    Returns:
        The full new AGENTS.md contents.

    Raises:
        SystemExit: If a begin marker has no matching end marker.
    """
    wrapped = MARK_BEGIN + "\n" + block.rstrip() + "\n" + MARK_END
    if existing is None or not existing.strip():
        return wrapped + "\n"
    mb = _RE_BEGIN.search(existing)
    if mb:
        me = _RE_END.search(existing, mb.end())
        if not me:
            sys.exit("AGENTS.md: mealie:begin without mealie:end")
        return existing[:mb.start()] + wrapped + existing[me.end():]
    return existing.rstrip() + "\n\n" + wrapped + "\n"


def install(target, into, force, lang=None):
    """Render a target and copy it to its destination.

    Without --into, claude-code installs to ~ (the tree starts at .claude/)
    and antigravity to ~/.gemini/config/skills/. cursor and agents-md are
    project-scoped and require --into. For a global claude-code install the
    skill paths in the /mealie command are rewritten to absolute ~/.claude
    paths, so the command works from any project directory.

    Args:
        target: One of TARGETS.
        into: Target project, or None for a global install.
        force: Overwrite existing files. AGENTS.md is exempt: only its
            marked block is updated, regardless of this flag.
        lang: Content language baked into the installed skill.

    Raises:
        SystemExit: If a project-scoped target has no --into, or if files
            exist and force is False.
        OSError: If a file cannot be read or written.
    """
    if target in ("cursor", "agents-md") and not into:
        sys.exit(target + " is project-scoped, there is no global location "
                 "for it — name the target project with --into.")
    built = build_target(target, os.path.join(HERE, "dist"), lang)

    if into:
        dest = os.path.abspath(into)
    elif target == "claude-code":
        dest = os.path.expanduser("~")          # the tree starts at .claude/
    else:                                       # antigravity, global
        dest = None

    if target == "antigravity" and dest is None:
        src = os.path.join(built, ".agents", "skills", "mealie")
        dst = os.path.expanduser("~/.gemini/config/skills/mealie")
        _install_tree([(src, dst)], force)
        print("note: the workflow is project-scoped; use --into for a "
              "project.")
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
    if target == "claude-code" and not into:
        # global: /mealie runs from any project cwd, so the path has to point
        # at ~/.claude absolutely instead of relative to the project
        cmd = os.path.join(dest, ".claude", "commands", "mealie.md")
        with open(cmd, encoding="utf-8") as f:
            text = f.read()
        _write(cmd, text.replace(".claude/skills/mealie/",
                                 "~/.claude/skills/mealie/"))
    if agents_md:
        out = os.path.join(dest, "AGENTS.md")
        old = (open(out, encoding="utf-8").read()
               if os.path.exists(out) else None)
        with open(agents_md, encoding="utf-8") as f:
            raw = f.read()
        block = raw[raw.index(MARK_BEGIN) + len(MARK_BEGIN):
                    raw.index(MARK_END)].strip("\n") + "\n"
        _write(out, merge_agents_md(old, block))
        print("updated:" if old else "created:", out)


def _install_tree(pairs, force):
    """Copy source/target pairs, aborting on existing files.

    Checked completely before the first copy, so a run either installs
    everything or nothing.

    Args:
        pairs: (source, target) tuples; sources may be files or directories.
        force: Overwrite existing targets instead of aborting.

    Raises:
        SystemExit: If a target exists and force is False.
        OSError: If a copy fails.
    """
    existing = [dst for _, dst in pairs if os.path.exists(dst)]
    if existing and not force:
        sys.exit("already exists (overwrite with --force):\n  "
                 + "\n  ".join(sorted(existing)))
    for src, dst in pairs:
        if os.path.isdir(src):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
        print("installed:", dst)


def main():
    """Parse the command line, then install or render into dist/.

    Without --install every target is rendered, or only the one given by
    --target.

    Raises:
        SystemExit: On usage errors and from install/build_target.
    """
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--target", choices=TARGETS)
    p.add_argument("--out", default=os.path.join(HERE, "dist"))
    p.add_argument("--install", choices=TARGETS)
    p.add_argument("--into")
    p.add_argument("--force", action="store_true")
    p.add_argument("--lang", default=DEFAULT_LANG,
                   help="language of the recipe content (default: %(default)s)")
    a = p.parse_args()

    if a.install:
        install(a.install, a.into, a.force, a.lang)
        return
    for t in ([a.target] if a.target else TARGETS):
        print("built:", build_target(t, a.out, a.lang))


if __name__ == "__main__":
    main()
