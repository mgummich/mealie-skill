#!/usr/bin/env python3
"""
Mealie-Werkzeug: Kontext holen, pruefen, ACTIONS ausfuehren.

  index [--refresh]                    lokalen Rezeptindex bauen/erneuern
  ctx recipe <slug> [--search B ...]   Rezept + passende Foods + Organizer
  ctx <was> [--limit N] [--group G]    Arbeitspaket holen
       was: foods units categories tags tools cookbooks diet
  audit <was> [--limit N]              Luecken, Dubletten, Verwendung
       was: foods units categories tags tools recipes links
  usage <art> <id>                     Rezepte zu food/unit/category/tag/tool
  apply <actions.json> [--slug S] [--dry-run]

Der Index (.mealie_index.json) wird von allen audit-Befehlen genutzt und
liegt im aktuellen Verzeichnis. Bei Aenderungen an der Instanz: --refresh.

Env: MEALIE_URL, MEALIE_TOKEN
"""
import os
import re
import sys
import json
import time
import argparse
import requests

MEALIE = os.environ["MEALIE_URL"].rstrip("/")
MH = {"Authorization": f"Bearer {os.environ['MEALIE_TOKEN']}"}
INDEX = os.environ.get("MEALIE_INDEX", ".mealie_index.json")

# Endpunkte einmal gegen die eigene Instanz pruefen und hier anpassen.
EP = {
    "recipes": "/recipes",
    "foods": "/foods",
    "units": "/units",
    "labels": "/groups/labels",
    "categories": "/organizers/categories",
    "tags": "/organizers/tags",
    "tools": "/organizers/tools",
    "cookbooks": "/groups/cookbooks",
}
ORG = {"categories": "recipeCategory", "tags": "tags", "tools": "tools"}
CREATE_EP = {
    "create_label": "labels", "create_food": "foods", "create_unit": "units",
    "create_category": "categories", "create_tag": "tags",
    "create_tool": "tools", "create_cookbook": "cookbooks",
}
ORDER = [
    "create_label", "merge_food", "merge_unit", "create_food", "create_unit",
    "create_category", "create_tag", "create_tool", "update_food",
    "update_unit", "update_organizer", "retag_recipe", "delete_organizer",
    "create_cookbook", "update_cookbook", "patch_recipe", "set_image",
]

UMLAUT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
PLURAL = ("nen", "en", "er", "se", "n", "e", "s")
QTY = re.compile(r"[\d\u00bc-\u00be/.,\-]+|\(.*?\)")
STOP = {
    "g", "kg", "ml", "l", "el", "tl", "stk", "stueck", "stück", "prise",
    "dose", "packung", "bund", "cup", "cups", "tbsp", "tsp", "oz", "lb",
    "large", "small", "fresh", "chopped", "diced", "of", "and", "und",
    "zum", "zur", "fuer", "für", "nach", "etwas", "geschmack",
}


def norm(name):
    """Grobe Normalform fuer den Dublettenabgleich."""
    s = (name or "").lower().translate(UMLAUT)
    s = re.sub(r"[^a-z0-9]+", "", s)
    for suf in PLURAL:
        if len(s) > len(suf) + 3 and s.endswith(suf):
            return s[: -len(suf)]
    return s


def mreq(method, path, **kw):
    r = requests.request(method, f"{MEALIE}/api{path}", headers=MH, timeout=45, **kw)
    r.raise_for_status()
    return r.json() if r.text.strip() else {}


def mget(path, **params):
    d = mreq("GET", path, params={"perPage": 200, **params})
    return d.get("items", d) if isinstance(d, dict) else d


def brief(items):
    return ", ".join(f'{i["id"]}:{i["name"]}' for i in items)


