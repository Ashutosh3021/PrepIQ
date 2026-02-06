from fastapi import APIRouter, Depends, HTTPException
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
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return await get_current_user_from_token(f"Bearer {credentials.credentials}")

@router.get("/stats")
async def get_dashboard_stats(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get user dashboard statistics"""
    try:
        # Get current user
        user = await SupabaseAuthService.get_current_user(credentials.credentials, db)
        
        # Get user's subjects count
        subjects_count = db.query(models.Subject).filter(models.Subject.user_id == user.id).count()
        
        # Get predictions count
        predictions_count = db.query(models.Prediction).filter(models.Prediction.user_id == user.id).count()
        
        # Mock data for other stats (would be calculated from actual data in production)
        completion_percentage = min(100, subjects_count * 25)  # Simple mock calculation
        focus_area = "Linear Algebra" if subjects_count > 0 else "No subjects yet"
        study_streak = 3  # Mock streak
        days_to_exam = 45  # Mock days
        
        return {
            "subjects_count": subjects_count,
            "predictions_count": predictions_count,
            "completion_percentage": completion_percentage,
            "focus_area": focus_area,
            "study_streak": study_streak,
            "days_to_exam": days_to_exam,
            "recent_activity": [
                {
                    "action": "Started new subject",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "details": "Linear Algebra"
                },
                {
                    "action": "Generated predictions",
                    "timestamp": "2024-01-14T14:15:00Z",
                    "details": "Calculus"
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

@router.get("/recent-activity")
async def get_recent_activity(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get user's recent activity"""
    try:
        # Get current user
        user = await SupabaseAuthService.get_current_user(credentials.credentials, db)
        
        # Mock recent activity data
        recent_activity = [
            {
                "id": "1",
                "type": "study",
                "title": "Started Linear Algebra preparation",
                "description": "Began studying Unit 1: Matrices and Determinants",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "id": "2",
                "type": "prediction",
                "title": "Generated Calculus predictions",
                "description": "Created 25 question predictions with 85% confidence",
                "timestamp": "2024-01-14T14:15:00Z"
            },
            {
                "id": "3",
                "type": "test",
                "title": "Completed Mock Test",
                "description": "Scored 18/25 (72%) in Differential Equations",
                "timestamp": "2024-01-13T16:45:00Z"
            },
            {
                "id": "4",
                "type": "upload",
                "title": "Uploaded Question Paper",
                "description": "Added 2023 Mid-Semester paper for Physics",
                "timestamp": "2024-01-12T09:20:00Z"
            }
        ]
        
        return recent_activity
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent activity: {str(e)}")

@router.get("/progress")
async def get_study_progress(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get user's study progress data"""
    try:
        # Get current user
        user = await SupabaseAuthService.get_current_user(credentials.credentials, db)
        
        # Mock progress data
        daily_progress = [
            {"date": "2024-01-10", "value": 65, "target": 80},
            {"date": "2024-01-11", "value": 70, "target": 80},
            {"date": "2024-01-12", "value": 75, "target": 80},
            {"date": "2024-01-13", "value": 72, "target": 80},
            {"date": "2024-01-14", "value": 78, "target": 80},
            {"date": "2024-01-15", "value": 82, "target": 80}
        ]
        
        weekly_progress = [
            {"date": "2023-W50", "value": 60, "target": 75},
            {"date": "2023-W51", "value": 65, "target": 75},
            {"date": "2023-W52", "value": 70, "target": 75},
            {"date": "2024-W01", "value": 75, "target": 75},
            {"date": "2024-W02", "value": 80, "target": 75}
        ]
        
        monthly_progress = [
            {"date": "2023-10", "value": 55, "target": 70},
            {"date": "2023-11", "value": 60, "target": 70},
            {"date": "2023-12", "value": 68, "target": 70},
            {"date": "2024-01", "value": 75, "target": 70}
        ]
        
        return {
            "daily": daily_progress,
            "weekly": weekly_progress,
            "monthly": monthly_progress
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching study progress: {str(e)}")