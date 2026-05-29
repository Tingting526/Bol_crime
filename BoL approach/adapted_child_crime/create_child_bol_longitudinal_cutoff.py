"""Create Book-of-Life texts with person-specific outcome cutoffs.

This is the longitudinal version of the child crime BoL generator. It constructs
later justice-contact outcomes from 2000-2020 and renders each child's book only
with information observed before that child's own cutoff year:

  - target = 1: cutoff is the first event year for "ever" targets, or the
    second positive event year for the repeated-contact target.
  - target = 0: cutoff is the last year in which a target item is observed.

The script does not call an LLM. It prepares the data for LLM or tabular models.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd


REPO = Path(__file__).resolve().parent
PROJECT_REPO = REPO.parent

DATA_PATH = (
    PROJECT_REPO
    / "output/share_with_team/nlsy79_child_youngadult_combined_bundle/"
    / "nlsy79_child_youngadult_selected_crime_features.csv"
)
CODEBOOK_PATH = (
    PROJECT_REPO
    / "output/share_with_team/nlsy79_child_youngadult_combined_bundle/"
    / "nlsy79_child_youngadult_selected_crime_features_codebook.csv"
)
OUT_DIR = REPO / "data/processed_child_crime_longitudinal"

BOOKS_JSON = OUT_DIR / "books_child_crime_longitudinal_cutoff.json"
TARGETS_CSV = OUT_DIR / "child_crime_longitudinal_targets.csv"
TARGET_ITEMS_CSV = OUT_DIR / "child_crime_later_justice_target_items.csv"
FEATURE_INDEX_CSV = OUT_DIR / "child_crime_longitudinal_feature_index.csv"

MISSING_CODES = {-1, -2, -3, -4, -5, -7}
TARGET_START_YEAR = 2000
TARGET_END_YEAR = 2020
DEFAULT_MAX_BOOKS = None  # Set to an integer for a smaller sample.
MAX_FEATURES_PER_YEAR = 30

RACE_LABELS = {1: "Hispanic", 2: "Black", 3: "Non-Black, non-Hispanic"}
SEX_LABELS = {1: "male", 2: "female"}


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float, np.integer, np.floating)) and int(value) in MISSING_CODES:
        return None
    if isinstance(value, str) and value.strip() in {str(x) for x in MISSING_CODES}:
        return None
    return value


def safe_int(value):
    try:
        if pd.isna(value):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def clean_question(question: str) -> str:
    question = str(question or "").strip()
    question = " ".join(question.split()).replace("#", "number of")
    if not question:
        return "value"
    letters = [ch for ch in question if ch.isalpha()]
    if sum(ch.isupper() for ch in letters) / max(1, len(letters)) > 0.7:
        question = question.lower()
    return question[:1].upper() + question[1:]


def render_value(code: str, value):
    value = clean_value(value)
    if value is None:
        return None
    as_int = safe_int(value)
    if code == "C0005300" and as_int in RACE_LABELS:
        return RACE_LABELS[as_int]
    if code == "C0005400" and as_int in SEX_LABELS:
        return SEX_LABELS[as_int]
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def sentence_for(code: str, value, codebook_by_code: dict) -> str | None:
    rendered = render_value(code, value)
    if rendered is None:
        return None
    meta = codebook_by_code.get(code, {})
    question = clean_question(meta.get("question", meta.get("variable", code)))
    return f"{question}: {rendered}"


def target_items(codebook: pd.DataFrame, columns: set[str]) -> pd.DataFrame:
    cb = codebook.copy()
    cb["year_num"] = pd.to_numeric(cb["survey_year"], errors="coerce")
    keep = (
        cb["csv_code"].isin(columns)
        & cb["variable"].isin(["YASR-66", "YASR-67"])
        & cb["year_num"].between(TARGET_START_YEAR, TARGET_END_YEAR)
    )
    items = cb.loc[keep, ["csv_code", "ref_id", "variable", "survey_year", "question"]].copy()
    items["year"] = pd.to_numeric(items["survey_year"], errors="coerce").astype(int)
    return items.sort_values(["year", "variable", "csv_code"])


def construct_later_justice_targets(data: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    years = sorted(items["year"].unique())
    rows = []
    for _, row in data.iterrows():
        observed_years = []
        positive_years = []
        positive_item_count = 0
        for year in years:
            codes = items.loc[items["year"] == year, "csv_code"].tolist()
            vals = [clean_value(row.get(code)) for code in codes]
            observed = [v for v in vals if v is not None]
            if observed:
                observed_years.append(year)
            if any(float(v) > 0 for v in observed):
                positive_years.append(year)
            positive_item_count += sum(float(v) > 0 for v in observed)

        if observed_years:
            ever = int(len(positive_years) > 0)
            repeated = int(len(set(positive_years)) >= 2)
            first_event_year = min(positive_years) if positive_years else np.nan
            repeated_event_year = sorted(set(positive_years))[1] if repeated else np.nan
            last_observed_year = max(observed_years)
            ever_cutoff = first_event_year if ever else last_observed_year
            repeated_cutoff = repeated_event_year if repeated else last_observed_year
        else:
            ever = np.nan
            repeated = np.nan
            first_event_year = np.nan
            repeated_event_year = np.nan
            last_observed_year = np.nan
            ever_cutoff = np.nan
            repeated_cutoff = np.nan

        rows.append(
            {
                "C0000100": row["C0000100"],
                "C0000200": row["C0000200"],
                "later_justice_contact_ever": ever,
                "later_justice_contact_repeated_years": repeated,
                "later_justice_positive_item_count": positive_item_count,
                "later_justice_positive_year_count": len(set(positive_years)),
                "later_justice_first_event_year": first_event_year,
                "later_justice_repeated_event_year": repeated_event_year,
                "later_justice_last_observed_year": last_observed_year,
                "cutoff_year_for_ever_target": ever_cutoff,
                "cutoff_year_for_repeated_target": repeated_cutoff,
            }
        )
    return pd.DataFrame(rows)


def build_feature_index(codebook: pd.DataFrame, columns: set[str]) -> pd.DataFrame:
    cb = codebook.copy()
    cb["year_num"] = pd.to_numeric(cb["survey_year"], errors="coerce")
    is_noncrime = ~(
        cb["topic"].eq("Crime & Substance Use")
        | cb["selection_source"].str.contains("crime_related_variable|constructed_target", na=False)
    )
    is_selected = cb["selection_source"].str.contains(
        "demographic_control|quick_curated|lasso_top30|mother_level_added_variable", na=False
    )
    keep = cb["csv_code"].isin(columns) & is_noncrime & is_selected
    features = cb.loc[keep, ["csv_code", "ref_id", "variable", "survey_year", "topic", "selection_source", "question"]].copy()
    features = features[~features["csv_code"].isin(["C0000100", "C0000200"])]
    return features.sort_values(["survey_year", "topic", "csv_code"])


def book_for_child(row: pd.Series, features: pd.DataFrame, codebook_by_code: dict, cutoff_year: int) -> str:
    child_id = int(row["C0000100"])
    mother_id = int(row["C0000200"]) if not pd.isna(row["C0000200"]) else "unknown"
    lines = [
        f"This Book of Life describes NLSY79 child respondent {child_id}, linked to mother ID {mother_id}.",
        f"Only information observed before {cutoff_year} is included.",
    ]

    static = features[features["survey_year"].eq("XRND")]
    static_parts = []
    for code in static["csv_code"]:
        sentence = sentence_for(code, row.get(code), codebook_by_code)
        if sentence:
            static_parts.append(sentence)
    if static_parts:
        lines.append("Stable background information: " + "; ".join(static_parts) + ".")

    yearly = features[~features["survey_year"].eq("XRND")].copy()
    yearly["year"] = pd.to_numeric(yearly["survey_year"], errors="coerce")
    yearly = yearly[yearly["year"].notna() & (yearly["year"] < cutoff_year)]
    yearly = yearly.sort_values(["year", "topic", "csv_code"])
    for year, group in yearly.groupby("year"):
        parts = []
        for code in group["csv_code"]:
            sentence = sentence_for(code, row.get(code), codebook_by_code)
            if sentence:
                parts.append(sentence)
            if len(parts) >= MAX_FEATURES_PER_YEAR:
                break
        if parts:
            lines.append(f"In {int(year)}: " + "; ".join(parts) + ".")
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATA_PATH)
    codebook = pd.read_csv(CODEBOOK_PATH, dtype=str).fillna("")

    items = target_items(codebook, set(data.columns))
    targets = construct_later_justice_targets(data, items)
    features = build_feature_index(codebook, set(data.columns))
    codebook_by_code = codebook.set_index("csv_code").to_dict(orient="index")

    eligible = targets[targets["later_justice_contact_repeated_years"].notna()].copy()
    eligible = eligible.sort_values(["later_justice_contact_repeated_years", "C0000100"], ascending=[False, True])
    if DEFAULT_MAX_BOOKS is not None:
        eligible = eligible.head(DEFAULT_MAX_BOOKS)

    data_by_id = data.set_index("C0000100", drop=False)
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    books = {}
    for _, target in eligible.iterrows():
        child_id = int(target["C0000100"])
        cutoff = safe_int(target["cutoff_year_for_repeated_target"])
        if cutoff is None:
            continue
        row = data_by_id.loc[child_id]
        books[str(child_id)] = {
            "text": book_for_child(row, features, codebook_by_code, cutoff),
            "generated_at": now,
            "source": "nlsy79_child_youngadult_selected_crime_features",
            "target": "later_justice_contact_repeated_years",
            "cutoff_year": cutoff,
        }

    items.to_csv(TARGET_ITEMS_CSV, index=False)
    targets.to_csv(TARGETS_CSV, index=False)
    features.to_csv(FEATURE_INDEX_CSV, index=False)
    BOOKS_JSON.write_text(json.dumps(books, indent=2, sort_keys=True))

    (OUT_DIR / "README.md").write_text(
        "\n".join(
            [
                "# Child Crime Books with Person-Specific Cutoffs",
                "",
                "Generated by `create_child_bol_longitudinal_cutoff.py`.",
                "",
                "Target window: later justice contact from 2000-2020.",
                "Target items: probation (`YASR-67`) and corrections/jail/reform (`YASR-66`).",
                "For positives, books include only features before the repeated-contact event year.",
                "For negatives, books include only features before the last observed target year.",
                "",
            ]
        )
    )

    print(f"Target items: {len(items)}")
    print(f"Eligible target rows: {len(eligible)}")
    print(f"Books written: {len(books)}")
    print(f"Repeated-contact base rate: {eligible['later_justice_contact_repeated_years'].mean():.3f}")
    print(f"Wrote books to {BOOKS_JSON.relative_to(REPO)}")
    print(f"Wrote targets to {TARGETS_CSV.relative_to(REPO)}")
    print(f"Wrote feature index to {FEATURE_INDEX_CSV.relative_to(REPO)}")


if __name__ == "__main__":
    main()
