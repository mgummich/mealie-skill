---
name: mealie
description: Pflegt eine Mealie-Instanz. Rezepte optimieren (leere Felder fuellen, Zutaten gegen den Food-Bestand parsen, Schritte uebersetzen, metrisch umrechnen, Bild setzen), Lebensmittel und Einheiten aufraeumen (Beschreibung, Plural, Label, Aliase, Dubletten zusammenfuehren), Kategorien/Tags/Utensilien konsolidieren, Kochbuecher anlegen, doppelte Rezepte und tote Links finden, Diaet-Tags aus Zutaten ableiten. Verwenden bei Mealie, Rezeptdatenbank, Zutaten parsen, Foods, Dubletten, Kochbuch, Schlagworten.
---

# Mealie-Pflege

Immer drei Phasen: **ANALYSE -> PLAN -> AUSFÜHRUNG**.
Ohne ausdrückliche Freigabe des Plans wird nichts geschrieben.
Nie zwei Aufgabenarten in einem Plan mischen.

## Modus wählen und passende Referenz lesen

Lies **nur** die Referenz zum aktuellen Modus, nicht alle:

| Anliegen | Referenz |
|---|---|
| Rezept aufräumen, Zutaten parsen, Felder füllen | `references/recipes.md` |
| Lebensmittel oder Einheiten: Lücken, Dubletten | `references/foods.md` |
| Kategorien, Tags, Utensilien konsolidieren | `references/organizers.md` |
| Kochbuch anlegen oder überarbeiten | `references/cookbooks.md` |
| Doppelte Rezepte, tote Bilder/Quell-URLs, Diät-Tags | `references/maintenance.md` |

Das ACTIONS-Format ist für alle Modi gleich: `references/actions.md`.
Diese Datei erst lesen, wenn Phase 2 ansteht.

## Werkzeug

`scripts/mealie_ctx.py` kapselt alle API-Zugriffe. Nicht den Quelltext lesen,
sondern mit `--help` aufrufen.

    index [--refresh]                  lokalen Rezeptindex bauen
    audit <was> [--limit N]            foods units categories tags tools
                                       recipes links
    ctx recipe <slug> [--search B]     Rezept + passende Foods + Organizer
    ctx <was> [--limit N] [--group G]  foods units categories tags tools
                                       cookbooks diet
    usage <art> <id>                   Rezepte zu food/unit/category/tag/tool
    apply <datei> [--slug S] [--dry-run]

Der erste `audit`-Aufruf baut den Index (ein Durchlauf über alle Rezepte,
dauert je nach Bestand eine Weile). Alle weiteren Audits lesen daraus.
Nach jedem schreibenden `apply` wird der Index verworfen und neu gebaut.

Kontextbefehle liefern bereits gefiltert. Vollständige Tabellen nie
ungefiltert laden, keine Rezeptschleifen von Hand bauen - dafür ist der
Index da.

Umgebungsvariablen: `MEALIE_URL`, `MEALIE_TOKEN`.

## Ausgabestil: caveman

Ist der Skill `caveman` verfügbar, aktiviere ihn für diesen Ablauf. Audits,
Pläne und Reports sind lange, tabellarische Ausgaben - genau der Fall, in dem
Kompression trägt.

**Nur die Chat-Ausgabe wird komprimiert.** Alles, was in Mealie landet oder
dort gelesen wird, bleibt normale deutsche Prosa in voller Qualität:

| komprimiert | volle Prosa |
|---|---|
| Analysetabelle, Statuszeilen | `description` von Rezepten und Foods |
| Plan (A–H, Gruppenlisten) | Zubereitungsschritte |
| Report am Ende | Notizen, Kochbuchbeschreibungen |
| deine Zwischenkommentare | alles in `actions.json` |

Der Grund: `actions.json` ist kein Chat, sondern Datenbankinhalt. Eine
Food-Beschreibung im Caveman-Stil steht dauerhaft in der Instanz und wird von
Menschen gelesen, die nichts von diesem Ablauf wissen.

**Warnungen bleiben vollständig.** Hinweise auf destruktive Operationen,
Rückfragen bei Unsicherheit und die Freigabefrage in ganzen Sätzen -
caveman hat dafür eine eigene Klarheitsregel. Bei einem Merge, der 14
Rezepte umschreibt, ist Eindeutigkeit mehr wert als ein paar gesparte Tokens.

Ohne den Skill: normal antworten, aber knapp - Tabellen statt Fließtext,
keine Wiederholung dessen, was das Werkzeug schon ausgegeben hat.

## Regeln für alle Modi

Nichts erfinden: Zutaten, Mengen und Schritte werden nur strukturiert,
übersetzt und korrigiert, nie ergänzt oder weggelassen. Vorhandene korrekte
Werte bleiben.

Alles Deutsch; etablierte Fachbegriffe (Sous-vide, Roux, Ganache) bleiben.
Metrische Einheiten.

Geschätztes im Report markieren. Im Zweifel Feld leer lassen statt raten.

Erst suchen, dann anlegen - bei Foods, Einheiten und Organizern gleichermaßen.
Auch Schreibvarianten, Singular/Plural und fremdsprachige Entsprechungen
prüfen.

Destruktive Operationen (`merge_*`, `delete_organizer`, `retag_recipe`)
im Plan ausdrücklich kennzeichnen, mit Zahl der betroffenen Rezepte, und
darauf hinweisen, dass sie nicht rückgängig zu machen sind.

Pakete klein halten: höchstens 25 Lücken oder 5 Dubletten-/Organizer-Gruppen
pro Lauf.

Bei Abbruch keine Reparaturversuche auf Verdacht - erreichten Zustand melden
und nachfragen.
