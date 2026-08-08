# Mealie-Pflege

> Übernimmst du das Projekt als Agent? Lies zuerst `HANDOFF.md` (Zustand,
> was verifiziert ist, offene Punkte) und `CLAUDE.md` (Projektregeln).
> Gegen eine echte Mealie-Instanz lief noch kein Aufruf.

Zwei Wege, dieselben Regeln:

| | Antigravity | Standalone |
|---|---|---|
| Modell | das der IDE | Anthropic API, Prompt-Caching |
| Bedienung | `/mealie <modus>` | `optimize.py <modus> …` |
| Stärke | Browser für Bild- und Quellenrecherche, Plan-Artefakt | Batch über viele Rezepte |

Gemeinsam: lokaler Rezeptindex statt wiederholter API-Schleifen, Plan vor
jeder Schreiboperation, deterministische Ausführung über eine ACTIONS-Liste.

## Modi

| Modus | macht |
|---|---|
| `recipe` | leere Felder füllen, Zutaten parsen, Schritte übersetzen, metrisch umrechnen, Bild setzen |
| `foods` | Lebensmittel: Beschreibung, Plural, Label, Aliase; Dubletten zusammenführen |
| `units` | dasselbe für Einheiten |
| `organizers` | Kategorien, Tags, Utensilien konsolidieren; Rezepte umhängen, leere Objekte löschen |
| `cookbooks` | Kochbücher als Filterregeln anlegen und überarbeiten |
| `maintenance` | doppelte Rezepte, tote Bilder und Quell-URLs, Diät-Tags aus Zutaten |

## Vorbereitung

    export MEALIE_URL=https://mealie.example.org
    export MEALIE_TOKEN=<Profil -> API Tokens>

Vor dem ersten Lauf ein Backup ziehen: Mealie -> Site Settings -> Backups.

Endpunktpfade prüfen, sie unterscheiden sich zwischen Mealie-Versionen:

    for p in foods units groups/labels organizers/categories \
             organizers/tags organizers/tools groups/cookbooks; do
      printf '%-26s ' "$p"
      curl -s -o /dev/null -w '%{http_code}\n' \
        -H "Authorization: Bearer $MEALIE_TOKEN" "$MEALIE_URL/api/$p?perPage=1"
    done

Was 404 liefert, im `EP`-Dictionary von `mealie_ctx.py` anpassen
(`/api/categories` statt `/api/organizers/categories` bei älteren Versionen).

Ebenfalls einmal verifizieren, weil je nach Version `PUT` oder `POST`:
`/api/foods/merge` und `/api/units/merge`.

## Installation

    python3 build.py --install claude-code           # global, ~/.claude/
    python3 build.py --install antigravity           # global, ~/.gemini/config/
    python3 build.py --install claude-code --into <projekt>
    python3 build.py --install cursor --into <projekt>
    python3 build.py --install agents-md --into <projekt>   # Codex, Zed, …

`cursor` und `agents-md` sind projektbezogen und verlangen `--into`.
Vorhandene Dateien werden nie still überschrieben (`--force`); eine
bestehende `AGENTS.md` wird nur im markierten Block aktualisiert.

Ohne `--install` rendert `python3 build.py` alle Ziele nach `dist/`.

In Antigravity und Claude Code danach:

    /mealie rezept mein-rezept
    /mealie lebensmittel
    /mealie organizer
    /mealie kochbuch
    /mealie wartung

Erster Lauf: Terminal auf „Request Review", damit du jeden `apply`-Aufruf
siehst. Für die Bild- und Quellenrecherche die Domains deiner Rezeptquellen
sowie `commons.wikimedia.org`, `pexels.com`, `unsplash.com` freigeben.

## Standalone

    export ANTHROPIC_API_KEY=sk-ant-…
    pip install requests

    python standalone/optimize.py recipe mein-rezept --dry-run
    python standalone/optimize.py recipe --batch --limit 20
    python standalone/optimize.py foods luecken --limit 25
    python standalone/optimize.py foods dubletten --limit 5
    python standalone/optimize.py units dubletten
    python standalone/optimize.py organizers tags
    python standalone/optimize.py cookbooks --zweck "Schnelle Feierabendküche"
    python standalone/optimize.py maintenance links

## Werkzeug direkt

`mealie_ctx.py` funktioniert auch ohne Modell:

    python .../mealie_ctx.py index --refresh
    python .../mealie_ctx.py audit foods|units|categories|tags|tools|recipes|links
    python .../mealie_ctx.py ctx recipe <slug>
    python .../mealie_ctx.py ctx foods|units|categories|tags|tools|cookbooks|diet
    python .../mealie_ctx.py usage tag <id>
    python .../mealie_ctx.py apply actions.json --dry-run

