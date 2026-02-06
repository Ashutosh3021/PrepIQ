from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, date, timedelta

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
    prefix="/plan",
    tags=["Study Plans"]
)

@router.post("/generate", response_model=schemas.StudyPlanResponse)
def generate_study_plan(
    plan_request: schemas.StudyPlanRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.generate_study_plan(
            db=db,
            user_id=current_user.id,
            subject_id=plan_request.subject_id,
            start_date=plan_request.start_date,
            exam_date=plan_request.exam_date
        )
        
        # Format the response to match the schema
        return {
            "plan_id": result["plan_id"],
            "subject_id": result["subject_id"],
            "total_days": result["total_days"],
            "daily_schedule": [
                schemas.StudyPlanDay(
                    day=item["day"],
                    date=item["date"],
                    topics=item["topics"],
                    recommended_hours=item["recommended_hours"],
                    priority_topics=item["priority_topics"]
                ) for item in result["daily_schedule"]
            ]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=schemas.StudyPlanResponse)
def get_current_study_plan(
    user_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this study plan"
        )
    
    service = PrepIQService()
    try:
        result = service.get_user_study_plan(
            db=db,
            user_id=user_id
        )
        
        return {
            "plan_id": result["plan_id"],
            "subject_id": result["subject_id"],
            "total_days": result["total_days"],
            "daily_schedule": [
                schemas.StudyPlanDay(
                    day=item["day"],
                    date=item["date"],
                    topics=item["topics"],
                    recommended_hours=item["recommended_hours"],
                    priority_topics=item["priority_topics"]
                ) for item in result["daily_schedule"]
            ]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{plan_id}", response_model=schemas.StudyPlanUpdateResponse)
def update_study_plan(
    plan_id: str,
    plan_update: schemas.StudyPlanUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.update_study_plan_progress(
            db=db,
            plan_id=plan_id,
            user_id=current_user.id,
            days_completed=plan_update.days_completed,
            on_track=plan_update.on_track
        )
        
        # Get the updated plan details
        updated_plan = service.get_user_study_plan(db=db, user_id=current_user.id)
        
        return {
            "message": result["message"],
            "plan": {
                "plan_id": updated_plan["plan_id"],
                "subject_id": updated_plan["subject_id"],
                "total_days": updated_plan["total_days"],
                "daily_schedule": [
                    schemas.StudyPlanDay(
                        day=item["day"],
                        date=item["date"],
                        topics=item["topics"],
                        recommended_hours=item["recommended_hours"],
                        priority_topics=item["priority_topics"]
                    ) for item in updated_plan["daily_schedule"]
                ],
                "days_completed": updated_plan["days_completed"],
                "completion_percentage": updated_plan["completion_percentage"],
                "on_track": updated_plan["on_track"]
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )