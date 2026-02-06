from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from .. import models, schemas
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import from the new Supabase-first auth service
from services.supabase_first_auth import get_current_user_from_token

# Dependency for protected routes
async def get_current_user(authorization: str = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)
from ..services import PrepIQService

router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"]
)

@router.get("/{subject_id}/frequency")
def get_frequency_analysis(
    subject_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.get_frequency_analysis(
            db=db,
            subject_id=subject_id,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/{subject_id}/weightage")
def get_weightage_analysis(
    subject_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.get_weightage_analysis(
            db=db,
            subject_id=subject_id,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/{subject_id}/repetitions")
def get_repetition_analysis(
    subject_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.get_repetition_analysis(
            db=db,
            subject_id=subject_id,
            user_id=current_user.id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/{subject_id}/trends")
def get_trend_analysis(
    subject_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.get_trend_analysis(
            db=db,
            subject_id=subject_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/data")
def get_analysis_data(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        # Get all analysis data for the user
        # Get user's subjects
        subjects = db.query(models.Subject).filter(models.Subject.user_id == current_user.id).all()
        
        if not subjects:
            # Return empty data if no subjects
            return {
                "performanceData": [],
                "subjectPerformance": [],
                "weeklyProgress": []
            }
        
        # Use the first subject for analysis as an example
        # In a real implementation, you'd aggregate across all subjects
        first_subject = subjects[0]
        
        # Get trend analysis for the first subject
        trend_data = service.get_trend_analysis(db=db, subject_id=first_subject.id)
        
        # Get frequency analysis for the first subject
        freq_data = service.get_frequency_analysis(db=db, subject_id=first_subject.id, user_id=current_user.id)
        
        # Get repetition analysis for the first subject
        rep_data = service.get_repetition_analysis(db=db, subject_id=first_subject.id, user_id=current_user.id)
        
        # Format the data for the frontend
        performance_data = []
        if 'trend_data' in trend_data and trend_data['trend_data']:
            # Convert trend data to expected format
            for idx, trend_point in enumerate(trend_data['trend_data']):
                performance_data.append({
                    "name": f"Week {idx + 1}",
                    "score": min(100, max(0, trend_point.get('score', 0))),
                    "target": 80
                })
        
        # Create subject performance data
        subject_performance = []
        for subject in subjects[:4]:  # Limit to first 4 subjects
            subject_performance.append({
                "subject": subject.name,
                "performance": min(100, max(0, len([s for s in subjects if s.name == subject.name]) * 25)),
                "color": "#3b82f6"  # Blue
            })
        
        # Create weekly progress data
        weekly_progress = []
        for i in range(1, 7):
            weekly_progress.append({
                "week": f"Week {i}",
                "progress": min(100, 60 + (i * 5))  # Increasing trend
            })
        
        return {
            "performanceData": performance_data,
            "subjectPerformance": subject_performance,
            "weeklyProgress": weekly_progress
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )