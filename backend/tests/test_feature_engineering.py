"""
Unit tests for feature_engineering pure math — no LLM, no DB, no network.

Run from backend/:
  python -m pytest tests/test_feature_engineering.py -v
or:
  python tests/test_feature_engineering.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

# Allow `python tests/test_feature_engineering.py` without installing package
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.services.feature_engineering import (  # noqa: E402
    RECENCY_DECAY,
    UNKNOWN_GAP,
    compute_features_for_observations,
    compute_last_asked_gap,
    compute_marks_trend,
    compute_recurrence_count,
    compute_recency_weight,
)


def test_recurrence_distinct_years():
    assert compute_recurrence_count([2020, 2020, 2021, 2022, 2022]) == 3
    assert compute_recurrence_count([]) == 0
    assert compute_recurrence_count([2019]) == 1


def test_recency_weight_prefers_recent():
    older = compute_recency_weight([2018, 2019], reference_year=2024)
    newer = compute_recency_weight([2022, 2023], reference_year=2024)
    assert newer > older


def test_recency_weight_formula():
    assert compute_recency_weight([2024], reference_year=2024) == 1.0
    expected = round(RECENCY_DECAY ** 1, 6)
    assert compute_recency_weight([2023], reference_year=2024) == expected
    expected2 = round(1.0 + RECENCY_DECAY, 6)
    assert compute_recency_weight([2023, 2024], reference_year=2024) == expected2


def test_marks_trend_increasing():
    slope = compute_marks_trend([(2020, 10), (2021, 20), (2022, 30)])
    assert slope > 0
    assert math.isclose(slope, 10.0, rel_tol=1e-6)


def test_marks_trend_decreasing():
    slope = compute_marks_trend([(2020, 30), (2021, 20), (2022, 10)])
    assert slope < 0
    assert math.isclose(slope, -10.0, rel_tol=1e-6)


def test_marks_trend_flat_or_single_year():
    assert compute_marks_trend([(2020, 15), (2021, 15), (2022, 15)]) == 0.0
    assert compute_marks_trend([(2020, 15)]) == 0.0
    assert compute_marks_trend([]) == 0.0


def test_last_asked_gap():
    assert compute_last_asked_gap([2020, 2022], reference_year=2024) == 2
    assert compute_last_asked_gap([2024], reference_year=2024) == 0
    assert compute_last_asked_gap([], reference_year=2024) == UNKNOWN_GAP


def test_aggregate_observations():
    # Unit A: 2020 totals 10 marks, 2022 totals 15 → slope +2.5, gap 2 from 2024
    # Unit B: 2023 only — recurrence 1, gap 1
    obs = [
        ("Unit A", 2020, 5),
        ("Unit A", 2022, 15),
        ("Unit B", 2023, 8),
        ("Unit A", 2020, 5),  # same year again — recurrence still 2
    ]
    vectors = compute_features_for_observations(obs, reference_year=2024)
    by_key = {v.key: v for v in vectors}
    assert set(by_key) == {"Unit A", "Unit B"}

    a = by_key["Unit A"]
    assert a.recurrence_count == 2
    assert a.last_asked_gap == 2
    assert a.marks_trend > 0
    assert math.isclose(a.marks_trend, 2.5, rel_tol=1e-6)
    assert a.recency_weight > 0

    b = by_key["Unit B"]
    assert b.recurrence_count == 1
    assert b.last_asked_gap == 1
    assert b.marks_trend == 0.0


def test_skips_empty_keys_and_bad_years():
    obs = [
        ("", 2020, 5),
        ("Unit X", 1800, 5),
        ("Unit X", 2021, 5),
    ]
    vectors = compute_features_for_observations(obs, reference_year=2024)
    assert len(vectors) == 1
    assert vectors[0].key == "Unit X"
    assert vectors[0].recurrence_count == 1


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
