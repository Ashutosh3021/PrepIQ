"""
Government-track ML prediction layer (NEET / JEE).

Per-user, per-subject training only — no cross-user pooling.
Each subject's multi-year tagged PYQ history is sufficient for simple linear models.

Minimum data threshold
----------------------
MIN_HISTORY_YEARS = 4

Reasoning (not implicit):
- marks_trend is an OLS slope and is undefined / zero with fewer than 2 distinct
  years of observations for a unit.
- Supervised samples are constructed causally: for each target year T we build
  features from years < T only. With H distinct exam years we obtain at most
  H-1 labeled rows per unit.
- NEET/JEE syllabus units typically number 15–30 per subject. With H=4 we get
  ~3 samples/unit × ~20 units ≈ 60 rows for a 4-feature logistic / linear model —
  enough for a stable fit without heavy regularization. H=3 yields only ~2
  samples/unit (borderline and trend slope often noisy). H≥5 is ideal but many
  users will not yet have that depth; 4 is the defensible floor before we attempt
  training rather than signal ranking.

Cold-start: if distinct years with tagged observations < MIN_HISTORY_YEARS, we do
NOT train. We rank the current unit_features table with the same heuristic used by
the university stats fallback and mark the response clearly as signal-based
(source_type still government_ml path, but model_version carries a "signal-only"
tag and reasoning states that no trained model was used).

Leakage control
---------------
Feature vectors for a historical year T use ONLY observations with year < T.
reference_year for gap/recency is set to T-1 so "last_asked_gap" and recency
weights reflect knowledge available before exam T. Marks and appearance labels
come from year T alone.
"""
from __future__ import annotations

import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler

