
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Cardiac ED Journeys",
    page_icon="🏥",
    layout="wide",
)

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(
    r"C:\MIMIC\mimic-iv-ed\extracted\mimic-iv-ed-2.2\ed"
)
PROFILE_PATH = PROJECT_DIR / "data" / "cardiac_candidate_encounters.csv"

PATTERNS = {
    "Chest pain / symptoms": (
        r"chest pain|angina|palpitation"
    ),
    "Myocardial infarction / ischemia": (
        r"myocardial infarction|nstemi|stemi|ischemic heart|"
        r"ischaemic heart|ischemic heart disease|coronary artery disease"
    ),
    "Heart failure": r"heart failure|congestive heart failure",
    "Arrhythmia / rate disorders": (
        r"atrial fibrillation|atrial flutter|arrhythmia|tachycardia|"
        r"bradycardia|supraventricular"
    ),
    "Other cardiovascular conditions": (
        r"cardiac arrest|cardiomyopathy|pericarditis|endocarditis"
    ),
}

VITALS = {
    "heartrate": "Heart rate (bpm)",
    "sbp": "Systolic blood pressure (mmHg)",
    "dbp": "Diastolic blood pressure (mmHg)",
    "o2sat": "Oxygen saturation (%)",
    "resprate": "Respiratory rate (/min)",
    "temperature": "Temperature",
}

st.title("From ED Arrival to Disposition")
st.markdown(
    "### Cardiac-related emergency department encounters"
)
st.write(
    "Explore how demographic characteristics, initial clinical state, "
    "diagnosis groups, and triage relate to ED care. This is an "
    "observational analysis of a keyword-defined cohort."
)


@st.cache_data
def load_data():
    if not PROFILE_PATH.exists():
        raise FileNotFoundError(
            f"Encounter profile not found: {PROFILE_PATH}"
        )

    if not (DATA_DIR / "diagnosis.csv.gz").exists():
        raise FileNotFoundError(
            f"Diagnosis file not found: {DATA_DIR / 'diagnosis.csv.gz'}"
        )

    encounters = pd.read_csv(PROFILE_PATH)

    diagnoses = pd.read_csv(
        DATA_DIR / "diagnosis.csv.gz",
        usecols=["subject_id", "stay_id", "icd_title"],
    )

    edstays = pd.read_csv(
        DATA_DIR / "edstays.csv.gz",
        usecols=[
            "subject_id", "stay_id", "intime", "outtime",
            "gender", "race", "disposition", "hadm_id",
        ],
    )

    # Normalize timestamps and calculate ED length of stay.
    for col in ["intime", "outtime"]:
        if col in encounters.columns:
            encounters[col] = pd.to_datetime(
                encounters[col], errors="coerce"
            )

    if "ed_los_hours" not in encounters.columns:
        encounters["ed_los_hours"] = (
            encounters["outtime"] - encounters["intime"]
        ).dt.total_seconds() / 3600

    # Rebuild the diagnosis-category bridge from source diagnoses.
    diagnoses["title_lower"] = (
        diagnoses["icd_title"].fillna("").str.lower()
    )

    category_frames = []
    for category, pattern in PATTERNS.items():
        matches = diagnoses[
            diagnoses["title_lower"].str.contains(
                pattern, regex=True, na=False
            )
        ][["subject_id", "stay_id"]].drop_duplicates()

        matches["diagnosis_group"] = category
        category_frames.append(matches)

    bridge = pd.concat(category_frames, ignore_index=True)
    bridge = bridge.drop_duplicates(
        ["subject_id", "stay_id", "diagnosis_group"]
    )

    # Keep one row per encounter in the main table.
    base = encounters.drop_duplicates("stay_id").copy()

    # Fill demographic/disposition values from ED stay records when needed.
    base = base.merge(
        edstays[
            ["stay_id", "gender", "race", "disposition", "hadm_id"]
        ].drop_duplicates("stay_id"),
        on="stay_id",
        how="left",
        suffixes=("", "_source"),
    )

    for col in ["gender", "race", "disposition", "hadm_id"]:
        source_col = f"{col}_source"
        if source_col in base.columns:
            if col not in base.columns:
                base[col] = base[source_col]
            else:
                base[col] = base[col].where(
                    base[col].notna(), base[source_col]
                )
            base.drop(columns=[source_col], inplace=True)

    # Count all ED visits per patient using the complete ED stays table.
    all_stays = edstays.copy()
    all_stays["intime"] = pd.to_datetime(
        all_stays["intime"], errors="coerce"
    )
    all_stays = all_stays.sort_values("intime")
    all_stays["ed_visit_number"] = (
        all_stays.groupby("subject_id").cumcount() + 1
    )

    visit_lookup = all_stays[
        ["subject_id", "stay_id", "ed_visit_number"]
    ].drop_duplicates("stay_id")

    base = base.merge(
        visit_lookup, on=["subject_id", "stay_id"], how="left"
    )

    return base, bridge


