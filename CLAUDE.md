# Mealie-Pflege — Projektregeln

Werkzeug zum Aufräumen einer Mealie-Instanz über deren REST-API. Zwei
Frontends, eine gemeinsame Logik: ein Antigravity-Skill und ein
Standalone-Skript für die Anthropic API.

## Architektur

    skill/                  einzige Quelle der Wahrheit
      SKILL.md              Router: Modus wählen, gemeinsame Regeln
      references/*.md       Details je Modus, nur bei Bedarf gelesen
      workflow.md           Ablauf für /mealie
      scripts/mealie_ctx.py ALLE API-Zugriffe, kein Modellaufruf
    standalone/
      prompts/common.txt    Grundsätze + ACTIONS-Format (handgepflegt)
      optimize.py           Modellaufruf, Freigabe, Batch
    build.py                rendert dist/ für claude-code, antigravity,
                            cursor, agents-md; installiert mit --install
    test_build.py           python3 test_build.py

`mealie_ctx.py` ist die einzige Stelle mit HTTP-Zugriff auf Mealie.
`optimize.py` ruft es als Subprozess auf und leitet die Modusprompts zur
Laufzeit aus `skill/references/` ab (`build.render_standalone`). Neue
Funktionalität gehört ins Skript, nicht in die Prompts.

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

**Regeln stehen an einer Stelle.** `skill/` ist die Quelle; `dist/` und die
Standalone-Prompts werden gerendert, nie von Hand gepflegt. Drei Stellen in
den Referenzen tragen `<!-- nur-agent -->`/`<!-- standalone: … -->`-Marker
für Text, der je Kontext verschieden sein muss.

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
