"""Dashboard stats — Pyronites data plane (Fix Phase D)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Set

from fastapi import APIRouter, Depends, Header, HTTPException

logger = logging.getLogger(__name__)

from ..services.pyronites_auth import get_current_user_from_token
from ..repositories import subjects as subjects_repo
from ..repositories import predictions as predictions_repo
from ..repositories import mock_tests as mock_tests_repo
from ..repositories import papers as papers_repo
from ..repositories import users as users_repo

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


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


@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user["id"]
        subjects = subjects_repo.list_for_user(user_id)
        subjects_count = len(subjects)
        subject_names = {str(s.get("id")): str(s.get("name") or "Subject") for s in subjects}

        # One query for every prediction the user owns. The old handler issued
        # a per-subject prediction query in five separate loops.
        predictions = predictions_repo.list_for_user(user_id)
        predictions_count = len(predictions)
        predictions_by_subject: Dict[str, List[Dict[str, Any]]] = {}
        for p in predictions:
            predictions_by_subject.setdefault(str(p.get("subject_id")), []).append(p)

        # Profile is best-effort: the users table may be missing/unreachable
        # (e.g. PyroCore rate limits or not yet migrated). JWT claims already
        # carry the targeting fields, so a failed read must not 500 the stats.
        try:
            profile = users_repo.get(user_id) or {}
        except Exception as e:
            logger.warning("dashboard profile read failed (continuing): %s", e)
            profile = {}
        days_to_exam = current_user.get("days_until_exam") or profile.get("days_until_exam")
        exam_date = current_user.get("exam_date") or profile.get("exam_date")
        if exam_date and days_to_exam is None:
            d = _parse_date(exam_date)
            if d:
                days_to_exam = max(0, (d - datetime.now(timezone.utc).date()).days)

        today = datetime.now().date()
        activity_dates: Set = set()
        for t in mock_tests_repo.list_for_user(user_id):
            d = _parse_date(t.get("created_at"))
            if d:
                activity_dates.add(d)
        for p in predictions:
            d = _parse_date(p.get("created_at"))
            if d:
                activity_dates.add(d)

        study_streak = 0
        check = today
        while check in activity_dates:
            study_streak += 1
            check -= timedelta(days=1)

        completion_percentage = 0
        if subjects_count > 0:
            with_pred = sum(
                1
                for s in subjects
                if predictions_by_subject.get(str(s.get("id")))
            )
            completion_percentage = int((with_pred / subjects_count) * 100)

        focus_area = "No subjects yet"
        if subjects:
            focus_area = subject_names[str(subjects[0].get("id"))]
            # prefer the subject owning the most recent prediction
            latest_ts = ""
            latest_name = None
            for p in predictions:
                ts = str(p.get("created_at") or "")
                if ts >= latest_ts:
                    latest_ts = ts
                    latest_name = subject_names.get(str(p.get("subject_id")))
            if latest_name:
                focus_area = latest_name

        recent_activity: List[Dict[str, Any]] = []
        for p in predictions:
            sname = subject_names.get(str(p.get("subject_id")), "Subject")
            recent_activity.append(
                {
                    "action": f"Generated predictions for {sname}",
                    "timestamp": str(p.get("created_at") or ""),
                }
            )
        for s in subjects:
            sid = str(s.get("id"))
            sname = subject_names.get(sid, "Subject")
            # question_papers has no user column, so papers are per-subject.
            for paper in papers_repo.list_for_subject(sid)[:3]:
                recent_activity.append(
                    {
                        "action": f"Uploaded paper for {sname}",
                        "timestamp": str(paper.get("created_at") or ""),
                    }
                )
        for t in mock_tests_repo.list_for_user(user_id):
            status_label = "Completed" if t.get("is_completed") else "Started"
            recent_activity.append(
                {
                    "action": f"{status_label} mock test",
                    "timestamp": str(t.get("created_at") or ""),
                }
            )
        recent_activity.sort(key=lambda x: x.get("timestamp") or "", reverse=True)

        return {
            "subjects_count": subjects_count,
            "predictions_count": predictions_count,
            "completion_percentage": completion_percentage,
            "focus_area": focus_area,
            "study_streak": study_streak,
            "days_to_exam": days_to_exam,
            "recent_activity": recent_activity[:5],
        }
    except Exception:
        # Full traceback goes to the server log; the client gets a generic
        # message instead of internals.
        logger.exception("dashboard stats failed")
        raise HTTPException(status_code=500, detail="Error fetching dashboard stats")


@router.get("/recent-activity")
async def get_recent_activity(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    items: List[Dict[str, Any]] = []
    subjects = subjects_repo.list_for_user(user_id)
    subject_names = {str(s.get("id")): str(s.get("name") or "Subject") for s in subjects}
    for s in subjects:
        items.append(
            {
                "id": str(s.get("id")),
                "type": "study",
                "title": f"Started {s.get('name')} preparation",
                "description": f"Added subject: {s.get('name')}",
                "timestamp": str(s.get("created_at") or ""),
            }
        )
    for p in predictions_repo.list_for_user(user_id):
        sname = subject_names.get(str(p.get("subject_id")), "Subject")
        items.append(
            {
                "id": str(p.get("id")),
                "type": "prediction",
                "title": f"Generated {sname} predictions",
                "description": f"Created {p.get('total_questions') or 0} question predictions",
                "timestamp": str(p.get("created_at") or ""),
            }
        )
    for t in mock_tests_repo.list_for_user(user_id):
        items.append(
            {
                "id": str(t.get("id")),
                "type": "test",
                "title": "Completed Mock Test" if t.get("is_completed") else "Started Mock Test",
                "description": f"Score {t.get('percentage')}" if t.get("percentage") is not None else "Mock test",
                "timestamp": str(t.get("created_at") or ""),
            }
        )
    items.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return items[:10]


@router.get("/progress")
async def get_study_progress(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    today = datetime.now().date()
    activity_dates: Set = set()
    for t in mock_tests_repo.list_for_user(user_id):
        d = _parse_date(t.get("created_at"))
        if d:
            activity_dates.add(d)
    for p in predictions_repo.list_for_user(user_id):
        d = _parse_date(p.get("created_at"))
        if d:
            activity_dates.add(d)

    daily_progress = []
    for i in range(6, -1, -1):
        check_date = today - timedelta(days=i)
        count = 1 if check_date in activity_dates else 0
        daily_progress.append(
            {"date": check_date.isoformat(), "value": min(100, count * 50), "target": 80}
        )

    weekly_progress = []
    for i in range(4, -1, -1):
        week_start = today - timedelta(days=today.weekday() + i * 7)
        week_end = week_start + timedelta(days=6)
        count = sum(1 for d in activity_dates if week_start <= d <= week_end)
        year, week, _ = week_start.isocalendar()
        weekly_progress.append(
            {"date": f"{year}-W{week:02d}", "value": min(100, count * 15), "target": 75}
        )

    return {"daily": daily_progress, "weekly": weekly_progress, "monthly": []}
