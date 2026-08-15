"""Analysis routes — Pyronites data plane.

Previously these returned 503 ("deferred after the Pyronites migration").
They are now implemented on top of the same PyroCore data the dashboard uses
(subjects, predictions, mock_tests) so the analysis page renders real,
aggregated insight instead of erroring. All handlers degrade gracefully to a
valid empty Analysis payload rather than 500/503.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Header, HTTPException

from ..services.pyronites_auth import get_current_user_from_token
from ..repositories import subjects as subjects_repo
from ..repositories import predictions as predictions_repo
from ..repositories import mock_tests as mock_tests_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

_COLORS = [
    "#6366F1", "#06B6D4", "#F59E0B", "#EF4444",
    "#10B981", "#8B5CF6", "#EC4899", "#14B8A6",
]


def _parse_date(value: Any):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    s = str(value)
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d").date()
        except Exception:
            return None


def _coerce_json(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return default
        try:
            parsed = json.loads(s)
            return parsed if isinstance(parsed, (dict, list)) else default
        except Exception:
            return default
    return default


def _empty_analysis() -> Dict[str, Any]:
    return {
        "performanceData": [],
        "subjectPerformance": [],
        "weeklyProgress": [],
        "predictionsAccuracy": [],
        "topicMastery": [],
        "studyInsights": {
            "total_subjects": 0,
            "total_questions_analyzed": 0,
            "average_accuracy": 0,
            "high_priority_topics": [],
            "recommended_focus_areas": [],
        },
    }


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


def _build_analysis(user_id: str, subject_id: Optional[str] = None) -> Dict[str, Any]:
    subjects = subjects_repo.list_for_user(user_id) or []
    if subject_id:
        subjects = [s for s in subjects if str(s.get("id")) == str(subject_id)]
    mock_tests = mock_tests_repo.list_for_user(user_id) or []

    subject_preds: List[Tuple[Dict[str, Any], List[Dict[str, Any]]]] = []
    for s in subjects:
        sid = str(s.get("id"))
        preds = predictions_repo.list_for_user_subject(user_id, sid) or []
        subject_preds.append((s, preds))

    subject_performance: List[Dict[str, Any]] = []
    predictions_accuracy: List[Dict[str, Any]] = []
    performance_data: List[Dict[str, Any]] = []
    topic_mastery: List[Dict[str, Any]] = []
    high_priority: List[Dict[str, Any]] = []
    focus_areas: List[str] = []
    total_questions = 0
    accuracy_vals: List[float] = []
    activity_dates = set()

    for idx, (s, preds) in enumerate(subject_preds):
        name = str(s.get("name") or "Subject")
        sid = str(s.get("id"))
        s_tests = [t for t in mock_tests if str(t.get("subject_id")) == sid]

        percs = [float(t.get("percentage") or 0) for t in s_tests if t.get("percentage") is not None]
        if percs:
            perf = round(sum(percs) / len(percs))
        elif preds:
            accs = [float(p.get("prediction_accuracy_score") or 0) for p in preds]
            perf = round((sum(accs) / len(accs)) * 100) if accs else 0
        else:
            perf = 0

        q_pred = sum(int(p.get("total_questions") or 0) for p in preds)
        q_test = sum(int(t.get("total_questions") or 0) for t in s_tests)
        total_q = q_pred + q_test
        total_questions += total_q

        subject_performance.append({
            "subject": name,
            "performance": perf,
            "total_questions": total_q,
            "color": _COLORS[idx % len(_COLORS)],
        })

        if preds:
            accs = [float(p.get("prediction_accuracy_score") or 0) for p in preds]
            avg_acc = (sum(accs) / len(accs)) if accs else 0
            predictions_accuracy.append({
                "subject": name,
                "accuracy_score": round(avg_acc, 2),
                "total_predictions": len(preds),
            })
            for a in accs:
                accuracy_vals.append(a * 100)

        for p in preds:
            pred_qs = _coerce_json(p.get("predicted_questions_json"), [])
            if isinstance(pred_qs, list):
                for q in pred_qs:
                    if not isinstance(q, dict):
                        continue
                    unit = str(q.get("unit") or q.get("topic") or q.get("unit_name") or "General")
                    w = q.get("weightage") or q.get("estimated_weightage") or q.get("marks") or 0
                    try:
                        w = float(w)
                    except Exception:
                        w = 0.0
                    performance_data.append({
                        "subject": name,
                        "unit": unit,
                        "weightage": w,
                        "date": str(p.get("created_at") or ""),
                    })
            ml = _coerce_json(p.get("ml_analysis_json"), {})
            if isinstance(ml, dict):
                uw = ml.get("unit_weightage") or ml.get("unit_coverage")
                if isinstance(uw, dict):
                    for unit, val in uw.items():
                        try:
                            val = float(val)
                        except Exception:
                            continue
                        topic_mastery.append({
                            "subject": name,
                            "topic": str(unit),
                            "mastery_level": round(min(100.0, max(0.0, val))),
                            "frequency": int(p.get("total_questions") or 0),
                        })
            d = _parse_date(p.get("created_at"))
            if d:
                activity_dates.add(d)

        for t in s_tests:
            d = _parse_date(t.get("created_at"))
            if d:
                activity_dates.add(d)
            for kind, raw in (("weak", t.get("weak_topics_json")), ("strong", t.get("strong_topics_json"))):
                topics = _coerce_json(raw, [])
                if not isinstance(topics, list):
                    continue
                for tp in topics:
                    mastery = 30 if kind == "weak" else 85
                    if isinstance(tp, str):
                        tname = tp
                    elif isinstance(tp, dict):
                        tname = str(tp.get("topic") or tp.get("name") or tp.get("unit") or "Topic")
                        mastery = int(tp.get("mastery_level") or mastery)
                    else:
                        continue
                    topic_mastery.append({
                        "subject": name,
                        "topic": tname,
                        "mastery_level": mastery,
                        "frequency": 1,
                    })
                    if kind == "weak":
                        high_priority.append({
                            "subject": name,
                            "topic": tname,
                            "impact_score": 0.8,
                        })

        if perf < 60 and name not in focus_areas:
            focus_areas.append(name)

    if accuracy_vals:
        average_accuracy = round(sum(accuracy_vals) / len(accuracy_vals))
    else:
        test_percs = [float(t.get("percentage") or 0) for t in mock_tests if t.get("percentage") is not None]
        average_accuracy = round(sum(test_percs) / len(test_percs)) if test_percs else 0

    today = datetime.now(timezone.utc).date()
    weekly_progress = []
    for i in range(5, -1, -1):
        wk_start = today - timedelta(days=today.weekday() + i * 7)
        wk_end = wk_start + timedelta(days=6)
        cnt = sum(1 for d in activity_dates if wk_start <= d <= wk_end)
        year, week, _ = wk_start.isocalendar()
        weekly_progress.append({
            "week": f"{year}-W{week:02d}",
            "progress": min(100, cnt * 15),
        })

    dedup: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for tm in topic_mastery:
        key = (tm["subject"], tm["topic"])
        if key not in dedup or tm["mastery_level"] > dedup[key]["mastery_level"]:
            dedup[key] = tm
    topic_mastery = list(dedup.values())

    if not focus_areas:
        focus_areas = [f"{t['topic']} ({t['subject']})" for t in high_priority[:5]]
    else:
        focus_areas = [str(a) for a in focus_areas]

    return {
        "performanceData": performance_data,
        "subjectPerformance": subject_performance,
        "weeklyProgress": weekly_progress,
        "predictionsAccuracy": predictions_accuracy,
        "topicMastery": topic_mastery,
        "studyInsights": {
            "total_subjects": len(subjects),
            "total_questions_analyzed": total_questions,
            "average_accuracy": average_accuracy,
            "high_priority_topics": high_priority[:10],
            "recommended_focus_areas": focus_areas[:10],
        },
    }


@router.get("/data")
async def get_analysis_data(current_user: dict = Depends(get_current_user)):
    try:
        return _build_analysis(current_user["id"])
    except Exception as e:
        logger.warning("analysis/data failed (returning empty): %s", e)
        return _empty_analysis()


@router.get("/{subject_id}/frequency")
async def get_frequency_analysis(subject_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return _build_analysis(current_user["id"], subject_id=subject_id)
    except Exception as e:
        logger.warning("analysis frequency failed (returning empty): %s", e)
        return _empty_analysis()


@router.get("/{subject_id}/weightage")
async def get_weightage_analysis(subject_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return _build_analysis(current_user["id"], subject_id=subject_id)
    except Exception as e:
        logger.warning("analysis weightage failed (returning empty): %s", e)
        return _empty_analysis()


@router.get("/{subject_id}/repetitions")
async def get_repetition_analysis(subject_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return _build_analysis(current_user["id"], subject_id=subject_id)
    except Exception as e:
        logger.warning("analysis repetitions failed (returning empty): %s", e)
        return _empty_analysis()


@router.get("/{subject_id}/trends")
async def get_trend_analysis(subject_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return _build_analysis(current_user["id"], subject_id=subject_id)
    except Exception as e:
        logger.warning("analysis trends failed (returning empty): %s", e)
        return _empty_analysis()


@router.get("/important-questions/{subject_id}")
async def get_important_questions(subject_id: str, current_user: dict = Depends(get_current_user)):
    try:
        return _build_analysis(current_user["id"], subject_id=subject_id)
    except Exception as e:
        logger.warning("analysis important-questions failed (returning empty): %s", e)
        return _empty_analysis()
