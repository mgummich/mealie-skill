#!/usr/bin/env python3
"""Mealie tool: fetch context, run checks, execute ACTIONS.

  setup [--check]                      check the connection, store credentials
  index [--refresh]                    build/refresh the local recipe index
  ctx recipe <slug> [--search T ...]   recipe + matching foods + organizers
  ctx <what> [--limit N] [--group G]   fetch a work package
       what: foods units categories tags tools cookbooks diet
  audit <what> [--limit N]             gaps, duplicates, usage
       what: foods units labels categories tags tools recipes links extras
  usage <kind> <id>                    recipes using a food/unit/category/tag/tool
  apply <actions.json> [--slug S] [--dry-run]

The index (.mealie_index.json) is used by every audit command and lives in
the current directory. After changes to the instance: --refresh.

Every applied action lands in .mealie.changelog.jsonl with the state it
overwrote - there is no other way back from a merge or a delete.

Env: MEALIE_URL, MEALIE_TOKEN — or a .mealie.env (written by "setup") or
.env in the current directory.
"""
import argparse
import getpass
import json
import os
import re
import sys
import time

import requests

INDEX = os.environ.get("MEALIE_INDEX", ".mealie_index.json")
# Raised whenever build_index learns a field an audit reads. An older index
# is rebuilt rather than silently audited on fields it does not carry.
INDEX_VERSION = 2
# Every applied action with the state it overwrote. Mealie has no undo and
# this tool has no rollback, so the changelog is the only way back: it is
# written before the next action runs, not at the end of the run.
CHANGELOG = os.environ.get("MEALIE_CHANGELOG", ".mealie.changelog.jsonl")
# Per-instance decisions the rule set wants recorded once: locale,
# category axis, container assumptions, the bare-food default table.
HOUSE_FILE = os.environ.get("MEALIE_RULES", ".mealie.rules.json")
ENV_FILE = os.environ.get("MEALIE_ENV", ".mealie.env")
ENV_FALLBACK = ".env"           # read as well, never written by setup
ENV_KEYS = ("MEALIE_URL", "MEALIE_TOKEN")
# Other Mealie tools name the same two values differently: mcp-mealie shares
# MEALIE_URL but calls the token MEALIE_API_TOKEN, other servers use
# MEALIE_BASE_URL/MEALIE_API_KEY. Accepting all of them means one env file
# serves every tool; the canonical names win when a file or the environment
# carries both.
ENV_ALIASES = {"MEALIE_BASE_URL": "MEALIE_URL",
               "MEALIE_API_TOKEN": "MEALIE_TOKEN",
               "MEALIE_API_KEY": "MEALIE_TOKEN"}
# HTTP 429 from Mealie's rate limiter: wait and try again rather than lose a
# half-built index. Retry-After wins when the response carries it.
RETRIES = 5
BACKOFF = 2.0
_CONN = None

# Check these endpoints against your own instance once and adjust them here.
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
# Recipe fields Mealie replaces wholesale on a PATCH. A payload carrying
# three ingredient lines does not add three lines, it leaves the recipe with
# exactly those three. Shortening one of them is therefore a deletion, which
# is what _guard_recipe_lists refuses without an explicit "replace".
RECIPE_LISTS = ("recipeIngredient", "recipeInstructions", "notes", "tags",
                "recipeCategory", "tools", "assets", "extras")

ORDER = [
    "create_label", "merge_food", "merge_unit", "create_food", "create_unit",
    "create_category", "create_tag", "create_tool", "update_food",
    "update_unit", "update_organizer", "retag_recipe", "delete_organizer",
    "delete_food", "delete_unit",
    "create_cookbook", "update_cookbook", "patch_recipe", "set_image",
]
# Kinds update_organizer and delete_organizer accept. Labels are organizers
# to this format even though they hang off a food rather than a recipe;
# retag_recipe deliberately does not take them, there is nothing to retag.
ORG_KINDS = ("categories", "tags", "tools", "labels")

# Duplicate matching is tuned for German and English recipe data: umlaut
# folding, German plural endings (which cover the English "s" and "es") and
# a stop word list holding both languages. Other languages still work, but
# the heuristic finds fewer pairs there.
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
    """Reduce a name to a coarse normal form for duplicate matching.

    Lowercases, folds umlauts, drops every non-alphanumeric character and
    strips one common German plural suffix. Deliberately lossy: it groups
    Tomate/Tomaten, not Ei/Eier.

    Args:
        name: Raw name; None and empty string are allowed.

    Returns:
        The normalized key, possibly an empty string.
    """
    s = (name or "").lower().translate(UMLAUT)
    s = re.sub(r"[^a-z0-9]+", "", s)
    for suf in PLURAL:
        if len(s) > len(suf) + 3 and s.endswith(suf):
            return s[: -len(suf)]
    return s


def parse_env(text):
    """Read KEY=VALUE lines from an env file.

    Comments, blank lines, a leading "export " and quotes around the value
    are tolerated; unknown keys are ignored. The ENV_ALIASES names are read
    under their canonical key, but lose against it.

    Args:
        text: Content of the env file.

    Returns:
        A dict with the recognized keys from ENV_KEYS.
    """
    out, aliased = {}, {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        val = val.strip().strip("'\"")
        if key in ENV_ALIASES:
            aliased[ENV_ALIASES[key]] = val
        elif key in ENV_KEYS:
            out[key] = val
    return {**aliased, **out}


def read_cfg():
    """Collect URL and token from the environment and the env files.

    The environment wins, then ENV_FILE, then ENV_FALLBACK (a plain .env, as
    written by other tools) - all relative to the current directory. Nothing
    is validated here.

    Returns:
        A dict with the keys from ENV_KEYS that have a value.

    Raises:
        SystemExit: If an env file exists but cannot be read.
    """
    cfg = {**{canon: os.environ[name]
              for name, canon in ENV_ALIASES.items() if os.environ.get(name)},
           **{k: os.environ[k] for k in ENV_KEYS if os.environ.get(k)}}
    for path in dict.fromkeys((ENV_FILE, ENV_FALLBACK)):
        if len(cfg) == len(ENV_KEYS):
            break
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                file_cfg = parse_env(fh.read())
        except OSError as e:
            sys.exit(f"{path} unreadable: {e}")
        cfg = {**file_cfg, **cfg}
    return cfg


def conn():
    """Resolve the Mealie base URL and the auth header, cached per process.

    Returns:
        A (base_url, headers) tuple.

    Raises:
        SystemExit: If URL or token are configured nowhere.
    """
    global _CONN
    if _CONN:
        return _CONN
    cfg = read_cfg()
    missing = [k for k in ENV_KEYS if not cfg.get(k)]
    if missing:
        sys.exit(f"{', '.join(missing)} not set – neither in the environment "
                 f"nor in {ENV_FILE} or {ENV_FALLBACK}. Run:\n"
                 f"  python3 {os.path.basename(__file__)} setup\n"
                 "or export the variables by hand (token: Mealie -> Profile "
                 "-> API Tokens).")
    _CONN = (cfg["MEALIE_URL"].rstrip("/"),
             {"Authorization": f"Bearer {cfg['MEALIE_TOKEN']}"})
    return _CONN


def mreq(method, path, **kw):
    """Send one authenticated request to the Mealie API.

    Args:
        method: HTTP method, e.g. "GET" or "PATCH".
        path: Path below /api, starting with a slash.
        **kw: Passed through to requests.request (json, params, ...).

    A 429 is retried up to RETRIES times, waiting for Retry-After or an
    exponential backoff. Every other status is left to the caller. This is
    the single choke point for the API, so reads and writes alike are
    covered - including the sanitize() pass on every writing body.

    Returns:
        The parsed JSON body, or an empty dict for an empty response.

    Raises:
        requests.HTTPError: If the response status is 4xx or 5xx, 429
            included once the retries are used up.
    """
    base, headers = conn()
    if method in ("POST", "PUT", "PATCH") and "json" in kw:
        kw["json"] = sanitize(kw["json"])
    for attempt in range(RETRIES):
        r = requests.request(method, f"{base}/api{path}", headers=headers,
                             timeout=45, **kw)
        if r.status_code != 429 or attempt == RETRIES - 1:
            break
        try:
            wait = float(r.headers.get("Retry-After", ""))
        except ValueError:
            wait = 0.0
        time.sleep(max(wait, BACKOFF * (attempt + 1)))
    r.raise_for_status()
    return r.json() if r.text.strip() else {}


def mget(path, **params):
    """GET a Mealie endpoint and unwrap the paginated envelope.

    Args:
        path: Path below /api, starting with a slash.
        **params: Query parameters; perPage defaults to 200 on collections.

    Returns:
        The "items" list for paginated endpoints, otherwise the body itself.

    Raises:
        requests.HTTPError: If the response status is 4xx or 5xx.
    """
    # Only collections paginate. A single object answers under its own path,
    # and pagination parameters on that path are at best ignored.
    if path in EP.values():
        params = {"perPage": 200, **params}
    d = mreq("GET", path, params=params)
    if not isinstance(d, dict) or "items" not in d:
        return d
    items = d["items"]
    # A page is not the table. An instance with 225 foods answers the first
    # 200 and says so in total_pages; without following it every audit,
    # every duplicate check and every name collision guard silently works
    # on a subset. Callers that drive pagination themselves (build_index)
    # pass "page" and keep control.
    if "page" not in params:
        for page in range(2, (d.get("total_pages") or 1) + 1):
            nxt = mreq("GET", path, params={**params, "page": page})
            items += (nxt or {}).get("items", [])
    return items


# Fields of a recipe that no mode reads and none writes: bookkeeping,
# per-object timestamps and the rendered duplicates of data that is already
# there. Dropping them shrinks a `ctx recipe` by roughly half, measured over
# a 259 recipe library. The ratio rises with the ingredient count - every
# ingredient drags a full food and unit object along, most of it noise - and
# falls for recipes whose bulk is prose, which is kept in full.
NOISE = {
    "userId", "groupId", "householdId", "dateAdded", "dateUpdated",
    "createdAt", "updatedAt", "lastMade", "assets", "comments", "extras",
    "settings", "isOcrRecipe", "imageDir", "display", "summary",
    "householdsWithIngredientFood", "onHand", "labelId", "label",
    "aliases", "fraction", "useAbbreviation", "slug",
}


# Fields the API returns but refuses to take back. Mealie serves objects
# with their own bookkeeping attached; sending that bookkeeping into a write
# makes the backend validate a shape it never accepts and answer 500 rather
# than 422. Every write that starts from a GET - retag_recipe, the update_*
# operations - would otherwise carry them.
WRITE_NOISE = {
    "createdAt", "updatedAt", "update_at", "dateAdded", "dateUpdated",
    "householdsWithIngredientFood", "label",
}


def sanitize(value):
    """Drop fields no write accepts, recursively.

    Unlike slim() this keeps empty and null values: a write body says what a
    field should become, and "" or null is a legitimate answer.

    Args:
        value: Any fragment of a request body.

    Returns:
        The fragment without the WRITE_NOISE keys, at every depth.
    """
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()
                if k not in WRITE_NOISE}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