## Aufbau

    skill/                  einzige Quelle der Wahrheit
      SKILL.md              schlanker Router
      references/*.md       Details, nur bei Bedarf gelesen
      workflow.md           Ablauf für /mealie
      scripts/mealie_ctx.py alle API-Zugriffe
    standalone/
      prompts/common.txt    Grundsätze + ACTIONS-Format (handgepflegt)
      optimize.py           Modellaufruf, Freigabe, Batch
    build.py                rendert dist/ für die vier Ziele, installiert
                            mit --install
    test_build.py           python3 test_build.py

## Ausgabestil: caveman

Der Skill nutzt [caveman](https://github.com/juliusbrussee/caveman), falls
installiert – eine Kompression des Antwortstils. Audits, Pläne und Reports
sind hier lange Tabellenausgaben, also genau der Fall, in dem sich das lohnt.

Installation (Antigravity, Skill-Ordner analog zu `mealie`):

    cp -r <caveman-repo>/skills/caveman  <workspace>/.agents/skills/

**Die Abgrenzung ist wichtiger als die Aktivierung.** Komprimiert wird nur
die Chat-Ausgabe. Alles, was über `actions.json` in die Datenbank wandert –
Rezept- und Food-Beschreibungen, Zubereitungsschritte, Notizen,
Kochbuchbeschreibungen – bleibt vollständige deutsche Prosa. Diese Texte
liest später jemand in der Mealie-Oberfläche, ohne von diesem Ablauf zu
wissen. Die Regel steht sowohl in `SKILL.md` als auch in
`references/actions.md`, weil sie genau dort verletzt würde.

Warnungen zu destruktiven Operationen, Rückfragen und die Freigabefrage
bleiben ebenfalls in ganzen Sätzen. Bei einem Merge, der 14 Rezepte
umschreibt, ist Eindeutigkeit mehr wert als ein paar gesparte Tokens –
caveman hat dafür eine eigene Klarheitsregel.

Ohne den Skill ändert sich nichts: Die Referenzen verlangen ohnehin knappe,
tabellarische Ausgaben. Standalone ist die entsprechende Regel direkt in
`prompts/common.txt` eingebaut.

Ehrlich zur Ersparnis: caveman senkt nur die **Ausgabe**-Tokens und bringt
selbst rund 1–1,5 k Eingabe-Tokens pro Turn mit. Bei den langen Plänen und
Reports dieses Ablaufs geht die Rechnung auf; bei kurzen Einzelabfragen kann
sie negativ werden.

## Token-Haushalt

Drei Maßnahmen, in der Reihenfolge ihrer Wirkung:

**Referenzdateien statt einer großen SKILL.md.** Der Router ist rund 700
Tokens; die Moduldetails (je 900–1300) liest der Agent nur, wenn der Modus
gewählt ist. Vorher kostete jede Mealie-Anfrage den vollen Regelsatz.

**Lokaler Rezeptindex.** `audit` und `usage` lesen aus `.mealie_index.json`
statt jedes Mal alle Rezepte einzeln abzurufen. Der Index wird beim ersten
Audit gebaut und nach jedem schreibenden `apply` verworfen.

**Gezielte Suche statt voller Tabellen.** `ctx recipe` sucht nur die Foods,
die zu den Zutaten dieses Rezepts passen. Bei ein paar hundert Foods ist das
der Unterschied zwischen 500 und 20.000 Tokens Kontext.

Standalone kommt Prompt-Caching dazu. Gemeinsame Regeln und Modusregeln
bilden **einen** Block, weil der gemeinsame Teil allein unter der
Mindestgröße von 1024 Tokens liegt. Der Cache wird also je Modus
wiederverwendet, nicht modusübergreifend. Kontrolle in der `[usage]`-Zeile:
erst `cache_creation_input_tokens`, danach `cache_read_input_tokens`.
Der Cache lebt fünf Minuten ab letztem Treffer — Batch-Läufe am Stück
durchlaufen lassen.

## Sicherheitsnetze

Die Ausführungsreihenfolge ist erzwungen und bricht vor dem ersten
Schreibzugriff ab, wenn die ACTIONS sie verletzen:

    create_label -> merge_food -> merge_unit -> create_food -> create_unit
    -> create_category -> create_tag -> create_tool -> update_food
    -> update_unit -> update_organizer -> retag_recipe -> delete_organizer
    -> create_cookbook -> update_cookbook -> patch_recipe -> set_image

Destruktive Operationen werden vor der Ausführung angesagt. `--dry-run`
zeigt jede Aktion, ohne zu schreiben. Rezepte löscht das Werkzeug nie —
doppelte Rezepte werden nur vorgelegt.

## Heuristiken und ihre Grenzen

**Dubletten** laufen über eine Normalform (Kleinschreibung, Umlaute
aufgelöst, gängige Pluralendungen entfernt). Gefunden werden Tomate/Tomaten
und Kürbis/Kuerbis; korrekt nicht gruppiert werden Butter/Buttermilch und
Tomate/Cherrytomate. Nicht gefunden werden unregelmäßige Formen (Ei/Eier)
und echte Synonyme (Frühlingszwiebel/Lauchzwiebel) — die ergänzt das Modell
beim Prüfen der Gruppen.

**Doppelte Rezepte** über Namensgleichheit plus Jaccard-Ähnlichkeit der
Zutaten ab 0.6. Ein hoher Wert ist ein Verdacht, kein Beweis: Varianten
desselben Gerichts liegen naturgemäß hoch.

**Diät-Tags** werden nur aus vollständig geparsten Zutaten abgeleitet und
nur als Ausschlusskriterium. Bei Unsicherheit wird nicht getaggt — ein
falsches „glutenfrei" ist teurer als ein fehlendes.
