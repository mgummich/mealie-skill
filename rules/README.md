# Mealie Regelwerk / Rule Set

Ein vollständiges Regelwerk für eine gepflegte Mealie-Datenbank, in zwei Sprachfassungen.

A complete rule set for a well-maintained Mealie database, in two language versions.

- `de/` — deutsche Fassung (kanonisch: bundesdeutsches Standarddeutsch)
- `en/` — English version (canonical: en-GB, swappable to en-US)

Die beiden Sprachfassungen sind **eigenständige Regelwerke**, keine Übersetzungen voneinander. Wo die Sprache sich anders verhält, unterscheiden sich die Regeln.

The two language versions are **independent rule sets**, not translations of one another. Where the language behaves differently, the rules differ with it.

---

## Aufbau / Structure

Jede Entität hat zwei Dokumente:

Each entity has two documents:

| Suffix | Zweck | Purpose |
| --- | --- | --- |
| `-anlegen` / `-create` | Neues anlegen und Eingehendes zuordnen | Create new entries and file incoming ones |
| `-ueberarbeiten` / `-cleanup` | Vorhandenen Bestand bereinigen | Clean up what is already there |

Der Unterschied ist grundsätzlich: Beim Anlegen ist der schlimmste Fall eine falsche Zuordnung in einem Datensatz. Beim Überarbeiten ist er stille Beschädigung über den ganzen Bestand. Deshalb lautet die Standardhandlung dort **ohne Beleg nichts ändern**.

The difference is fundamental. When creating, the worst case is one record filed wrongly. When cleaning up, it is silent damage across the whole corpus. So the default action there is **change nothing without evidence**.

## Lesereihenfolge / Reading order

Die Nummerierung ist die Abhängigkeitsreihenfolge. Wer bereinigt, arbeitet sie von oben nach unten ab.

The numbering is the dependency order. A cleanup works through it from top to bottom.

| # | Entität / Entity | Deutsch | English | Hängt an / Depends on | Menge / Size |
| - | --- | --- | --- | --- | --- |
| 01 | Lebensmittel / Foods | [anlegen](de/01-lebensmittel-anlegen-DE.md) · [überarbeiten](de/01-lebensmittel-ueberarbeiten-DE.md) | [create](en/01-foods-create-EN.md) · [cleanup](en/01-foods-cleanup-EN.md) | Zutatenzeile / ingredient line | offen / open |
| 02 | Einheiten / Units | [anlegen](de/02-einheiten-anlegen-DE.md) · [überarbeiten](de/02-einheiten-ueberarbeiten-DE.md) | [create](en/02-units-create-EN.md) · [cleanup](en/02-units-cleanup-EN.md) | Zutatenzeile / ingredient line | geschlossen / closed, 25–40 |
| 03 | Labels | [anlegen](de/03-labels-anlegen-DE.md) · [überarbeiten](de/03-labels-ueberarbeiten-DE.md) | [create](en/03-labels-create-EN.md) · [cleanup](en/03-labels-cleanup-EN.md) | Lebensmittel / foods | geschlossen / closed, 29 |
| 04 | Kategorien / Categories | [anlegen](de/04-kategorien-anlegen-DE.md) · [überarbeiten](de/04-kategorien-ueberarbeiten-DE.md) | [create](en/04-categories-create-EN.md) · [cleanup](en/04-categories-cleanup-EN.md) | Rezept / recipe | geschlossen / closed, 10–20 |
| 05 | Schlagwörter / Tags | [anlegen](de/05-schlagwoerter-anlegen-DE.md) · [überarbeiten](de/05-schlagwoerter-ueberarbeiten-DE.md) | [create](en/05-tags-create-EN.md) · [cleanup](en/05-tags-cleanup-EN.md) | Rezept / recipe | offen, kontrolliert / open, controlled, 40–120 |
| 06 | Utensilien / Tools | [anlegen](de/06-utensilien-anlegen-DE.md) · [überarbeiten](de/06-utensilien-ueberarbeiten-DE.md) | [create](en/06-tools-create-EN.md) · [cleanup](en/06-tools-cleanup-EN.md) | Rezept / recipe | halboffen / semi-open, 15–40 |
| 07 | Rezepte / Recipes | [anlegen](de/07-rezepte-anlegen-DE.md) · [überarbeiten](de/07-rezepte-ueberarbeiten-DE.md) | [create](en/07-recipes-create-EN.md) · [cleanup](en/07-recipes-cleanup-EN.md) | — | offen / open |
| 08 | Kochbücher / Cookbooks | [anlegen](de/08-kochbuecher-anlegen-DE.md) · [überarbeiten](de/08-kochbuecher-ueberarbeiten-DE.md) | [create](en/08-cookbooks-create-EN.md) · [cleanup](en/08-cookbooks-cleanup-EN.md) | gespeicherter Filter / saved filter | 5–20 |
| 09 | Extras | [Extras](de/09-extras-DE.md) | [Extras](en/09-extras-EN.md) | Feld auf / field on 01, 02, 07 | Register / register |