def slim(value, keep_slug=False):
    """Strip bookkeeping fields from an API object, recursively.

    A blacklist rather than a whitelist: fields Mealie adds later survive,
    only the known noise goes. The recipe slug is kept at the top level
    because every write needs it.

    Args:
        value: Any fragment of a decoded API response.
        keep_slug: Keep the "slug" key at this level.

    Returns:
        The fragment without the noise fields and without empty nutrition
        or null entries.
    """
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in NOISE and not (k == "slug" and keep_slug):
                continue
            if v is None or v == "" or v == [] or v == {}:
                continue
            out[k] = slim(v)
        return out
    if isinstance(value, list):
        return [slim(v) for v in value]
    return value


def brief(items):
    """Format objects as a compact "id:name, id:name" line.

    Args:
        items: Objects carrying "id" and "name".

    Returns:
        One comma-separated line for the model context.
    """
    return ", ".join(f'{i["id"]}:{i["name"]}' for i in items)


# ---------- index ----------
def build_index():
    """Walk every recipe once and write the local index to disk.

    The only place that fetches all recipes individually. Every audit reads
    the resulting file instead of looping over the API again.

    A recipe the instance cannot serve is skipped, not fatal: Mealie answers
    500 for recipes it fails to serialize, and a single one of those used to
    cost the whole index. The slugs are kept in the index so `audit recipes`
    can name them long after the build scrolled away.

    Returns:
        The index dict: {"built": epoch seconds, "recipes": [...],
        "failed": [slugs]}, where each recipe carries slug, name, organizer
        ids, food/unit ids, food names, ingredient, step and unparsed
        counts, image flag, source URL and a description flag.

    Raises:
        requests.HTTPError: If a recipe *list* request fails; failures on a
            single recipe are collected instead.
        OSError: If the index file cannot be written.
    """
    recipes, failed, page = [], [], 1
    while True:
        items = mget(EP["recipes"], page=page, perPage=100)
        if not items:
            break
        for r in items:
            try:
                f = mget(f"{EP['recipes']}/{r['slug']}")
            except requests.HTTPError as e:
                failed.append(r["slug"])
                print(f"skipped {r['slug']}: "
                      f"{e.response.status_code} from the instance",
                      file=sys.stderr)
                continue
            ings = f.get("recipeIngredient") or []
            notes = f.get("notes") or []
            recipes.append({
                "slug": f["slug"],
                "name": f.get("name"),
                "notes": [(n.get("title") or "") for n in notes
                          if isinstance(n, dict)],
                "extras": sorted((f.get("extras") or {}).keys()),
                "rating": f.get("rating"),
                "lastMade": bool(f.get("lastMade")),
                # lines whose amount ended up as prose in the note, and
                # lines with no evidence of what was imported
                "amountInNote": sum(
                    1 for i in ings
                    if not (i.get("unit") or {}).get("id")
                    and re.search(r"\d", i.get("note") or "")),
                "noOriginalText": sum(
                    1 for i in ings if not (i.get("originalText") or "").strip()),
                "converted": sum(
                    1 for i in ings if "Original:" in (i.get("note") or "")),
                "categories": [c["id"] for c in f.get("recipeCategory") or []],
                "tags": [t["id"] for t in f.get("tags") or []],
                "tools": [t["id"] for t in f.get("tools") or []],
                "foods": [i["food"]["id"] for i in ings
                          if (i.get("food") or {}).get("id")],
                "foodNames": [i["food"]["name"] for i in ings
                              if (i.get("food") or {}).get("id")],
                "units": [i["unit"]["id"] for i in ings
                          if (i.get("unit") or {}).get("id")],
                "ings": len(ings),
                "steps": len(f.get("recipeInstructions") or []),
                "unparsed": sum(1 for i in ings if not (i.get("food") or {}).get("id")),
                "image": bool(f.get("image")),
                "orgURL": f.get("orgURL") or f.get("originalURL"),
                "description": bool((f.get("description") or "").strip()),
            })
        page += 1
    data = {"built": time.time(), "version": INDEX_VERSION,
            "recipes": recipes, "failed": failed}
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


def load_index(refresh=False):
    """Return the index, rebuilding it when missing or explicitly refreshed.

    Args:
        refresh: Force a rebuild even if the index file exists.

    Returns:
        The index dict as described in build_index.
    """
    if refresh or not os.path.exists(INDEX):
        return build_index()
    idx = json.load(open(INDEX, encoding="utf-8"))
    if idx.get("version") != INDEX_VERSION:
        print("(index predates the current fields – rebuilding)",
              file=sys.stderr)
        return build_index()
    return idx


def counts(idx, field):
    """Count how many recipes reference each id of one index field.

    Args:
        idx: Index dict from load_index.
        field: Index field to tally, e.g. "foods", "tags" or "tools".

    Returns:
        Mapping of object id to number of recipes using it. Ids that appear
        in no recipe are absent, not zero.
    """
    c: dict = {}
    for r in idx["recipes"]:
        for i in r[field]:
            c[i] = c.get(i, 0) + 1
    return c


# ---------- duplicates ----------
def dupe_groups(items, extra_keys=None):
    """Group objects that share a normalized name, plural or alias.

    A suspicion, never a verdict: the model reviews each group before
    anything is merged.

    Args:
        items: Objects with "id" and "name", optionally "pluralName" and
            "aliases".
        extra_keys: Optional callable returning further raw strings to
            normalize and match on for one object.

    Returns:
        List of (key, members) tuples with two or more members each. Groups
        with an identical member set appear once.
    """
    by: dict = {}
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
    """List the empty fields of a food or unit.

    Units are checked for abbreviation instead of description and label,
    which they do not have.

    Args:
        f: Food or unit object.
        kind: Either "foods" or "units".

    Returns:
        Names of the missing fields, e.g. ["plural", "label"]. Empty when
        the object is complete.
    """
    out = []
    if not (f.get("pluralName") or "").strip():
        out.append("plural")
    if not (f.get("aliases") or []):
        out.append("aliases")
    if kind == "units":
        if not (f.get("abbreviation") or "").strip():
            out.append("abbreviation")
        return out
    if not (f.get("description") or "").strip():
        out.append("description")
    if not f.get("labelId") and not (f.get("label") or {}).get("id"):
        out.append("label")
    return out


def food_line(f, kind="foods"):
    """Render one food or unit as a pipe-separated context line.

    Args:
        f: Food or unit object.
        kind: "foods" gives id|name|plural|label|aliases|desc(+/-),
            "units" gives id|name|plural|abbreviation.

    Returns:
        A single line without trailing newline.
    """
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
def alias_collisions(items):
    """Find strings that are a lookup key on more than one object.

    An alias reachable from two foods makes matching non-deterministic:
    the parser picks one arbitrarily, and which one can change between
    runs. The rule set calls this a hard error rather than a finding.

    Args:
        items: Foods or units with "name", "pluralName" and "aliases".

    Returns:
        Mapping of the colliding string to the names holding it, sorted.
    """
    by: dict = {}
    for it in items:
        keys = {(it.get(k) or "").strip().casefold()
                for k in ("name", "pluralName")}
        keys |= {(al.get("name") or "").strip().casefold()
                 for al in it.get("aliases") or []}
        for key in keys - {""}:
            by.setdefault(key, set()).add(it.get("name") or it["id"])
    return {k: sorted(v) for k, v in sorted(by.items()) if len(v) > 1}


def abbrev_collisions(units):
    """Find abbreviations that sit on more than one unit.

    Args:
        units: Unit records.

    Returns:
        Mapping of the abbreviation to the unit names holding it.
    """
    by: dict = {}
    for u in units:
        for key in {(u.get(k) or "").strip().casefold()
                    for k in ("abbreviation", "pluralAbbreviation")} - {""}:
            by.setdefault(key, set()).add(u.get("name") or u["id"])
    return {k: sorted(v) for k, v in sorted(by.items()) if len(v) > 1}


def non_metric(units, conv):
    """List the units that the rule set converts rather than stores.

    Args:
        units: Unit records from the instance.
        conv: Conversions data for the content language.

    Returns:
        The matching unit records.
    """
    canons = list(conv["forbidden"]) + list(conv.get("forbiddenAmbiguous", []))
    spellings = {c.casefold() for c in canons}
    for canon in canons:
        spellings |= {v.casefold()
                      for v in conv["unitVariants"].get(canon, [canon])}
    return [u for u in units
            if {(u.get(k) or "").strip().casefold()
                for k in ("name", "pluralName", "abbreviation")} & spellings]


def _share(part, whole):
    """Format a count as "n (x %)" against a total.

    Args:
        part: The counted subset.
        whole: The total; zero yields "0".

    Returns:
        The formatted string.
    """
    if not whole:
        return "0"
    return f"{part} ({round(100 * part / whole)} %)"


