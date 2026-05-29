"""Compare LLM Book-of-Life predictions with tabular logistic regression.

The logistic model uses the same variables that were rendered into the child
Book-of-Life sample. It trains on all labeled children except the 30 sampled
LLM cases, then evaluates on exactly those same sampled cases.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


REPO = Path(__file__).resolve().parent
PROJECT_REPO = REPO.parent
OUT_DIR = REPO / "data/processed_child_crime"

DATA_PATH = (
    PROJECT_REPO
    / "output/share_with_team/nlsy79_child_youngadult_combined_bundle/"
    / "nlsy79_child_youngadult_selected_crime_features.csv"
)
TARGETS_PATH = (
    PROJECT_REPO
    / "output/child_youngadult/constructed_justice_contact_baseline/"
    / "constructed_justice_contact_targets.csv"
)
FEATURE_INDEX_PATH = OUT_DIR / "child_crime_bol_feature_index.csv"
SAMPLE_IDS_PATH = OUT_DIR / "child_crime_sample_ids.csv"
LLM_PREDICTIONS_PATH = OUT_DIR / "child_crime_llm_predictions.csv"

COMPARISON_CSV = OUT_DIR / "child_crime_llm_vs_logit_comparison.csv"
LOGIT_PREDICTIONS_CSV = OUT_DIR / "child_crime_logit_same_features_predictions.csv"

TARGET = "justice_contact_repeated"
LLM_THRESHOLD = 0.25
MISSING_CODES = {-1, -2, -3, -4, -5, -7}


def clean_missing(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
        out.loc[out[col].isin(MISSING_CODES), col] = np.nan
    return out


def metrics(y_true: np.ndarray, prob: np.ndarray, threshold: float) -> dict:
    pred = (prob >= threshold).astype(int)
    tp = int(((pred == 1) & (y_true == 1)).sum())
    tn = int(((pred == 0) & (y_true == 0)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum())
    fn = int(((pred == 0) & (y_true == 1)).sum())
    return {
        "threshold": threshold,
        "accuracy": accuracy_score(y_true, pred),
        "auc": roc_auc_score(y_true, prob) if len(np.unique(y_true)) > 1 else np.nan,
        "sensitivity_tpr": tp / (tp + fn) if (tp + fn) else np.nan,
        "specificity_tnr": tn / (tn + fp) if (tn + fp) else np.nan,
        "fpr": fp / (fp + tn) if (fp + tn) else np.nan,
        "fnr": fn / (fn + tp) if (fn + tp) else np.nan,
        "predicted_positive_rate": float(pred.mean()),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def best_accuracy_threshold(y_true: np.ndarray, prob: np.ndarray) -> float:
    grid = np.unique(np.concatenate([np.arange(0.05, 0.951, 0.05), prob]))
    scores = [(accuracy_score(y_true, (prob >= t).astype(int)), t) for t in grid]
    return float(sorted(scores, reverse=True)[0][1])


def main() -> None:
    data = pd.read_csv(DATA_PATH)
    targets = pd.read_csv(TARGETS_PATH)
    feature_index = pd.read_csv(FEATURE_INDEX_PATH)
    sample_ids = pd.read_csv(SAMPLE_IDS_PATH)["C0000100"].astype(int).tolist()

    feature_cols = [c for c in feature_index["csv_code"].tolist() if c in data.columns]
    model_df = data[["C0000100"] + feature_cols].merge(
        targets[["C0000100", TARGET]],
        on="C0000100",
        how="inner",
    )
    model_df = model_df[model_df[TARGET].notna()].copy()
    model_df = clean_missing(model_df, feature_cols)

    test_mask = model_df["C0000100"].isin(sample_ids)
    train = model_df[~test_mask].copy()
    test = model_df[test_mask].copy()

    categorical_cols = [c for c in ["C0005300", "C0005400"] if c in feature_cols]
    numeric_cols = [c for c in feature_cols if c not in categorical_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                numeric_cols,
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            ),
        ],
        remainder="drop",
    )

    clf = Pipeline(
        [
            ("preprocess", preprocessor),
            ("logit", LogisticRegression(max_iter=1000, class_weight="balanced", solver="liblinear")),
        ]
    )

    clf.fit(train[feature_cols], train[TARGET].astype(int))
    train_prob = clf.predict_proba(train[feature_cols])[:, 1]
    test_prob = clf.predict_proba(test[feature_cols])[:, 1]

    logit_threshold = best_accuracy_threshold(train[TARGET].astype(int).to_numpy(), train_prob)
    logit_preds = pd.DataFrame(
        {
            "C0000100": test["C0000100"].astype(int),
            "y_true": test[TARGET].astype(int),
            "logit_probability": test_prob,
            "logit_prediction_threshold_0_5": (test_prob >= 0.5).astype(int),
            "logit_prediction_train_best_threshold": (test_prob >= logit_threshold).astype(int),
        }
    )
    logit_preds.to_csv(LOGIT_PREDICTIONS_CSV, index=False)

    rows = []
    y_test = test[TARGET].astype(int).to_numpy()
    for threshold_name, threshold in [("0.50", 0.5), ("train_best_accuracy", logit_threshold)]:
        row = metrics(y_test, test_prob, threshold)
        row.update({"model": "tabular_logistic_regression", "threshold_name": threshold_name})
        rows.append(row)

    if LLM_PREDICTIONS_PATH.exists():
        llm = pd.read_csv(LLM_PREDICTIONS_PATH)
        llm = llm[llm["y_true"].notna()].copy()
        y_llm = llm["y_true"].astype(int).to_numpy()
        p_llm = llm["probability"].to_numpy()
        for threshold_name, threshold in [("0.50", 0.5), ("0.25", LLM_THRESHOLD)]:
            row = metrics(y_llm, p_llm, threshold)
            row.update({"model": "book_of_life_llm", "threshold_name": threshold_name})
            rows.append(row)

    comparison = pd.DataFrame(rows)
    first_cols = ["model", "threshold_name", "threshold", "accuracy", "auc"]
    comparison = comparison[first_cols + [c for c in comparison.columns if c not in first_cols]]
    comparison.to_csv(COMPARISON_CSV, index=False)

    print(f"Train N: {len(train)} | Test N: {len(test)} | Features: {len(feature_cols)}")
    print(f"Logistic train-best threshold: {logit_threshold:.3f}")
    print("\nComparison on the same sampled children:")
    print(comparison.to_string(index=False))
    print(f"\nWrote comparison to {COMPARISON_CSV.relative_to(REPO)}")
    print(f"Wrote logistic predictions to {LOGIT_PREDICTIONS_CSV.relative_to(REPO)}")


if __name__ == "__main__":
    main()
