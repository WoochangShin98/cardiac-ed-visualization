
from pathlib import Path
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

from config import DATA_DIR, ED_DIR

CARDIAC_FILE = DATA_DIR / "cardiac_candidate_encounters.csv"
OUTPUT_FILE = DATA_DIR / "non_cardiac_candidate_encounters.csv"

# Use the same broad discovery categories as the existing
# cardiac classification script.
CARDIAC_PATTERNS = {
    "Chest pain / symptoms": (
        r"chest pain|angina|palpitation"
    ),
    "Myocardial infarction / ischemia": (
        r"myocardial infarction|nstemi|stemi|"
        r"ischemic heart|ischaemic heart|"
        r"ischemic heart disease|coronary artery disease"
    ),
    "Heart failure": (
        r"heart failure|congestive heart failure"
    ),
    "Arrhythmia / rate disorders": (
        r"atrial fibrillation|atrial flutter|arrhythmia|"
        r"tachycardia|bradycardia|supraventricular"
    ),
    "Other cardiovascular conditions": (
        r"cardiac arrest|cardiomyopathy|pericarditis|"
        r"endocarditis"
    ),
}

EXPECTED_COLUMNS = [
    "subject_id",
    "stay_id",
    "hadm_id",
    "intime",
    "outtime",
    "gender",
    "race",
    "arrival_transport",
    "disposition",
    "temperature",
    "heartrate",
    "resprate",
    "o2sat",
    "sbp",
    "dbp",
    "pain",
    "acuity",
    "chiefcomplaint",
    "ed_los_hours",
]


# ============================================================
# HELPERS
# ============================================================

def read_gzip_csv(path: Path) -> pd.DataFrame:
    """Read a compressed CSV, with an informative error."""
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    return pd.read_csv(
        path,
        compression="gzip",
        low_memory=False,
    )


def require_columns(
    frame: pd.DataFrame,
    columns: list[str],
    name: str,
) -> None:
    """Fail clearly when a source table lacks required fields."""
    missing = sorted(set(columns) - set(frame.columns))

    if missing:
        raise ValueError(
            f"{name} is missing required columns: {missing}\n"
            f"Available columns: {frame.columns.tolist()}"
        )


def normalize_id(series: pd.Series) -> pd.Series:
    """Normalize integer-like IDs for cross-file comparison."""
    numeric = pd.to_numeric(series, errors="coerce")

    # MIMIC identifiers are integer-valued. Reject unexpected
    # non-integer values instead of silently truncating them.
    invalid = numeric.notna() & (numeric % 1 != 0)

    if invalid.any():
        raise ValueError(
            f"Found {int(invalid.sum())} non-integer encounter IDs."
        )

    return numeric.astype("Int64")


# ============================================================
# 1. CHECK INPUT FILES
# ============================================================

print("=" * 72)
print("NON-CARDIAC ED COHORT CREATION")
print("=" * 72)

for path in [
    ED_DIR / "edstays.csv.gz",
    ED_DIR / "triage.csv.gz",
    ED_DIR / "diagnosis.csv.gz",
    CARDIAC_FILE,
]:
    if not path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {path}"
        )

print("All required input files exist.")


# ============================================================
# 2. LOAD SOURCE TABLES
# ============================================================

ed = read_gzip_csv(ED_DIR / "edstays.csv.gz")
triage = read_gzip_csv(ED_DIR / "triage.csv.gz")
diagnoses = read_gzip_csv(ED_DIR / "diagnosis.csv.gz")

cardiac = pd.read_csv(
    CARDIAC_FILE,
    usecols=["stay_id"],
    low_memory=False,
)

require_columns(
    ed,
    [
        "subject_id",
        "stay_id",
        "hadm_id",
        "intime",
        "outtime",
        "gender",
        "race",
        "arrival_transport",
        "disposition",
    ],
    "edstays.csv.gz",
)

require_columns(
    diagnoses,
    ["stay_id", "icd_title"],
    "diagnosis.csv.gz",
)

require_columns(
    triage,
    ["stay_id"],
    "triage.csv.gz",
)

print(f"Source ED rows: {len(ed):,}")
print(f"Source diagnosis rows: {len(diagnoses):,}")
print(f"Source triage rows: {len(triage):,}")
print(f"Existing cardiac rows: {len(cardiac):,}")


# ============================================================
# 3. VALIDATE SOURCE ENCOUNTER IDENTIFIERS
# ============================================================

ed["stay_id"] = normalize_id(ed["stay_id"])
diagnoses["stay_id"] = normalize_id(diagnoses["stay_id"])
triage["stay_id"] = normalize_id(triage["stay_id"])
cardiac["stay_id"] = normalize_id(cardiac["stay_id"])

if ed["stay_id"].isna().any():
    raise ValueError(
        "The ED source contains missing stay_id values."
    )

if ed["stay_id"].duplicated().any():
    raise ValueError(
        "The ED source has duplicate stay_id values. "
        "Resolve these before building the cohort."
    )

cardiac_stay_ids = set(
    cardiac["stay_id"].dropna().tolist()
)

if cardiac["stay_id"].dropna().duplicated().any():
    raise ValueError(
        "The existing cardiac cohort contains duplicate stay IDs."
    )


# ============================================================
# 4. IDENTIFY CARDIAC-LABELLED ENCOUNTERS
# ============================================================

diagnosis_title = (
    diagnoses["icd_title"]
    .fillna("")
    .astype(str)
    .str.lower()
)

diagnosis_cardiac_mask = pd.Series(
    False,
    index=diagnoses.index,
)

print("\nDiagnosis matching:")

for category, pattern in CARDIAC_PATTERNS.items():
    matches = diagnosis_title.str.contains(
        pattern,
        regex=True,
        na=False,
    )

    matching_stays = diagnoses.loc[
        matches, "stay_id"
    ].dropna().nunique()

    diagnosis_cardiac_mask |= matches

    print(f"  {category}: {matching_stays:,} unique stays")

diagnosis_cardiac_stay_ids = set(
    diagnoses.loc[
        diagnosis_cardiac_mask, "stay_id"
    ].dropna().tolist()
)

# Exclude the union of:
#   1. Stays matching the diagnosis-title patterns.
#   2. Every stay already in the existing cardiac cohort.
#
# This guarantees that a cardiac cohort encounter cannot also
# be retained in the new non-cardiac cohort.

excluded_stay_ids = (
    diagnosis_cardiac_stay_ids | cardiac_stay_ids
)

print(
    "\nDiagnosis-matched cardiac stays: "
    f"{len(diagnosis_cardiac_stay_ids):,}"
)
print(
    "Existing cardiac cohort stays: "
    f"{len(cardiac_stay_ids):,}"
)
print(
    "Total unique excluded stay IDs: "
    f"{len(excluded_stay_ids):,}"
)


# ============================================================
# 5. SELECT NON-CARDIAC ED ENCOUNTERS
# ============================================================

non_cardiac_ed = ed.loc[
    ~ed["stay_id"].isin(excluded_stay_ids)
].copy()

print(
    "\nNon-cardiac candidates before triage join: "
    f"{len(non_cardiac_ed):,}"
)


# ============================================================
# 6. PREPARE TRIAGE DATA WITHOUT SILENTLY DROPPING CONFLICTS
# ============================================================

triage_columns = [
    "stay_id",
    "temperature",
    "heartrate",
    "resprate",
    "o2sat",
    "sbp",
    "dbp",
    "pain",
    "acuity",
    "chiefcomplaint",
]

available_triage_columns = [
    column
    for column in triage_columns
    if column in triage.columns
]

if "stay_id" not in available_triage_columns:
    raise ValueError(
        "Triage table does not contain stay_id."
    )

triage_subset = triage[available_triage_columns].copy()

# Remove exact duplicate rows only. Do not silently choose one
# of several conflicting triage records for the same encounter.
triage_subset = triage_subset.drop_duplicates()

duplicate_triage_mask = triage_subset["stay_id"].duplicated(
    keep=False
)

if duplicate_triage_mask.any():
    duplicate_count = triage_subset.loc[
        duplicate_triage_mask, "stay_id"
    ].nunique()

    raise ValueError(
        f"{duplicate_count:,} ED stays have multiple distinct "
        "triage records. Inspect these records and define a "
        "documented selection rule before proceeding."
    )


# ============================================================
# 7. JOIN TRIAGE AND CALCULATE ED LENGTH OF STAY
# ============================================================

result = non_cardiac_ed.merge(
    triage_subset,
    on="stay_id",
    how="left",
    validate="one_to_one",
    indicator=True,
)

