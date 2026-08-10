# Extras: Konvention & Pflege (DE)

> Gilt für das Feld `extras` auf **Rezepten, Lebensmitteln und Einheiten**.

Dieses Dokument fasst Anlegen und Überarbeiten zusammen, weil `extras` kein eigenes Objekt ist, sondern ein Feld — und weil die Pflege aus genau einem Durchgang besteht.

## Grundsatz

`extras` ist ein freies Schlüssel-Wert-Objekt ohne Schema. Genau deshalb ist es die Stelle, an der eine gepflegte Datenbank zuerst verwildert: Alles, wofür sich niemand einen Platz überlegen will, landet hier, und niemand merkt es, weil das Feld in der Oberfläche kaum sichtbar ist.

> **Oberste Regel:** `extras` ist die **letzte** Möglichkeit, nicht die bequemste. Was in ein vorhandenes Feld passt, gehört dorthin — auch wenn das mehr Arbeit ist.

> **Zweite Regel:** Ein Schlüssel, der nicht im Register (§3) steht, existiert nicht und wird beim nächsten Durchgang gelöscht.

---

## 1. Was `extras` **nicht** ist

| Verlockung | Warum falsch | Richtiger Ort |
| --- | --- | --- |
| `extras.zubereitungszeit` | es gibt `prepTime` | Rezeptfeld |
| `extras.vegetarisch` | Klassifikation zum Filtern | Schlagwort |
| `extras.notiz` | Fließtext fürs Kochen | `notes[]` (Rezepte §8) |
| `extras.quelle` | dafür gibt es `orgURL` | Rezeptfeld |
| `extras.bewertung` | es gibt `rating` | Rezeptfeld |
| `extras.kalorien` | es gibt `nutrition` | Rezeptfeld |

**Der entscheidende technische Grund:** Kochbuchfilter greifen auf Rezeptfelder zu — auf Kategorien, Schlagwörter, Utensilien, `rating`, `lastMade` —, **nicht auf `extras`**. Was man je zum Filtern braucht, ist in `extras` funktional tot. Das ist der häufigste und teuerste Fehler mit diesem Feld.

---

## 2. Wann `extras` berechtigt ist

Drei Fälle, sonst keiner:

1. **Fremdsystem-Identifikatoren.** Die ID aus dem Quellsystem eines Imports, eine GTIN am Lebensmittel, eine Artikelnummer beim Lieferanten. Daten, die Mealie nicht kennt und nie kennen wird.
2. **Automatisierung.** Flags für externe Werkzeuge — Home Assistant, n8n, eigene Skripte. Nichts, was ein Mensch in der Oberfläche liest.
3. **Haushaltsspezifische Werte ohne Feld.** Der übliche Einkaufsort eines Lebensmittels, der Standardpreis, das Regal im Vorratsschrank.

Alles drei hat gemeinsam: **Maschinen lesen es, Menschen nicht.** Sobald ein Mensch den Wert beim Kochen oder Einkaufen sehen soll, ist `extras` der falsche Ort.

---

## 3. Schlüssel-Register (verbindlich)

Es gibt ein Register, das jeden erlaubten Schlüssel führt: Name, Entität, Zweck, Wertformat, verantwortliches System. Ohne Register ist `extras` nicht pflegbar, weil man einen Tippfehler nicht von einem neuen Schlüssel unterscheiden kann.

### 3.1 Namensform
`namensraum.schluessel` — beides kleingeschrieben, nur `a–z`, `0–9`, `.` und `_`. Keine Leerzeichen, keine Umlaute, keine Bindestriche.

Der Namensraum benennt das **System**, nicht das Thema:

| Namensraum | Bedeutung |
| --- | --- |
| `import.` | stammt aus einem Import |
| `pantry.` | Vorrats- und Einkaufsdaten |
| `automation.` | von externen Werkzeugen gelesen oder geschrieben |
| `legacy.` | aus einer Altdatenbank übernommen, nur zur Nachvollziehbarkeit |

