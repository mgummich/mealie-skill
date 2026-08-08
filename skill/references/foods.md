# Lebensmittel und Einheiten

Gilt für `foods` und `units` gleichermaßen - beide haben einen echten
Merge-Endpunkt. Zwei Aufgaben, nie im selben Plan:
**Lücken füllen** ist harmlos, **Dubletten zusammenführen** ist destruktiv.

## Phase 1 - Analyse

    audit foods          # oder: audit units

Gib wieder: Anzahl gesamt, Verteilung der Lücken, ungenutzte Einträge,
Dublettengruppen mit Rezeptzahlen. Frage dann, womit begonnen werden soll.

Der Dublettenverdacht ist eine grobe Normalform-Heuristik. Sie findet
Tomate/Tomaten und Kürbis/Kuerbis, aber nicht Ei/Eier oder
Frühlingszwiebel/Lauchzwiebel. Prüfe die Gruppen inhaltlich und ergänze
Paare, die die Heuristik übersieht.

## Phase 2a - Lücken füllen

    ctx foods --limit 25

Plan als Tabelle `Food | fehlt | Ergänzung`. Nur fehlende Felder ergänzen,
bestehende Werte nie überschreiben.

- `name`: Singular, allgemeinsprachlich ("Kichererbse", nicht "Kichererbsen
  aus der Dose"). Stimmt der Name nicht, im Plan ausweisen und korrigieren.
- `pluralName`: korrekte deutsche Pluralform.
- `description`: 2-4 Sätze wikiartig - was es ist, Herkunft/Sorte,
  kulinarische Verwendung, Lagerung oder gängiger Ersatz. Sachlich, keine
  Ich-Form, keine Werbesprache, keine Mengenangaben.
- `labelId`: passendes Label aus dem gelieferten Bestand. Fehlt eines, anlegen
  (Name + Hex-Farbe), orientiert an Supermarkt-Abteilungen: Obst & Gemüse,
  Fleisch & Fisch, Molkereiprodukte, Trockenwaren & Backen, Konserven &
  Gläser, Gewürze & Kräuter, Öle & Essige, Tiefkühl, Getränke, Sonstiges.
- `aliases`: Synonyme, regionale Bezeichnungen, Schreibvarianten ohne Umlaut
  und die englische Bezeichnung.

Bei Einheiten stattdessen `name`, `pluralName`, `abbreviation`,
<!-- nur-agent -->
`useAbbreviation`. Einheiten haben kein Label und keine Beschreibung; das
Werkzeug meldet dort nur Plural, Aliase und Abkürzung als Lücke.
<!-- standalone: `useAbbreviation`. Kein Label. -->

## Phase 2b - Dubletten zusammenführen

    ctx foods --group "Tomate"

Zielobjekt ist das Food mit den meisten Rezeptverwendungen; bei Gleichstand
das inhaltlich bessere (Beschreibung, Label, Plural gesetzt). Stimmt dessen
Name nicht, erst per `update_food` korrigieren, dann mergen.

Plan je Gruppe:

    Gruppe: Tomate
      BEHALTEN  Tomate (3f2a…) – 14 Rezepte, Label gesetzt
      MERGEN    Tomaten (91bc…) – 2 Rezepte  -> wird zu Alias
      MERGEN    tomato (55de…) – 0 Rezepte   -> wird zu Alias
      DANACH    update_food: aliases += Tomaten, tomato, tomatoes

Der Merge schreibt die betroffenen Rezepte um und löscht das Quell-Food.
Nicht rückgängig zu machen - im Plan ausdrücklich nennen, mit Rezeptzahl.

Nach jedem Merge die Namen der gelöschten Objekte als `aliases` an das Ziel
hängen, sonst entsteht dieselbe Dublette beim nächsten Import.

**Nicht zusammenführen** bei sachlichem Unterschied trotz ähnlichem Namen:
Tomate/Cherrytomate, Milch/Buttermilch, Zucker/Puderzucker, Paprika
(Gemüse)/Paprikapulver, Zwiebel/Frühlingszwiebel, EL/TL. Im Zweifel
offenlassen und unter RÜCKFRAGEN aufführen.

## Ungenutzte Einträge

`audit` listet Foods und Einheiten ohne Rezeptverwendung. Die sind meist
harmlos (Reste alter Importe), aber gute Merge-Quellen: Ein ungenutztes
Duplikat lässt sich ohne Rezeptänderung entfernen. Nicht ungefragt löschen -
vorschlagen und begründen.

## Phase 3 - Ausführung

    apply actions.json

Report: AKTUALISIERT (Objekt - welche Felder) · ZUSAMMENGEFÜHRT
(von -> nach, Anzahl umgeschriebener Rezepte) · ALIASE ERGÄNZT · OFFEN
(bewusst nicht zusammengeführt, mit Begründung).

Pakete klein halten: höchstens 25 Lücken oder 5 Dublettengruppen pro Lauf.
