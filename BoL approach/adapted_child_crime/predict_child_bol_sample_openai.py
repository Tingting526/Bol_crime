"""Predict child crime targets from the generated Book-of-Life sample.

This script requires your own OpenAI API key in `.env`:

    OPENAI_API_KEY=sk-...
    OPENAI_MODEL=gpt-5.4-nano

It reads `data/processed_child_crime/books_child_crime_sample.json` and writes
LLM predictions to `data/processed_child_crime/child_crime_llm_predictions.csv`.
Use `--dry-run` to validate paths and prompts without calling the API.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parent
OUT_DIR = REPO / "data/processed_child_crime"
BOOKS_JSON = OUT_DIR / "books_child_crime_sample.json"
TARGETS_CSV = OUT_DIR / "child_crime_targets_sample.csv"
PREDICTIONS_CSV = OUT_DIR / "child_crime_llm_predictions.csv"

DEFAULT_TARGET = "justice_contact_repeated"
DEFAULT_MODEL = "gpt-5.4-nano"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_jsonish(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def make_prompt(book_text: str, target: str) -> str:
    target_description = {
        "justice_contact_repeated": (
            "whether the person will have repeated justice-system contact, defined as at least "
            "two positive reports across conviction, adult-court conviction, probation, or "
            "corrections/jail/reform items"
        ),
        "justice_contact_ever": (
            "whether the person will have any justice-system contact, defined as any positive "
            "report across conviction, adult-court conviction, probation, or corrections/jail/reform items"
        ),
        "target_violent_ever": "whether the person will ever report a violent delinquency item",
        "target_property_ever": "whether the person will ever report a property delinquency item",
    }.get(target, f"the binary target `{target}`")

    return f"""Read the Book of Life below and predict {target_description}.

Return only valid JSON with exactly these keys:
{{"prediction": 0 or 1, "probability": number between 0 and 1, "reason": "one short sentence"}}

Do not mention protected attributes as reasons unless they are necessary to describe information explicitly in the text.

Book of Life:
{book_text}
"""


def predict_one(client, model: str, book_text: str, target: str) -> dict:
    prompt = make_prompt(book_text, target)
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
            {"role": "user", "content": prompt},
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
    parser.add_argument("--target", default=DEFAULT_TARGET)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--overwrite", action="store_true", help="Re-predict cases already present in the output CSV.")
    args = parser.parse_args()

    load_env(REPO / ".env")
    model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)

    books = json.loads(BOOKS_JSON.read_text())
    targets = pd.read_csv(TARGETS_CSV)
    if args.limit is not None:
        books = dict(list(books.items())[: args.limit])

    existing = pd.DataFrame()
    if PREDICTIONS_CSV.exists() and not args.overwrite:
        existing = pd.read_csv(PREDICTIONS_CSV)
        done_ids = set(existing.loc[existing["target"] == args.target, "C0000100"].astype(str))
        books = {cid: payload for cid, payload in books.items() if cid not in done_ids}

    print(f"Books to predict: {len(books)}")
    print(f"Target: {args.target}")
    print(f"Model: {model}")

    if args.dry_run:
        first_id, first_book = next(iter(books.items()))
        print("\n=== Dry-run prompt excerpt ===")
        print(make_prompt(first_book["text"], args.target)[:1800])
        print(f"\nWould write predictions to {PREDICTIONS_CSV.relative_to(REPO)}")
        return

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise SystemExit(
            "OPENAI_API_KEY is missing. Create a local .env from .env.example and add your key."
        )

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    rows = []
    for child_id, payload in books.items():
        pred = predict_one(client, model, payload["text"], args.target)
        rows.append({"C0000100": int(child_id), "model": model, "target": args.target, **pred})
        print(f"Predicted {child_id}: {pred['prediction']} p={pred['probability']:.3f}")

    preds = pd.DataFrame(rows)
    if len(preds):
        preds = preds.merge(targets[["C0000100", args.target]], on="C0000100", how="left")
        preds.rename(columns={args.target: "y_true"}, inplace=True)
        preds["correct"] = preds["prediction"] == preds["y_true"]

    if len(existing) and not args.overwrite:
        preds = pd.concat([existing, preds], ignore_index=True)
        preds = preds.drop_duplicates(["C0000100", "target"], keep="last")
    preds.to_csv(PREDICTIONS_CSV, index=False)

    print(f"\nWrote {len(preds)} predictions to {PREDICTIONS_CSV.relative_to(REPO)}")
    if preds["y_true"].notna().any():
        print(f"Accuracy on labeled rows: {preds.loc[preds['y_true'].notna(), 'correct'].mean():.3f}")


if __name__ == "__main__":
    main()
