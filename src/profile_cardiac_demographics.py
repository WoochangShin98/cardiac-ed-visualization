
import pandas as pd

from config import DATA_DIR as OUT_DIR, ED_DIR as DATA_DIR

diagnosis = pd.read_csv(DATA_DIR / "diagnosis.csv.gz")
edstays = pd.read_csv(DATA_DIR / "edstays.csv.gz")
triage = pd.read_csv(DATA_DIR / "triage.csv.gz")

title = diagnosis["icd_title"].fillna("").str.lower()

patterns = {
    "Chest pain / symptoms": r"chest pain|angina|palpitation",
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

category_frames = []

for category, pattern in patterns.items():
    matches = diagnosis[title.str.contains(pattern, regex=True)].copy()
    stays = matches[["subject_id", "stay_id"]].drop_duplicates()
    stays["category"] = category
    category_frames.append(stays)

candidates = pd.concat(category_frames, ignore_index=True)
candidate_ids = candidates[["subject_id", "stay_id"]].drop_duplicates()

# Join candidate encounters to ED stay details and triage measurements.
profile = candidate_ids.merge(
    edstays, on=["subject_id", "stay_id"], how="left"
)

profile = profile.merge(
    triage, on=["subject_id", "stay_id"], how="left",
    suffixes=("", "_triage")
)

# Calculate elapsed ED time in hours.
profile["intime"] = pd.to_datetime(profile["intime"], errors="coerce")
profile["outtime"] = pd.to_datetime(profile["outtime"], errors="coerce")
profile["ed_los_hours"] = (
    profile["outtime"] - profile["intime"]
).dt.total_seconds() / 3600

print("\n=== CANDIDATE ENCOUNTER PROFILE ===")
print("Distinct candidate ED stays:", len(candidate_ids))
print("Distinct patients:", candidate_ids["subject_id"].nunique())

print("\n=== AVAILABLE TRIAGE MEASUREMENTS ===")
for col in [
    "temperature", "heartrate", "resprate",
    "o2sat", "sbp", "dbp", "acuity"
]:
    if col in profile.columns:
        available = profile[col].notna().sum()
        print(f"{col}: {available:,} / {len(profile):,} "
              f"({available / len(profile) * 100:.1f}%)")

print("\n=== ED LENGTH OF STAY (HOURS) ===")
print(profile["ed_los_hours"].describe().round(2))

print("\n=== AGE DATA CHECK ===")
print("Age is not available in the ED stay table.")
print("We will investigate linking the hospital admissions table next.")

# Save only derived analysis outputs inside this project.
OUT_DIR.mkdir(exist_ok=True)

profile.to_csv(OUT_DIR / "cardiac_candidate_encounters.csv", index=False)
print("\nSaved derived encounter profile to:")
print(OUT_DIR / "cardiac_candidate_encounters.csv")
