# Schlagwörter: Überarbeiten des vorhandenen Bestands (DE)

> Ergänzung zu **Schlagwörter: Anlegen & Zuweisen**. *Cleanup §x* verweist auf **Food Rules (DE): Überarbeiten des vorhandenen Bestands**.

## Grundsatz

Schlagwörter verwildern schneller als jede andere Entität, weil sie frei anlegbar sind und niemand beim Anlegen die Liste sieht. Der typische Bestand nach zwei Jahren: dreihundert Einträge, davon die Hälfte einmal verwendet, ein Dutzend Synonymgruppen, und ein paar Schlagwörter an fast jedem Rezept.

> Vor dem ersten Schreibvorgang: Export, Referenzzähler pro Schlagwort, Changelog (Cleanup §1).

---

## 1. Reihenfolge der Durchgänge

| # | Durchgang | Art |
| - | --------- | --- |
| 0 | Inventur | nur lesend |
| 1 | Hygiene | nicht destruktiv |
| 2 | **Facettierung** | umstrukturierend |
| 3 | Synonyme zusammenführen | destruktiv |
| 4 | Entität korrigieren | umstrukturierend |
| 5 | Ausdünnen | destruktiv |
| 6 | Rezepte entlasten | nicht destruktiv |
| 7 | Verifikation | nur lesend |

---

## 2. Durchgang 0 — Inventur

- Referenzzähler pro Schlagwort, absteigend sortiert
- Schlagwörter mit **einer** Referenz — meist die größte Gruppe
- Schlagwörter an **über 90 %** der Rezepte
- Schlagwörter, die keiner Facette zuzuordnen sind
- **Rezepte mit mehr als acht Schlagwörtern**
- Schlagwörter mit Zahlen, Emoji, `#`, Und-Verknüpfungen

---

## 3. Durchgang 1 — Hygiene

Trimmen, Groß-/Kleinschreibung nach Anlegen §6 (Adjektive klein, Substantive groß), Plural → Singular, Emoji und `#` entfernen, Bindestrich-Schreibweise vereinheitlichen.

Achtung: Reine Schreibvarianten (`Vegetarisch`/`vegetarisch`) sind hier zu vereinheitlichen — inhaltliche Synonyme (`veggie`/`fleischlos`) gehören in Durchgang 3.

---

## 4. Durchgang 2 — Facettierung

Jedes Schlagwort einer Facette zuordnen (Anlegen §1). Das Ergebnis ist eine Tabelle, die anschließend gepflegt wird.

Was sich **keiner** Facette zuordnen lässt, ist ein Kandidat für Durchgang 4 oder 5 — nicht für eine neue Facette. Neue Facetten nur, wenn mindestens fünf bestehende Schlagwörter hineinfallen.

Die Facettierung ist Voraussetzung für Durchgang 3: Synonyme liegen fast immer innerhalb einer Facette, und facettenweise zu prüfen ist um Größenordnungen schneller als paarweise.

---

## 5. Durchgang 3 — Synonyme zusammenführen

Facette für Facette durchgehen. Typische Gruppen:

- `vegetarisch` / `veggie` / `fleischlos` / `ohne Fleisch`
- `schnell` / `blitzschnell` / `in 20 Minuten` / `Feierabend`
- `Ofen` / `Backofen` / `aus dem Ofen`
- `Meal Prep` / `Vorkochen` / `mealprep`
- `kinderfreundlich` / `Kinder` / `familientauglich`

**Survivor** ist das Schlagwort, das der Benennungsregel entspricht — **nicht** automatisch das mit dem höchsten Zähler. Anders als bei Lebensmitteln ist das Umhängen hier billig und die Benennung entscheidet über künftige Konsistenz.

Ablauf: Survivor festlegen, alle Rezepte des Verlierers vertaggen, Zähler prüfen, Verlierer löschen, protokollieren.

---

## 6. Durchgang 4 — Entität korrigieren

| Gefundenes Schlagwort | Ziel |
| --- | --- |
| `Hauptgericht`, `Dessert` | Kategorie — Schlagwort löschen, wenn die Kategorie schon zugewiesen ist |
| `Springform 26 cm`, `Eismaschine` | Utensil — überführen, dann löschen |
| `Hähnchen`, `mit Kürbis` | ersatzlos löschen, Zutatensuche deckt es ab |
| `30 Minuten`, `4 Portionen` | in das Mealie-Rezeptfeld übertragen, dann löschen |
| `ohne Nüsse`, `ohne Gluten` | **löschen** — Negativ-Zusicherung (Anlegen §5); ggf. durch das positive `glutenfrei` ersetzen |
| `Test`, `TODO`, `neu` | löschen |

Wie bei Kategorien gilt: **erst überführen, dann löschen.** Ein Utensil anzulegen und die Rezepte zu verknüpfen kostet zehn Minuten; die verlorene Zuordnung kostet einen Nachmittag.

---

## 7. Durchgang 5 — Ausdünnen

| Fall | Aktion |
| --- | --- |
| eine Referenz | zusammenführen, wenn eine Gruppe passt; sonst löschen |
| null Referenzen | löschen |
| über 90 % der Rezepte | löschen — es filtert nichts |
| unter 5 Referenzen und keine Facette | löschen |

Beim Löschen keine Sentimentalität: Ein Schlagwort, das seit zwei Jahren ein Rezept trägt, findet dieses Rezept nicht besser als die Volltextsuche.

---

## 8. Durchgang 6 — Rezepte entlasten

Rezepte mit mehr als acht Schlagwörtern durchsehen. Nach den Durchgängen 3–5 schrumpft diese Liste meist von selbst.

Priorität beim Kürzen: Facetten *Küche*, *Ernährung* und *Anlass* behalten — sie werden am häufigsten gefiltert. *Quelle* und *Publikum* fliegen zuerst.

---

## 9. Durchgang 7 — Verifikation

- Jedes Schlagwort hat **genau eine** Facette
- Schlagwörter mit einer Referenz: **null** oder begründet
- Schlagwörter über 90 %: **null**
- Rezepte mit mehr als acht Schlagwörtern: **null**
- Gesamtzahl der Schlagwort-Zuordnungen darf sinken — aber jede in Durchgang 4 überführte Gruppe muss ihre Zuordnungen in der Zielentität wiederfinden
- Stichprobe: fünf Rezepte pro Facette ansehen — filtert die Facette tatsächlich sinnvoll?

---

## 10. Checkliste

- [ ] Facettentabelle vollständig, jedes Schlagwort zugeordnet?
- [ ] Synonyme facettenweise geprüft, nicht paarweise?
- [ ] Survivor nach Benennungsregel gewählt, nicht nach Zähler?
- [ ] Falsche Entitäten **überführt** statt gelöscht?
- [ ] Negativ-Schlagwörter (`ohne X`) entfernt?
- [ ] Einzelreferenzen und 90-%-Schlagwörter bereinigt?
- [ ] Kein Rezept über acht Schlagwörtern?
- [ ] Zuordnungen der überführten Gruppen in der Zielentität nachweisbar?