def cmd_audit(a):
    """Print gaps, duplicate suspicions and usage figures. Writes nothing.

    Reads the index rather than looping over recipes; only the object lists
    themselves (foods, units, organizers) come from the API.

    Args:
        a: Parsed arguments with what (foods, units, categories, tags,
            tools, recipes, links), limit, refresh and check_urls.

    Raises:
        SystemExit: If "what" is unknown.
        requests.HTTPError: If a Mealie request fails. Unreachable source
            URLs under --check-urls are reported, not raised.
    """
    what = a.what
    line = house_line()
    if line:
        print(line)
    idx = load_index(a.refresh)
    R = idx["recipes"]

    if what in ("foods", "units"):
        items = mget(EP[what])
        used = counts(idx, what)
        lint = load_data("lint.json", getattr(a, "lang", None))
        print(f"{len(items)} {what} in total, {len(used)} of them in use")
        clash = alias_collisions(items)
        if clash:
            print(f"!! ALIAS COLLISIONS ({len(clash)}, hard error – matching "
                  "is non-deterministic until these are resolved):")
            for key, names in list(clash.items())[: a.limit]:
                print(f'   "{key}" on {", ".join(names)}')
        if what == "foods":
            g: dict = {}
            for f in items:
                for x in gaps(f, what):
                    g[x] = g.get(x, 0) + 1
            print("GAPS: " + ", ".join(f"{k}={v}" for k, v in sorted(g.items())))
            no_label = [f for f in items if not f.get("labelId")]
            print("WITHOUT LABEL: " + _share(len(no_label), len(items))
                  + " – they land unsorted at the end of every shopping list")
            limit = lint["foodDescriptionMax"]
            long_desc = [f["name"] for f in items
                         if len(f.get("description") or "") > limit]
            if long_desc:
                print(f"DESCRIPTION OVER {limit} CHARACTERS: {len(long_desc)}")
            if lint["foodNameCase"] == "lower":
                wrong = [f["name"] for f in items
                         if f["name"] != (f["name"] or "").lower()]
                print(f"NAME NOT LOWERCASE: {len(wrong)}" + (
                    " – " + ", ".join(wrong[:10]) if wrong else ""))
        else:
            conv = load_data("conversions.json", getattr(a, "lang", None))
            bad = non_metric(items, conv)
            print(f"NON-METRIC ({len(bad)}, the conversion worklist):" if bad
                  else "NON-METRIC: 0")
            for u in sorted(bad, key=lambda u: -used.get(u["id"], 0)):
                n = used.get(u["id"], 0)
                print(f'   {u["name"]} – {n} recipe' + ("s" if n != 1 else ""))
            abbr = abbrev_collisions(items)
            if abbr:
                print(f"!! ABBREVIATION COLLISIONS ({len(abbr)}, hard error):")
                for key, names in abbr.items():
                    print(f'   "{key}" on {", ".join(names)}')
            missing = [u["name"] for u in items
                       if not (u.get("abbreviation") or "").strip()]
            print(f"WITHOUT ABBREVIATION: {len(missing)}" + (
                " – " + ", ".join(missing[:10]) if missing else ""))
        unused = [i for i in items if not used.get(i["id"])]
        print(f"UNUSED: {len(unused)}" + (
            " – " + ", ".join(i["name"] for i in unused[:15]) if unused else ""))
        groups = dupe_groups(items)
        print(f"\nPOSSIBLE DUPLICATES: {len(groups)} groups")
        for k, ms in groups[: a.limit]:
            print("  [{}] {}".format(k, " | ".join(
                f'{m["name"]} ({m["id"][:8]}, {used.get(m["id"], 0)} rec.)'
                for m in ms)))

    elif what in ORG:
        items = mget(EP[what])
        used = counts(idx, what)
        print(f"{len(items)} {what} in total")
        no_recipes = [i for i in items if not used.get(i["id"])]
        rare = [i for i in items if 0 < used.get(i["id"], 0) <= 2]
        print(f"UNUSED: {len(no_recipes)}" + (
            " – " + ", ".join(i["name"] for i in no_recipes[:15])
            if no_recipes else ""))
        print(f"RARE (1-2 recipes): {len(rare)}" + (
            " – " + ", ".join(f'{i["name"]}({used[i["id"]]})' for i in rare[:15])
            if rare else ""))
        miss = [i["name"] for i in items if not (i["name"] or "").strip()]
        if miss:
            print(f"WITHOUT A NAME: {len(miss)}")
        groups = dupe_groups(items)
        print(f"\nPOSSIBLE DUPLICATES: {len(groups)} groups")
        for k, ms in groups[: a.limit]:
            print("  [{}] {}".format(k, " | ".join(
                f'{m["name"]} ({m["id"][:8]}, {used.get(m["id"], 0)} rec.)'
                for m in ms)))
        print("\nLARGEST: " + ", ".join(
            f'{i["name"]}({used.get(i["id"], 0)})'
            for i in sorted(items, key=lambda x: -used.get(x["id"], 0))[:10]))

        lint = load_data("lint.json", getattr(a, "lang", None))
        cap = {"categories": "maxCategories", "tags": "maxTags",
               "tools": "maxTools"}[what]
        over = [r["slug"] for r in R if len(r[what]) > lint[cap]]
        print(f"OVER THE CAP OF {lint[cap]}: {len(over)} recipes" + (
            " – " + ", ".join(over[:10]) if over else ""))
        if what == "categories":
            avg = sum(len(r["categories"]) for r in R) / (len(R) or 1)
            note = " – above 1.5 the axis has collapsed" if avg > 1.5 else ""
            print(f"AVERAGE PER RECIPE: {avg:.2f}{note}")
            none = [r["slug"] for r in R if not r["categories"]]
            print(f"WITHOUT A CATEGORY: {len(none)}")
        if what == "tags":
            everywhere = [i["name"] for i in items
                          if used.get(i["id"], 0) > 0.9 * len(R)]
            if everywhere:
                print("ON OVER 90 % OF RECIPES (filters nothing): "
                      + ", ".join(everywhere))
        if what == "tools":
            everyday = {e.casefold() for e in lint.get("everydayEquipment", [])}
            fails = [i["name"] for i in items
                     if (i["name"] or "").casefold() in everyday]
            print(f"FAILS THE GATING TEST: {len(fails)}" + (
                " – " + ", ".join(fails) if fails else ""))

    elif what == "recipes":
        by: dict = {}
        for r in R:
            by.setdefault(norm(r["name"]), []).append(r)
        name_dupes = [v for v in by.values() if len(v) > 1]
        print(f"{len(R)} recipes, {len(name_dupes)} name duplicates")

        lines = sum(r["ings"] for r in R)
        linked = lines - sum(r["unparsed"] for r in R)
        print(f"LINES WITH A LINKED FOOD: {_share(linked, lines)} of {lines}"
              " – the headline number, target above 95 %")
        amount_in_note = [r["slug"] for r in R if r.get("amountInNote")]
        if amount_in_note:
            print(f"AMOUNT STRANDED IN THE NOTE: {len(amount_in_note)} recipes"
                  " – " + ", ".join(amount_in_note[:10]))
        no_orig = [r["slug"] for r in R if r.get("noOriginalText")]
        if no_orig:
            print(f"LINES WITHOUT originalText: {len(no_orig)} recipes – fill "
                  "it from the display value before repairing them")
        converted = sum(r.get("converted", 0) for r in R)
        print(f"LINES CARRYING Original:: {converted}")

        lint = load_data("lint.json", getattr(a, "lang", None))
        allowed = set(lint["noteTitles"])
        odd = sorted({t for r in R for t in r.get("notes", [])
                      if t not in allowed})
        if odd:
            print("NOTE TITLES OUTSIDE THE VOCABULARY: " + ", ".join(odd[:15]))
        many = [r["slug"] for r in R
                if len(r.get("notes", [])) > lint["maxNotes"]]
        if many:
            print(f"OVER {lint['maxNotes']} NOTES: {len(many)} recipes")
        one_step = [r["slug"] for r in R if r.get("steps") == 1]
        long_steps = [r["slug"] for r in R if (r.get("steps") or 0) > 15]
        print(f"ONE SINGLE STEP: {len(one_step)} · OVER 15 STEPS: "
              f"{len(long_steps)}")
        cooked = sum(1 for r in R if r.get("lastMade"))
        rated = sum(1 for r in R if r.get("rating"))
        print(f"COOKED (lastMade set): {cooked} · RATED: {rated}"
              " – work these first, they are the ones in use")
        broken = idx.get("failed") or []
        if broken:
            print(f"UNREADABLE ({len(broken)}, the instance answers with an "
                  "error – fix them in the UI): " + ", ".join(broken))
        for grp in name_dupes[: a.limit]:
            print("  " + " | ".join(x["slug"] for x in grp))
        # ingredient overlap as a second source of suspicion
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
        print(f"\nSIMILAR INGREDIENTS (Jaccard >= 0.6): {len(sim)}")
        for j, s1, s2 in sim[: a.limit]:
            print(f"  {j}  {s1}  <->  {s2}")
        # stubs: no ingredients and no steps, an import that produced nothing
        stubs = [r["slug"] for r in R
                 if not r["ings"] and not r.get("steps")]
        print(f"\nSTUBS (no ingredients, no steps): {len(stubs)}" + (
            " – " + ", ".join(stubs[: a.limit]) if stubs else ""))

    elif what == "labels":
        labels = mget(EP["labels"])
        foods = mget(EP["foods"])
        lint = load_data("lint.json", getattr(a, "lang", None))
        per: dict = {}
        for f in foods:
            per[f.get("labelId")] = per.get(f.get("labelId"), 0) + 1
        print(f"{len(labels)} labels, {len(foods)} foods")
        print("FOODS WITHOUT A LABEL: "
              + _share(per.get(None, 0), len(foods))
              + " – the most important number here")
        # A label belongs to a group. A food carrying the id of a label
        # this token cannot see is unlabelled in practice, and no amount
        # of relabelling here will move it.
        known = {x["id"] for x in labels}
        dangling = [f["name"] for f in foods
                    if f.get("labelId") and f["labelId"] not in known]
        if dangling:
            print(f"LABEL NOT REACHABLE: {len(dangling)} foods carry a "
                  "labelId that is not in this group's label list – they "
                  "sort nowhere until they are relabelled: "
                  + ", ".join(dangling[:10]))
        default = lint["defaultLabelColor"].casefold()
        plain = [x["name"] for x in labels
                 if not (x.get("color") or "").strip()
                 or (x.get("color") or "").casefold() == default]
        print(f"ON THE DEFAULT COLOUR: {len(plain)}" + (
            " – " + ", ".join(plain[:10]) if plain else ""))
        hues: dict = {}
        for x in labels:
            hues.setdefault((x.get("color") or "").casefold(), []).append(
                x["name"])
        dupe_hue = {k: v for k, v in hues.items() if k and len(v) > 1}
        if dupe_hue:
            print(f"HUE USED TWICE: {len(dupe_hue)}")
            for colour, names in dupe_hue.items():
                print(f"   {colour}: {', '.join(names)}")
        small = [(x["name"], per.get(x["id"], 0)) for x in labels
                 if per.get(x["id"], 0) < 10]
        if small:
            print("UNDER TEN FOODS: " + ", ".join(
                f"{n}({c})" for n, c in sorted(small, key=lambda p: p[1])))
        other = next((x for x in labels
                      if (x["name"] or "").casefold() in ("other",
                                                          "sonstiges")), None)
        if other:
            share = per.get(other["id"], 0)
            note = " – over 5 %, it is being used as a dumping ground" if (
                foods and share > 0.05 * len(foods)) else ""
            print(f'"{other["name"]}": {_share(share, len(foods))}{note}')

    elif what == "extras":
        keys: dict = {}
        for r in R:
            for k in r.get("extras", []):
                keys.setdefault(k, {"recipes": 0})["recipes"] += 1
        for kind in ("foods", "units"):
            for it in mget(EP[kind]):
                for k in (it.get("extras") or {}):
                    keys.setdefault(k, {})[kind] = keys.get(
                        k, {}).get(kind, 0) + 1
        house = read_house() or {}
        registered = {e.get("key") for e in house.get("extrasRegister") or []}
        print(f"{len(keys)} distinct extras keys across recipes, foods and "
              "units")
        if not keys:
            print("nothing to reconcile")
            return
        for key in sorted(keys):
            where = ", ".join(f"{v} {k}" for k, v in sorted(keys[key].items()))
            mark = "" if key in registered else "   !! not in the register"
            print(f"   {key}: {where}{mark}")
        unused = registered - set(keys)
        if unused:
            print("REGISTERED BUT UNUSED: " + ", ".join(sorted(unused)))
        print("\nAnything that fits a real field is moved there, not kept. A "
              "key you might filter by is dead here: cookbook filters cannot "
              "read extras.")

    elif what == "links":
        no_img = [r["slug"] for r in R if not r["image"]]
        no_src = [r["slug"] for r in R if not r["orgURL"]]
        print(f"WITHOUT IMAGE: {len(no_img)}" + (
            " – " + ", ".join(no_img[:15]) if no_img else ""))
        print(f"WITHOUT SOURCE URL: {len(no_src)}")
        if not a.check_urls:
            print("\n(pass --check-urls to check source URLs for reachability)")
            return
        dead: list = []
        for r in R:
            if not r["orgURL"]:
                continue
            try:
                resp = requests.head(r["orgURL"], timeout=10, allow_redirects=True)
                if resp.status_code >= 400:
                    dead.append((r["slug"], resp.status_code, r["orgURL"]))
            except requests.RequestException as e:
                dead.append((r["slug"], type(e).__name__, r["orgURL"]))
        print(f"\nDEAD SOURCE URLS: {len(dead)}")
        for slug, code, url in dead[: a.limit]:
            print(f"  {slug}  [{code}]  {url}")
    else:
        sys.exit(f"unknown: {what}")