try:
    df, diagnosis_bridge = load_data()
except Exception as exc:
    st.error(f"Could not load the analysis data: {exc}")
    st.stop()

if df.empty:
    st.error("The encounter dataset is empty.")
    st.stop()

# Sidebar filters
st.sidebar.header("Explore the cohort")

def choices(column):
    if column not in df.columns:
        return []
    return sorted(df[column].dropna().astype(str).unique().tolist())

race_values = choices("race")
gender_values = choices("gender")
disposition_values = choices("disposition")
category_values = sorted(diagnosis_bridge["diagnosis_group"].unique())

selected_races = st.sidebar.multiselect(
    "Race", race_values, default=race_values
)
selected_genders = st.sidebar.multiselect(
    "Gender", gender_values, default=gender_values
)
selected_categories = st.sidebar.multiselect(
    "Diagnosis group", category_values, default=category_values
)
selected_dispositions = st.sidebar.multiselect(
    "ED disposition", disposition_values, default=disposition_values
)

filtered = df.copy()
if "race" in filtered.columns:
    filtered = filtered[
        filtered["race"].astype(str).isin(selected_races)
    ]
if "gender" in filtered.columns:
    filtered = filtered[
        filtered["gender"].astype(str).isin(selected_genders)
    ]
if "disposition" in filtered.columns:
    filtered = filtered[
        filtered["disposition"].astype(str).isin(selected_dispositions)
    ]

selected_stay_ids = set(
    diagnosis_bridge[
        diagnosis_bridge["diagnosis_group"].isin(selected_categories)
    ]["stay_id"]
)
filtered = filtered[filtered["stay_id"].isin(selected_stay_ids)]

if filtered.empty:
    st.warning("No encounters match these filters.")
    st.stop()

# Repeated diagnosis groups are handled separately in category-based views.
filtered_bridge = diagnosis_bridge[
    diagnosis_bridge["stay_id"].isin(filtered["stay_id"])
    & diagnosis_bridge["diagnosis_group"].isin(selected_categories)
]

n_stays = filtered["stay_id"].nunique()
n_patients = filtered["subject_id"].nunique()
median_los = filtered["ed_los_hours"].median()

m1, m2, m3, m4 = st.columns(4)
m1.metric("ED encounters", f"{n_stays:,}")
m2.metric("Distinct patients", f"{n_patients:,}")
m3.metric(
    "Median ED stay",
    f"{median_los:.2f} hours" if pd.notna(median_los) else "N/A",
)
m4.metric(
    "Hospital admission linked",
    f"{filtered['hadm_id'].notna().sum():,}"
    if "hadm_id" in filtered.columns else "N/A",
)

st.caption(
    "Diagnosis groups can overlap. Counts in category-based charts may "
    "therefore exceed the number of unique ED encounters. A linked hospital "
    "admission is not the same as ED disposition."
)

q1, q2, q3 = st.tabs([
    "Q1 · Demographics & ED stays",
    "Q2 · Initial clinical state",
    "Q3 · Triage & subsequent care",
])

