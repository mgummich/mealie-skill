# Rezepte: Anlegen & Importieren (DE)

> Das integrierende Regelwerk. Alle anderen laufen hier zusammen: *Parse §x* zeigt auf **Food Rules (DE): Parsen & Anlegen**, *Einheiten §x* / *Kategorien §x* / *Schlagwörter §x* / *Utensilien §x* auf die jeweiligen Anlegen-Dokumente.

## Grundsatz

Ein Rezept ist kein Textdokument, sondern eine **strukturierte Zusammenstellung**: Zutatenzeilen mit verknüpften Lebensmitteln und Einheiten, nummerierte Schritte, Metadaten. Nur die Struktur macht Einkaufsliste, Skalierung und Suche möglich. Ein Rezept, dessen Zutaten als roher Text dastehen, ist ein Bild mit Buchstaben.

> **Oberste Regel:** Erst prüfen, ob das Rezept schon existiert. Dubletten sind bei Rezepten teurer als bei jeder anderen Entität, weil Bewertungen, Notizen und `lastMade` sich auf beide verteilen und keins mehr die Wahrheit trägt.

---

## 1. Vor dem Anlegen

### 1.1 Dublettenprüfung
Nach dem Gerichtnamen und nach zwei bis drei charakteristischen Zutaten suchen. Treffer bedeutet nicht automatisch Dublette:

| Fall | Aktion |
| --- | --- |
| Gleiches Gericht, gleiche Quelle | **nicht anlegen** — vorhandenes Rezept öffnen |
| Gleiches Gericht, andere Quelle, deutlich andere Zubereitung | anlegen, im `description` die Abgrenzung nennen |
| Gleiches Gericht, kleine Abwandlung (andere Kräuter, mehr Schärfe) | **nicht anlegen** — als Notiz (§8) ins vorhandene Rezept |
| Gleiches Grundrezept, anderes Endgericht | anlegen, Grundrezept als Unterrezept verknüpfen (§5.6) |

Die dritte Zeile ist die häufigste. Eine Variante ist eine Notiz, kein Rezept.

### 1.2 Quelle
Bei Import aus dem Netz: `orgURL` **immer** setzen. Sie ist die einzige Möglichkeit, später Umrechnungen, Mengen oder unklare Schritte am Original zu prüfen.

Bei Rezepten aus Büchern oder von Personen: Quelle in eine Notiz mit dem Titel `Quelle` (§8). Fremde Rezepttexte gehören in die eigene Sammlung, nicht in eine öffentliche Freigabe — `settings.public` bleibt bei fremden Texten auf `false`.

---

## 2. Pflichtfelder

Ohne diese wird nicht gespeichert:

- `name`
- mindestens eine Zutatenzeile mit verknüpftem `food`
- mindestens ein Schritt in `recipeInstructions`
- `recipeServings`
- genau eine `category` (Kategorien §2)

Alles Übrige ist optional — aber ein Rezept ohne Zeitangaben taucht in keiner Aufwandssuche auf.

---

## 3. Name und Beschreibung

### 3.1 `name`
- Der **Gerichtname**, wie man ihn im Alltag sagt: `Linsensuppe mit Speck`
- Keine Wertung, kein Superlativ: nicht `Omas allerbeste Linsensuppe`
- Keine Emoji, keine Quellenangabe im Titel, keine Nummerierung
- Kein Mengen- oder Zeithinweis im Titel: `Linsensuppe`, nicht `Linsensuppe in 30 Minuten` — dafür gibt es `prepTime` und Schlagwörter
- Unterscheidungen gehören in den Titel, wenn zwei Rezepte desselben Gerichts koexistieren: `Linsensuppe (schwäbisch)` und `Linsensuppe (türkisch)`

`slug` wird automatisch erzeugt und nicht von Hand gesetzt.

### 3.2 `description`
Ein bis zwei Sätze: **was es ist** und **wann man es kocht**. Keine Kochbuch-Prosa, keine Anleitung, keine Zutatenliste.

> Deftiger Eintopf mit Tellerlinsen und Speck; braucht wenig Aufsicht und schmeckt aufgewärmt besser.

---

## 4. Mengen und Zeiten

### 4.1 Portionen und Ausbeute
Mealie trennt drei Felder:

| Feld | Bedeutung | Beispiel |
| --- | --- | --- |
| `recipeServings` | Anzahl Portionen — Basis für die Skalierung | `4` |
| `recipeYieldQuantity` | Menge des Endprodukts | `12` |
| `recipeYield` | Einheit der Ausbeute als Text | `Muffins`, `Gläser à 250 ml` |

Bei Hauptgerichten reicht `recipeServings`. Bei Gebäck, Eingemachtem und Grundrezepten zusätzlich die Ausbeute füllen — sonst weiß niemand, ob „1 Portion" ein Muffin oder das ganze Blech ist.

