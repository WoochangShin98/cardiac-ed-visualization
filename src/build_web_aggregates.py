"""Aggregate the encounter table into a summary "cube" for the website.

The website must NEVER load patient-level rows. This script turns
data/q1_ed_experience.csv into svelte-app/static/data/ed_cube.json, which
holds only group-level summaries (counts, quantiles, histograms).

Cube dimensions (each can also be rolled up to "All"):
  group   : Non-cardiac | Cardiac (all) | 5 primary cardiac categories
  acuity  : 1..5 | Unknown
  dispo   : Admitted | Home | Other
  gender  : Female | Male
  age     : 18-44 | 45-64 | 65-79 | 80+ | Unknown

Privacy:
  - cells with n < MIN_CELL_SIZE are dropped
  - counts between 1 and MIN_CELL_SIZE-1 inside a cell become null
  - every published count is rounded to the nearest ROUND_TO, so small
    suppressed values cannot be recovered exactly by subtracting cells

Usage:
  python src/build_web_aggregates.py
  python src/build_web_aggregates.py --input data/synthetic_q1_ed_experience.csv
"""
import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd

from config import CARDIAC_PATTERNS, DATA_DIR, MIN_CELL_SIZE, WEB_DATA_DIR

ALL = "All"
CARDIAC_ALL = "Cardiac (all)"
NON_CARDIAC = "Non-cardiac"

DIMS = ["group", "acuity", "dispo", "gender", "age"]
DIM_VALUES = {
    "group": [ALL, NON_CARDIAC, CARDIAC_ALL, *CARDIAC_PATTERNS.keys()],
    "acuity": [ALL, "1", "2", "3", "4", "5", "Unknown"],
    "dispo": [ALL, "Admitted", "Home", "Other"],
    "gender": [ALL, "Female", "Male"],
    "age": [ALL, "18-44", "45-64", "65-79", "80+", "Unknown"],
}

LOS_EDGES = list(range(0, 26, 2)) + [np.inf]          # 0-2, ..., 22-24, 24+
LOS_LABELS = [f"{a}-{b}" for a, b in zip(LOS_EDGES[:-2], LOS_EDGES[1:-1])] + ["24+"]
PAIN_LEVELS = list(range(11))
DX_LABELS = ["0", "1", "2", "3", "4", "5-7", "8+"]
TRANSPORT = ["AMBULANCE", "WALK IN", "HELICOPTER", "OTHER", "UNKNOWN"]
VITALS = ["heartrate", "sbp", "dbp", "o2sat", "resprate", "temperature"]


# ------------------------------------------------------------------
# Load + derive categorical dimensions
# ------------------------------------------------------------------
def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)

    df["group"] = np.where(
        df["cohort"].eq("Cardiac"),
        df["cardiac_category"].fillna("Chest pain / symptoms"),
        NON_CARDIAC,
    )

    acuity = pd.to_numeric(df["acuity"], errors="coerce")
    df["acuity_dim"] = acuity.round().astype("Int64").astype(str)
    df.loc[~acuity.isin([1, 2, 3, 4, 5]), "acuity_dim"] = "Unknown"

    disp = df["disposition"].fillna("").str.upper()
    df["dispo"] = np.select(
        [disp.eq("ADMITTED"), disp.eq("HOME")], ["Admitted", "Home"], "Other"
    )

    g = df["gender"].fillna("").str.upper().str[0]
    df["gender_dim"] = g.map({"F": "Female", "M": "Male"})
    df = df[df["gender_dim"].notna()].copy()     # drop the few unknowns

    age = pd.to_numeric(df.get("age"), errors="coerce")
    df["age_dim"] = pd.cut(age, [17, 44, 64, 79, np.inf],
                           labels=["18-44", "45-64", "65-79", "80+"]).astype(str)
    df.loc[age.isna() | (age < 18), "age_dim"] = "Unknown"

    # pain: numeric 0-10 only ("asleep", "unable" etc. -> missing)
    pain = pd.to_numeric(df["pain"], errors="coerce")
    df["pain_num"] = pain.where(pain.between(0, 10)).round()

    df["los"] = pd.to_numeric(df["ed_los_hours"], errors="coerce")
    df.loc[(df["los"] < 0) | (df["los"] > 24 * 7), "los"] = np.nan

    dx = pd.to_numeric(df["diagnosis_count"], errors="coerce").fillna(0)
    df["dx_bucket"] = pd.cut(dx, [-1, 0, 1, 2, 3, 4, 7, np.inf],
                             labels=DX_LABELS).astype(str)

    t = df["arrival_transport"].fillna("UNKNOWN").str.upper()
    df["transport"] = t.where(t.isin(TRANSPORT), "OTHER")

    for v in VITALS:
        df[v] = pd.to_numeric(df.get(v), errors="coerce")

    df = df.drop(columns=["acuity", "gender", "age"], errors="ignore")
    return df.rename(columns={"acuity_dim": "acuity",
                              "gender_dim": "gender",
                              "age_dim": "age"})


