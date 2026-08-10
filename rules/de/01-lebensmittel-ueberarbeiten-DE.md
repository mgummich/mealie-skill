# Mealie Food Rules (DE): Überarbeiten des vorhandenen Bestands

> Ergänzung zu **Food Rules (DE): Parsen & Anlegen**. Jenes Dokument behandelt Strings, die von außen ankommen. Dieses behandelt die Lebensmittel, die bereits da sind. Verweise der Form *Parse §8* zeigen dorthin.

## Zweck
Eine gewachsene Lebensmittelliste — aus mehreren Quellen importiert, von mehreren Personen bearbeitet — regelkonform machen, ohne die Rezepte zu zerstören, die daran hängen.

Die beiden Dokumente unterscheiden sich in einem entscheidenden Punkt:

| | Parse-Regeln | Cleanup-Regeln |
| --- | --- | --- |
| Eingabe | ein String ohne Geschichte | ein Bestand mit lebenden Rezeptverknüpfungen |
| Schlimmster Fall | eine falsche Verknüpfung in einem Rezept | stille Beschädigung über Hunderte Rezepte |
| Umkehrbarkeit | trivial — neu verknüpfen | Merges und Löschungen sind faktisch endgültig |
| Standardhandlung | zuordnen, nicht anlegen | **ohne Beleg nichts ändern** |

> **Oberste Regel:** Ein Lebensmittel ist nicht falsch, weil es hässlich ist. Es ist falsch, wenn es *mehrdeutig, doppelt, falsch gelabelt oder unauffindbar* ist. Kosmetische Umbenennungen kosten Verknüpfungsstabilität und bringen nichts.

---

## 1. Voraussetzungen (nicht überspringen)

Vor dem ersten Schreibvorgang:

1. **Vollexport** von Lebensmitteln, Aliassen, Labels und Rezept-Lebensmittel-Verknüpfungen. Rückspielbarkeit prüfen.
2. **Referenzzähler pro Lebensmittel** — wie viele Rezepte es verwenden. Davon hängt jede Survivor-Entscheidung und jede Priorisierung ab.
3. **Eine Changelog-Tabelle** mit einer Zeile pro Operation: Zeitstempel, Operation, Quell-ID(s), Ziel-ID, betroffene Rezeptanzahl, Bearbeiter, Begründung (§12).
4. **Dry-Run-Fähigkeit.** Jeder Durchgang erzeugt zuerst ein Diff und wird erst nach dem Lesen angewendet. Ein Durchgang mit ungelesenem Diff ist kein Durchgang.

Wer keinen Referenzzähler erzeugen kann, hört hier auf. Zusammenführen, ohne zu wissen, was worauf zeigt, ist Raten mit dauerhaften Folgen.

---

## 2. Reihenfolge der Durchgänge (genau diese)

Die Durchgänge sind so geordnet, dass jeder auf Daten läuft, die der vorherige bereits bereinigt hat. Eine andere Reihenfolge erzeugt Arbeit, die man wiederholen muss.

| # | Durchgang | Art | Risiko |
| - | --------- | --- | ------ |
| 0 | Inventur & Kennzahlen | nur lesend | keins |
| 1 | Feld-Hygiene | nicht destruktiv | gering |
| 2 | Alias-Integrität | nicht destruktiv | gering |
| 3 | Duplikat-Erkennung & Merge | **destruktiv** | hoch |
| 4 | Mehrdeutigkeit & Split | **umstrukturierend** | hoch |
| 5 | Namenskonformität (Umbenennen) | nicht destruktiv, wenn korrekt | mittel |
| 6 | `pluralName` korrigieren | nicht destruktiv | gering |
| 7 | Label korrigieren | nicht destruktiv | gering |
| 8 | Beschreibungsformat | nicht destruktiv | keins |
| 9 | Aussortieren | **destruktiv** | mittel |
| 10 | Verifikation durch Neu-Parsen | nur lesend | keins |

