# Mealie Food Rules (DE): Parsen & Anlegen

## Zweck
Diese Regeln gelten, wenn ein **Lebensmittel-String** ankommt — aus einem Rezeptimport, einer manuellen Eingabe oder einer Bereinigung. Die Aufgabe lautet in dieser Reihenfolge:

1. Den String einem **bereits vorhandenen** Lebensmittel zuordnen.
2. Wenn keine Zuordnung möglich ist: entscheiden, ob es **überhaupt existieren soll**.
3. Erst dann **anlegen**, nach den Benennungsregeln in §8.

Der Normalfall ist *zuordnen*, nicht *anlegen*. Jedes unnötige neue Lebensmittel ist ein dauerhaftes Duplikat, das Einkaufslisten zersplittert und die Rezeptaggregation zerstört.

> **Oberste Regel:** Nie ein Lebensmittel anlegen, das sich von einem vorhandenen nur durch Plural, Groß-/Kleinschreibung, Interpunktion, Umlautschreibung, Zubereitungsangabe oder einen entfernten Qualifikator unterscheidet.

---

## 0. Sprachraum (einmal festlegen, nie mischen)

Kanonisch ist **bundesdeutsches Standarddeutsch**. AT- und CH-Varianten sind **Aliasse** auf dem kanonischen Lebensmittel — nie ein zweiter Eintrag und nie ein Grund zum Anlegen.

| Kanonisch (DE) | Alias (AT/CH)                    |
| -------------- | -------------------------------- |
| Kartoffel      | Erdapfel, Erdäpfel               |
| Tomate         | Paradeiser                       |
| Aubergine      | Melanzani                        |
| Hackfleisch    | Faschiertes, Gehacktes           |
| Quark          | Topfen                           |
| Sahne          | Obers, Rahm, Nidel               |
| Brötchen       | Semmel, Schrippe, Weckle         |
| Blumenkohl     | Karfiol                          |
| Pfifferling    | Eierschwammerl                   |
| Aprikose       | Marille                          |
| Meerrettich    | Kren                             |
| Johannisbeere  | Ribisel                          |

Innerdeutsche Varianten ebenso als Alias: `Möhre` kanonisch, `Karotte`, `Mohrrübe`, `gelbe Rübe`, `Wurzel` als Alias.

---

## 1. Der Lebensmittel-Datensatz

- `name` (string): kanonischer Name (DE, Singular, korrekt großgeschrieben)
- `pluralName` (string): gängiger Plural, oder gleich `name` bei Stoffnamen
- `description` (string): `Definition; Verwendung/Zubereitung.`
- `aliases` (array): immer vorhanden, mindestens `[]`, Einträge als `{ "name": "..." }`
- `label` (string): genau ein Label aus §9

`name`, `pluralName` und jeder Alias sind **Suchschlüssel**. Aliasse sind keine Dekoration — sie sind der Mechanismus, der das Matching überhaupt funktionieren lässt. Jede aufgelöste Nicht-Zuordnung fließt zurück (§11).

---

## 2. Was ist ein Lebensmittel-String?

Der Lebensmittel-String ist das, was von einer Rezeptzeile übrig bleibt, wenn Menge, Einheit und Anweisung entfernt sind. Er ist **nicht** die Rezeptzeile.

```
"2 EL frisch gehackter Koriander, plus etwas mehr zum Servieren"
 └ Menge ┘ └ Zubereitung ┘ └ FOOD ┘ └ Serviervorschlag ──────┘
                                ↓
                       Koriander [frisch]
```

Eine Zeile kann **mehrere** Strings enthalten. An `und`, `oder`, `/` und an Kommas zwischen vollständigen Lebensmitteln trennen:
- `"Salz und Pfeffer nach Geschmack"` → `Salz`, `Pfeffer`
- `"Olivenöl, zum Anbraten"` → `Olivenöl`

---

## 3. Normalisierungs-Pipeline (nur für die Suche)

In genau dieser Reihenfolge. Ergebnis ist ein **Suchschlüssel**, der nie in die Datenbank geschrieben wird — der gespeicherte `name` behält immer seine korrekte Form.

1. Unicode NFC; trimmen; Mehrfach-Leerzeichen zusammenfassen
2. Groß-/Kleinschreibung vollständig auf Kleinschreibung falten
3. Umschließende Interpunktion, nachgestellte Kommas/Punkte und Klammereinschübe entfernen — `(ca. 200 g)`, `(optional)` gehören in die Rezeptnotiz, nie ins Lebensmittel
4. **Umlaute und ß beidseitig falten** (§4.5)
5. Artikel und vage Mengenangaben am Anfang entfernen: `ein`, `eine`, `einen`, `etwas`, `ein wenig`, `ein paar`, `der`, `die`, `das`
6. Mengen und Einheiten entfernen (§4.1)
7. Zubereitungsangaben entfernen (§4.2)
8. Werbe- und Herkunftsadjektive entfernen (§4.3)
9. **Adjektivendungen normalisieren** (§4.4)
10. Singularisieren (§4.6)
11. Qualifikatoren extrahieren (§5) — **extrahieren, nicht verwerfen**

