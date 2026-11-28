# ENZCOM // Weather für Home Assistant

![ENZCOM // Weather](branding/weather.svg)

Wetter für deinen Ort: aktuelle Werte, Stunden- und Tagesvorhersagen sowie einzelne
Sensoren für Automationen. Einrichtung per Ortsuche, ohne YAML und ohne Wetter-API-Schlüssel.
Mehrere Orte sind als separate Integrationseinträge möglich.

## Installation

**ENZCOM // Weather** ist im gemeinsamen Katalog von Marketplace und HACS verfügbar.

### Marketplace ab Home Assistant 2026.11

1. Öffne als Administrator **Einstellungen → Marketplace**.
2. Suche nach **ENZCOM // Weather** und öffne den Eintrag.
3. Wähle **Installieren** und bestätige die Installation. Suche im Einrichtungsdialog
   nach deinem Ort und wähle ihn aus.

Für die Installation aus dem Marketplace-Katalog brauchst du kein GitHub-Konto.
Falls Home Assistant einen Neustart verlangt, starte zuerst neu. Wenn der
Einrichtungsdialog nicht geöffnet ist, wähle **ENZCOM // Weather** unter
**Einstellungen → Geräte & Dienste → Integration hinzufügen**.

### HACS mit Home Assistant 2026.10

1. Öffne **HACS** in der Seitenleiste und suche nach **ENZCOM // Weather**.
2. Öffne den Eintrag, wähle **Herunterladen** und starte Home Assistant neu.
3. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen**,
   wähle **ENZCOM // Weather** und suche nach deinem Ort.

Nach der Einrichtung kannst du im Dashboard eine Wettervorhersagekarte hinzufügen
und die neue Wetterentität auswählen.

[Eintrag in Marketplace oder HACS öffnen](https://my.home-assistant.io/redirect/hacs_repository/?owner=enzcom&repository=enzcom-weather&category=integration) ·
[Nach der Installation den Ort einrichten](https://my.home-assistant.io/redirect/config_flow_start/?domain=enzcom_weather)

Updates aus Marketplace oder HACS findest du in der Updateverwaltung von Home
Assistant. Starte Home Assistant nach dem Update neu, damit die neue Version geladen wird.

### Ausweichweg über das GitHub-Repository

Falls die Suche keinen Treffer zeigt, kannst du `https://github.com/enzcom/enzcom-weather`
als Repository hinzufügen.

- **Marketplace:** Wähle unter **Einstellungen → Marketplace** oben rechts
  **Aus Link hinzufügen**. Verbinde GitHub, wenn Home Assistant dich dazu auffordert,
  und füge die URL hinzu. Öffne den Eintrag und wähle **Installieren**.
- **HACS:** Wähle im Drei-Punkte-Menü **Benutzerdefinierte Repositories**. Füge die URL
  mit der Kategorie **Integration** hinzu. Lade **ENZCOM // Weather** herunter und
  starte Home Assistant neu. Richte anschließend den Ort wie oben beschrieben ein.

### Manuell per ZIP

Das ZIP `enzcom-weather-1.0.3.zip` aus den Releases enthält `custom_components/enzcom_weather/`.
Kopiere diesen Ordner vollständig in den Konfigurationsordner von Home Assistant,
starte Home Assistant neu und füge die Integration wie oben beschrieben hinzu.
Sichere bei Updates den bestehenden Ordner und spiele das neue ZIP auf demselben Weg ein.

Die Releases sind auf [GitHub](https://github.com/enzcom/enzcom-weather/releases)
und [ENZCOM // Code](https://code.enzcom.cloud/ENZCOM/weather-home-assistant/releases) verfügbar.

## Funktionen

- Native Wetterentität: Zustand, Temperatur, Luftfeuchtigkeit, Luftdruck, Sichtweite,
  Bewölkung, Windgeschwindigkeit, Böen und Windrichtung.
- Stundenprognosen bis zu 72 Stunden, soweit der Anbieter diese liefert.
- Tagesprognosen mit vollständigen Temperaturwerten; unvollständige Tagesmengen
  werden nicht als vollständige Tageswerte ausgegeben.
- Separate Sensoren für Temperatur, Feuchte, Druck, Wind, Böen, Windrichtung,
  Regenmenge des angegebenen Intervalls, nächste Stundenwahrscheinlichkeit,
  Datenstand und Datenverfügbarkeit. Sichtweite kann zusätzlich aktiviert werden.
- Windrichtung bezeichnet die Herkunft: 0°/360° Nord, 90° Ost. Windstille hat keine Richtung.
- Ein gemeinsamer Abruf je Ort alle zehn Minuten, mit nativer Fehlerbehandlung.
- Veraltete Daten und Abruffehler machen Wetter-/Messentitäten unverfügbar.
  Datenstand und Statussensor bleiben zur Erklärung erhalten.

Die Regenmenge des separaten Sensors steht in **l/m²** (zahlenmäßig gleich mm).
Sie ist die Menge des im Attribut genannten Mess-/Prognoseintervalls und kein
fortlaufender Zähler. Die native Wetterentität verwendet Home Assistants
standardisierte Niederschlagseinheiten; deren Anzeige richtet sich nach den
Home-Assistant-Einstellungen. Stundenregen wird dem richtigen Prognoseintervall
zugeordnet, auch wenn ein Anbieter Wind-/Temperaturzeit und Regenintervallende
unterschiedlich angibt. Fehlende Werte bleiben unbekannt.

Wetter- und Sensorentitäten passen in die normalen Home-Assistant-Karten.
Unsere Webdiagramme sind unter [ENZCOM // Weather](https://weather.enzcom.cloud)
verfügbar; eine eigene Dashboard-Karte ist nicht Bestandteil von Version 1.0.3.
UV, Pollen, Luftqualität und PV werden in dieser Ausgabe noch nicht als Entitäten
angeboten. Es werden keine Geräte geschaltet und keine Automationen angelegt.

## Datenschutz und Datenquellen

Home Assistant fragt ausschließlich den öffentlichen ENZCOM-Wetterdienst per HTTPS ab.
Bei der Ortsuche werden der Suchtext, später die ausgewählte Ortskennung sowie
technisch die IP-Adresse und eine Integrationskennung übertragen. Keine Geräte-,
Personen-, Kalender- oder Kontaktdaten werden gelesen oder versendet. Zugangsdaten
zu Wetteranbietern sind nicht erforderlich. Der Dienst benötigt Internetzugang.

Wetterdaten: DWD über Bright Sky oder MET Norway; Ortsdaten: GeoNames.
Die ausgewählte Datenquelle erscheint am Statussensor. Es gelten die
[Datenschutzhinweise](https://weather.enzcom.cloud/datenschutz) und das
[Impressum](https://weather.enzcom.cloud/impressum).

## Wartung

Mindestens Home Assistant 2026.10.0. Gegen 2026.10.2 und 2026.11.2 geprüft.
Quellcode unter MIT; ENZCOM-Name und Markenrechte bleiben unberührt. Support und
[Fehlerberichte](https://github.com/enzcom/enzcom-weather/issues) erfolgen bei ENZCOM.
Dies ist eine von ENZCOM gepflegte benutzerdefinierte Integration.

Prüfen: `python -m unittest discover -s tests -v` im jeweiligen Home-Assistant-Runtime.
Hassfest, HACS-Validierung und Runtimeprüfungen laufen über GitHub Actions.
