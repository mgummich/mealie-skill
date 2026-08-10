# Utensilien: Anlegen & Zuweisen bei der Rezepterstellung (DE)

## Grundsatz

Ein Utensil ist ein Gerät, das das Rezept **blockiert**: ohne dieses Gerät ist das Rezept nicht kochbar oder das Ergebnis ein anderes.

Felder: `name`, `slug`, `onHand`. **Keine Aliasse.** Deshalb ist die Namensdisziplin hier strenger als bei jeder anderen Entität — ein zweites Mal anders geschrieben ist ein zweites Utensil, und niemand merkt es.

> **Realistisch sind null bis vier Utensilien pro Rezept.** Null ist ein völlig normales Ergebnis. Ein Rezept mit acht Utensilien listet Küchenausstattung.

---

## 1. Der Blockade-Test

Eine Frage: **Hat eine funktionierende Durchschnittsküche das Gerät ohnehin?**

**Ja → kein Utensil.**
Messer, Schneidebrett, Topf, Pfanne, Schüssel, Sieb, Rührlöffel, Backblech, Schneebesen, Reibe, Sparschäler, Ofen, Herd, Kühlschrank.

**Nein → Utensil.**
Airfryer, Eismaschine, Sous-vide-Stick, Smoker, Küchenmaschine, Standmixer, Stabmixer, Fleischwolf, Waffeleisen, Dampfgarer, Spätzlepresse, Mörser, Pastamaschine, Zuckerthermometer, Springform, Kastenform, Tajine, Wok, Gusseisentopf, Kastenform, Muffinblech, Küchenwaage mit 1-g-Auflösung.

Grenzfälle nach der Frage entscheiden, ob das Weglassen das Gericht **verhindert** oder nur **erschwert**. Ein Stabmixer erschwert die Suppe, verhindert sie nicht — außer das Rezept lebt von der Textur. Im Zweifel: kein Utensil.

---

## 2. Zuweisen beim Rezeptanlegen

| Stufe | Prüfung | Aktion |
| --- | --- | --- |
| 0 | Gerät existiert exakt so | zuweisen |
| 1 | Gerät existiert unter dem Gattungsbegriff (`Thermomix` → `Küchenmaschine`) | **das bestehende** zuweisen |
| 2 | Gerät existiert in anderer Größe (`Springform 26 cm` vs. `Springform 20 cm`) | §3 — nur bei ergebnisrelevanter Größe getrennt |
| 3 | Gerät besteht den Blockade-Test nicht | **nicht zuweisen**, nicht anlegen |
| 4 | Neu und blockierend | anlegen (§4) |

**Vor jedem Anlegen die Liste ansehen.** Ohne Aliasse fängt nichts einen Tippfehler oder eine abweichende Schreibweise ab.

---

## 3. Größenangaben

Nur dann in den Namen, wenn die Größe das **Ergebnis** bestimmt:

- `Springform 26 cm` — ja, eine 20er-Form lässt denselben Teig überlaufen
- `Kastenform 30 cm` — ja
- `Topf 3 l` — nein, und generisch `Topf` fällt ohnehin unter §1
- `Schüssel groß` — nein

Format: `Gerät + Zahl + Einheit`, ohne Klammern, metrisch: `Springform 26 cm`. Zoll-Angaben aus Originalrezepten werden umgerechnet (1 inch = 2,54 cm) und auf gängige Formgrößen gerundet: 8 inch → 20 cm, 9 inch → 24 cm, 10 inch → 26 cm.

---

## 4. Anlegen

- Deutscher **Gattungsbegriff**, Singular, Substantiv groß, kein Plural
- **Keine Marke:** `Thermomix` → `Küchenmaschine`, `KitchenAid` → `Küchenmaschine`, `Crockpot` → `Slow Cooker`, `Bialetti` → `Espressokanne`
- Ausnahme: Ist die Marke umgangssprachlich zum Gattungsbegriff geworden und existiert keine gängige Alternative, ist sie der Name. `Slow Cooker` ist etabliert, `Thermomix` nicht.
- Keine Adjektive ohne Blockadewirkung: `Springform 26 cm`, nicht `große Springform (Marke egal)`
- **`onHand` bewusst setzen.** Das Flag ist der Haushaltsbestand, nicht der Wunschzettel. Nur wenn es stimmt, wird „Was kann ich heute überhaupt kochen?" beantwortbar.

---

## 5. Verhältnis zu Schlagwörtern

`Airfryer` ist **beides**: das Gerät ist ein Utensil, die Zubereitungsart ein Schlagwort der Facette *Methode*. Beides anzulegen ist richtig und kein Duplikat — das Utensil beantwortet „kann ich das?", das Schlagwort „zeig mir alle Airfryer-Rezepte".

Bedingung: Beide müssen **identisch heißen**, sonst wirkt es wie ein Fehler.

Umgekehrt gilt: `Ofen` ist ein Schlagwort, aber kein Utensil — jede Küche hat einen, er blockiert nicht.

---

## 6. Checkliste

- [ ] Besteht das Gerät den Blockade-Test (§1)?
- [ ] Liste vorher angesehen — es gibt keine Aliasse, die einen Tippfehler auffangen?
- [ ] Marke entfernt, Gattungsbegriff verwendet?
- [ ] Größe nur dann im Namen, wenn sie das Ergebnis bestimmt?
- [ ] Größenangabe metrisch und auf eine gängige Formgröße gerundet?
- [ ] Singular, Substantiv groß, kein Plural?
- [ ] `onHand` bewusst gesetzt?
- [ ] Bleibt das Rezept bei höchstens vier Utensilien?
