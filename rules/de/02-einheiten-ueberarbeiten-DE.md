# Einheiten: Überarbeiten des vorhandenen Bestands (DE)

> Ergänzung zu **Einheiten: Anlegen & Mappen**. Verweise der Form *Anlegen §x* zeigen dorthin, *Cleanup §x* auf **Food Rules (DE): Überarbeiten des vorhandenen Bestands**.

## Grundsatz

Einheiten sind wenige, aber jede hängt an vielen Zutatenzeilen. Eine falsch zusammengeführte Einheit verfälscht still Hunderte Mengenangaben — und anders als bei Lebensmitteln fällt das niemandem beim Kochen auf, weil die Zahl plausibel bleibt.

> **Standardhandlung: ohne Beleg nichts ändern.** Vor dem ersten Schreibvorgang: Vollexport, Referenzzähler pro Einheit, Changelog-Tabelle, Dry-Run (Cleanup §1).

---

## 1. Reihenfolge der Durchgänge

| # | Durchgang | Art | Risiko |
| - | --------- | --- | ------ |
| 0 | Inventur | nur lesend | keins |
| 1 | Hygiene | nicht destruktiv | gering |
| 2 | Abkürzungs-Kollisionen | nicht destruktiv | gering |
| 3 | Zusammenführen | **destruktiv** | hoch |
| 4 | **Nicht-metrische Einheiten auflösen** | **destruktiv** | **sehr hoch** |
| 5 | Felder vervollständigen | nicht destruktiv | gering |
| 6 | Ausdünnen | destruktiv | mittel |
| 7 | Verifikation | nur lesend | keins |

Durchgang 4 ist der aufwendigste und riskanteste des ganzen Regelwerks, weil er nicht Einheiten, sondern **Mengenwerte** verändert. Er kommt nach dem Zusammenführen, damit nicht dieselbe nicht-metrische Einheit in zwei Dubletten getrennt umgerechnet wird.

---

## 2. Durchgang 0 — Inventur

- Referenzzähler pro Einheit
- Einheiten ohne `abbreviation`, ohne `pluralName`, ohne `description`
- Abkürzungen, die an mehr als einer Einheit hängen — **harter Fehler**
- **alle nicht-metrischen Einheiten** und ihre Referenzzahl → Arbeitsliste für Durchgang 4
- Einheiten mit null Referenzen
- Zutatenzeilen mit `Stück`, wo das Original vermutlich leer war

---

## 3. Durchgang 1 — Hygiene

Trimmen, Interpunktion entfernen (`Gramm.` → `Gramm`), Groß-/Kleinschreibung nach Anlegen §4, Plural-Dubletten erkennen (`Dose`/`Dosen`, `Scheibe`/`Scheiben` als zwei Einträge), Schreibvarianten (`Eßlöffel`/`Esslöffel`), `gr` → `g`.

Findet dieser Durchgang Paare, sind das Merge-Kandidaten für Durchgang 3 — hier nur markieren, nicht zusammenführen.

---

## 4. Durchgang 2 — Abkürzungs-Kollisionen

Hängt dieselbe Abkürzung an zwei Einheiten, ist das Mapping nicht deterministisch und der Parser wählt willkürlich. Das entspricht der Alias-Kollision bei Lebensmitteln (Cleanup §5) und muss vor Durchgang 3 aufgelöst sein.

Typische Fälle: `T` an Teelöffel *und* Esslöffel; `l` an Liter *und* Blatt; `St.` an Stück *und* Stange.

Auflösung: Die etablierte Abkürzung bleibt an der einen Einheit, die andere bekommt eine eindeutige oder gar keine. Einbuchstabige Abkürzungen außer `g` und `l` ersatzlos entfernen.

---

## 5. Durchgang 3 — Zusammenführen

**Kandidatensignale:** identische normalisierte Namen; Singular/Plural-Paare; gleiche Abkürzung; Ausschreibung neben Abkürzung als zwei Einträge (`EL` und `Esslöffel`).

**Merge ist verboten bei:**
- `Teelöffel` vs. `Esslöffel` — Faktor 3
- US- und UK-Volumen, solange beide noch existieren — sie unterscheiden sich real
- `Packung` vs. `Dose` vs. `Glas` — verschiedene Behälter, verschiedene Hausannahmen
- `Prise` vs. `Messerspitze` — kulinarisch verschieden

**Ablauf** (wie Cleanup §6.4): Survivor nach Referenzzähler; kanonische Form nach Anlegen §4 setzen; Varianten des Verlierers in die **Parser-Konfiguration** übernehmen (Einheiten haben keine Alias-Liste, deshalb geht diese Information sonst verloren); alle Zutatenzeilen umhängen; Referenzzähler auf Summe prüfen; Verlierer löschen; protokollieren.

---

## 6. Durchgang 4 — Nicht-metrische Einheiten auflösen

Ziel: **null nicht-metrische Einheiten im Bestand.** Cup, Ounce, Pound, Fluid Ounce, Pint, Quart, Stick, Gallon verschwinden vollständig.

