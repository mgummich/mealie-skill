# Einheiten: Anlegen & Mappen bei der Rezepterstellung (DE)

> Teil der Mealie-Regelwerke. Verweise der Form *Parse §x* zeigen auf **Food Rules (DE): Parsen & Anlegen**.

## Grundsatz

Einheiten sind eine **geschlossene Menge** von etwa 25–40 Einträgen. Beim Rezeptimport wird praktisch nie eine Einheit angelegt — ein unbekanntes Einheitswort ist fast immer eine Schreibvariante, ein Lebensmittel oder eine nicht-metrische Einheit, die umgerechnet gehört.

> **Harte Regel 1 — metrisch.** Die Datenbank enthält **ausschließlich metrische Einheiten** sowie dimensionslose Zähl- und Behältermaße. Cup, Ounce, Pound, Fluid Ounce, Pint, Quart, Stick und Gallon werden **nie als Einheit angelegt**, in keiner Sprachfassung.

> **Harte Regel 2 — Original erhalten.** Wird eine Menge umgerechnet, muss die Originalangabe als **Notiz an der Zutatenzeile** stehen. Eine Umrechnung ohne Notiz ist Datenverlust: Sie ist nicht nachprüfbar, nicht korrigierbar und beim nächsten Import nicht wiedererkennbar.

---

## 1. Der erlaubte Bestand

### 1.1 Masse
`Milligramm (mg)`, `Gramm (g)`, `Kilogramm (kg)`

### 1.2 Volumen
`Milliliter (ml)`, `Liter (l)`, `Teelöffel (TL)`, `Esslöffel (EL)`

Teelöffel und Esslöffel sind zulässig, weil sie metrisch definiert sind: **1 TL = 5 ml, 1 EL = 15 ml**. Diese Definition gehört in die `description` der Einheit.

`Tasse` ist **keine** zulässige Einheit. Sie ist je nach Herkunft 200, 237 oder 250 ml und wird deshalb immer umgerechnet (§3).

### 1.3 Zähl- und Behältermaße
`Stück`, `Prise`, `Messerspitze`, `Bund`, `Zweig`, `Zehe`, `Stange`, `Scheibe`, `Blatt`, `Kopf`, `Knolle`, `Würfel`, `Handvoll`, `Schuss`, `Spritzer`, `Packung`, `Päckchen`, `Dose`, `Glas`, `Flasche`, `Becher`, `Tüte`

Diese sind dimensionslos und werden **nicht** umgerechnet. Bei schwankenden Behältern gehört die Hausannahme in die `description`: `Dose` → `Standardgröße 400 g, sofern nicht anders angegeben.`

### 1.4 Die leere Einheit
`2 Eier`, `1 Zitrone` haben keine Einheit. Das ist richtig und wird nie zu `Stück` erzwungen.

---

## 2. Mapping beim Import

Reihenfolge, beim ersten Treffer anhalten:

| Stufe | Prüfung | Aktion |
| --- | --- | --- |
| 0 | Token entspricht `abbreviation` einer Einheit | verknüpfen |
| 1 | Token entspricht `name` oder `pluralName` | verknüpfen |
| 2 | Token steht in der Variantenliste (§2.1) | verknüpfen |
| 3 | Token ist eine nicht-metrische Einheit | **umrechnen** (§3) |
| 4 | Token ist in Wahrheit ein Lebensmittel oder eine Größenangabe | §2.2 |
| 5 | Kein Treffer | **Review — nicht anlegen** |

### 2.1 Variantenliste
Einheiten haben in Mealie keine Alias-Liste. Die Varianten gehören deshalb in die Parser-Konfiguration:

| Ziel | Varianten |
| --- | --- |
| Esslöffel | `EL, El, el, Essl., Eßlöffel, Esslöffel, Eßl.` |
| Teelöffel | `TL, Tl, tl, Teel., Teelöffel` |
| Gramm | `g, gr, Gr., gramm, Gramm` |
| Kilogramm | `kg, Kg, kilo, Kilo` |
| Milliliter | `ml, mL, Milliliter` |
| Packung | `Pck., Pckg., Pkg., Packung, Päckchen` |
| Messerspitze | `Msp., Msp, Messerspitze` |
| Stück | `St., Stk., Stck., Stück` |