Der Rest ist der **Kandidaten-Basisname**.

> **Zuerst am längsten matchen, zuletzt strippen.** Die volle Kaskade zuerst gegen den *rohen* String laufen lassen, dann nach jeder Stripping-Stufe erneut. `geräucherte Forelle`, `saure Sahne`, `grüner Spargel` und `schwarzer Pfeffer` gehen verloren, wenn Adjektive vor dem Nachschlagen entfernt werden.

---

## 4. Was entfernt wird

### 4.1 Mengen und Einheiten
Zahlen, Brüche (`½`, `1/2`), Bereiche (`2–3`), und: `g, kg, mg, ml, l, TL, EL, Msp., Prise, Schuss, Spritzer, Handvoll, Bund, Zweig, Zehe, Stange, Scheibe, Blatt, Kopf, Knolle, Würfel, Packung, Päckchen, Dose, Glas, Flasche, Tüte, Becher, Tasse, St., Stück`

**Einheit/Lebensmittel-Kollisionen.** Mehrere Einheitswörter sind selbst Lebensmittel. Nur dann als Einheit behandeln, wenn `von`/`vom` folgt oder unmittelbar ein bekanntes Lebensmittel dahintersteht:
- `2 Zehen Knoblauch` → Einheit — aber `Gewürznelke` ist ein Lebensmittel
- `1 Stange Sellerie` → Einheit — aber `1 Zimtstange` → `Zimt [stange]`
- `2 Blatt Gelatine` → Einheit — aber `Lorbeerblatt` ist ein Lebensmittel
- `1 Würfel Hefe` → Einheit — aber `Brühwürfel` ist ein Lebensmittel

### 4.2 Zubereitungsangaben
`gehackt, fein gehackt, grob gehackt, gewürfelt, gewürfelt, in Scheiben, in Streifen, in Ringe, geschnitten, gerieben, fein gerieben, zerdrückt, gepresst, püriert, geschält, entkernt, entsteint, geputzt, halbiert, geviertelt, gekocht, abgekühlt, weich, geschmolzen, verquirlt, abgetropft, abgespült, zimmerwarm, nach Geschmack, zum Servieren, plus etwas mehr, zum Einfetten, zum Anbraten, zum Bestäuben, optional, geteilt`

### 4.3 Werbung und Herkunft
`hochwertig, bestes, reif, aus Freilandhaltung, Bio-, Bio, regional, saisonal, selbstgemacht, gekauft, übrig, Rest-`

Das Präfix `Bio-` ist besonders häufig und wird immer entfernt: `Bio-Zitrone` → `Zitrone`.

### 4.4 Adjektivendungen (deutsch-spezifisch, unverzichtbar)
Deutsche Adjektive werden dekliniert. Ohne diesen Schritt scheitert jede zweite Zuordnung.

Bei bekannten Adjektiv-Stämmen die Endung `-e, -er, -es, -em, -en` entfernen und auf den Stamm zurückführen:

| Im Rezept                                          | Stamm        |
| -------------------------------------------------- | ------------ |
| gemahlen, gemahlene, gemahlener, gemahlenem, gemahlenen | `gemahlen` |
| getrocknet, getrocknete, getrockneter, getrockneten | `getrocknet` |
| frisch, frische, frischer, frischem, frischen       | `frisch`     |
| geräuchert, geräucherte, geräucherter               | `geräuchert` |
| geröstet, geröstete, gerösteter                     | `geröstet`   |
| schwarz, schwarze, schwarzer, schwarzem, schwarzen  | `schwarz`    |
| sauer, saure, saurer, saurem *(Stammwechsel!)*      | `sauer`      |
| grün, grüne, grüner / rot, rote, roter              | `grün` / `rot` |

**Wichtig:** Das gilt in **beide** Richtungen. Ein gespeicherter Name wie `schwarzer Pfeffer` wird für die Suche ebenfalls zu `schwarz pfeffer` normalisiert, damit `schwarzem Pfeffer` und `schwarzen Pfeffer` darauf treffen. Gespeichert wird immer die **Nominativ-Singular-Form mit korrekter Endung**.

Achtung bei Stammwechsel: `sauer` → `saure` (nicht `sauere`), `dunkel` → `dunkle`, `edel` → `edle`.

### 4.5 Umlaute und ß
Für die Suche **beidseitig** falten, damit alle drei Schreibweisen kollidieren:

`ä ↔ ae ↔ a` · `ö ↔ oe ↔ o` · `ü ↔ ue ↔ u` · `ß ↔ ss`

`Möhre`, `Moehre` und `Mohre` müssen denselben Schlüssel ergeben. Die `ss`-Faltung deckt zugleich die Schweizer Schreibung ab (`Weisswein` → `Weißwein`).

