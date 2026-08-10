# Kategorien: Überarbeiten des vorhandenen Bestands (DE)

> Ergänzung zu **Kategorien: Anlegen & Zuweisen**. *Cleanup §x* verweist auf **Food Rules (DE): Überarbeiten des vorhandenen Bestands**.

## Grundsatz

Kategorien sind wenige und tragen die Navigationsstruktur. Der typische Schaden ist nicht ein Tippfehler, sondern eine **gebrochene Achse**: Über die Zeit sind Gerichtstyp, Mahlzeit, Küche und Anlass nebeneinander gewachsen, jedes Rezept hat vier Kategorien und keine sortiert mehr.

> Vor dem ersten Schreibvorgang: Export, Referenzzähler pro Kategorie, Changelog (Cleanup §1).

---

## 1. Reihenfolge der Durchgänge

| # | Durchgang | Art |
| - | --------- | --- |
| 0 | Inventur | nur lesend |
| 1 | Hygiene | nicht destruktiv |
| 2 | **Achse wiederherstellen** | umstrukturierend |
| 3 | Zusammenführen | destruktiv |
| 4 | Ausdünnen und hochstufen | destruktiv |
| 5 | Rezepte entlasten | nicht destruktiv |
| 6 | Verifikation | nur lesend |

---

## 2. Durchgang 0 — Inventur

- Referenzzähler pro Kategorie
- Kategorien mit unter fünf Rezepten
- **Rezepte mit mehr als zwei Kategorien** — das ist der Achsen-Indikator
- Rezepte ohne Kategorie
- Kategorien im Plural, mit Emoji, mit Quellen- oder Markennamen

Steht der Durchschnitt bei mehr als 1,5 Kategorien pro Rezept, ist die Achse mit hoher Wahrscheinlichkeit gebrochen.

---

## 3. Durchgang 1 — Hygiene

Trimmen, Groß-/Kleinschreibung, Plural → Singular (`Hauptgerichte` → `Hauptgericht`), Emoji und Nummerierungen entfernen.

Beim Umbenennen gilt wie überall: Die alte Schreibweise geht verloren, weil Kategorien keine Aliasse haben — externe Importe, die die alte Schreibweise verwenden, müssen angepasst werden.

---

## 4. Durchgang 2 — Achse wiederherstellen

Der Kern der Überarbeitung.

1. **Achse festlegen** und dokumentieren (Anlegen §1). Empfehlung: Gerichtstyp.
2. Jede vorhandene Kategorie einer der Achsen zuordnen: Gerichtstyp, Mahlzeit, Küche, Ernährung, Anlass, Aufwand, Methode, Zutat, Quelle, Status.
3. Alles, was **nicht** auf der gewählten Achse liegt, wird **in eine andere Entität überführt** — nicht gelöscht:

| Gefundene Kategorie | Ziel |
| --- | --- |
| `Frühstück`, `Abendessen` | Schlagwort, Facette *Anlass* |
| `Italienisch`, `Asiatisch` | Schlagwort, Facette *Küche* |
| `Vegetarisch`, `Vegan` | Schlagwort, Facette *Ernährung* |
| `Schnell`, `Unter 30 Minuten` | Schlagwort, Facette *Aufwand* |
| `Weihnachten`, `Grillen` | Schlagwort, Facette *Anlass* |
| `Airfryer`, `Slow Cooker` | Schlagwort *Methode* + Utensil |
| `Hähnchen`, `Kürbis` | ersatzlos — Zutatensuche |
| `Favoriten`, `Muss ich testen` | Schlagwort oder Kochbuch-Funktion |

**Überführen heißt:** erst das Schlagwort anlegen, dann alle Rezepte der Kategorie damit vertaggen, Zählerstände vergleichen, dann die Kategorie löschen. Nie umgekehrt — sonst geht die Zuordnung verloren.

---

## 5. Durchgang 3 — Zusammenführen

Kandidaten: Singular/Plural-Paare, Synonyme (`Nachtisch`/`Dessert`, `Vorspeise`/`Starter`), Ober-/Unterbegriffe, die niemand trennt (`Kuchen` und `Torte`).

Ablauf wie Cleanup §6.4: Survivor nach Referenzzähler, Rezepte umhängen, Zähler auf Summe prüfen, löschen, protokollieren.

**Merge verboten bei:** Kategorien, die auf der Achse tatsächlich verschieden sind — `Beilage` und `Salat` überschneiden sich, sind aber nicht dasselbe. Überschneidung ist kein Merge-Grund; nur Bedeutungsgleichheit ist einer.

---

## 6. Durchgang 4 — Ausdünnen und hochstufen

| Fall | Aktion |
| --- | --- |
| unter 5 Rezepte nach einem Jahr | in ein Schlagwort umwandeln (§4-Verfahren) |
| null Rezepte | löschen |
| über 40 % aller Rezepte | prüfen, ob eine sinnvolle Teilung existiert — eine Kategorie, in der fast alles liegt, sortiert nichts |
| Schlagwort mit über 15 Rezepten, das auf der Achse liegt | **zur Kategorie hochstufen** — der umgekehrte Weg ist ausdrücklich vorgesehen |

---

## 7. Durchgang 5 — Rezepte entlasten

Alle Rezepte mit mehr als zwei Kategorien durchsehen. Nach Durchgang 2 sollte die Liste fast leer sein; was übrig bleibt, sind echte Grenzfälle (eine Suppe, die Hauptgericht ist).

Regel: die **dominante** Kategorie behalten, die zweite nur, wenn das Gericht wirklich beides ist. Dritte und weitere entfernen.

---

## 8. Durchgang 6 — Verifikation

- Alle Kategorien liegen auf **einer** Achse
- Durchschnitt Kategorien pro Rezept: **1,0–1,3**
- Kategorien mit unter fünf Rezepten: **null**
- Rezepte ohne Kategorie: bekannt und begründet
- **Keine Rezeptzuordnung verloren** — jede in Durchgang 2 überführte Kategorie muss ein Schlagwort mit gleichem Zählerstand hinterlassen haben

Der letzte Punkt ist die Integritätsprüfung: Wer `Vegetarisch` als Kategorie löscht, ohne vorher 60 Rezepte zu vertaggen, verliert 60 Zuordnungen unwiederbringlich.

---

## 9. Checkliste

- [ ] Achse festgelegt und dokumentiert?
- [ ] Jede Kategorie einer Achse zugeordnet?
- [ ] Abweichende Kategorien **überführt** statt gelöscht — Schlagwort zuerst, Zähler verglichen, dann löschen?
- [ ] Merges nur bei Bedeutungsgleichheit, nicht bei Überschneidung?
- [ ] Kategorien unter fünf Rezepten zu Schlagwörtern umgewandelt?
- [ ] Schlagwörter über 15 Rezepten auf Hochstufung geprüft?
- [ ] Rezepte mit mehr als zwei Kategorien bereinigt?
- [ ] Keine Zuordnung verloren?
