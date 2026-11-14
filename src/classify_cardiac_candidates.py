from pathlib import Path
import pandas as pd

MIMIC_ED = Path(
r"C:\MIMIC\mimic-iv-ed\extracted\mimic-iv-ed-2.2\ed"
)

diagnosis = pd.read_csv(MIMIC_ED / "diagnosis.csv.gz")
edstays = pd.read_csv(MIMIC_ED / "edstays.csv.gz")

# Normalize diagnosis text for case-insensitive matching

title = diagnosis["icd_title"].fillna("").str.lower()

# Discovery categories, not a finalized clinical definition

patterns = {
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

# Associate each encounter with every category it matches.

# Categories can overlap; counts must not be added together.

category_rows = []

for category, pattern in patterns.items():
    matches = diagnosis[title.str.contains(pattern, regex=True)].copy()
    stays = matches[["subject_id", "stay_id"]].drop_duplicates()
    stays["category"] = category
    category_rows.append(stays)

categorized = pd.concat(category_rows, ignore_index=True)

print("\n" + "=" * 70)
print("1. DISTINCT ED STAYS PER CATEGORY")
print("=" * 70)

counts = (
categorized.groupby("category")["stay_id"]
.nunique()
.sort_values(ascending=False)
)

print(counts.to_string())
print(
"\nUnique stays matching at least one category: "
f"{categorized['stay_id'].nunique():,}"
)

# Check whether candidate stays have matching ED encounter records

candidate_stays = categorized[
["subject_id", "stay_id"]
].drop_duplicates()

cohort = candidate_stays.merge(
edstays,
on=["subject_id", "stay_id"],
how="left",
validate="one_to_one",
indicator=True,
)

print("\n" + "=" * 70)
print("2. ENCOUNTER LINKAGE VALIDATION")
print("=" * 70)
print(cohort["_merge"].value_counts().to_string())

cohort = cohort[cohort["_merge"] == "both"].copy()
cohort["has_hadm_id"] = cohort["hadm_id"].notna()

print(
f"\nCandidate encounters matched to edstays: {len(cohort):,}"
)
print(
f"With hospital admission link: "
f"{cohort['has_hadm_id'].sum():,}"
)
print(
f"Without hospital admission link: "
f"{(~cohort['has_hadm_id']).sum():,}"
)

print("\n" + "=" * 70)
print("3. ED DISPOSITION OF CANDIDATE ENCOUNTERS")
print("=" * 70)
print(cohort["disposition"].value_counts(dropna=False).to_string())

print("\n" + "=" * 70)
print("4. DISPOSITION BY DIAGNOSIS CATEGORY")
print("=" * 70)

category_outcomes = categorized.merge(
cohort[["subject_id", "stay_id", "disposition"]],
on=["subject_id", "stay_id"],
how="inner",
validate="many_to_one",
)

print(
pd.crosstab(
category_outcomes["category"],
category_outcomes["disposition"],
).to_string()
)

print("\nThis is exploratory profiling, not a finalized clinical cohort.")
print("Original MIMIC files were not modified.")
