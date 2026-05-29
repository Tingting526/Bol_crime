"""Evaluate thresholds for longitudinal child crime LLM predictions."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parent
OUT_DIR = REPO / "data/processed_child_crime_longitudinal"
PREDICTIONS_CSV = OUT_DIR / "child_crime_longitudinal_llm_predictions_120.csv"
THRESHOLDS_CSV = OUT_DIR / "child_crime_longitudinal_llm_threshold_eval_120.csv"


def auc_rank(y: np.ndarray, p: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return np.nan
    ranks = pd.Series(p).rank(method="average").to_numpy()
    n_pos = (y == 1).sum()
    n_neg = (y == 0).sum()
    return (ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def metrics(y: np.ndarray, p: np.ndarray, threshold: float) -> dict:
    pred = (p >= threshold).astype(int)
    tp = int(((pred == 1) & (y == 1)).sum())
    tn = int(((pred == 0) & (y == 0)).sum())
    fp = int(((pred == 1) & (y == 0)).sum())
    fn = int(((pred == 0) & (y == 1)).sum())
    return {
        "threshold": threshold,
        "accuracy": (tp + tn) / len(y),
        "auc": auc_rank(y, p),
        "sensitivity_tpr": tp / (tp + fn) if (tp + fn) else np.nan,
        "specificity_tnr": tn / (tn + fp) if (tn + fp) else np.nan,
        "fpr": fp / (fp + tn) if (fp + tn) else np.nan,
        "fnr": fn / (fn + tp) if (fn + tp) else np.nan,
        "predicted_positive_rate": pred.mean(),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def main() -> None:
    preds = pd.read_csv(PREDICTIONS_CSV)
    preds = preds[preds["y_true"].notna() & preds["probability"].notna()].copy()
    y = preds["y_true"].astype(int).to_numpy()
    p = preds["probability"].astype(float).to_numpy()
    thresholds = np.unique(np.concatenate([np.arange(0.05, 0.951, 0.05), p]))
    out = pd.DataFrame([metrics(y, p, float(t)) for t in thresholds])
    out = out.sort_values(["accuracy", "sensitivity_tpr"], ascending=[False, False])
    out.to_csv(THRESHOLDS_CSV, index=False)

    print(f"Evaluated {len(out)} thresholds on {len(preds)} labeled rows.")
    print("Top thresholds:")
    print(out.head(12).to_string(index=False))
    print(f"\nWrote {THRESHOLDS_CSV.relative_to(REPO)}")


if __name__ == "__main__":
    main()
