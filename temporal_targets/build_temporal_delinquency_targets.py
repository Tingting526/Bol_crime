"""
Build temporally defined delinquency/contact targets for the NLSY79
Child/Young Adult crime feature file.

The older `build_delinquency_targets_v3.py` aggregates "ever across waves".
That is useful descriptively, but it is ambiguous for prediction because the
outcome window is not separated from the predictor window.

This script defines later targets only from 2000-2020. For a strict baseline
prediction design, predictors should therefore be restricted to information
observed before 2000, for example up to 1998.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

DATA_PATH = PROJECT_DIR / "nlsy79_child_youngadult_selected_crime_features.csv"
OUT_DIR = SCRIPT_DIR
TARGETS_CSV = OUT_DIR / "nlsy79_temporal_delinquency_targets_2000_2020.csv"
ITEMS_CSV = OUT_DIR / "temporal_delinquency_target_items_2000_2020.csv"
BASE_RATES_CSV = OUT_DIR / "temporal_delinquency_target_base_rates_2000_2020.csv"

MISSING_CODES = {-1, -2, -3, -4, -5, -7}


# Broad direct delinquency/contact items used as the main outcome family.
# The outcome window is 2000-2020. Pre-2000 items are intentionally excluded.
ITEMS = [
    # 2000
    ("C2466100", 2000, "violence", "hurt someone badly enough to need a doctor"),
    ("C2466400", 2000, "property", "damaged school property on purpose"),
    ("Y1176200", 2000, "violence", "physical fight at school or work"),
    ("Y1176900", 2000, "justice", "sentenced to corrections/jail/reform"),
    ("Y1177000", 2000, "justice", "on probation"),
    # 2002
    ("C2765800", 2002, "violence", "hurt someone badly enough to need a doctor"),
    ("C2766100", 2002, "property", "damaged school property on purpose"),
    ("Y1415900", 2002, "violence", "hurt someone badly enough to need a doctor"),
    ("Y1416200", 2002, "property", "damaged school property on purpose"),
    ("Y1416800", 2002, "violence", "physical fight at school or work"),
    ("Y1417500", 2002, "justice", "sentenced to corrections/jail/reform"),
    ("Y1417600", 2002, "justice", "on probation"),
    # 2004
    ("C3045500", 2004, "violence", "hurt someone badly enough to need a doctor"),
    ("C3045800", 2004, "property", "damaged school property on purpose"),
    ("Y1667300", 2004, "violence", "hurt someone badly enough to need a doctor"),
    ("Y1667600", 2004, "property", "damaged school property on purpose"),
    ("Y1668200", 2004, "violence", "physical fight at school or work"),
    ("Y1668900", 2004, "justice", "sentenced to corrections/jail/reform"),
    ("Y1669000", 2004, "justice", "on probation"),
    # 2006
    ("C3366300", 2006, "violence", "hurt someone badly enough to need a doctor"),
    ("C3366600", 2006, "property", "damaged school property on purpose"),
    ("Y1940600", 2006, "violence", "hurt someone badly enough to need a doctor"),
    ("Y1940900", 2006, "property", "damaged school property on purpose"),
    ("Y1941500", 2006, "violence", "physical fight at school or work"),
    ("Y1942200", 2006, "justice", "sentenced to corrections/jail/reform"),
    ("Y1942300", 2006, "justice", "on probation"),
    # 2008
    ("C3870000", 2008, "violence", "hurt someone badly enough to need a doctor"),
    ("C3870300", 2008, "property", "damaged school property on purpose"),
    ("Y2256600", 2008, "violence", "hurt someone badly enough to need a doctor"),
    ("Y2256900", 2008, "property", "damaged school property on purpose"),
    ("Y2257500", 2008, "violence", "physical fight at school or work"),
    ("Y2258200", 2008, "justice", "sentenced to corrections/jail/reform"),
    ("Y2258300", 2008, "justice", "on probation"),
    # 2010
    ("C5118200", 2010, "violence", "hurt someone badly enough to need a doctor"),
    ("C5118500", 2010, "property", "damaged school property on purpose"),
    ("Y2608200", 2010, "violence", "hurt someone badly enough to need a doctor"),
    ("Y2608500", 2010, "property", "damaged school property on purpose"),
    ("Y2609100", 2010, "violence", "physical fight at school or work"),
    ("Y2609800", 2010, "justice", "sentenced to corrections/jail/reform"),
    ("Y2609900", 2010, "justice", "on probation"),
    # 2012
    ("C5695700", 2012, "violence", "hurt someone badly enough to need a doctor"),
    ("C5696000", 2012, "property", "damaged school property on purpose"),
    ("Y2958300", 2012, "violence", "hurt someone badly enough to need a doctor"),
    ("Y2958600", 2012, "property", "damaged school property on purpose"),
    ("Y2959200", 2012, "violence", "physical fight at school or work"),
    ("Y2959900", 2012, "justice", "sentenced to corrections/jail/reform"),
    ("Y2960000", 2012, "justice", "on probation"),
    # 2014
    ("C5967600", 2014, "violence", "hurt someone badly enough to need a doctor"),
    ("C5967900", 2014, "property", "damaged school property on purpose"),
    ("Y3325701", 2014, "violence", "hurt someone badly enough to need a doctor"),
    ("Y3325704", 2014, "property", "damaged school property on purpose"),
    ("Y3325801", 2014, "violence", "physical fight at school or work"),
    ("Y3326300", 2014, "justice", "sentenced to corrections/jail/reform"),
    ("Y3326400", 2014, "justice", "on probation"),
    # 2016
    ("Y3670801", 2016, "violence", "hurt someone badly enough to need a doctor"),
    ("Y3670804", 2016, "property", "damaged school property on purpose"),
    ("Y3670901", 2016, "violence", "physical fight at school or work"),
    ("Y3671500", 2016, "justice", "sentenced to corrections/jail/reform"),
    ("Y3671600", 2016, "justice", "on probation"),
    # 2018
    ("Y4275601", 2018, "violence", "hurt someone badly enough to need a doctor"),
    ("Y4275604", 2018, "property", "damaged school property on purpose"),
    ("Y4275701", 2018, "violence", "physical fight at school or work"),
    ("Y4276300", 2018, "justice", "sentenced to corrections/jail/reform"),
    ("Y4276400", 2018, "justice", "on probation"),
    # 2020
    ("Y4596801", 2020, "violence", "hurt someone badly enough to need a doctor"),
    ("Y4596804", 2020, "property", "damaged school property on purpose"),
    ("Y4596901", 2020, "violence", "physical fight at school or work"),
    ("Y4597500", 2020, "justice", "sentenced to corrections/jail/reform"),
    ("Y4597600", 2020, "justice", "on probation"),
]


def clean_value(value) -> float | None:
    if pd.isna(value):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    if int(value) in MISSING_CODES:
        return None
    return value


def summarize_years(row: pd.Series, item_table: pd.DataFrame, kind: str | None = None) -> dict:
    if kind is not None:
        item_table = item_table[item_table["item_type"] == kind]

    observed_years: list[int] = []
    positive_years: list[int] = []
    positive_item_count = 0

    for year, year_items in item_table.groupby("year"):
        values = [clean_value(row.get(code)) for code in year_items["csv_code"]]
        observed = [v for v in values if v is not None]
        if observed:
            observed_years.append(int(year))
        positives = [v for v in observed if v > 0]
        if positives:
            positive_years.append(int(year))
            positive_item_count += len(positives)

    positive_years_unique = sorted(set(positive_years))
    observed_years_unique = sorted(set(observed_years))
    return {
        "ever": int(bool(positive_years_unique)) if observed_years_unique else np.nan,
        "persistent": int(len(positive_years_unique) >= 2) if observed_years_unique else np.nan,
        "positive_item_count": positive_item_count if observed_years_unique else np.nan,
        "positive_year_count": len(positive_years_unique) if observed_years_unique else np.nan,
        "first_event_year": positive_years_unique[0] if positive_years_unique else np.nan,
        "second_event_year": positive_years_unique[1] if len(positive_years_unique) >= 2 else np.nan,
        "last_observed_year": observed_years_unique[-1] if observed_years_unique else np.nan,
    }


def base_rate_table(targets: pd.DataFrame, target_cols: list[str]) -> pd.DataFrame:
    rows = []
    total_n = len(targets)
    for col in target_cols:
        valid = targets[col].dropna()
        rows.append(
            {
                "target": col,
                "total_n": total_n,
                "eligible_n": len(valid),
                "missing_n": total_n - len(valid),
                "positive_n": int((valid == 1).sum()),
                "negative_n": int((valid == 0).sum()),
                "base_rate": float(valid.mean()) if len(valid) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def build_targets(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    item_table = pd.DataFrame(ITEMS, columns=["csv_code", "year", "item_type", "description"])
    item_table["available_in_feature_file"] = item_table["csv_code"].isin(df.columns)
    available_items = item_table[item_table["available_in_feature_file"]].copy()

    rows = []
    for _, row in df.iterrows():
        broad = summarize_years(row, available_items)
        justice = summarize_years(row, available_items, kind="justice")
        rows.append(
            {
                "C0000100": row["C0000100"],
                "C0000200": row.get("C0000200", np.nan),
                "later_any_delinquency_contact_2000_2020": broad["ever"],
                "later_persistent_delinquency_contact_2000_2020": broad["persistent"],
                "later_delinquency_contact_positive_item_count_2000_2020": broad["positive_item_count"],
                "later_delinquency_contact_positive_year_count_2000_2020": broad["positive_year_count"],
                "later_delinquency_contact_first_event_year_2000_2020": broad["first_event_year"],
                "later_delinquency_contact_second_event_year_2000_2020": broad["second_event_year"],
                "later_delinquency_contact_last_observed_year_2000_2020": broad["last_observed_year"],
                "later_any_justice_contact_2000_2020": justice["ever"],
                "later_persistent_justice_contact_2000_2020": justice["persistent"],
                "later_justice_contact_positive_item_count_2000_2020": justice["positive_item_count"],
                "later_justice_contact_positive_year_count_2000_2020": justice["positive_year_count"],
                "later_justice_contact_first_event_year_2000_2020": justice["first_event_year"],
                "later_justice_contact_second_event_year_2000_2020": justice["second_event_year"],
                "later_justice_contact_last_observed_year_2000_2020": justice["last_observed_year"],
            }
        )

    targets = pd.DataFrame(rows)
    target_cols = [
        "later_any_delinquency_contact_2000_2020",
        "later_persistent_delinquency_contact_2000_2020",
        "later_any_justice_contact_2000_2020",
        "later_persistent_justice_contact_2000_2020",
    ]
    rates = base_rate_table(targets, target_cols)
    return targets, item_table, rates


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(DATA_PATH)
    targets, item_table, rates = build_targets(df)
    targets.to_csv(TARGETS_CSV, index=False)
    item_table.to_csv(ITEMS_CSV, index=False)
    rates.to_csv(BASE_RATES_CSV, index=False)

    print(f"Wrote targets: {TARGETS_CSV}")
    print(f"Wrote target items: {ITEMS_CSV}")
    print(f"Wrote base rates: {BASE_RATES_CSV}")
    print()
    print(rates.to_string(index=False))


if __name__ == "__main__":
    main()
