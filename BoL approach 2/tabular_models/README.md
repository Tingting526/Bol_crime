# Tabular Models

This folder contains tabular baselines for comparison with the Book-of-Life text approach.

Current notebook:

- `tabular_model_baselines.ipynb`: L2 logistic regression and gradient boosting with explanations.

Design:

- Features: `BoL approach 2/data/features/baseline_pre2000_bol_feature_index.csv`
- Raw feature values: `nlsy79_child_youngadult_selected_crime_features.csv`
- Target: `later_persistent_delinquency_contact_2000_2020`
- Target file: `BoL approach 2/data/targets/nlsy79_temporal_delinquency_targets_2000_2020.csv`

Outputs are written to `BoL approach 2/tabular_models/outputs/`.