# ---------- Index ----------
def build_index():
    recipes, page = [], 1
    while True:
        items = mget(EP["recipes"], page=page, perPage=100)
        if not items:
            break
        for r in items:
            f = mget(f"{EP['recipes']}/{r['slug']}")
            ings = f.get("recipeIngredient") or []
            recipes.append({
                "slug": f["slug"],
                "name": f.get("name"),
                "categories": [c["id"] for c in f.get("recipeCategory") or []],
                "tags": [t["id"] for t in f.get("tags") or []],
                "tools": [t["id"] for t in f.get("tools") or []],
                "foods": [i["food"]["id"] for i in ings if (i.get("food") or {}).get("id")],
                "foodNames": [i["food"]["name"] for i in ings if (i.get("food") or {}).get("id")],
                "units": [i["unit"]["id"] for i in ings if (i.get("unit") or {}).get("id")],
                "ings": len(ings),
                "unparsed": sum(1 for i in ings if not (i.get("food") or {}).get("id")),
                "image": bool(f.get("image")),
                "orgURL": f.get("orgURL") or f.get("originalURL"),
                "description": bool((f.get("description") or "").strip()),
            })
        page += 1
    data = {"built": time.time(), "recipes": recipes}
    json.dump(data, open(INDEX, "w", encoding="utf-8"), ensure_ascii=False)
    return data


def load_index(refresh=False):
    if refresh or not os.path.exists(INDEX):
        return build_index()
    return json.load(open(INDEX, encoding="utf-8"))


def counts(idx, field):
    c = {}
    for r in idx["recipes"]:
        for i in r[field]:
            c[i] = c.get(i, 0) + 1
    return c


# ---------- Dubletten ----------
def dupe_groups(items, extra_keys=None):
    by = {}
    for f in items:
        keys = {norm(f.get("name"))}
        if f.get("pluralName"):
            keys.add(norm(f["pluralName"]))
        for a in f.get("aliases") or []:
            keys.add(norm(a.get("name", "")))
        if extra_keys:
            keys |= {norm(k) for k in extra_keys(f)}
        for k in keys:
            if k:
                by.setdefault(k, {})[f["id"]] = f
    seen, groups = set(), []
    for k, members in by.items():
        if len(members) < 2:
            continue
        sig = tuple(sorted(members))
        if sig in seen:
            continue
        seen.add(sig)
        groups.append((k, list(members.values())))
    return groups


def gaps(f, kind="foods"):
    """Fehlende Felder. Units haben kein Label und keine Beschreibung."""
    out = []
    if not (f.get("pluralName") or "").strip():
        out.append("plural")
    if not (f.get("aliases") or []):
        out.append("aliase")
    if kind == "units":
        if not (f.get("abbreviation") or "").strip():
            out.append("abkuerzung")
        return out
    if not (f.get("description") or "").strip():
        out.append("beschreibung")
    if not f.get("labelId") and not (f.get("label") or {}).get("id"):
        out.append("label")
    return out


def food_line(f, kind="foods"):
    al = ",".join(a.get("name", "") for a in (f.get("aliases") or []))
    if kind == "units":
        return "{}|{}|{}|{}".format(
            f["id"], f["name"], f.get("pluralName") or "",
            f.get("abbreviation") or "")
    return "{}|{}|{}|{}|{}|{}".format(
        f["id"], f["name"], f.get("pluralName") or "",
        (f.get("label") or {}).get("name") or "", al,
        "+" if (f.get("description") or "").strip() else "-")


