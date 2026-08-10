# Rezepte: Überarbeiten des vorhandenen Bestands (DE)

> Ergänzung zu **Rezepte: Anlegen & Importieren**. *Anlegen §x* zeigt dorthin, *Cleanup §x* auf **Food Rules (DE): Überarbeiten des vorhandenen Bestands**.

## Grundsatz

Rezepte sind die einzige Entität, die **Inhalt** trägt statt nur Struktur. Ein gelöschtes Schlagwort ist ärgerlich; ein gelöschtes Rezept ist weg — samt Bewertung, Notizen und der Erfahrung aus fünf Jahren.

> **Standardhandlung: ergänzen, nicht ersetzen.** Vor dem ersten Schreibvorgang: Vollexport inklusive Bildern, Changelog, Dry-Run (Cleanup §1).

Anders als bei den Stammdaten lohnt hier **kein flächendeckender Durchlauf**. Der Bestand ist zu groß und die Arbeit zu manuell. Stattdessen nach Wirkung priorisieren:

1. Rezepte, die tatsächlich gekocht werden (`lastMade` gesetzt, hohe `rating`)
2. Rezepte mit kaputten Zutatenzeilen — sie brechen Einkaufsliste und Skalierung
3. Alles Übrige, gelegentlich

---

## 1. Reihenfolge der Durchgänge

| # | Durchgang | Art | Risiko |
| - | --------- | --- | ------ |
| 0 | Inventur | nur lesend | keins |
| 1 | Dubletten | **destruktiv** | hoch |
| 2 | **Zutatenzeilen reparieren** | strukturell | mittel |
| 3 | Einheiten metrisieren | ändert Mengen | **hoch** |
| 4 | Schritte und Abschnitte | inhaltlich | gering |
| 5 | Metadaten | nicht destruktiv | gering |
| 6 | Zeiten, Portionen, Quelle | nicht destruktiv | gering |
| 7 | Verifikation | nur lesend | keins |

Durchgang 2 vor 3, weil sich eine Menge nur umrechnen lässt, wenn Lebensmittel und Einheit überhaupt erkannt sind.

---

## 2. Durchgang 0 — Inventur

- Rezepte gesamt; mit `lastMade`; mit `rating`
- **Anteil der Zutatenzeilen mit verknüpftem `food`** — die wichtigste Kennzahl des ganzen Dokuments
- Zutatenzeilen ohne `unit`, aber mit Zahl im `note`-Feld
- Rezepte mit nicht-metrischen Einheiten (Arbeitsliste aus *Einheiten überarbeiten* §2)
- Rezepte mit genau einem Zubereitungsschritt oder mit mehr als 15
- Rezepte ohne Kategorie, ohne Schritte, ohne Zutaten
- Rezepte mit mehr als acht Schlagwörtern, mehr als zwei Kategorien, mehr als vier Utensilien
- Rezepte ohne `orgURL` und ohne Quellennotiz
- Notizen mit freiem Titel, ohne Titel, oder mehr als fünf Notizen pro Rezept
- Namensdubletten und Beinahe-Dubletten

---

## 3. Durchgang 1 — Dubletten

**Signale:** identischer oder fast identischer `name`; gleiche `orgURL`; gleiche Zutatenmenge bei überlappenden Lebensmitteln; gleiches Bild.

**Kein Merge bei:** demselben Gericht aus verschiedenen Küchen oder mit deutlich anderer Zubereitung (Anlegen §1.1). Zwei Linsensuppen dürfen koexistieren — dann aber den Titel schärfen, damit die Unterscheidung sichtbar ist.

**Ablauf beim Merge:**
1. Survivor ist das Rezept mit **mehr Inhalt** — mehr strukturierte Zutatenzeilen, mehr Notizen, gesetztes `lastMade` und `rating`. Nicht das ältere, nicht das schönere.
2. Aus dem Verlierer **alles Einzigartige übernehmen**: Notizen, Kommentarinhalte, das bessere Bild, eine abweichende Variante als Notiz `Variante` (Anlegen §8)
3. Bewertung: die des häufiger gekochten Rezepts behalten, nicht mitteln
4. Verlierer löschen, protokollieren

Schritt 2 ist der Grund, warum dieser Durchgang manuell bleibt. Was im Verlierer steht, ist meistens genau die Erfahrung, die man behalten will.

---

## 4. Durchgang 2 — Zutatenzeilen reparieren

Der ertragreichste Durchgang. Typische Schäden aus alten Importen:

