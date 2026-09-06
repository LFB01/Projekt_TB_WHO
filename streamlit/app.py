from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from scipy.stats import friedmanchisquare


st.set_page_config(
    page_title="WHO-Tuberkulose-Dashboard",
    page_icon="🦠",
    layout="wide",
)

# Die Tab-Leiste bleibt beim Scrollen unterhalb der Streamlit-Kopfzeile sichtbar.
st.markdown(
    """
    <style>
        /*
        In Streamlit 1.51 darf nicht die tab-list selbst sticky sein:
        Ihr direkter Elterncontainer ist nur so hoch wie die Leiste und begrenzt
        dadurch jede Sticky-Bewegung. Stattdessen wird dieser Elterncontainer
        ausgewählt; dessen Elternteil umfasst auch den gesamten Tab-Inhalt.
        */
        div[data-testid="stTabs"] div[data-baseweb="tab-list"] {
            position: relative;
        }

        div[data-testid="stTabs"] div:has(> div[data-baseweb="tab-list"]) {
            position: sticky;
            top: 3.75rem;
            z-index: 1000;
            background-color: var(--background-color, white);
            border-bottom: 1px solid rgba(128, 128, 128, 0.25);
            padding-top: 0.25rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# Der Ordner, in dem diese app.py liegt.
APP_DIR = Path(__file__).resolve().parent

# Der Ordner mit den final bereinigten CSV-Dateien liegt eine Ebene höher.
CLEANED_DATA_DIR = APP_DIR.parent / "cleaned_data"


@st.cache_data
def load_data():
    """Lädt die vier bereinigten Analysedatensätze."""
    tb_all = pd.read_csv(CLEANED_DATA_DIR / "tb_analysis_cleaned.csv")
    tb_cases = pd.read_csv(CLEANED_DATA_DIR / "tb_cases_analysis_cleaned.csv")
    tb_resistance = pd.read_csv(CLEANED_DATA_DIR / "tb_dr_analysis_cleaned.csv")
    tb_outcomes = pd.read_csv(CLEANED_DATA_DIR / "tb_outcome_analysis_cleaned.csv")

    return tb_all, tb_cases, tb_resistance, tb_outcomes


tb_all, tb_cases, tb_resistance, tb_outcomes = load_data()

st.title("Tuberkulose-Screening und Erkrankungen im Folgejahr")

tab_overview, tab_time, tab_cases, tab_resistance, tab_outcomes = st.tabs(
    [
        "Überblick",
        "Zeitlicher Einfluss",
        "Fallzahlen",
        "Resistenzen",
        "Therapieergebnisse",
    ]
)

with tab_overview:
    st.markdown(
        """
    Diese Anwendung untersucht öffentlich verfügbare WHO-Daten zur Tuberkulose.

    **Forschungsfragen**

    1. Gehen höhere Raten von Kontaktpersonen-Screening und Tuberkulose-Prävention
       in einem Jahr mit einer günstigeren Entwicklung der gemeldeten TB-Fälle im
       Folgejahr einher?
    2. Gehen höhere Screening- und Präventionsraten mit niedrigeren Raten von
       Rifampicin-resistenter und multiresistenter Tuberkulose im Folgejahr einher?
    3. Gehen höhere Screening- und Präventionsraten mit besseren
       Therapieergebnissen im Folgejahr einher?
    """
    )

    st.info(
        "Die WHO-Daten enthalten gemeldete TB-Fälle. Diese sind nicht gleichbedeutend "
        "mit der tatsächlichen TB-Inzidenz, da sie auch von Diagnostik, Fallfindung "
        "und Meldesystemen abhängen."
    )

    st.subheader("Datenbasis")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Länder und Gebiete", tb_all["iso3"].nunique())
    col2.metric("Beobachtungsjahre", f'{tb_all["year"].min()}–{tb_all["year"].max()}')
    col3.metric("Länder-Jahr-Beobachtungen", len(tb_all))
    col4.metric("WHO-Regionen", tb_all["g_whoregion"].nunique())

    st.markdown(
        f"""
    Für die drei Fragestellungen wurden aus dem bereinigten Gesamtdatensatz getrennte
    Analysedatensätze gebildet:

    - **Fallzahlen:** {len(tb_cases)} Länder-Jahr-Beobachtungen
    - **Resistenzen:** {len(tb_resistance)} Länder-Jahr-Beobachtungen
    - **Therapieergebnisse:** {len(tb_outcomes)} Länder-Jahr-Beobachtungen

    Die Trennung verhindert, dass eine fehlende Zielvariable aus einem Themenbereich
    unnötig Beobachtungen aus einem anderen Themenbereich ausschließt.
    """
    )

case_preview = tb_cases[
    [
        "country",
        "year",
        "g_whoregion",
        "contact_screening_rate",
        "tpt_start_rate",
        "tpt_completion_rate",
        "c_newinc",
        "c_newinc_next_year",
        "c_newinc_percent_change_next_year",
    ]
].copy()

rate_columns = [
    "contact_screening_rate",
    "tpt_start_rate",
    "tpt_completion_rate",
]
case_preview[rate_columns] = case_preview[rate_columns] * 100

case_preview = case_preview.rename(
    columns={
        "country": "Land/Gebiet",
        "year": "Ausgangsjahr",
        "g_whoregion": "WHO-Region",
        "contact_screening_rate": "Kontaktpersonen-Screening (%)",
        "tpt_start_rate": "Beginn einer präventiven Therapie (%)",
        "tpt_completion_rate": "Abschluss einer präventiven Therapie (%)",
        "c_newinc": "Gemeldete TB-Fälle",
        "c_newinc_next_year": "Gemeldete TB-Fälle im Folgejahr",
        "c_newinc_percent_change_next_year": "Veränderung im Folgejahr (%)",
    }
)

with tab_cases:
    st.subheader("Screening, Prävention und gemeldete TB-Fälle")

    st.markdown(
        """
    **Teilfrage:** Gehen höhere Raten von Kontaktpersonen-Screening und
    Tuberkulose-Prävention in einem Jahr mit einer günstigeren Entwicklung der
    gemeldeten TB-Fälle im Folgejahr einher?

    Als mögliche Einflussgrößen werden drei Raten aus dem jeweiligen
    **Ausgangsjahr** betrachtet:

    - **Kontaktpersonen-Screening:** Anteil der identifizierten Kontaktpersonen,
      die auf Tuberkulose untersucht wurden.
    - **Beginn einer Tuberkulose-Prävention (TPT):** Anteil der identifizierten
      Kontaktpersonen, die eine Tuberkulose-Prävention begonnen haben.
    - **Abschluss einer Tuberkulose-Prävention (TPT):** Anteil der begonnenen
      präventiven Behandlungen, die abgeschlossen wurden.

    Die Zielvariable ist die **prozentuale Veränderung der gemeldeten TB-Fälle
    vom Ausgangsjahr zum Folgejahr**:

    `((Fälle im Folgejahr − Fälle im Ausgangsjahr) / Fälle im Ausgangsjahr) × 100`

    Ein negativer Wert steht für weniger gemeldete Fälle im Folgejahr, ein
    positiver Wert für mehr gemeldete Fälle.
    """
    )

    st.info(
        "Ein Rückgang gemeldeter Fälle bedeutet nicht automatisch einen Rückgang "
        "der tatsächlichen TB-Inzidenz. Ebenso kann intensivere Fallfindung "
        "zunächst zu mehr gemeldeten Fällen führen."
    )

    case_exposure_options = {
        "Kontaktpersonen-Screening": "contact_screening_rate",
        "Beginn einer Tuberkulose-Prävention (TPT)": "tpt_start_rate",
        "Abschluss einer Tuberkulose-Prävention (TPT)": "tpt_completion_rate",
    }

    region_options = {
        "Alle WHO-Regionen": None,
        "Afrika": "AFR",
        "Amerika": "AMR",
        "Östlicher Mittelmeerraum": "EMR",
        "Europa": "EUR",
        "Südostasien": "SEA",
        "Westpazifik": "WPR",
    }

    control1, control2 = st.columns(2)
    with control1:
        selected_case_exposure_label = st.selectbox(
            "Welche Ausgangsrate möchten Sie untersuchen?",
            options=case_exposure_options.keys(),
        )
    with control2:
        selected_region_label = st.selectbox(
            "Welche WHO-Region möchten Sie betrachten?",
            options=region_options.keys(),
        )

    selected_case_exposure = case_exposure_options[selected_case_exposure_label]
    selected_region = region_options[selected_region_label]

    selected_edge_flag = f"{selected_case_exposure}_edge_flag"
    case_filter = ~tb_cases["low_c_newinc_flag"] & ~tb_cases[selected_edge_flag]
    if selected_region is not None:
        case_filter &= tb_cases["g_whoregion"].eq(selected_region)

    case_plot_data = tb_cases[case_filter][
        [
            "country",
            "year",
            "g_whoregion",
            selected_case_exposure,
            "c_newinc_percent_change_next_year",
        ]
    ].dropna()

    case_plot_data = case_plot_data.rename(
        columns={
            "country": "Land/Gebiet",
            "year": "Ausgangsjahr",
            "g_whoregion": "WHO-Region",
            selected_case_exposure: "Ausgangsrate (%)",
            "c_newinc_percent_change_next_year": "Fallzahlveränderung im Folgejahr (%)",
        }
    )
    case_plot_data["Ausgangsrate (%)"] *= 100

    show_trendline = st.checkbox("Lineare Trendlinie anzeigen")

    points = (
        alt.Chart(case_plot_data)
        .mark_circle(size=60, opacity=0.55)
        .encode(
            x=alt.X(
                field="Ausgangsrate (%)",
                type="quantitative",
                title=f"{selected_case_exposure_label} (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            y=alt.Y(
                field="Fallzahlveränderung im Folgejahr (%)",
                type="quantitative",
                title="Fallzahlveränderung im Folgejahr (%)",
            ),
            tooltip=[
                alt.Tooltip("Land/Gebiet:N"),
                alt.Tooltip("Ausgangsjahr:O"),
                alt.Tooltip("WHO-Region:N"),
                alt.Tooltip("Ausgangsrate (%):Q", format=".1f"),
                alt.Tooltip(
                    "Fallzahlveränderung im Folgejahr (%):Q",
                    format=".1f",
                ),
            ],
        )
    )

    chart = points
    if show_trendline:
        trendline = (
            alt.Chart(case_plot_data)
            .transform_regression(
                "Ausgangsrate (%)",
                "Fallzahlveränderung im Folgejahr (%)",
            )
            .mark_line(color="#d62728", size=3)
            .encode(
                x=alt.X(
                    field="Ausgangsrate (%)",
                    type="quantitative",
                    scale=alt.Scale(domain=[0, 100]),
                ),
                y=alt.Y(
                    field="Fallzahlveränderung im Folgejahr (%)",
                    type="quantitative",
                ),
            )
        )
        chart = points + trendline

    st.altair_chart(chart.properties(height=500), use_container_width=True)

    spearman_rho = case_plot_data[
        ["Ausgangsrate (%)", "Fallzahlveränderung im Folgejahr (%)"]
    ].corr(method="spearman").iloc[0, 1]

    metric1, metric2 = st.columns(2)
    metric1.metric("Dargestellte Beobachtungen", len(case_plot_data))
    metric2.metric("Spearman-Korrelation (ρ)", f"{spearman_rho:.2f}")

    st.caption(
        "Ausgeschlossen sind fehlende Werte, Ausgangsjahre mit weniger als zehn "
        "gemeldeten TB-Fällen sowie Randwerte von genau 0 % oder 100 % bei der "
        "ausgewählten Ausgangsrate. Die Korrelation beschreibt einen statistischen "
        "Zusammenhang, aber keine Kausalität."
    )

    st.markdown(
        """
    **Einordnung des Ergebnisses:** Im Gesamtdatensatz zeigt sich kein stabiler
    Zusammenhang zwischen den untersuchten Screening- beziehungsweise
    Präventionsraten und der Veränderung der gemeldeten TB-Fälle im Folgejahr.
    Einzelne regionale Korrelationen können stärker ausfallen, unterscheiden sich
    jedoch in ihrer Richtung und beruhen teilweise auf deutlich weniger
    Beobachtungen. Sie sind deshalb nicht als belastbarer Effekt zu interpretieren.

    """
    )

    with st.expander("Fallzahl-Datensatz anzeigen"):
        st.dataframe(case_preview, hide_index=True)

with tab_resistance:
    st.subheader("Screening, Prävention und resistente Tuberkulose")

    st.markdown(
        """
    **Teilfrage:** Gehen höhere Raten von Kontaktpersonen-Screening und
    Tuberkulose-Prävention in einem Jahr mit niedrigeren Resistenzraten bei neu
    diagnostizierten TB-Fällen im Folgejahr einher?

    Als mögliche Einflussgrößen werden erneut das Kontaktpersonen-Screening, der
    Beginn einer Tuberkulose-Prävention und deren Abschluss im jeweiligen
    **Ausgangsjahr** betrachtet.

    Untersucht werden zwei Zielvariablen aus dem **Folgejahr**:

    - **Rifampicin-Resistenzrate:** Anteil der auf Rifampicin getesteten neuen
      bakteriologisch bestätigten pulmonalen TB-Fälle mit nachgewiesener
      Rifampicin-Resistenz.
    - **MDR-TB-Rate:** Anteil der auf Rifampicin und Isoniazid getesteten neuen
      TB-Fälle mit einer Resistenz gegen beide Wirkstoffe. Diese Kombination wird
      als multiresistente Tuberkulose (MDR-TB) bezeichnet.
    """
    )

    st.info(
        "Die Resistenzraten beziehen sich nur auf Fälle mit dokumentiertem "
        "Resistenztestergebnis. Unterschiede in Testabdeckung, Falldefinitionen "
        "und Meldesystemen können die internationale Vergleichbarkeit beeinflussen."
    )

    resistance_exposure_options = {
        "Kontaktpersonen-Screening": "contact_screening_rate",
        "Beginn einer Tuberkulose-Prävention (TPT)": "tpt_start_rate",
        "Abschluss einer Tuberkulose-Prävention (TPT)": "tpt_completion_rate",
    }
    resistance_target_options = {
        "Rifampicin-Resistenz": "rr_rate_new_next_year",
        "MDR-TB": "mdr_rate_new_next_year",
    }

    resistance_control1, resistance_control2 = st.columns(2)
    with resistance_control1:
        selected_resistance_exposure_label = st.selectbox(
            "Welche Ausgangsrate möchten Sie untersuchen?",
            options=resistance_exposure_options.keys(),
            key="resistance_exposure",
        )
    with resistance_control2:
        selected_resistance_target_label = st.selectbox(
            "Welche Resistenzrate möchten Sie betrachten?",
            options=resistance_target_options.keys(),
            key="resistance_target",
        )

    selected_resistance_exposure = resistance_exposure_options[
        selected_resistance_exposure_label
    ]
    selected_resistance_target = resistance_target_options[
        selected_resistance_target_label
    ]

    resistance_edge_flag = f"{selected_resistance_exposure}_edge_flag"
    resistance_plot_data = tb_resistance[~tb_resistance[resistance_edge_flag]][
        [
            "country",
            "year",
            "g_whoregion",
            selected_resistance_exposure,
            selected_resistance_target,
        ]
    ].dropna()

    resistance_plot_data = resistance_plot_data.rename(
        columns={
            "country": "Land/Gebiet",
            "year": "Ausgangsjahr",
            "g_whoregion": "WHO-Region",
            selected_resistance_exposure: "Ausgangsrate (%)",
            selected_resistance_target: "Resistenzrate im Folgejahr (%)",
        }
    )
    resistance_plot_data[
        ["Ausgangsrate (%)", "Resistenzrate im Folgejahr (%)"]
    ] *= 100

    show_resistance_trendline = st.checkbox(
        "Lineare Trendlinie anzeigen",
        key="resistance_trendline",
    )

    resistance_points = (
        alt.Chart(resistance_plot_data)
        .mark_circle(size=60, opacity=0.55)
        .encode(
            x=alt.X(
                field="Ausgangsrate (%)",
                type="quantitative",
                title=f"{selected_resistance_exposure_label} (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            y=alt.Y(
                field="Resistenzrate im Folgejahr (%)",
                type="quantitative",
                title=f"{selected_resistance_target_label} im Folgejahr (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            tooltip=[
                alt.Tooltip("Land/Gebiet:N"),
                alt.Tooltip("Ausgangsjahr:O"),
                alt.Tooltip("WHO-Region:N"),
                alt.Tooltip("Ausgangsrate (%):Q", format=".1f"),
                alt.Tooltip("Resistenzrate im Folgejahr (%):Q", format=".1f"),
            ],
        )
    )

    resistance_chart = resistance_points
    if show_resistance_trendline:
        resistance_trendline = (
            alt.Chart(resistance_plot_data)
            .transform_regression(
                "Ausgangsrate (%)",
                "Resistenzrate im Folgejahr (%)",
            )
            .mark_line(color="#d62728", size=3)
            .encode(
                x=alt.X(
                    field="Ausgangsrate (%)",
                    type="quantitative",
                    scale=alt.Scale(domain=[0, 100]),
                ),
                y=alt.Y(
                    field="Resistenzrate im Folgejahr (%)",
                    type="quantitative",
                    scale=alt.Scale(domain=[0, 100]),
                ),
            )
        )
        resistance_chart = resistance_points + resistance_trendline

    st.altair_chart(
        resistance_chart.properties(height=500),
        use_container_width=True,
    )

    resistance_spearman_rho = resistance_plot_data[
        ["Ausgangsrate (%)", "Resistenzrate im Folgejahr (%)"]
    ].corr(method="spearman").iloc[0, 1]

    resistance_metric1, resistance_metric2 = st.columns(2)
    resistance_metric1.metric(
        "Dargestellte Beobachtungen",
        len(resistance_plot_data),
    )
    resistance_metric2.metric(
        "Spearman-Korrelation (ρ)",
        f"{resistance_spearman_rho:.2f}",
    )

    st.caption(
        "Ausgeschlossen sind fehlende Werte und Randwerte von genau 0 % oder "
        "100 % bei der ausgewählten Ausgangsrate. Die Korrelation beschreibt "
        "einen statistischen Zusammenhang, aber keine Kausalität."
    )

    st.markdown(
        """
    **Einordnung des Ergebnisses:** Es zeigt sich kein stabiler Zusammenhang
    zwischen den untersuchten Screening- beziehungsweise Präventionsraten und den
    Rifampicin- oder MDR-TB-Raten im Folgejahr. Einzelne Korrelationen fallen
    stärker aus, wechseln aber je nach Variable und Teilgruppe in ihrer Richtung.

    Die Ergebnisse sind zusätzlich durch unterschiedliche Resistenztestung und
    Datenabdeckung zwischen Ländern eingeschränkt. Aus dieser Analyse lässt sich
    daher weder ein schützender noch ein schädlicher kausaler Einfluss von
    Screening oder TPT auf die Resistenzraten ableiten.
    """
    )

    resistance_display = tb_resistance[
        [
            "country",
            "year",
            "g_whoregion",
            "contact_screening_rate",
            "tpt_start_rate",
            "tpt_completion_rate",
            "rr_rate_new_next_year",
            "mdr_rate_new_next_year",
        ]
    ].copy()

    resistance_rate_columns = [
        "contact_screening_rate",
        "tpt_start_rate",
        "tpt_completion_rate",
        "rr_rate_new_next_year",
        "mdr_rate_new_next_year",
    ]
    resistance_display[resistance_rate_columns] *= 100

    resistance_display = resistance_display.rename(
        columns={
            "country": "Land/Gebiet",
            "year": "Ausgangsjahr",
            "g_whoregion": "WHO-Region",
            "contact_screening_rate": "Kontaktpersonen-Screening (%)",
            "tpt_start_rate": "Beginn einer präventiven Therapie (%)",
            "tpt_completion_rate": "Abschluss einer präventiven Therapie (%)",
            "rr_rate_new_next_year": "Rifampicin-Resistenz im Folgejahr (%)",
            "mdr_rate_new_next_year": "MDR-TB im Folgejahr (%)",
        }
    )

    with st.expander("Resistenz-Datensatz anzeigen"):
        st.dataframe(resistance_display, hide_index=True)

with tab_outcomes:
    st.subheader("Screening, Prävention und Therapieergebnisse")

    st.markdown(
        """
    **Teilfrage:** Gehen höhere Raten von Kontaktpersonen-Screening und
    Tuberkulose-Prävention in einem Jahr mit besseren Therapieergebnissen im
    Folgejahr einher?

    Als mögliche Einflussgrößen werden erneut das Kontaktpersonen-Screening, der
    Beginn einer Tuberkulose-Prävention und deren Abschluss im jeweiligen
    **Ausgangsjahr** betrachtet.

    Untersucht werden drei Zielvariablen aus dem **Folgejahr**:

    - **Therapieerfolgsrate:** Anteil der erfolgreich behandelten Personen an der
      dokumentierten Behandlungskohorte.
    - **Todesrate:** Anteil der während der Behandlung verstorbenen Personen an
      der dokumentierten Behandlungskohorte.
    - **Nicht erfolgreiche Therapieergebnisse:** zusammengefasster Anteil von
      Therapieversagen, Tod und Behandlungsabbruch beziehungsweise Verlust aus
      der Nachverfolgung an der dokumentierten Behandlungskohorte.
    """
    )

    st.info(
        "Die Zielvariablen beschreiben Ergebnisse dokumentierter "
        "Behandlungskohorten. Unterschiede in Kohortengröße, Erfassung und "
        "Berichtspraxis können die Vergleichbarkeit zwischen Ländern beeinflussen."
    )

    outcome_exposure_options = {
        "Kontaktpersonen-Screening": "contact_screening_rate",
        "Beginn einer Tuberkulose-Prävention (TPT)": "tpt_start_rate",
        "Abschluss einer Tuberkulose-Prävention (TPT)": "tpt_completion_rate",
    }
    outcome_target_options = {
        "Therapieerfolg": "treatment_success_rate_next_year",
        "Todesrate": "treatment_death_rate_next_year",
        "Nicht erfolgreiche Therapieergebnisse": "unsuccessful_rate_next_year",
    }

    outcome_control1, outcome_control2 = st.columns(2)
    with outcome_control1:
        selected_outcome_exposure_label = st.selectbox(
            "Welche Ausgangsrate möchten Sie untersuchen?",
            options=outcome_exposure_options.keys(),
            key="outcome_exposure",
        )
    with outcome_control2:
        selected_outcome_target_label = st.selectbox(
            "Welches Therapieergebnis möchten Sie betrachten?",
            options=outcome_target_options.keys(),
            key="outcome_target",
        )

    selected_outcome_exposure = outcome_exposure_options[
        selected_outcome_exposure_label
    ]
    selected_outcome_target = outcome_target_options[selected_outcome_target_label]

    outcome_edge_flag = f"{selected_outcome_exposure}_edge_flag"
    outcome_filter = ~tb_outcomes[outcome_edge_flag]
    targets_with_upper_edge_exclusion = {
        "treatment_success_rate_next_year",
        "unsuccessful_rate_next_year",
    }
    if selected_outcome_target in targets_with_upper_edge_exclusion:
        outcome_filter &= ~tb_outcomes[selected_outcome_target].eq(1)

    outcome_plot_data = tb_outcomes[outcome_filter][
        [
            "country",
            "year",
            "g_whoregion",
            "newrel_coh_next_year",
            selected_outcome_exposure,
            selected_outcome_target,
        ]
    ].dropna()

    outcome_plot_data = outcome_plot_data.rename(
        columns={
            "country": "Land/Gebiet",
            "year": "Ausgangsjahr",
            "g_whoregion": "WHO-Region",
            "newrel_coh_next_year": "Behandlungskohorte im Folgejahr",
            selected_outcome_exposure: "Ausgangsrate (%)",
            selected_outcome_target: "Therapieergebnis im Folgejahr (%)",
        }
    )
    outcome_plot_data[
        ["Ausgangsrate (%)", "Therapieergebnis im Folgejahr (%)"]
    ] *= 100

    show_outcome_trendline = st.checkbox(
        "Lineare Trendlinie anzeigen",
        key="outcome_trendline",
    )

    outcome_points = (
        alt.Chart(outcome_plot_data)
        .mark_circle(size=60, opacity=0.55)
        .encode(
            x=alt.X(
                field="Ausgangsrate (%)",
                type="quantitative",
                title=f"{selected_outcome_exposure_label} (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            y=alt.Y(
                field="Therapieergebnis im Folgejahr (%)",
                type="quantitative",
                title=f"{selected_outcome_target_label} im Folgejahr (%)",
                scale=alt.Scale(domain=[0, 100]),
            ),
            tooltip=[
                alt.Tooltip("Land/Gebiet:N"),
                alt.Tooltip("Ausgangsjahr:O"),
                alt.Tooltip("WHO-Region:N"),
                alt.Tooltip("Behandlungskohorte im Folgejahr:Q", format=",.0f"),
                alt.Tooltip("Ausgangsrate (%):Q", format=".1f"),
                alt.Tooltip("Therapieergebnis im Folgejahr (%):Q", format=".1f"),
            ],
        )
    )

    outcome_chart = outcome_points
    if show_outcome_trendline:
        outcome_trendline = (
            alt.Chart(outcome_plot_data)
            .transform_regression(
                "Ausgangsrate (%)",
                "Therapieergebnis im Folgejahr (%)",
            )
            .mark_line(color="#d62728", size=3)
            .encode(
                x=alt.X(
                    field="Ausgangsrate (%)",
                    type="quantitative",
                    scale=alt.Scale(domain=[0, 100]),
                ),
                y=alt.Y(
                    field="Therapieergebnis im Folgejahr (%)",
                    type="quantitative",
                    scale=alt.Scale(domain=[0, 100]),
                ),
            )
        )
        outcome_chart = outcome_points + outcome_trendline

    st.altair_chart(
        outcome_chart.properties(height=500),
        use_container_width=True,
    )

    outcome_spearman_rho = outcome_plot_data[
        ["Ausgangsrate (%)", "Therapieergebnis im Folgejahr (%)"]
    ].corr(method="spearman").iloc[0, 1]

    outcome_metric1, outcome_metric2 = st.columns(2)
    outcome_metric1.metric(
        "Dargestellte Beobachtungen",
        len(outcome_plot_data),
    )
    outcome_metric2.metric(
        "Spearman-Korrelation (ρ)",
        f"{outcome_spearman_rho:.2f}",
    )

    outcome_exclusion_text = (
        " Zusätzlich wurden Zielwerte von genau 100 % ausgeschlossen."
        if selected_outcome_target in targets_with_upper_edge_exclusion
        else ""
    )
    st.caption(
        "Ausgeschlossen sind fehlende Werte und Randwerte von genau 0 % oder "
        "100 % bei der ausgewählten Ausgangsrate."
        f"{outcome_exclusion_text} Die Korrelation beschreibt einen statistischen "
        "Zusammenhang, aber keine Kausalität."
    )

    st.markdown(
        """
    **Einordnung des Ergebnisses:** Auch bei den Therapieergebnissen zeigt sich
    kein stabiler Zusammenhang mit den untersuchten Screening- und
    Präventionsraten. Beim Abschluss einer TPT bestehen höchstens schwache Hinweise
    auf einen Zusammenhang mit höherem Therapieerfolg und weniger nicht
    erfolgreichen Verläufen. Das Muster ist jedoch nicht stark oder konsistent
    genug, um daraus eine allgemeine Aussage für alle Länder abzuleiten.

    Die Analyse beruht auf aggregierten Länderwerten und unterschiedlich großen
    Behandlungskohorten. Sie erlaubt daher keine Aussage darüber, ob eine konkrete
    präventive Behandlung das spätere Therapieergebnis einzelner Personen
    verursacht oder verbessert hat.
    """
    )

    outcome_display = tb_outcomes[
        [
            "country",
            "year",
            "g_whoregion",
            "contact_screening_rate",
            "tpt_start_rate",
            "tpt_completion_rate",
            "newrel_coh_next_year",
            "treatment_success_rate_next_year",
            "treatment_death_rate_next_year",
            "unsuccessful_rate_next_year",
        ]
    ].copy()

    outcome_rate_columns = [
        "contact_screening_rate",
        "tpt_start_rate",
        "tpt_completion_rate",
        "treatment_success_rate_next_year",
        "treatment_death_rate_next_year",
        "unsuccessful_rate_next_year",
    ]
    outcome_display[outcome_rate_columns] *= 100

    outcome_display = outcome_display.rename(
        columns={
            "country": "Land/Gebiet",
            "year": "Ausgangsjahr",
            "g_whoregion": "WHO-Region",
            "contact_screening_rate": "Kontaktpersonen-Screening (%)",
            "tpt_start_rate": "Beginn einer präventiven Therapie (%)",
            "tpt_completion_rate": "Abschluss einer präventiven Therapie (%)",
            "newrel_coh_next_year": "Behandlungskohorte im Folgejahr",
            "treatment_success_rate_next_year": "Therapieerfolg im Folgejahr (%)",
            "treatment_death_rate_next_year": "Todesrate im Folgejahr (%)",
            "unsuccessful_rate_next_year": "Nicht erfolgreiche Ergebnisse im Folgejahr (%)",
        }
    )

    with st.expander("Therapieergebnis-Datensatz anzeigen"):
        st.dataframe(outcome_display, hide_index=True)

with tab_time:
    st.subheader("Zeitliche Entwicklung der gemeldeten TB-Fälle")

    st.markdown(
        """
    Die ursprünglichen Analysen zeigten keinen stabilen Zusammenhang zwischen
    Screening beziehungsweise TPT und den Zielvariablen. Deshalb wurde zusätzlich
    untersucht, ob sich die Veränderung der gemeldeten TB-Fälle stärker nach dem
    **Kalenderjahr** unterscheidet.

    Das angegebene Jahr ist jeweils das **Ausgangsjahr**. Die dargestellte
    Veränderung bezieht sich auf das anschließende Kalenderjahr:

    - **2019:** Veränderung der Fallmeldungen von 2019 zu 2020
    - **2020:** Veränderung von 2020 zu 2021
    - **2021:** Veränderung von 2021 zu 2022
    - **2022:** Veränderung von 2022 zu 2023
    - **2023:** Veränderung von 2023 zu 2024

    Für einen besser vergleichbaren Zeitverlauf wurde zusätzlich eine
    **Subanalyse der 70 Länder und Gebiete mit vollständigen Beobachtungen für
    alle fünf Jahresübergänge** durchgeführt. Diese Länder und Gebiete weisen
    in jedem der fünf Ausgangsjahre mindestens zehn gemeldete TB-Fälle auf.
    """
    )

    st.info(
        "Während der COVID-19-Pandemie waren TB-Diagnostik, Versorgung und "
        "Fallmeldung erheblich beeinträchtigt. Ein Rückgang der gemeldeten Fälle "
        "im Jahr 2020 ist daher eher Ausdruck einer Untererfassung statt einer tatsächlichen "
        "Abnahme der TB-Inzidenz."
    )

    temporal_panel = tb_cases[tb_cases["temporal_analysis_cohort_flag"]][
        [
            "country",
            "year",
            "g_whoregion",
            "c_newinc_percent_change_next_year",
        ]
    ].dropna()

    temporal_panel["Vergleichszeitraum"] = temporal_panel["year"].apply(
        lambda year: f"{int(year)} → {int(year) + 1}"
    )

    median_change_by_year = (
        temporal_panel.groupby("year", as_index=False)[
            "c_newinc_percent_change_next_year"
        ]
        .median()
        .rename(
            columns={
                "year": "Ausgangsjahr",
                "c_newinc_percent_change_next_year": "Mediane Fallzahlveränderung (%)",
            }
        )
    )
    median_change_by_year["Vergleichszeitraum"] = median_change_by_year[
        "Ausgangsjahr"
    ].apply(lambda year: f"{int(year)} → {int(year) + 1}")

    median_bars = (
        alt.Chart(median_change_by_year)
        .mark_bar(size=55)
        .encode(
            x=alt.X(
                field="Vergleichszeitraum",
                type="ordinal",
                title="Vergleichszeitraum",
                sort="ascending",
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y(
                field="Mediane Fallzahlveränderung (%)",
                type="quantitative",
                title="Median der Veränderung gemeldeter TB-Fälle (%)",
            ),
            color=alt.condition(
                alt.datum["Mediane Fallzahlveränderung (%)"] < 0,
                alt.value("#4c78a8"),
                alt.value("#e45756"),
            ),
            tooltip=[
                alt.Tooltip("Vergleichszeitraum:N"),
                alt.Tooltip(
                    "Mediane Fallzahlveränderung (%):Q",
                    format=".1f",
                ),
            ],
        )
    )

    median_labels = (
        alt.Chart(median_change_by_year)
        .mark_text(dy=-10, fontSize=14, fontWeight="bold")
        .encode(
            x=alt.X(
                field="Vergleichszeitraum",
                type="ordinal",
                sort="ascending",
            ),
            y=alt.Y(
                field="Mediane Fallzahlveränderung (%)",
                type="quantitative",
            ),
            text=alt.Text(
                field="Mediane Fallzahlveränderung (%)",
                type="quantitative",
                format="+.1f",
            ),
        )
    )

    zero_line = alt.Chart(pd.DataFrame({"Null": [0]})).mark_rule(
        color="#444444",
        strokeWidth=1,
    ).encode(y="Null:Q")

    median_time_chart = (median_bars + median_labels + zero_line).properties(
        title={
            "text": "Wie veränderten sich die gemeldeten TB-Fälle?",
            "subtitle": [
                "Median der Veränderung gegenüber dem Vorjahr"
            ],
        },
        height=450,
    )

    st.altair_chart(
        median_time_chart,
        use_container_width=True,
    )

    st.caption(
        "Ein negativer Wert bedeutet, dass die gemeldeten TB-Fälle im Median "
        "zurückgingen; ein positiver Wert bedeutet einen medianen Anstieg. "
        "Blau kennzeichnet einen Rückgang, Rot einen Anstieg."
    )

    temporal_panel["Verlauf"] = temporal_panel[
        "c_newinc_percent_change_next_year"
    ].apply(
        lambda value: (
            "Rückgang"
            if value < -3
            else "Anstieg"
            if value > 3
            else "Stabil (−3 bis +3 %)"
        )
    )

    direction_shares = (
        temporal_panel.groupby(
            ["Vergleichszeitraum", "Verlauf"],
            as_index=False,
        )
        .size()
        .rename(columns={"size": "Länder und Gebiete"})
    )
    direction_shares["Anteil (%)"] = (
        direction_shares["Länder und Gebiete"]
        / direction_shares.groupby("Vergleichszeitraum")[
            "Länder und Gebiete"
        ].transform("sum")
        * 100
    )

    period_order = [
        "2019 → 2020",
        "2020 → 2021",
        "2021 → 2022",
        "2022 → 2023",
        "2023 → 2024",
    ]
    direction_order = ["Rückgang", "Stabil (−3 bis +3 %)", "Anstieg"]

    direction_chart = (
        alt.Chart(direction_shares)
        .mark_bar()
        .encode(
            x=alt.X(
                field="Vergleichszeitraum",
                type="ordinal",
                title="Vergleichszeitraum",
                sort=period_order,
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y(
                field="Anteil (%)",
                type="quantitative",
                title="Anteil der Länder und Gebiete (%)",
                stack="zero",
                scale=alt.Scale(domain=[0, 100]),
            ),
            color=alt.Color(
                field="Verlauf",
                type="nominal",
                title="Veränderung der Meldungen",
                sort=direction_order,
                scale=alt.Scale(
                    domain=direction_order,
                    range=["#4c78a8", "#b8b8b8", "#e45756"],
                ),
            ),
            order=alt.Order(field="Verlauf", sort="ascending"),
            tooltip=[
                alt.Tooltip("Vergleichszeitraum:N"),
                alt.Tooltip("Verlauf:N"),
                alt.Tooltip("Länder und Gebiete:Q"),
                alt.Tooltip("Anteil (%):Q", format=".1f"),
            ],
        )
        .properties(
            title={
                "text": "In wie vielen Ländern sanken oder stiegen die Meldungen?",
                "subtitle": [
                    "Verteilung der 70 Länder und Gebiete mit Beobachtungen in allen Jahren"
                ],
            },
            height=420,
        )
    )

    st.altair_chart(direction_chart, use_container_width=True)

    st.caption(
        "Als stabil gilt eine Veränderung zwischen −3 % und +3 %. Jeder Balken "
        "umfasst dieselben 70 Länder und Gebiete mit Beobachtungen in allen Jahren."
    )

    region_names = {
        "AFR": "Afrika",
        "AMR": "Amerika",
        "EMR": "Östlicher Mittelmeerraum",
        "EUR": "Europa",
        "SEA": "Südostasien",
        "WPR": "Westpazifik",
    }
    regional_medians = (
        temporal_panel.groupby(
            ["g_whoregion", "Vergleichszeitraum"],
            as_index=False,
        )["c_newinc_percent_change_next_year"]
        .median()
        .rename(
            columns={
                "g_whoregion": "WHO-Region",
                "c_newinc_percent_change_next_year": "Mediane Veränderung (%)",
            }
        )
    )
    regional_medians["WHO-Region"] = regional_medians["WHO-Region"].map(
        region_names
    )

    heatmap_base = alt.Chart(regional_medians).encode(
        x=alt.X(
            field="Vergleichszeitraum",
            type="ordinal",
            title="Vergleichszeitraum",
            sort=period_order,
            axis=alt.Axis(labelAngle=0),
        ),
        y=alt.Y(
            field="WHO-Region",
            type="nominal",
            title="WHO-Region",
        ),
    )

    heatmap_tooltip = [
        alt.Tooltip("WHO-Region:N"),
        alt.Tooltip("Vergleichszeitraum:N"),
        alt.Tooltip("Mediane Veränderung (%):Q", format="+.1f"),
    ]

    regional_heatmap = heatmap_base.mark_rect().encode(
        color=alt.Color(
            field="Mediane Veränderung (%)",
            type="quantitative",
            title="Median (%)",
            scale=alt.Scale(scheme="redblue", reverse=True, domainMid=0),
        ),
        tooltip=heatmap_tooltip,
    )

    heatmap_labels = heatmap_base.mark_text(fontSize=13).encode(
        text=alt.Text("Mediane Veränderung (%):Q", format="+.1f"),
        color=alt.value("black"),
        tooltip=heatmap_tooltip,
    )

    st.altair_chart(
        (regional_heatmap + heatmap_labels).properties(
            title={
                "text": "Wie unterschied sich die Entwicklung nach WHO-Region?",
                "subtitle": [
                    "70 Länder und Gebiete mit vollständigen Beobachtungen für alle fünf Jahresübergänge"
                ],
            },
            height=360,
        ),
        use_container_width=True,
    )

    st.caption(
        "Jede Zelle zeigt die mediane Veränderung innerhalb einer WHO-Region und "
        "eines Vergleichszeitraums. Blau steht für Rückgang, Rot für Anstieg."
    )

    st.subheader("Statistische Einordnung")

    friedman_data = temporal_panel.pivot(
        index="country",
        columns="year",
        values="c_newinc_percent_change_next_year",
    ).dropna()
    friedman_years = sorted(friedman_data.columns)
    friedman_result = friedmanchisquare(
        *(friedman_data[year] for year in friedman_years)
    )

    time_metric1, time_metric2 = st.columns(2)
    time_metric1.metric("Friedman-Teststatistik", f"{friedman_result.statistic:.2f}")
    time_metric2.metric(
        "p-Wert",
        "< 0,001" if friedman_result.pvalue < 0.001 else f"{friedman_result.pvalue:.3f}",
    )

    st.markdown(
        f"""
    Der Friedman-Test vergleicht die Fallzahlveränderungen der gleichen
    **{len(friedman_data)} Länder und Gebiete** über alle fünf Zeiträume. Er
    berücksichtigt damit, dass jedes Land wiederholt beobachtet wird. Das Ergebnis
    zeigt, dass sich die zeitlichen Verteilungen statistisch unterscheiden. Der
    Test zeigt jedoch nicht, welche einzelnen Zeiträume sich unterscheiden oder
    wodurch die Unterschiede verursacht wurden.

    In ergänzenden linearen Regressionen wurden die Ausgangsraten schrittweise
    gemeinsam mit dem Kalenderjahr und der WHO-Region betrachtet. Die
    Standardfehler wurden dabei nach Ländern gruppiert.

    - Ohne zeitliche Kontrolle lag das **R² nur zwischen 0,002 und 0,003**.
    - Nach Ergänzung des Kalenderjahres stieg es auf **0,142 bis 0,243**.
    - Mit Kalenderjahr und WHO-Region lag es bei **0,163 bis 0,275**.
    - Die Konfidenzintervalle der Screening- und TPT-Koeffizienten schnitten in
      allen Modellen die Nulllinie.

    **Zentrale Erkenntnis:** Das Kalenderjahr erklärt in diesen Daten deutlich mehr von der
    Fallzahlentwicklung als die untersuchten Screening- und Präventionsraten. Das
    zeitliche Muster stimmt mit den bekannten Auswirkungen der COVID-19-Pandemie
    auf TB-Diagnostik und Fallmeldung überein. Es beweist jedoch nicht, dass COVID-19
    allein alle beobachteten Veränderungen verursacht hat.

    Die folgenden Reiter zeigen die Zusammenhänge von Screening und Prävention
    mit Fallzahlen, Resistenzen und Therapieergebnissen im Detail.
    """
    )
