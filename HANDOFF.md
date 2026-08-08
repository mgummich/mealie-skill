# Handoff

Stand: 9. August 2026. Übergabe an Claude Code zur Inbetriebnahme.

## Was das ist

Werkzeug zum Aufräumen einer Mealie-Instanz. Sechs Modi: `recipe`, `foods`,
`units`, `organizers`, `cookbooks`, `maintenance`. Aufbau und Regeln stehen
in `CLAUDE.md`, Bedienung im `README.md`.

## Wichtigste Einschränkung

**Gegen eine echte Mealie-Instanz lief noch kein einziger Aufruf.** Die
Entwicklung fand ohne Zugang statt. Alles unten unter „ungeprüft" ist aus der
Dokumentation abgeleitet, nicht verifiziert. Die erste Aufgabe ist deshalb
Verifikation, nicht Erweiterung.

Genauso wenig getestet: der Anthropic-API-Pfad in `optimize.py` und die
Caching-Kennzahlen.

## Verifiziert

Gegen synthetische Daten getestet und bestanden:

- Syntax beider Skripte, `--help` beider Skripte
- `apply --dry-run`: Reihenfolge-Guard bricht bei Verstoß vor dem ersten
  Schreibzugriff ab; unbekannte Operationen werden abgewiesen
- `$ref:<id_as>`-Auflösung rekursiv über Dicts und Listen
- `patch_recipe`/`set_image` ohne `--slug` bricht sauber ab
- `norm()`-Normalform: Tomate/Tomaten, Zwiebel/Zwiebeln, Kürbis/Kuerbis,
  Möhre/Möhren treffen; Butter/Buttermilch und Tomate/Cherrytomate nicht
- `audit recipes`: Namensdubletten und Jaccard-Ähnlichkeit (Testpaar 0.67)
- `audit links`, `usage tag <id>` gegen künstlichen Index
- `gaps()` trennt Foods und Units korrekt (Units ohne Label/Beschreibung)
- Cache-Blöcke aller Modi liegen bei 1.900–2.400 Tokens, über der
  1024-Token-Mindestgröße

## Ungeprüft — hier anfangen

### 1. Endpunktpfade

Unterscheiden sich zwischen Mealie-Versionen. Prüfschleife im README,
Abschnitt „Vorbereitung". Was 404 liefert, im `EP`-Dictionary von
`mealie_ctx.py` anpassen. Kandidaten: `/api/organizers/categories` vs.
`/api/categories`, `/api/groups/labels`, `/api/groups/cookbooks`.

### 2. Merge-Endpunkte

`merge_food` und `merge_unit` nutzen `PUT /api/foods/merge` mit
`{"fromFood", "toFood"}` bzw. `{"fromUnit", "toUnit"}`. Je nach Version ist
es `POST` und/oder anders benannt. **An genau einem Testpaar prüfen**, bevor
eine Gruppe läuft — der Vorgang ist nicht umkehrbar.

### 3. Kochbuch-Schema

`create_cookbook` reicht das Payload durch. Neuere Mealie-Versionen nutzen
statt `categories`/`tags`/`tools` plus `requireAll*` einen
`queryFilterString`. Einmal ein bestehendes Kochbuch per GET abrufen und das
Schema in `references/cookbooks.md` festschreiben.

### 4. Teilaktualisierung

`update_food`, `update_unit`, `update_organizer`, `update_cookbook` machen
GET, mergen im Speicher, dann PUT. Falls die Instanz PATCH auf diesen
Ressourcen unterstützt, ist das die sauberere Variante — ein Zweig in
`cmd_apply`.

### 5. `retag_recipe`

Liest das Rezept, filtert `remove`, hängt `add` an, PATCHt das Feld. Ob
Mealie beim PATCH vollständige Objekte oder nur IDs erwartet, ist ungeprüft.
An einem unwichtigen Rezept testen.

### 6. Bild setzen

`POST /api/recipes/{slug}/image` mit `{"url", "includeTags"}` — Feldname und
Methode verifizieren.

## Bekannte Schwächen

**Batch-Slug-Erkennung** in `optimize.py`, `mode_recipe`: parst die Textausgabe
von `audit recipes` heuristisch auf Slugs. Fragil. Besser: `--json`-Flag in
`mealie_ctx.py` ergänzen und strukturiert lesen. Das ist die lohnendste
Aufräumarbeit.

**Kein Retry, kein Rate-Limiting.** Bei großen Beständen baut `build_index`
einen Request pro Rezept ohne Pause. Bei fremd gehosteten Instanzen ggf.
drosseln.

**`audit links --check-urls`** schickt HEAD-Requests an fremde Server, seriell
und ohne Timeout-Budget insgesamt. Einmalig laufen lassen, nicht in einen
Cron.

**Keine Tests.** Es gibt keine Testdatei; verifiziert wurde per Hand. Ein
`tests/` mit pytest gegen einen gemockten `mreq` wäre sinnvoll, sobald die
Endpunkte stehen.

**Index-Invalidierung ist grob:** nach jedem `apply` wird der ganze Index
gelöscht, auch wenn nur ein Tag umbenannt wurde. Bei großen Beständen teuer.

## Erste Sitzung — Vorschlag

1. `MEALIE_URL`, `MEALIE_TOKEN` setzen. **Backup ziehen**: Mealie →
   Site Settings → Backups. Ohne das nicht weitermachen.
2. Prüfschleife aus dem README laufen lassen, `EP` anpassen.
3. `python3 .../mealie_ctx.py index --refresh` — läuft der Durchlauf durch?
   Wie lange dauert er?
4. `audit foods`, `audit tags`, `audit recipes` — plausibel?
5. Ein Rezept lesend: `ctx recipe <slug>`.
6. Erster Schreibversuch: eine einzelne `update_food`-Aktion auf ein
   unwichtiges Food, erst `--dry-run`, dann echt. Ergebnis in der Oberfläche
   kontrollieren.
7. Erst danach Merges, und auch dann mit einem einzigen Paar.

## Prompts neu ableiten

`standalone/prompts/*.txt` stammen aus `antigravity/skills/mealie/references/`.
Nach Regeländerungen neu erzeugen: Referenz kopieren, Skriptaufrufzeilen
entfernen (die gelten nur in Antigravity), `common.txt` bleibt handgepflegt.
Danach prüfen, dass jeder kombinierte Block über 1024 Tokens liegt, sonst
greift das Prompt-Caching nicht.

## Offene Fragen an den Nutzer

- Mealie-Version? Bestimmt die Hälfte der offenen Punkte oben.
- Größenordnung: wie viele Rezepte, Foods, Tags? Bestimmt, ob der Index
  so tragfähig ist.
- Soll `caveman` installiert werden? Der Skill nutzt ihn, wenn vorhanden,
  funktioniert aber ohne.