| Schaden | Erkennung | Reparatur |
| --- | --- | --- |
| Zeile ist roher Text | kein `food` verknüpft | über die Parse-Regeln neu zerlegen, `food` und `unit` verknüpfen |
| Zubereitung im Lebensmittel | `food` heißt `Zwiebeln, fein gehackt` | Zubereitung in `note`, Lebensmittel korrigieren (Parse §4.2) |
| Menge im Notizfeld | `note` enthält `ca. 200 g` | in `quantity` und `unit` überführen |
| Mehrere Lebensmittel in einer Zeile | `Salz und Pfeffer` | in zwei Zeilen trennen (Anlegen §5.2) |
| Erfundene Menge | `1 Stück Salz` | `quantity: 0`, Einheit leeren, `note: nach Geschmack` |
| Selbstgemachte Komponente als Lebensmittel | `food` heißt `Pizzateig` | in `referencedRecipe` umwandeln (Anlegen §5.6) |
| Einheit enthält Lebensmittel | `unit` heißt `Knoblauchzehe` | `unit: Zehe`, `food: Knoblauch` |

**Harte Regel:** `originalText` bleibt **unangetastet**. Sie ist bei jeder Reparatur der einzige Beleg dafür, was ursprünglich dastand. Wer sie überschreibt, macht den nächsten Fehler unauffindbar.

Fehlt `originalText` — bei alten Beständen häufig —, vor der Reparatur den aktuellen `display`-Wert hineinschreiben. Danach reparieren.

---

## 5. Durchgang 3 — Einheiten metrisieren

Läuft gegen die Arbeitsliste aus *Einheiten: Überarbeiten* §6 und folgt exakt deren Schutzregeln:

- **nie in Blöcken** — der Umrechnungsfaktor hängt am Lebensmittel
- **nie ohne Notiz** — `Original: …` an jede geänderte Zeile (Einheiten §3.6)
- **nie raten** — fehlt der Dichtewert, bleibt die Zeile unverändert und geht in die Review
- **nie rückwärts** — eine Zeile mit `Original:` wird nie erneut umgerechnet
- **Backrezepte zuerst und einzeln**

Zusätzlich rezeptspezifisch: **Temperaturen in den Schritten mitnehmen.** Ein Rezept mit metrischen Zutaten und `350 °F` im Text ist halb umgestellt und im Zweifel schlimmer als gar nicht. Format: `175 °C (Original: 350 °F)`.

Ebenso Formgrößen in Zoll in Schritten und Utensilien: 8 inch → 20 cm, 9 inch → 24 cm, 10 inch → 26 cm.

---

## 6. Durchgang 4 — Schritte, Abschnitte und Notizen

Nur bei Rezepten, die tatsächlich gekocht werden. Prüfen:

- **Ein einziger Schritt** → in Handlungsblöcke teilen (Anlegen §6.1)
- **Über 15 Schritte** → meist Satz-für-Satz-Fragmente, zusammenfassen
- **Zutaten ohne `ingredientReferences`** → entweder verknüpfen oder feststellen, dass die Zutat in der Anleitung fehlt. Das ist der zuverlässigste Weg, kaputte Importe zu finden.
- **Abschnittsüberschriften** in Zutaten (§5.7) und Schritten aufeinander abstimmen
- **Mengen im Text**, die nicht zur Zutatenzeile passen → angleichen oder entfernen (Anlegen §6.3)

Sprache nur dort korrigieren, wo sie unverständlich ist. Ein Rezept umzuformulieren, weil der Stil nicht gefällt, ist Arbeit ohne Ertrag.

### 6.1 Notizen einsortieren
Notizen sind der Ort, an dem über Jahre alles landet, wofür sich niemand einen anderen Platz überlegt hat. Jede Notiz gegen die Abgrenzung in *Anlegen §8.1* prüfen:

| Gefundene Notiz | Ziel |
| --- | --- |
| beschreibt einen Handgriff (`Vorher den Ofen vorheizen`) | als Schritt in `recipeInstructions` |
| betrifft eine einzelne Zutat (`Butter zimmerwarm verwenden`) | in die `note` dieser Zutatenzeile |
| enthält `Original:` oder eine Umrechnung | in die `note` der betroffenen Zutatenzeile |
| wiederholt die `description` | löschen |
| nennt Zeit oder Portionen (`dauert etwa 40 Minuten`) | in das jeweilige Feld, dann löschen |
| ist ein vollständiges Alternativrezept | eigenes Rezept anlegen, Notiz auf einen Verweis kürzen |
| trägt einen freien Titel (`Info`, `Hinweis`, `Wichtig!`) | auf das Vokabular aus *Anlegen §8.2* abbilden |
| ist ein Textklumpen ohne Titel | nach Titeln aufteilen |
| behauptet Allergenfreiheit | löschen (Schlagwörter §5) |

