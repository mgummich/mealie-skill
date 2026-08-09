#!/usr/bin/env python3
"""
Maintain Mealie through the Anthropic API.

  optimize.py recipe <slug> [<slug> ...]
  optimize.py recipe --batch [--limit 20]
  optimize.py foods gaps|duplicates [--limit N]
  optimize.py units gaps|duplicates [--limit N]
  optimize.py organizers categories|tags|tools [--limit N]
  optimize.py cookbooks --purpose "Quick weeknight cooking"
  optimize.py maintenance duplicates|links|diet [--limit N]

  --dry-run   only show the plan, write nothing
  --yes       execute without asking

Context and execution go through skill/scripts/mealie_ctx.py; this script
adds the model call, the approval gate and the batch loop.

Env: MEALIE_URL, MEALIE_TOKEN, ANTHROPIC_API_KEY
     MEALIE_LANG   language of the recipe content (default: English)
     MODEL         model id (default: claude-sonnet-4-6)
"""
import os
import re
import sys
import json
import time
import argparse
import subprocess
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import build
CTX = os.environ.get("MEALIE_CTX", os.path.join(
    HERE, "..", "skill", "scripts", "mealie_ctx.py"))
AH = {
    "x-api-key": os.environ["ANTHROPIC_API_KEY"],
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}
MODEL = os.environ.get("MODEL", "claude-sonnet-4-6")

PROMPTS = {
    "recipe": "recipes.md", "foods": "foods.md", "units": "foods.md",
    "organizers": "organizers.md", "cookbooks": "cookbooks.md",
    "maintenance": "maintenance.md",
}