**Die Reihenfolge ist nicht beliebig.** Kochbücher (08) filtern auf 04, 05 und 06 — wer sie zuerst baut, baut auf Vokabular, das anschließend zusammengeführt wird, und der Filter läuft still leer. Rezepte (07) verweisen auf 01 bis 06; deren Bereinigung läuft davor.

**The order is not arbitrary.** Cookbooks (08) filter on 04, 05 and 06 — build them first and you build on vocabulary that gets merged away afterwards, and the filter runs empty without a sound. Recipes (07) point at 01 to 06, so those are cleaned first.

---

## Durchgehende Konventionen / Conventions throughout

**Metrisch.** Die Datenbank enthält ausschließlich metrische Einheiten sowie dimensionslose Zähl- und Behältermaße. Cup, Ounce, Pound, Stick und Pint werden nie angelegt, sondern umgerechnet — in beiden Sprachfassungen.

**Metric.** The database holds metric units only, plus dimensionless count and container measures. Cup, ounce, pound, stick and pint are never created, they are converted — in both language versions.

**`Original:` als Beleg.** Wird eine Menge umgerechnet, steht die Originalangabe als Notiz an der **Zutatenzeile**, mit dem festen englischen Präfix `Original:` in beiden Sprachfassungen, damit eine Erkennungsregel für die ganze Datenbank reicht. Sie dient doppelt: als Nachweis für Menschen und als Marker gegen doppelte Umrechnung.

**`Original:` as evidence.** When an amount is converted, the original goes as a note on the **ingredient line**, with the fixed English prefix `Original:` in both language versions, so that one detection rule covers the whole database. It serves twice over: as evidence a person can check, and as the marker that stops a second conversion of the same line.

**Zuordnen vor Anlegen.** Jede Entität hat eine Matching-Kaskade. Angelegt wird erst, wenn sie vollständig leer ausgeht.

**Match before creating.** Every entity has a matching cascade. Something is created only once the cascade has come back entirely empty.

**Fuzzy-Treffer nie automatisch übernehmen.** `Korinthen` und `Koriander` unterscheiden sich um zwei Zeichen und sind völlig verschiedene Dinge.

**Never accept a fuzzy match automatically.** `Korinthen` and `Koriander` differ by two characters and are entirely different things.

**Überführen statt löschen.** Steht ein Eintrag in der falschen Entität, wird zuerst das Ziel angelegt und verknüpft, dann der Zählerstand verglichen, dann gelöscht. Nie umgekehrt.

**Transfer rather than delete.** When an entry sits in the wrong entity, the target is created and linked first, then the counts are compared, then the source is deleted. Never the other way round.

---

## Mitgelieferte Daten / Bundled data

| Datei / File | Inhalt / Contents |
| --- | --- |
| [`de/02-einheiten-DE.json`](de/02-einheiten-DE.json) | 29 Einheiten, importfertig, mit Aliassen, Abkürzungen und Standardisierung |
| [`en/02-units-EN.json`](en/02-units-EN.json) | 25 units, ready to import, with aliases, abbreviations and standardisation |

