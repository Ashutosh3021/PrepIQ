from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List
import logging
from datetime import datetime, timedelta, timezone, date as date_type

from ..database import get_db
from .. import models
from ..services.supabase_first_auth import get_current_user_from_token

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)


@router.get("/stats")
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user dashboard statistics"""
    try:
        user_id = current_user["id"]

        db_user = db.query(models.User).filter(models.User.id == user_id).first()

        subjects_count = db.query(models.Subject).filter(
            models.Subject.user_id == user_id
        ).count()

        predictions_count = db.query(models.Prediction).filter(
            models.Prediction.user_id == user_id
        ).count()

        # Days to exam
        days_to_exam = None
        if db_user:
            if db_user.exam_date:
                now = datetime.now(timezone.utc)
                exam_dt = db_user.exam_date
                if exam_dt.tzinfo is None:
                    exam_dt = exam_dt.replace(tzinfo=timezone.utc)
                days_to_exam = max(0, (exam_dt - now).days)
            elif db_user.days_until_exam:
                days_to_exam = max(0, db_user.days_until_exam)

        # M-08: use server local date so streak is not off-by-one for non-UTC users
        today = datetime.now().date()

        # Collect distinct activity dates (simple separate queries — no fragile union_all)
        activity_dates: set = set()

        for (d,) in db.query(func.date(models.ChatHistory.created_at)).filter(
            models.ChatHistory.user_id == user_id
        ).distinct():
            if d:
                activity_dates.add(d)

        for (d,) in db.query(func.date(models.MockTest.created_at)).filter(
            models.MockTest.user_id == user_id
        ).distinct():
            if d:
                activity_dates.add(d)

        for (d,) in db.query(func.date(models.Prediction.created_at)).filter(
            models.Prediction.user_id == user_id
        ).distinct():
            if d:
                activity_dates.add(d)

        # Consecutive-day streak
        study_streak = 0
        check = today
        while check in activity_dates:
            study_streak += 1
            check -= timedelta(days=1)

        # Completion percentage
        completion_percentage = 0
        if subjects_count > 0:
            subjects_with_predictions = db.query(models.Subject).filter(
                models.Subject.user_id == user_id,
                models.Subject.predictions_generated > 0,
            ).count()
            completion_percentage = int((subjects_with_predictions / subjects_count) * 100)

        # Focus area — H-12: eager-load subject to avoid lazy load
        focus_area = "No subjects yet"
        if subjects_count > 0:
            latest_prediction = (
                db.query(models.Prediction)
                .options(joinedload(models.Prediction.subject))
                .filter(models.Prediction.user_id == user_id)
                .order_by(desc(models.Prediction.created_at))
                .first()
            )
            if latest_prediction and latest_prediction.subject:
                focus_area = latest_prediction.subject.name
            else:
                first_subject = db.query(models.Subject).filter(
                    models.Subject.user_id == user_id
                ).first()
                if first_subject:
                    focus_area = first_subject.name

        # Recent activity — H-12: eager-load subject relationships
        recent_activity = []

        recent_chats = (
            db.query(models.ChatHistory)
            .options(joinedload(models.ChatHistory.subject))
            .filter(models.ChatHistory.user_id == user_id)
            .order_by(desc(models.ChatHistory.created_at))
            .limit(2)
            .all()
        )
        for chat in recent_chats:
            subject_name = chat.subject.name if chat.subject else "Unknown"
            recent_activity.append({
                "action": f"Asked question about {subject_name}",
                "timestamp": chat.created_at.isoformat(),
            })

        recent_predictions = (
            db.query(models.Prediction)
            .options(joinedload(models.Prediction.subject))
            .filter(models.Prediction.user_id == user_id)
            .order_by(desc(models.Prediction.created_at))
            .limit(2)
            .all()
        )
        for pred in recent_predictions:
            subject_name = pred.subject.name if pred.subject else "Unknown"
            recent_activity.append({
                "action": f"Generated predictions for {subject_name}",
                "timestamp": pred.created_at.isoformat(),
            })

        recent_tests = (
            db.query(models.MockTest)
            .options(joinedload(models.MockTest.subject))
            .filter(models.MockTest.user_id == user_id)
            .order_by(desc(models.MockTest.created_at))
            .limit(2)
            .all()
        )
        for test in recent_tests:
            subject_name = test.subject.name if test.subject else "Unknown"
            status_label = "Completed" if test.is_completed else "Started"
            recent_activity.append({
                "action": f"{status_label} mock test for {subject_name}",
                "timestamp": test.created_at.isoformat(),
            })

        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = recent_activity[:5]

        return {
            "subjects_count": subjects_count,
            "predictions_count": predictions_count,
            "completion_percentage": completion_percentage,
            "focus_area": focus_area,
            "study_streak": study_streak,
            "days_to_exam": days_to_exam,
            "recent_activity": recent_activity,
        }

    except Exception as e:
        import traceback
        logger.error(f"Dashboard stats error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")


@router.get("/recent-activity")
async def get_recent_activity(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's recent activity"""
    try:
        user_id = current_user["id"]
        recent_activity = []

        for subject in (
            db.query(models.Subject)
            .filter(models.Subject.user_id == user_id)
            .order_by(desc(models.Subject.created_at))
            .limit(3)
        ):
            recent_activity.append({
                "id": str(subject.id),
                "type": "study",
                "title": f"Started {subject.name} preparation",
                "description": f"Added subject: {subject.name}",
                "timestamp": subject.created_at.isoformat(),
            })

        for pred in (
            db.query(models.Prediction)
            .options(joinedload(models.Prediction.subject))
            .filter(models.Prediction.user_id == user_id)
            .order_by(desc(models.Prediction.created_at))
            .limit(3)
        ):
            subject_name = pred.subject.name if pred.subject else "Unknown"
            recent_activity.append({
                "id": str(pred.id),
                "type": "prediction",
                "title": f"Generated {subject_name} predictions",
                "description": f"Created {pred.total_questions or 0} question predictions",
                "timestamp": pred.created_at.isoformat(),
            })

        for test in (
            db.query(models.MockTest)
            .options(joinedload(models.MockTest.subject))
            .filter(models.MockTest.user_id == user_id)
            .order_by(desc(models.MockTest.created_at))
            .limit(3)
        ):
            subject_name = test.subject.name if test.subject else "Unknown"
            if test.is_completed and test.percentage:
                recent_activity.append({
                    "id": str(test.id),
                    "type": "test",
                    "title": "Completed Mock Test",
                    "description": f"Scored {test.percentage}% in {subject_name}",
                    "timestamp": test.created_at.isoformat(),
                })
            else:
                recent_activity.append({
                    "id": str(test.id),
                    "type": "test",
                    "title": "Started Mock Test",
                    "description": f"Mock test for {subject_name}",
                    "timestamp": test.created_at.isoformat(),
                })

        for paper in (
            db.query(models.QuestionPaper)
            .options(joinedload(models.QuestionPaper.subject))
            .join(models.Subject)
            .filter(models.Subject.user_id == user_id)
            .order_by(desc(models.QuestionPaper.created_at))
            .limit(3)
        ):
            subject_name = paper.subject.name if paper.subject else "Unknown"
            recent_activity.append({
                "id": str(paper.id),
                "type": "upload",
                "title": "Uploaded Question Paper",
                "description": f"Added {paper.exam_year or 'recent'} paper for {subject_name}",
                "timestamp": paper.created_at.isoformat(),
            })

        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return recent_activity[:10]

    except Exception as e:
        import traceback
        logger.error(f"Dashboard recent activity error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching recent activity: {str(e)}")