Beim **Anlegen** wird zusätzlich die `ae/oe/ue/ss`-Variante als expliziter Alias gespeichert (§8.4) — die Faltung ist für die Suche, der Alias für Menschen und externe Systeme.

### 4.6 Singularisierung
Deutsche Plurale sind unregelmäßig — nie einfach `-s` abschneiden. Rückwärts über die Plural-Muster:

`-n/-en` (Tomaten → Tomate) · `-e` (Brote → Brot) · `-e` + Umlaut (Würste → Wurst) · nur Umlaut (Äpfel → Apfel) · `-er` + Umlaut (Eier → Ei, Kräuter → Kraut) · `-s` (Steaks → Steak)

**Pluraliatantum unangetastet lassen:** `Haferflocken`, `Semmelbrösel`, `Nudeln`, `Cornflakes`. Wenn die Singularisierung nichts trifft, der Plural aber schon, gewinnt der Plural.

### 4.7 Komposita-Kopf abtrennen (deutsch-spezifisch)
Deutsch verpackt die Einheit oft im Wort selbst: `Knoblauchzehe`, `Zwiebelwürfel`, `Salatkopf`, `Petersilienzweig`.

Nur unter **allen drei** Bedingungen abtrennen:
1. der volle String hat in Tier 0–2 nichts getroffen,
2. der Kopf steht auf der Whitelist: `-zehe, -kopf, -knolle, -zweig, -bund, -scheibe, -streifen, -würfel, -stück, -hälfte`,
3. der Rest trifft ein vorhandenes Lebensmittel.

Fugenelemente `-s-` und `-n-` beim Abtrennen mit entfernen: `Petersilienzweig` → `Petersilie`, `Rindsbraten` → `Rind`.

> **Gefahr:** `Eiweiß`, `Brühwürfel`, `Lorbeerblatt`, `Zimtstange`, `Vanilleschote` und `Sahnesteif` sehen wie Kompositum-plus-Einheit aus, sind aber eigene Lebensmittel. Deshalb Bedingung 1: der volle String wird immer zuerst nachgeschlagen.

---

## 5. Qualifikator-Extraktion

Diese Wörter werden **nicht** entfernt. Sie werden herausgelöst und zu Klammer-Qualifikatoren, weil sie bestimmen, welches Lebensmittel gemeint ist.

| Im String erkannt                              | Qualifikator     |
| ---------------------------------------------- | ---------------- |
| frisch                                         | `[frisch]`       |
| getrocknet, gedörrt                            | `[getrocknet]`   |
| ganz (bei Gewürzen)                            | `[ganz]`         |
| gemahlen, gemörsert, pulverisiert              | `[gemahlen]`     |
| Korn, Körner                                   | `[korn]`         |
| Flocken, zerstoßen (bei Chili)                 | `[flocken]`      |
| Stange, Stangen                                | `[stange]`       |
| Blatt, Blätter (bei Gelatine)                  | `[blatt]`        |
| Saft von, ausgepresst, frisch gepresst         | `[saft]`         |
| Abrieb von, abgerieben, Schale abgerieben      | `[abrieb]`       |
| Schale, Zesten                                 | `[schale]`       |
| aus der Dose, Dosen-, Konserven-               | `[dose]`         |
| tiefgekühlt, TK-, gefroren                     | `[tk]`           |
| eingelegt, in Essig, sauer eingelegt           | `[eingelegt]`    |
| geröstet                                       | `[geröstet]`     |
| geräuchert                                     | `[geräuchert]`   |

**Extraktionsregeln**

- **Nur ein Qualifikator.** Bei zwei Treffern den bestimmenden behalten, den anderen in die Rezeptnotiz. `fein abgeriebene Schale einer Bio-Zitrone` → `Zitrone [abrieb]`.
- **Genitiv- und `von`-Konstruktionen kehren die Reihenfolge um.** `Saft von 2 Zitronen`, `Abrieb einer Limette`, `die Schale einer Orange` — das Kopfnomen ist der *Qualifikator*, das Objekt ist die Basis. Von rechts nach links parsen.
- **Feste Produktnamen schlagen Qualifikatoren.** Vor der Behandlung von `geräuchert` als Qualifikator den ganzen String nachschlagen: `geräucherte Forelle`, `geräuchertes Paprikapulver` und `Räucherlachs` sind eigene Lebensmittel.
- **Pulver-Umleitung.** Wenn `[gemahlen]` extrahiert wurde, zusätzlich `<Basis>pulver` prüfen. `1 TL gemahlener Ingwer` → kein `Ingwer [gemahlen]` vorhanden → `Ingwerpulver` trifft. Das ist im Deutschen der **Regelfall**, nicht die Ausnahme: `Knoblauchpulver`, `Zwiebelpulver`, `Zimtpulver`, `Paprikapulver`, `Chilipulver`.
- **Kompositum-Umleitung.** `Pfefferkörner` → `schwarzer Pfeffer [korn]`; `Zimtstange` → `Zimt [stange]`; `Vanilleschote` bleibt eigenes Lebensmittel.

---

