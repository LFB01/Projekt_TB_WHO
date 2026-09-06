# Tuberkulose-Screening und Erkrankungen im Folgejahr

Dieses Projekt untersucht anhand öffentlich verfügbarer WHO-Daten, ob höhere
Raten von Kontaktpersonen-Screening und Tuberkulose-Prävention (TPT) mit einer
günstigeren Entwicklung gemeldeter TB-Fälle im Folgejahr zusammenhängen.
Ergänzend werden Resistenzraten und Therapieergebnisse betrachtet.

## Forschungsfragen

1. Gehen höhere Screening- und Präventionsraten mit einer günstigeren
   Entwicklung der gemeldeten TB-Fälle im Folgejahr einher?
2. Gehen sie mit niedrigeren Raten Rifampicin-resistenter und multiresistenter
   Tuberkulose im Folgejahr einher?
3. Gehen sie mit besseren Therapieergebnissen im Folgejahr einher?

## Inhalt

- `data/`: am 29.04.2026 heruntergeladene WHO-Rohdaten und Data Dictionary
- `cleaned_data/`: finale Analysedatensätze
- `01_data_cleaning.ipynb`: Datenbereinigung und Erzeugung der Analysedaten
- `02_data_visualization.ipynb`: deskriptive und explorative Visualisierung
- `03_temporal_analysis.ipynb`: vertiefende zeitliche Analyse und Regressionen
- `streamlit/app.py`: interaktives Dashboard

## Installation

Python 3.11 oder neuer wird empfohlen. Im Hauptverzeichnis des Projekts:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Streamlit-App starten

Der Startbefehl muss im Hauptverzeichnis ausgeführt werden:

```bash
streamlit run streamlit/app.py
```

Danach ist die App normalerweise unter `http://localhost:8501` erreichbar.

## Reihenfolge der Analyse

Die Notebooks können in der nummerierten Reihenfolge ausgeführt werden. Das
Cleaning-Notebook liest die Dateien aus `data/` und schreibt die Ergebnisse nach
`cleaned_data/`. Die weiteren Notebooks und die Streamlit-App verwenden diese
bereinigten Dateien.

## Zentrale Einordnung

Im untersuchten Zeitraum zeigte sich kein stabiler Zusammenhang zwischen den
Screening- beziehungsweise TPT-Raten und den Zielvariablen im Folgejahr. Der
zeitliche Verlauf der gemeldeten TB-Fälle wurde deutlich durch die Jahre im Umfeld
der COVID-19-Pandemie geprägt. Gemeldete Fälle sind nicht mit der tatsächlichen
TB-Inzidenz gleichzusetzen; die Analyse erlaubt keine kausalen Schlussfolgerungen.

## Datenquelle

World Health Organization, Global Programme on Tuberculosis and Lung Health:
<https://www.who.int/teams/global-programme-on-tuberculosis-and-lung-health/data>
(abgerufen am 29.04.2026).
