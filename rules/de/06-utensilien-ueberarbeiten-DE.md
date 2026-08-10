# Utensilien: Überarbeiten des vorhandenen Bestands (DE)

> Ergänzung zu **Utensilien: Anlegen & Zuweisen**. *Cleanup §x* verweist auf **Food Rules (DE): Überarbeiten des vorhandenen Bestands**.

## Grundsatz

Utensilien haben **keine Aliasse**. Jede abweichende Schreibweise ist deshalb ein eigener Eintrag, und der Bestand verdoppelt sich stiller als bei jeder anderen Entität: `Springform`, `Springform 26cm`, `Springform 26 cm`, `Backform (Springform)` stehen nebeneinander, und niemand sieht es, weil jedes nur an drei Rezepten hängt.

Der zweite typische Schaden: Der Bestand ist mit **Küchenausstattung** gefüllt — Messer, Schüssel, Topf — und beantwortet damit die Frage „Was kann ich heute kochen?" nicht mehr.

> Vor dem ersten Schreibvorgang: Export, Referenzzähler pro Utensil, Changelog (Cleanup §1).

---

## 1. Reihenfolge der Durchgänge

| # | Durchgang | Art |
| - | --------- | --- |
| 0 | Inventur | nur lesend |
| 1 | Hygiene | nicht destruktiv |
| 2 | Schreibvarianten zusammenführen | destruktiv |
| 3 | **Blockade-Test anwenden** | destruktiv |
| 4 | Marken und Größen bereinigen | destruktiv |
| 5 | `onHand` prüfen | nicht destruktiv |
| 6 | Rezepte entlasten | nicht destruktiv |
| 7 | Verifikation | nur lesend |

---

## 2. Durchgang 0 — Inventur

- Referenzzähler pro Utensil
- Einträge, die sich nur in Schreibweise, Leerzeichen oder Größe unterscheiden
- Einträge mit Markennamen
- Einträge, die den Blockade-Test nicht bestehen — meist die größte Gruppe
- **Rezepte mit mehr als vier Utensilien**
- `onHand`-Verteilung: steht alles auf `false` oder alles auf `true`, wurde das Flag nie gepflegt

---

## 3. Durchgang 1 — Hygiene

Trimmen, Groß-/Kleinschreibung, Plural → Singular (`Springformen` → `Springform`), Leerzeichen vor Einheiten vereinheitlichen (`26cm` → `26 cm`), Klammerzusätze entfernen (`Backform (Springform)` → `Springform`).

---

## 4. Durchgang 2 — Schreibvarianten zusammenführen

Weil es keine Aliasse gibt, ist das hier der ertragreichste Durchgang. Kandidaten:

- Schreibvarianten: `Airfryer` / `Air Fryer` / `Heißluftfritteuse`
- Mit und ohne Größe: `Springform` / `Springform 26 cm`
- Gattung und Marke: `Küchenmaschine` / `Thermomix` / `KitchenAid`
- Deutsch und Englisch: `Standmixer` / `Blender`; `Slow Cooker` / `Schongarer`

**Survivor** ist der Eintrag, der der Benennungsregel entspricht (Anlegen §4) — deutscher Gattungsbegriff, Singular, ohne Marke. Der Referenzzähler entscheidet nur bei Gleichstand, weil das Umhängen hier billig ist.

Ablauf: Survivor festlegen, Rezepte umhängen, Zähler auf Summe prüfen, Verlierer löschen, protokollieren.

---

## 5. Durchgang 3 — Blockade-Test anwenden

Jedes Utensil gegen Anlegen §1 prüfen: **Hat eine funktionierende Durchschnittsküche das Gerät ohnehin?**

Fällt die Antwort auf „ja", wird das Utensil **von allen Rezepten entfernt** und danach gelöscht. Typische Kandidaten: Messer, Schneidebrett, Topf, Pfanne, Schüssel, Sieb, Rührlöffel, Backblech, Schneebesen, Reibe, Ofen, Herd.

Das fühlt sich nach Verlust an und ist keiner: Diese Einträge tragen null Information, weil sie auf jedes Rezept zutreffen. Genau wie ein Schlagwort an 90 % der Rezepte filtern sie nichts.

**Grenzfälle** einzeln entscheiden: verhindert das Fehlen das Gericht oder erschwert es nur? Im Zweifel entfernen — ein fehlendes Utensil ist leichter nachzutragen als ein überfülltes Register zu leeren.

---

## 6. Durchgang 4 — Marken und Größen

**Marken** in den Gattungsbegriff überführen (Anlegen §4). Ausnahme nur, wenn die Marke umgangssprachlich zum Gattungsbegriff geworden ist und keine gängige Alternative existiert.

**Größen** prüfen: Steht eine Größe im Namen, ohne dass sie das Ergebnis bestimmt, entfernen und mit dem generischen Eintrag zusammenführen. Bestimmt sie das Ergebnis, muss sie **metrisch** und auf eine gängige Formgröße gerundet sein — Zoll-Angaben aus Originalrezepten umrechnen: 8 inch → 20 cm, 9 inch → 24 cm, 10 inch → 26 cm.

---

## 7. Durchgang 5 — `onHand` prüfen

`onHand` ist der Haushaltsbestand. Nach einer Bereinigung ist die Liste kurz genug, um sie einmal vollständig durchzugehen — das dauert Minuten und macht die Frage „Was kann ich heute kochen?" erstmals verlässlich beantwortbar.

Steht der gesamte Bestand auf demselben Wert, wurde das Flag nie gepflegt und die Funktion war nie in Betrieb.

---

## 8. Durchgang 6 — Rezepte entlasten

Rezepte mit mehr als vier Utensilien durchsehen. Nach Durchgang 3 sollte die Liste weitgehend leer sein; was übrig bleibt, sind Rezepte, die tatsächlich Spezialgerät brauchen — oder Rezepte, bei denen jemand die Zubereitungsschritte in die Utensilienliste kopiert hat.

Verbrauchsmaterial (`Backpapier`, `Frischhaltefolie`, `Zahnstocher`) ist kein Utensil und gehört in die Zubereitungsschritte.

---

## 9. Durchgang 7 — Verifikation

- Keine zwei Einträge, die dasselbe Gerät bezeichnen
- Keine Markennamen außer den begründeten Ausnahmen
- Kein Eintrag, der den Blockade-Test nicht besteht
- Alle Größenangaben metrisch
- Rezepte mit mehr als vier Utensilien: **null** oder begründet
- Durchschnitt Utensilien pro Rezept: **unter 1,5**
- `onHand` für jeden Eintrag bewusst gesetzt

---

## 10. Checkliste

- [ ] Schreibvarianten zusammengeführt — es gibt keine Aliasse, die sie auffangen?
- [ ] Survivor nach Benennungsregel gewählt, nicht nach Zähler?
- [ ] Blockade-Test auf **jeden** Eintrag angewendet?
- [ ] Küchenausstattung erst von allen Rezepten entfernt, dann gelöscht?
- [ ] Marken in Gattungsbegriffe überführt?
- [ ] Größen nur bei Ergebnisrelevanz behalten und metrisch angegeben?
- [ ] Verbrauchsmaterial in die Zubereitungsschritte verschoben?
- [ ] `onHand` einmal vollständig durchgegangen?