# Q1: demographics and ED stays
with q1:
    st.header("Q1. How do demographic factors relate to ED stays?")
    st.write(
        "Compare diagnosis groups, demographic characteristics, disposition, "
        "and ED length of stay."
    )

    category_data = filtered_bridge.merge(
        filtered[
            [
                "stay_id", "gender", "race", "disposition",
                "ed_los_hours", "subject_id", "ed_visit_number",
            ]
        ].drop_duplicates("stay_id"),
        on="stay_id",
        how="inner",
    )

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("ED length of stay")
        fig = px.box(
            category_data,
            x="diagnosis_group",
            y="ed_los_hours",
            color="gender",
            points=False,
            labels={
                "diagnosis_group": "Diagnosis group",
                "ed_los_hours": "ED stay (hours)",
                "gender": "Gender",
            },
        )
        fig.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.subheader("Disposition by diagnosis and race")
        disp = (
            category_data.groupby(
                ["diagnosis_group", "race", "disposition"],
                observed=True,
            )["stay_id"]
            .nunique()
            .reset_index(name="encounters")
        )
        fig = px.bar(
            disp,
            x="diagnosis_group",
            y="encounters",
            color="disposition",
            facet_col="race",
            facet_col_wrap=2,
            barmode="stack",
            labels={
                "diagnosis_group": "Diagnosis group",
                "encounters": "Distinct encounters",
                "disposition": "Disposition",
                "race": "Race",
            },
        )
        fig.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Repeat ED visits")
    repeat_data = category_data.drop_duplicates(
        ["subject_id", "stay_id", "diagnosis_group"]
    )
    if "ed_visit_number" in repeat_data.columns:
        fig = px.box(
            repeat_data,
            x="diagnosis_group",
            y="ed_visit_number",
            color="race",
            points=False,
            labels={
                "diagnosis_group": "Diagnosis group",
                "ed_visit_number": "Visit number in available ED data",
                "race": "Race",
            },
        )
        fig.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Visit number is calculated from the available ED stays file; "
            "it is not a measure of disease severity."
        )

# Q2: arrival condition
with q2:
    st.header("Q2. How did patients present at ED arrival?")
    st.write(
        "Compare initial vital signs and triage acuity across diagnosis "
        "groups and demographic characteristics."
    )

    category_data = filtered_bridge.merge(
        filtered[
            [
                "stay_id", "gender", "race", "disposition",
                "acuity", *[c for c in VITALS if c in filtered.columns],
            ]
        ].drop_duplicates("stay_id"),
        on="stay_id",
        how="inner",
    )

    available_vitals = [
        col for col in VITALS if col in category_data.columns
    ]

    if available_vitals:
        chosen_vital = st.selectbox(
            "Vital sign",
            available_vitals,
            format_func=lambda col: VITALS[col],
            key="q2_vital",
        )

        fig = px.box(
            category_data,
            x="diagnosis_group",
            y=chosen_vital,
            color="gender",
            points=False,
            facet_col="race",
            facet_col_wrap=2,
            labels={
                "diagnosis_group": "Diagnosis group",
                chosen_vital: VITALS[chosen_vital],
                "gender": "Gender",
                "race": "Race",
            },
        )
        fig.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Triage acuity across diagnosis groups")
    if "acuity" in category_data.columns:
        acuity_data = category_data.dropna(subset=["acuity"])
        fig = px.box(
            acuity_data,
            x="diagnosis_group",
            y="acuity",
            color="gender",
            points=False,
            labels={
                "diagnosis_group": "Diagnosis group",
                "acuity": "Triage acuity score",
                "gender": "Gender",
            },
        )
        fig.update_layout(xaxis_tickangle=-25)
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Confirm the acuity coding and direction from the dataset "
            "documentation before interpreting higher or lower scores."
        )

    st.subheader("Multiple vital signs")
    if len(available_vitals) >= 2:
        selected_vitals = st.multiselect(
            "Choose vital signs to compare",
            available_vitals,
            default=available_vitals[:3],
            format_func=lambda col: VITALS[col],
        )
        if selected_vitals:
            summary = (
                category_data.groupby("diagnosis_group")[selected_vitals]
                .median()
                .reset_index()
                .melt(
                    id_vars="diagnosis_group",
                    var_name="measurement",
                    value_name="median_value",
                )
            )
            summary["measurement"] = summary["measurement"].map(VITALS)
            fig = px.bar(
                summary,
                x="diagnosis_group",
                y="median_value",
                color="measurement",
                barmode="group",
                labels={
                    "diagnosis_group": "Diagnosis group",
                    "median_value": "Median (native measurement units)",
                    "measurement": "Measurement",
                },
            )
            fig.update_layout(xaxis_tickangle=-25)
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Measurements use different units and scales. Interpret "
                "each measurement separately; raw bar heights are not "
                "directly comparable across different units."
            )