def ctx(*args):
    """Run mealie_ctx.py as a subprocess and return its stdout.

    The only way this script talks to Mealie: no HTTP access of its own,
    all API logic stays in the tool.

    Args:
        *args: Arguments for mealie_ctx.py; non-strings are converted.

    Returns:
        The stdout of the call.

    Raises:
        SystemExit: If the call exits non-zero; stderr is printed.
    """
    r = subprocess.run([sys.executable, CTX, *map(str, args)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"mealie_ctx {' '.join(map(str, args))} failed:\n{r.stderr}")
    return r.stdout


def system_block(mode):
    """Build common rules, ACTIONS format and mode rules as ONE cache block.

    ACTIONS format and mode rules are derived from skill/references/ at
    runtime (build.render_standalone) — one source, no prompt copies.
    Separate blocks would be finer grained, but the common part is below
    the 1024 token cache minimum and would not take effect on its own. The
    cache is therefore reused per mode, not across modes.

    The content language comes from $MEALIE_LANG (default English) and is
    substituted into all three parts.

    Args:
        mode: Key from PROMPTS, e.g. "recipe" or "maintenance".

    Returns:
        The system parameter for the Messages API: a single text block
        marked cache_control ephemeral.

    Raises:
        KeyError: If the mode is unknown.
        SystemExit: If a reference contains an unpaired marker.
        OSError: If a prompt or reference file cannot be read.
    """
    common = build.set_language(open(
        os.path.join(HERE, "prompts", "common.txt"), encoding="utf-8").read())
    refs = os.path.join(HERE, "..", "skill", "references")
    rendered = [build.render_standalone(
        open(os.path.join(refs, name), encoding="utf-8").read())
        for name in ("actions.md", PROMPTS[mode])]
    text = "\n\n".join([common] + rendered)
    return [{"type": "text", "text": text,
             "cache_control": {"type": "ephemeral"}}]


def ask(mode, user_msg):
    """Send one request to the Messages API and return text plus usage.

    Args:
        mode: Key from PROMPTS, selects the system block.
        user_msg: User message, usually context plus task.

    Returns:
        Tuple (concatenated text blocks, usage dict). The usage dict shows
        cache_creation_input_tokens on the first call of a mode and
        cache_read_input_tokens afterwards.

    Raises:
        requests.HTTPError: If the API answers with an error status.
    """
    body = {"model": MODEL, "max_tokens": 8000, "system": system_block(mode),
            "messages": [{"role": "user", "content": user_msg}]}
    r = requests.post("https://api.anthropic.com/v1/messages",
                      headers=AH, json=body, timeout=240)
    r.raise_for_status()
    d = r.json()
    return ("\n".join(b["text"] for b in d["content"] if b["type"] == "text"),
            d.get("usage", {}))


def extract_actions(text):
    """Pull the ACTIONS object out of a model answer.

    Scans the json code fences from the back, so a later corrected plan
    wins over an earlier draft. Blocks that do not parse are skipped.

    Args:
        text: Full model answer.

    Returns:
        The dict containing "actions", or None if the answer has no usable
        ACTIONS block.
    """
    for b in reversed(re.findall(r"```json\s*(.*?)```", text, re.S)):
        try:
            data = json.loads(b)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "actions" in data:
            return data
    return None


def run(mode, task, user_msg, args, slug=None):
    """Ask the model, get approval, apply the plan.

    Destructive operations are announced before the prompt. Under
    --dry-run nothing is written and no approval is asked for; without
    --yes an explicit "y" is required. The ACTIONS go to a temporary
    .actions.json, which mealie_ctx.py apply executes and which is removed
    afterwards.

    Args:
        mode: Key from PROMPTS.
        task: Label for the header line; falls back to slug.
        user_msg: User message with context and task.
        args: Parsed arguments; dry_run and yes are read.
        slug: Recipe slug, required for patch_recipe and set_image.

    Raises:
        SystemExit: If mealie_ctx.py apply fails.
        requests.HTTPError: If the API call fails.
    """
    print(f"\n{'=' * 62}\n{mode}: {task or slug}\n{'=' * 62}")
    text, usage = ask(mode, user_msg)
    print(text)
    print(f"\n[usage] {usage}")
    if args.dry_run:
        return
    data = extract_actions(text)
    if not data:
        print("!! No ACTIONS found - skipped.")
        return
    actions = data["actions"]
    destructive = sorted({a["op"] for a in actions if a["op"] in (
        "merge_food", "merge_unit", "delete_organizer", "retag_recipe")})
    if destructive:
        print(f"\n!! Destructive: {', '.join(destructive)} - recipes will be "
              "rewritten and objects deleted.")
    if not args.yes:
        if input(f"\nExecute {len(actions)} actions? [y/N] ").strip().lower() != "y":
            print("Aborted.")
            return
    with open(".actions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(ctx(*(["apply", ".actions.json"] + (["--slug", slug] if slug else []))))
    os.remove(".actions.json")


# ---------- modes ----------
def mode_recipe(args):
    """Work through recipes one by one.

    With --batch and without slugs the targets come from the recipe audit.
    Between runs there is a one second pause: the prompt cache lives about
    five minutes, so a batch should keep moving.

    Args:
        args: Parsed arguments with targets, batch and limit.

    Raises:
        SystemExit: If neither slugs nor --batch are given.
    """
    slugs = args.targets
    if args.batch and not slugs:
        out = ctx("audit", "recipes")
        slugs = [w for line in out.splitlines() if line.startswith("  ")
                 for w in line.replace("|", " ").split()
                 if "-" in w][: args.limit or 20]
    if not slugs:
        sys.exit("give a slug or use --batch")
    for i, slug in enumerate(slugs):
        run("recipe", None, ctx("ctx", "recipe", slug) + "\nStart with phase 1.",
            args, slug=slug)
        if i < len(slugs) - 1:
            time.sleep(1)   # keep moving: the cache lives about 5 minutes


def mode_table(args, kind):
    """Fill gaps or review duplicates in foods and units.

    Args:
        args: Parsed arguments; targets[0] selects the task, default
            "gaps", anything else means duplicates.
        kind: Either "foods" or "units".
    """
    task = (args.targets or ["gaps"])[0]
    if task == "gaps":
        body = ctx("ctx", kind, "--limit", args.limit or 25)
        head = f"TASK: fill the gaps in {kind}"
    else:
        body = ctx("audit", kind, "--limit", args.limit or 5)
        head = f"TASK: review the duplicates in {kind}"
    run("foods", f"{kind}/{task}", f"{head}\n\n{body}\nStart with phase 1.", args)


def mode_organizers(args):
    """Consolidate categories, tags or tools.

    The model gets both the audit and the full list, since retagging needs
    the usage figures of every object.

    Args:
        args: Parsed arguments; targets[0] selects the kind, default
            "tags".
    """
    kind = (args.targets or ["tags"])[0]
    body = ctx("audit", kind, "--limit", args.limit or 5) + "\n" + ctx("ctx", kind)
    run("organizers", kind,
        f"TASK: consolidate {kind}\n\n{body}\nStart with phase 1.", args)


def mode_cookbooks(args):
    """Create cookbooks as filter rules.

    Args:
        args: Parsed arguments; --purpose or the remaining targets give the
            purpose. Without either, the model suggests one itself.
    """
    purpose = args.purpose or " ".join(args.targets) or "(open - propose something)"
    run("cookbooks", "cookbooks",
        f"TASK: create a cookbook. Purpose: {purpose}\n\n"
        + ctx("ctx", "cookbooks") + "\nStart with phase 1.", args)


def mode_maintenance(args):
    """Review duplicate recipes, dead links or diet tags.

    Duplicate recipes are only presented; the tool never deletes a recipe.

    Args:
        args: Parsed arguments; targets[0] selects the task ("duplicates",
            "links", otherwise diet), default "duplicates".
    """
    task = (args.targets or ["duplicates"])[0]
    if task == "duplicates":
        body = ctx("audit", "recipes", "--limit", args.limit or 15)
    elif task == "links":
        body = ctx("audit", "links", "--limit", args.limit or 25)
    else:
        body = ctx("ctx", "diet", "--limit", args.limit or 25)
    run("maintenance", task, f"TASK: {task}\n\n{body}\nStart with phase 1.", args)


def main():
    """Parse the command line and dispatch to the mode function.

    Raises:
        SystemExit: On usage errors and from every mode that aborts.
    """
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["recipe", "foods", "units", "organizers",
                                    "cookbooks", "maintenance"])
    p.add_argument("targets", nargs="*")
    p.add_argument("--batch", action="store_true")
    p.add_argument("--limit", type=int)
    p.add_argument("--purpose")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--yes", action="store_true")
    a = p.parse_args()

    {"recipe": mode_recipe,
     "foods": lambda x: mode_table(x, "foods"),
     "units": lambda x: mode_table(x, "units"),
     "organizers": mode_organizers,
     "cookbooks": mode_cookbooks,
     "maintenance": mode_maintenance}[a.mode](a)


if __name__ == "__main__":
    main()