## 6. Matching-Kaskade

Tiers der Reihe nach. **Beim ersten Tier mit genau einem Treffer anhalten.**

| Tier | Prüfung                                                              | Aktion             |
| ---- | -------------------------------------------------------------------- | ------------------ |
| 0    | Roher String entspricht exakt `name`                                  | Verknüpfen         |
| 1    | Suchschlüssel entspricht normalisiertem `name` oder `pluralName`      | Verknüpfen         |
| 2    | Suchschlüssel entspricht einem normalisierten `alias`                 | Verknüpfen         |
| 3    | Basis + extrahierter Qualifikator trifft `Basis [qualifikator]`       | Verknüpfen         |
| 4    | Umleitungen: `<Basis>pulver`, Kompositum-Formen                       | Verknüpfen         |
| 5    | Basis trifft, aber zum Qualifikator existiert kein Eintrag            | siehe §6.1         |
| 6    | Komposita-Kopf abgetrennt (§4.7)                                      | Verknüpfen, sonst Review |
| 7    | Fuzzy: Levenshtein ≤ 2 bei Schlüsseln ab 6 Zeichen                    | **Nur vorschlagen** |
| 8    | Nichts                                                                | weiter zu §7       |

**Tier 7 nie automatisch akzeptieren.** Fuzzy-Treffer gehen in die Review-Queue. Automatisches Übernehmen führt `Korinthen`/`Koriander` und `Kümmel`/`Kreuzkümmel` still zusammen — zwei Paare, die sich um genau zwei bzw. drei Zeichen unterscheiden und völlig verschiedene Dinge sind.

**Mehr als ein Treffer in einem Tier ist eine Mehrdeutigkeit, keine Zuordnung** — ab in die Review (§12), nicht den ersten nehmen.

### 6.1 Basis trifft, Qualifikator fehlt
Häufigster realer Fall. Die Antwort hängt davon ab, ob der Qualifikator **trennend** ist.

- **Trennende Qualifikatoren** — `[frisch]`, `[getrocknet]`, `[ganz]`, `[gemahlen]`, `[saft]`, `[abrieb]`, `[schale]`, `[flocken]`, `[stange]`, `[blatt]`, `[korn]`: das Lebensmittel ist wirklich ein anderes. **Nicht** stillschweigend auf die Basis zurückfallen. Variante anlegen (§7) oder Review.
- **Nicht trennende Qualifikatoren** — `[dose]`, `[tk]`, `[eingelegt]`, `[geröstet]`, `[geräuchert]`: Lager- oder Bearbeitungszustände. Existiert keine Variante, mit der Basis verknüpfen und den Qualifikator als Rezeptnotiz behalten. Nur dann zum eigenen Lebensmittel machen, wenn sich die kulinarische Rolle tatsächlich unterscheidet.

### 6.2 Standardauflösung für nackte mehrdeutige Basen
Eine nackte Basis ohne Qualifikator ist kein Fehler — Rezepte schreiben ständig so. Mit einer festen Tabelle auflösen, statt jeden Fall in die Review zu schicken:

| Nackter String | Löst auf zu                     | Begründung                     |
| -------------- | ------------------------------- | ------------------------------ |
| Pfeffer        | `schwarzer Pfeffer [gemahlen]`  | Tafelpfeffer ist der Standard  |
| Salz           | `Salz`                          | Stoffname, keine Trennung      |
| Knoblauch      | `Knoblauch [frisch]`            | Frisch ist der Rezeptstandard  |
| Zwiebel        | `Zwiebel [frisch]`              | Frisch ist der Rezeptstandard  |
| Ingwer         | `Ingwer [frisch]`               | Frisch ist der Rezeptstandard  |
| Petersilie     | `Petersilie [frisch]`           | Frisch ist der Kräuterstandard |
| Oregano        | `Oregano [getrocknet]`          | Bei diesem Kraut Standard      |
| Zimt           | `Zimtpulver`                    | Backstandard                   |
| Milch          | `Vollmilch`                     | Hausstandard                   |
| Mehl           | `Weizenmehl Type 405`           | Hausstandard                   |
| Sahne          | `Schlagsahne`                   | Hausstandard                   |
| Brühe          | *Review*                        | Wirklich nicht auflösbar       |

Diese Tabelle gehört in die Datenbank, nicht in jemandes Kopf, und wird erweitert, sobald dieselbe nackte Basis zweimal in der Review landet.

---

## 7. Soll es existieren? (das Anlege-Gate)

Nur erreicht, wenn die Kaskade nichts geliefert hat. Drei Fragen, in dieser Reihenfolge.

### 7.1 Ist es überhaupt ein Lebensmittel?
**Ja** — Grundzutaten, Halbfabrikate, die als Zutat dienen (Mehl, Nudeln, Brühe, Saucen), Würzmittel, und vorverarbeitete Produkte, die man als Basis kauft (geräucherte Makrele, Hähnchenschnitzel, Gyrosstreifen).

**Nein — nicht anlegen:**

