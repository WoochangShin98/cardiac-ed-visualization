from pathlib import Path
import pandas as pd

# Location of your existing MIMIC-IV-ED files
MIMIC_ED = Path(
    r"C:\MIMIC\mimic-iv-ed\extracted\mimic-iv-ed-2.2\ed"
)

# Tables we want to inspect first
tables = [
    "edstays",
    "triage",
    "diagnosis",
    "vitalsign",
]

for table in tables:
    file_path = MIMIC_ED / f"{table}.csv.gz"

    print("\n" + "=" * 70)
    print(f"TABLE: {table}")
    print("=" * 70)

    if not file_path.exists():
        print(f"FILE NOT FOUND: {file_path}")
        continue

    # Read the compressed CSV directly without extracting it
    df = pd.read_csv(file_path)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")
    print(f"Column names: {list(df.columns)}")

    print("\nData types:")
    print(df.dtypes.to_string())

    print("\nMissing values:")
    print(df.isna().sum().to_string())

    print("\nFirst 3 rows:")
    print(df.head(3).to_string(index=False))

    if "subject_id" in df.columns:
        print(f"\nUnique patients: {df['subject_id'].nunique():,}")

    if "stay_id" in df.columns:
        print(f"Unique ED stays: {df['stay_id'].nunique():,}")