# ---------- audit ----------
def cmd_audit(a):
    what = a.what
    idx = load_index(a.refresh)
    R = idx["recipes"]

    if what in ("foods", "units"):
        items = mget(EP[what])
        used = counts(idx, what)
        print(f"{len(items)} {what} gesamt, {len(used)} davon verwendet")
        if what == "foods":
            g = {}
            for f in items:
                for x in gaps(f, what):
                    g[x] = g.get(x, 0) + 1
            print("LUECKEN: " + ", ".join(f"{k}={v}" for k, v in sorted(g.items())))
        unused = [i for i in items if not used.get(i["id"])]
        print(f"UNGENUTZT: {len(unused)}" + (
            " – " + ", ".join(i["name"] for i in unused[:15]) if unused else ""))
        groups = dupe_groups(items)
        print(f"\nDUBLETTENVERDACHT: {len(groups)} Gruppen")
        for k, ms in groups[: a.limit]:
            print("  [{}] {}".format(k, " | ".join(
                f'{m["name"]} ({m["id"][:8]}, {used.get(m["id"], 0)} Rez.)' for m in ms)))

    elif what in ORG:
        items = mget(EP[what])
        used = counts(idx, what)
        print(f"{len(items)} {what} gesamt")
        no_recipes = [i for i in items if not used.get(i["id"])]
        rare = [i for i in items if 0 < used.get(i["id"], 0) <= 2]
        print(f"UNGENUTZT: {len(no_recipes)}" + (
            " – " + ", ".join(i["name"] for i in no_recipes[:15]) if no_recipes else ""))
        print(f"SELTEN (1-2 Rezepte): {len(rare)}" + (
            " – " + ", ".join(f'{i["name"]}({used[i["id"]]})' for i in rare[:15]) if rare else ""))
        miss = [i["name"] for i in items if not (i["name"] or "").strip()]
        if miss:
            print(f"OHNE NAMEN: {len(miss)}")
        groups = dupe_groups(items)
        print(f"\nDUBLETTENVERDACHT: {len(groups)} Gruppen")
        for k, ms in groups[: a.limit]:
            print("  [{}] {}".format(k, " | ".join(
                f'{m["name"]} ({m["id"][:8]}, {used.get(m["id"], 0)} Rez.)' for m in ms)))
        print(f"\nGROESSTE: " + ", ".join(
            f'{i["name"]}({used.get(i["id"], 0)})'
            for i in sorted(items, key=lambda x: -used.get(x["id"], 0))[:10]))

    elif what == "recipes":
        by = {}
        for r in R:
            by.setdefault(norm(r["name"]), []).append(r)
        name_dupes = [v for v in by.values() if len(v) > 1]
        print(f"{len(R)} Rezepte, {len(name_dupes)} Namensdubletten")
        for grp in name_dupes[: a.limit]:
            print("  " + " | ".join(x["slug"] for x in grp))
        # Zutatenueberschneidung als zweiter Verdacht
        sets = [(r, set(r["foods"])) for r in R if len(r["foods"]) >= 4]
        seen, sim = set(), []
        for i, (r1, s1) in enumerate(sets):
            for r2, s2 in sets[i + 1:]:
                inter = len(s1 & s2)
                jac = inter / len(s1 | s2)
                if jac >= 0.6 and (r1["slug"], r2["slug"]) not in seen:
                    seen.add((r1["slug"], r2["slug"]))
                    sim.append((round(jac, 2), r1["slug"], r2["slug"]))
        sim.sort(reverse=True)
        print(f"\nZUTATENAEHNLICH (Jaccard >= 0.6): {len(sim)}")
        for j, s1, s2 in sim[: a.limit]:
            print(f"  {j}  {s1}  <->  {s2}")

    elif what == "links":
        no_img = [r["slug"] for r in R if not r["image"]]
        no_src = [r["slug"] for r in R if not r["orgURL"]]
        print(f"OHNE BILD: {len(no_img)}" + (
            " – " + ", ".join(no_img[:15]) if no_img else ""))
        print(f"OHNE QUELL-URL: {len(no_src)}")
        if not a.check_urls:
            print("\n(--check-urls setzen, um Quell-URLs auf Erreichbarkeit zu pruefen)")
            return
        dead = []
        for r in R:
            if not r["orgURL"]:
                continue
            try:
                resp = requests.head(r["orgURL"], timeout=10, allow_redirects=True)
                if resp.status_code >= 400:
                    dead.append((r["slug"], resp.status_code, r["orgURL"]))
            except requests.RequestException as e:
                dead.append((r["slug"], type(e).__name__, r["orgURL"]))
        print(f"\nTOTE QUELL-URLS: {len(dead)}")
        for slug, code, url in dead[: a.limit]:
            print(f"  {slug}  [{code}]  {url}")
    else:
        sys.exit(f"unbekannt: {what}")