Begründung der zwei nicht offensichtlichen Positionen: **Dedupe vor Split**, weil das Aufteilen eines Lebensmittels, das sich später als Duplikat herausstellt, die Arbeit verdoppelt; **Umbenennen nach Merge**, weil frühes Umbenennen neue Beinahe-Duplikate erzeugt, die der Merge-Durchgang dann wieder einfangen müsste.

Immer einen Durchgang über den ganzen Bestand laufen lassen. Nicht ein Lebensmittel komplett durchsanieren und zum nächsten gehen — das erzeugt ein Diff, das niemand prüfen kann.

---

## 3. Durchgang 0 — Inventur

Nur lesend. Diese Zahlen vor und nach der gesamten Bereinigung erheben, sonst lässt sich nicht feststellen, ob es etwas gebracht hat:

- Lebensmittel gesamt; Lebensmittel mit null Rezeptverknüpfungen (**Waisen**); mit genau einer
- Lebensmittel mit `aliases: []`
- Lebensmittel, deren `name` gegen Parse §8 verstößt (Groß-/Kleinschreibung, Plural, Klammern, Marke)
- Lebensmittel ohne Label oder mit Label `Sonstiges`
- Lebensmittel mit leerer oder zu langer `description`
- **Alias-Kollisionen**: jeder Alias-String, der von mehr als einem Lebensmittel aus erreichbar ist — harter Fehler, keine Warnung
- Rezeptzeilen, die derzeit überhaupt nicht zuordnen

Jede Arbeitsliste **absteigend nach Referenzzähler** sortieren. Das Lebensmittel in 40 Rezepten ist eine Stunde wert; die Waise in null Rezepten kann bis Durchgang 9 warten.

---

## 4. Durchgang 1 — Feld-Hygiene

Rein mechanisch, gefahrlos automatisierbar:

- Leerzeichen trimmen, Mehrfach-Leerzeichen zusammenfassen, Unicode auf NFC normalisieren
- Nachgestellte Interpunktion aus `name`, `pluralName`, Aliassen entfernen
- Groß-/Kleinschreibung nach Parse §8.1 korrigieren — im Deutschen heißt das: Substantiv groß, Adjektiv klein, Klammer-Qualifikator klein
- Sicherstellen, dass `aliases` auf jedem Lebensmittel als Array existiert (`[]`, wenn leer)
- Aliasse entfernen, die identisch mit dem eigenen `name` oder `pluralName` sind (case-insensitiv)
- Aliasse innerhalb eines Lebensmittels case-insensitiv deduplizieren

Alles automatisieren. Wenn eine Änderung hier eine Ermessensentscheidung braucht, gehört sie in einen späteren Durchgang.

---

## 5. Durchgang 2 — Alias-Integrität

Aliasse sind Suchschlüssel. Ein kaputter Alias ist ein kaputtes Matching, kein Schönheitsfehler.

**Alias-Kollision — harter Fehler.** Steht derselbe String als Alias an zwei Lebensmitteln, ist das Matching nicht deterministisch und der Parser wählt willkürlich. Jede Kollision muss vor Durchgang 3 aufgelöst sein:

- Die beiden sind dasselbe → Merge-Kandidat, weiter an Durchgang 3
- Die beiden sind verschieden, der Alias gehört zu einem → beim anderen löschen
- Die beiden sind verschieden und der Alias ist wirklich mehrdeutig (`Pfeffer`, `Brühe`) → **bei beiden löschen** und stattdessen eine Zeile in die Standardtabelle Parse §6.2 aufnehmen. Eine Mehrdeutigkeit gehört in eine sichtbare Tabelle, nicht versteckt in zwei Alias-Listen.