| Der String ist…                        | Beispiel                              | Stattdessen                                        |
| -------------------------------------- | ------------------------------------- | -------------------------------------------------- |
| Eine Marke                             | Rama, Nutella, Miracel Whip, Fondor   | Auf das Generikum abbilden (`Margarine`, `Nuss-Nougat-Creme`, `Salatmayonnaise`, `Würzmittel`); Marke nur dann als Alias, wenn sie umgangssprachlich generisch ist |
| Eine selbst hergestellte Zubereitung   | Kartoffelpüree, selbstgemachtes Pesto, Teig | Auf die Komponenten verknüpfen oder als Unterrezept markieren |
| Ein fertiges Gericht                   | Parfait, Sorbet, Petit Four           | Markieren — ein Gericht ist kein Lebensmittel       |
| Ein Rest oder Zustand eines Gerichts   | Reste vom Braten, abgekühlte Nudeln   | Auf das Basis-Lebensmittel, Zustand in die Notiz    |
| Zu generisch zum Einkaufen             | Saft, Teig, Fleisch, Käse (ohne Näheres) | Review — das Rezept fragen, nicht raten           |
| Eine Mischung, die eine Anweisung ist  | „Pastagewürz (Oregano, Basilikum, Thymian)" | In die genannten Komponenten aufteilen         |

> **Ausnahme:** Wenn man es **als ein Produkt kauft** *und* es einen **festen, gängigen Produktnamen** hat, der als eine Rezeptzeile auftaucht, darf es angelegt werden: `Italienische Kräuter`, `Kräuter der Provence`, `Lebkuchengewürz`, `Garam Masala`, `Fünf-Gewürze-Pulver`. Schwankungen zwischen Marken sind akzeptabel, solange die kulinarische Rolle gleich bleibt.

### 7.2 Gibt es einen Beinahe-Treffer?
Wenn Tier 7 irgendeinen Fuzzy-Kandidaten geliefert hat: **nicht anlegen**, ab in die Review. Das ist die wichtigste Schutzregel des ganzen Dokuments. Duplikate entstehen fast immer genau hier.

### 7.3 Ist es gängig genug für einen eigenen Datensatz?
Konservativ bleiben. Eine einmalige exotische Zutat aus einem einzelnen Rezept darf in der Review liegen bleiben, bis sie ein zweites Mal auftaucht. **Im echten Zweifel lieber ein eigenes Lebensmittel anlegen als übermäßig zusammenführen** — ein überflüssiger Eintrag lässt sich per Merge reparieren, eine falsche Zusammenführung beschädigt still jedes Rezept auf beiden Seiten.

---

## 8. Das Lebensmittel anlegen

Erst jetzt greifen die Benennungsregeln.

### 8.1 `name`
- Gängiger deutscher Name, **Singular**, **korrekt großgeschrieben**
- Keine Markennamen
- Etablierte Lehnwörter bleiben: `Tahini`, `Miso`, `Gochujang`, `Crème fraîche`, `Ketchup`

**Groß-/Kleinschreibung (deutsch-spezifisch):**
- Substantive groß: `Tomate`, `Zwiebel`, `Knoblauchpulver`
- Bei mehrteiligen Namen nur das Substantiv groß, das Adjektiv klein: `schwarzer Pfeffer`, `saure Sahne`, `grüner Spargel`
- Adjektive im **Nominativ Singular** mit korrekter Endung speichern — die Suche normalisiert die Endung ohnehin weg (§4.4)
- **Qualifikatoren in Klammern bleiben immer klein**, auch substantivische: `Zimt [stange]`, `Zitrone [saft]`. Sie sind technische Tags, kein Fließtext.

### 8.2 Qualifikatoren
`Basisname [qualifikator]`, kleingeschrieben, ein Wort, **maximal einer pro Name**. Whitelist wie in §5.

**Deutsch-spezifische Ausnahme 1 — Komposita statt Klammern.** Wenn „X-pulver" der gängige Produktname ist, ist **das** der `name`, nicht `X [gemahlen]`: `Knoblauchpulver`, `Zwiebelpulver`, `Ingwerpulver`, `Zimtpulver`, `Paprikapulver`, `Chilipulver`, `Currypulver`, `Backpulver`, `Kakaopulver`, `Senfpulver`. Nie mit Bindestrich oder Leerzeichen als `name` — das sind Aliasse.

**Deutsch-spezifische Ausnahme 2 — feste Wörter schlagen Klammern.** Wo es ein eigenes Wort gibt, das Wort nehmen: `Lorbeerblatt`, `Semmelbrösel`, `Haferflocken`, `Puderzucker`, `Speisestärke`, `Vanilleschote`, `Tomatenmark`.

**Keine Klammern**, wenn der Produktname ein festes Kompositum ist, das keine Form/Zustand-Angabe ist: `Hähnchenbrust`, `Hähnchenschenkel`, `Eigelb`, `Eiweiß`, `Hüttenkäse`, `Schlagsahne`, `Frühstücksspeck`.