# Q3: triage and care
with q3:
    st.header("Q3. How did triage relate to subsequent ED care?")
    st.write(
        "Examine associations among triage acuity, initial vital signs, "
        "diagnosis groups, and ED disposition."
    )

    category_data = filtered_bridge.merge(
        filtered[
            [
                "stay_id", "gender", "race", "disposition",
                "acuity", *[c for c in VITALS if c in filtered.columns],
            ]
        ].drop_duplicates("stay_id"),
        on="stay_id",
        how="inner",
    )

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Disposition across acuity levels")
        if "acuity" in category_data.columns:
            data = category_data.dropna(subset=["acuity"])
            counts = (
                data.groupby(
                    ["diagnosis_group", "acuity", "disposition"],
                    observed=True,
                )["stay_id"]
                .nunique()
                .reset_index(name="encounters")
            )
            fig = px.bar(
                counts,
                x="acuity",
                y="encounters",
                color="disposition",
                facet_col="diagnosis_group",
                facet_col_wrap=2,
                barmode="stack",
                labels={
                    "acuity": "Triage acuity score",
                    "encounters": "Distinct encounters",
                    "disposition": "ED disposition",
                },
            )
            st.plotly_chart(fig, use_container_width=True)

    
    with c2:
        st.subheader("Disposition by diagnosis and race")
        disp = (
            category_data.groupby(
                ["diagnosis_group", "race", "disposition"],
                observed=True,
            )["stay_id"]
            .nunique()
            .reset_index(name="encounters")
        )

        # Use a single chart instead of creating one facet per race.
        disp["diagnosis_race"] = (
            disp["diagnosis_group"] + " | " + disp["race"].astype(str)
        )

        fig = px.bar(
            disp,
            x="diagnosis_race",
            y="encounters",
            color="disposition",
            barmode="stack",
            labels={
                "diagnosis_race": "Diagnosis group | Race",
                "encounters": "Distinct ED encounters",
                "disposition": "ED disposition",
            },
            hover_data=["diagnosis_group", "race"],
        )
        fig.update_layout(
            xaxis_tickangle=-45,
            xaxis_title="Diagnosis group | Race",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Triage patterns across demographics")
    if "acuity" in category_data.columns:
        data = category_data.dropna(subset=["acuity"])
        fig = px.density_heatmap(
            data,
            x="acuity",
            y="diagnosis_group",
            facet_col="gender",
            histfunc="count",
            labels={
                "acuity": "Triage acuity score",
                "diagnosis_group": "Diagnosis group",
                "count": "Encounter count",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Data notes and limitations")
st.markdown(
    """
    - The cohort is identified using diagnosis-title keywords and is not a
      clinically validated cardiac cohort.
    - Diagnosis categories overlap; one ED stay can appear in multiple groups.
    - Age is not currently available in the local dataset.
    - Race and gender comparisons are descriptive and should not be interpreted
      as causal or biological explanations.
    - ED disposition, hospital admission linkage, and later hospital outcomes
      are distinct concepts.
    - Only ED stays and measurements present in the available source files
      are included. Missing measurements are not treated as zero.
    """
)

with st.expander("Preview filtered encounters"):
    st.dataframe(filtered.head(100), use_container_width=True)