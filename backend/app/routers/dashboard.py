from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..database import get_db
from .. import models
# Use the new Supabase-first auth service
from services.supabase_first_auth import get_current_user_from_token

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)

# Security setup
security = HTTPBearer()

# Dependency for protected routes
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)

@router.get("/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user dashboard statistics"""
    try:
        from datetime import datetime, timezone
        from sqlalchemy import func, desc
        
        # Get user's data
        user = current_user
        user_id = user["id"]
        
        # Get user record from database to access exam_date and days_until_exam
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        
        # Get user's subjects count
        subjects_count = db.query(models.Subject).filter(models.Subject.user_id == user_id).count()
        
        # Get predictions count
        predictions_count = db.query(models.Prediction).filter(models.Prediction.user_id == user_id).count()
        
        # Calculate days to exam from user's exam_date or days_until_exam
        days_to_exam = None
        if db_user:
            if db_user.exam_date:
                # Calculate from exam_date
                now = datetime.now(timezone.utc)
                exam_dt = db_user.exam_date
                if exam_dt.tzinfo is None:
                    exam_dt = exam_dt.replace(tzinfo=timezone.utc)
                delta = exam_dt - now
                days_to_exam = max(0, delta.days)
            elif db_user.days_until_exam:
                # Use the days_until_exam field directly
                days_to_exam = max(0, db_user.days_until_exam)
        
        # Calculate study streak from actual user activity
        # Count consecutive days with activity (chat, tests, uploads, predictions)
        study_streak = 0
        today = datetime.now(timezone.utc).date()
        
        # Get all activity dates from different tables
        activity_dates = set()
        
        # Chat activity
        chat_dates = db.query(func.date(models.ChatHistory.created_at)).filter(
            models.ChatHistory.user_id == user_id
        ).distinct().all()
        activity_dates.update([d[0] for d in chat_dates if d[0]])
        
        # Test activity
        test_dates = db.query(func.date(models.MockTest.created_at)).filter(
            models.MockTest.user_id == user_id
        ).distinct().all()
        activity_dates.update([d[0] for d in test_dates if d[0]])
        
        # Prediction activity
        prediction_dates = db.query(func.date(models.Prediction.created_at)).filter(
            models.Prediction.user_id == user_id
        ).distinct().all()
        activity_dates.update([d[0] for d in prediction_dates if d[0]])
        
        # Calculate consecutive days from today backwards
        if activity_dates:
            from datetime import timedelta
            check_date = today
            while check_date in activity_dates:
                study_streak += 1
                check_date = check_date - timedelta(days=1)
        
        # Calculate completion percentage based on subjects with predictions
        completion_percentage = 0
        if subjects_count > 0:
            subjects_with_predictions = db.query(models.Subject).filter(
                models.Subject.user_id == user_id,
                models.Subject.predictions_generated > 0
            ).count()
            completion_percentage = int((subjects_with_predictions / subjects_count) * 100)
        
        # Get focus area from most recent prediction or subject
        focus_area = "No subjects yet"
        if subjects_count > 0:
            # Try to get from latest prediction
            latest_prediction = db.query(models.Prediction).filter(
                models.Prediction.user_id == user_id
            ).order_by(desc(models.Prediction.created_at)).first()
            
            if latest_prediction and latest_prediction.subject:
                focus_area = latest_prediction.subject.name
            else:
                # Fallback to first subject
                first_subject = db.query(models.Subject).filter(
                    models.Subject.user_id == user_id
                ).first()
                if first_subject:
                    focus_area = first_subject.name
        
        # Get real recent activity from database
        recent_activity = []
        
        # Get recent chats
        recent_chats = db.query(models.ChatHistory).filter(
            models.ChatHistory.user_id == user_id
        ).order_by(desc(models.ChatHistory.created_at)).limit(2).all()
        
        for chat in recent_chats:
            subject_name = chat.subject.name if chat.subject else "Unknown"
            recent_activity.append({
                "action": f"Asked question about {subject_name}",
                "timestamp": chat.created_at.isoformat()
            })
        
        # Get recent predictions
        recent_predictions = db.query(models.Prediction).filter(
            models.Prediction.user_id == user_id
        ).order_by(desc(models.Prediction.created_at)).limit(2).all()
        
        for pred in recent_predictions:
            subject_name = pred.subject.name if pred.subject else "Unknown"
            recent_activity.append({
                "action": f"Generated predictions for {subject_name}",
                "timestamp": pred.created_at.isoformat()
            })
        
        # Get recent tests
        recent_tests = db.query(models.MockTest).filter(
            models.MockTest.user_id == user_id
        ).order_by(desc(models.MockTest.created_at)).limit(2).all()
        
        for test in recent_tests:
            subject_name = test.subject.name if test.subject else "Unknown"
            status = "Completed" if test.is_completed else "Started"
            recent_activity.append({
                "action": f"{status} mock test for {subject_name}",
                "timestamp": test.created_at.isoformat()
            })
        
        # Sort by timestamp and limit to 5 most recent
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity = recent_activity[:5]
        
        return {
            "subjects_count": subjects_count,
            "predictions_count": predictions_count,
            "completion_percentage": completion_percentage,
            "focus_area": focus_area,
            "study_streak": study_streak,
            "days_to_exam": days_to_exam,
            "recent_activity": recent_activity
        }
    except Exception as e:
        import traceback
        error_msg = f"Dashboard stats error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        try:
            with open("dashboard_error.log", "a") as f:
                from datetime import datetime
                f.write(f"\n--- Error at {datetime.now()} ---\n")
                f.write(error_msg)
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

@router.get("/recent-activity")
async def get_recent_activity(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's recent activity"""
    try:
        from sqlalchemy import desc
        
        # Get user's data
        user = current_user
        user_id = user["id"]
        
        recent_activity = []
        
        # Get recent subjects created
        recent_subjects = db.query(models.Subject).filter(
            models.Subject.user_id == user_id
        ).order_by(desc(models.Subject.created_at)).limit(3).all()
        
        for subject in recent_subjects:
            recent_activity.append({
                "id": str(subject.id),
                "type": "study",
                "title": f"Started {subject.name} preparation",
                "description": f"Added subject: {subject.name}",
                "timestamp": subject.created_at.isoformat()
            })
        
        # Get recent predictions
        recent_predictions = db.query(models.Prediction).filter(
            models.Prediction.user_id == user_id
        ).order_by(desc(models.Prediction.created_at)).limit(3).all()
        
        for pred in recent_predictions:
            subject_name = pred.subject.name if pred.subject else "Unknown"
            question_count = pred.total_questions or 0
            recent_activity.append({
                "id": str(pred.id),
                "type": "prediction",
                "title": f"Generated {subject_name} predictions",
                "description": f"Created {question_count} question predictions",
                "timestamp": pred.created_at.isoformat()
            })
        
        # Get recent tests
        recent_tests = db.query(models.MockTest).filter(
            models.MockTest.user_id == user_id
        ).order_by(desc(models.MockTest.created_at)).limit(3).all()
        
        for test in recent_tests:
            subject_name = test.subject.name if test.subject else "Unknown"
            if test.is_completed and test.percentage:
                recent_activity.append({
                    "id": str(test.id),
                    "type": "test",
                    "title": "Completed Mock Test",
                    "description": f"Scored {test.percentage}% in {subject_name}",
                    "timestamp": test.created_at.isoformat()
                })
            else:
                recent_activity.append({
                    "id": str(test.id),
                    "type": "test",
                    "title": "Started Mock Test",
                    "description": f"Mock test for {subject_name}",
                    "timestamp": test.created_at.isoformat()
                })
        
        # Get recent paper uploads
        recent_papers = db.query(models.QuestionPaper).join(
            models.Subject
        ).filter(
            models.Subject.user_id == user_id
        ).order_by(desc(models.QuestionPaper.created_at)).limit(3).all()
        
        for paper in recent_papers:
            subject_name = paper.subject.name if paper.subject else "Unknown"
            recent_activity.append({
                "id": str(paper.id),
                "type": "upload",
                "title": "Uploaded Question Paper",
                "description": f"Added {paper.exam_year or 'recent'} paper for {subject_name}",
                "timestamp": paper.created_at.isoformat()
            })
        
        # Sort by timestamp and return most recent 10
        recent_activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return recent_activity[:10]
        
    except Exception as e:
        import traceback
        print(f"Dashboard recent activity error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching recent activity: {str(e)}")

@router.get("/progress")
async def get_study_progress(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's study progress data"""
    try:
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import func
        
        # Get user's data
        user = current_user
        user_id = user["id"]
        
        # Calculate daily progress for last 7 days
        daily_progress = []
        today = datetime.now(timezone.utc).date()
        
        for i in range(6, -1, -1):  # Last 7 days
            check_date = today - timedelta(days=i)
            
            # Count activities on this date
            activity_count = 0
            
            # Chat activity
            chat_count = db.query(models.ChatHistory).filter(
                models.ChatHistory.user_id == user_id,
                func.date(models.ChatHistory.created_at) == check_date
            ).count()
            activity_count += chat_count
            
            # Test activity
            test_count = db.query(models.MockTest).filter(
                models.MockTest.user_id == user_id,
                func.date(models.MockTest.created_at) == check_date
            ).count()
            activity_count += test_count
            
            # Prediction activity
            pred_count = db.query(models.Prediction).filter(
                models.Prediction.user_id == user_id,
                func.date(models.Prediction.created_at) == check_date
            ).count()
            activity_count += pred_count
            
            # Convert to percentage (cap at 100)
            value = min(100, activity_count * 20)  # Each activity = 20%
            
            daily_progress.append({
                "date": check_date.isoformat(),
                "value": value,
                "target": 80
            })
        
        # Calculate weekly progress (last 5 weeks)
        weekly_progress = []
        for i in range(4, -1, -1):
            week_start = today - timedelta(days=today.weekday() + (i * 7))
            week_end = week_start + timedelta(days=6)
            
            # Count activities in this week
            activity_count = 0
            
            activity_count += db.query(models.ChatHistory).filter(
                models.ChatHistory.user_id == user_id,
                func.date(models.ChatHistory.created_at) >= week_start,
                func.date(models.ChatHistory.created_at) <= week_end
            ).count()
            
            activity_count += db.query(models.MockTest).filter(
                models.MockTest.user_id == user_id,
                func.date(models.MockTest.created_at) >= week_start,
                func.date(models.MockTest.created_at) <= week_end
            ).count()
            
            activity_count += db.query(models.Prediction).filter(
                models.Prediction.user_id == user_id,
                func.date(models.Prediction.created_at) >= week_start,
                func.date(models.Prediction.created_at) <= week_end
            ).count()
            
            value = min(100, activity_count * 10)  # Each activity = 10%
            
            # Format as ISO week
            year, week, _ = week_start.isocalendar()
            weekly_progress.append({
                "date": f"{year}-W{week:02d}",
                "value": value,
                "target": 75
            })
        
        # Calculate monthly progress (last 4 months)
        monthly_progress = []
        for i in range(3, -1, -1):
            # Calculate month
            month_date = today.replace(day=1) - timedelta(days=i*30)
            month_start = month_date.replace(day=1)
            
            # Get next month start
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
            
            # Count activities in this month
            activity_count = 0
            
            activity_count += db.query(models.ChatHistory).filter(
                models.ChatHistory.user_id == user_id,
                func.date(models.ChatHistory.created_at) >= month_start,
                func.date(models.ChatHistory.created_at) <= month_end
            ).count()
            
            activity_count += db.query(models.MockTest).filter(
                models.MockTest.user_id == user_id,
                func.date(models.MockTest.created_at) >= month_start,
                func.date(models.MockTest.created_at) <= month_end
            ).count()
            
            activity_count += db.query(models.Prediction).filter(
                models.Prediction.user_id == user_id,
                func.date(models.Prediction.created_at) >= month_start,
                func.date(models.Prediction.created_at) <= month_end
            ).count()
            
            value = min(100, activity_count * 5)  # Each activity = 5%
            
            monthly_progress.append({
                "date": month_start.strftime("%Y-%m"),
                "value": value,
                "target": 70
            })
        
        return {
            "daily": daily_progress,
            "weekly": weekly_progress,
            "monthly": monthly_progress
        }
    except Exception as e:
        import traceback
        print(f"Dashboard progress error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching study progress: {str(e)}")