# ---------- ctx ----------
def cmd_ctx(a):
    what = a.what

    if what == "recipe":
        recipe = mget(f"{EP['recipes']}/{a.slug}")
        terms = set(a.search or [])
        for ing in recipe.get("recipeIngredient", []) or []:
            raw = ((ing.get("food") or {}).get("name") or ing.get("originalText")
                   or ing.get("note") or "")
            raw = QTY.sub(" ", raw.lower())
            w = [x.strip(".,;:()") for x in re.split(r"[\s,/]+", raw) if x]
            w = [x for x in w if len(x) > 2 and x not in STOP]
            if w:
                terms.add(" ".join(w[:3]))
                terms.add(w[-1])
        hits = {}
        for t in terms:
            try:
                for f in mget(EP["foods"], search=t, perPage=5):
                    hits[f["id"]] = f
            except requests.HTTPError:
                continue
        print("REZEPT:")
        print(json.dumps(recipe, ensure_ascii=False, indent=1))
        print("\nFOODS (Vorsuche, id|name|plural|label|aliase|desc):")
        print("\n".join(food_line(f) for f in hits.values()) or "(keine)")
        print("\nUNITS: " + brief(mget(EP["units"])))
        print("LABELS: " + brief(mget(EP["labels"])))
        print("CATEGORIES: " + brief(mget(EP["categories"])))
        print("TAGS: " + brief(mget(EP["tags"])))
        print("TOOLS: " + brief(mget(EP["tools"])))
        return

    if what in ("foods", "units"):
        items = mget(EP[what])
        fmt = ("id|name|plural|abkuerzung" if what == "units"
               else "id|name|plural|label|aliase|beschreibung(+/-)")
        print(f"Format: {fmt}\n")
        if a.group:
            key = norm(a.group)
            sel = [f for f in items if norm(f["name"]) == key or any(
                norm(x.get("name", "")) == key for x in f.get("aliases") or [])]
            used = counts(load_index(), what)
            print("DUBLETTENGRUPPE:")
            for f in sel:
                print(f" {food_line(f, what)}  rezepte: {used.get(f['id'], 0)}")
                if (f.get("description") or "").strip():
                    print("   desc: " + f["description"][:160])
        else:
            sel = [f for f in items if gaps(f, what)][: a.limit]
            print(f"MIT LUECKEN ({len(sel)}):")
            for f in sel:
                print(f" {food_line(f, what)}  fehlt: {','.join(gaps(f, what))}")
        if what == "foods":
            print("\nLABELS: " + brief(mget(EP["labels"])))
        return

    if what in ORG:
        idx = load_index()
        items = mget(EP[what])
        used = counts(idx, what)
        print(f"{what.upper()} – id|name|rezepte")
        for i in sorted(items, key=lambda x: -used.get(x["id"], 0)):
            print(f' {i["id"]}|{i["name"]}|{used.get(i["id"], 0)}')
        if a.group:
            key = norm(a.group)
            ids = [i["id"] for i in items if norm(i["name"]) == key]
            print(f"\nREZEPTE der Gruppe [{a.group}]:")
            for r in idx["recipes"]:
                hit = [i for i in ids if i in r[what]]
                if hit:
                    print(f' {r["slug"]}  ({",".join(h[:8] for h in hit)})')
        return

    if what == "cookbooks":
        idx = load_index()
        print("VORHANDENE KOCHBUECHER:")
        for c in mget(EP["cookbooks"]):
            print(f' {c["id"]}|{c.get("name")}|{c.get("description", "")[:60]}')
        for kind in ORG:
            u = counts(idx, kind)
            items = mget(EP[kind])
            print(f"\n{kind.upper()} (id|name|rezepte):")
            for i in sorted(items, key=lambda x: -u.get(x["id"], 0)):
                print(f' {i["id"]}|{i["name"]}|{u.get(i["id"], 0)}')
        print(f'\nREZEPTE GESAMT: {len(idx["recipes"])}')
        return

    if what == "diet":
        idx = load_index()
        tags = {t["id"]: t["name"] for t in mget(EP["tags"])}
        sel = [r for r in idx["recipes"] if r["foods"]][: a.limit]
        print("Format: slug | vorhandene tags | zutaten\n")
        for r in sel:
            tn = ",".join(tags.get(t, "?") for t in r["tags"]) or "-"
            print(f' {r["slug"]} | {tn} | {", ".join(r["foodNames"])}')
        print("\nTAGS: " + brief(mget(EP["tags"])))
        return

    sys.exit(f"unbekannt: {what}")