**Unzulässige Aliasse — herabstufen oder löschen.** Ein Alias, der in Wahrheit eine *abgeleitete Form* (`Zitronensaft` an `Zitrone`), eine *Sorte* (`Boskoop` an `Apfel`) oder ein *anderes Produkt* (`Korinthen` an `Rosinen`) ist, ist eine stille Fehlzuordnung: Jedes Rezept, das ihn verwendet, landet am falschen Lebensmittel. Entfernen und prüfen, ob das richtige Lebensmittel existiert — wenn nicht, ist es ein Split (Durchgang 4) oder eine Neuanlage.

**Fehlende Aliasse — ergänzen.** Für jedes Lebensmittel die Saat-Liste aus Parse §8.4 durchgehen: Umlaut-/ß-Ersatzschreibung, AT/CH-Varianten, regionale DE-Varianten, Bindestrich-/Leerzeichen-Varianten, Pulver-Formen. Das ist der billigste Qualitätsgewinn der ganzen Bereinigung, weil er künftige Review-Fälle in automatische Treffer verwandelt.

> Im Deutschen ist die **Umlaut-Ersatzschreibung** hier der größte Einzelposten. Ein Bestand, in dem `Moehre`, `Kaese` und `Weisswein` fehlen, produziert dauerhaft Review-Fälle aus jeder Quelle, die ohne Umlaute exportiert.

---

## 6. Durchgang 3 — Duplikate und Merge

### 6.1 Kandidaten finden
Jedes Signal getrennt laufen lassen und jede Liste für sich prüfen:

1. Identische normalisierte Suchschlüssel (Parse §3) — nahezu sichere Duplikate
2. Alias-Kollisionen, die Durchgang 2 überlebt haben
3. `name` des einen entspricht `pluralName` des anderen
4. Fuzzy-Paare: Levenshtein ≤ 2 bei Schlüsseln ab 6 Zeichen
5. Ein `name` ist Teilstring eines anderen — findet `Öl` / `Olivenöl` und ähnliche zu generische Reste
6. Gleiches Label + gemeinsames Kopfnomen — im Deutschen besonders ergiebig, weil Komposita dasselbe Grundwort teilen (`Rinderhack`, `Hackfleisch vom Rind`)

Signale 4–6 liefern **Kandidaten, nie Entscheidungen**.

### 6.2 Merge ist verboten bei
Diese sehen aus wie Duplikate und sind keine. Ein Merge beschädigt hier Daten unumkehrbar:

- **Abgeleitete Formen**: `Zitrone` vs. `Zitrone [saft]` vs. `Zitrone [abrieb]`
- **Sorten**: `Apfel` vs. `Boskoop`
- **Andere Produkte**: Korinthen vs. Rosinen; `Speisestärke` vs. `Maismehl`; `Natron` vs. `Backpulver`
- **Frisch vs. getrocknet**, ganz vs. gemahlen und jeder andere trennende Qualifikator (Parse §6.1)
- **Echt verschiedene Produkte**: `Schlagsahne` vs. `saure Sahne`; `Schmand` vs. `Crème fraîche`; `Büffelmozzarella` vs. `Mozzarella`
- **Zubereitung vs. Basis**: Espresso vs. Kaffee; Pulled Pork vs. Schweineschulter

Fällt ein Paar hierunter, ist es kein Merge. Entweder sind beide korrekt, oder eines ist ein Fall für Durchgang 9.

### 6.3 Survivor wählen
In dieser Reihenfolge:

1. Höchster Referenzzähler — minimiert Neuverknüpfungen und damit Risiko
2. Bei Gleichstand: derjenige, dessen `name` bereits Parse §8 entspricht
3. Bei Gleichstand: der ältere Datensatz — stabile IDs zählen für externe Anbindungen

Der `name` des Survivors darf dabei **weiterhin falsch sein**. Die Survivor-Wahl entscheidet, welcher *Datensatz* überlebt; der Name wird in Durchgang 5 korrigiert. Nicht den schwach referenzierten Datensatz nehmen, nur weil sein Name schöner ist.