triage_match_count = int(
    (result["_merge"] == "both").sum()
)

triage_missing_count = int(
    (result["_merge"] == "left_only").sum()
)

result = result.drop(columns=["_merge"])

print(f"\nEncounters with triage records: {triage_match_count:,}")
print(f"Encounters without triage records: {triage_missing_count:,}")

# Add any unavailable expected triage fields as missing columns,
# preserving the same schema as the cardiac comparison cohort.
for column in EXPECTED_COLUMNS:
    if column not in result.columns:
        result[column] = pd.NA

result["intime"] = pd.to_datetime(
    result["intime"],
    errors="coerce",
)

result["outtime"] = pd.to_datetime(
    result["outtime"],
    errors="coerce",
)

result["ed_los_hours"] = (
    result["outtime"] - result["intime"]
).dt.total_seconds() / 3600

result = result[EXPECTED_COLUMNS].copy()


# ============================================================
# 8. VALIDATE THE FINAL COHORT
# ============================================================

if result["stay_id"].isna().any():
    raise ValueError(
        "The final cohort contains missing stay_id values."
    )

if result["stay_id"].duplicated().any():
    raise ValueError(
        "The final cohort contains duplicate stay_id values."
    )

overlap_ids = set(
    result["stay_id"].dropna().tolist()
) & cardiac_stay_ids

if overlap_ids:
    raise ValueError(
        f"Validation failed: {len(overlap_ids):,} stay IDs "
        "overlap with the existing cardiac cohort."
    )

# Check whether any diagnosis-pattern-matched stay remains.
remaining_diagnosis_matches = (
    set(result["stay_id"].dropna().tolist())
    & diagnosis_cardiac_stay_ids
)

if remaining_diagnosis_matches:
    raise ValueError(
        "Validation failed: diagnosis-matched cardiac stays "
        "remain in the output."
    )

if len(result.columns) != 19:
    raise ValueError(
        f"Expected 19 columns, found {len(result.columns)}."
    )


# ============================================================
# 9. SAVE OUTPUT
# ============================================================

DATA_DIR.mkdir(parents=True, exist_ok=True)

result.to_csv(
    OUTPUT_FILE,
    index=False,
)

# Re-read the saved file to validate the actual output.
saved = pd.read_csv(
    OUTPUT_FILE,
    low_memory=False,
)

if saved.columns.tolist() != EXPECTED_COLUMNS:
    raise ValueError(
        "Saved CSV schema does not match the expected schema."
    )

if saved["stay_id"].duplicated().any():
    raise ValueError(
        "Saved CSV contains duplicate stay IDs."
    )

saved_ids = set(
    normalize_id(saved["stay_id"]).dropna().tolist()
)

if saved_ids & cardiac_stay_ids:
    raise ValueError(
        "Saved CSV overlaps with the cardiac cohort."
    )


# ============================================================
# 10. REPORT SUMMARY
# ============================================================

print("\n" + "=" * 72)
print("NON-CARDIAC COHORT SUMMARY")
print("=" * 72)

print(f"Original ED encounters: {len(ed):,}")
print(f"Diagnosis-matched cardiac stays: "
      f"{len(diagnosis_cardiac_stay_ids):,}")
print(f"Existing cardiac cohort stays: "
      f"{len(cardiac_stay_ids):,}")
print(f"Final non-cardiac encounters: {len(saved):,}")
print(f"Unique patients: {saved['subject_id'].nunique():,}")
print(f"Unique stay IDs: {saved['stay_id'].nunique():,}")
print(f"Duplicate stay IDs: {saved['stay_id'].duplicated().sum():,}")
print(f"Overlap with cardiac cohort: "
      f"{saved['stay_id'].isin(cardiac_stay_ids).sum():,}")
print(f"Columns: {len(saved.columns)}")

print("\nDisposition counts:")
print(saved["disposition"].value_counts(dropna=False).to_string())

print("\nMissing values:")
print(saved.isna().sum().to_string())

print(f"\nOutput saved to:\n{OUTPUT_FILE.resolve()}")

print("\nValidation passed.")
print(
    "Interpretation: encounters excluded by recorded diagnosis "
    "matching rules; this does not establish absence of cardiac "
    "medical history."
)
print("Original MIMIC source files and cardiac CSV were not modified.")
