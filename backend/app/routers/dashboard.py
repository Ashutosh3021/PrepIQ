"""Dashboard stats — Pyronites data plane (Fix Phase D)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Set

from fastapi import APIRouter, Depends, Header, HTTPException

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

        predictions_count = 0
        for s in subjects:
            predictions_count += len(
                predictions_repo.list_for_user_subject(user_id, str(s.get("id")))
            )

        profile = users_repo.get(user_id) or {}
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
        for s in subjects:
            for p in predictions_repo.list_for_user_subject(user_id, str(s.get("id"))):
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
            with_pred = 0
            for s in subjects:
                if predictions_repo.list_for_user_subject(user_id, str(s.get("id"))):
                    with_pred += 1
            completion_percentage = int((with_pred / subjects_count) * 100)

        focus_area = "No subjects yet"
        if subjects:
            focus_area = str(subjects[0].get("name") or "Subject")
            # prefer latest prediction subject
            latest_name = None
            latest_ts = ""
            for s in subjects:
                for p in predictions_repo.list_for_user_subject(user_id, str(s.get("id"))):
                    ts = str(p.get("created_at") or "")
                    if ts >= latest_ts:
                        latest_ts = ts
                        latest_name = s.get("name")
            if latest_name:
                focus_area = str(latest_name)

        recent_activity: List[Dict[str, Any]] = []
        for s in subjects:
            sid = str(s.get("id"))
            sname = s.get("name") or "Subject"
            for p in predictions_repo.list_for_user_subject(user_id, sid):
                recent_activity.append(
                    {
                        "action": f"Generated predictions for {sname}",
                        "timestamp": str(p.get("created_at") or ""),
                    }
                )
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")


@router.get("/recent-activity")
async def get_recent_activity(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    items: List[Dict[str, Any]] = []
    for s in subjects_repo.list_for_user(user_id):
        items.append(
            {
                "id": str(s.get("id")),
                "type": "study",
                "title": f"Started {s.get('name')} preparation",
                "description": f"Added subject: {s.get('name')}",
                "timestamp": str(s.get("created_at") or ""),
            }
        )
        for p in predictions_repo.list_for_user_subject(user_id, str(s.get("id"))):
            items.append(
                {
                    "id": str(p.get("id")),
                    "type": "prediction",
                    "title": f"Generated {s.get('name')} predictions",
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
    for s in subjects_repo.list_for_user(user_id):
        for p in predictions_repo.list_for_user_subject(user_id, str(s.get("id"))):
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
