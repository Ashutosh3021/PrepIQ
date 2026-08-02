"""
Pyronites-backed prediction pipeline (Fix Phase C + Phase 6 university signals).

University track: LLM prompt + stats fallback consume shared feature_engineering
signals (recurrence, recency_weight, marks_trend, last_asked_gap) per topic.

Tiering (Tier 0 / cold / full via PREDICTION_MIN_PAPERS_FULL) is unchanged.
source_type persisted as "university_llm" for this path.
"""
from __future__ import annotations

import json
import logging
import os
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

from app.core.llm_provider import get_llm_client
from app.repositories import papers as papers_repo
from app.repositories import predictions as predictions_repo
from app.repositories import questions as questions_repo
from app.repositories import subjects as subjects_repo
from app.services.feature_engineering import (
    FeatureVector,
    compute_university_topic_features,
    features_to_prompt_block,
)

logger = logging.getLogger(__name__)

MIN_PAPERS_FULL = int(os.getenv("PREDICTION_MIN_PAPERS_FULL", "3") or "3")
MAX_ITEMS = int(os.getenv("PREDICTION_MAX_ITEMS", "10") or "10")
CONTEXT_CHARS = int(os.getenv("PREDICTION_CONTEXT_CHARS", "12000") or "12000")

_VALID_PROB = {"very_high", "high", "moderate", "low"}
SOURCE_TYPE_UNIVERSITY = "university_llm"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _prob_from_confidence(conf: float) -> str:
    if conf >= 0.8:
        return "very_high"
    if conf >= 0.65:
        return "high"
    if conf >= 0.4:
        return "moderate"
    return "low"


def normalize_predicted_item(raw: Dict[str, Any], index: int, source: str) -> Dict[str, Any]:
    """Stable shape for API + mock-test weighting (confidence_score, text, topic/unit, marks)."""
    text = str(raw.get("text") or raw.get("question_text") or "").strip()
    topic = str(raw.get("topic") or raw.get("unit") or raw.get("unit_name") or "General").strip() or "General"
    try:
        marks = int(raw.get("marks") if raw.get("marks") is not None else 5)
    except (TypeError, ValueError):
        marks = 5
    marks = max(1, marks)
    try:
        conf = float(raw.get("confidence_score") if raw.get("confidence_score") is not None else 0.5)
    except (TypeError, ValueError):
        conf = 0.5
    conf = max(0.0, min(1.0, conf))
    prob = str(raw.get("probability") or "").lower().strip()
    if prob not in _VALID_PROB:
        prob = _prob_from_confidence(conf)
    try:
        qn = int(raw.get("question_number") or index)
    except (TypeError, ValueError):
        qn = index
    return {
        "question_number": qn,
        "text": text,
        "topic": topic,
        "unit": topic,
        "marks": marks,
        "probability": prob,
        "confidence_score": conf,
        "reasoning": str(raw.get("reasoning") or ""),
        "source": source,
        "question_text": text,
        "id": str(raw.get("id") or f"pred-{index}"),
    }


