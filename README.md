# ENZCOM // Weather für Home Assistant

![ENZCOM // Weather](custom_components/enzcom_weather/brand/weather.svg)

Wetter für deinen Ort: aktuelle Werte, Stunden- und Tagesvorhersagen sowie einzelne
Sensoren für Automationen. Einrichtung per Ortsuche, ohne YAML und ohne Wetter-API-Schlüssel.
Mehrere Orte sind als separate Integrationseinträge möglich.

[In Marketplace / HACS öffnen](https://my.home-assistant.io/redirect/hacs_repository/?owner=enzcom&repository=enzcom-weather&category=integration) ·
[Nach der Installation einrichten](https://my.home-assistant.io/redirect/config_flow_start/?domain=enzcom_weather)

## Installation

### Home Assistant ab 2026.11: Marketplace

1. **Einstellungen → Marketplace → Aus Link hinzufügen** öffnen.
2. `https://github.com/enzcom/enzcom-weather` eintragen. Für benutzerdefinierte
   Repositories gegebenenfalls die GitHub-Verbindung bestätigen.
3. **Installieren** wählen und im Einrichtungsdialog deinen Ort suchen/auswählen.
4. Im Dashboard eine Wettervorhersagekarte hinzufügen und die neue Wetterentität wählen.

Die Integration ist zunächst eine benutzerdefinierte Quelle. Eine beantragte
Katalogaufnahme bedeutet noch keine Aufnahme oder Prüfung durch Home Assistant.
Updates erscheinen in der Updateverwaltung; Updates einer geladenen Integration
benötigen einen Neustart. Beim erstmaligen Marketplace-Installieren ist normalerweise
kein Neustart nötig.

### Home Assistant 2026.10: HACS

1. HACS öffnen, im Menü **Benutzerdefinierte Repositories** auswählen.
2. `https://github.com/enzcom/enzcom-weather` mit Kategorie **Integration** hinzufügen.
3. ENZCOM // Weather herunterladen und Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → ENZCOM // Weather**.
5. Ort suchen und das passende Ergebnis auswählen.

### Ohne Marketplace oder HACS

Das ZIP `enzcom-weather-1.0.0.zip` aus den Releases enthält `custom_components/enzcom_weather/`.
Diesen Ordner vollständig in den Konfigurationsordner von Home Assistant kopieren,
Home Assistant neu starten und die Integration wie oben hinzufügen. Vor Updates
bestehenden Ordner sichern; bei manueller Installation Updates ebenfalls manuell einspielen.

Releases und identische Downloads zusätzlich auf
[ENZCOM // Code](https://code.enzcom.cloud/ENZCOM/weather-home-assistant/releases).

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
verfügbar; eine eigene Dashboard-Karte ist nicht Bestandteil von Version 1.0.0.
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