# ---------- ctx ----------
def cmd_ctx(a):
    """Print one work package for the model. Writes nothing.

    For "recipe" the food search is targeted: only foods matching the
    ingredients of that recipe are fetched, not the whole table.

    Args:
        a: Parsed arguments with what (recipe, foods, units, categories,
            tags, tools, cookbooks, diet), slug, search, limit and group.

    Raises:
        SystemExit: If "what" is unknown.
        requests.HTTPError: If a Mealie request fails. Failing food
            searches for single terms are skipped.
    """
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
        print("RECIPE:")
        print(json.dumps(slim(recipe, keep_slug=True) if not a.full else recipe,
                         ensure_ascii=False, indent=1))
        print("\nFOODS (pre-search, id|name|plural|label|aliases|desc):")
        print("\n".join(food_line(f) for f in hits.values()) or "(none)")
        print("\nUNITS: " + brief(mget(EP["units"])))
        print("LABELS: " + brief(mget(EP["labels"])))
        print("CATEGORIES: " + brief(mget(EP["categories"])))
        print("TAGS: " + brief(mget(EP["tags"])))
        print("TOOLS: " + brief(mget(EP["tools"])))
        return

    if what in ("foods", "units"):
        items = mget(EP[what])
        fmt = ("id|name|plural|abbreviation" if what == "units"
               else "id|name|plural|label|aliases|description(+/-)")
        print(f"Format: {fmt}\n")
        if a.group:
            key = norm(a.group)
            sel = [f for f in items if norm(f["name"]) == key or any(
                norm(x.get("name", "")) == key for x in f.get("aliases") or [])]
            used = counts(load_index(), what)
            print("DUPLICATE GROUP:")
            for f in sel:
                print(f" {food_line(f, what)}  recipes: {used.get(f['id'], 0)}")
                if (f.get("description") or "").strip():
                    print("   desc: " + f["description"][:160])
        else:
            sel = [f for f in items if gaps(f, what)][: a.limit]
            print(f"WITH GAPS ({len(sel)}):")
            for f in sel:
                print(f" {food_line(f, what)}  missing: {','.join(gaps(f, what))}")
        if what == "foods":
            print("\nLABELS: " + brief(mget(EP["labels"])))
        return

    if what in ORG:
        idx = load_index()
        items = mget(EP[what])
        used = counts(idx, what)
        print(f"{what.upper()} – id|name|recipes")
        for i in sorted(items, key=lambda x: -used.get(x["id"], 0)):
            print(f' {i["id"]}|{i["name"]}|{used.get(i["id"], 0)}')
        if a.group:
            key = norm(a.group)
            ids = [i["id"] for i in items if norm(i["name"]) == key]
            print(f"\nRECIPES in group [{a.group}]:")
            for r in idx["recipes"]:
                hit = [i for i in ids if i in r[what]]
                if hit:
                    print(f' {r["slug"]}  ({",".join(h[:8] for h in hit)})')
        return

    if what == "cookbooks":
        idx = load_index()
        print("EXISTING COOKBOOKS:")
        for c in mget(EP["cookbooks"]):
            print(f' {c["id"]}|{c.get("name")}|{c.get("description", "")[:60]}')
        for kind in ORG:
            u = counts(idx, kind)
            items = mget(EP[kind])
            print(f"\n{kind.upper()} (id|name|recipes):")
            for i in sorted(items, key=lambda x: -u.get(x["id"], 0)):
                print(f' {i["id"]}|{i["name"]}|{u.get(i["id"], 0)}')
        print(f'\nRECIPES IN TOTAL: {len(idx["recipes"])}')
        return

    if what == "diet":
        idx = load_index()
        tags = {t["id"]: t["name"] for t in mget(EP["tags"])}
        sel = [r for r in idx["recipes"] if r["foods"]][: a.limit]
        print("Format: slug | existing tags | ingredients\n")
        for r in sel:
            tn = ",".join(tags.get(t, "?") for t in r["tags"]) or "-"
            print(f' {r["slug"]} | {tn} | {", ".join(r["foodNames"])}')
        print("\nTAGS: " + brief(mget(EP["tags"])))
        return

    sys.exit(f"unknown: {what}")


def cmd_usage(a):
    """Print the slugs of all recipes using one object. Writes nothing.

    Args:
        a: Parsed arguments with kind (food, unit, category, tag, tool)
            and id.
    """
    idx = load_index()
    field = {"food": "foods", "unit": "units", "category": "categories",
             "tag": "tags", "tool": "tools"}[a.kind]
    hits = [r["slug"] for r in idx["recipes"] if a.id in r[field]]
    print(f"{len(hits)} recipes:")
    for h in hits:
        print("  " + h)


# ---------- apply ----------
def resolve(value, refs):
    """Replace "$ref:key" placeholders with ids collected during the run.

    Recurses into dicts and lists so a reference can sit anywhere in a
    payload.

    Args:
        value: Payload fragment of any type.
        refs: Mapping of reference name to the id created earlier.

    Returns:
        The fragment with every reference resolved.

    Raises:
        KeyError: If a reference has no matching id, which happens when the
            creating action comes later in the list or is missing.
    """
    if isinstance(value, str) and value.startswith("$ref:"):
        key = value[5:]
        if key not in refs:
            raise KeyError(f"unknown reference $ref:{key}")
        return refs[key]
    if isinstance(value, dict):
        return {k: resolve(v, refs) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, refs) for v in value]
    return value


_TAKEN: dict = {}


def taken(kind, oid, payload):
    """Find a name or alias in the payload that another object already owns.

    Mealie holds a unique constraint over food and unit names including
    their aliases, and answers a rename into an existing name with a
    constraint error instead of a usable message. The right move there is a
    merge, not a rename, so the check runs before the write.

    Args:
        kind: "foods" or "units".
        oid: Id of the object being updated, excluded from the comparison.
        payload: The update payload, read for "name", "pluralName" and
            "aliases".

    Returns:
        The first colliding string, or None when the payload is free.

    Raises:
        requests.HTTPError: If the list request fails.
    """
    if kind not in _TAKEN:
        _TAKEN[kind] = mget(EP[kind])
    wanted = {(payload.get(k) or "").strip().casefold()
              for k in ("name", "pluralName")}
    wanted |= {(x.get("name") or "").strip().casefold()
               for x in payload.get("aliases") or []}
    wanted.discard("")
    for other in _TAKEN[kind]:
        if other["id"] == oid:
            continue
        names = {(other.get(k) or "").strip().casefold()
                 for k in ("name", "pluralName")}
        names |= {(x.get("name") or "").strip().casefold()
                  for x in other.get("aliases") or []}
        hit = wanted & (names - {""})
        if hit:
            return min(hit)
    return None


# ---------- conversion ----------
FRACTIONS = {"¼": 0.25, "½": 0.5, "¾": 0.75, "⅐": 1 / 7, "⅑": 1 / 9,
             "⅒": 0.1, "⅓": 1 / 3, "⅔": 2 / 3, "⅕": 0.2, "⅖": 0.4,
             "⅗": 0.6, "⅘": 0.8, "⅙": 1 / 6, "⅚": 5 / 6, "⅛": 0.125,
             "⅜": 0.375, "⅝": 0.625, "⅞": 0.875}
RE_TEMP = re.compile(r"^\s*(-?\d+(?:[.,]\d+)?)\s*°?\s*(f|fahrenheit)\b",
                     re.IGNORECASE)


def _house_lang():
    """Derive the data-pack language from the house rules, if there are any.

    The locale is the decision the rule set wants recorded once, so it
    outranks the environment: an instance whose foods are German is
    audited against the German vocabularies even in an English shell.

    Returns:
        A two-letter code, or None when no house rules are configured.
    """
    house = read_house() or {}
    return (house.get("locale") or "")[:2].lower() or None


