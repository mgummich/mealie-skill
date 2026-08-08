#!/usr/bin/env python3
"""
Mealie ueber die Anthropic API pflegen.

  optimize.py recipe <slug> [<slug> ...]
  optimize.py recipe --batch [--limit 20]
  optimize.py foods luecken|dubletten [--limit N]
  optimize.py units luecken|dubletten [--limit N]
  optimize.py organizers categories|tags|tools [--limit N]
  optimize.py cookbooks --zweck "Schnelle Feierabendkueche"
  optimize.py maintenance dubletten|links|diaet [--limit N]

  --dry-run   nur Plan zeigen, nichts schreiben
  --yes       ohne Rueckfrage ausfuehren

Kontext und Ausfuehrung laufen ueber mealie_ctx.py aus dem Antigravity-Skill;
dieses Skript ergaenzt Modellaufruf, Freigabe und Batch-Schleife.

Env: MEALIE_URL, MEALIE_TOKEN, ANTHROPIC_API_KEY
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
CTX = os.environ.get("MEALIE_CTX", os.path.join(
    HERE, "..", "antigravity", "skills", "mealie", "scripts", "mealie_ctx.py"))
AH = {
    "x-api-key": os.environ["ANTHROPIC_API_KEY"],
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}
MODEL = os.environ.get("MODEL", "claude-sonnet-4-6")

PROMPTS = {
    "recipe": "recipe.txt", "foods": "foods.txt", "units": "foods.txt",
    "organizers": "organizers.txt", "cookbooks": "cookbooks.txt",
    "maintenance": "maintenance.txt",
}


def ctx(*args):
    """mealie_ctx.py aufrufen und die Ausgabe zurueckgeben."""
    r = subprocess.run([sys.executable, CTX, *map(str, args)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"mealie_ctx {' '.join(map(str, args))} fehlgeschlagen:\n{r.stderr}")
    return r.stdout


def system_block(mode):
    """Gemeinsame Regeln + Modusregeln als EIN gecachter Block.

    Getrennte Bloecke waeren feiner, aber der gemeinsame Teil liegt unter
    der Cache-Mindestgroesse von 1024 Tokens und wuerde allein nicht greifen.
    """
    p = os.path.join(HERE, "prompts")
    text = (open(os.path.join(p, "common.txt"), encoding="utf-8").read()
            + "\n\n" + open(os.path.join(p, PROMPTS[mode]), encoding="utf-8").read())
    return [{"type": "text", "text": text,
             "cache_control": {"type": "ephemeral"}}]


def ask(mode, user_msg):
    body = {"model": MODEL, "max_tokens": 8000, "system": system_block(mode),
            "messages": [{"role": "user", "content": user_msg}]}
    r = requests.post("https://api.anthropic.com/v1/messages",
                      headers=AH, json=body, timeout=240)
    r.raise_for_status()
    d = r.json()
    return ("\n".join(b["text"] for b in d["content"] if b["type"] == "text"),
            d.get("usage", {}))


def extract_actions(text):
    for b in reversed(re.findall(r"```json\s*(.*?)```", text, re.S)):
        try:
            data = json.loads(b)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and "actions" in data:
            return data
    return None


def run(mode, task, user_msg, args, slug=None):
    print(f"\n{'=' * 62}\n{mode}: {task or slug}\n{'=' * 62}")
    text, usage = ask(mode, user_msg)
    print(text)
    print(f"\n[usage] {usage}")
    if args.dry_run:
        return
    data = extract_actions(text)
    if not data:
        print("!! Keine ACTIONS gefunden – uebersprungen.")
        return
    actions = data["actions"]
    destructive = sorted({a["op"] for a in actions if a["op"] in (
        "merge_food", "merge_unit", "delete_organizer", "retag_recipe")})
    if destructive:
        print(f"\n!! Destruktiv: {', '.join(destructive)} – Rezepte werden "
              "umgeschrieben bzw. Objekte geloescht.")
    if not args.yes:
        if input(f"\n{len(actions)} Aktionen ausfuehren? [j/N] ").strip().lower() != "j":
            print("Abgebrochen.")
            return
    with open(".actions.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print(ctx(*(["apply", ".actions.json"] + (["--slug", slug] if slug else []))))
    os.remove(".actions.json")


# ---------- Modi ----------
def mode_recipe(args):
    slugs = args.targets
    if args.batch and not slugs:
        out = ctx("audit", "recipes")
        slugs = [w for line in out.splitlines() if line.startswith("  ")
                 for w in line.replace("|", " ").split() if "-" in w][: args.limit or 20]
    if not slugs:
        sys.exit("Slug angeben oder --batch verwenden")
    for i, slug in enumerate(slugs):
        run("recipe", None, ctx("ctx", "recipe", slug) + "\nStarte mit Phase 1.",
            args, slug=slug)
        if i < len(slugs) - 1:
            time.sleep(1)   # zuegig bleiben: Cache lebt nur ~5 Minuten


def mode_table(args, kind):
    """foods / units – Luecken oder Dubletten."""
    task = (args.targets or ["luecken"])[0]
    if task == "luecken":
        body = ctx("ctx", kind, "--limit", args.limit or 25)
        head = f"AUFGABE: Luecken fuellen bei {kind}"
    else:
        body = ctx("audit", kind, "--limit", args.limit or 5)
        head = f"AUFGABE: Dubletten pruefen bei {kind}"
    run("foods", f"{kind}/{task}", f"{head}\n\n{body}\nStarte mit Phase 1.", args)


def mode_organizers(args):
    kind = (args.targets or ["tags"])[0]
    body = ctx("audit", kind, "--limit", args.limit or 5) + "\n" + ctx("ctx", kind)
    run("organizers", kind,
        f"AUFGABE: {kind} konsolidieren\n\n{body}\nStarte mit Phase 1.", args)


def mode_cookbooks(args):
    zweck = args.zweck or " ".join(args.targets) or "(offen – schlage sinnvolle vor)"
    run("cookbooks", "kochbuecher",
        f"AUFGABE: Kochbuch anlegen. Zweck: {zweck}\n\n"
        + ctx("ctx", "cookbooks") + "\nStarte mit Phase 1.", args)


def mode_maintenance(args):
    task = (args.targets or ["dubletten"])[0]
    if task == "dubletten":
        body = ctx("audit", "recipes", "--limit", args.limit or 15)
    elif task == "links":
        body = ctx("audit", "links", "--limit", args.limit or 25)
    else:
        body = ctx("ctx", "diet", "--limit", args.limit or 25)
    run("maintenance", task, f"AUFGABE: {task}\n\n{body}\nStarte mit Phase 1.", args)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["recipe", "foods", "units", "organizers",
                                    "cookbooks", "maintenance"])
    p.add_argument("targets", nargs="*")
    p.add_argument("--batch", action="store_true")
    p.add_argument("--limit", type=int)
    p.add_argument("--zweck")
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
