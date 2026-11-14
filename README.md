Website: https://cardiac-ed-visualization.vercel.app/
# Cardiac Patients in the Emergency Department

**CSCI 5609: Visualization · University of Minnesota Twin Cities · Fall 2026**
**Team The Outliers:** Woochang Shin, Sruti Paladugu, Ananya Nair

An interactive, scrollytelling website built on **MIMIC-IV-ED** (Beth Israel Deaconess Medical Center, 2011–2019).

> **Key question:** How does a cardiac patient’s journey through the emergency department (ED) differ from everyone else’s?

---

## Contents

1. [What the website shows](#what-the-website-shows)
2. [Repository structure](#repository-structure)
3. [Quick start: view the website](#quick-start-view-the-website)
4. [Rebuild the data from MIMIC-IV-ED](#rebuild-the-data-from-mimic-iv-ed)
5. [Working without MIMIC access](#working-without-mimic-access)
6. [Privacy and data use](#privacy-and-data-use)
7. [Definitions and limitations](#definitions-and-limitations)
8. [Troubleshooting](#troubleshooting)

---

## What the website shows

The site follows one patient through the ED, then hands over to free exploration.

| Stage | Question | Visualization |
|---|---|---|
| 1 · Arrival | Who comes in, and how? | Patient-group table (arrival by ambulance), triage vital signs |
| 2 · Triage | How urgent? How much pain? | Mean pain bars that morph into full 0–10 pain distributions by acuity |
| 3 · ED stay | How long do they stay? | Length-of-stay distributions, then box plots split by triage acuity |
| 4 · Disposition | Admitted or sent home? | Stay length for admitted vs. discharged patients; five cardiac condition groups |
| 5 · Explore | Your turn | Linked dashboard: a sticky filter bar plus four views that update together |

**Interactions:** scroll steps drive chart transitions (grow-in, split, morph, explode); click an acuity label or a condition row to filter every view; hover any mark for exact values and sample sizes. Story sentences are filled in automatically from the data.

> **Status (FP2):** the charts, scroll transitions and linked dashboard work. The scenes are currently ordered by finding (gap → acuity → pain → conditions); regrouping them into the journey stages above, with a sticky journey stepper, is the next step.

---

## Repository structure

```text
.
├── src/                              # Python data pipeline (run locally with MIMIC access)
│   ├── config.py                     # Shared paths (MIMIC_ED_DIR, MIMIC_HOSP_DIR) and cardiac categories
│   ├── profile_cardiac_demographics.py   # Step 1: builds the cardiac cohort
│   ├── create_non_cardiac_cohort.py      # Step 2: builds the non-cardiac comparison cohort
│   ├── prepare_q1_visualization_data.py  # Step 3: merges cohorts into one encounter table
│   ├── build_web_aggregates.py           # Step 4: aggregates it into the website's JSON
│   ├── make_synthetic_data.py            # Fake data for testing without MIMIC
│   ├── inspect_data.py                   # Exploratory: inspect raw tables
│   ├── profile_cardiac_candidates.py     # Exploratory: profile candidate cohort
│   └── classify_cardiac_candidates.py    # Exploratory: category counts
├── svelte-app/                       # The website (SvelteKit)
│   ├── src/routes/+page.svelte       # Page: hero, story scenes, explorer
│   ├── src/lib/story/                # Scrollytelling scenes and charts
│   ├── src/lib/components/           # Linked explorer charts and filter bar
│   └── static/data/ed_cube.json      # Aggregated data used by the site (no patient-level rows)
├── app/dashboard.py                  # Earlier Streamlit prototype (FP1, exploratory)
├── requirements.txt
└── README.md
```

Patient-level files are written to a local `data/` folder that is never committed.

---

## Quick start: view the website

You do **not** need MIMIC access for this step. The aggregated data file is already in the repository.

Requirements: [Node.js](https://nodejs.org) (LTS) and Git.

```powershell
git clone https://github.com/WoochangShin98/cardiac-ed-visualization.git
cd cardiac-ed-visualization\svelte-app
npm install
npm run dev
```

Open **http://localhost:5173**. Keep the terminal open while viewing; press `Ctrl+C` to stop.

---

## Rebuild the data from MIMIC-IV-ED

Only users with credentialed PhysioNet access to MIMIC-IV-ED can run this.

### 1. Set up Python

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pandas numpy
```

If PowerShell blocks activation: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

### 2. Point the scripts at your MIMIC files

The `ed` folder must contain `edstays.csv.gz`, `triage.csv.gz` and `diagnosis.csv.gz` (no need to unzip).

```powershell
$env:MIMIC_ED_DIR = "C:\path\to\mimic-iv-ed-2.2\ed"
# Optional, adds patient age (needs MIMIC-IV hosp/patients.csv.gz):
$env:MIMIC_HOSP_DIR = "C:\path\to\mimic-iv\hosp"
```

These settings last only for the current terminal window.

### 3. Run the pipeline (from the repository root)

```powershell
python src/profile_cardiac_demographics.py      # -> data/cardiac_candidate_encounters.csv
python src/create_non_cardiac_cohort.py         # -> data/non_cardiac_candidate_encounters.csv
python src/prepare_q1_visualization_data.py     # -> data/q1_ed_experience.csv (patient-level, local only)
python src/build_web_aggregates.py              # -> svelte-app/static/data/ed_cube.json
```

Then view the site as in [Quick start](#quick-start-view-the-website).

---

## Working without MIMIC access

To develop or test the website with fake numbers:

```powershell
python src/make_synthetic_data.py
python src/build_web_aggregates.py --input data/synthetic_q1_ed_experience.csv
```

This overwrites `ed_cube.json` with **synthetic** values. Never commit that version or present its numbers as findings; restore the real file with `git restore svelte-app/static/data/ed_cube.json`.

---

## Privacy and data use

MIMIC-IV-ED is a credentialed dataset governed by the PhysioNet Credentialed Health Data Use Agreement.

- This repository contains **no raw MIMIC files and no patient-level data**. `.gitignore` blocks `data/*` and `*.csv`.
- The website loads **only** `ed_cube.json`, which holds group-level summaries (counts, quantiles, histograms).
- Groups with fewer than **11** visits are hidden, small counts inside a group are hidden, and **all counts are rounded to the nearest 10** so hidden values cannot be recovered by subtraction.
- In line with the agreement, the code used to produce these results is shared openly here.
- Do not upload raw or patient-level MIMIC data to online AI tools.

---

## Definitions and limitations

| Term | Meaning |
|---|---|
| Cardiac visit | ED stay with ≥ 1 diagnosis title matching heart-related keywords |
| Condition group | MI / ischemia, heart failure, arrhythmia, other cardiovascular, chest pain / symptoms. A visit matching several is assigned to the most specific (in that order). |
| Acuity | Triage level, 1 (most urgent) to 5 |
| ED stay | Hours from ED arrival (`intime`) to departure (`outtime`) |
| Disposition | Admitted, sent home, or other (transfer, left without being seen, …) |

- The cardiac definition is **keyword-based and exploratory**, not clinically validated; chest pain does not confirm heart disease.
- MIMIC-IV-ED records only arrival and departure, so **waiting time to see a provider cannot be measured**; we show total ED stay.
- Pain scores that are not numbers (e.g. “asleep”) are treated as missing.
- Age requires linking MIMIC-IV hosp data and is omitted when that file is unavailable.
- All results are descriptive associations, not causes.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `npm` or `git` is not recognized | Install Node.js (LTS) or Git, then reopen the terminal |
| Site says “Could not load ed_cube.json” | Check that `svelte-app/static/data/ed_cube.json` exists |
| `cd svelte-app` fails | You are already inside `svelte-app`, or not in the repository folder; check the path shown in the prompt |
| Required input file not found | `MIMIC_ED_DIR` is wrong or was set in a different terminal; set it again |
| `git push` is rejected (fetch first) | Run `git pull --no-rebase --no-edit`, then `git push` |

---

*Created for CSCI 5609: Visualization, University of Minnesota Twin Cities. For exploratory visualization only, not clinical decision-making.*
