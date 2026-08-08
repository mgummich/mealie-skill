# Portabler Mealie-Skill — Entwurf

Stand: 9. August 2026.

## Ziel

Eine Quelle der Wahrheit für die Regeln, aus der sich die Skill-Formate aller
gängigen Agent-Werkzeuge erzeugen lassen: Claude Code, Antigravity/Gemini,
Cursor und die Werkzeuge, die `AGENTS.md` lesen (Codex, Zed, OpenCode).

Nicht Teil dieses Entwurfs: MCP-Server, CI, PyPI-Paket, Versionierung der
erzeugten Artefakte.

## Ausgangslage

`antigravity/skills/mealie/` ist heute zugleich Quelle und Zielformat. Der
zweite Konsument, `standalone/`, hat eine eigene Kopie der Regeln in
`prompts/*.txt`, die von Hand aus `references/*.md` abgeleitet wird — ein im
`HANDOFF.md` dokumentierter Wartungsschritt, der bei jeder Regeländerung
vergessen werden kann.

Der Unterschied zwischen einer Referenz und dem daraus abgeleiteten Prompt ist
mechanisch: Es fallen die Zeilen weg, die `mealie_ctx.py` aufrufen, weil sie
nur im Antigravity-Kontext gelten.

## Layout

    skill/                       einzige Quelle der Wahrheit
      SKILL.md                   Router (Frontmatter: name, description)
      references/*.md            sechs Dateien, inkl. actions.md
      workflow.md                bisher antigravity/workflows/mealie.md
      scripts/mealie_ctx.py
    standalone/
      optimize.py
      prompts/common.txt         handgepflegt, nicht abgeleitet
    build.py
    test_build.py
    dist/                        gitignored

`SKILL.md` ist das kanonische Format. Es ist ohne Änderung
Claude-Code-tauglich, und Antigravity nutzt dasselbe Schema. Die beiden
übrigen Ziele sind Umformungen davon.

`standalone/prompts/<modus>.txt` entfallen ersatzlos. `optimize.py` leitet die
Modusregeln zur Laufzeit aus `skill/references/<modus>.md` ab, mit derselben
Strip-Funktion, die auch der Build nutzt. Damit verschwindet der manuelle
Ableitungsschritt, statt automatisiert zu werden. `common.txt` bleibt
handgepflegt: Es ist eigenständig formuliert, keine Ableitung.

`optimize.py` löst `mealie_ctx.py` künftig über `../skill/scripts/` auf statt
über `../antigravity/skills/mealie/scripts/`. Bei den Zielen `cursor` und
`agents-md`, die kein Skill-Verzeichnis kennen, landet das Skript unter
`mealie/scripts/` im Zielprojekt.

## Ziele des Builds

| Ziel | Layout | Umformung |
|---|---|---|
| `claude-code` | `.claude/skills/mealie/` + `.claude/commands/mealie.md` | keine; `workflow.md` wird Slash-Command |
| `antigravity` | `.agents/skills/mealie/` + `.agents/workflows/mealie.md` | keine |
| `cursor` | `.cursor/rules/mealie.mdc` + `mealie-<modus>.mdc` + `mealie/scripts/` | Frontmatter, Pfadangaben |
| `agents-md` | `AGENTS.md` + `mealie/references/` + `mealie/scripts/` | Router einbetten, Pfade umbiegen |

### Cursor

Eine Regeldatei je Referenz, nicht eine große Sammeldatei. Regeln mit
`alwaysApply: false` und einer `description` fordert der Agent bei Bedarf an —
dasselbe Prinzip wie die Referenzaufteilung in `SKILL.md`. Eine Sammeldatei
würde den Token-Vorteil aufheben, der laut `README.md` der Grund für die
Aufteilung war.

Die `description` je Modusdatei entsteht aus der Zeile, die für diesen Modus
schon in der Router-Tabelle von `SKILL.md` steht.

Frontmatter je erzeugter `.mdc`:

    ---
    description: <Zeile aus der Router-Tabelle>
    alwaysApply: false
    ---

### AGENTS.md

`AGENTS.md` enthält nur den Router. Die Referenzen liegen daneben als normale
Markdown-Dateien unter `mealie/references/` und werden per Dateizugriff
gelesen.

Grund: `AGENTS.md` liegt bei diesen Werkzeugen permanent im Kontext. Die
vollen Regeln dort einzubetten kostet bei jeder Anfrage im Projekt rund 5000
Tokens, auch wenn es nicht um Mealie geht.

### Pfadangaben

Die Referenzen sind im Fließtext mit `references/recipes.md` und
`scripts/mealie_ctx.py` benannt. Für `agents-md` stimmen diese Pfade nicht
mehr, für Cursor gibt es keine Pfade, sondern Regelnamen. `build.py` ersetzt
die Angaben je Ziel. Die Quelle behält die Antigravity-/Claude-Schreibweise,
weil das die beiden Ziele ohne Umformung sind.

## Bedienung

    python build.py                          alles nach dist/
    python build.py --target cursor          nur ein Ziel
    python build.py --install claude-code    nach ~/.claude/skills/
    python build.py --install cursor --into ../myapp

Ohne `--install` schreibt der Build ausschließlich nach `dist/`. Fremde
Verzeichnisse werden nur auf ausdrückliche Anforderung angefasst.

## Schutz vorhandener Dateien

Zwei Fälle, unterschiedlich behandelt:

**Skill- und Rules-Verzeichnisse** (`.claude/skills/mealie/`,
`.agents/skills/mealie/`, `.cursor/rules/mealie*.mdc`) gehören vollständig
diesem Werkzeug. Existieren sie bereits, bricht der Installer ab und verlangt
`--force`. Kein stilles Überschreiben.

**`AGENTS.md`** gehört dem Nutzer und kann beliebigen anderen Inhalt haben.
Der Installer schreibt nie die ganze Datei, sondern setzt einen Block zwischen
die Marker:

    <!-- mealie:begin -->
    …
    <!-- mealie:end -->

Ein erneuter Lauf ersetzt genau diesen Block; alles außerhalb bleibt
unverändert. Fehlt die Datei, wird sie angelegt. Fehlen die Marker in einer
vorhandenen Datei, wird der Block angehängt.

## Test

Eine Datei `test_build.py`, reine `assert`s, kein Framework, keine neuen
Abhängigkeiten. Sie deckt die drei Stellen mit echter Logik ab:

1. Strippen der Werkzeugzeilen: Aus einer Referenz mit `audit foods`-Zeile
   wird ein Text ohne diese Zeile, der Rest bleibt zeichengleich.
2. Umschreiben der Pfadangaben je Ziel.
3. Idempotenz des AGENTS.md-Blocks: zweimaliges Einfügen ergibt dieselbe
   Datei; Inhalt außerhalb der Marker überlebt.

Kopiervorgänge brauchen keinen Test.

## Mitzuziehende Dokumente

- `CLAUDE.md`: Architekturblock auf das neue Layout; die Regel „Prompts neu
  ableiten" entfällt.
- `README.md`: Installationsabschnitt je Werkzeug statt nur Antigravity.
- `HANDOFF.md`: Abschnitt „Prompts neu ableiten" streichen. Die übrigen
  offenen Punkte (Endpunktverifikation, Merge-Endpunkte, Batch-Slug-Erkennung)
  bleiben unberührt — dieser Entwurf ändert nichts an `mealie_ctx.py`.

## Was sich nicht ändert

`mealie_ctx.py` bleibt inhaltlich unangetastet und wandert nur mit dem
Verzeichnis. Die Regeln selbst — drei Phasen, erzwungene Ausführungsreihenfolge,
kein Rezeptlöschen, volle Prosa in `actions.json` — sind von diesem Entwurf
nicht betroffen.