### 6.1 Ablauf pro Einheit
1. **Alle** referenzierenden Zutatenzeilen ziehen, mit Lebensmittel und Menge
2. Nach Typ sortieren: Flüssigkeit, Masse, Trockenvolumen (Anlegen §3.1)
3. Zeilen, deren Lebensmittel **nicht** in der Dichtetabelle steht (Anlegen §3.4), aussortieren → Review, **nicht umrechnen**
4. Die verbleibenden Zeilen einzeln umrechnen und runden (Anlegen §3.5)
5. Pro Zeile die Notiz `Original: …` setzen (Anlegen §3.6), vorhandene Notizen mit `; ` erhalten
6. Auf die metrische Einheit umhängen
7. Erst wenn der Referenzzähler der alten Einheit **null** ist: löschen
8. Protokollieren, mit Angabe der umgerechneten Zeilenzahl

### 6.2 Harte Schutzregeln
- **Nie in Blöcken umrechnen.** Jede Zeile wird gelesen, weil der Faktor vom Lebensmittel abhängt. Eine Sammel-Umrechnung „alle cups × 240 ml" zerstört jedes Backrezept im Bestand.
- **Nie ohne Notiz.** Eine Zeile ohne `Original:` ist nicht mehr überprüfbar — der Fehler wird unauffindbar.
- **Nie raten.** Fehlt der Dichtewert, bleibt die Zeile unverändert und geht in die Review. Eine offene Zeile ist reparierbar, eine falsche Zahl nicht.
- **Nie rückwärts.** Eine bereits umgerechnete Zeile wird nie erneut umgerechnet. Die `Original:`-Notiz ist auch die Erkennungsmarke dafür.
- **Backrezepte zuerst und einzeln.** Dort entscheiden wenige Gramm; herzhafte Rezepte verzeihen Rundung.

### 6.3 Wenn die Umrechnung nicht möglich ist
Bleibt eine nicht-metrische Einheit am Ende referenziert, wird sie **nicht gelöscht**, sondern als `deprecated` markiert: keine neuen Zuweisungen, aber die vorhandenen Zeilen bleiben lesbar. Löschen erst, wenn der Zähler null ist.

---

## 7. Durchgang 5 — Felder vervollständigen

Für jede verbleibende Einheit:
- `abbreviation` gesetzt, eindeutig, korrekt geschrieben
- `pluralName` — unveränderliche Einheiten prüfen (Gramm, Liter, Esslöffel, Stück bleiben gleich); `pluralAbbreviation` = `abbreviation`
- `fraction` passend zur Klasse
- `description` mit Definition (`1 EL = 15 ml`) oder Hausannahme (`Dose: Standardgröße 400 g`)
- Varianten in der Parser-Konfiguration, inklusive alter `ß`-Form

Das ist der Durchgang mit dem besten Aufwand-Nutzen-Verhältnis: Er verwandelt künftige Review-Fälle in automatische Treffer und kostet kein Risiko.

---

## 8. Durchgang 6 — Ausdünnen

| Fall | Aktion |
| --- | --- |
| null Referenzen, metrisch | behalten, wenn Teil des Kernbestands; sonst löschen |
| null Referenzen, nicht-metrisch | löschen |
| Einheit enthält ein Lebensmittel (`Knoblauchzehe`) | Zeilen auf `Zehe` + Food umhängen, dann löschen |
| Einheit ist eine Größenangabe (`groß`) | Zeilen: Wert in die Zutatennotiz, Einheit leeren, dann löschen |
| `Portion` | auf das Rezept-Portionsfeld umhängen, dann löschen |

---

## 9. Durchgang 7 — Verifikation

Gegen die Basiswerte aus Durchgang 0:

- **nicht-metrische Einheiten: null** (oder vollständig als `deprecated` begründet)
- Abkürzungs-Kollisionen: **null**
- Einheiten ohne `abbreviation` oder `description`: **null**
- **Gesamtzahl der Zutatenzeilen unverändert** — jede Abweichung bedeutet Verlust
- Stichprobe: 20 umgerechnete Zeilen manuell nachrechnen, davon mindestens fünf aus Backrezepten
- Alle umgerechneten Zeilen tragen `Original:` — Abweichung heißt, Durchgang 4 war lückenhaft

Die Stichprobe ist nicht optional. Sie ist die einzige Prüfung, die einen systematischen Umrechnungsfehler findet, bevor er in tausend Zeilen steht.

---

## 10. Checkliste

**Vor dem Start**
- [ ] Export erstellt und Rückspielbarkeit geprüft?
- [ ] Referenzzähler pro Einheit vorhanden?
- [ ] Arbeitsliste der nicht-metrischen Einheiten erstellt?

**Pro Merge**
- [ ] Kein verbotenes Paar (§5)?
- [ ] Varianten des Verlierers in die Parser-Konfiguration übernommen?
- [ ] Referenzzähler nach dem Umhängen stimmig?

**Pro Umrechnung**
- [ ] Zeile einzeln gelesen, nicht in Blöcken verarbeitet?
- [ ] Typ korrekt bestimmt und Dichtetabelle verwendet?
- [ ] Lebensmittel nicht in der Tabelle → Zeile unverändert in die Review?
- [ ] `Original: …` gesetzt, vorhandene Notiz erhalten?
- [ ] Rundung innerhalb 2 %?
- [ ] Alte Einheit erst bei Zähler null gelöscht?

**Zum Schluss**
- [ ] Null nicht-metrische Einheiten?
- [ ] Zeilenzahl unverändert?
- [ ] Stichprobe von 20 Zeilen nachgerechnet?
