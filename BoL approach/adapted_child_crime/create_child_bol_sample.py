"""Create a small Book-of-Life sample from the NLSY79 Child/Young Adult data.

This script does not call an LLM and does not need an API key. It converts the
cleaned child/young-adult feature subset from the crime project into a
Book-of-Life-style JSON file that can be inspected locally or plugged into the
starter notebooks later.

Outputs:
  data/processed_child_crime/books_child_crime_sample.json
  data/processed_child_crime/child_crime_targets_sample.csv
  data/processed_child_crime/child_crime_sample_ids.csv
  data/processed_child_crime/child_crime_bol_feature_index.csv
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
CURATED_FEATURES_PATH = PROJECT_REPO / "output/child_youngadult/quick_curated_logit/curated_predictor_dictionary.csv"
TEAM_FEATURE_MATCHES_PATH = PROJECT_REPO / "output/child_youngadult/team_feature_models/team_feature_codebook_matches.csv"
TEAM_LASSO_TOP_PATH = PROJECT_REPO / "output/child_youngadult/team_feature_models/top30_team_feature_lasso_selected_variables.csv"
SUBSTANTIVE_LASSO_TOP_PATH = PROJECT_REPO / "output/child_youngadult/lasso_substantive_variables/top30_lasso_selected_variables_by_target.csv"
JUSTICE_TARGETS_PATH = (
    PROJECT_REPO
    / "output/child_youngadult/constructed_justice_contact_baseline/"
    / "constructed_justice_contact_targets.csv"
)

OUT_DIR = REPO / "data/processed_child_crime"
BOOKS_JSON = OUT_DIR / "books_child_crime_sample.json"
TARGETS_CSV = OUT_DIR / "child_crime_targets_sample.csv"
SAMPLE_IDS_CSV = OUT_DIR / "child_crime_sample_ids.csv"
FEATURE_INDEX_CSV = OUT_DIR / "child_crime_bol_feature_index.csv"

SAMPLE_N = 120
MAX_FEATURES_PER_YEAR = 24
MAX_STATIC_FEATURES = 16
MAX_PREDICTOR_YEAR = 1998
MAX_TEAM_SUGGESTED_PER_GROUP = 8
MAX_LASSO_FEATURES_PER_TARGET = 25

MISSING_CODES = {-1, -2, -3, -4, -5, -7}

RACE_LABELS = {
    1: "Hispanic",
    2: "Black",
    3: "Non-Black, non-Hispanic",
}
SEX_LABELS = {
    1: "male",
    2: "female",
}

SOURCE_ALIASES = {
    "quick_curated_logit_predictor": "curated_predictor",
    "quick_curated_predictor": "curated_predictor",
    "team_feature_lasso_top30": "team_feature_lasso_top",
    "substantive_lasso_top30": "substantive_lasso_top",
}


def safe_int(value):
    try:
        if pd.isna(value):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def clean_value(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float, np.integer, np.floating)) and int(value) in MISSING_CODES:
        return None
    if isinstance(value, str) and value.strip() in {str(x) for x in MISSING_CODES}:
        return None
    return value


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


def clean_question(question: str) -> str:
    question = str(question or "").strip()
    question = " ".join(question.split())
    if not question:
        return "value"
    question = question.replace("#", "number of")
    letters = [ch for ch in question if ch.isalpha()]
    upper_share = sum(ch.isupper() for ch in letters) / max(1, len(letters))
    if upper_share > 0.7:
        question = question.lower()
    return question[:1].upper() + question[1:]


def sentence_for(code: str, value, codebook_by_code: dict) -> str | None:
    rendered = render_value(code, value)
    if rendered is None:
        return None
    meta = codebook_by_code.get(code, {})
    variable = meta.get("variable") or code
    question = clean_question(meta.get("question", variable))
    return f"{question}: {rendered}"


def _add_source(source_map: dict[str, set[str]], code: str, source: str) -> None:
    if not isinstance(code, str) or not code:
        return
    source = SOURCE_ALIASES.get(source, source)
    source_map.setdefault(code, set()).add(source)


def _load_codes_from_curated(source_map: dict[str, set[str]]) -> None:
    curated = pd.read_csv(CURATED_FEATURES_PATH)
    curated["year_num"] = pd.to_numeric(curated["year"], errors="coerce")
    keep = curated["year_num"].isna() | (curated["year_num"] <= MAX_PREDICTOR_YEAR)
    for code in curated.loc[keep, "csv_code"].dropna().unique():
        _add_source(source_map, code, "quick_curated_predictor")


def _load_codes_from_team_suggestions(source_map: dict[str, set[str]]) -> None:
    if not TEAM_FEATURE_MATCHES_PATH.exists():
        return
    matches = pd.read_csv(TEAM_FEATURE_MATCHES_PATH)
    matches["year_num"] = pd.to_numeric(matches["year"], errors="coerce")
    matches = matches[matches["year_num"].isna() | (matches["year_num"] <= MAX_PREDICTOR_YEAR)].copy()
    matches = matches[matches["feature_group"].notna()].copy()

    selected = []
    for _, group in matches.sort_values(["feature_group", "year_num", "csv_code"]).groupby("feature_group"):
        selected.append(group.head(MAX_TEAM_SUGGESTED_PER_GROUP))
    if not selected:
        return
    selected = pd.concat(selected, ignore_index=True)
    for code in selected["csv_code"].dropna().unique():
        _add_source(source_map, code, "team_suggested_feature")


def _load_codes_from_lasso(path: Path, source: str, source_map: dict[str, set[str]]) -> None:
    if not path.exists():
        return
    lasso = pd.read_csv(path)
    if "abs_coefficient" in lasso.columns:
        lasso["abs_coefficient_num"] = pd.to_numeric(lasso["abs_coefficient"], errors="coerce")
        lasso = lasso.sort_values(["target", "abs_coefficient_num"], ascending=[True, False])
    elif "rank" in lasso.columns:
        lasso["rank_num"] = pd.to_numeric(lasso["rank"], errors="coerce")
        lasso = lasso.sort_values(["target", "rank_num"], ascending=[True, True])
    selected = []
    for _, group in lasso.groupby("target"):
        group = group.copy()
        group["year_num"] = pd.to_numeric(group.get("year", group.get("survey_year")), errors="coerce")
        group = group[group["year_num"].isna() | (group["year_num"] <= MAX_PREDICTOR_YEAR)]
        selected.append(group.head(MAX_LASSO_FEATURES_PER_TARGET))
    if not selected:
        return
    selected = pd.concat(selected, ignore_index=True)
    for code in selected["csv_code"].dropna().unique():
        _add_source(source_map, code, source)


def build_feature_index(codebook: pd.DataFrame) -> pd.DataFrame:
    source_map: dict[str, set[str]] = {}

    if "selection_source" in codebook.columns:
        selected_feature_sources = codebook[
            codebook["selection_source"].str.contains("quick_curated|lasso_top30|demographic_control", na=False)
        ].copy()
        selected_feature_sources["year_num"] = pd.to_numeric(selected_feature_sources["survey_year"], errors="coerce")
        selected_feature_sources = selected_feature_sources[
            selected_feature_sources["year_num"].isna()
            | (selected_feature_sources["year_num"] <= MAX_PREDICTOR_YEAR)
        ]
        selected_feature_sources = selected_feature_sources[selected_feature_sources["topic"] != "Crime & Substance Use"]
        for _, row in selected_feature_sources.iterrows():
            for source in str(row["selection_source"]).split(";"):
                _add_source(source_map, row["csv_code"], source.strip())

    _load_codes_from_curated(source_map)
    _load_codes_from_team_suggestions(source_map)
    _load_codes_from_lasso(TEAM_LASSO_TOP_PATH, "team_feature_lasso_top", source_map)
    _load_codes_from_lasso(SUBSTANTIVE_LASSO_TOP_PATH, "substantive_lasso_top", source_map)

    keep_codes = sorted(source_map)
    feature_index = codebook[codebook["csv_code"].isin(keep_codes)].copy()
    feature_index = feature_index[~feature_index["csv_code"].isin(["C0000100", "C0000200"])].copy()
    feature_index = feature_index[feature_index["topic"] != "Crime & Substance Use"].copy()

    control_codes = ["C0005300", "C0005400", "C0005500", "C0005700", "C0005800", "C0007000"]
    controls = codebook[codebook["csv_code"].isin(control_codes)].copy()
    feature_index = pd.concat([controls, feature_index], ignore_index=True).drop_duplicates("csv_code")
    for code in control_codes:
        _add_source(source_map, code, "demographic_control")
    feature_index["selection_source"] = feature_index["csv_code"].map(
        lambda code: "; ".join(sorted(source_map.get(code, {"demographic_control"})))
    )
    feature_index["year_num"] = pd.to_numeric(feature_index["survey_year"], errors="coerce")

    cols = ["csv_code", "ref_id", "variable", "survey_year", "topic", "selection_source", "question"]
    return feature_index[cols].sort_values(["survey_year", "topic", "csv_code"])


def choose_sample_ids(data: pd.DataFrame, justice_targets: pd.DataFrame | None) -> pd.DataFrame:
    targets = data[["C0000100", "C0000200", "target_property_ever", "target_violent_ever"]].copy()

    if justice_targets is not None:
        targets = targets.merge(
            justice_targets[
                [
                    "C0000100",
                    "justice_contact_ever",
                    "justice_contact_repeated",
                    "justice_contact_positive_item_count",
                    "justice_contact_first_positive_year",
                ]
            ],
            on="C0000100",
            how="left",
        )

    balance_col = "justice_contact_repeated" if "justice_contact_repeated" in targets.columns else "target_violent_ever"

    if TARGETS_CSV.exists():
        existing = pd.read_csv(TARGETS_CSV)
        existing = existing[existing["C0000100"].isin(targets["C0000100"])].copy()
        existing_ids = set(existing["C0000100"])
    else:
        existing = targets.iloc[0:0].copy()
        existing_ids = set()

    remaining = targets[~targets["C0000100"].isin(existing_ids)].copy()
    need_n = max(0, SAMPLE_N - len(existing))
    existing_pos = 0
    existing_neg = 0
    if len(existing) > 0:
        existing_pos = int((existing[balance_col] == 1).sum())
        existing_neg = int((existing[balance_col] == 0).sum())
    target_pos = SAMPLE_N // 2
    need_pos = max(0, target_pos - existing_pos)
    need_neg = max(0, need_n - need_pos)

    positives = remaining[remaining[balance_col] == 1].sample(
        n=min(need_pos, int((remaining[balance_col] == 1).sum())),
        random_state=1979 + len(existing),
    )
    negatives = remaining[remaining[balance_col] == 0].sample(
        n=min(need_neg, int((remaining[balance_col] == 0).sum())),
        random_state=1980 + len(existing),
    )
    sample = pd.concat([existing, positives, negatives], ignore_index=True)
    return sample.sample(frac=1, random_state=2026).reset_index(drop=True)


def book_for_child(row: pd.Series, feature_index: pd.DataFrame, codebook_by_code: dict) -> str:
    child_id = int(row["C0000100"])
    mother_id = int(row["C0000200"]) if not pd.isna(row["C0000200"]) else "unknown"

    static_codes = feature_index[feature_index["survey_year"].eq("XRND")]["csv_code"].tolist()
    year_features = feature_index[~feature_index["survey_year"].eq("XRND")].copy()
    year_features["year_num"] = pd.to_numeric(year_features["survey_year"], errors="coerce")
    year_features = year_features[year_features["year_num"].notna()].sort_values(["year_num", "topic", "csv_code"])

    lines = [
        f"This Book of Life describes NLSY79 child respondent {child_id}, linked to mother ID {mother_id}.",
    ]

    static_parts = []
    for code in static_codes:
        if code in row and len(static_parts) < MAX_STATIC_FEATURES:
            sentence = sentence_for(code, row[code], codebook_by_code)
            if sentence:
                static_parts.append(sentence)
    if static_parts:
        lines.append("Stable background information: " + "; ".join(static_parts) + ".")

    for year, group in year_features.groupby("year_num"):
        parts = []
        for _, feature in group.iterrows():
            code = feature["csv_code"]
            if code not in row:
                continue
            sentence = sentence_for(code, row[code], codebook_by_code)
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
    feature_index = build_feature_index(codebook)
    feature_index = feature_index[feature_index["csv_code"].isin(data.columns)].copy()

    justice_targets = pd.read_csv(JUSTICE_TARGETS_PATH) if JUSTICE_TARGETS_PATH.exists() else None
    sample_targets = choose_sample_ids(data, justice_targets)
    sample_data = data[data["C0000100"].isin(sample_targets["C0000100"])].copy()
    sample_data = sample_targets[["C0000100"]].merge(sample_data, on="C0000100", how="left")

    codebook_by_code = codebook.set_index("csv_code").to_dict(orient="index")
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    books = {}
    for _, row in sample_data.iterrows():
        child_id = int(row["C0000100"])
        books[str(child_id)] = {
            "text": book_for_child(row, feature_index, codebook_by_code),
            "generated_at": now,
            "source": "nlsy79_child_youngadult_selected_crime_features",
        }

    sample_targets.to_csv(TARGETS_CSV, index=False)
    sample_targets[["C0000100", "C0000200"]].to_csv(SAMPLE_IDS_CSV, index=False)
    feature_index.to_csv(FEATURE_INDEX_CSV, index=False)
    BOOKS_JSON.write_text(json.dumps(books, indent=2, sort_keys=True))

    (OUT_DIR / "README.md").write_text(
        "\n".join(
            [
                "# Child/Young Adult Book-of-Life Sample",
                "",
                "This folder is generated by `create_child_bol_sample.py` and does not require an API key.",
                "",
                "Files:",
                "- `books_child_crime_sample.json`: rendered Book-of-Life texts.",
                "- `child_crime_targets_sample.csv`: target labels for the sampled children.",
                "- `child_crime_sample_ids.csv`: child and mother IDs for the sample.",
                "- `child_crime_bol_feature_index.csv`: variables used in the rendered texts.",
                "",
                "The books use non-crime predictors up to 1998 from curated predictors, teammate suggestions,",
                "team-feature LASSO selections, and substantive LASSO selections.",
                "Set `MAX_PREDICTOR_YEAR = 1996` in the script for a stricter pre-1998 setup.",
                "Crime outcomes are kept out of the book text and stored only in the target CSV.",
                "",
            ]
        )
    )

    lengths = [len(v["text"]) for v in books.values()]
    print(f"Wrote {len(books)} child Books of Life to {BOOKS_JSON.relative_to(REPO)}")
    print(f"Wrote targets to {TARGETS_CSV.relative_to(REPO)}")
    print(f"Wrote feature index to {FEATURE_INDEX_CSV.relative_to(REPO)}")
    print(f"Average book length: {int(np.mean(lengths))} characters")
    first_key = sorted(books)[0]
    print("\n=== Sample book excerpt ===")
    print(books[first_key]["text"][:1800])


if __name__ == "__main__":
    main()