**Portionen immer auf eine gerade, alltagstaugliche Zahl** normieren: 2 oder 4. Rezepte mit `recipeServings: 6` aus der Quelle dürfen bleiben, aber Mengen nicht auf krumme Werte umrechnen — Mealie skaliert selbst.

### 4.2 Zeiten
Freitextfelder, deshalb **einheitliches Format** festlegen und durchhalten: `25 Min.`, `1 Std. 30 Min.`

- `prepTime` — aktive Vorbereitung
- `cookTime` — Garzeit am Herd oder im Ofen
- `performTime` — aktive Arbeitszeit während des Garens
- `totalTime` — nur setzen, wenn es **nicht** die Summe ist, also bei Wartezeiten: Teig gehen lassen, marinieren, kühlen

Keine Spannen (`20–25 Min.`) — die kürzere Zahl nehmen und die Spanne in einen Schritt schreiben. Keine Wartezeit in `prepTime` verstecken; das verfälscht jede Aufwandssuche.

---

## 5. Zutaten — der Kern

### 5.1 Struktur einer Zeile
Jede Zeile zerfällt in vier Felder, und jedes gehört an seinen Platz:

| Feld | Inhalt | Beispiel |
| --- | --- | --- |
| `quantity` | die Zahl | `2` |
| `unit` | die Einheit (Einheiten §1) | `EL` |
| `food` | das Lebensmittel (Parse-Regeln) | `Olivenöl` |
| `note` | Zubereitung, Zustand, Alternativen, Originalangaben | `plus etwas zum Anbraten` |

`originalText` trägt die Rohzeile aus dem Import und wird **nicht überschrieben** — sie ist der Beleg, an dem sich jeder Parse-Fehler nachweisen lässt.

`display` wird berechnet und nicht von Hand gesetzt.

### 5.2 Ein Lebensmittel pro Zeile
`Salz und Pfeffer` sind zwei Zeilen. `2 Möhren und 1 Stange Sellerie` sind zwei Zeilen. Nur getrennte Zeilen landen korrekt auf der Einkaufsliste.

### 5.3 Was in die Notiz gehört
- Zubereitung: `fein gehackt`, `in Scheiben`, `zimmerwarm`
- Zustand und Auswahl: `möglichst reif`, `Bio, unbehandelte Schale`
- Alternativen: `oder Crème fraîche`
- Teilmengen: `davon 1 EL zum Bestreuen`
- **Originalangaben nach Umrechnung**: `Original: 1 cup` (Einheiten §3.6)

Mehrere Angaben mit `; ` trennen: `fein gehackt; Original: 1 cup`

### 5.4 Was **nicht** in die Notiz gehört
- Mengen, die ins `quantity`-Feld gehören
- Einheiten, die ins `unit`-Feld gehören
- Arbeitsschritte, die in `recipeInstructions` gehören (`10 Minuten anbraten`)
- Das Lebensmittel selbst

### 5.5 Mengenlose Zutaten
`Salz nach Geschmack` bekommt `quantity: 0`, keine Einheit, `food: Salz`, `note: nach Geschmack`. Nie eine erfundene Menge eintragen — sie landet sonst auf der Einkaufsliste.

Ebenso: `2 Eier` hat **keine** Einheit (Einheiten §1.4).

### 5.6 Unterrezepte statt Sammel-Lebensmittel
Mealie verknüpft Rezepte über `referencedRecipe` direkt in der Zutatenzeile. Das ist der richtige Ort für alles, was die Parse-Regeln als Lebensmittel ausschließen:

- `Kartoffelpüree`, `selbstgemachtes Pesto`, `Pizzateig`, `Hühnerbrühe (selbst gekocht)`

Existiert das Unterrezept noch nicht, entweder anlegen oder die Komponenten direkt in die Zutatenliste aufnehmen — aber **kein Lebensmittel namens „Kartoffelpüree" erzeugen** (Parse §7.1).

### 5.7 Abschnitte
Bei mehrteiligen Rezepten `title` auf der **ersten Zeile** eines Abschnitts setzen: `Für den Teig`, `Für die Füllung`, `Zum Servieren`. Die übrigen Zeilen des Abschnitts lassen `title` leer.

Abschnitte erst ab etwa acht Zutaten oder bei echten Teilzubereitungen. Vier Zutaten unter drei Überschriften sind Lärm.

### 5.8 Reihenfolge
Zutaten in der **Verwendungsreihenfolge** listen, nicht nach Warengruppe. Wer beim Kochen von oben nach unten liest, soll nicht springen müssen.

---

## 6. Zubereitungsschritte

### 6.1 Ein Schritt = ein zusammenhängender Handlungsblock
Nicht ein Satz, nicht eine ganze Seite. Faustregel: was man am Stück tut, bevor man das nächste Mal etwas anderes anfasst.