def _build_stats(question_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    units: Counter = Counter()
    marks: Counter = Counter()
    samples: List[str] = []
    for q in question_rows:
        unit = str(q.get("unit_name") or q.get("unit") or "General")
        units[unit] += 1
        try:
            m = int(q.get("marks") or 0)
        except (TypeError, ValueError):
            m = 0
        if m:
            marks[m] += 1
        text = str(q.get("question_text") or q.get("text") or "").strip()
        if text and len(samples) < 40:
            samples.append(text[:400])
    return {
        "unit_frequency": dict(units),
        "marks_distribution": {str(k): v for k, v in marks.items()},
        "total_questions": len(question_rows),
        "sample_questions": samples,
    }


def _feature_rank_score(v: FeatureVector) -> float:
    """Higher = more likely to appear again (shared ranking for fallback)."""
    # Recency-weighted recurrence, boost rising marks, penalize long silence lightly
    trend_boost = 1.0 + max(-0.5, min(0.5, v.marks_trend / 20.0))
    gap_pen = 1.0 / (1.0 + 0.15 * max(0, v.last_asked_gap))
    return float(v.recency_weight) * max(1, v.recurrence_count) * trend_boost * gap_pen


def _trend_phrase(slope: float) -> str:
    if slope > 0.5:
        return "marks trend increasing"
    if slope < -0.5:
        return "marks trend decreasing"
    return "marks trend flat"


def _stats_fallback_from_features(
    vectors: Sequence[FeatureVector],
    source: str,
) -> List[Dict[str, Any]]:
    """
    Ranked fallback items grounded in the same 4-signal table as the LLM prompt.
    Not generic study tips — each item cites recurrence / recency / trend / gap.
    """
    ranked = sorted(vectors, key=_feature_rank_score, reverse=True)
    out: List[Dict[str, Any]] = []
    for i, v in enumerate(ranked[:MAX_ITEMS], start=1):
        trend = _trend_phrase(v.marks_trend)
        conf = min(
            0.75,
            max(
                0.35,
                0.3
                + 0.12 * min(v.recurrence_count, 5)
                + 0.08 * min(v.recency_weight, 3.0)
                + (0.05 if v.marks_trend > 0 else 0.0),
            ),
        )
        text = (
            f"Likely exam focus: {v.key} — appeared across {v.recurrence_count} year(s), "
            f"recency_weight={v.recency_weight:.3f}, {trend} (slope={v.marks_trend:.2f}), "
            f"last asked {v.last_asked_gap} year(s) ago."
        )
        reasoning = (
            f"Signal-ranked fallback (no LLM). Primary signals: recurrence={v.recurrence_count}, "
            f"recency_weight={v.recency_weight:.3f}, marks_trend={v.marks_trend:.3f}, "
            f"last_asked_gap={v.last_asked_gap}."
        )
        out.append(
            normalize_predicted_item(
                {
                    "question_number": i,
                    "text": text,
                    "topic": v.key,
                    "unit": v.key,
                    "marks": 5,
                    "confidence_score": conf,
                    "reasoning": reasoning,
                },
                i,
                source,
            )
        )
    return out


def _stats_fallback_predictions(stats: Dict[str, Any], source: str) -> List[Dict[str, Any]]:
    """Legacy frequency-only fallback when feature vectors are empty."""
    units = stats.get("unit_frequency") or {}
    ranked = sorted(units.items(), key=lambda x: x[1], reverse=True)
    out: List[Dict[str, Any]] = []
    for i, (unit, count) in enumerate(ranked[:MAX_ITEMS], start=1):
        total = max(int(stats.get("total_questions") or 1), 1)
        conf = min(0.35 + (count / total) * 0.4, 0.75)
        out.append(
            normalize_predicted_item(
                {
                    "question_number": i,
                    "text": (
                        f"Topic focus: {unit} (raw frequency={count}/{total}; "
                        f"year-level feature signals unavailable for this subject)."
                    ),
                    "topic": unit,
                    "unit": unit,
                    "marks": 5,
                    "confidence_score": conf,
                    "reasoning": (
                        f"Frequency-only fallback. count={count}, total_questions={total}. "
                        f"Feature signals missing (no exam_year / topic years)."
                    ),
                },
                i,
                source,
            )
        )
    return out


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _call_llm(prompt: str) -> List[Dict[str, Any]]:
    client = get_llm_client("prediction")
    if not client.is_available:
        return []
    try:
        try:
            parsed = client.generate_json(prompt, expect_list=False)
        except Exception:
            text = client.generate_text(prompt)
            parsed = json.loads(_strip_fences(text))

        raw_list = None
        if isinstance(parsed, dict):
            raw_list = parsed.get("predictions") or parsed.get("items")
        elif isinstance(parsed, list):
            raw_list = parsed
        if not isinstance(raw_list, list):
            return []

        out: List[Dict[str, Any]] = []
        for i, item in enumerate(raw_list[:MAX_ITEMS], start=1):
            if not isinstance(item, dict):
                continue
            norm = normalize_predicted_item(item, i, "llm")
            if norm["text"]:
                out.append(norm)
        return out
    except Exception as e:
        logger.warning("Prediction LLM failed: %s", e)
        return []


def generate_predictions(user_id: str, subject_id: str) -> Dict[str, Any]:
    subject = subjects_repo.get_for_user(subject_id, user_id)
    if not subject:
        raise ValueError("Subject not found")

    completed = papers_repo.list_completed_for_subject(subject_id)
    paper_count = len(completed)
    question_rows = questions_repo.list_for_subject(subject_id)
    completed_ids = {str(p.get("id")) for p in completed}
    if completed_ids:
        filtered = [q for q in question_rows if str(q.get("paper_id")) in completed_ids]
        if filtered:
            question_rows = filtered

    if paper_count == 0 and question_rows:
        paper_count = len({str(q.get("paper_id")) for q in question_rows if q.get("paper_id")})

    # Tier 0 — unchanged
    if paper_count == 0 or not question_rows:
        return {
            "id": None,
            "subject_id": subject_id,
            "predictions": [],
            "predicted_questions": [],
            "total_marks": 0,
            "coverage_percentage": 0,
            "unit_coverage": {},
            "generated_at": _now(),
            "fallback_used": True,
            "fallback_reason": "no_papers" if paper_count == 0 else "no_questions",
            "message": (
                "Upload at least one past paper and wait for extraction to get predictions. "
                f"Add {MIN_PAPERS_FULL}+ papers for fuller AI-powered predictions."
            ),
            "source": "no_data",
            "source_type": SOURCE_TYPE_UNIVERSITY,
            "warning": None,
        }

    stats = _build_stats(question_rows)
    subject_name = str(subject.get("name") or "Subject")
    syllabus = subject.get("syllabus_json")
    syllabus_text = ""
    if syllabus:
        syllabus_text = json.dumps(syllabus) if isinstance(syllabus, (dict, list)) else str(syllabus)

    # Phase 4 university signals (on-request; no unit_features write)
    try:
        topic_features = compute_university_topic_features(subject_id)
    except Exception as e:
        logger.warning("university topic features failed: %s", e)
        topic_features = []

    feature_block = features_to_prompt_block(topic_features, limit=25)
    feature_json = [
        {
            "topic": v.key,
            "recurrence_count": v.recurrence_count,
            "recency_weight": v.recency_weight,
            "marks_trend": v.marks_trend,
            "last_asked_gap": v.last_asked_gap,
        }
        for v in topic_features
    ]

    cold = paper_count < MIN_PAPERS_FULL
    source_tag = "cold_start" if cold else "full"
    warning = (
        "Generated with limited papers — treat as guidance, not a full historical pattern analysis."
        if cold
        else None
    )

    samples = stats.get("sample_questions") or []
    sample_block = "\n".join(f"- {s}" for s in samples)[:CONTEXT_CHARS]

    prompt = f"""You are an exam prediction engine for university/engineering students.
Subject: {subject_name}
Papers analyzed: {paper_count}
Question count: {stats.get('total_questions')}

STRUCTURED TOPIC SIGNALS (primary evidence — use these numbers):
Each row is topic | recurrence_count | recency_weight | marks_trend_slope | last_asked_gap_years
{feature_block}

Structured JSON of the same signals:
{json.dumps(feature_json)[:4000]}

Raw frequency counts (secondary, for volume only):
{json.dumps(stats.get('unit_frequency') or {})}
Marks distribution: {json.dumps(stats.get('marks_distribution') or {})}
Syllabus (optional): {syllabus_text[:2000]}

Sample extracted questions (for wording/style grounding only):
{sample_block}

Return JSON only with this shape:
{{"predictions":[{{"question_number":1,"text":"...","topic":"...","unit":"...","marks":5,"probability":"high","confidence_score":0.0,"reasoning":"..."}}],"total_marks":0,"coverage_percentage":0,"unit_coverage":{{}},"generated_at":"ISO"}}

Rules:
- Rank topics using the structured signals (high recurrence + high recency_weight + rising marks_trend + small last_asked_gap).
- In every reasoning field, cite the numeric signals that most influenced the item
  (e.g. "recurrence=3, recency_weight=1.72, marks_trend=+2.1, last_asked_gap=1").
- Do not invent past papers you were not given.
- confidence_score between 0 and 1.
- At most {MAX_ITEMS} predictions, ranked by likelihood.
- Sample question text is for style/grounding only; do not copy it verbatim as a "prediction".
"""

    llm_preds = _call_llm(prompt)
    fallback_used = False
    if not llm_preds:
        if topic_features:
            llm_preds = _stats_fallback_from_features(topic_features, "stats")
        else:
            llm_preds = _stats_fallback_predictions(stats, "stats")
        fallback_used = True
        source_tag = "stats" if not cold else "cold_start"

    llm_preds.sort(key=lambda x: float(x.get("confidence_score") or 0), reverse=True)
    final = llm_preds[:MAX_ITEMS]
    for i, p in enumerate(final, start=1):
        p["question_number"] = i
        if p.get("source") == "llm":
            p["source"] = source_tag

    unit_coverage: Dict[str, int] = {}
    for p in final:
        u = str(p.get("unit") or "General")
        unit_coverage[u] = unit_coverage.get(u, 0) + 1
    total_marks = sum(int(p.get("marks") or 0) for p in final)

    hist_units = set((stats.get("unit_frequency") or {}).keys())
    if hist_units and final:
        coverage_percentage = int(round(100 * len(set(unit_coverage) & hist_units) / len(hist_units)))
    else:
        coverage_percentage = 0

    record_id: Optional[str] = None
    persist_warning: Optional[str] = None
    try:
        record = predictions_repo.create(
            user_id,
            subject_id,
            {
                "predictions": final,
                "total_questions": len(final),
                "total_marks": total_marks,
                "unit_coverage": unit_coverage,
                "ml_analysis_json": {
                    "source": source_tag,
                    "source_type": SOURCE_TYPE_UNIVERSITY,
                    "fallback_used": fallback_used,
                    "paper_count": paper_count,
                    "topic_features": feature_json,
                    "stats": {
                        "unit_frequency": stats.get("unit_frequency"),
                        "total_questions": stats.get("total_questions"),
                    },
                },
                "prediction_accuracy_score": 0.0,
                "source_type": SOURCE_TYPE_UNIVERSITY,
                "model_version": None,
            },
        )
        record_id = str(record.get("id")) if record else None
    except Exception as e:
        logger.error("Failed to persist prediction for subject %s: %s", subject_id, e)
        # Retry without source_type if column missing on remote schema
        msg = str(e)
        if "source_type" in msg or "Identifier" in msg:
            try:
                record = predictions_repo.create(
                    user_id,
                    subject_id,
                    {
                        "predictions": final,
                        "total_questions": len(final),
                        "total_marks": total_marks,
                        "unit_coverage": unit_coverage,
                        "ml_analysis_json": {
                            "source": source_tag,
                            "source_type": SOURCE_TYPE_UNIVERSITY,
                            "fallback_used": fallback_used,
                            "paper_count": paper_count,
                            "topic_features": feature_json,
                        },
                        "prediction_accuracy_score": 0.0,
                    },
                )
                record_id = str(record.get("id")) if record else None
            except Exception as e2:
                persist_warning = f"Generated in-memory only (persist failed: {e2})"
        else:
            persist_warning = f"Generated in-memory only (persist failed: {e})"

    combined_warning = warning
    if persist_warning:
        combined_warning = f"{warning + ' ' if warning else ''}{persist_warning}".strip()

    return {
        "id": record_id,
        "subject_id": subject_id,
        "predictions": final,
        "predicted_questions": final,
        "total_marks": total_marks,
        "coverage_percentage": coverage_percentage,
        "unit_coverage": unit_coverage,
        "generated_at": _now(),
        "fallback_used": fallback_used or cold,
        "fallback_reason": "llm_unavailable" if fallback_used else ("limited_papers" if cold else None),
        "message": None,
        "warning": combined_warning,
        "source": source_tag,
        "source_type": SOURCE_TYPE_UNIVERSITY,
    }


def get_prediction(prediction_id: str, user_id: str) -> Dict[str, Any]:
    row = predictions_repo.get(prediction_id)
    if not row or str(row.get("user_id")) != str(user_id):
        raise ValueError("Prediction not found")
    return _row_to_response(row)


def get_latest_prediction(subject_id: str, user_id: str) -> Dict[str, Any]:
    subject = subjects_repo.get_for_user(subject_id, user_id)
    if not subject:
        raise ValueError("Subject not found")
    row = predictions_repo.get_latest(user_id, subject_id)
    if not row:
        raise ValueError("No predictions found for this subject")
    return _row_to_response(row)


def _row_to_response(row: Dict[str, Any]) -> Dict[str, Any]:
    raw = row.get("predicted_questions_json") or []
    if isinstance(raw, str):
        try:
            preds = json.loads(raw)
        except Exception:
            preds = []
    else:
        preds = raw if isinstance(raw, list) else []
    if isinstance(preds, list):
        preds = [
            normalize_predicted_item(p, i + 1, str(p.get("source") or "stored"))
            for i, p in enumerate(preds)
            if isinstance(p, dict)
        ]
    unit_coverage = row.get("unit_coverage_json") or {}
    if isinstance(unit_coverage, str):
        try:
            unit_coverage = json.loads(unit_coverage)
        except Exception:
            unit_coverage = {}
    return {
        "id": str(row.get("id")),
        "subject_id": str(row.get("subject_id")),
        "predictions": preds,
        "predicted_questions": preds,
        "total_marks": int(row.get("total_predicted_marks") or 0),
        "coverage_percentage": 0,
        "unit_coverage": unit_coverage if isinstance(unit_coverage, dict) else {},
        "generated_at": row.get("created_at") or _now(),
        "fallback_used": False,
        "source": "stored",
        "source_type": row.get("source_type") or SOURCE_TYPE_UNIVERSITY,
        "accuracy_score": row.get("prediction_accuracy_score"),
    }