### 6.4 Merge-Ablauf
1. `name` des Survivors auf die kanonische Form setzen (Parse §8) — auch wenn das keiner der beiden aktuellen Namen ist
2. **`name` und `pluralName` des Verlierers als Aliasse am Survivor ergänzen.** Nicht verhandelbar: sonst scheitert jede Rezeptquelle, die die alte Schreibweise verwendet, ab sofort wieder
3. Aliasse vereinigen, dann Hygiene aus Durchgang 1 und 2 auf das Ergebnis erneut anwenden
4. Die kürzere, klarere `description` behalten; sind beide schlecht, nach Parse §10 neu schreiben
5. Das **korrektere** `label` übernehmen — nicht automatisch das des Survivors; gegen die Fehlertabelle Parse §9.2 prüfen
6. Alle Rezeptverknüpfungen vom Verlierer auf den Survivor umhängen
7. Prüfen, dass der Referenzzähler des Survivors der Summe beider vorherigen Zähler entspricht
8. Verlierer löschen und Changelog-Zeile schreiben

Schritt 7 ist die Schutzprüfung. Stimmt die Summe nicht, gingen Verknüpfungen verloren — zurückrollen.

---

## 7. Durchgang 4 — Mehrdeutigkeit und Split

### 7.1 Ein mehrdeutiges Lebensmittel erkennen
Nacktes `Zimt`, `Pfeffer`, `Koriander`, `Brühe` — Lebensmittel, die verschiedene Rezepte verschieden meinen. Die Signale:

- Der Name trägt keinen Qualifikator, obwohl ein trennender auf ihn zutrifft (Parse §6.1)
- Die zeigenden Rezeptzeilen widersprechen sich: mal `Stange`, mal `gemahlen`
- Seine Aliasse enthalten abgeleitete Formen (in Durchgang 2 gefunden)

### 7.2 Zuerst Belege sammeln
**Die tatsächlichen Rezeptzeilen ziehen**, bevor irgendetwas entschieden wird. Ein Lebensmittel, das 30 Rezepte alle gleich meinen, ist nicht mehrdeutig, egal was der Name suggeriert — es braucht eine Umbenennung in Durchgang 5, keinen Split. Ein Split auf Verdacht erzeugt Varianten, die niemand verwendet.

### 7.3 Split-Ablauf
1. Varianten nach Parse §8 anlegen (`Zimt [stange]`, `Zimtpulver`)
2. **Rezeptverknüpfungen einzeln umhängen**, jede Zeile lesen. Nie in Blöcken.
3. Zeilen, die sich aus dem Text nicht klassifizieren lassen, bleiben am Basis-Lebensmittel und gehen in die Review — eine falsche Zuordnung ist schlimmer als eine offene
4. Jeden Alias auf die Variante verschieben, die er tatsächlich bezeichnet (Parse §8.5)
5. Über den Ursprungsdatensatz entscheiden:
   - Er hat eine legitime unqualifizierte Bedeutung (`Zitrone` neben `Zitrone [saft]`) → **behalten**
   - Er war rein mehrdeutig und hat jetzt null Referenzen → löschen
   - Er hat noch nicht klassifizierbare Referenzen → behalten, markieren, später erneut ansehen
6. Die nackte Form in die Standardtabelle Parse §6.2 aufnehmen, damit künftige Importe ohne Review auflösen

### 7.4 Die Zurückhaltungsregel
Jeder Split vervielfacht Einkaufslisten-Einträge. Aufteilen, wenn Rezepte sich tatsächlich widersprechen — nicht, um die Taxonomie elegant zu machen. Nicht trennende Qualifikatoren (`[dose]`, `[tk]`, `[geröstet]`, `[geräuchert]`) rechtfertigen in der Regel **keinen** Split: ein Lebensmittel behalten, den Qualifikator in die Rezeptnotiz, außer die kulinarische Rolle unterscheidet sich wirklich.

---

## 8. Durchgang 5 — Namenskonformität