Beide sind gegen die Regeln validiert: keine nicht-metrische Einheit, keine Abkürzungs-Kollision, keine Alias-Dublette.

Both are validated against the rules: no non-metric unit, no abbreviation collision, no duplicated alias.

---

## Prüfung gegen das Mealie-Schema / Checked against the Mealie schema

Zuletzt gegen **Mealie 3.22.0** geprüft (OpenAPI-Spezifikation und Schema-Quellen, 2026-08-10). Zwei Annahmen erwiesen sich als falsch und sind korrigiert:

Last checked against **Mealie 3.22.0** (OpenAPI specification and schema sources, 2026-08-10). Two assumptions turned out to be wrong and have been corrected:

- **Einheiten haben Aliasse.** `CreateIngredientUnit` enthält ein `aliases`-Feld. Schreibvarianten gehören deshalb in die Datenbank, nicht in eine Parser-Konfiguration.
- **Units have aliases.** `CreateIngredientUnit` carries an `aliases` field. Spelling variants therefore belong in the database, not in a parser configuration.
- **Es gibt eine eingebaute Standardisierung.** `standardQuantity` und `standardUnit`. Das Feld ist ein freier String; `StandardizedUnitType` listet acht anerkannte Werte, vier metrische (`gram`, `kilogram`, `milliliter`, `liter`) und vier imperiale, und dient der Übereinstimmung mit dem Frontend, nicht der Validierung. Das Regelwerk verwendet ausschließlich die vier metrischen. Im JSON für alle sieben metrischen Einheiten gesetzt; bei Zähl- und Behältermaßen bewusst `null`, weil eine standardisierte `Prise` sonst in Einkaufslisten aufaddiert würde.
- **There is a built-in standardisation.** `standardQuantity` and `standardUnit`. The field is a plain string; `StandardizedUnitType` lists eight recognised values, four metric (`gram`, `kilogram`, `milliliter`, `liter`) and four imperial, and exists for consistency with the frontend rather than for validation. The rule set uses the four metric ones only. Set in the JSON for all seven metric units; deliberately `null` for count and container measures, because a standardised `pinch` would otherwise add up across shopping lists.

Die beiden Felder gehören zusammen: Ohne `standardUnit` oder mit einer `standardQuantity` von 0 oder weniger setzt Mealie beide auf `null` zurück, ohne das zu melden.

The two fields belong together: without a `standardUnit`, or with a `standardQuantity` of zero or less, Mealie resets both to `null` and does not say so.

Bestätigt hat sich: **Utensilien haben keine Aliasse** (`RecipeToolCreate` kennt nur `name` und `households_with_tool`). Deshalb ist die Namensdisziplin dort strenger als überall sonst.

Confirmed: **tools have no aliases** (`RecipeToolCreate` knows only `name` and `households_with_tool`). That is why naming discipline is stricter there than anywhere else.

Ebenfalls seit Mealie 2.0 und für 08 maßgeblich: Kochbücher hängen am Haushalt, nicht an der Gruppe, und ihr Filter ist ein einziger `queryFilterString`.

Also since Mealie 2.0, and decisive for 08: cookbooks hang off the household rather than the group, and their filter is a single `queryFilterString`.

---

## Nicht abgedeckt / Out of scope

Bewusst außerhalb des Zuschnitts, falls später gebraucht:

Deliberately outside the cut, in case they are wanted later:

- Einkaufslisten und deren Positionen / shopping lists and their items
- Essensplan-Einträge (ein Eintrag kann statt einer Rezept-ID auch nur `title` und `text` tragen — freie Einträge wie „Reste" oder „auswärts") / meal plan entries, which may carry only `title` and `text` instead of a recipe id — free entries such as "leftovers" or "eating out"
- `assets` und `comments` am Rezept / on the recipe
- Haushalte, Gruppen, Benutzer / households, groups, users
- Die haushaltsbezogenen Vorratsflags / the household stock flags `householdsWithIngredientFood` und/and `householdsWithTool`
