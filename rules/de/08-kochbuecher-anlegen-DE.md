# Kochbücher: Anlegen (DE)

> Baut auf **Kategorien**, **Schlagwörtern** und **Utensilien** auf. Ein Kochbuch erzeugt keine Ordnung, es **verbraucht** sie.

## Grundsatz

Ein Kochbuch in Mealie ist kein Ordner, in den man Rezepte legt, sondern ein **gespeicherter Filter**. Rezepte fallen hinein, sobald sie den Filter erfüllen — und fallen wieder heraus, wenn sich ihre Schlagwörter ändern.

Felder: `name`, `description`, `slug`, `position`, `public`, `queryFilterString`.

> **Oberste Regel:** Ein Kochbuch ist höchstens so gut wie das Vokabular, auf das es filtert. **Kochbücher erst anlegen, wenn Kategorien und Schlagwörter bereinigt sind** — sonst baut man auf Begriffe, die im nächsten Durchgang zusammengeführt werden, und der Filter läuft still leer.

---

## 1. Der Anlege-Test

Ein neues Kochbuch nur, wenn **alle drei** zutreffen:

1. **Ausdrückbar.** Es lässt sich vollständig als Filter auf vorhandene Kategorien, Schlagwörter, Utensilien, `rating` oder `lastMade` schreiben. Braucht es eine Handauswahl, ist es kein Kochbuch.
2. **Wiederkehrend.** Man öffnet es regelmäßig. Eine einmalige Suche ist eine Suche, kein Kochbuch.
3. **Trefferzahl zwischen etwa 5 und 50.** Weniger ist unnötig, mehr ist keine Auswahl mehr, sondern der Bestand mit Zusatzschritt.

Fehlt ein Schlagwort für den Filter, wird es **zuerst nach den Schlagwortregeln geprüft und angelegt** — nie ein Schlagwort erfinden, nur damit ein Kochbuch funktioniert. Besteht es den Schlagworttest nicht, besteht das Kochbuch ihn auch nicht.

---

## 2. Sinnvolle Kochbücher

| Kochbuch | Filteridee |
| --- | --- |
| Feierabendküche | Schlagwort `schnell` und Kategorie `Hauptgericht` |
| Vegetarische Hauptgerichte | Schlagwort `vegetarisch` und Kategorie `Hauptgericht` |
| Noch nie gekocht | `lastMade` ist leer |
| Bewährt | `rating` ab 4 |
| Airfryer | Schlagwort `Airfryer` |
| Vorratskammer | Schlagwort `Vorratshaltung` |
| Weihnachtsbacken | Schlagwörter `Weihnachten` und Kategorie `Gebäck` |
| Meal Prep fürs Büro | Schlagwörter `Meal Prep` und `einfrierbar` |

`Noch nie gekocht` ist das nützlichste Kochbuch überhaupt und braucht kein einziges Schlagwort — es beantwortet die Frage, warum man Rezepte sammelt.

---

## 3. Keine Kochbücher

| Kandidat | Warum nicht |
| --- | --- |
| ein Kochbuch je Kategorie (`Desserts`) | die Kategorieansicht tut das bereits |
| `Muss ich testen` | das ist der Essensplan oder `Noch nie gekocht` |
| ein Kochbuch je Person | dafür gibt es Haushalte und Benutzer |
| `Alle Rezepte` | leerer Filter, kein Nutzen |
| `Sonstiges` | ein Filter, den man nicht beschreiben kann, ist keiner |
| ein Kochbuch für ein einzelnes Menü | das ist ein Essensplan |

---

## 4. `queryFilterString`

### 4.1 Wie man ihn erzeugt
Den Filter **in der Oberfläche zusammenklicken und die erzeugte Zeichenkette übernehmen.** Die Syntax ist versionsabhängig; von Hand geschriebene Filter brechen beim Update still, und ein stiller Bruch heißt: leeres Kochbuch, das niemandem auffällt.

### 4.2 Was filterbar ist
Rezeptfelder und deren Beziehungen: Kategorien, Schlagwörter, Utensilien, `rating`, `lastMade`, `createdAt`, Haushalt und Benutzer.

**Nicht filterbar ist `extras`** (Extras §1). Was je zur Auswahl dienen soll, gehört deshalb in ein Schlagwort, nicht in ein Extra.

### 4.3 Aufbau
- Bedingungen mit `AND` und `OR` verknüpfen, Gruppen klammern
- **Höchstens drei Bedingungen.** Ein Filter, den man nicht in einem Satz erklären kann, wird nach einem halben Jahr nicht mehr verstanden und nicht mehr gepflegt.
- `OR` sparsam: Zwei mit `OR` verknüpfte Themen sind meist zwei Kochbücher.
- Nach Möglichkeit auf **Namen** statt auf IDs filtern — Namen überstehen einen Neuaufbau der Datenbank, IDs nicht.

---

## 5. Weitere Felder

**`name`** — Substantivphrase, sagt das Ergebnis, nicht den Filter: `Feierabendküche`, nicht `vegetarisch + schnell`. Kein `Meine`, keine Emoji.

**`description`** — ein Satz, der den Filter **in Worten** wiedergibt: *Vegetarische Hauptgerichte, die in unter 30 Minuten fertig sind.* Ohne diesen Satz weiß später niemand, warum ein Rezept fehlt, und der Filter wird geraten statt gelesen.

**`position`** — die Reihenfolge in der Seitenleiste. Alltagskochbücher nach oben, saisonale und seltene nach unten. Die Position bewusst setzen; die Reihenfolge nach Anlagedatum ist selten die nützliche.

**`public`** — dieselbe Regel wie bei Rezepten: nur öffentlich, wenn **alle** enthaltenen Rezepte eigener Text und eigenes Bild sind. Da sich der Inhalt eines Kochbuchs automatisch ändert, ist das schwer zu garantieren — im Zweifel `false`.

**`slug`** wird erzeugt und nicht von Hand gesetzt.

---

## 6. Nach dem Anlegen prüfen

1. **Trefferzahl ansehen.** Null oder drei Treffer heißt: Filter falsch oder Vokabular fehlt.
2. **Zwei Stichproben.** Ein Rezept öffnen, das drin ist, und eines, das fehlen müsste — stimmt beides?
3. **Gegenprobe.** Ein Rezept suchen, das drin sein *sollte* und fehlt. Meist fehlt ihm ein Schlagwort, nicht dem Kochbuch eine Bedingung.

Punkt 3 ist der eigentliche Wert des ganzen Konstrukts: Kochbücher decken Lücken im Vertaggen auf, die sonst niemand findet.

---

## 7. Checkliste

- [ ] Kategorien und Schlagwörter vorher bereinigt?
- [ ] Vollständig als Filter ausdrückbar, ohne Handauswahl?
- [ ] Wiederkehrender Bedarf, nicht eine einmalige Suche?
- [ ] Trefferzahl zwischen etwa 5 und 50?
- [ ] Kein fehlendes Schlagwort erfunden, nur damit der Filter geht?
- [ ] Filter in der Oberfläche erzeugt statt von Hand geschrieben?
- [ ] Höchstens drei Bedingungen, auf Namen statt IDs?
- [ ] `description` gibt den Filter in einem Satz wieder?
- [ ] `position` bewusst gesetzt?
- [ ] `public` nur bei durchgehend eigenem Inhalt?
- [ ] Trefferzahl und zwei Stichproben geprüft?