Parse §8 auf jeden nicht konformen Namen anwenden. **Der alte Name wird immer zum Alias.** Das ist der am häufigsten vergessene Schritt jeder Bereinigung, und das Vergessen zerstört still jeden künftigen Import aus jeder Quelle, die noch die alte Schreibweise verwendet.

Prioritätsreihenfolge, weil Umbenennen Kosten hat:

1. Namen, die **falsch** sind — Marken, Gerichte, Zubereitungen, mehrdeutige Formen
2. Namen, die das **Parsen brechen** — Plural statt Singular, erfundene Klammerformen, zwei Qualifikatoren
3. Namen, die nur **inkonsistent** sind — Groß-/Kleinschreibung, Leerzeichen, Bindestriche

Kategorie 3 allein rechtfertigt bei großem Bestand keine flächendeckende Umbenennung. Bündeln oder in den Durchgang einhängen, der diese Datensätze ohnehin anfasst.

Beim Umbenennen `pluralName` in derselben Operation mitziehen — ein umbenanntes Lebensmittel mit veraltetem Plural ist eine neue Fehlzuordnung. Im Deutschen gilt dasselbe für die **Adjektivendung**: wird `schwarzer Pfeffer` zu `schwarzer Pfeffer [gemahlen]`, muss die Nominativform erhalten bleiben, sonst greift die Endungsnormalisierung aus Parse §4.4 ins Leere.

---

## 9. Durchgänge 6–8 — Plural, Label, Beschreibung

**`pluralName`** — gegen Parse §8.3 prüfen. Die typischen Fehler: geratenes `+s` bei unregelmäßigem Plural (`Apfels` statt `Äpfel`), ein Stoffname mit erfundenem Plural (`Reise`, `Mehle`), und eine Klammer-Variante, die die Basis statt des zählbaren Teils pluralisiert hat.

**Labels** — label-weise arbeiten, nicht lebensmittel-weise. Alles unter einem Label ziehen, auf Fremdkörper durchsehen, gegen die Fehlertabelle Parse §9.2 prüfen. `Sonstiges` ist eine Arbeitsliste, kein Label: jedes Lebensmittel dort ist entweder falsch gelabelt oder ein Kandidat für Durchgang 9.

**Beschreibungen** — `Definition; Verwendung.` und die Zeichengrenze durchsetzen. Der einzige Durchgang ohne Datenintegritätsrisiko, also zuletzt und aggressiv automatisierbar.

---

## 10. Durchgang 9 — Aussortieren

| Art | Test | Aktion |
| --- | ---- | ------ |
| Waise | null Rezeptreferenzen | löschen, wenn auch als künftiges Lebensmittel unplausibel — sonst behalten |
| Marke | Parse §7.1 | ins Generikum mergen; Marke nur dann Alias, wenn umgangssprachlich generisch |
| Gericht oder Zubereitung | Parse §7.1 | wenn referenziert: in Unterrezept umwandeln oder auf Komponenten umhängen; löschen nur ohne Referenzen |
| Zu generisch | `Saft`, `Teig`, `Fleisch` | nur behalten, wenn Rezepte es wirklich so verwenden; sonst splitten oder löschen |
| Test- oder Import-Artefakt | `test`, `xxx`, leere Namen | löschen |

**Bei vorhandenen Referenzen deaktivieren statt löschen.** Ein `deprecated`-Flag hält den Datensatz für Matching und Auswertung erreichbar, blendet ihn aber aus Auswahllisten aus — und ist umkehrbar. Löschen ist es nicht. Löschen bleibt Datensätzen ohne Referenzen und ohne historischen Wert vorbehalten.

---

## 11. Durchgang 10 — Verifikation

Die Bereinigung ist nur dann echt, wenn das Parsen besser geworden ist. Die Parse-Regeln über den gesamten Rezeptbestand erneut laufen lassen und gegen die Basiswerte aus Durchgang 0 vergleichen:

