"""Shared paths and definitions for the data pipeline.

Set MIMIC_ED_DIR / MIMIC_HOSP_DIR as environment variables if your local
MIMIC copy lives somewhere other than the defaults below.

PowerShell example:
    $env:MIMIC_ED_DIR = "D:\\mimic\\mimic-iv-ed-2.2\\ed"
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
WEB_DATA_DIR = ROOT / "svelte-app" / "static" / "data"

ED_DIR = Path(os.environ.get(
    "MIMIC_ED_DIR",
    r"C:\MIMIC\mimic-iv-ed\extracted\mimic-iv-ed-2.2\ed",
))

# Optional: MIMIC-IV hosp module, only needed for patient age
# (patients.csv.gz -> anchor_age / anchor_year). Age is not in MIMIC-IV-ED.
HOSP_DIR = Path(os.environ.get(
    "MIMIC_HOSP_DIR",
    r"C:\MIMIC\mimic-iv\hosp",
))

# Broad discovery categories (same regexes as the existing scripts).
# Ordered by PRIORITY: when one stay matches several categories, its
# primary category is the first match in this order (most specific /
# most severe first; "Chest pain / symptoms" last because it is the
# least specific).
CARDIAC_PATTERNS = {
    "MI / ischemia": (
        r"myocardial infarction|nstemi|stemi|"
        r"ischemic heart|ischaemic heart|"
        r"ischemic heart disease|coronary artery disease"
    ),
    "Heart failure": r"heart failure|congestive heart failure",
    "Arrhythmia": (
        r"atrial fibrillation|atrial flutter|arrhythmia|"
        r"tachycardia|bradycardia|supraventricular"
    ),
    "Other cardiovascular": (
        r"cardiac arrest|cardiomyopathy|pericarditis|endocarditis"
    ),
    "Chest pain / symptoms": r"chest pain|angina|palpitation",
}

# Cells with fewer encounters than this are suppressed in the web output.
MIN_CELL_SIZE = 11
