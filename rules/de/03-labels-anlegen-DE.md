# Labels: Anlegen & Zuweisen (DE)

> Ergänzung zu **Food Rules (DE): Parsen & Anlegen**. Dort steht in §9, *welches* Label ein Lebensmittel bekommt. Hier steht, wie das Label selbst aussieht.

## Grundsatz

Ein Label ist in Mealie eine eigene Entität (`MultiPurposeLabel`) mit genau zwei Feldern: `name` und `color`. Es hängt am **Lebensmittel**, nicht am Rezept, und sein einziger echter Zweck ist die **Einkaufsliste**: Es gruppiert und sortiert, damit man den Laden einmal durchläuft statt dreimal.

> **Oberste Regel:** Das Label beantwortet *„wo steht das im Laden?"* — nicht *„was ist das kulinarisch?"* und schon gar nicht *„was für ein Gericht ist das?"*. Die letzten beiden Fragen beantworten Kategorien und Schlagwörter, und die hängen an Rezepten.

Geschlossene Menge, **29 Einträge**. Wachstum ist ein Fehlersignal.

---

## 1. Abgrenzung

| Entität | Hängt an | Beantwortet |
| --- | --- | --- |
| **Label** | Lebensmittel | Wo im Laden liegt es? |
| Kategorie | Rezept | Was für ein Gericht ist das? |
| Schlagwort | Rezept | Welche Eigenschaft hat das Rezept? |

Ein Label wie `Vegetarisch` oder `Schnell` ist ein Kategorienfehler: Beides sind Eigenschaften von Rezepten, nicht Regale im Supermarkt. Ein Label `Weihnachten` ebenso.

---

## 2. Der Anlege-Test

Ein neues Label nur, wenn **alle vier** zutreffen:

1. Es entspricht einer **eigenen Zone im Laden oder Vorrat** — etwas, wofür man einen eigenen Weg macht.
2. Mindestens **zehn Lebensmittel** fallen hinein. Weniger heißt: Das gehört in ein bestehendes Label.
3. Es überschneidet sich mit keinem bestehenden Label. Bei Überschneidung gewinnt das bestehende.
4. Es ist keine Eigenschaft, sondern ein Ort (§1).

Trifft eines nicht zu, bekommt das Lebensmittel das nächstliegende bestehende Label — oder `Sonstiges`, das ausdrücklich als Arbeitsliste gedacht ist.

---

## 3. Benennung

- Substantiv, deutsche Groß-/Kleinschreibung, wie in der festen Liste (Food Rules §9.3)
- Plural ist hier **richtig**, weil Labels Warengruppen bezeichnen: `Milchprodukte`, `Hülsenfrüchte`, `Nüsse & Samen`
- Doppelbegriffe mit `&`, wo die Zone zwei Dinge umfasst: `Öl, Essig & Fett`
- Keine Emoji im `name` — sie brechen die Sortierung und die Suche

---

## 4. Farben

### 4.1 Die Farbe ist funktional
`color` ist kein Dekor. Auf der Einkaufsliste erkennt man am Farbblock, dass ein neuer Bereich beginnt — bevor man den Text liest. Zufällige Farben machen die Liste unlesbarer als gar keine.

**Regel: Die Farbe kodiert die Zone, nicht das einzelne Label.** Labels derselben Zone teilen sich einen Farbton in verschiedenen Helligkeiten. Dass `Käse` und `Milchprodukte` ähnlich aussehen, ist kein Fehler, sondern die Absicht — sie liegen im Laden nebeneinander.

### 4.2 Zonenpalette