- Anteil der Rezeptzeilen mit Treffer in Tier ≤ 3 — muss **steigen**
- Größe der Review-Queue — muss **sinken**
- Alias-Kollisionen — müssen **null** sein
- Nicht konforme Namen — müssen **null** sein
- Waisenzahl — sollte sinken, ein kleiner stabiler Rest ist in Ordnung
- **Gesamtzahl der Rezept-Lebensmittel-Verknüpfungen — muss unverändert sein**, außer ein dokumentierter Split oder eine dokumentierte Löschung erklärt die Differenz

Die letzte Zeile ist die Integritätsprüfung der gesamten Aktion. Jeder unerklärte Rückgang bedeutet, dass in Durchgang 3 oder 4 Verknüpfungen verloren gingen.

---

## 12. Changelog, Idempotenz und Rollback

**Jede Operation protokollieren**: Zeitstempel, Typ (`merge`/`split`/`rename`/`relabel`/`delete`), Quell- und Ziel-IDs, alte und neue Werte, betroffene Rezeptanzahl, Bearbeiter, einzeilige Begründung. „Weil die Regeln es sagen" ist keine Begründung; „Duplikat von #412, 0 Referenzen, Alias-Kollision auf *Karotte*" ist eine.

**Idempotenz.** Ein zweiter vollständiger Durchlauf über einen bereits bereinigten Bestand muss null Änderungen erzeugen. Tut er das nicht, widersprechen sich zwei Regeln — den Widerspruch finden und beheben, statt mit dauerndem Rauschen zu leben.

**Ping-Pong-Schutz.** Wird ein Lebensmittel in einem Lauf A → B und im nächsten B → A umbenannt, enthalten die Regeln einen echten Widerspruch. Den Datensatz einfrieren, den Regelkonflikt auflösen, dann freigeben. Die Durchgänge dürfen sich nie über Läufe hinweg gegenseitig bekämpfen.

**Rollback.** Merges und Löschungen sind nur aus Export plus Changelog umkehrbar. Beides so lange aufbewahren, bis Sicherheit besteht — praktisch mindestens einen vollen Importzyklus jeder verwendeten Rezeptquelle lang.

---

## 13. Checklisten

**Vor dem Start**
- [ ] Export erstellt und Rückspielbarkeit geprüft?
- [ ] Referenzzähler pro Lebensmittel verfügbar?
- [ ] Changelog-Tabelle bereit?
- [ ] Basiswerte aus Durchgang 0 festgehalten?

**Pro Durchgang**
- [ ] Ein Durchgang, über den ganzen Bestand?
- [ ] Diff erzeugt und tatsächlich gelesen, bevor angewendet wurde?
- [ ] Arbeitsliste nach Referenzzähler sortiert?

**Pro Merge**
- [ ] Wirklich dasselbe Lebensmittel und kein verbotenes Paar aus §6.2?
- [ ] Survivor nach Referenzzähler gewählt, nicht nach Namensästhetik?
- [ ] `name` und `pluralName` des Verlierers als Aliasse ergänzt?
- [ ] Label gegen die Fehlertabelle geprüft und nicht bloß geerbt?
- [ ] Referenzzähler nach dem Umhängen stimmig?

**Pro Split**
- [ ] Tatsächliche Rezeptzeilen als Beleg gelesen?
- [ ] Referenzen einzeln umgehängt, nie in Blöcken?
- [ ] Nicht klassifizierbare Referenzen an der Basis belassen und markiert?
- [ ] Nackte Form in die Standardtabelle aufgenommen?

**Pro Umbenennung**
- [ ] Alter Name als Alias ergänzt?
- [ ] `pluralName` in derselben Operation aktualisiert?
- [ ] Adjektivendung im Nominativ korrekt (§8)?

**Zum Schluss**
- [ ] Gesamtzahl der Rezeptverknüpfungen unverändert oder vollständig erklärt?
- [ ] Alias-Kollisionen bei null?
- [ ] Zweiter vollständiger Lauf ohne Änderungen?