**Zwei Notizen mit demselben Titel** zu einer zusammenfassen. **Mehr als fünf Notizen** heißt fast immer, dass mehrere Zeilen der Tabelle zutreffen.

Zuletzt die **Kommentare** durchsehen: Was dort an dauerhaftem Wissen steht — „beim zweiten Mal 10 Minuten länger gebacken" —, wandert in eine Notiz `Erfahrung`. Kommentare bleiben stehen, das Wissen ist dann aber gesichert.

---

## 7. Durchgang 5 — Metadaten

Läuft nach den Bereinigungen der Stammdaten, nicht davor — sonst vertaggt man mit Schlagwörtern, die anschließend zusammengeführt werden.

- Rezepte mit mehr als zwei Kategorien entlasten (Kategorien überarbeiten §7)
- Rezepte mit mehr als acht Schlagwörtern kürzen; Priorität behalten *Küche*, *Ernährung*, *Anlass*
- Utensilien gegen den Blockade-Test prüfen; Küchenausstattung entfernen
- Rezepte ohne Kategorie nachziehen
- Geschätzte Nährwerte **entfernen** — nur Werte aus der Quelle bleiben

---

## 8. Durchgang 6 — Zeiten, Portionen, Quelle

- Zeitformat vereinheitlichen (Anlegen §4.2), Spannen auflösen
- Wartezeiten aus `prepTime` in `totalTime` verschieben — sonst ist jede Aufwandssuche falsch
- `recipeServings` prüfen; bei Gebäck und Eingemachtem `recipeYieldQuantity` und `recipeYield` ergänzen
- `orgURL` nachtragen, wo bekannt; sonst Notiz `Quelle`
- `settings.public` prüfen: bei fremdem Text oder fremdem Bild auf `false`

---

## 9. Durchgang 7 — Verifikation

Gegen die Basiswerte aus Durchgang 0:

- **Anteil Zutatenzeilen mit verknüpftem `food`** — muss deutlich steigen; Ziel über 95 %
- nicht-metrische Einheiten in Zutaten **und** Schritttexten: **null**
- jede umgerechnete Zeile trägt `Original:`
- Rezepte ohne Zutaten, ohne Schritte oder ohne Kategorie: **null**
- Notiztitel außerhalb des Vokabulars: **null**; kein Rezept über fünf Notizen
- **Anzahl der Rezepte unverändert**, außer dokumentierte Merges erklären die Differenz
- **Anzahl der Zutatenzeilen unverändert**, außer dokumentierte Trennungen erklären den Zuwachs
- Stichprobe: fünf überarbeitete Rezepte vollständig lesen und einmal gedanklich nachkochen

Die letzte Prüfung findet, was keine Kennzahl findet: Schritte, die nach der Reparatur auf Zutaten verweisen, die es nicht mehr gibt.

---

## 10. Checkliste

**Vor dem Start**
- [ ] Export inklusive Bilder erstellt und Rückspielbarkeit geprüft?
- [ ] Nach Wirkung priorisiert statt flächendeckend gearbeitet?
- [ ] Stammdaten-Bereinigungen (Lebensmittel, Einheiten, Schlagwörter) vorher gelaufen?

**Pro Merge**
- [ ] Wirklich dasselbe Rezept und keine legitime Variante?
- [ ] Survivor nach Inhalt gewählt, nicht nach Alter?
- [ ] Notizen, Kommentare, Bild und Bewertung aus dem Verlierer übernommen?

**Pro Zutatenreparatur**
- [ ] `originalText` unangetastet — oder vorher aus `display` befüllt?
- [ ] `food` und `unit` verknüpft, Zubereitung in `note`?
- [ ] Mehrfachzeilen getrennt, erfundene Mengen entfernt?
- [ ] Selbstgemachte Komponenten in `referencedRecipe` überführt?

**Pro Umrechnung**
- [ ] Zeile einzeln bearbeitet, Dichtetabelle verwendet?
- [ ] `Original: …` gesetzt?
- [ ] Temperaturen und Formgrößen in den Schritten mitgenommen?

**Zum Schluss**
- [ ] Rezept- und Zeilenzahl erklärt?
- [ ] Über 95 % der Zeilen mit verknüpftem `food`?
- [ ] Fünf Rezepte vollständig gegengelesen?
