# ACTIONS-Format

Plan und Ausführung sind getrennt: Du schreibst `actions.json`, prüfst mit
`--dry-run`, holst die Freigabe, dann führt das Skript aus.

**Inhalte in `actions.json` sind Datenbankinhalt, kein Chat.** Auch wenn der
Ausgabestil komprimiert ist (siehe caveman in SKILL.md): `description`,
Zubereitungsschritte, Notizen und Kochbuchbeschreibungen werden hier in
vollständiger deutscher Prosa geschrieben. Sie stehen dauerhaft in der
Instanz und werden von Menschen gelesen, die diesen Ablauf nicht kennen.

```json
{"actions": [
  {"op": "create_label", "id_as": "lbl_gewuerze",
   "payload": {"name": "Gewürze & Kräuter", "color": "#8B5E3C"}},
  {"op": "create_food", "id_as": "food_kreuzkuemmel",
   "payload": {"name": "Kreuzkümmel", "labelId": "$ref:lbl_gewuerze"}}
]}
```

`"$ref:<id_as>"` wird zur Laufzeit durch die ID des im selben Lauf angelegten
Objekts ersetzt. Bestehende Objekte immer über ihre echte ID referenzieren.

## Reihenfolge

Zwingend, Verstöße brechen vor dem ersten Schreibzugriff ab:

    create_label -> merge_food -> merge_unit -> create_food -> create_unit
    -> create_category -> create_tag -> create_tool -> update_food
    -> update_unit -> update_organizer -> retag_recipe -> delete_organizer
    -> create_cookbook -> update_cookbook -> patch_recipe -> set_image

Der Grund: erst umhängen, dann löschen; erst anlegen, dann referenzieren.

## Operationen

| op | payload |
|---|---|
| `create_label` | `name`, `color` (Hex) |
| `create_food` | `name`, `pluralName`, `description`, `labelId`, `aliases` |
| `create_unit` | `name`, `pluralName`, `abbreviation` |
| `create_category` / `create_tag` / `create_tool` | `name` |
| `merge_food` / `merge_unit` | `from`, `to` (IDs) |
| `update_food` / `update_unit` | `id` + nur die zu setzenden Felder |
| `update_organizer` | `kind` (`categories`/`tags`/`tools`), `id`, Felder |
| `retag_recipe` | `slug`, `kind`, `add` (IDs), `remove` (IDs) |
| `delete_organizer` | `kind`, `id` |
| `create_cookbook` | `name`, `description`, `categories`/`tags`/`tools`, `requireAll*` |
| `update_cookbook` | `id` + zu ändernde Felder |
| `patch_recipe` | nur geänderte Rezeptfelder (braucht `--slug`) |
| `set_image` | `url` (braucht `--slug`) |

## Teilaktualisierung

`update_food`, `update_unit`, `update_organizer` und `update_cookbook` lesen
den bestehenden Datensatz und legen die angegebenen Felder darüber - führe
nur auf, was sich ändern soll.

Ausnahme: Listenfelder werden **ersetzt**, nicht ergänzt. Bei `aliases`
also immer die bestehenden Einträge mit aufführen.

## Aufruf

    python scripts/mealie_ctx.py apply actions.json --dry-run
    python scripts/mealie_ctx.py apply actions.json              # ohne Rezeptbezug
    python scripts/mealie_ctx.py apply actions.json --slug <slug>  # mit