### 3.2 Beispielregister

| Schlüssel | Entität | Zweck | Format |
| --- | --- | --- | --- |
| `import.source_id` | Rezept | ID im Quellsystem | Zeichenkette |
| `import.imported_at` | Rezept | Importzeitpunkt | ISO-8601 |
| `pantry.gtin` | Lebensmittel | Barcode | 8–14 Ziffern |
| `pantry.shelf` | Lebensmittel | Regal im Vorrat | Zeichenkette |
| `pantry.default_price` | Lebensmittel | Preis je Einheit | Dezimalzahl als Zeichenkette |
| `automation.print_label` | Rezept | vom Etikettendrucker gelesen | `true` / `false` |
| `legacy.old_unit` | Einheit | Name vor der Metrisierung | Zeichenkette |

### 3.3 Werte
- **Immer Zeichenketten.** Das Feld erlaubt mehr, aber gemischte Typen brechen jedes Skript, das über den Bestand läuft.
- Wahrheitswerte als `true` / `false` in Kleinschreibung
- Datumsangaben als ISO-8601: `2026-08-10`
- Zahlen mit Punkt als Dezimaltrenner, ohne Einheit im Wert: `2.49`, nicht `2,49 €`
- **Keine Listen, keine verschachtelten Objekte.** Wer eine Liste braucht, braucht eine eigene Entität.
- **Keine personenbezogenen Daten.** `extras` wird bei Exporten und Freigaben mitgegeben und ist nirgends als vertraulich markiert.

---

## 4. Pflege (ein Durchgang)

**Schritt 1 — Inventur.** Alle vorkommenden Schlüssel über Rezepte, Lebensmittel und Einheiten auslesen, mit Häufigkeit. Das ist bereits die halbe Arbeit: In der Regel sind es weniger als zwanzig verschiedene, und die Hälfte davon Tippfehler.

**Schritt 2 — Gegen das Register abgleichen.**

| Befund | Aktion |
| --- | --- |
| im Register, Format korrekt | belassen |
| im Register, Format falsch | Wert normalisieren |
| Tippfehler oder Schreibvariante eines registrierten Schlüssels | umbenennen |
| passt in ein echtes Feld (§1) | **dorthin überführen**, dann löschen |
| kommt genau einmal vor und niemand kennt es | löschen |
| berechtigt nach §2, aber nicht registriert | **registrieren** — nicht löschen |

**Schritt 3 — Verifikation.** Kein Schlüssel außerhalb des Registers; keine Werte mit anderem Typ als Zeichenkette; keine personenbezogenen Daten; jeder registrierte Schlüssel hat ein verantwortliches System. Ein Schlüssel, für den sich kein System mehr zuständig fühlt, ist ein Löschkandidat beim nächsten Durchgang.

---

## 5. Checkliste

**Vor dem Schreiben eines Extras**
- [ ] Gibt es wirklich kein passendes Feld (§1)?
- [ ] Wird der Wert je zum Filtern gebraucht? Dann darf er **nicht** hierhin.
- [ ] Fällt er unter einen der drei berechtigten Fälle (§2)?
- [ ] Liest ihn eine Maschine und kein Mensch?
- [ ] Steht der Schlüssel im Register — oder wird er jetzt dort eingetragen?
- [ ] Namensform `namensraum.schluessel`, klein, ohne Umlaute?
- [ ] Wert als Zeichenkette, ISO-Datum, Punkt als Dezimaltrenner, keine Einheit im Wert?
- [ ] Keine personenbezogenen Daten?

**Bei der Pflege**
- [ ] Alle Schlüssel über alle drei Entitäten inventarisiert?
- [ ] Schlüssel mit echtem Zielfeld überführt statt gelöscht?
- [ ] Einzelvorkommen geprüft und entfernt?
- [ ] Jeder registrierte Schlüssel hat ein verantwortliches System?
