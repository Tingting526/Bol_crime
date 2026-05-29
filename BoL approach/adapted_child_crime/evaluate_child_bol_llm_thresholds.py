"""Evaluate thresholds for the child Book-of-Life LLM predictions."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parent
OUT_DIR = REPO / "data/processed_child_crime"
PREDICTIONS_CSV = OUT_DIR / "child_crime_llm_predictions.csv"
THRESHOLDS_CSV = OUT_DIR / "child_crime_llm_threshold_eval.csv"


def metrics_at_threshold(y_true: np.ndarray, prob: np.ndarray, threshold: float) -> dict:
    pred = (prob >= threshold).astype(int)
    tp = int(((pred == 1) & (y_true == 1)).sum())
    tn = int(((pred == 0) & (y_true == 0)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum())
    fn = int(((pred == 0) & (y_true == 1)).sum())
    return {
        "threshold": threshold,
        "accuracy": (tp + tn) / len(y_true),
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
    preds["y_true"] = preds["y_true"].astype(int)

    grid = np.round(np.arange(0.05, 0.951, 0.05), 2)
    exact = np.unique(preds["probability"].to_numpy())
    thresholds = np.unique(np.concatenate([grid, exact]))

    rows = [metrics_at_threshold(preds["y_true"].to_numpy(), preds["probability"].to_numpy(), float(t)) for t in thresholds]
    out = pd.DataFrame(rows).sort_values(["accuracy", "sensitivity_tpr"], ascending=[False, False])
    out.to_csv(THRESHOLDS_CSV, index=False)

    best = out.iloc[0]
    print(f"Evaluated {len(out)} thresholds on {len(preds)} labeled rows.")
    print(
        "Best threshold by accuracy: "
        f"{best['threshold']:.2f} | accuracy={best['accuracy']:.3f} | "
        f"TP={int(best['tp'])}, TN={int(best['tn'])}, FP={int(best['fp'])}, FN={int(best['fn'])}"
    )
    print("\nTop thresholds:")
    print(out.head(10).to_string(index=False))
    print(f"\nWrote threshold table to {THRESHOLDS_CSV.relative_to(REPO)}")


if __name__ == "__main__":
    main()