| # | Label | Zone | `color` |
| -- | --- | --- | --- |
| 1 | Gemüse | Frisch (Grün) | `#43A047` |
| 2 | Obst | Frisch | `#7CB342` |
| 3 | Frische Kräuter | Frisch | `#1B5E20` |
| 4 | Kartoffeln & Knollen | Frisch | `#9CCC65` |
| 5 | Fleisch | Fleisch & Fisch (Rot) | `#B71C1C` |
| 6 | Geflügel | Fleisch & Fisch | `#E53935` |
| 7 | Fisch & Meeresfrüchte | Fleisch & Fisch | `#FF7043` |
| 8 | Wurst & Aufschnitt | Fleisch & Fisch | `#AD1457` |
| 9 | Milchprodukte | Gekühlt (Blau) | `#1E88E5` |
| 10 | Käse | Gekühlt | `#64B5F6` |
| 11 | Eier | Gekühlt | `#0D47A1` |
| 12 | Brot & Gebäck | Brot & Frühstück (Braun) | `#8D6E63` |
| 13 | Backzutaten | Brot & Frühstück | `#BCAAA4` |
| 14 | Frühstückscerealien | Brot & Frühstück | `#5D4037` |
| 15 | Nudeln & Reis | Trocken (Gelb/Oliv) | `#F9A825` |
| 16 | Hülsenfrüchte | Trocken | `#9E9D24` |
| 17 | Nüsse & Samen | Trocken | `#827717` |
| 18 | Kräuter & Gewürze | Würzen (Orange) | `#EF6C00` |
| 19 | Öl, Essig & Fett | Würzen | `#FFB300` |
| 20 | Saucen & Würzmittel | Würzen | `#F4511E` |
| 21 | Brühe & Geschmacksgeber | Würzen | `#BF360C` |
| 22 | Snacks | Snacks & Süß (Pink) | `#EC407A` |
| 23 | Süßwaren & Aufstriche | Snacks & Süß | `#C2185B` |
| 24 | Getränke | Getränke (Türkis) | `#00ACC1` |
| 25 | Wein | Getränke (Alkohol, Violett) | `#8E24AA` |
| 26 | Bier | Getränke | `#26C6DA` |
| 27 | Spirituosen & Liköre | Getränke (Alkohol) | `#6A1B9A` |
| 28 | Kaffee & Tee | Getränke | `#00838F` |
| 29 | Sonstiges | Rest (Grau) | `#757575` |

### 4.3 Farbregeln
- **Nur Hex mit sechs Stellen und führendem `#`.** Mealies Standard ist `#959595`; ein Label, das darauf stehen bleibt, ist ungepflegt.
- Kein Farbton doppelt vergeben — auch nicht in verschiedenen Zonen.
- Ausreichend dunkel oder ausreichend hell, damit der Text lesbar bleibt; Mittelgraue mit wenig Kontrast vermeiden.
- **Nie auf Farbe allein verlassen.** Rot-Grün-Schwäche betrifft etwa jeden zwölften Mann; deshalb steht der Name immer daneben und die Reihenfolge (§5) trägt die eigentliche Struktur.

---

## 5. Reihenfolge auf der Einkaufsliste

Die Sortierung der Labels wird pro Einkaufsliste gesetzt und ist der eigentliche Nutzen des ganzen Systems. **Sie folgt dem Weg durch den Laden, nicht dem Alphabet.**

Bewährte Reihenfolge für einen typischen deutschen Supermarkt:

`Gemüse` → `Obst` → `Frische Kräuter` → `Kartoffeln & Knollen` → `Brot & Gebäck` → `Milchprodukte` → `Käse` → `Eier` → `Fleisch` → `Geflügel` → `Wurst & Aufschnitt` → `Fisch & Meeresfrüchte` → `Nudeln & Reis` → `Hülsenfrüchte` → `Backzutaten` → `Frühstückscerealien` → `Nüsse & Samen` → `Kräuter & Gewürze` → `Öl, Essig & Fett` → `Saucen & Würzmittel` → `Brühe & Geschmacksgeber` → `Snacks` → `Süßwaren & Aufstriche` → `Kaffee & Tee` → `Getränke` → `Bier` → `Wein` → `Spirituosen & Liköre` → `Sonstiges`

Die Reihenfolge einmal im eigenen Laden ablaufen und anpassen. Sie ist wichtiger als jede Farbe.

---

## 6. Label zuweisen

Jedes Lebensmittel bekommt **genau ein** Label — das Feld `labelId` ist einwertig. Die Zuordnungsregeln stehen in den Food Rules §9.1 und §9.2, insbesondere: nach dem labeln, **was es ist**, nicht nach Herkunft oder Verwendung.

Ein Lebensmittel ohne Label landet auf der Einkaufsliste unsortiert am Ende. Das ist der schnellste Weg, das System unbrauchbar zu machen.

---

## 7. Checkliste

- [ ] Beantwortet das Label „wo im Laden", nicht „welche Eigenschaft" (§1)?
- [ ] Mindestens zehn Lebensmittel, keine Überschneidung mit einem bestehenden?
- [ ] Name aus der festen Liste, Plural, ohne Emoji?
- [ ] `color` gesetzt, sechsstelliges Hex, nicht der Standard `#959595`?
- [ ] Farbton passt zur Zone und ist nicht doppelt vergeben?
- [ ] Reihenfolge auf der Einkaufsliste dem Ladenweg angepasst?
- [ ] Jedes Lebensmittel hat genau ein Label?