Die alte `ß`-Schreibung (`Eßlöffel`) taucht in eingescannten und älteren Quellen zuverlässig auf und wird sonst nie zugeordnet.

### 2.2 Kein Einheiten-Token
| Erkannt | Warum | Ergebnis |
| --- | --- | --- |
| `Knoblauchzehe` | Lebensmittel im Wort | Einheit `Zehe` + Food `Knoblauch` (Parse §4.7) |
| `groß`, `mittel`, `klein` | Größenangabe | Zutatennotiz |
| `nach Geschmack`, `etwas` | keine Menge | leere Einheit + Notiz |
| `Portion` | Mealie-Rezeptfeld | Portionsfeld verwenden |
| `2 EL` | Menge im Token | Menge ins Mengenfeld |

---

## 3. Umrechnung nicht-metrischer Angaben

### 3.1 Ablauf
1. Nicht-metrische Einheit erkennen
2. **Typ bestimmen:** Flüssigkeit, Masse oder Trockenvolumen
3. Umrechnen (§3.2–3.4)
4. **Kaufmännisch runden** (§3.5)
5. **Notiz schreiben** (§3.6)
6. Metrische Einheit verknüpfen

Bei Unsicherheit in Schritt 2 oder 3: **nicht raten.** Menge und Originaleinheit in die Notiz, Zeile in die Review. Eine falsche Umrechnung im Backrezept ist schlimmer als eine offene Frage.

### 3.2 Direkte Masse und Volumen
| Original | Metrisch | Praxiswert |
| --- | --- | --- |
| 1 oz | 28,35 g | **28 g** |
| 1 lb | 453,6 g | **450 g** |
| 1 fl oz | 29,57 ml | **30 ml** |
| 1 pint (US) | 473 ml | **475 ml** |
| 1 pint (UK) | 568 ml | **570 ml** |
| 1 quart (US) | 946 ml | **950 ml** |
| 1 gallon (US) | 3,785 l | **3,8 l** |
| 1 stick Butter | 113,4 g | **115 g** |
| 1 inch | 2,54 cm | **2,5 cm** |

### 3.3 Flüssigkeiten nach Volumen
Dichte ≈ 1, also direkt: 1 US cup = 240 ml, 1 UK/metrische Tasse = 250 ml, 1 US tbsp = 14,8 ml ≈ **15 ml**, 1 US tsp = 4,9 ml ≈ **5 ml**.

Löffelmaße aus US-Quellen werden also einfach zu `EL` und `TL` — die Abweichung liegt unter 2 % und damit unter der Küchenpräzision.

### 3.4 Trockene Zutaten nach Volumen — Dichtetabelle
Das ist der einzige wirklich fehleranfällige Fall. Eine Tasse Mehl und eine Tasse Honig unterscheiden sich um fast das Dreifache. **Nie über ml umwegen und dann Masse schätzen** — die Tabelle verwenden.

Werte je **1 US cup (240 ml)**:

| Zutat | Masse |
| --- | --- |
| Weizenmehl | 120 g |
| Vollkornmehl | 130 g |
| Zucker, weiß | 200 g |
| Zucker, braun (gepresst) | 220 g |
| Puderzucker | 120 g |
| Butter | 227 g |
| Öl | 218 g |
| Milch, Wasser | 240 g |
| Naturjoghurt | 245 g |
| Honig, Sirup | 340 g |
| Haferflocken | 90 g |
| Reis, roh | 185 g |
| Kakaopulver | 85 g |
| Nüsse, gehackt | 120 g |
| Semmelbrösel | 108 g |
| Schokotropfen | 170 g |
| Käse, gerieben | 100 g |

Löffelmaße trockener Zutaten: 1 EL Mehl ≈ 8 g, 1 EL Zucker ≈ 12 g, 1 EL Butter ≈ 14 g, 1 EL Honig ≈ 21 g, 1 TL Salz ≈ 6 g.

