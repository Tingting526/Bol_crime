"""LLM prediction test for broad persistent delinquency/contact BoLs."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parent
OUT_DIR = REPO / "data/processed_child_crime_broad_persistent"
BOOKS_JSON = OUT_DIR / "books_child_crime_broad_persistent_sample_120.json"
TARGETS_CSV = OUT_DIR / "child_crime_broad_persistent_targets.csv"
PREDICTIONS_CSV = OUT_DIR / "child_crime_broad_persistent_llm_predictions_120.csv"
TARGET = "later_persistent_delinquency_contact"
DEFAULT_MODEL = "gpt-5.4-nano"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def parse_jsonish(text: str) -> dict:
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def make_prompt(book_text: str) -> str:
    return f"""Read the Book of Life below and predict whether this person will show persistent later delinquency/contact.

The target equals 1 if the person has direct delinquency/contact indicators in at least two different later survey years from 2000-2020. The indicators include physical fighting, hurting someone badly, damaging property, probation, or being sentenced to corrections/jail/reform. The Book of Life has already been cut off before the target point.

Calibrate your probability. Examples:
- A person with repeated early externalizing behavior, prior substance use, prior fights/property damage, and weak school/family attachment should usually receive a higher probability, often above 0.50.
- A person with mostly stable school/family information, few behavioral risk indicators, and no prior delinquency/contact should usually receive a lower probability, often below 0.35.
- If the text is sparse or mixed, use an intermediate probability rather than defaulting to zero.

Return only valid JSON with exactly these keys:
{{"prediction": 0 or 1, "probability": number between 0 and 1, "reason": "one short sentence"}}

Make `prediction` consistent with `probability`: prediction must be 1 if probability >= 0.50 and 0 otherwise.
Use `probability` as your estimated probability that the target equals 1.

Book of Life:
{book_text}
"""


def predict_one(client, model: str, book_text: str) -> dict:
    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "You are a careful research assistant making binary risk predictions from "
                    "structured life-history text. Return compact JSON only."
                ),
            },
            {"role": "user", "content": make_prompt(book_text)},
        ],
        max_output_tokens=180,
    )
    parsed = parse_jsonish(response.output_text)
    return {
        "prediction": int(parsed["prediction"]),
        "probability": float(parsed["probability"]),
        "reason": str(parsed.get("reason", "")),
        "raw_response": response.output_text,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    load_env(REPO / ".env")
    model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
    books = json.loads(BOOKS_JSON.read_text())
    targets = pd.read_csv(TARGETS_CSV)
    truth = targets[["C0000100", TARGET, "cutoff_year"]].copy()
    truth["C0000100"] = truth["C0000100"].astype(int)

    existing = pd.DataFrame()
    if PREDICTIONS_CSV.exists() and not args.overwrite:
        existing = pd.read_csv(PREDICTIONS_CSV)
        done = set(existing["C0000100"].astype(int).astype(str))
        books = {cid: payload for cid, payload in books.items() if cid not in done}

    print(f"Books to predict: {len(books)}")
    print(f"Model: {model}")

    if args.dry_run:
        first_id, first_book = next(iter(books.items()))
        print(make_prompt(first_book["text"])[:1800])
        return

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is missing. Add it to .env.")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    rows = []
    for child_id, payload in books.items():
        pred = predict_one(client, model, payload["text"])
        rows.append({"C0000100": int(child_id), "model": model, "target": TARGET, **pred})
        print(f"Predicted {child_id}: {pred['prediction']} p={pred['probability']:.3f}")

    new_preds = pd.DataFrame(rows)
    if len(new_preds):
        new_preds = new_preds.merge(truth, on="C0000100", how="left")
        new_preds.rename(columns={TARGET: "y_true"}, inplace=True)
        new_preds["correct"] = new_preds["prediction"] == new_preds["y_true"]
    preds = pd.concat([existing, new_preds], ignore_index=True) if len(existing) else new_preds
    preds = preds.drop_duplicates(["C0000100", "target"], keep="last")
    preds.to_csv(PREDICTIONS_CSV, index=False)
    print(f"\nWrote {len(preds)} predictions to {PREDICTIONS_CSV.relative_to(REPO)}")
    if "correct" in preds:
        print(f"Accuracy using prediction column: {preds['correct'].mean():.3f}")


if __name__ == "__main__":
    main()
