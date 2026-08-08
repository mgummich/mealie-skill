---
description: Mealie pflegen - Rezepte, Lebensmittel, Kategorien/Tags/Utensilien, Kochbuecher, Wartung. Fragt nach dem Modus und arbeitet in drei Phasen mit Freigabe.
---

# Mealie pflegen

Optionales Argument: der Modus (`rezept <slug>`, `lebensmittel`, `einheiten`,
`organizer`, `kochbuch`, `wartung`). Fehlt es, frage nach.

Halte dich an den Skill `mealie`. Lies **nur** die Referenz zum gewaehlten
Modus, nicht alle.

Ist der Skill `caveman` verfuegbar, aktiviere ihn jetzt fuer Analyse, Plan
und Report. Nicht fuer Inhalte, die nach Mealie geschrieben werden, und
nicht fuer Warnungen und Rueckfragen - Abgrenzung siehe SKILL.md.

## Schritt 1 - Modus und Referenz

    rezept        -> references/recipes.md
    lebensmittel  -> references/foods.md
    einheiten     -> references/foods.md
    organizer     -> references/organizers.md
    kochbuch      -> references/cookbooks.md
    wartung       -> references/maintenance.md

Alle Skriptaufrufe mit dem Praefix:

    python .agents/skills/mealie/scripts/mealie_ctx.py

Lies nur die Ausgaben, nicht den Quelltext des Skripts.

## Schritt 2 - Analyse

Fuehre den `audit`- oder `ctx`-Befehl aus der Referenz aus und gib das
Ergebnis zusammengefasst wieder. Beim ersten Aufruf baut das Skript den
Rezeptindex - das dauert einmalig.

Frage danach, welche Teilaufgabe und welche Paketgroesse. Nie zwei
Aufgabenarten in einem Plan.

## Schritt 3 - Plan vorlegen und anhalten

Plan als Artefakt in der Struktur der Referenz. Aktionen nach `actions.json`
im Workspace-Root, Format siehe `references/actions.md`.

Pruefen mit:

    ... apply actions.json --dry-run

Destruktive Operationen (merge, delete, retag) im Plan kennzeichnen, mit
Zahl der betroffenen Rezepte. Danach ausdruecklich nach Freigabe fragen und
**anhalten**. Bei Korrekturwuenschen Plan und `actions.json` anpassen,
erneut vorlegen.

## Schritt 4 - Ausfuehrung

Nur nach Freigabe:

    ... apply actions.json                # ohne Rezeptbezug
    ... apply actions.json --slug <slug>  # Rezeptmodus

Bricht das Skript ab, keine Reparaturversuche auf Verdacht - erreichten
Zustand melden und nachfragen.

## Schritt 5 - Report

Report in der Struktur der Referenz ausgeben, `actions.json` loeschen und
fragen, ob das naechste Paket folgen soll.
