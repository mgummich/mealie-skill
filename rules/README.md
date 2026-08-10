# Mealie Regelwerk / Rule Set

Ein vollständiges Regelwerk für eine gepflegte Mealie-Datenbank, in zwei Sprachfassungen.
A complete rule set for a well-maintained Mealie database, in two language versions.

- `de/` — deutsche Fassung (kanonisch: bundesdeutsches Standarddeutsch)
- `en/` — English version (canonical: en-GB, swappable to en-US)
- `archiv/` — überholte Vorfassungen, nur zur Nachvollziehbarkeit

Die beiden Sprachfassungen sind **eigenständige Regelwerke**, keine Übersetzungen voneinander. Wo die Sprache sich anders verhält, unterscheiden sich die Regeln.

---

## Aufbau

Jede Entität hat zwei Dokumente:

| Suffix | Zweck |
| --- | --- |
| `-anlegen` / `-create` | Neues anlegen und Eingehendes zuordnen |
| `-ueberarbeiten` / `-cleanup` | Vorhandenen Bestand bereinigen |

Der Unterschied ist grundsätzlich: Beim Anlegen ist der schlimmste Fall eine falsche Zuordnung in einem Datensatz. Beim Überarbeiten ist er stille Beschädigung über den ganzen Bestand. Deshalb lautet die Standardhandlung dort **ohne Beleg nichts ändern**.

## Lesereihenfolge

Die Nummerierung ist die Abhängigkeitsreihenfolge. Wer bereinigt, arbeitet sie von oben nach unten ab.

| # | Entität | Hängt an | Menge |
| - | --- | --- | --- |
| 01 | Lebensmittel / Foods | Zutatenzeile | offen |
| 02 | Einheiten / Units | Zutatenzeile | geschlossen, 25–40 |
| 03 | Labels | Lebensmittel | geschlossen, 29 |
| 04 | Kategorien / Categories | Rezept | geschlossen, 10–20 |
| 05 | Schlagwörter / Tags | Rezept | offen, kontrolliert, 40–120 |
| 06 | Utensilien / Tools | Rezept | halboffen, 15–40 |
| 07 | Rezepte / Recipes | — | offen |
| 08 | Kochbücher / Cookbooks | gespeicherter Filter | 5–20 |
| 09 | Extras | Feld auf 01, 02, 07 | Register |

**Die Reihenfolge ist nicht beliebig.** Kochbücher (08) filtern auf 04, 05 und 06 — wer sie zuerst baut, baut auf Vokabular, das anschließend zusammengeführt wird, und der Filter läuft still leer. Rezepte (07) verweisen auf 01 bis 06; deren Bereinigung läuft davor.

---

## Durchgehende Konventionen

**Metrisch.** Die Datenbank enthält ausschließlich metrische Einheiten sowie dimensionslose Zähl- und Behältermaße. Cup, Ounce, Pound, Stick und Pint werden nie angelegt, sondern umgerechnet — in beiden Sprachfassungen.

**`Original:` als Beleg.** Wird eine Menge umgerechnet, steht die Originalangabe als Notiz an der **Zutatenzeile**, mit dem festen englischen Präfix `Original:` in beiden Sprachfassungen, damit eine Erkennungsregel für die ganze Datenbank reicht. Sie dient doppelt: als Nachweis für Menschen und als Marker gegen doppelte Umrechnung.

**Zuordnen vor Anlegen.** Jede Entität hat eine Matching-Kaskade. Angelegt wird erst, wenn sie vollständig leer ausgeht.

**Fuzzy-Treffer nie automatisch übernehmen.** `Korinthen` und `Koriander` unterscheiden sich um zwei Zeichen und sind völlig verschiedene Dinge.

**Überführen statt löschen.** Steht ein Eintrag in der falschen Entität, wird zuerst das Ziel angelegt und verknüpft, dann der Zählerstand verglichen, dann gelöscht. Nie umgekehrt.

---

## Mitgelieferte Daten

| Datei | Inhalt |
| --- | --- |
| `de/02-einheiten-DE.json` | 29 Einheiten, importfertig, mit Aliassen, Abkürzungen und Standardisierung |
| `en/02-units-EN.json` | 25 units, same structure |

Beide sind gegen die Regeln validiert: keine nicht-metrische Einheit, keine Abkürzungs-Kollision, keine Alias-Dublette.

---

## Prüfung gegen das Mealie-Schema

Die Regeln wurden gegen `mealie-next` geprüft. Zwei Annahmen erwiesen sich als falsch und sind korrigiert:

- **Einheiten haben Aliasse.** `CreateIngredientUnit` enthält ein `aliases`-Feld. Schreibvarianten gehören deshalb in die Datenbank, nicht in eine Parser-Konfiguration.
- **Es gibt eine eingebaute Standardisierung.** `standardQuantity` und `standardUnit` mit dem Enum `gram, kilogram, milliliter, liter`. Im JSON für alle sieben metrischen Einheiten gesetzt; bei Zähl- und Behältermaßen bewusst `null`, weil eine standardisierte `Prise` sonst in Einkaufslisten aufaddiert würde.

Bestätigt hat sich: **Utensilien haben keine Aliasse** (`RecipeToolCreate` kennt nur `name` und `households_with_tool`). Deshalb ist die Namensdisziplin dort strenger als überall sonst.

---

## Nicht abgedeckt

Bewusst außerhalb des Zuschnitts, falls später gebraucht:

- Einkaufslisten und deren Positionen
- Essensplan-Einträge (ein Eintrag kann statt einer Rezept-ID auch nur `title` und `text` tragen — freie Einträge wie „Reste" oder „auswärts")
- `assets` und `comments` am Rezept
- Haushalte, Gruppen, Benutzer
- Die haushaltsbezogenen Vorratsflags `householdsWithIngredientFood` und `householdsWithTool`

---

## Archiv

`archiv/` enthält drei überholte Dateien: die wörtliche englische Übersetzung der ursprünglichen niederländischen Vorlage sowie die beiden kombinierten Metadaten-Dokumente, die inzwischen in Einzeldokumente je Entität aufgeteilt sind. Sie sind **nicht** zu verwenden und liegen nur bei, um Entscheidungen nachvollziehen zu können.
