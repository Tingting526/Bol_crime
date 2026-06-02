# Tabular Based Models

Tabular baselines using the **original BoL approach** feature index.

The original BoL feature index has 864 year-specific features from 1986-2020. Because the target window is also 2000-2020, these notebooks mirror the original BoL person-specific cutoff logic before modeling:

- positive cases: keep only features before the second positive event year
- negative cases: keep only features before the last observed target year

Folders:

- `logistic_regression/`: L2 logistic regression notebook with feature importance/XAI and outputs
- `gradient_boosting/`: gradient boosting with decision stumps notebook and outputs

Shared comparison output:

- `tabular_original_bol_feature_model_comparison.csv`

Current test results:

| Model | Test accuracy | Test AUC |
|---|---:|---:|
| L2 Logistic Regression | 0.888 | 0.949 |
| Gradient Boosting Stumps | 0.814 | 0.904 |

Important: these results use the original BoL person-specific cutoff setup, not the stricter fixed pre-2000 temporal baseline. They are useful for comparing tabular models against the original BoL idea, but they should not be interpreted as the same prediction task as a fixed pre-2000 baseline.

Explainability outputs:

- Logistic regression:
  - `logistic_regression/logistic_regression_original_bol_features.ipynb`
  - `logistic_regression/outputs/l2_logistic_regression_coefficients.csv`
  - `logistic_regression/outputs/l2_logistic_regression_permutation_importance.csv`
  - `logistic_regression/outputs/l2_logistic_regression_linear_shap_global_importance.csv`
  - `logistic_regression/outputs/l2_logistic_regression_linear_shap_local_top_contributions.csv`
- Gradient boosting:
  - `gradient_boosting/outputs/gradient_boosting_stumps_feature_importance.csv`
  - `gradient_boosting/outputs/gradient_boosting_stumps_permutation_importance.csv`
  - `gradient_boosting/outputs/gradient_boosting_stumps_shap_style_global_importance.csv`
  - `gradient_boosting/outputs/gradient_boosting_stumps_shap_style_local_top_contributions.csv`

The external SHAP package is not required. The notebooks implement model-specific SHAP-style additive attributions:

- Logistic regression: exact linear logit contributions, `coefficient * (value - training_mean)`.
- Gradient boosting stumps: additive stump contributions centered around each stump's average training contribution.

Interpretation caution: because the original BoL setup allows person-specific cutoff years, feature importance can be influenced by age, survey timing, residence, and cutoff-adjacent variables. Treat these explanations as diagnostics for the original BoL setup, not as causal effects.