- Zu fein: `Zwiebel schälen.` / `Zwiebel würfeln.` / `Öl erhitzen.`
- Zu grob: ein Absatz mit dem gesamten Rezept
- Richtig: `Zwiebel schälen und fein würfeln. Öl in einem großen Topf erhitzen und die Zwiebel darin bei mittlerer Hitze 5 Minuten glasig dünsten.`

### 6.2 Sprache
- Imperativ, zweite Person Plural vermieden: `Zwiebel würfeln`, nicht `Würfeln Sie die Zwiebel`
- Gegenwart, keine Erzählung
- Garzeiten und erkennbare Zustände nennen: `5 Minuten, bis die Zwiebel glasig ist`
- Temperaturen metrisch mit Originalangabe in Klammern: `175 °C (Original: 350 °F)`

### 6.3 Mengen im Schritttext
Mengen im Text **wiederholen**, wenn eine Zutat mehrfach oder geteilt verwendet wird — sonst nicht. `Die Hälfte des Käses unterrühren` ist nötig; `2 EL Olivenöl in der Pfanne erhitzen` ist redundant, wenn es nur einmal vorkommt.

Wird eine Menge wiederholt, muss sie mit der Zutatenzeile **übereinstimmen**. Bei Skalierung driften Texte auseinander — deshalb sparsam.

### 6.4 `ingredientReferences`
Zutaten mit dem Schritt verknüpfen, in dem sie verwendet werden. Das ist der beste Schutz gegen vergessene Zutaten: Eine Zutat ohne Referenz ist entweder überflüssig oder ein Loch in der Anleitung.

### 6.5 `title` und `summary`
`title` ist die **Abschnittsüberschrift** des Schritts (`Teig`, `Füllung`, `Fertigstellen`), passend zu den Zutatenabschnitten aus §5.7. `summary` ist eine Kurzfassung des Schritts — nur setzen, wenn sie mehr sagt als die ersten Worte des Texts.

---

## 7. Metadaten

| Feld | Regelwerk | Kurzregel |
| --- | --- | --- |
| `recipeCategory` | Kategorien §2 | genau eine, höchstens zwei |
| `tags` | Schlagwörter §2 | höchstens acht, jedes einer Facette zuordenbar |
| `tools` | Utensilien §2 | nur blockierende Geräte, null bis vier |
| `rating` | — | erst nach dem Kochen setzen, nicht beim Anlegen |
| `nutrition` | — | nur übernehmen, wenn aus der Quelle; nie schätzen |

Ein geschätzter Nährwert ist schlechter als keiner, weil er wie eine Messung aussieht.

---

## 8. Notizen (`notes`)

### 8.1 Wo Text hingehört — die Abgrenzung
Mealie hat vier Orte für Text. Der häufigste Fehler ist nicht ein schlecht formulierter Text, sondern ein Text am falschen Ort: Dort findet ihn beim Kochen niemand, und beim Skalieren wird er falsch.

| Frage | Ort | Beispiel |
| --- | --- | --- |
| Gehört es zu **genau einer Zutat**? | `recipeIngredient[].note` | `fein gehackt`, `Original: 1 cup`, `oder Crème fraîche` |
| Ist es ein **Handgriff in der Reihenfolge**? | `recipeInstructions[].text` | `Zwiebel 5 Minuten glasig dünsten` |
| Gilt es fürs **ganze Rezept, ist aber kein Handgriff**? | `notes[]` | `Teig hält sich 2 Tage im Kühlschrank` |
| Ist es der **Einzeiler, wozu das Gericht taugt**? | `description` | siehe §3.2 |

Entscheidungsreihenfolge von oben nach unten. Beim ersten Ja aufhören.

**Kommentare sind kein Notizersatz.** Sie sind Gesprächsverlauf und vergänglich. Wer beim dritten Kochen etwas Bleibendes lernt, schreibt es in eine Notiz `Erfahrung` — nicht in einen Kommentar, wo es unter zehn anderen verschwindet.

### 8.2 Feste Titel (kontrolliertes Vokabular)
`notes` sind Objekte aus `title` und `text` — nicht ein Textklumpen. Wie bei den Schlagwörtern gilt ein festes Vokabular, sonst stehen nach zwei Jahren `Info`, `Hinweis`, `Anmerkung` und `Wichtig!` nebeneinander und keiner weiß, was wo steht.

| Titel | Inhalt |
| --- | --- |
| `Quelle` | Buch, Person, Seitenzahl — nur wenn `orgURL` nicht passt |
| `Variante` | Abwandlungen, die kein eigenes Rezept rechtfertigen (§1.1) |
| `Vorbereitung` | was am Vortag oder Stunden vorher gemacht werden kann |
| `Aufbewahrung` | Haltbarkeit, Einfrieren, Aufwärmen |
| `Dazu passt` | Beilagen, Getränke, Reihenfolge im Menü |
| `Erfahrung` | was beim letzten Mal nicht funktioniert hat |