# ------------------------------------------------------------------
# Per-cell statistics
# ------------------------------------------------------------------
ROUND_TO = 10


def rnd(count) -> int:
    """Round a count to the nearest ROUND_TO (protects against differencing)."""
    return int(round(int(count) / ROUND_TO)) * ROUND_TO


def mask(count: int):
    """Hide small non-zero counts, round the rest."""
    count = int(count)
    return None if 0 < count < MIN_CELL_SIZE else rnd(count)


def counts(series: pd.Series, levels) -> list:
    vc = series.value_counts()
    return [mask(vc.get(level, 0)) for level in levels]


def q(series: pd.Series, p) -> float | None:
    s = series.dropna()
    return None if s.empty else round(float(s.quantile(p)), 2)


def cell_stats(d: pd.DataFrame) -> dict:
    los = d["los"]
    los_bins = pd.cut(los, LOS_EDGES, right=False, labels=LOS_LABELS)
    pain = d["pain_num"].dropna().astype(int)
    return {
        "n": rnd(len(d)),
        "los": {
            "n": rnd(los.notna().sum()),
            "p10": q(los, .10), "q1": q(los, .25), "median": q(los, .5),
            "q3": q(los, .75), "p90": q(los, .90),
            "mean": None if los.dropna().empty else round(float(los.mean()), 2),
            "hist": counts(los_bins, LOS_LABELS),
        },
        "pain": {
            "n": rnd(len(pain)),
            "mean": None if pain.empty else round(float(pain.mean()), 2),
            "median": q(pain, .5), "q1": q(pain, .25), "q3": q(pain, .75),
            "dist": counts(pain, PAIN_LEVELS),
        },
        "dispo": counts(d["dispo"], DIM_VALUES["dispo"][1:]),
        "dx": counts(d["dx_bucket"], DX_LABELS),
        "transport": counts(d["transport"], TRANSPORT),
        "vitals": {
            v: {"n": rnd(d[v].notna().sum()), "q1": q(d[v], .25),
                "median": q(d[v], .5), "q3": q(d[v], .75)}
            for v in VITALS
        },
    }


def build_cube(df: pd.DataFrame) -> dict:
    cells = {}
    other_dims = DIMS[1:]

    # The group dimension has two extra roll-ups: "All" and "Cardiac (all)".
    group_sources = [
        (None, df),                                     # each real group
        (CARDIAC_ALL, df[df["group"] != NON_CARDIAC]),
        (ALL, df),
    ]

    for fixed_group, source in group_sources:
        for r in range(len(other_dims) + 1):
            for kept in itertools.combinations(other_dims, r):
                keys = (["group"] if fixed_group is None else []) + list(kept)
                grouped = source.groupby(keys, observed=True) if keys else [((), source)]
                for values, d in grouped:
                    if len(d) < MIN_CELL_SIZE:
                        continue
                    values = values if isinstance(values, tuple) else (values,)
                    coord = dict(zip(keys, values))
                    if fixed_group is not None:
                        coord["group"] = fixed_group
                    key = "|".join(str(coord.get(dim, ALL)) for dim in DIMS)
                    cells[key] = cell_stats(d)
    return cells


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path,
                        default=DATA_DIR / "q1_ed_experience.csv")
    parser.add_argument("--output", type=Path,
                        default=WEB_DATA_DIR / "ed_cube.json")
    args = parser.parse_args()

    df = load(args.input)
    cells = build_cube(df)

    out = {
        "meta": {
            "source": "MIMIC-IV-ED v2.2 (aggregated; no patient-level rows)",
            "total_encounters": rnd(len(df)),
            "min_cell_size": MIN_CELL_SIZE,
            "counts_rounded_to": ROUND_TO,
            "dims": DIMS,
            "dim_values": DIM_VALUES,
            "los_bins": LOS_LABELS,
            "pain_levels": PAIN_LEVELS,
            "dispo_levels": DIM_VALUES["dispo"][1:],
            "dx_labels": DX_LABELS,
            "transport_levels": TRANSPORT,
            "vitals": VITALS,
            "age_available": bool((df["age"] != "Unknown").any()),
        },
        "cells": cells,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    size_kb = args.output.stat().st_size / 1024
    print(f"Saved {len(cells):,} cells -> {args.output} ({size_kb:,.0f} KB)")
    print(df.groupby("group").size().to_string())


if __name__ == "__main__":
    main()