def data_dir():
    """Locate the data directory that ships beside this script.

    Returns:
        Absolute path to skill/data, which the build copies next to the
        script for every target.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "data"))


def load_data(name, lang=None):
    """Read one data file for a content language, falling back to English.

    Args:
        name: File name below the language directory, e.g.
            "conversions.json".
        lang: Language directory; defaults to $MEALIE_LANG, then "en".

    Returns:
        The decoded file.

    Raises:
        SystemExit: If neither the language file nor the English one is
            readable.
    """
    lang = (lang or _house_lang() or os.environ.get("MEALIE_LANG")
            or "en").lower()[:2]
    for candidate in dict.fromkeys((lang, "en")):
        path = os.path.join(data_dir(), candidate, name)
        if os.path.exists(path):
            if candidate != lang:
                print(f"(no {name} for {lang}, using {candidate})",
                      file=sys.stderr)
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
    sys.exit(f"{name} not found under {data_dir()}")


def parse_amount(text):
    """Split a leading quantity off an ingredient string.

    Understands integers, decimals with a full stop or comma, ASCII
    fractions, unicode fractions and mixed forms ("1 1/2", "1½"). A range
    ("2-3") yields its lower figure, which is what the rules ask for.

    Args:
        text: The raw string, e.g. "1 1/2 cups plain flour".

    Returns:
        A (quantity, rest) tuple; quantity is None when the string does not
        start with one.
    """
    s = text.strip()
    total, matched = 0.0, False
    while s:
        m = re.match(r"^(\d+(?:[.,]\d+)?)\s*/\s*(\d+)", s)
        if m:
            total += float(m.group(1).replace(",", ".")) / float(m.group(2))
            s, matched = s[m.end():].lstrip(), True
            continue
        m = re.match(r"^(\d+(?:[.,]\d+)?)", s)
        if m and not matched:
            total += float(m.group(1).replace(",", "."))
            s, matched = s[m.end():].lstrip(), True
            # a range takes its lower figure; the upper one is dropped here
            s = re.sub(r"^[-–—]\s*\d+(?:[.,]\d+)?\s*", "", s)
            continue
        if s[0] in FRACTIONS:
            total += FRACTIONS[s[0]]
            s, matched = s[1:].lstrip(), True
            continue
        break
    return (total if matched else None), s


def match_unit(text, variants):
    """Find a known unit at the start of a string, longest variant first.

    Args:
        text: String with the quantity already removed.
        variants: Mapping of canonical unit to its spellings.

    Returns:
        A (canonical unit, rest) tuple, or (None, text) when nothing
        matches.
    """
    pairs = sorted(((v, canon) for canon, vs in variants.items()
                    if not canon.startswith("_") for v in vs),
                   key=lambda p: -len(p[0]))
    low = text.lower()
    for spelling, canon in pairs:
        s = spelling.lower()
        if not low.startswith(s):
            continue
        rest = text[len(spelling):]
        # a unit ends at a word boundary: "instant yeast" is not "in"
        if rest[:1].isalnum():
            continue
        return canon, rest.lstrip(" .,")
    return None, text


def round_metric(value, table, limit):
    """Round to the step for the magnitude, finer if the step overshoots.

    Args:
        value: The exact converted figure.
        table: Pairs of (upper bound or None, step).
        limit: Largest relative deviation the rounding may introduce.

    Returns:
        The rounded figure as an int where it is whole.
    """
    step = table[-1][1]
    for bound, candidate in table:
        if bound is None or value < bound:
            step = candidate
            break
    out = round(value / step) * step
    if value and abs(out - value) / value > limit:
        out = round(value)
    return int(out) if float(out).is_integer() else round(out, 1)


def density_key(food, data):
    """Resolve a food string to a key of the density table.

    Args:
        food: The food part of the line, free text.
        data: The conversions data.

    Returns:
        The matching key, or None when the table does not know the food.
    """
    probe = re.split(r"[,;(]", food)[0].strip().strip(".").casefold()
    if not probe:
        return None
    aliases = {k.casefold(): v for k, v in data["densityAliases"].items()}
    table = {k.casefold(): k for k in data["densityPerCup"]}
    if probe in aliases:
        probe = aliases[probe].casefold()
    return table.get(probe)


def convert_line(line, data, fan=False):
    """Convert one non-metric amount, or say why it cannot be converted.

    Follows rules/*/02-units-create §3: the type decides the route, dry
    volumes go through the density table rather than through millilitres,
    and anything the table does not know is left for review instead of
    being estimated.

    Args:
        line: A raw amount, e.g. "1 cup plain flour" or "350 F".
        data: The conversions data for the content language.
        fan: Report the fan oven figure as well.

    Returns:
        A dict with "text" (the line to write) and "note" (the Original:
        note), or with "review" naming what is missing.
    """
    m = RE_TEMP.match(line)
    if m:
        raw = float(m.group(1).replace(",", "."))
        entry = data["oven"].get(str(int(raw)))
        if entry:
            celsius, fan_c = entry["conventional"], entry["fan"]
        else:
            celsius = round((raw - 32) * 5 / 9 / 5) * 5
            fan_c = celsius - 20
        text = f"{celsius} °C" + (f" ({fan_c} °C fan)" if fan else "")
        return {"text": text, "note": f"Original: {line.strip()}"}

    qty, rest = parse_amount(line)
    unit, food = match_unit(rest, data["unitVariants"])
    if unit is None:
        return {"review": "no non-metric unit recognised - nothing to convert"}
    if qty is None:
        return {"review": f"no quantity in front of {unit!r}"}
    note = f"Original: {line.strip()}"

    if unit == "inch":
        cm = data["tinSizes"].get(str(int(qty)))
        cm = cm if cm and not food.strip() else qty * data["direct"]["inch"]["exact"]
        return {"text": f"{round_metric(cm, [[100, 0.5]], 0.05)} cm",
                "note": note}

    if unit in data["direct"]:
        d = data["direct"][unit]
        value = round_metric(qty * d["exact"], data["rounding"],
                             data["roundingLimit"])
        # the practical figure from the rules wins for a single unit
        if qty == 1:
            value = d["practical"]
        return {"text": f'{value} {d["unit"]} {food}'.rstrip(), "note": note}

    key = density_key(food, data)
    spoon = data["spoonGrams"].get(unit, {})
    spoon_key = None
    if key and key in spoon:
        spoon_key = key
    elif food.strip().casefold() in {k.casefold() for k in spoon}:
        spoon_key = next(k for k in spoon
                         if k.casefold() == food.strip().casefold())
    if spoon_key:
        grams = round_metric(qty * spoon[spoon_key], data["rounding"],
                             data["roundingLimit"])
        return {"text": f"{grams} g {food}".rstrip(), "note": note}

    if unit in ("tablespoon", "teaspoon"):
        # 1 tbsp = 15 ml, 1 tsp = 5 ml: metrically defined, so the line
        # stays as it is unless the density table can make it grams.
        return {"keep": f"{unit} is a permitted unit - no conversion needed"}

    liquids = {k.casefold() for k in data.get("liquidFoods", [])}
    if key and key.casefold() in liquids:
        ml = round_metric(qty * data["liquidMl"].get(unit, data["cupMl"]),
                          data["rounding"], data["roundingLimit"])
        return {"text": f"{ml} ml {food}".rstrip(), "note": note}

    if key:
        cups = qty * (data["liquidMl"].get(unit, data["cupMl"])
                      / data["cupMl"])
        grams = round_metric(cups * data["densityPerCup"][key],
                             data["rounding"], data["roundingLimit"])
        return {"text": f"{grams} g {food}".rstrip(), "note": note}
    return {"review": f"{food.strip() or 'this food'} is not in the density "
                      "table - leave the line and review it"}


def cmd_convert(a):
    """Convert non-metric amounts and print what to write into the line.

    Deterministic on purpose: the density table decides, not an estimate,
    and every converted line comes back with the Original: note the rules
    require.

    Args:
        a: Parsed arguments with lines (one or more raw amounts), lang and
            the fan flag.

    Raises:
        SystemExit: If the conversions data is missing.
    """
    data = load_data("conversions.json", a.lang)
    for line in a.lines:
        out = convert_line(line, data, a.fan)
        if "review" in out:
            print(f"REVIEW  {line}  –  {out['review']}")
        elif "keep" in out:
            print(f"KEEP    {line}  –  {out['keep']}")
        else:
            print(f'{out["text"]}   [note: {out["note"]}]')


# ---------- house rules ----------
def read_house():
    """Read the house rules of this working directory.

    Returns:
        The decoded file, or None when there is none.

    Raises:
        SystemExit: If the file exists but is not valid JSON.
    """
    if not os.path.exists(HOUSE_FILE):
        return None
    try:
        with open(HOUSE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as e:
        sys.exit(f"{HOUSE_FILE} is not valid JSON: {e}")


def house_line():
    """Summarize the house rules in one line for a command header.

    Returns:
        The line, or None when no house rules are configured.
    """
    house = read_house()
    if not house:
        return None
    defaults = len(house.get("defaultResolutions") or {})
    parts = [f"locale={house.get('locale', '?')}",
             f"category axis={house.get('categoryAxis', '?')}",
             f"{defaults} default resolutions"]
    return "house rules: " + ", ".join(parts)


def cmd_rules(a):
    """Show the house rules, or write the template to start from.

    These are the decisions the rule set wants recorded once - the locale,
    the category axis, the container assumptions, the table that resolves
    bare ambiguous foods. Kept in a file rather than in a session, because
    a decision nobody wrote down is remade differently next month.

    Args:
        a: Parsed arguments with the init flag, force and lang.

    Raises:
        SystemExit: If the file exists and --force was not given, or if
            there is nothing to show.
        OSError: If the file cannot be written.
    """
    if not a.init:
        house = read_house()
        if not house:
            sys.exit(f"no {HOUSE_FILE} here. Write the template with:\n"
                     f"  python3 {os.path.basename(__file__)} rules --init")
        print(json.dumps(house, ensure_ascii=False, indent=2))
        return
    if os.path.exists(HOUSE_FILE) and not a.force:
        sys.exit(f"{HOUSE_FILE} already exists - overwrite with --force")
    template = load_data("house.json", a.lang)
    _write_text(HOUSE_FILE, json.dumps(template, ensure_ascii=False, indent=2)
                + "\n")
    print(f"written: {HOUSE_FILE}. Go through it once - the locale and the "
          "category axis are decisions, not defaults.")


# ---------- seeding ----------
SEEDABLE = ("labels", "units")


def _unit_keys(unit):
    """Collect every string a unit can be recognised by.

    Args:
        unit: A unit record, from the instance or from the data pack.

    Returns:
        A set of casefolded names, plurals, abbreviations and aliases.
    """
    keys = {(unit.get(k) or "").strip().casefold()
            for k in ("name", "pluralName", "abbreviation",
                      "pluralAbbreviation")}
    keys |= {(al.get("name") or "").strip().casefold()
             for al in unit.get("aliases") or []}
    return keys - {""}


def seed_actions(what, lang=None, existing=None):
    """Build the actions that create the missing part of a data pack.

    The packs are the fixed vocabularies of the rule set - 29 labels with
    their zone colours, the closed set of metric units with aliases and
    standardisation. Seeding them is a plan like any other: it goes through
    apply, which lints it, orders it and logs it.

    Args:
        what: "labels" or "units".
        lang: Content language of the pack.
        existing: What the instance already holds, or None to seed the
            whole pack.

    Returns:
        A (actions, skipped) tuple; skipped names are already present.
    """
    pack = load_data(f"{what}.json", lang)[what]
    actions, skipped = [], []
    if what == "labels":
        have = {(x.get("name") or "").strip().casefold()
                for x in existing or []}
        for label in pack:
            if label["name"].casefold() in have:
                skipped.append(label["name"])
                continue
            actions.append({"op": "create_label",
                            "payload": {"name": label["name"],
                                        "color": label["color"]}})
        return actions, skipped

    have = set()
    for unit in existing or []:
        have |= _unit_keys(unit)
    for unit in pack:
        clash = _unit_keys(unit) & have
        if clash:
            skipped.append(f'{unit["name"]} ({min(clash)} exists)')
            continue
        actions.append({"op": "create_unit",
                        "payload": {k: v for k, v in unit.items()
                                    if not k.startswith("_")}})
    return actions, skipped


def cmd_seed(a):
    """Write the actions for a fixed vocabulary of the rule set.

    Writes nothing to the instance: the output is an ACTIONS file, checked
    with apply --dry-run and executed after approval like any other plan.
    What the instance already holds is skipped, so a second run on a seeded
    instance produces an empty plan.

    Args:
        a: Parsed arguments with what (labels, units or all), lang, out and
            the all flag.

    Raises:
        SystemExit: If "what" is unknown or the pack is missing.
        requests.HTTPError: If the instance cannot be read; --all skips
            that call.
    """
    kinds = SEEDABLE if a.what == "all" else (a.what,)
    for kind in kinds:
        if kind not in SEEDABLE:
            sys.exit(f"seed: unknown pack {kind!r} - one of "
                     f"{', '.join(SEEDABLE)} or all")
    actions, report = [], []
    for kind in kinds:
        existing = None if a.all else mget(EP[kind])
        made, skipped = seed_actions(kind, a.lang, existing)
        actions += made
        report.append(f"{kind}: {len(made)} to create, {len(skipped)} already "
                      "there" + (" – " + ", ".join(skipped[:8]) if skipped
                                 else ""))
    text = json.dumps({"actions": actions}, ensure_ascii=False, indent=2)
    if a.out:
        _write_text(a.out, text + "\n")
        print(f"{len(actions)} actions -> {a.out}")
    else:
        print(text)
    for line in report:
        print(line, file=sys.stderr)
    if not actions:
        print("nothing to seed", file=sys.stderr)


def _write_text(path, text):
    """Write a file, creating the directory when it is missing.

    Args:
        path: Target path.
        text: Content to write.

    Raises:
        OSError: If the file cannot be written.
    """
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


# ---------- plan lint ----------
RE_EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿]")


def _finding(out, level, *parts):
    """Append one lint finding, joining the message fragments as they stand.

    Args:
        out: List the finding is appended to.
        level: "ERROR" or "WARN".
        *parts: Message fragments.
    """
    out.append((level, "".join(parts)))


def _lint_unit(payload, conv, lint, out):
    """Check one create_unit payload against the unit rules.

    Args:
        payload: The action payload.
        conv: Conversions data, for the forbidden units.
        lint: Lint data for the content language.
        out: List the findings are appended to as (level, message).
    """
    def spellings(canons):
        out = {c.casefold() for c in canons}
        for canon in canons:
            out |= {v.casefold()
                    for v in conv["unitVariants"].get(canon, [canon])}
        return out

    names = [payload.get(k) or "" for k in ("name", "pluralName",
                                            "abbreviation")]
    hit = next((n for n in names
                if n.casefold() in spellings(conv["forbidden"])), None)
    if hit:
        _finding(out, "ERROR", f'create_unit "{hit}" is not metric. The rules '
                 "convert these amounts instead of storing the "
                 "unit - see convert.")
    # "stick" is a butter stick to convert and a celery stick to keep. The
    # name cannot tell them apart, the description can - so this warns.
    hit = next((n for n in names
                if n.casefold() in spellings(conv.get("forbiddenAmbiguous", []))),
               None)
    if hit and not hit.casefold() in spellings(conv["forbidden"]):
        _finding(out, "WARN", f'create_unit "{hit}": permitted only as the '
                 "count measure (a stick of celery). The US butter "
                 "stick is converted - say which in the description.")
    abbr = payload.get("abbreviation") or ""
    if (len(abbr) == 1
            and abbr not in lint["singleLetterAbbreviations"]):
        _finding(out, "WARN", f'create_unit "{payload.get("name")}": '
                 f'single-letter abbreviation "{abbr}" is '
                 "ambiguous - T/t have ruined recipes before")
    plural_abbr = payload.get("pluralAbbreviation")
    if (abbr and plural_abbr and plural_abbr != abbr
            and abbr.casefold() in lint["symbolAbbreviations"]):
        _finding(out, "WARN", f'create_unit "{payload.get("name")}": '
                 "metric symbols are not pluralised, so "
                 "pluralAbbreviation should equal abbreviation")


def _lint_food(payload, lint, out):
    """Check one create_food payload against the food rules.

    Args:
        payload: The action payload.
        lint: Lint data for the content language.
        out: List the findings are appended to as (level, message).
    """
    name = payload.get("name") or ""
    if lint["foodNameCase"] == "lower" and name != name.lower():
        _finding(out, "WARN", f'create_food "{name}": names are lowercase')
    if not payload.get("labelId"):
        _finding(out, "WARN", f'create_food "{name}": no label - it lands '
                 "unsorted at the end of every shopping list")
    if not payload.get("aliases"):
        _finding(out, "WARN", f'create_food "{name}": no aliases - the next '
                 "import phrasing it differently will not match")
    limit = lint["foodDescriptionMax"]
    if len(payload.get("description") or "") > limit:
        _finding(out, "WARN", f'create_food "{name}": description over '
                 f"{limit} characters")


def _lint_organizer(op, payload, lint, out):
    """Check one create_tag, create_category or create_tool payload.

    Args:
        op: The operation name.
        payload: The action payload.
        lint: Lint data for the content language.
        out: List the findings are appended to as (level, message).
    """
    name = payload.get("name") or ""
    low = f" {name.casefold()} "
    if RE_EMOJI.search(name) or "#" in name:
        _finding(out, "WARN", f'{op} "{name}": no emoji, no hash')
    if op == "create_tag":
        if lint["tagNameCase"] == "lower" and name != name.lower():
            _finding(out, "WARN", f'create_tag "{name}": tags are lowercase')
        if any(c in low for c in lint["conjunctions"]):
            _finding(out, "WARN", f'create_tag "{name}": two concepts in one '
                     "tag - that is two tags")
        if any(name.casefold().startswith(p)
               for p in lint["negativeTagPrefixes"]):
            _finding(out, "WARN", f'create_tag "{name}": a negative tag reads '
                     "as an allergen guarantee and is not one")
    if op == "create_tool":
        brand = next((b for b in lint["toolBrands"] if b in low), None)
        if brand:
            _finding(out, "WARN", f'create_tool "{name}": brand - use the '
                     "generic term")
        if re.search(r'\d\s*(inch|in\b|")', name, re.IGNORECASE):
            _finding(out, "WARN", f'create_tool "{name}": sizes are metric '
                     "(8 inch -> 20 cm, 9 -> 23, 10 -> 26)")


def _lint_recipe(payload, lint, out):
    """Check one patch_recipe payload against the recipe rules.

    Args:
        payload: The action payload.
        lint: Lint data for the content language.
        out: List the findings are appended to as (level, message).
    """
    slug = payload.get("slug", "<--slug>")
    for field, key, what in (("tags", "maxTags", "tags"),
                             ("recipeCategory", "maxCategories", "categories"),
                             ("tools", "maxTools", "tools")):
        if field in payload and len(payload[field] or []) > lint[key]:
            _finding(out, "WARN", f"patch_recipe {slug}: "
                     f"{len(payload[field])} {what}, the rules "
                     f"cap it at {lint[key]}")
    notes = payload.get("notes")
    if notes is None:
        return
    if len(notes) > lint["maxNotes"]:
        _finding(out, "WARN", f"patch_recipe {slug}: {len(notes)} notes, the "
                 f"rules cap it at {lint['maxNotes']}")
    titles = [(n.get("title") or "") for n in notes if isinstance(n, dict)]
    unknown = [t for t in titles if t not in lint["noteTitles"]]
    if unknown:
        _finding(out, "WARN", f"patch_recipe {slug}: note titles outside the "
                 f"vocabulary: {', '.join(unknown or ['(none)'])} "
                 f"- allowed: {', '.join(lint['noteTitles'])}")


def lint_actions(actions, lang=None):
    """Check a plan against the rules that can be checked mechanically.

    Judgement calls stay with the model; this catches the slips the rule
    set calls out by name. Only a non-metric unit is fatal - that one the
    rules forbid outright, in every language version.

    Args:
        actions: The parsed action list.
        lang: Content language for the vocabularies.

    Returns:
        A list of (level, message) findings, "ERROR" or "WARN".
    """
    conv, lint = load_data("conversions.json", lang), load_data("lint.json", lang)
    out: list = []
    for x in actions:
        op, payload = x["op"], x.get("payload", {})
        if op == "create_unit":
            _lint_unit(payload, conv, lint, out)
        elif op == "create_food":
            _lint_food(payload, lint, out)
        elif op in ("create_tag", "create_category", "create_tool"):
            _lint_organizer(op, payload, lint, out)
        elif op == "patch_recipe":
            _lint_recipe(payload, lint, out)
        elif op == "create_label":
            color = payload.get("color") or ""
            if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                _finding(out, "WARN", f'create_label "{payload.get("name")}": '
                         "color must be a six-digit hex")
            elif color.casefold() == lint["defaultLabelColor"].casefold():
                _finding(out, "WARN", f'create_label "{payload.get("name")}": '
                         "left on Mealie's default colour")
        elif op in ("update_food", "update_unit") and payload.get("name"):
            kind = "foods" if op == "update_food" else "units"
            old = next((o.get("name") for o in _TAKEN.get(kind, [])
                        if o.get("id") == payload.get("id")), None)
            aliases = {(al.get("name") or "").casefold()
                       for al in payload.get("aliases") or []}
            if old and old.casefold() != (payload["name"] or "").casefold() \
                    and old.casefold() not in aliases:
                _finding(out, "WARN", f'{op} {payload.get("id")}: renaming '
                         f'"{old}" -> "{payload["name"]}" without '
                         "keeping the old name as an alias breaks "
                         "every future import using it")
    return out


def log_change(run, op, target, before, payload, result=None):
    """Append one applied action and the state it overwrote to CHANGELOG.

    Written per action rather than per run, so a run that dies halfway
    leaves the actions it did apply on record. "before" holds only the
    fields the action touches - enough to put them back, small enough that
    the file stays readable.

    Args:
        run: Identifier shared by every action of one apply run.
        op: The operation name.
        target: Ids or slug the action addressed.
        before: The overwritten state, or None where nothing was overwritten.
        payload: The payload as sent.
        result: Optional response fragment, e.g. a created id.

    Raises:
        SystemExit: If the changelog cannot be written. Without it a
            destructive run has no way back, so this aborts rather than
            continuing unlogged.
    """
    rec = {"ts": time.time(), "run": run, "op": op, "target": target,
           "before": before, "payload": payload}
    if result is not None:
        rec["result"] = result
    try:
        with open(CHANGELOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError as e:
        sys.exit(f"changelog {CHANGELOG} not writable ({e}). Refusing to "
                 "write to the instance without a record of what changed.")


def _recipe_before(slug, cache):
    """Fetch a recipe once per run and remember it.

    Args:
        slug: Recipe slug.
        cache: Slug to recipe mapping, filled as a side effect.

    Returns:
        The recipe as the instance currently holds it.

    Raises:
        requests.HTTPError: If the recipe cannot be read.
    """
    if slug not in cache:
        cache[slug] = mreq("GET", f'{EP["recipes"]}/{slug}')
    return cache[slug]


def _guard_recipe_lists(actions, default_slug, cache):
    """Refuse a patch_recipe that would shorten a list field.

    Runs before the first write. Legitimate shortenings exist - merging two
    ingredient lines, dropping a note - so the action can carry
    "replace": true and say that the removal is meant.

    Args:
        actions: The parsed action list.
        default_slug: The --slug fallback for actions without their own.
        cache: Slug to recipe mapping, filled as recipes are fetched.

    Raises:
        SystemExit: On the first shortening list field without "replace".
        requests.HTTPError: If a recipe cannot be read.
    """
    for x in actions:
        if x["op"] != "patch_recipe":
            continue
        payload = x.get("payload", {})
        fields = [f for f in RECIPE_LISTS if f in payload]
        slug = payload.get("slug") or default_slug
        if not fields or not slug:
            continue            # a missing slug is reported by the run itself
        cur = _recipe_before(slug, cache)
        for f in fields:
            have, want = len(cur.get(f) or []), len(payload[f] or [])
            if want < have and not x.get("replace"):
                sys.exit(
                    f'patch_recipe {slug}: "{f}" holds {have} entries, the '
                    f"payload has {want}. Mealie replaces the field instead "
                    f"of merging, so {have - want} would be deleted. Pass "
                    'the complete list, or add "replace": true to the '
                    "action if the removal is intended.")


def _guard_deletes(actions, idx):
    """Refuse to delete a food or unit that recipes still reference.

    Deleting a referenced food strips it from those recipes silently -
    unlike a merge, which repoints them. The count comes from the index,
    which is built before the run, so a plan that frees the last reference
    and deletes in the same run is refused too: audit again afterwards.

    Args:
        actions: The parsed action list.
        idx: Index dict, or None when no index exists.

    Raises:
        SystemExit: If a target is still referenced, or if there is no
            index to check against.
    """
    targets = [x for x in actions
               if x["op"] in ("delete_food", "delete_unit")]
    if not targets:
        return
    if not idx:
        sys.exit("delete_food/delete_unit needs the index to check that "
                 "nothing references the object. Run an audit first.")
    for x in targets:
        kind = "foods" if x["op"] == "delete_food" else "units"
        oid = x.get("payload", {}).get("id")
        users = _merge_users(idx, kind, oid)
        if users:
            sys.exit(f'{x["op"]} {oid}: {len(users)} recipe(s) still use it '
                     f"({', '.join(users[:5])}). Deleting strips it from "
                     "them; merge it into the survivor instead, or retag "
                     "those recipes first.")


def _merge_users(idx, kind, oid):
    """List the slugs of the recipes that use one food or unit.

    Args:
        idx: Index dict, or None when no index exists.
        kind: "foods" or "units".
        oid: Id of the object about to be merged away.

    Returns:
        The slugs, or None when there is no index to read.
    """
    if not idx:
        return None
    return [r["slug"] for r in idx["recipes"] if oid in r[kind]]


def _verify_merge(kind, src, dst, slugs, limit=25):
    """Read the affected recipes back and confirm the merge relinked them.

    Mealie answers a merge with a success status, not with a count, so a
    merge that silently drops references looks exactly like one that
    worked. This reads the recipes the index said were affected and checks
    that none of them still points at the source.

    Args:
        kind: "foods" or "units".
        src: Id of the merged-away object.
        dst: Id of the survivor.
        slugs: Slugs that used src before the merge, or None to skip.
        limit: Most recipes to read back; beyond that a sample is checked.

    Raises:
        SystemExit: If a recipe still references the source.
        requests.HTTPError: If a recipe cannot be read.
    """
    if slugs is None:
        print("!! merge not verified: no index. Run an audit first so the "
              "affected recipes are known.")
        return
    key = "food" if kind == "foods" else "unit"
    checked, stale = slugs[:limit], []
    for slug in checked:
        rec = mreq("GET", f'{EP["recipes"]}/{slug}')
        if any((i.get(key) or {}).get("id") == src
               for i in rec.get("recipeIngredient") or []):
            stale.append(slug)
    if stale:
        sys.exit(f"merge {kind} {src} -> {dst}: {len(stale)} recipe(s) still "
                 f"reference the source: {', '.join(stale)}. Stopping before "
                 f"the remaining actions; the overwritten state is in "
                 f"{CHANGELOG}.")
    sample = " (sample)" if len(slugs) > limit else ""
    print(f"VERIFIED {len(checked)}/{len(slugs)} recipes relinked{sample}")


def cmd_apply(a):
    """Execute an ACTIONS file against the instance. The only writing path.

    Checks unknown operations, the order given by ORDER, the names a food
    or unit update wants and the recipe list fields a patch would shorten,
    so a violating plan aborts without touching anything. The same checks
    run under --dry-run, which needs the instance for them: without a
    connection the structural checks still run and the rest is reported as
    skipped. After a writing run the index is deleted.

    Every applied action is written to CHANGELOG with the state it
    overwrote, before the next action runs. That file is the only way back
    from a merge or a delete.

    A rename changes the recipe slug; the new one is read back from the
    response so that a later set_image in the same run still finds the
    recipe.

    Args:
        a: Parsed arguments with file (path to actions.json), slug (the
            default for patch_recipe and set_image, which may each carry
            their own) and dry_run.

    Raises:
        SystemExit: On unknown operations, violated order, a rename into a
            name another food or unit already holds, a patch_recipe that
            would shorten a list field, a merge that left references
            behind, a patch_recipe/set_image without any slug, or a failed
            write. Actions already applied stay applied; there is no
            rollback beyond CHANGELOG.
        KeyError: If a "$ref:" cannot be resolved.
    """
    actions = json.load(open(a.file, encoding="utf-8"))["actions"]
    bad = [x["op"] for x in actions if x["op"] not in ORDER]
    if bad:
        sys.exit(f"Unknown operations: {bad}")
    idxmap = {op: i for i, op in enumerate(ORDER)}
    seq = [idxmap[x["op"]] for x in actions]
    if seq != sorted(seq):
        sys.exit("Order violated – allowed is:\n  " + " -> ".join(ORDER))

    idx = (json.load(open(INDEX, encoding="utf-8"))
           if os.path.exists(INDEX) else None)
    # The guards below read from the instance. A dry run is also the way to
    # check a plan's structure offline, so there they are best effort: what
    # cannot be checked is named rather than passed over in silence.
    cache: dict = {}
    guarded = not a.dry_run or all(read_cfg().get(k) for k in ENV_KEYS)
    if not guarded:
        print("[dry-run] nothing configured: name collisions and recipe list "
              "fields NOT checked")
    try:
        for x in actions if guarded else []:
            if x["op"] not in ("update_food", "update_unit"):
                continue
            kind = "foods" if x["op"] == "update_food" else "units"
            payload = x.get("payload", {})
            clash = taken(kind, payload.get("id"), payload)
            if clash:
                sys.exit(f'{x["op"]} {payload.get("id")}: "{clash}" already '
                         f"exists on another {kind[:-1]}. Merge the two "
                         "instead of renaming one into the other's name.")
        if guarded:
            _guard_recipe_lists(actions, a.slug, cache)
        # after taken(), so a rename can be checked against the stored name
        findings = lint_actions(actions, getattr(a, "lang", None))
        for level, msg in findings:
            print(f"{level:<5} {msg}")
        if any(level == "ERROR" for level, _ in findings):
            sys.exit("plan violates a rule the rule set calls non-negotiable "
                     "- nothing was written")
    except requests.RequestException as e:
        if not a.dry_run:
            raise
        print(f"[dry-run] instance not reachable ({e.__class__.__name__}): "
              "name collisions and recipe list fields NOT checked")

    for x in actions:
        if x["op"] not in ("update_organizer", "delete_organizer"):
            continue
        kind = x.get("payload", {}).get("kind")
        if kind not in ORG_KINDS:
            sys.exit(f'{x["op"]}: unknown kind {kind!r} - one of '
                     f"{', '.join(ORG_KINDS)}")
    _guard_deletes(actions, idx)

    if any(x["op"] in ("merge_food", "merge_unit", "delete_organizer",
                       "delete_food", "delete_unit")
           for x in actions) and not a.dry_run:
        print("!! Contains destructive operations (merge/delete). "
              "Recipes will be rewritten, objects deleted.\n")

    run = f"{int(time.time())}"
    refs: dict = {}
    renamed: dict = {}          # old slug -> new one, after a rename
    done = 0
    try:
        for x in actions:
            op, payload = x["op"], x.get("payload", {})
            if a.dry_run:
                shown = json.dumps(payload, ensure_ascii=False)[:220]
                print(f"[dry-run] {op}: {shown}")
                if x.get("id_as"):
                    refs[x["id_as"]] = "<new-id>"
                continue
            payload = resolve(payload, refs)

            if op in CREATE_EP:
                res = mreq("POST", EP[CREATE_EP[op]], json=payload)
                if x.get("id_as"):
                    refs[x["id_as"]] = res.get("id")
                print(f'CREATED {op[7:]} – {payload.get("name")} – {res.get("id")}')
                log_change(run, op, {"id": res.get("id")}, None, payload,
                           {"id": res.get("id")})
            elif op in ("merge_food", "merge_unit"):
                kind = "foods" if op == "merge_food" else "units"
                # The loser is gone after the merge, so its record is read
                # first: the changelog is the only place it survives.
                src = mreq("GET", f'{EP[kind]}/{payload["from"]}')
                users = _merge_users(idx, kind, payload["from"])
                fkey = "fromFood" if kind == "foods" else "fromUnit"
                tkey = "toFood" if kind == "foods" else "toUnit"
                mreq("PUT", f"{EP[kind]}/merge",
                     json={fkey: payload["from"], tkey: payload["to"]})
                print(f'MERGED {kind} {payload["from"]} -> {payload["to"]}')
                log_change(run, op, {"kind": kind, **payload},
                           {"source": src, "recipes": users}, payload)
                _verify_merge(kind, payload["from"], payload["to"], users)
            elif op in ("update_food", "update_unit"):
                kind = "foods" if op == "update_food" else "units"
                fid = payload.pop("id")
                cur = mreq("GET", f"{EP[kind]}/{fid}")
                mreq("PUT", f"{EP[kind]}/{fid}", json={**cur, **payload})
                print(f'UPDATED {kind} – {cur.get("name")} – ' + ", ".join(payload))
                log_change(run, op, {"kind": kind, "id": fid},
                           {k: cur.get(k) for k in payload}, payload)
            elif op == "update_organizer":
                kind = payload.pop("kind")
                oid = payload.pop("id")
                cur = mreq("GET", f"{EP[kind]}/{oid}")
                mreq("PUT", f"{EP[kind]}/{oid}", json={**cur, **payload})
                print(f'UPDATED {kind} – {cur.get("name")} – ' + ", ".join(payload))
                log_change(run, op, {"kind": kind, "id": oid},
                           {k: cur.get(k) for k in payload}, payload)
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
                print(f'RETAGGED {payload["slug"]} {kind}: '
                      f'+{len(payload.get("add", []))} -{len(rm)}')
                log_change(run, op, {"slug": payload["slug"], "kind": kind},
                           {field: cur}, payload)
            elif op == "delete_organizer":
                kind = payload["kind"]
                gone = mreq("GET", f'{EP[kind]}/{payload["id"]}')
                mreq("DELETE", f'{EP[kind]}/{payload["id"]}')
                print(f'DELETED {kind} {payload["id"]}')
                log_change(run, op, {"kind": kind, "id": payload["id"]},
                           gone, payload)
            elif op in ("delete_food", "delete_unit"):
                kind = "foods" if op == "delete_food" else "units"
                gone = mreq("GET", f'{EP[kind]}/{payload["id"]}')
                mreq("DELETE", f'{EP[kind]}/{payload["id"]}')
                print(f'DELETED {kind[:-1]} – {gone.get("name")} – '
                      f'{payload["id"]}')
                log_change(run, op, {"kind": kind, "id": payload["id"]},
                           gone, payload)
            elif op == "update_cookbook":
                cid = payload.pop("id")
                cur = mreq("GET", f'{EP["cookbooks"]}/{cid}')
                mreq("PUT", f'{EP["cookbooks"]}/{cid}', json={**cur, **payload})
                print(f'UPDATED cookbook – {cur.get("name")}')
                log_change(run, op, {"id": cid},
                           {k: cur.get(k) for k in payload}, payload)
            elif op == "patch_recipe":
                slug = payload.pop("slug", None) or a.slug
                if not slug:
                    sys.exit("patch_recipe needs --slug or a slug in the payload")
                # Read before writing, even for a single scalar field: a PATCH
                # overwrites without saying what was there, and the changelog is
                # what makes it reversible.
                cur = _recipe_before(slug, cache)
                res = mreq("PATCH", f'{EP["recipes"]}/{slug}', json=payload)
                print(f"PATCHED {slug} – " + ", ".join(payload))
                log_change(run, op, {"slug": slug},
                           {k: cur.get(k) for k in payload}, payload)
                # Mealie re-derives the slug from the name. Every later action on
                # this recipe – set_image above all – has to follow it, otherwise
                # it hits a 404 on a recipe that was just written.
                fresh = res.get("slug") if isinstance(res, dict) else res
                if isinstance(fresh, str) and fresh and fresh != slug:
                    print(f"SLUG {slug} -> {fresh} (renamed)")
                    renamed[slug] = fresh
                    if slug == a.slug:
                        a.slug = fresh
            elif op == "set_image":
                slug = payload.get("slug") or a.slug
                slug = renamed.get(slug, slug)
                if not slug:
                    sys.exit("set_image needs --slug or a slug in the payload")
                mreq("POST", f'{EP["recipes"]}/{slug}/image',
                     json={"url": payload["url"], "includeTags": False})
                print(f'IMAGE {slug} – {payload["url"]}')
                # The replaced image itself is not recoverable - Mealie serves it
                # under a fixed path that the new one takes over. The log records
                # that there was one, not what it looked like.
                log_change(run, op, {"slug": slug},
                           {"hadImage": bool((cache.get(slug) or {}).get("image"))},
                           payload)
            done += 1
    except requests.RequestException as e:
        print(f"\n!! ABORTED after {done}/{len(actions)} actions: {e}")
        print(f"applied actions and what they overwrote: {CHANGELOG}")
        rest = [y["op"] for y in actions[done:]]
        print("not applied: " + ", ".join(rest))
        print("No repair attempt is made. Report the state reached and ask.")
        raise SystemExit(1) from e

    if not a.dry_run and os.path.exists(INDEX):
        os.remove(INDEX)
        print("(index discarded – rebuilt on the next audit)")


def probe(url, token):
    """Try one authenticated call against an instance.

    Args:
        url: Base URL of the Mealie instance, without a trailing slash.
        token: API token from Mealie -> Profile -> API Tokens.

    Returns:
        A (ok, message) tuple; the message names the cause on failure.
    """
    try:
        r = requests.get(f"{url}/api/users/self", timeout=15,
                         headers={"Authorization": f"Bearer {token}"})
    except requests.RequestException as e:
        return False, f"no connection to {url} ({e.__class__.__name__})"
    if r.status_code in (401, 403):
        return False, (f"token rejected (HTTP {r.status_code}) – expired, or "
                       "from another instance")
    if r.status_code == 404:
        return False, f"{url} answers but has no Mealie API – wrong URL?"
    if not r.ok:
        return False, f"HTTP {r.status_code} from {url}"
    try:
        who = (r.json() or {}).get("username") or "?"
    except ValueError:
        return False, f"{url} answers, but not with JSON – wrong URL?"
    return True, f"{url} reachable, authenticated as {who}"


def write_env_file(url, token):
    """Write URL and token to ENV_FILE with owner-only permissions.

    Args:
        url: Base URL of the Mealie instance.
        token: API token, stored in clear text.
    """
    fd = os.open(ENV_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(f"MEALIE_URL={url}\nMEALIE_TOKEN={token}\n")
    os.chmod(ENV_FILE, 0o600)


def cmd_setup(a):
    """Check the connection and optionally store the credentials.

    With --check the existing configuration is only probed. Otherwise URL
    and token are asked for, probed, and on request written to ENV_FILE.

    Args:
        a: Parsed arguments with the "check" flag.

    Raises:
        SystemExit: If the probe fails, or nothing is configured under
            --check.
    """
    cfg = read_cfg()
    url, token = cfg.get("MEALIE_URL", "").rstrip("/"), cfg.get("MEALIE_TOKEN", "")
    entered = False

    if not a.check:
        shown = url or "https://mealie.example.org"
        url = (input(f"Mealie URL [{shown}]: ").strip() or url).rstrip("/")
        hint = "keep stored token" if token else "Mealie -> Profile -> API Tokens"
        new_token = getpass.getpass(f"API token ({hint}, not echoed): ").strip()
        entered = bool(new_token) or url != cfg.get("MEALIE_URL", "").rstrip("/")
        token = new_token or token

    if not (url and token):
        sys.exit("nothing configured yet. Run without --check to enter "
                 "URL and token.")

    ok, msg = probe(url, token)
    print(("ok – " if ok else "failed – ") + msg)
    if not ok:
        sys.exit(1)
    if a.check or not entered:
        return

    where = " (overwrites the existing file)" if os.path.exists(ENV_FILE) else ""
    print(f"\nThe token can be stored in {ENV_FILE}{where}. It is written in "
          "clear text; the file gets mode 600 and belongs in .gitignore.")
    if input("Store? [y/N]: ").strip().lower() not in ("y", "yes"):
        print("Not stored. Export by hand:\n"
              f"  export MEALIE_URL={url}\n  export MEALIE_TOKEN=<token>")
        return
    write_env_file(url, token)
    print(f"written: {ENV_FILE} (mode 600)")
    if ENV_FILE not in _read_gitignore():
        print(f"still missing in .gitignore: add a line {ENV_FILE}")


def _read_gitignore():
    """Read .gitignore from the current directory.

    Returns:
        The content, or an empty string if there is none.
    """
    try:
        with open(".gitignore", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def main():
    """Parse the command line and dispatch to the cmd_* function.

    Raises:
        SystemExit: On usage errors and from every command that aborts.
    """
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("setup", help="check the connection, store credentials")
    s.add_argument("--check", action="store_true",
                   help="only probe the existing configuration, ask nothing")
    s.set_defaults(func=cmd_setup)

    i = sub.add_parser("index", help="build the recipe index")
    i.add_argument("--refresh", action="store_true")
    i.set_defaults(func=lambda a: print(
        f'{len(load_index(True)["recipes"])} recipes indexed -> {INDEX}'))

    c = sub.add_parser("ctx", help="fetch a work package")
    c.add_argument("what")
    c.add_argument("slug", nargs="?")
    c.add_argument("--search", nargs="*")
    c.add_argument("--limit", type=int, default=25)
    c.add_argument("--group")
    c.add_argument("--full", action="store_true",
                   help="recipe: unabridged JSON instead of the slim view")
    c.set_defaults(func=cmd_ctx)

    d = sub.add_parser("audit", help="gaps, duplicates, usage")
    d.add_argument("what")
    d.add_argument("--limit", type=int, default=25)
    d.add_argument("--refresh", action="store_true")
    d.add_argument("--check-urls", action="store_true")
    d.add_argument("--lang", help="content language for the vocabularies")
    d.set_defaults(func=cmd_audit)

    u = sub.add_parser("usage", help="recipes using one object")
    u.add_argument("kind", choices=["food", "unit", "category", "tag", "tool"])
    u.add_argument("id")
    u.set_defaults(func=cmd_usage)

    ru = sub.add_parser("rules", help="house rules of this instance")
    ru.add_argument("--init", action="store_true",
                    help=f"write the template to {HOUSE_FILE}")
    ru.add_argument("--force", action="store_true")
    ru.add_argument("--lang", help="content language of the template")
    ru.set_defaults(func=cmd_rules)

    sd = sub.add_parser("seed", help="actions for a fixed vocabulary")
    sd.add_argument("what", help="labels, units or all")
    sd.add_argument("--lang", help="content language of the pack")
    sd.add_argument("--out", help="write the ACTIONS file here")
    sd.add_argument("--all", action="store_true",
                    help="seed the whole pack without asking the instance")
    sd.set_defaults(func=cmd_seed)

    cv = sub.add_parser("convert", help="non-metric amount -> metric + note")
    cv.add_argument("lines", nargs="+",
                    help='e.g. "1 cup plain flour", "8 oz", "350 F"')
    cv.add_argument("--lang", help="content language of the food names")
    cv.add_argument("--fan", action="store_true",
                    help="temperatures: also give the fan oven figure")
    cv.set_defaults(func=cmd_convert)

    ap = sub.add_parser("apply", help="execute ACTIONS")
    ap.add_argument("file")
    ap.add_argument("--slug")
    ap.add_argument("--lang", help="content language for the plan lint")
    ap.add_argument("--dry-run", action="store_true")
    ap.set_defaults(func=cmd_apply)

    a = p.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
