"""
Shared feature engineering core (Phase 4).

Four signals, reused by government ML and university LLM pipelines:

1. recurrence_count — distinct years (or papers if year missing) a key appeared in
2. recency_weight   — exponential decay favoring recent years (see formula below)
3. marks_trend      — linear slope of total marks vs year (float)
4. last_asked_gap   — years since last appearance (relative to reference year)

Government mode: groups by questions.tagged_unit, persists to unit_features.
University mode: groups by questions.unit_name (extraction topic), on-request only
  (no persistence — lower paper counts; inject into LLM prompt without DB write).

IMPORTANT: papers.exam_year is often null on POST /upload. When year is missing we
fall back to the calendar year of paper.created_at / processed_at so signals remain
defined. Callers that need strict year fidelity should populate exam_year on upload.
"""
from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# Exponential decay base for recency_weight.
# weight contribution of an appearance in year y:
#   RECENCY_DECAY ** (reference_year - y)
# With 0.85, an appearance 5 years ago contributes ~0.44 of a current-year hit.
RECENCY_DECAY = 0.85

# If a key has never been seen with a usable year, gap is this sentinel.
UNKNOWN_GAP = 99


@dataclass(frozen=True)
class FeatureVector:
    key: str
    recurrence_count: int
    recency_weight: float
    marks_trend: float
    last_asked_gap: int

    def as_row(self) -> Dict[str, Any]:
        return {
            "unit_name": self.key,
            "recurrence_count": self.recurrence_count,
            "recency_weight": self.recency_weight,
            "marks_trend": self.marks_trend,
            "last_asked_gap": self.last_asked_gap,
        }


# ---------------------------------------------------------------------------
# Pure math (fully unit-testable, no I/O)
# ---------------------------------------------------------------------------