**Steht die Zutat nicht in der Tabelle:** in Milliliter umrechnen, Originalangabe in die Notiz, Zeile in die Review. Die Tabelle wird erweitert, sobald dieselbe Zutat zweimal auftaucht.

### 3.5 Rundung
| Bereich | Schrittweite |
| --- | --- |
| < 20 g/ml | 1 |
| 20–100 g/ml | 5 |
| 100–1000 g/ml | 10 |
| > 1000 g/ml | 50, oder in kg/l mit einer Nachkommastelle |

Nie Scheingenauigkeit: `236,588 ml` ist falsch, `240 ml` ist richtig. **Grenze:** Die Rundung darf höchstens 2 % vom exakten Wert abweichen. Bei Backrezepten mit Triebmitteln, Salz oder Hefe im Zweifel feiner runden — dort entscheiden wenige Gramm.

### 3.6 Notizformat (verbindlich)
Die Notiz beginnt immer mit demselben Präfix, damit sie maschinell auffindbar ist:

```
Original: 1 cup
Original: 2 sticks Butter
Original: 8 oz
```

Nur die Originalangabe, keine Erklärung, keine Umrechnung — die steht ja bereits in der Zeile. Vorhandene Zubereitungsnotizen bleiben erhalten und werden mit `; ` angehängt:

```
fein gehackt; Original: 1 cup
```

### 3.7 Temperaturen
Gehören nicht zu den Einheiten, sondern in die Zubereitungsschritte, folgen aber derselben Regel:

| °F | °C Ober-/Unterhitze | °C Umluft |
| --- | --- | --- |
| 300 | 150 | 130 |
| 325 | 160 | 140 |
| 350 | 175 | 155 |
| 375 | 190 | 170 |
| 400 | 200 | 180 |
| 425 | 220 | 200 |
| 450 | 230 | 210 |

Umluft = Ober-/Unterhitze minus 20 °C. Die Originalangabe kommt in Klammern dahinter: `175 °C (Original: 350 °F)`.

---

## 4. Wann doch eine Einheit anlegen?

Selten, und nur wenn **alle drei** zutreffen:

1. Sie ist metrisch oder dimensionslos.
2. Sie existiert nicht bereits unter Name, Abkürzung oder Variante.
3. Sie taucht in **mehr als einem** Rezept auf — ein Einzelfall bleibt in der Review.

Beim Anlegen:
- `name` ausgeschrieben, Singular, deutsche Rechtschreibung
- `abbreviation` in der üblichen Form mit korrekter Groß-/Kleinschreibung; **nie einbuchstabig** außer `g` und `l`; nie `gr` für Gramm
- `pluralName`: viele deutsche Einheiten sind **unveränderlich** — Gramm, Kilogramm, Liter, Milliliter, Esslöffel, Teelöffel, Stück bleiben gleich; Prise → Prisen, Zehe → Zehen, Scheibe → Scheiben, Dose → Dosen, Blatt → Blätter, Kopf → Köpfe
- `pluralAbbreviation` = `abbreviation`; Abkürzungen werden nie pluralisiert (`500 g`, nicht `500 gs`)
- `fraction` an bei Löffel- und Stückmaßen, aus bei Gramm und Milliliter
- `description` trägt die Definition bzw. Hausannahme

---

## 5. Checkliste

- [ ] Ist das Token wirklich eine Einheit und kein Lebensmittel, keine Größe, keine Menge?
- [ ] Wurde die Variantenliste geprüft, inklusive alter `ß`-Schreibung?
- [ ] Bei nicht-metrischer Einheit: Typ korrekt bestimmt (Flüssigkeit / Masse / Trockenvolumen)?
- [ ] Bei Trockenvolumen: Dichtetabelle verwendet statt geschätzt?
- [ ] Zutat nicht in der Tabelle → Review statt Rateversuch?
- [ ] Sinnvoll gerundet, Abweichung unter 2 %?
- [ ] **Notiz `Original: …` gesetzt?**
- [ ] Vorhandene Zubereitungsnotiz erhalten geblieben?
- [ ] Keine neue Einheit angelegt, obwohl eine Umrechnung genügt hätte?
