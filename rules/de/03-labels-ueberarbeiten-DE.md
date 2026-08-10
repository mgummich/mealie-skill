# Labels: Überarbeiten des vorhandenen Bestands (DE)

> Ergänzung zu **Labels: Anlegen & Zuweisen**. *Cleanup §x* verweist auf **Food Rules (DE): Überarbeiten des vorhandenen Bestands**.

## Grundsatz

Labels sind wenige, aber jedes hängt an vielen Lebensmitteln und damit an jeder Einkaufsliste. Der typische Schaden ist nicht ein falscher Name, sondern eine **kaputte Achse**: Über die Zeit sind Warengruppen, Ernährungsformen und Verwendungszwecke nebeneinander gewachsen, und die Einkaufsliste sortiert nichts mehr.

> Vor dem ersten Schreibvorgang: Export, Anzahl Lebensmittel pro Label, Changelog (Cleanup §1).

---

## 1. Reihenfolge der Durchgänge

| # | Durchgang | Art |
| - | --------- | --- |
| 0 | Inventur | nur lesend |
| 1 | **Achse wiederherstellen** | umstrukturierend |
| 2 | Zusammenführen | destruktiv |
| 3 | Lebensmittel ohne Label nachziehen | nicht destruktiv |
| 4 | Farben vereinheitlichen | nicht destruktiv |
| 5 | Reihenfolge am Ladenweg ausrichten | nicht destruktiv |
| 6 | Verifikation | nur lesend |

---

## 2. Durchgang 0 — Inventur

- Anzahl Lebensmittel pro Label, absteigend
- **Lebensmittel ohne Label** — die wichtigste Zahl; sie landen unsortiert am Listenende
- Labels mit weniger als zehn Lebensmitteln
- Labels mit der Standardfarbe `#959595` oder ohne gesetzte Farbe
- Doppelt vergebene Farbtöne
- Labels, die keine Warengruppe bezeichnen (§3)
- Größe des Labels `Sonstiges` — über 5 % des Bestands heißt: Es wird als Ablage benutzt

---

## 3. Durchgang 1 — Achse wiederherstellen

Jedes Label prüfen: Bezeichnet es eine **Zone im Laden**? Wenn nicht, gehört es in eine andere Entität — und wird **überführt, nicht gelöscht**:

| Gefundenes Label | Ziel |
| --- | --- |
| `Vegetarisch`, `Vegan`, `Glutenfrei` | Schlagwort am Rezept, Facette *Ernährung* |
| `Hauptgericht`, `Dessert` | Kategorie am Rezept |
| `Schnell`, `Vorrat` | Schlagwort, Facette *Aufwand* bzw. *Haltbarkeit* |
| `Weihnachten`, `Grillen` | Schlagwort, Facette *Anlass* |
| `Asiatisch`, `Italienisch` | Schlagwort, Facette *Küche* — **nicht** ein Label „Asia-Regal" |
| `Lieblingszutaten`, `Test` | ersatzlos |

**Überführen heißt:** erst das Ziel anlegen und die betroffenen Rezepte oder Lebensmittel dort verknüpfen, Zählerstände vergleichen, dann das Label löschen. Die Lebensmittel des gelöschten Labels bekommen vorher ein korrektes Warengruppen-Label — sonst stehen sie anschließend ohne da.

Der Fall `Asiatisch` ist der verführerischste: In manchen Läden gibt es tatsächlich ein Asia-Regal. Trotzdem ist Sojasauce eine Sauce und Reis ein Trockenprodukt — die Herkunft ist eine Rezepteigenschaft, kein Warengruppen-Ort (Food Rules §9.1).

---

## 4. Durchgang 2 — Zusammenführen

**Kandidaten:** Singular/Plural-Paare (`Gewürz`/`Gewürze`), Synonyme (`Milchprodukte`/`Molkereiprodukte`), Ober- und Unterbegriffe, die niemand trennt (`Nüsse` und `Samen` als zwei Labels), Übersetzungsdubletten (`Dairy`/`Milchprodukte`).