**`Erfahrung` ist die wertvollste Notiz und wird am häufigsten vergessen.** Sie ist der einzige Ort, an dem steht, dass die Angabe im Original zu wenig Salz war oder der Teig 10 Minuten länger braucht als geschrieben.

Ein neuer Titel nur, wenn er auf mindestens fünf Rezepte passt — sonst gehört der Inhalt unter einen bestehenden.

### 8.3 Form
- **Ein Titel kommt pro Rezept nur einmal vor.** Zwei Notizen `Variante` werden zu einer mit zwei Absätzen.
- **Höchstens fünf Notizen** pro Rezept. Mehr heißt fast immer: etwas gehört nach §8.1 woandershin.
- Der `text` bleibt unter etwa 400 Zeichen. Was länger wird, ist meist ein eigenes Rezept oder ein Zubereitungsschritt.
- Ganze Sätze, kein Stichwortstil — Notizen werden Monate später gelesen.

### 8.4 Was **nicht** in eine Notiz gehört
- Handgriffe, die in `recipeInstructions` gehören — auch nicht als „Tipp"
- Angaben zu einer einzelnen Zutat, die in deren `note` gehören
- Verweise wie `siehe Schritt 3` — Schritte werden umsortiert, der Verweis bleibt falsch stehen
- Zeiten und Portionen, für die es Felder gibt (§4)
- Ein vollständiges Alternativrezept — das ist ein eigenes Rezept
- Allergen-Zusicherungen (Schlagwörter §5): eine Notiz `enthält keine Nüsse` wirkt wie eine Garantie und ist keine

---

## 9. Bild und Einstellungen

**Bild:** eines genügt, vom fertigen Gericht, möglichst selbst fotografiert. Fremde Bilder nur mit `settings.public: false`.

**Einstellungen:** `public` nur bei eigenen Rezepten oder eigener Formulierung. `showNutrition` nur, wenn `nutrition` tatsächlich gefüllt ist. `locked` für Rezepte, die nach mehrfachem Kochen final sind.

---

## 10. Nach dem Import prüfen

Ein Netzimport füllt die Felder, aber selten korrekt. Diese fünf Punkte immer nachsehen:

1. **Zutatenzeilen geparst?** Zeilen ohne verknüpftes `food` sind roher Text und funktionieren nirgends.
2. **Einheiten metrisch?** Cups, Ounces und Sticks umrechnen, `Original:` in die Notiz (Einheiten §3).
3. **Zubereitung in die Notiz gerutscht?** Importer schreiben oft `2 Zwiebeln, fein gehackt` komplett ins `food`.
4. **Schritte sinnvoll geschnitten?** Viele Quellen liefern einen einzigen Block oder Satz-für-Satz-Fragmente.
5. **Metadaten aus der Quelle geprüft?** Importierte Schlagwörter sind meist SEO-Begriffe und verstoßen gegen Schlagwörter §4.

---

## 11. Checkliste

**Vor dem Anlegen**
- [ ] Nach Name und charakteristischen Zutaten auf Dubletten gesucht?
- [ ] Ist es wirklich ein eigenes Rezept und keine Variante (§1.1)?
- [ ] `orgURL` oder Quellennotiz gesetzt?

**Zutaten**
- [ ] Jede Zeile mit verknüpftem `food` und passender `unit`?
- [ ] Ein Lebensmittel pro Zeile?
- [ ] Alle Einheiten metrisch, Umrechnungen mit `Original:` belegt?
- [ ] Zubereitung in der Notiz, nicht im `food`?
- [ ] `originalText` unangetastet?
- [ ] Mengenlose Zutaten mit `quantity: 0` statt erfundener Menge?
- [ ] Selbstgemachte Komponenten als `referencedRecipe` statt als Lebensmittel?
- [ ] Reihenfolge entspricht der Verwendung?

**Zubereitung**
- [ ] Schritte als Handlungsblöcke, nicht als Sätze oder Blöcke?
- [ ] Imperativ, Garzeiten und Zustände genannt?
- [ ] Temperaturen metrisch mit Originalangabe?
- [ ] `ingredientReferences` gesetzt — keine Zutat ohne Schritt?

**Metadaten**
- [ ] Genau eine Kategorie, höchstens acht Schlagwörter, höchstens vier Utensilien?
- [ ] Zeiten im Hausformat, Wartezeit in `totalTime` statt in `prepTime`?
- [ ] `recipeServings` gesetzt, bei Gebäck zusätzlich die Ausbeute?
- [ ] Nährwerte nur aus der Quelle, nie geschätzt?
- [ ] `public` nur bei eigenem Text und eigenem Bild?
