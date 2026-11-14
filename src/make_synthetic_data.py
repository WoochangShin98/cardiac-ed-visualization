"""FAKE data with the same schema as data/q1_ed_experience.csv.

For building/testing the website without MIMIC access. Numbers are
random and roughly shaped like FP1 results - never present them as findings.

    python src/make_synthetic_data.py
    python src/build_web_aggregates.py --input data/synthetic_q1_ed_experience.csv
"""
import numpy as np
import pandas as pd

from config import CARDIAC_PATTERNS, DATA_DIR

rng = np.random.default_rng(5609)
N = 420_000
cats = list(CARDIAC_PATTERNS.keys())

cohort = np.where(rng.random(N) < 0.125, "Cardiac", "Non-cardiac")
is_c = cohort == "Cardiac"
category = np.where(is_c, rng.choice(cats, N, p=[.14, .16, .30, .05, .35]), None)

acuity = rng.choice([1, 2, 3, 4, 5], N, p=[.06, .33, .53, .07, .01]).astype(float)
acuity[is_c] = rng.choice([1, 2, 3, 4, 5], is_c.sum(), p=[.08, .55, .35, .015, .005])
acuity[rng.random(N) < 0.016] = np.nan

age = np.clip(rng.normal(np.where(is_c, 66, 50), 18), 18, 100).round()
pain = np.clip(rng.normal(np.where(is_c, 3.5, 4.2) + (acuity == 4) * 1, 3.2), 0, 10).round()
pain[rng.random(N) < 0.08] = np.nan

los = rng.lognormal(np.log(np.where(is_c, 6.4, 5.3)) + 0.05 * (age - 55) / 10, 0.6)
admit_p = np.clip(0.25 + 0.25 * is_c + 0.005 * (age - 50) - 0.05 * (np.nan_to_num(acuity, nan=3) - 3), .03, .95)
u = rng.random(N)
disposition = np.where(u < admit_p, "ADMITTED",
                       np.where(u < admit_p + (1 - admit_p) * .9, "HOME",
                                rng.choice(["TRANSFER", "LEFT WITHOUT BEING SEEN", "ELOPED"], N)))

df = pd.DataFrame({
    "stay_id": np.arange(N) + 30_000_000,
    "cohort": cohort,
    "cardiac_category": category,
    "n_cardiac_categories": np.where(is_c, 1, 0),
    "pain": pain, "acuity": acuity,
    "diagnosis_count": np.clip(rng.poisson(np.where(is_c, 2.4, 1.9)), 1, 12),
    "ed_los_hours": los.round(2),
    "gender": rng.choice(["F", "M"], N, p=[.54, .46]),
    "race": rng.choice(["WHITE", "BLACK/AFRICAN AMERICAN", "HISPANIC/LATINO", "ASIAN", "OTHER"], N),
    "age": age,
    "arrival_transport": rng.choice(["WALK IN", "AMBULANCE", "UNKNOWN", "OTHER", "HELICOPTER"], N,
                                    p=[.6, .33, .04, .025, .005]),
    "disposition": disposition,
    "temperature": rng.normal(98.1, 0.8, N).round(1),
    "heartrate": rng.normal(np.where(is_c, 88, 85), 18).round(),
    "resprate": rng.normal(18, 2.5, N).round(),
    "o2sat": np.clip(rng.normal(98, 2, N), 70, 100).round(),
    "sbp": rng.normal(np.where(is_c, 140, 133), 24).round(),
    "dbp": rng.normal(78, 14, N).round(),
})

out = DATA_DIR / "synthetic_q1_ed_experience.csv"
DATA_DIR.mkdir(exist_ok=True)
df.to_csv(out, index=False)
print(f"Saved FAKE data: {out} ({len(df):,} rows)")