from app.services.feature_engineering import (
    FeatureVector,
    compute_features_for_observations,
    compute_last_asked_gap,
    compute_marks_trend,
    compute_recurrence_count,
    compute_recency_weight,
    RECENCY_DECAY,
    UNKNOWN_GAP,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Documented threshold (see module docstring)
# ---------------------------------------------------------------------------
MIN_HISTORY_YEARS = int(os.getenv("GOV_ML_MIN_HISTORY_YEARS", "4") or "4")

SOURCE_TYPE_GOVERNMENT = "government_ml"
MODEL_VERSION = "gov-ml-lr-v1"  # logistic + linear, causal features, 4-signal set
SIGNAL_ONLY_VERSION = "gov-signal-only-v1"

FEATURE_NAMES = (
    "recurrence_count",
    "recency_weight",
    "marks_trend",
    "last_asked_gap",
)

MAX_ITEMS = int(os.getenv("PREDICTION_MAX_ITEMS", "10") or "10")


@dataclass
class YearUnitOutcome:
    unit: str
    year: int
    appeared: int  # 0/1
    marks: float


@dataclass
class TrainedModels:
    appearance_model: LogisticRegression
    marks_model: LinearRegression
    scaler: StandardScaler
    feature_names: Tuple[str, ...]
    n_train_rows: int
    n_units: int
    years_used: List[int]
    model_version: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def _paper_year(paper: Dict[str, Any]) -> Optional[int]:
    y = _safe_year(paper.get("exam_year"))
    if y is not None:
        return y
    for field in ("processed_at", "created_at", "updated_at"):
        y = _safe_year(paper.get(field))
        if y is not None:
            return y
    return None


def collect_tagged_observations(
    subject_id: str,
) -> Tuple[List[Tuple[str, int, float]], List[int]]:
    """
    Load (unit, year, marks) from tagged government questions.
    Returns observations and sorted list of distinct years present.
    """
    from app.repositories import papers as papers_repo
    from app.repositories import questions as questions_repo

    papers = papers_repo.list_for_subject(subject_id)
    papers_by_id = {str(p["id"]): p for p in papers if p.get("id")}
    questions = questions_repo.list_for_subject(subject_id)

    obs: List[Tuple[str, int, float]] = []
    years_set: set = set()
    for q in questions:
        unit = str(q.get("tagged_unit") or "").strip()
        if not unit or unit.lower() in ("unknown", "unmatched", "none"):
            continue
        paper = papers_by_id.get(str(q.get("paper_id") or "")) or {}
        year = _paper_year(paper)
        if year is None:
            continue
        marks = float(q.get("marks") or 0)
        obs.append((unit, year, marks))
        years_set.add(year)
    return obs, sorted(years_set)


def _features_from_obs_before(
    obs: Sequence[Tuple[str, int, float]],
    unit: str,
    *,
    cutoff_year: int,
) -> Tuple[float, float, float, float]:
    """
    Causal feature vector for `unit` using only observations with year < cutoff_year.
    reference_year for gap/recency = cutoff_year - 1 (knowledge before exam cutoff_year).
    """
    prior = [(u, y, m) for u, y, m in obs if u == unit and y < cutoff_year]
    y_ref = cutoff_year - 1
    if not prior:
        return (0.0, 0.0, 0.0, float(UNKNOWN_GAP))

    years = [y for _, y, _ in prior]
    pairs = [(y, m) for _, y, m in prior]
    return (
        float(compute_recurrence_count(years)),
        float(compute_recency_weight(years, reference_year=y_ref, decay=RECENCY_DECAY)),
        float(compute_marks_trend(pairs)),
        float(compute_last_asked_gap(years, reference_year=y_ref)),
    )


def _marks_in_year(
    obs: Sequence[Tuple[str, int, float]], unit: str, year: int
) -> float:
    return float(sum(m for u, y, m in obs if u == unit and y == year))


def assemble_training_rows(
    obs: Sequence[Tuple[str, int, float]],
    years: Sequence[int],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[str]]:
    """
    Build causal supervised dataset.

    For each target year T in years[1:]:
      X = features from years < T (as known up to T-1)
      y_appear = 1 if unit had any marks in T else 0
      y_marks  = total marks for unit in T

    Units that never appear in any year are skipped (no signal).
    Returns X, y_appear, y_marks, unit_labels (aligned rows).
    """
    if len(years) < 2:
        return (
            np.zeros((0, 4)),
            np.zeros(0),
            np.zeros(0),
            [],
        )

    units = sorted({u for u, _, _ in obs})
    rows_x: List[List[float]] = []
    rows_a: List[int] = []
    rows_m: List[float] = []
    row_units: List[str] = []

    target_years = list(years[1:])  # need at least one prior year
    for T in target_years:
        for unit in units:
            feats = _features_from_obs_before(obs, unit, cutoff_year=T)
            marks_T = _marks_in_year(obs, unit, T)
            appeared = 1 if marks_T > 0 else 0
            rows_x.append(list(feats))
            rows_a.append(appeared)
            rows_m.append(marks_T)
            row_units.append(unit)

    X = np.asarray(rows_x, dtype=float)
    y_a = np.asarray(rows_a, dtype=int)
    y_m = np.asarray(rows_m, dtype=float)
    return X, y_a, y_m, row_units


def train_models(
    obs: Sequence[Tuple[str, int, float]],
    years: Sequence[int],
) -> Optional[TrainedModels]:
    """
    Fit LogisticRegression (appearance) + LinearRegression (marks) per subject.
    Returns None if data is insufficient after assembly.
    """
    X, y_a, y_m, _ = assemble_training_rows(obs, years)
    if X.shape[0] < 8:
        # Absolute floor: need a handful of rows even if year count passed
        logger.info(
            "government_ml: only %d training rows after causal assembly — skip train",
            X.shape[0],
        )
        return None

    # Appearance: need both classes ideally; if only one class, logistic is useless
    if len(np.unique(y_a)) < 2:
        logger.info("government_ml: single appearance class — skip logistic train")
        return None

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    appear = LogisticRegression(
        max_iter=500,
        class_weight="balanced",
        solver="lbfgs",
        random_state=42,
    )
    appear.fit(Xs, y_a)

    marks = LinearRegression()
    marks.fit(Xs, y_m)

    return TrainedModels(
        appearance_model=appear,
        marks_model=marks,
        scaler=scaler,
        feature_names=FEATURE_NAMES,
        n_train_rows=int(X.shape[0]),
        n_units=len({u for u, _, _ in obs}),
        years_used=list(years),
        model_version=MODEL_VERSION,
    )


def _inference_feature_matrix(
    obs: Sequence[Tuple[str, int, float]],
    units: Sequence[str],
    *,
    next_exam_year: int,
) -> np.ndarray:
    """Features as known just before next_exam_year (all history with year < next)."""
    rows = [
        list(_features_from_obs_before(obs, u, cutoff_year=next_exam_year))
        for u in units
    ]
    return np.asarray(rows, dtype=float)


def _prob_label(p: float) -> str:
    if p >= 0.8:
        return "very_high"
    if p >= 0.65:
        return "high"
    if p >= 0.4:
        return "moderate"
    return "low"


def _feature_rank_score(v: FeatureVector) -> float:
    trend_boost = 1.0 + max(-0.5, min(0.5, v.marks_trend / 20.0))
    gap_pen = 1.0 / (1.0 + 0.15 * max(0, v.last_asked_gap))
    return float(v.recency_weight) * max(1, v.recurrence_count) * trend_boost * gap_pen


def signal_based_predictions(
    vectors: Sequence[FeatureVector],
    *,
    subject_name: str = "Subject",
) -> List[Dict[str, Any]]:
    """
    Cold-start / insufficient-history path.
    Rank raw unit_features; mark clearly as signal-based (not model-based).
    """
    ranked = sorted(vectors, key=_feature_rank_score, reverse=True)
    out: List[Dict[str, Any]] = []
    for i, v in enumerate(ranked[:MAX_ITEMS], start=1):
        conf = min(
            0.72,
            max(
                0.32,
                0.28
                + 0.11 * min(v.recurrence_count, 5)
                + 0.07 * min(v.recency_weight, 3.0)
                + (0.05 if v.marks_trend > 0 else 0.0),
            ),
        )
        text = (
            f"[SIGNAL-BASED, not model-trained] Likely focus: {v.key} — "
            f"recurrence={v.recurrence_count}, recency_weight={v.recency_weight:.3f}, "
            f"marks_trend={v.marks_trend:.2f}, last_asked_gap={v.last_asked_gap}."
        )
        reasoning = (
            f"Insufficient multi-year history (< {MIN_HISTORY_YEARS} distinct years) "
            f"for trained government_ml models on this subject. Ranked from raw "
            f"unit_features signals only. recurrence={v.recurrence_count}, "
            f"recency_weight={v.recency_weight:.3f}, marks_trend={v.marks_trend:.3f}, "
            f"last_asked_gap={v.last_asked_gap}."
        )
        # Heuristic marks weight from recurrence + trend (not a model)
        est_marks = max(1, int(round(4 + 0.8 * v.recurrence_count + max(0, v.marks_trend))))
        out.append(
            {
                "question_number": i,
                "text": text,
                "topic": v.key,
                "unit": v.key,
                "marks": est_marks,
                "probability": _prob_label(conf),
                "confidence_score": round(conf, 4),
                "reasoning": reasoning,
                "source": "signal_ranked",
                "p_appear": conf,
                "predicted_marks": float(est_marks),
                "features": {
                    "recurrence_count": v.recurrence_count,
                    "recency_weight": v.recency_weight,
                    "marks_trend": v.marks_trend,
                    "last_asked_gap": v.last_asked_gap,
                },
            }
        )
    return out


def model_based_predictions(
    models: TrainedModels,
    obs: Sequence[Tuple[str, int, float]],
    *,
    next_exam_year: int,
) -> List[Dict[str, Any]]:
    units = sorted({u for u, _, _ in obs})
    if not units:
        return []

    X = _inference_feature_matrix(obs, units, next_exam_year=next_exam_year)
    Xs = models.scaler.transform(X)

    # P(appear)
    if hasattr(models.appearance_model, "predict_proba"):
        proba = models.appearance_model.predict_proba(Xs)
        # class order from model.classes_
        classes = list(models.appearance_model.classes_)
        if 1 in classes:
            p_idx = classes.index(1)
            p_appear = proba[:, p_idx]
        else:
            p_appear = proba[:, -1]
    else:
        p_appear = models.appearance_model.predict(Xs).astype(float)

    pred_marks = models.marks_model.predict(Xs)
    pred_marks = np.maximum(pred_marks, 0.0)

    items: List[Dict[str, Any]] = []
    for i, unit in enumerate(units):
        p = float(p_appear[i])
        m = float(pred_marks[i])
        feats = {
            "recurrence_count": float(X[i, 0]),
            "recency_weight": float(X[i, 1]),
            "marks_trend": float(X[i, 2]),
            "last_asked_gap": float(X[i, 3]),
        }
        conf = max(0.05, min(0.95, p))
        text = (
            f"Predicted unit: {unit} — P(appear)={p:.3f}, "
            f"expected marks≈{m:.1f} (model {models.model_version})."
        )
        reasoning = (
            f"Model-based ({models.model_version}). Causal features before {next_exam_year}: "
            f"recurrence={feats['recurrence_count']:.0f}, "
            f"recency_weight={feats['recency_weight']:.3f}, "
            f"marks_trend={feats['marks_trend']:.3f}, "
            f"last_asked_gap={feats['last_asked_gap']:.0f}. "
            f"Trained on {models.n_train_rows} rows across years {models.years_used}."
        )
        items.append(
            {
                "question_number": 0,  # filled after sort
                "text": text,
                "topic": unit,
                "unit": unit,
                "marks": max(1, int(round(m))) if p >= 0.35 else max(1, int(round(m * 0.5))),
                "probability": _prob_label(conf),
                "confidence_score": round(conf, 4),
                "reasoning": reasoning,
                "source": "government_ml",
                "p_appear": round(p, 4),
                "predicted_marks": round(m, 2),
                "features": feats,
            }
        )

    # Rank by P(appear) then predicted marks
    items.sort(key=lambda x: (x["p_appear"], x["predicted_marks"]), reverse=True)
    final = items[:MAX_ITEMS]
    for i, it in enumerate(final, start=1):
        it["question_number"] = i
    return final


def generate_government_predictions(
    user_id: str,
    subject_id: str,
    subject: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Entry point for government track.

    1. Collect tagged observations + distinct years
    2. If years < MIN_HISTORY_YEARS → signal-based ranking of unit_features
    3. Else train logistic + linear on causal rows, score next exam year
    4. Persist via caller with source_type=government_ml and model_version
    """
    from app.services.feature_engineering import compute_government_unit_features

    subject_name = str(subject.get("name") or "Subject")
    obs, years = collect_tagged_observations(subject_id)

    # Always refresh / read current feature table for transparency in response
    try:
        current_vectors = compute_government_unit_features(
            subject_id, persist=True
        )
    except Exception as e:
        logger.warning("compute_government_unit_features failed: %s", e)
        current_vectors = []
        if obs:
            # Offline compute without persist
            current_vectors = compute_features_for_observations(
                obs,
                reference_year=(max(years) if years else None),
            )

    feature_table = [
        {
            "unit_name": v.key,
            "recurrence_count": v.recurrence_count,
            "recency_weight": round(v.recency_weight, 4),
            "marks_trend": round(v.marks_trend, 4),
            "last_asked_gap": v.last_asked_gap,
        }
        for v in sorted(
            current_vectors,
            key=lambda x: (x.recency_weight * max(1, x.recurrence_count)),
            reverse=True,
        )
    ]

    n_years = len(years)
    cold = n_years < MIN_HISTORY_YEARS or not obs

    if cold:
        preds = signal_based_predictions(current_vectors, subject_name=subject_name)
        model_version = SIGNAL_ONLY_VERSION
        source_tag = "signal_ranked"
        warning = (
            f"SIGNAL-BASED predictions (not model-trained). "
            f"This subject has {n_years} distinct tagged year(s); "
            f"government_ml requires ≥ {MIN_HISTORY_YEARS} years of history "
            f"before logistic/linear models are fit. Ranked from unit_features only."
        )
        fallback_used = True
        fallback_reason = "insufficient_history_years"
        train_meta: Dict[str, Any] = {
            "trained": False,
            "n_years": n_years,
            "min_required": MIN_HISTORY_YEARS,
            "years": years,
        }
    else:
        models = train_models(obs, years)
        if models is None:
            preds = signal_based_predictions(current_vectors, subject_name=subject_name)
            model_version = SIGNAL_ONLY_VERSION
            source_tag = "signal_ranked"
            warning = (
                "SIGNAL-BASED predictions (not model-trained). "
                "Year count met threshold but causal assembly lacked class diversity "
                "or enough rows for a stable fit. Fell back to unit_features ranking."
            )
            fallback_used = True
            fallback_reason = "train_failed_or_degenerate"
            train_meta = {
                "trained": False,
                "n_years": n_years,
                "years": years,
                "reason": "degenerate_labels_or_too_few_rows",
            }
        else:
            next_year = max(years) + 1
            preds = model_based_predictions(models, obs, next_exam_year=next_year)
            model_version = models.model_version
            source_tag = "government_ml"
            warning = None
            fallback_used = False
            fallback_reason = None
            train_meta = {
                "trained": True,
                "n_years": n_years,
                "years": years,
                "n_train_rows": models.n_train_rows,
                "n_units": models.n_units,
                "next_exam_year": next_year,
                "model_version": model_version,
            }

    unit_coverage: Dict[str, int] = {}
    for p in preds:
        u = str(p.get("unit") or "General")
        unit_coverage[u] = unit_coverage.get(u, 0) + 1
    total_marks = sum(int(p.get("marks") or 0) for p in preds)

    return {
        "predictions": preds,
        "predicted_questions": preds,
        "total_marks": total_marks,
        "coverage_percentage": 0,
        "unit_coverage": unit_coverage,
        "generated_at": _now_iso(),
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason,
        "message": None,
        "warning": warning,
        "source": source_tag,
        "source_type": SOURCE_TYPE_GOVERNMENT,
        "model_version": model_version,
        "ml_analysis_json": {
            "source": source_tag,
            "source_type": SOURCE_TYPE_GOVERNMENT,
            "model_version": model_version,
            "train_meta": train_meta,
            "unit_features_table": feature_table,
            "min_history_years": MIN_HISTORY_YEARS,
            "feature_names": list(FEATURE_NAMES),
        },
    }


# ---------------------------------------------------------------------------
# Offline / demo helpers (no DB) — used by scripts and sanity checks
# ---------------------------------------------------------------------------


def demo_train_and_predict(
    obs: Sequence[Tuple[str, int, float]],
) -> Dict[str, Any]:
    """
    Pure-function demo path: assemble, train, score without repositories.
    Returns raw feature table (current) + predictions side by side.
    """
    years = sorted({y for _, y, _ in obs})
    vectors = compute_features_for_observations(
        obs, reference_year=(max(years) if years else None)
    )
    feature_table = [
        {
            "unit_name": v.key,
            "recurrence_count": v.recurrence_count,
            "recency_weight": round(v.recency_weight, 4),
            "marks_trend": round(v.marks_trend, 4),
            "last_asked_gap": v.last_asked_gap,
        }
        for v in sorted(
            vectors,
            key=lambda x: (x.recency_weight * max(1, x.recurrence_count)),
            reverse=True,
        )
    ]

    n_years = len(years)
    if n_years < MIN_HISTORY_YEARS:
        preds = signal_based_predictions(vectors)
        return {
            "mode": "signal",
            "model_version": SIGNAL_ONLY_VERSION,
            "years": years,
            "feature_table": feature_table,
            "predictions": preds,
            "warning": f"Need ≥{MIN_HISTORY_YEARS} years; have {n_years}",
        }

    models = train_models(obs, years)
    if models is None:
        preds = signal_based_predictions(vectors)
        return {
            "mode": "signal",
            "model_version": SIGNAL_ONLY_VERSION,
            "years": years,
            "feature_table": feature_table,
            "predictions": preds,
            "warning": "Train failed (degenerate)",
        }

    next_year = max(years) + 1
    preds = model_based_predictions(models, obs, next_exam_year=next_year)

    # Also expose causal training matrix sample for inspection
    X, y_a, y_m, row_units = assemble_training_rows(obs, years)
    sample_rows = []
    for i in range(min(12, len(row_units))):
        sample_rows.append(
            {
                "unit": row_units[i],
                "features": {
                    FEATURE_NAMES[j]: float(X[i, j]) for j in range(4)
                },
                "label_appear": int(y_a[i]),
                "label_marks": float(y_m[i]),
            }
        )

    return {
        "mode": "model",
        "model_version": models.model_version,
        "years": years,
        "next_exam_year": next_year,
        "n_train_rows": models.n_train_rows,
        "feature_table": feature_table,
        "predictions": preds,
        "training_sample_rows": sample_rows,
        "warning": None,
    }
