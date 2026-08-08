# Mealie-Pflege — Projektregeln

Werkzeug zum Aufräumen einer Mealie-Instanz über deren REST-API. Zwei
Frontends, eine gemeinsame Logik: ein Antigravity-Skill und ein
Standalone-Skript für die Anthropic API.

## Architektur

    antigravity/skills/mealie/
      SKILL.md              Router: Modus wählen, gemeinsame Regeln
      references/*.md       Details je Modus, nur bei Bedarf gelesen
      scripts/mealie_ctx.py ALLE API-Zugriffe, kein Modellaufruf
    antigravity/workflows/mealie.md
    standalone/
      prompts/common.txt    Grundsätze + ACTIONS-Format
      prompts/<modus>.txt   aus references/ abgeleitet
      optimize.py           Modellaufruf, Freigabe, Batch

`mealie_ctx.py` ist die einzige Stelle mit HTTP-Zugriff auf Mealie.
`optimize.py` ruft es als Subprozess auf. Neue Funktionalität gehört ins
Skript, nicht in die Prompts.

## Nicht verhandelbar

**Drei Phasen: ANALYSE -> PLAN -> AUSFÜHRUNG.** Nie schreiben, ohne dass ein
Plan vorlag und freigegeben wurde. Das gilt auch für dich als Agent: Bei
Änderungen am Werkzeug erst zeigen, was passieren würde.

**Die Ausführungsreihenfolge in `ORDER` ist erzwungen** und bricht vor dem
ersten Schreibzugriff ab. Reihenfolge ändern heißt: `references/actions.md`
und `prompts/common.txt` mitziehen, sonst schlagen die Pläne des Modells
gegen den Guard.

**Kein Rezeptlöschen.** Es gibt bewusst keine Operation dafür. Doppelte
Rezepte werden vorgelegt, gelöscht wird von Hand in der Oberfläche.

**`actions.json` ist Datenbankinhalt, kein Chat.** Beschreibungen, Schritte,
Notizen und Kochbuchtexte immer in vollständiger deutscher Prosa, auch wenn
der Ausgabestil komprimiert ist (caveman). Diese Regel steht in `SKILL.md`
und in `references/actions.md` — beide anpassen, wenn sie sich ändert.

**Regeln stehen an einer Stelle.** `standalone/prompts/*.txt` sind aus
`references/*.md` abgeleitet. Änderst du eine Regel, ändere die Referenz und
leite neu ab (siehe HANDOFF.md, Abschnitt „Prompts neu ableiten").

## Konventionen

Deutsch in allen Ausgaben, Prompts und Kommentaren. Umlaute in
Python-Docstrings und `--help` vermeiden (ae/oe/ue), in Markdown und
Modellausgaben verwenden.

Zeilenlänge 88, keine externen Abhängigkeiten außer `requests`.

Neue Operationen brauchen: Eintrag in `ORDER`, Zweig in `cmd_apply`, Zeile in
der Tabelle in `references/actions.md`, Test im Dry-Run.

Neue Audits schreiben nichts und lesen aus dem Index, nicht per Einzelabruf.

## Index

`.mealie_index.json` im Arbeitsverzeichnis, gebaut beim ersten `audit`, nach
jedem schreibenden `apply` gelöscht. Ein Durchlauf über alle Rezepte. Alle
Auswertungen (Verwendungszahlen, Dubletten, Linkrot) lesen daraus — nie
eigene Rezeptschleifen bauen.

## Testen ohne Instanz

Ein künstlicher Index reicht für alles außer HTTP:

    MEALIE_INDEX=/tmp/.mealie_index.json python3 mealie_ctx.py audit recipes

Für `apply` immer `--dry-run` — der schreibt nichts und prüft trotzdem
Reihenfolge, `$ref`-Auflösung und Payload-Struktur.