**Merge verboten bei:** Labels, die im Laden wirklich getrennt liegen. `Käse` und `Milchprodukte` überschneiden sich fachlich, sind aber zwei Wege — das ist der Grund, warum die Food Rules sie ausdrücklich trennen.

**Ablauf:** Survivor ist das Label mit den meisten Lebensmitteln; kanonischen Namen nach *Anlegen §3* setzen; **alle Lebensmittel des Verlierers umhängen**; Zähler auf Summe prüfen; Verlierer löschen; protokollieren.

Der Zählerabgleich ist hier besonders wichtig: Ein gelöschtes Label setzt `labelId` der betroffenen Lebensmittel still auf leer, und das fällt erst beim nächsten Einkauf auf.

---

## 5. Durchgang 3 — Lebensmittel ohne Label

Die Arbeitsliste aus Durchgang 0, absteigend nach Verwendungshäufigkeit im Rezeptbestand abarbeiten. Ein Lebensmittel, das in 30 Rezepten steht, ist eine Stunde wert; eines aus einem einzigen Rezept kann warten.

Zuweisung nach Food Rules §9.1 und §9.2. Was sich wirklich nicht einordnen lässt, bekommt `Sonstiges` — aber `Sonstiges` ist eine **Arbeitsliste, kein Ruheort**: Wächst es über 5 % des Bestands, fehlt entweder ein Label oder die Zuordnung wird zu bequem gemacht.

---

## 6. Durchgang 4 — Farben

Die Zonenpalette aus *Anlegen §4.2* durchsetzen:

- Alle Labels mit `#959595` bekommen ihre Zonenfarbe
- Doppelt vergebene Farbtöne auflösen
- Prüfen, dass jede Zone als Block erkennbar ist und benachbarte Zonen sich deutlich unterscheiden

Der Durchgang ist risikofrei und in zwanzig Minuten erledigt — er verändert nur `color` und kein einziges Lebensmittel.

---

## 7. Durchgang 5 — Reihenfolge

Die Label-Sortierung der Einkaufsliste am tatsächlichen Ladenweg ausrichten (*Anlegen §5*). Am besten mit der nächsten realen Einkaufsliste in der Hand: Wo man springen muss, stimmt die Reihenfolge nicht.

Bei mehreren Läden nach dem hauptsächlich genutzten sortieren. Zwei konkurrierende Reihenfolgen sind schlechter als eine unvollkommene.

---

## 8. Durchgang 6 — Verifikation

- **Lebensmittel ohne Label: null**
- Labels, die keine Warengruppe bezeichnen: **null**
- Labels mit Standardfarbe: **null**
- Doppelte Farbtöne: **null**
- `Sonstiges` unter 5 % des Lebensmittelbestands
- **Keine Label-Zuordnung verloren** — jedes in Durchgang 1 überführte Label muss seine Lebensmittel auf einem anderen Label wiederfinden
- Praxistest: eine echte Einkaufsliste erzeugen und einmal durchlaufen

Der Praxistest ist die einzige Prüfung, die zeigt, ob die Reihenfolge stimmt. Keine Kennzahl ersetzt ihn.

---

## 9. Checkliste

- [ ] Jedes Label als Warengruppe geprüft, Fremdkörper **überführt** statt gelöscht?
- [ ] Vor dem Löschen eines Labels dessen Lebensmittel neu zugeordnet?
- [ ] Merges nur bei Bedeutungsgleichheit, nicht bei fachlicher Überschneidung?
- [ ] Lebensmittel ohne Label nach Verwendungshäufigkeit abgearbeitet?
- [ ] Zonenpalette vollständig durchgesetzt, keine Standardfarbe mehr?
- [ ] Reihenfolge am realen Ladenweg geprüft?
- [ ] `Sonstiges` unter 5 %?