def _safe_year(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        y = int(value)
        if 1990 <= y <= 2100:
            return y
    except (TypeError, ValueError):
        pass
    if isinstance(value, str) and len(value) >= 4 and value[:4].isdigit():
        try:
            y = int(value[:4])
            if 1990 <= y <= 2100:
                return y
        except ValueError:
            pass
    return None


def compute_recurrence_count(years: Sequence[int]) -> int:
    """Number of distinct years the key appeared in."""
    return len({int(y) for y in years})


def compute_recency_weight(
    years: Sequence[int],
    *,
    reference_year: Optional[int] = None,
    decay: float = RECENCY_DECAY,
) -> float:
    """
    Exponential recency weight.

    Formula
    -------
    Let Y_ref = reference_year or max(years).
    For each distinct year y in `years` (one contribution per year, not per question):
        w_y = decay ** (Y_ref - y)
    recency_weight = sum(w_y)

    Rationale: exponential decay is smoother than linear for sparse exam years and
    still puts most mass on the last 3–5 sittings. Distinct years only — repeated
    questions in the same year do not inflate the weight.
    """
    if not years:
        return 0.0
    ys = sorted({int(y) for y in years})
    y_ref = int(reference_year) if reference_year is not None else ys[-1]
    total = 0.0
    for y in ys:
        total += float(decay) ** max(0, y_ref - y)
    return round(total, 6)


def compute_marks_trend(
    year_marks: Sequence[Tuple[int, float]],
) -> float:
    """
    Linear slope of total marks allocated vs year.

    Representation: float slope (marks per year).
      > 0  marks allocation increasing over years
      = 0  flat / fewer than 2 distinct years
      < 0  decreasing

    Method: ordinary least squares on (year, sum_marks_that_year).
    Slope = Cov(x,y) / Var(x). Not normalized to [-1,1] so magnitude remains
    interpretable (e.g. +2.5 ≈ +2.5 marks/year average growth).
    """
    if not year_marks:
        return 0.0
    by_year: Dict[int, float] = defaultdict(float)
    for y, m in year_marks:
        by_year[int(y)] += float(m or 0)
    if len(by_year) < 2:
        return 0.0
    xs = sorted(by_year.keys())
    ys = [by_year[x] for x in xs]
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    var_x = sum((x - mean_x) ** 2 for x in xs)
    if var_x <= 0:
        return 0.0
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return round(cov / var_x, 6)


def compute_last_asked_gap(
    years: Sequence[int],
    *,
    reference_year: Optional[int] = None,
) -> int:
    """
    Years since the key was last asked: Y_ref - max(years).
    Y_ref defaults to max(years) → gap 0 when data is current within the set.
    Prefer passing calendar/reference year from the caller for true "years since".
    """
    if not years:
        return UNKNOWN_GAP
    ys = [int(y) for y in years]
    last = max(ys)
    y_ref = int(reference_year) if reference_year is not None else last
    return max(0, y_ref - last)


def compute_features_for_observations(
    observations: Sequence[Tuple[str, int, float]],
    *,
    reference_year: Optional[int] = None,
) -> List[FeatureVector]:
    """
    Core aggregator.

    observations: iterable of (key, year, marks) — one row per question appearance.
    Returns one FeatureVector per distinct key, sorted by key.
    """
    by_key: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
    for key, year, marks in observations:
        k = (key or "").strip()
        if not k:
            continue
        y = _safe_year(year)
        if y is None:
            continue
        by_key[k].append((y, float(marks or 0)))

    # Global reference: max year across all data (or explicit)
    all_years = [y for pairs in by_key.values() for y, _ in pairs]
    y_ref = int(reference_year) if reference_year is not None else (max(all_years) if all_years else None)

    out: List[FeatureVector] = []
    for key in sorted(by_key.keys()):
        pairs = by_key[key]
        years = [y for y, _ in pairs]
        out.append(
            FeatureVector(
                key=key,
                recurrence_count=compute_recurrence_count(years),
                recency_weight=compute_recency_weight(years, reference_year=y_ref),
                marks_trend=compute_marks_trend(pairs),
                last_asked_gap=compute_last_asked_gap(years, reference_year=y_ref),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------


def _paper_year(paper: Dict[str, Any]) -> Optional[int]:
    y = _safe_year(paper.get("exam_year"))
    if y is not None:
        return y
    for field in ("processed_at", "created_at", "updated_at"):
        y = _safe_year(paper.get(field))
        if y is not None:
            return y
    return None


def _collect_observations(
    questions: Sequence[Dict[str, Any]],
    papers_by_id: Dict[str, Dict[str, Any]],
    *,
    key_field: str,
) -> List[Tuple[str, int, float]]:
    obs: List[Tuple[str, int, float]] = []
    for q in questions:
        key = str(q.get(key_field) or "").strip()
        if not key or key.lower() in ("unknown", "unmatched", "none"):
            continue
        paper = papers_by_id.get(str(q.get("paper_id") or "")) or {}
        year = _paper_year(paper)
        if year is None:
            continue
        marks = float(q.get("marks") or 0)
        obs.append((key, year, marks))
    return obs


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------


def compute_government_unit_features(
    subject_id: str,
    *,
    persist: bool = True,
    reference_year: Optional[int] = None,
) -> List[FeatureVector]:
    """
    Government mode: group by questions.tagged_unit + paper exam_year/marks.
    When persist=True, write/replace rows in unit_features for the subject.
    """
    from app.repositories import papers as papers_repo
    from app.repositories import questions as questions_repo
    from app.repositories import unit_features as unit_features_repo

    papers = papers_repo.list_for_subject(subject_id)
    papers_by_id = {str(p["id"]): p for p in papers if p.get("id")}
    questions = questions_repo.list_for_subject(subject_id)
    obs = _collect_observations(questions, papers_by_id, key_field="tagged_unit")
    vectors = compute_features_for_observations(obs, reference_year=reference_year)

    if persist and vectors:
        now = datetime.now(timezone.utc).isoformat()
        rows = []
        for v in vectors:
            row = v.as_row()
            row["computed_at"] = now
            rows.append(row)
        try:
            unit_features_repo.replace_for_subject(subject_id, rows)
        except Exception as e:
            logger.warning("unit_features persist failed (upsert fallback): %s", e)
            for row in rows:
                try:
                    unit_features_repo.upsert_for_subject_unit(
                        subject_id, row["unit_name"], row
                    )
                except Exception as e2:
                    logger.warning("unit_features upsert failed for %s: %s", row.get("unit_name"), e2)

    return vectors


def compute_university_topic_features(
    subject_id: str,
    *,
    reference_year: Optional[int] = None,
) -> List[FeatureVector]:
    """
    University mode: group by questions.unit_name (parser/LLM extraction topic).

    Persistence: **none** (on-request only).
    Why: university subjects usually have fewer papers; features are injected into
    the LLM prompt at generation time. Avoids another write path and stale rows
    when extraction labels are noisy. Government track needs durable unit_features
    for ML training/scoring; university does not.
    """
    from app.repositories import papers as papers_repo
    from app.repositories import questions as questions_repo

    papers = papers_repo.list_for_subject(subject_id)
    papers_by_id = {str(p["id"]): p for p in papers if p.get("id")}
    questions = questions_repo.list_for_subject(subject_id)
    obs = _collect_observations(questions, papers_by_id, key_field="unit_name")
    return compute_features_for_observations(obs, reference_year=reference_year)


def features_to_prompt_block(vectors: Sequence[FeatureVector], *,
                             limit: int = 20) -> str:
    """Compact text block for university LLM prompt injection (later phase)."""
    if not vectors:
        return "(no topic feature signals)"
    ranked = sorted(
        vectors,
        key=lambda v: (v.recency_weight * max(1, v.recurrence_count), -v.last_asked_gap),
        reverse=True,
    )[:limit]
    lines = [
        "topic | recurrence | recency_w | marks_slope | years_since",
    ]
    for v in ranked:
        lines.append(
            f"{v.key} | {v.recurrence_count} | {v.recency_weight:.3f} | "
            f"{v.marks_trend:.3f} | {v.last_asked_gap}"
        )
    return "\n".join(lines)
