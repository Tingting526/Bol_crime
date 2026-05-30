# BoL Approach 2: Temporal Baseline Setup

This folder contains the stricter baseline version of the Book-of-Life crime setup.

Design:

- Predictors: stable background variables and survey information before 2000.
- Target window: delinquency/contact outcomes observed from 2000 to 2020.
- Main target: `later_persistent_delinquency_contact_2000_2020`.

Folder structure:

- `notebooks/`: Jupyter notebooks for target construction and Book-of-Life text generation.
- `data/targets/`: temporal target files, target item list, and base rates.
- `data/features/`: pre-2000 BoL feature index and sample IDs.
- `data/books/`: rendered Book-of-Life JSON files.

Recommended order:

1. Run `notebooks/temporal_delinquency_targets_documentation.ipynb`.
2. Run `notebooks/temporal_bol_baseline_texts.ipynb`.
3. Run `notebooks/bol_prediction_trial.ipynb` for a first prediction smoke test.
