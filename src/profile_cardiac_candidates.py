from pathlib import Path
import pandas as pd

MIMIC_ED = Path(
r"C:\MIMIC\mimic-iv-ed\extracted\mimic-iv-ed-2.2\ed"
)

# Load only the tables needed for this initial profile

edstays = pd.read_csv(MIMIC_ED / "edstays.csv.gz")
diagnosis = pd.read_csv(MIMIC_ED / "diagnosis.csv.gz")
triage = pd.read_csv(MIMIC_ED / "triage.csv.gz")

print("\n" + "=" * 70)
print("1. ED DISPOSITION")
print("=" * 70)
print(edstays["disposition"].value_counts(dropna=False).to_string())

print("\n" + "=" * 70)
print("2. HOSPITAL ADMISSION LINKAGE")
print("=" * 70)

linked = edstays["hadm_id"].notna()

print(f"Total ED encounters: {len(edstays):,}")
print(f"With hospital admission link: {linked.sum():,}")
print(f"Without hospital admission link: {(~linked).sum():,}")
print(f"Percentage linked: {linked.mean() * 100:.2f}%")

print("\n" + "=" * 70)
print("3. POTENTIAL CARDIAC DIAGNOSIS TITLES")
print("=" * 70)

# Broad discovery terms, not a finalized clinical definition

terms = [
"myocardial infarction",
"ischemic heart",
"ischaemic heart",
"coronary artery",
"heart failure",
"cardiac arrest",
"arrhythmia",
"atrial fibrillation",
"atrial flutter",
"tachycardia",
"bradycardia",
"angina",
"chest pain",
"cardiomyopathy",
"pericarditis",
"endocarditis",
]

title = diagnosis["icd_title"].fillna("").str.lower()
pattern = "|".join(terms)
candidates = diagnosis[title.str.contains(pattern, regex=True)].copy()

print(f"Matching diagnosis records: {len(candidates):,}")
print(
"Distinct ED stays with a matching diagnosis: "
f"{candidates['stay_id'].nunique():,}"
)
print(
"Distinct diagnosis titles: "
f"{candidates['icd_title'].nunique():,}"
)

print("\nMost frequent matching diagnosis titles:")
print(
candidates["icd_title"]
.value_counts()
.head(40)
.to_string()
)

print("\n" + "=" * 70)
print("4. COMMON CHIEF COMPLAINTS IN POTENTIAL CARDIAC ENCOUNTERS")
print("=" * 70)

candidate_stays = candidates[["subject_id", "stay_id"]].drop_duplicates()

candidate_triage = triage.merge(
candidate_stays,
on=["subject_id", "stay_id"],
how="inner",
validate="one_to_one",
)

print(
candidate_triage["chiefcomplaint"]
.fillna("Missing")
.value_counts()
.head(30)
.to_string()
)

print("\n" + "=" * 70)
print("5. CARDIAC CANDIDATE ICD CODES")
print("=" * 70)

print(
candidates.groupby(
["icd_version", "icd_code", "icd_title"],
dropna=False,
)
.size()
.sort_values(ascending=False)
.head(50)
.to_string()
)

print("\nProfile complete. Original MIMIC files were not modified.")