def cmd_usage(a):
    idx = load_index()
    field = {"food": "foods", "unit": "units", "category": "categories",
             "tag": "tags", "tool": "tools"}[a.kind]
    hits = [r["slug"] for r in idx["recipes"] if a.id in r[field]]
    print(f"{len(hits)} Rezepte:")
    for h in hits:
        print("  " + h)


# ---------- apply ----------
def resolve(value, refs):
    if isinstance(value, str) and value.startswith("$ref:"):
        key = value[5:]
        if key not in refs:
            raise KeyError(f"unbekannte Referenz $ref:{key}")
        return refs[key]
    if isinstance(value, dict):
        return {k: resolve(v, refs) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, refs) for v in value]
    return value


def cmd_apply(a):
    actions = json.load(open(a.file, encoding="utf-8"))["actions"]
    bad = [x["op"] for x in actions if x["op"] not in ORDER]
    if bad:
        sys.exit(f"Unbekannte Operationen: {bad}")
    idxmap = {op: i for i, op in enumerate(ORDER)}
    seq = [idxmap[x["op"]] for x in actions]
    if seq != sorted(seq):
        sys.exit("Reihenfolge verletzt – erlaubt ist:\n  " + " -> ".join(ORDER))
    if any(x["op"] in ("merge_food", "merge_unit", "delete_organizer")
           for x in actions) and not a.dry_run:
        print("!! Enthaelt destruktive Operationen (merge/delete). "
              "Rezepte werden umgeschrieben, Objekte geloescht.\n")

    refs = {}
    for x in actions:
        op, payload = x["op"], x.get("payload", {})
        if a.dry_run:
            print(f"[dry-run] {op}: {json.dumps(payload, ensure_ascii=False)[:220]}")
            if x.get("id_as"):
                refs[x["id_as"]] = "<neue-id>"
            continue
        payload = resolve(payload, refs)

        if op in CREATE_EP:
            res = mreq("POST", EP[CREATE_EP[op]], json=payload)
            if x.get("id_as"):
                refs[x["id_as"]] = res.get("id")
            print(f'ANGELEGT {op[7:]} – {payload.get("name")} – {res.get("id")}')
        elif op in ("merge_food", "merge_unit"):
            kind = "foods" if op == "merge_food" else "units"
            mreq("PUT", f"{EP[kind]}/merge",
                 json={"fromFood" if kind == "foods" else "fromUnit": payload["from"],
                       "toFood" if kind == "foods" else "toUnit": payload["to"]})
            print(f'ZUSAMMENGEFUEHRT {kind} {payload["from"]} -> {payload["to"]}')
        elif op in ("update_food", "update_unit"):
            kind = "foods" if op == "update_food" else "units"
            fid = payload.pop("id")
            cur = mreq("GET", f"{EP[kind]}/{fid}")
            mreq("PUT", f"{EP[kind]}/{fid}", json={**cur, **payload})
            print(f'AKTUALISIERT {kind} – {cur.get("name")} – ' + ", ".join(payload))
        elif op == "update_organizer":
            kind = payload.pop("kind")
            oid = payload.pop("id")
            cur = mreq("GET", f"{EP[kind]}/{oid}")
            mreq("PUT", f"{EP[kind]}/{oid}", json={**cur, **payload})
            print(f'AKTUALISIERT {kind} – {cur.get("name")} – ' + ", ".join(payload))
        elif op == "retag_recipe":
            kind = payload["kind"]
            field = ORG[kind]
            rec = mreq("GET", f'{EP["recipes"]}/{payload["slug"]}')
            cur = rec.get(field) or []
            rm = set(payload.get("remove", []))
            new = [c for c in cur if c["id"] not in rm]
            have = {c["id"] for c in new}
            for add_id in payload.get("add", []):
                if add_id not in have:
                    obj = mreq("GET", f"{EP[kind]}/{add_id}")
                    new.append(obj)
            mreq("PATCH", f'{EP["recipes"]}/{payload["slug"]}', json={field: new})
            print(f'UMGEHAENGT {payload["slug"]} {kind}: '
                  f'+{len(payload.get("add", []))} -{len(rm)}')
        elif op == "delete_organizer":
            mreq("DELETE", f'{EP[payload["kind"]]}/{payload["id"]}')
            print(f'GELOESCHT {payload["kind"]} {payload["id"]}')
        elif op == "update_cookbook":
            cid = payload.pop("id")
            cur = mreq("GET", f'{EP["cookbooks"]}/{cid}')
            mreq("PUT", f'{EP["cookbooks"]}/{cid}', json={**cur, **payload})
            print(f'AKTUALISIERT cookbook – {cur.get("name")}')
        elif op == "patch_recipe":
            if not a.slug:
                sys.exit("patch_recipe braucht --slug")
            mreq("PATCH", f'{EP["recipes"]}/{a.slug}', json=payload)
            print("GEPATCHT " + ", ".join(payload))
        elif op == "set_image":
            if not a.slug:
                sys.exit("set_image braucht --slug")
            mreq("POST", f'{EP["recipes"]}/{a.slug}/image',
                 json={"url": payload["url"], "includeTags": False})
            print("BILD " + payload["url"])

    if not a.dry_run and os.path.exists(INDEX):
        os.remove(INDEX)
        print("(Index verworfen – beim naechsten audit neu gebaut)")


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("index", help="Rezeptindex bauen")
    i.add_argument("--refresh", action="store_true")
    i.set_defaults(func=lambda a: print(
        f'{len(load_index(True)["recipes"])} Rezepte indiziert -> {INDEX}'))

    c = sub.add_parser("ctx", help="Arbeitspaket holen")
    c.add_argument("what")
    c.add_argument("slug", nargs="?")
    c.add_argument("--search", nargs="*")
    c.add_argument("--limit", type=int, default=25)
    c.add_argument("--group")
    c.set_defaults(func=cmd_ctx)

    d = sub.add_parser("audit", help="Luecken, Dubletten, Verwendung")
    d.add_argument("what")
    d.add_argument("--limit", type=int, default=25)
    d.add_argument("--refresh", action="store_true")
    d.add_argument("--check-urls", action="store_true")
    d.set_defaults(func=cmd_audit)

    u = sub.add_parser("usage", help="Rezepte zu einem Objekt")
    u.add_argument("kind", choices=["food", "unit", "category", "tag", "tool"])
    u.add_argument("id")
    u.set_defaults(func=cmd_usage)

    ap = sub.add_parser("apply", help="ACTIONS ausfuehren")
    ap.add_argument("file")
    ap.add_argument("--slug")
    ap.add_argument("--dry-run", action="store_true")
    ap.set_defaults(func=cmd_apply)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
