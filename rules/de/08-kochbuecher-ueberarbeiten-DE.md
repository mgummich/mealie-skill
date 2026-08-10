# Kochbücher: Überarbeiten des vorhandenen Bestands (DE)

> Ergänzung zu **Kochbücher: Anlegen**.

## Grundsatz

Kochbücher sind die einzige Entität, die **still kaputtgeht**. Ein zusammengeführtes Schlagwort, eine gelöschte Kategorie, ein umbenanntes Utensil — und der Filter greift ins Leere. Das Kochbuch verschwindet nicht, es wird nur leer, und niemand bemerkt es, weil man ein leeres Kochbuch nicht öffnet.

> **Deshalb gilt: Nach jeder Bereinigung von Kategorien, Schlagwörtern oder Utensilien werden die Kochbuchfilter geprüft.** Dieser Durchgang ist kein eigenes Projekt, sondern der Abschluss der anderen.

---

## 1. Reihenfolge der Durchgänge

| # | Durchgang | Art |
| - | --------- | --- |
| 0 | Inventur | nur lesend |
| 1 | **Gebrochene Filter reparieren** | nicht destruktiv |
| 2 | Leere und übervolle Kochbücher | destruktiv |
| 3 | Überschneidungen auflösen | destruktiv |
| 4 | Beschreibungen und Reihenfolge | nicht destruktiv |
| 5 | Sichtbarkeit prüfen | nicht destruktiv |
| 6 | Verifikation | nur lesend |

---

## 2. Durchgang 0 — Inventur

- **Trefferzahl pro Kochbuch** — die einzige Kennzahl, die zählt
- Kochbücher mit **null** Treffern
- Kochbücher mit mehr als 50 Treffern oder mehr als 30 % des Bestands
- Filter, die auf einen Namen oder eine ID verweisen, die es nicht mehr gibt
- Kochbücher ohne `description`
- Kochbücher mit `public: true`
- Kochbuchpaare mit weitgehend gleicher Treffermenge

---

## 3. Durchgang 1 — Gebrochene Filter

Für jedes Kochbuch mit null Treffern oder auffällig eingebrochener Trefferzahl:

| Ursache | Reparatur |
| --- | --- |
| Schlagwort wurde zusammengeführt | Filter auf den Survivor umschreiben |
| Schlagwort wurde in eine andere Entität überführt | Filter auf die Zielentität umschreiben |
| Kategorie wurde zum Schlagwort herabgestuft | Bedingung von Kategorie auf Schlagwort ändern |
| Utensil wurde gelöscht (Blockade-Test) | Bedingung entfernen oder auf das Methoden-Schlagwort umstellen |
| Filter verweist auf eine ID | auf den Namen umstellen (*Anlegen §4.3*) |
| Vokabular fehlt jetzt ganz | Kochbuch löschen — nicht das Schlagwort wiederbeleben |

Die letzte Zeile ist wichtig: Wurde ein Schlagwort zu Recht entfernt, war das darauf gebaute Kochbuch ebenfalls nicht tragfähig. Kein Vokabular zurückholen, um ein Kochbuch zu retten.

---

## 4. Durchgang 2 — Leere und übervolle

| Fall | Aktion |
| --- | --- |
| null Treffer, Filter intakt | löschen — der Bedarf war offenbar keiner |
| unter 5 Treffer, dauerhaft | löschen oder Bedingung lockern |
| über 50 Treffer | Bedingung schärfen oder in zwei Kochbücher teilen |
| über 30 % des Bestands | löschen — das ist der Bestand mit Zusatzklick |
| `Alle Rezepte`, `Sonstiges` | löschen |

Kochbücher zu löschen ist ungefährlich: Es geht **kein Rezept** verloren, nur ein gespeicherter Filter. Das ist die einzige Entität in diesem Regelwerk, bei der Löschen fast folgenlos ist — entsprechend großzügig darf man sein.

---

## 5. Durchgang 3 — Überschneidungen

Zwei Kochbücher mit weitgehend derselben Treffermenge sind eines. Prüfen, welches den klareren Filter und den besseren Namen hat; das andere löschen.

Teilmengen sind dagegen in Ordnung: `Vegetarisch` und `Vegetarische Hauptgerichte` dürfen koexistieren, solange beide regelmäßig benutzt werden. Wird nur eines geöffnet, verschwindet das andere.

---

## 6. Durchgang 4 — Beschreibungen und Reihenfolge

- Jedem Kochbuch eine `description`, die den Filter **in einem Satz** wiedergibt (*Anlegen §5*). Ohne sie ist jede spätere Reparatur Rätselraten.
- `position` neu setzen: die tatsächlich genutzten nach oben. Nach der Bereinigung ist die Liste kurz genug, um sie in einem Zug zu ordnen.
- Namen prüfen: Sagt er das Ergebnis oder den Filter? `Feierabendküche` statt `schnell + Hauptgericht`.

---

## 7. Durchgang 5 — Sichtbarkeit

Jedes Kochbuch mit `public: true` einzeln prüfen: Sind **alle** aktuell enthaltenen Rezepte eigener Text und eigenes Bild? Da sich der Inhalt mit dem Vokabular ändert, kann ein Kochbuch, das gestern unbedenklich war, heute ein fremdes Rezept enthalten.

Im Zweifel auf `false`. Ein öffentliches Kochbuch, dessen Inhalt sich automatisch ändert, ist eine dauerhafte Aufsichtspflicht.

---

## 8. Durchgang 6 — Verifikation

- Kochbücher mit null Treffern: **null**
- Filter, die auf nicht existierendes Vokabular verweisen: **null**
- Kochbücher ohne `description`: **null**
- Filter auf IDs statt Namen: **null**
- Jedes Kochbuch zwischen etwa 5 und 50 Treffern
- Stichprobe: Jedes Kochbuch einmal öffnen und ein Rezept suchen, das fehlen müsste — die gefundenen Lücken sind Vertaggungsfehler, keine Filterfehler

Die letzte Prüfung ist der eigentliche Ertrag: Kochbücher sind der beste vorhandene Test dafür, ob die Rezepte sauber vertaggt sind.

---

## 9. Checkliste

- [ ] Läuft dieser Durchgang **nach** der Bereinigung von Kategorien, Schlagwörtern und Utensilien?
- [ ] Trefferzahl pro Kochbuch erhoben und mit dem Vorwert verglichen?
- [ ] Gebrochene Filter auf das neue Vokabular umgeschrieben?
- [ ] Kein Vokabular wiederbelebt, nur um ein Kochbuch zu retten?
- [ ] Leere, winzige und übervolle Kochbücher bereinigt?
- [ ] Überschneidende Kochbücher zusammengeführt, echte Teilmengen belassen?
- [ ] Jede `description` gibt den Filter in einem Satz wieder?
- [ ] `position` nach tatsächlicher Nutzung gesetzt?
- [ ] Jedes öffentliche Kochbuch auf fremde Inhalte geprüft?
