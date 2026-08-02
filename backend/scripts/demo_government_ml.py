#!/usr/bin/env python3
"""
Demo / sanity-check for government_ml on synthetic multi-year NEET-style data.

Does not touch the DB. Builds (unit, year, marks) observations that mimic a
user's tagged Biology PYQ history, then runs causal training + inference and
prints the raw unit_features table next to model predictions.

Run from backend/:
  python scripts/demo_government_ml.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.services.government_ml import (  # noqa: E402
    MIN_HISTORY_YEARS,
    demo_train_and_predict,
)


def build_neet_biology_obs():
    """
    Synthetic 6-year NEET Biology unit marks (realistic recurrence patterns).

    High-recurrence / rising: Human Physiology, Genetics, Ecology
    Medium / flat: Plant Physiology, Cell Biology
    Sparse / declining: Biomolecules, Reproduction (plants)
    Recent debut: Biotechnology
    """
    # (unit, year, marks) — multiple questions per year summed via assembly
    data = []

    def add(unit, year, marks_list):
        for m in marks_list:
            data.append((unit, year, float(m)))

    # 2019
    add("Human Physiology", 2019, [4, 4, 3])
    add("Genetics and Evolution", 2019, [4, 3])
    add("Ecology and Environment", 2019, [3, 3])
    add("Cell Structure and Function", 2019, [4])
    add("Plant Physiology", 2019, [3, 2])
    add("Biomolecules", 2019, [4, 3])
    add("Reproduction", 2019, [3])

    # 2020
    add("Human Physiology", 2020, [4, 4, 4])
    add("Genetics and Evolution", 2020, [4, 4])
    add("Ecology and Environment", 2020, [4, 3])
    add("Cell Structure and Function", 2020, [3, 3])
    add("Plant Physiology", 2020, [3])
    add("Biomolecules", 2020, [3])
    add("Reproduction", 2020, [4, 3])

    # 2021
    add("Human Physiology", 2021, [4, 4, 4, 3])
    add("Genetics and Evolution", 2021, [4, 4, 3])
    add("Ecology and Environment", 2021, [4, 4])
    add("Cell Structure and Function", 2021, [4])
    add("Plant Physiology", 2021, [3, 3])
    add("Biotechnology", 2021, [4])  # debut
    # Biomolecules skipped this year
    add("Reproduction", 2021, [3])

    # 2022
    add("Human Physiology", 2022, [4, 4, 4, 4])
    add("Genetics and Evolution", 2022, [4, 4, 4])
    add("Ecology and Environment", 2022, [4, 3, 3])
    add("Cell Structure and Function", 2022, [3, 3])
    add("Plant Physiology", 2022, [4])
    add("Biotechnology", 2022, [4, 3])
    add("Biomolecules", 2022, [2])
    # Reproduction skipped

    # 2023
    add("Human Physiology", 2023, [4, 4, 4, 4, 3])
    add("Genetics and Evolution", 2023, [4, 4, 4])
    add("Ecology and Environment", 2023, [4, 4])
    add("Cell Structure and Function", 2023, [4, 3])
    add("Plant Physiology", 2023, [3, 3])
    add("Biotechnology", 2023, [4, 4])
    add("Biomolecules", 2023, [2])
    add("Reproduction", 2023, [3])

    # 2024
    add("Human Physiology", 2024, [4, 4, 4, 4, 4])
    add("Genetics and Evolution", 2024, [4, 4, 4, 3])
    add("Ecology and Environment", 2024, [4, 4, 3])
    add("Cell Structure and Function", 2024, [4])
    add("Plant Physiology", 2024, [3])
    add("Biotechnology", 2024, [4, 4, 3])
    # Biomolecules absent
    # Reproduction absent

    return data


def main():
    obs = build_neet_biology_obs()
    years = sorted({y for _, y, _ in obs})
    print("=" * 72)
    print("PrepIQ government_ml demo — NEET Biology (synthetic, per-user)")
    print(f"MIN_HISTORY_YEARS = {MIN_HISTORY_YEARS}")
    print(f"Distinct years in history: {years} (n={len(years)})")
    print("=" * 72)

    result = demo_train_and_predict(obs)

    print(f"\nMode: {result['mode']} | model_version: {result['model_version']}")
    if result.get("warning"):
        print(f"Warning: {result['warning']}")
    if result.get("n_train_rows") is not None:
        print(
            f"Training rows: {result['n_train_rows']} | "
            f"next_exam_year: {result.get('next_exam_year')}"
        )

    print("\n--- Raw unit_features table (as of max year in history) ---")
    print(
        f"{'unit':<32} {'rec':>4} {'recency_w':>10} {'marks_trend':>12} {'gap':>5}"
    )
    print("-" * 72)
    for row in result["feature_table"]:
        print(
            f"{row['unit_name']:<32} {row['recurrence_count']:>4} "
            f"{row['recency_weight']:>10.4f} {row['marks_trend']:>12.4f} "
            f"{row['last_asked_gap']:>5}"
        )

    if result.get("training_sample_rows"):
        print("\n--- Sample causal training rows (features known BEFORE label year) ---")
        for r in result["training_sample_rows"][:8]:
            f = r["features"]
            print(
                f"  {r['unit']:<28} X=[{f['recurrence_count']:.0f}, "
                f"{f['recency_weight']:.3f}, {f['marks_trend']:.2f}, "
                f"{f['last_asked_gap']:.0f}]  "
                f"appear={r['label_appear']} marks={r['label_marks']:.0f}"
            )

    print("\n--- Predictions (ranked) ---")
    print(
        f"{'#':>2} {'unit':<32} {'P(appear)':>9} {'marks≈':>7} {'prob':<12} conf"
    )
    print("-" * 72)
    for p in result["predictions"]:
        print(
            f"{p['question_number']:>2} {p['unit']:<32} "
            f"{p.get('p_appear', p['confidence_score']):>9.3f} "
            f"{p.get('predicted_marks', p['marks']):>7.1f} "
            f"{p['probability']:<12} {p['confidence_score']:.3f}"
        )
        print(f"   reasoning: {p['reasoning'][:140]}...")

    print("\n--- Sanity check notes ---")
    print(
        "Expect Human Physiology / Genetics / Ecology / Biotechnology near the top:\n"
        "  - high recurrence, high recency_weight, non-negative marks_trend.\n"
        "Biomolecules / Reproduction should rank lower (gap + declining volume).\n"
        "Compare ranks to the raw feature table above — model should not invert\n"
        "obvious signal order unless the causal labels justify it."
    )
    print("\nFull JSON dump of top prediction:")
    if result["predictions"]:
        print(json.dumps(result["predictions"][0], indent=2))


if __name__ == "__main__":
    main()