@router.get("/progress")
async def get_study_progress(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's study progress data.

    H-11: The original union_all approach produced ambiguous column names and
    could fail on some SQLAlchemy/PostgreSQL versions.  Replaced with three
    simple queries that collect activity dates into a Python set — same result,
    no fragile SQL column aliasing.
    """
    try:
        user_id = current_user["id"]
        today = datetime.now().date()  # M-08: local date
        start_date = today - timedelta(days=30)

        # Collect all activity dates in the last 30 days
        activity_dates: set = set()

        for (d,) in db.query(func.date(models.ChatHistory.created_at)).filter(
            models.ChatHistory.user_id == user_id,
            func.date(models.ChatHistory.created_at) >= start_date,
        ).distinct():
            if d:
                activity_dates.add(d)

        for (d,) in db.query(func.date(models.MockTest.created_at)).filter(
            models.MockTest.user_id == user_id,
            func.date(models.MockTest.created_at) >= start_date,
        ).distinct():
            if d:
                activity_dates.add(d)

        for (d,) in db.query(func.date(models.Prediction.created_at)).filter(
            models.Prediction.user_id == user_id,
            func.date(models.Prediction.created_at) >= start_date,
        ).distinct():
            if d:
                activity_dates.add(d)

        # Daily progress (last 7 days)
        daily_progress = []
        for i in range(6, -1, -1):
            check_date = today - timedelta(days=i)
            # Count how many of the three tables had activity on this day
            count = sum(1 for d in activity_dates if d == check_date)
            daily_progress.append({
                "date": check_date.isoformat(),
                "value": min(100, count * 33),
                "target": 80,
            })

        # Weekly progress (last 5 weeks)
        weekly_progress = []
        for i in range(4, -1, -1):
            week_start = today - timedelta(days=today.weekday() + i * 7)
            week_end = week_start + timedelta(days=6)
            count = sum(1 for d in activity_dates if week_start <= d <= week_end)
            year, week, _ = week_start.isocalendar()
            weekly_progress.append({
                "date": f"{year}-W{week:02d}",
                "value": min(100, count * 10),
                "target": 75,
            })

        # Monthly progress (last 4 months)
        monthly_progress = []
        for i in range(3, -1, -1):
            month_start = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
            count = sum(1 for d in activity_dates if month_start <= d <= month_end)
            monthly_progress.append({
                "date": month_start.strftime("%Y-%m"),
                "value": min(100, count * 5),
                "target": 70,
            })

        return {
            "daily": daily_progress,
            "weekly": weekly_progress,
            "monthly": monthly_progress,
        }

    except Exception as e:
        import traceback
        logger.error(f"Dashboard progress error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error fetching study progress: {str(e)}")
