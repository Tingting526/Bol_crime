"""Create Books of Life for the broad persistent delinquency/contact target.

Target:
  later_persistent_delinquency_contact = 1 if a child/young adult has direct
  delinquency/contact indicators in at least two different later survey years
  from 2000-2020.

Cutoff:
  - positive cases: include predictors before the second positive event year
  - negative cases: include predictors before the last observed target year
"""
from __future__ import annotations

import datetime as dt
import json
import re
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
BROAD_TARGETS_PATH = REPO / "data/processed_child_crime_longitudinal/later_broad_delinquency_contact_targets.csv"
BROAD_ITEMS_PATH = REPO / "data/processed_child_crime_longitudinal/later_broad_delinquency_contact_target_items.csv"

OUT_DIR = REPO / "data/processed_child_crime_broad_persistent"
BOOKS_JSON = OUT_DIR / "books_child_crime_broad_persistent_cutoff.json"
TARGETS_CSV = OUT_DIR / "child_crime_broad_persistent_targets.csv"
FEATURE_INDEX_CSV = OUT_DIR / "child_crime_broad_persistent_feature_index.csv"
SAMPLE_IDS_CSV = OUT_DIR / "child_crime_broad_persistent_sample_ids_120.csv"
SAMPLE_BOOKS_JSON = OUT_DIR / "books_child_crime_broad_persistent_sample_120.json"

TARGET = "later_persistent_delinquency_contact"
MISSING_CODES = {-1, -2, -3, -4, -5, -7}
MAX_FEATURES_PER_YEAR = 30
SAMPLE_N = 120

RACE_LABELS = {1: "Hispanic", 2: "Black", 3: "Non-Black, non-Hispanic"}
SEX_LABELS = {1: "male", 2: "female"}

DOMAIN_PATTERNS = {
    "behavioral/externalizing": (
        "BEHAVIOR PROBLEMS|BPI|ARGUES|CHEATS|LIES|DISOBEDIENT|TEMPER|IMPULSIVE|"
        "HANGS AROUND|TROUBLE|SORRY AFTER"
    ),
    "school/achievement": (
        "SCHOOL|TEACHER|HOMEWORK|GRADE|CLASSWORK|TRAINING|PIAT|MATH|READING|ATTEND"
    ),
    "family/home": (
        "MOTHER|FATHER|PARENT|HOME|HOUSEHOLD|FAMILY|RULES|TALKS|MEETING"
    ),
    "socioeconomic/work": (
        "POVERTY|INCOME|WELFARE|AFDC|FOOD STAMP|EMPLOY|WORK|JOB"
    ),
    "peer/neighborhood": (
        "PEER|FRIEND|NEIGHBOR|WEAPON|GANG|KIDS WHO GET INTO"
    ),
    "substance/risk behavior": (
        "ALCOHOL|DRUG|MARIJUANA|SMOK|CIGARETTE"
    ),
    "prior delinquency/contact": (
        "FIGHT|HURT SOMEONE|DAMAGED|PROBATION|CORRECTIONS|JAIL|CONVICTED|COURT"
    ),
}

GROUP_ORDER = [
    "background",
    "family/home",
    "socioeconomic/work",
    "school/achievement",
    "behavioral/externalizing",
    "peer/neighborhood",
    "substance/risk behavior",
    "prior delinquency/contact",
    "health",
    "other",
]


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
    meta = codebook_by_code.get(code, {})
    question = clean_question(meta.get("question", meta.get("variable", code)))
    raw_value = clean_value(value)
    if raw_value is None:
        return None
    as_int = safe_int(raw_value)
    question_upper = question.upper()
    yes_no_like = (
        as_int in (0, 1)
        and (
            question_upper.startswith(("HAS ", "HAVE ", "HAD ", "EVER ", "WAS ", "IS ", "DOES ", "DID "))
            or " EVER " in question_upper
            or " IN PAST " in question_upper
            or " IN LAST YEAR " in question_upper
        )
    )
    rendered = "yes" if yes_no_like and as_int == 1 else "no" if yes_no_like and as_int == 0 else render_value(code, raw_value)
    if rendered is None:
        return None
    return f"{question}: {rendered}"


def assign_feature_group(row: pd.Series) -> str:
    text = f"{row.get('variable', '')} {row.get('question', '')} {row.get('topic', '')}".upper()
    if row.get("survey_year") == "XRND" or row.get("csv_code") in {"C0005300", "C0005400", "C0005500", "C0005700", "C0005800", "C0007000"}:
        return "background"
    if "HEALTH" in text or "HEIGHT" in text:
        return "health"
    for group, pattern in DOMAIN_PATTERNS.items():
        if re.search(pattern, text):
            return group
    return "other"