### 8.3 `pluralName`
Nie `+s` raten. Mustertabelle:

| Muster            | Beispiel                            |
| ----------------- | ----------------------------------- |
| `-n` / `-en`      | Tomate → Tomaten, Bohne → Bohnen    |
| `-e`              | Brot → Brote                        |
| `-e` + Umlaut     | Wurst → Würste, Nuss → Nüsse        |
| nur Umlaut        | Apfel → Äpfel                       |
| `-er` + Umlaut    | Ei → Eier, Kraut → Kräuter          |
| `-s`              | Steak → Steaks, Avocado → Avocados  |

- **Stoffnamen:** `pluralName == name` (`Reis`, `Salz`, `Mehl`, `Butter`, `Zucker`, `Milch`, `Oregano`)
- **Pluraliatantum:** `pluralName == name` (`Haferflocken`, `Semmelbrösel`, `Nudeln`)
- Klammer-Varianten pluralisieren den zählbaren Teil: `Zimt [stange]` → `Zimt [stangen]`, `schwarzer Pfeffer [korn]` → `schwarzer Pfeffer [körner]`, `Zitrone [saft]` bleibt unverändert

### 8.4 Aliasse sofort befüllen
Ein neues Lebensmittel mit `"aliases": []` verfehlt das nächste Rezept, das es anders schreibt. Beim Anlegen ergänzen:

1. **Den String, der das Anlegen ausgelöst hat**, sofern legitime Variante
2. **Umlaut-/ß-Ersatzschreibung**: `Moehre`, `Kaese`, `Weisswein`, `Gruenkohl`
3. **AT/CH-Varianten**: `Erdapfel`, `Paradeiser`, `Obers`, `Faschiertes`, `Melanzani`
4. **Regionale DE-Varianten**: `Karotte`, `Mohrrübe`, `Blaukraut`
5. **Bindestrich-/Leerzeichen-Varianten**: `Knoblauch-Pulver`, `Knoblauch Pulver`
6. **Kleinschreibung**, wenn Rezepte so schreiben: `knoblauchpulver`

### 8.5 Nie ein Alias — immer ein eigenes Lebensmittel
- Sorten: `Boskoop`, `Braeburn`, `Sieglinde`, `Bamberger Hörnchen`
- Abgeleitete Formen: `Zitrone [saft]` ≠ `Zitrone`; `Limette [abrieb]` ≠ `Limette`
- Andere Produkte: Korinthen ≠ Rosinen; `Speisestärke` ≠ `Maismehl`; `Natron` ≠ `Backpulver`
- Zubereitungen: Espresso ≠ Kaffee; Pulled Pork ≠ Schweineschulter
- Echt verschiedene Produkte: `Büffelmozzarella` ≠ `Mozzarella`; `Schlagsahne` ≠ `saure Sahne`; `Schmand` ≠ `Crème fraîche`
- Frisch vs. getrocknet, wenn beide existieren

### 8.6 Benennungsbeispiele
| ❌ Falsch          | ✅ Richtig                    |
| ----------------- | ---------------------------- |
| Rama              | Margarine                    |
| Nutella           | Nuss-Nougat-Creme            |
| Erdapfel          | Kartoffel (Alias: Erdapfel)  |
| Paradeiser        | Tomate (Alias: Paradeiser)   |
| Topfen            | Quark (Alias: Topfen)        |
| maple syrup       | Ahornsirup                   |
| cottage cheese    | Hüttenkäse                   |
| nutritional yeast | Edelhefeflocken              |
| baking soda       | Natron                       |

---

## 9. Labels (beim Anlegen vergeben)

### 9.1 Prinzipien
1. Danach labeln, **was es IST**, nicht nach Herkunft oder Verwendung — Fischfond → Brühe & Geschmacksgeber, Austernsauce → Saucen & Würzmittel
2. Käse immer getrennt von Milchprodukten
3. Süßwaren & Aufstriche = süße Produkte inklusive süßer Brotaufstrich
4. Wurst & Aufschnitt = verarbeitetes Fleisch, auch streichfähig

### 9.2 Häufige Fehler
| Zutat             | ❌ Falsch                 | ✅ Richtig                 |
| ----------------- | ------------------------ | ------------------------- |
| Austernsauce      | Fisch & Meeresfrüchte    | Saucen & Würzmittel       |
| Fischfond         | Fisch & Meeresfrüchte    | Brühe & Geschmacksgeber   |
| Mozzarella        | Milchprodukte            | Käse                      |
| Cappuccinopulver  | Milchprodukte            | Kaffee & Tee              |
| Haferflocken      | Nüsse & Samen            | Frühstückscerealien       |
| Buchweizen        | Backzutaten              | Nudeln & Reis             |
| Rosinen           | Süßwaren & Aufstriche    | Obst                      |
| Tofu              | Milchprodukte            | Hülsenfrüchte             |
| Erdnussbutter     | Nüsse & Samen            | Süßwaren & Aufstriche     |
| Mett              | Fleisch                  | Wurst & Aufschnitt        |
| Tzatziki          | Milchprodukte            | Saucen & Würzmittel       |
| Hummus            | Hülsenfrüchte            | Saucen & Würzmittel       |
| Marmelade         | Saucen & Würzmittel      | Süßwaren & Aufstriche     |
| Honig             | Backzutaten              | Süßwaren & Aufstriche     |
| Leberwurst        | Fleisch                  | Wurst & Aufschnitt        |
| Kokosmilch        | Sonstiges                | Milchprodukte             |

