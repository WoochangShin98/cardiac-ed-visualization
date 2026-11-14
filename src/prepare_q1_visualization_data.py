"""Build the encounter-level analysis table (LOCAL ONLY - never publish).

Output: data/q1_ed_experience.csv  (one row per ED stay, patient-level)

Changes for FP2:
  - cardiac_category: primary cardiac category (see config.CARDIAC_PATTERNS)
  - cat_* flags: every category a stay matches (categories can overlap)
  - arrival_transport and triage vital signs
  - age (only if MIMIC-IV hosp/patients.csv.gz is available)

Next step: python src/build_web_aggregates.py
"""
import pandas as pd

from config import (
    CARDIAC_PATTERNS, DATA_DIR, ED_DIR, HOSP_DIR,
)

cardiac = pd.read_csv(DATA_DIR / "cardiac_candidate_encounters.csv",
                      low_memory=False)
non_cardiac = pd.read_csv(DATA_DIR / "non_cardiac_candidate_encounters.csv",
                          low_memory=False)
diagnoses = pd.read_csv(ED_DIR / "diagnosis.csv.gz")

diagnoses["stay_id"] = pd.to_numeric(diagnoses["stay_id"], errors="coerce")
diagnoses = diagnoses.dropna(subset=["stay_id"])

# ---------------------------------------------------------------
# 1. Number of distinct diagnosis codes per stay (unchanged)
# ---------------------------------------------------------------
diagnosis_count = (
    diagnoses.drop_duplicates(subset=["stay_id", "icd_code", "icd_version"])
    .groupby("stay_id").size()
    .rename("diagnosis_count").reset_index()
)

# ---------------------------------------------------------------
# 2. Cardiac category flags + primary category
# ---------------------------------------------------------------
title = diagnoses["icd_title"].fillna("").str.lower()
flag_cols = []
flags = pd.DataFrame({"stay_id": diagnoses["stay_id"]})
for i, (category, pattern) in enumerate(CARDIAC_PATTERNS.items()):
    col = f"cat_{i}"
    flag_cols.append(col)
    flags[col] = title.str.contains(pattern, regex=True, na=False)
flags = flags.groupby("stay_id")[flag_cols].any().reset_index()

category_names = list(CARDIAC_PATTERNS.keys())


def primary_category(row):
    for col, name in zip(flag_cols, category_names):
        if row[col]:
            return name
    return pd.NA


flags["cardiac_category"] = flags.apply(primary_category, axis=1)
flags["n_cardiac_categories"] = flags[flag_cols].sum(axis=1)

# ---------------------------------------------------------------
# 3. Combine cohorts
# ---------------------------------------------------------------
frames = []
for name, frame in [("Cardiac", cardiac), ("Non-cardiac", non_cardiac)]:
    frame = frame.drop_duplicates("stay_id").copy()
    frame["cohort"] = name
    frame["stay_id"] = pd.to_numeric(frame["stay_id"], errors="coerce")
    frame = frame.merge(diagnosis_count, on="stay_id", how="left",
                        validate="one_to_one")
    frame["diagnosis_count"] = frame["diagnosis_count"].fillna(0).astype(int)
    frames.append(frame)

overlap = set(cardiac["stay_id"]) & set(non_cardiac["stay_id"])
if overlap:
    raise ValueError(f"Cohorts overlap on {len(overlap)} stay IDs")

combined = pd.concat(frames, ignore_index=True)
combined = combined.merge(
    flags[["stay_id", "cardiac_category", "n_cardiac_categories", *flag_cols]],
    on="stay_id", how="left", validate="one_to_one",
)
is_non = combined["cohort"] == "Non-cardiac"
combined.loc[is_non, "cardiac_category"] = pd.NA
combined.loc[is_non, flag_cols] = False
combined["n_cardiac_categories"] = combined["n_cardiac_categories"].fillna(0)

# Readable flag names
combined = combined.rename(columns={
    col: "cat_" + name.lower().replace(" / ", "_").replace(" ", "_")
    for col, name in zip(flag_cols, category_names)
})

# ---------------------------------------------------------------
# 4. Age (optional - needs MIMIC-IV hosp module)
# ---------------------------------------------------------------
patients_path = HOSP_DIR / "patients.csv.gz"
if patients_path.exists() and "subject_id" in combined.columns:
    patients = pd.read_csv(patients_path,
                           usecols=["subject_id", "anchor_age", "anchor_year"])
    combined = combined.merge(patients, on="subject_id", how="left")
    in_year = pd.to_datetime(combined["intime"], errors="coerce").dt.year
    combined["age"] = combined["anchor_age"] + (in_year - combined["anchor_year"])
    combined = combined.drop(columns=["anchor_age", "anchor_year"])
    print(f"Age linked for {combined['age'].notna().mean():.1%} of stays")
else:
    combined["age"] = pd.NA
    print(f"[info] {patients_path} not found - age left empty.")

# ---------------------------------------------------------------
# 5. Save (local, gitignored)
# ---------------------------------------------------------------
output_columns = [
    "stay_id", "cohort", "cardiac_category", "n_cardiac_categories",
    *[c for c in combined.columns if c.startswith("cat_")],
    "pain", "acuity", "diagnosis_count", "ed_los_hours",
    "gender", "race", "age", "arrival_transport", "disposition",
    "temperature", "heartrate", "resprate", "o2sat", "sbp", "dbp",
]
for col in output_columns:
    if col not in combined.columns:
        combined[col] = pd.NA

combined = combined[output_columns]
out = DATA_DIR / "q1_ed_experience.csv"
combined.to_csv(out, index=False)

print(f"Saved: {out}  (patient-level - DO NOT publish)")
print(f"Rows: {len(combined):,}")
print(combined.groupby("cohort").size())
print("\nPrimary cardiac category:")
print(combined["cardiac_category"].value_counts(dropna=False))
print("\nMissing values:")
print(combined.isna().sum())