def build_feature_index(codebook: pd.DataFrame, columns: set[str]) -> pd.DataFrame:
    cb = codebook.copy()
    text = (cb["variable"] + " " + cb["question"] + " " + cb["topic"]).str.upper()
    is_constructed = cb["selection_source"].str.contains("constructed_target", na=False)
    is_selected = cb["selection_source"].str.contains(
        "demographic_control|quick_curated|lasso_top30|mother_level_added_variable", na=False
    )
    is_domain_relevant = pd.Series(False, index=cb.index)
    for pattern in DOMAIN_PATTERNS.values():
        is_domain_relevant = is_domain_relevant | text.str.contains(pattern, regex=True)

    # Keep selected predictors and add theoretically relevant predictors,
    # including prior risk behavior. The renderer later applies the
    # person-specific cutoff, so post-outcome values never enter a book.
    keep = cb["csv_code"].isin(columns) & ~is_constructed & (is_selected | is_domain_relevant)
    features = cb.loc[keep, ["csv_code", "ref_id", "variable", "survey_year", "topic", "selection_source", "question"]].copy()
    features = features[~features["csv_code"].isin(["C0000100", "C0000200"])]
    features["feature_group"] = features.apply(assign_feature_group, axis=1)
    features["year_num"] = pd.to_numeric(features["survey_year"], errors="coerce")

    # Avoid overly repetitive current-sentence charge detail fields; keep the
    # direct behavior/contact indicators instead.
    q = features["question"].str.upper()
    features = features[~q.str.contains("CHARGES R CONVICTED OF FOR CURRENT", na=False)]

    return features.sort_values(["survey_year", "feature_group", "topic", "csv_code"])


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
    yearly = yearly.sort_values(["year", "feature_group", "topic", "csv_code"])
    for year, group in yearly.groupby("year"):
        group_lines = []
        for feature_group in GROUP_ORDER:
            subgroup = group[group["feature_group"] == feature_group]
            if subgroup.empty:
                continue
            parts = []
            for code in subgroup["csv_code"]:
                sentence = sentence_for(code, row.get(code), codebook_by_code)
                if sentence:
                    parts.append(sentence)
                if len(parts) >= MAX_FEATURES_PER_YEAR:
                    break
            if parts:
                group_lines.append(f"{feature_group}: " + "; ".join(parts))
        if group_lines:
            lines.append(f"In {int(year)}: " + " | ".join(group_lines) + ".")
    return "\n".join(lines)


def make_sample(targets: pd.DataFrame, books: dict) -> pd.DataFrame:
    if SAMPLE_IDS_CSV.exists():
        return pd.read_csv(SAMPLE_IDS_CSV)
    eligible = targets[targets[TARGET].notna() & targets["C0000100"].astype(int).astype(str).isin(books)].copy()
    pos = eligible[eligible[TARGET] == 1].sample(n=SAMPLE_N // 2, random_state=3026)
    neg = eligible[eligible[TARGET] == 0].sample(n=SAMPLE_N - len(pos), random_state=3027)
    sample = pd.concat([pos, neg], ignore_index=True).sample(frac=1, random_state=3028)
    sample.to_csv(SAMPLE_IDS_CSV, index=False)
    return sample


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATA_PATH)
    codebook = pd.read_csv(CODEBOOK_PATH, dtype=str).fillna("")
    targets = pd.read_csv(BROAD_TARGETS_PATH)
    features = build_feature_index(codebook, set(data.columns))
    codebook_by_code = codebook.set_index("csv_code").to_dict(orient="index")

    # For this target, the second positive year is the event cutoff for positives.
    targets = targets.copy()
    targets["cutoff_year"] = np.where(
        targets[TARGET] == 1,
        targets["later_delinquency_contact_second_event_year"],
        targets["later_delinquency_contact_last_observed_year"],
    )
    eligible = targets[targets[TARGET].notna() & targets["cutoff_year"].notna()].copy()

    data_by_id = data.set_index("C0000100", drop=False)
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    books = {}
    for _, target_row in eligible.iterrows():
        child_id = int(target_row["C0000100"])
        cutoff = safe_int(target_row["cutoff_year"])
        if cutoff is None:
            continue
        row = data_by_id.loc[child_id]
        books[str(child_id)] = {
            "text": book_for_child(row, features, codebook_by_code, cutoff),
            "generated_at": now,
            "source": "nlsy79_child_youngadult_selected_crime_features",
            "target": TARGET,
            "cutoff_year": cutoff,
        }

    sample = make_sample(eligible, books)
    sample_ids = [str(int(x)) for x in sample["C0000100"]]
    sample_books = {cid: books[cid] for cid in sample_ids if cid in books}

    eligible.to_csv(TARGETS_CSV, index=False)
    features.to_csv(FEATURE_INDEX_CSV, index=False)
    BOOKS_JSON.write_text(json.dumps(books, indent=2, sort_keys=True))
    SAMPLE_BOOKS_JSON.write_text(json.dumps(sample_books, indent=2, sort_keys=True))

    (OUT_DIR / "README.md").write_text(
        "\n".join(
            [
                "# Broad Persistent Delinquency/Contact Books",
                "",
                "Target: `later_persistent_delinquency_contact`.",
                "Positive cases have direct delinquency/contact indicators in at least two different years from 2000-2020.",
                "Books are cut off before the second positive event year for positives and before the last observed target year for negatives.",
                "",
            ]
        )
    )

    print(f"Eligible rows: {len(eligible)}")
    print(f"Base rate: {eligible[TARGET].mean():.3f}")
    print(f"Books written: {len(books)}")
    print(f"Sample books written: {len(sample_books)}")
    print(f"Average sample book length: {int(np.mean([len(v['text']) for v in sample_books.values()]))}")


if __name__ == "__main__":
    main()