### 9.3 Die 29 Labels
| #  | Label                    | Beispiele                                        |
| -- | ------------------------ | ------------------------------------------------ |
| 1  | Gemüse                   | Tomate, Zwiebel, Möhre, Jalapeño                 |
| 2  | Obst                     | Apfel, Banane, Rosinen                           |
| 3  | Frische Kräuter          | Basilikum, Petersilie, Zitronengras              |
| 4  | Kartoffeln & Knollen     | Kartoffel, Sellerie, Radieschen                  |
| 5  | Fleisch                  | Rinderfilet, Hackfleisch, Schweinefilet          |
| 6  | Geflügel                 | Hähnchen, Hähnchenbrust, Ente, Pute              |
| 7  | Fisch & Meeresfrüchte    | Lachs, Garnele, Miesmuschel, Nori                |
| 8  | Wurst & Aufschnitt       | Schinken, Speck, Salami, Leberwurst              |
| 9  | Milchprodukte            | Milch, Joghurt, Sahne, Kokosmilch                |
| 10 | Käse                     | Emmentaler, Mozzarella, Bergkäse, Frischkäse     |
| 11 | Eier                     | Ei, Eigelb, Eiweiß                               |
| 12 | Brot & Gebäck            | Brot, Croissant, Tortilla                        |
| 13 | Backzutaten              | Mehl, Zucker, Backpulver, Hefe                   |
| 14 | Frühstückscerealien      | Haferflocken, Müsli, Cornflakes                  |
| 15 | Nudeln & Reis            | Spaghetti, Reis, Ramen, Udon                     |
| 16 | Hülsenfrüchte            | Kichererbse, Linsen, Tofu                        |
| 17 | Nüsse & Samen            | Mandel, Walnuss, Sesam                           |
| 18 | Kräuter & Gewürze        | Zimt, Muskatnuss, Paprikapulver                  |
| 19 | Öl, Essig & Fett         | Olivenöl, Balsamico, Butterschmalz               |
| 20 | Saucen & Würzmittel      | Ketchup, Sojasauce, Ajvar, Pesto, Mayonnaise     |
| 21 | Brühe & Geschmacksgeber  | Hühnerbrühe, Fischfond, Brühwürfel               |
| 22 | Snacks                   | Chips, Salzstangen, Erdnussflips                 |
| 23 | Süßwaren & Aufstriche    | Schokolade, Bonbons, Marmelade, Honig            |
| 24 | Getränke                 | Cola, Orangensaft, Tonic                         |
| 25 | Wein                     | Rotwein, Sherry, Portwein                        |
| 26 | Bier                     | Pils, Weizenbier, IPA                            |
| 27 | Spirituosen & Liköre     | Rum, Whisky, Cointreau                           |
| 28 | Kaffee & Tee             | Kaffee, grüner Tee, Rooibos                      |
| 29 | Sonstiges                | Nicht einzuordnen                                |

---

## 10. Beschreibungen

**Format:** `[Kurze Definition]; [Verwendung/Zubereitung].` — **maximal 120 Zeichen** (20 mehr als in anderen Sprachfassungen, weil deutsche Komposita länger sind), ein Merkmal plus eine typische Anwendung, keine Werbesprache.

- Dunkle Sauce aus Austernextrakt; herzhafter Würzstoff in der asiatischen Küche.
- Fetter Fisch; vielseitig zuzubereiten.
- Gewürzmischung für Cajun-Gerichte; scharf, mit Paprika und Cayenne.

---

## 11. Rückkopplung

Das Matching wird nur besser, wenn Auflösungen zurückgeschrieben werden. Nach **jeder** manuellen Auflösung:

- Auf ein vorhandenes Lebensmittel aufgelöst und der String war echtes Synonym oder Schreibvariante → **als Alias ergänzen**
- Auf ein vorhandenes Lebensmittel aufgelöst, aber der String war eine abgeleitete Form (`Zitronensaft` → `Zitrone`) → **kein Alias**; entweder fehlt die Varianten-Entität oder der Parse war falsch
- Zweimal dieselbe nackte Basis → **Zeile in die Tabelle §6.2 aufnehmen**
- Ein Wort musste von Hand entfernt werden → **in §4 aufnehmen**
- Eine Adjektivform wurde nicht erkannt → **in §4.4 aufnehmen** (unregelmäßige Stämme wie `sauer`, `dunkel`, `edel` sind hier die üblichen Verdächtigen)

