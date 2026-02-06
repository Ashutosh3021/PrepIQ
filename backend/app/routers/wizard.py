from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

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

router = APIRouter(
    prefix="/wizard",
    tags=["User Setup Wizard"]
)

logger = logging.getLogger(__name__)

@router.get("/status")
def get_wizard_status(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user has completed the setup wizard"""
    return {
        "completed": current_user.wizard_completed,
        "exam_name": current_user.exam_name,
        "days_until_exam": current_user.days_until_exam,
        "focus_subjects": current_user.focus_subjects,
        "study_hours_per_day": current_user.study_hours_per_day,
        "target_score": current_user.target_score,
        "preparation_level": current_user.preparation_level
    }

@router.post("/step1", response_model=schemas.UserResponse)
def complete_step1(
    wizard_data: schemas.WizardStep1,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete Step 1 of the setup wizard"""
    try:
        # Update user with step 1 data
        current_user.exam_name = wizard_data.exam_name
        current_user.days_until_exam = wizard_data.days_until_exam
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User {current_user.id} completed wizard step 1")
        
        return current_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in wizard step 1: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save wizard data"
        )

@router.post("/step2", response_model=schemas.UserResponse)
def complete_step2(
    wizard_data: schemas.WizardStep2,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete Step 2 of the setup wizard"""
    try:
        # Update user with step 2 data
        current_user.focus_subjects = wizard_data.focus_subjects
        current_user.study_hours_per_day = wizard_data.study_hours_per_day
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User {current_user.id} completed wizard step 2")
        
        return current_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in wizard step 2: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save wizard data"
        )

@router.post("/step3", response_model=schemas.UserResponse)
def complete_step3(
    wizard_data: schemas.WizardStep3,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete Step 3 of the setup wizard"""
    try:
        # Update user with step 3 data
        current_user.target_score = wizard_data.target_score
        current_user.preparation_level = wizard_data.preparation_level
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User {current_user.id} completed wizard step 3")
        
        return current_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in wizard step 3: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save wizard data"
        )

@router.post("/complete", response_model=schemas.UserResponse)
def complete_wizard(
    wizard_data: schemas.WizardCompletion,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark the wizard as completed"""
    try:
        # Mark wizard as completed
        current_user.wizard_completed = wizard_data.wizard_completed
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User {current_user.id} completed the setup wizard")
        
        return current_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing wizard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete wizard"
        )

@router.put("/update", response_model=schemas.UserResponse)
def update_wizard_data(
    update_data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update wizard data after completion"""
    try:
        # Update user fields if provided
        if update_data.exam_name is not None:
            current_user.exam_name = update_data.exam_name
        if update_data.days_until_exam is not None:
            current_user.days_until_exam = update_data.days_until_exam
        if update_data.focus_subjects is not None:
            current_user.focus_subjects = update_data.focus_subjects
        if update_data.study_hours_per_day is not None:
            current_user.study_hours_per_day = update_data.study_hours_per_day
        if update_data.target_score is not None:
            current_user.target_score = update_data.target_score
        if update_data.preparation_level is not None:
            current_user.preparation_level = update_data.preparation_level
            
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"User {current_user.id} updated wizard data")
        
        return current_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating wizard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update wizard data"
        )