Eine Auflösung, die keine Regel verändert, kommt nächste Woche wieder.

---

## 12. Mehrdeutigkeit und Review

In die Review statt zu raten, wenn:
- zwei oder mehr Lebensmittel im selben Tier treffen
- ein trennender Qualifikator extrahiert wurde, aber keine passende Variante existiert
- ein Fuzzy-Kandidat existiert (Tier 7) — immer
- der String nach einem Gericht, einer Marke oder einer Anweisung aussieht
- der String nach dem Strippen leer ist (der Parser hat das Lebensmittel gefressen — meist eine Einheit/Lebensmittel-Kollision, §4.1)

Review-Einträge tragen: die rohe Rezeptzeile, den Suchschlüssel, das erreichte Tier und alle geprüften Kandidaten. Ohne die rohe Zeile kann niemand einen Parser-Bug von einem fehlenden Lebensmittel unterscheiden.

---

## 13. Durchgerechnete Beispiele

| Rezeptzeile                                | Suchschlüssel        | Weg                                    | Ergebnis                        |
| ------------------------------------------ | -------------------- | -------------------------------------- | ------------------------------- |
| `2 EL frisch gehackter Koriander`          | `frisch koriander`   | Zubereitung weg → `[frisch]` extrahiert | `Koriander [frisch]`            |
| `Saft von 2 Zitronen`                      | `zitrone saft`       | `von`-Konstruktion umgedreht           | `Zitrone [saft]`                |
| `1 Dose gehackte Tomaten (400 g)`          | `tomate`             | `[dose]` extrahiert, Tier 3            | `Tomate [dose]`                 |
| `1 TL gemahlener Ingwer`                   | `ingwer`             | `[gemahlen]` → Pulver-Umleitung        | `Ingwerpulver`                  |
| `2 Knoblauchzehen, gepresst`               | `knoblauch`          | `Zehe` = Einheit → §6.2                | `Knoblauch [frisch]`            |
| `Salz und Pfeffer nach Geschmack`          | `salz` / `pfeffer`   | getrennt → §6.2                        | `Salz` + `schwarzer Pfeffer [gemahlen]` |
| `mit schwarzem Pfeffer würzen`             | `schwarz pfeffer`    | Adjektivendung normalisiert (§4.4)     | `schwarzer Pfeffer [gemahlen]`  |
| `1 Bio-Zitrone, Schale fein abgerieben`    | `zitrone abrieb`     | `Bio-` weg, `[abrieb]` extrahiert      | `Zitrone [abrieb]`              |
| `200 g Reste vom Hähnchen`                 | `hähnchen`           | Rest eines Gerichts                    | `Hähnchen` + Notiz              |
| `1 Bund Petersilienzweige`                 | `petersilie`         | Kompositum-Kopf + Fugen-n (§4.7)       | `Petersilie [frisch]`           |
| `50 g Korinthen`                           | `korinthen`          | Fuzzy-Treffer auf `Koriander`          | **Review** — keine Zuordnung    |

Die letzte Zeile ist der ganze Sinn dieses Dokuments. `Korinthen` und `Koriander` unterscheiden sich um zwei Zeichen, beide sind reale Wörter, und ein automatisch akzeptierter Fuzzy-Treffer läge hier zuverlässig falsch.

---

## 14. Checklisten

**Parsen**
- [ ] Wurde der rohe String vor jedem Strippen geprüft?
- [ ] Wurden mehrere Lebensmittel in einer Zeile getrennt?
- [ ] Wurden Adjektivendungen normalisiert (§4.4)?
- [ ] Wurden Umlaute und ß beidseitig gefaltet (§4.5)?
- [ ] Wurden Qualifikatoren extrahiert statt entfernt?
- [ ] Ist die Pulver-Umleitung gelaufen?
- [ ] Wurde ein Komposita-Kopf nur unter allen drei Bedingungen abgetrennt?
- [ ] Wurde eine nackte Basis aus der Standardtabelle aufgelöst, nicht geraten?
- [ ] Ging jeder Fuzzy-Treffer in die Review statt akzeptiert zu werden?

**Anlegen**
- [ ] Hat die volle Kaskade wirklich nichts geliefert?
- [ ] Ist es ein Lebensmittel — keine Marke, kein Gericht, keine Zubereitung, keine Anweisung?
- [ ] Gab es einen Beinahe-Treffer? (wenn ja: Review, nicht anlegen)
- [ ] Ist `name` gängiges Deutsch, Singular, korrekt großgeschrieben, bundesdeutsche Variante?
- [ ] Wurde das Kompositum (`Knoblauchpulver`) statt einer erfundenen Klammerform verwendet?
- [ ] Ist `pluralName` der echte deutsche Plural (nicht `+s` geraten)?
- [ ] Sind Aliasse befüllt — inklusive Umlaut-Ersatzschreibung und dem auslösenden String?
- [ ] Stammt das Label aus der festen Liste?
- [ ] Ist `description` im festen Format und unter 120 Zeichen?
