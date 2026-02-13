from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from ..database import get_db
from .. import models, schemas
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import from the new Supabase-first auth service
from services.supabase_first_auth import get_current_user_from_token

router = APIRouter(
    prefix="/wizard",
    tags=["User Setup Wizard"]
)

logger = logging.getLogger(__name__)

# Dependency for protected routes with lazy user creation
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user with lazy creation in application database.
    This ensures the user always exists in the local DB when accessed.
    """
    return await get_current_user_from_token(authorization, db)

@router.get("/status")
async def get_wizard_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get wizard completion status and user data.
    User is guaranteed to exist (auto-created by get_current_user dependency).
    """
    try:
        # Calculate days until exam if exam_date is set
        days_until_exam = current_user.get("days_until_exam")
        exam_date = current_user.get("exam_date")
        
        if exam_date and not days_until_exam:
            from datetime import timezone
            now = datetime.now(timezone.utc)
            exam_dt = exam_date
            if exam_dt.tzinfo is None:
                exam_dt = exam_dt.replace(tzinfo=timezone.utc)
            delta = exam_dt - now
            days_until_exam = max(0, delta.days)
        
        return {
            "completed": current_user.get("wizard_completed", False),
            "exam_name": current_user.get("exam_name"),
            "days_until_exam": days_until_exam,
            "focus_subjects": current_user.get("focus_subjects", []),
            "study_hours_per_day": current_user.get("study_hours_per_day"),
            "target_score": current_user.get("target_score"),
            "preparation_level": current_user.get("preparation_level")
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions (401, 403, etc.) as-is
        raise
    except Exception as e:
        # Only unexpected errors become 500
        logger.error(f"Unexpected error in get_wizard_status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching wizard status"
        )

@router.post("/step1", response_model=schemas.WizardStepResponse)
async def complete_step1(
    wizard_data: schemas.WizardStep1,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete Step 1 of the setup wizard - Save exam name and days until exam"""
    try:
        # Get user from database (guaranteed to exist due to lazy creation)
        db_user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
        
        if not db_user:
            # This shouldn't happen with lazy creation, but handle gracefully
            logger.error(f"User {current_user['id']} not found in database after lazy creation")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please try logging in again."
            )
        
        # Validate input
        if not wizard_data.exam_name or len(wizard_data.exam_name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Exam name is required"
            )
        
        if not wizard_data.days_until_exam or wizard_data.days_until_exam < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Days until exam must be at least 1"
            )
        
        if wizard_data.days_until_exam > 365:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Days until exam cannot exceed 365"
            )
        
        # Update user with step 1 data
        db_user.exam_name = wizard_data.exam_name.strip()
        db_user.days_until_exam = wizard_data.days_until_exam
        
        # Calculate exam date from days_until_exam
        from datetime import timezone
        exam_date = datetime.now(timezone.utc) + timedelta(days=wizard_data.days_until_exam)
        db_user.exam_date = exam_date
        
        # Commit changes
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User {current_user['id']} completed wizard step 1 - Exam: {wizard_data.exam_name}, Days: {wizard_data.days_until_exam}")
        
        return {
            "id": str(current_user["id"]),
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "access_token": None
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        db.rollback() if 'db' in locals() else None
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in wizard step 1: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save wizard data. Please try again."
        )

@router.post("/step2", response_model=schemas.WizardStepResponse)
async def complete_step2(
    wizard_data: schemas.WizardStep2,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete Step 2 of the setup wizard - Save focus subjects and study hours"""
    try:
        # Get user from database
        db_user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please try logging in again."
            )
        
        # Validate input
        if not wizard_data.focus_subjects or len(wizard_data.focus_subjects) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="At least one subject must be selected"
            )
        
        if len(wizard_data.focus_subjects) > 10:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot select more than 10 subjects"
            )
        
        if not wizard_data.study_hours_per_day or wizard_data.study_hours_per_day < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Study hours per day must be at least 1"
            )
        
        if wizard_data.study_hours_per_day > 12:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Study hours per day cannot exceed 12"
            )
        
        # Update user with step 2 data
        db_user.focus_subjects = wizard_data.focus_subjects
        db_user.study_hours_per_day = wizard_data.study_hours_per_day
        
        # Automatically create subjects from focus_subjects
        created_subjects = []
        for subject_name in wizard_data.focus_subjects:
            # Check if subject already exists for this user
            existing_subject = db.query(models.Subject).filter(
                models.Subject.user_id == current_user["id"],
                models.Subject.name.ilike(subject_name)
            ).first()
            
            if not existing_subject:
                # Create new subject
                new_subject = models.Subject(
                    user_id=current_user["id"],
                    name=subject_name,
                    code=f"SUB-{subject_name[:3].upper()}-{datetime.now().strftime('%Y')}",
                    semester=1,
                    academic_year=str(datetime.now().year)
                )
                db.add(new_subject)
                created_subjects.append(subject_name)
        
        # Commit changes
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User {current_user['id']} completed wizard step 2 - Subjects: {len(wizard_data.focus_subjects)}, Hours: {wizard_data.study_hours_per_day}, Created: {len(created_subjects)} new subjects")
        
        return {
            "id": str(current_user["id"]),
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "access_token": None
        }
        
    except HTTPException:
        db.rollback() if 'db' in locals() else None
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in wizard step 2: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save wizard data. Please try again."
        )

@router.post("/step3", response_model=schemas.WizardStepResponse)
async def complete_step3(
    wizard_data: schemas.WizardStep3,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete Step 3 of the setup wizard - Save target score and preparation level"""
    try:
        # Get user from database
        db_user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please try logging in again."
            )
        
        # Validate input
        if not wizard_data.target_score or wizard_data.target_score < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Target score must be at least 1%"
            )
        
        if wizard_data.target_score > 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Target score cannot exceed 100%"
            )
        
        valid_levels = ["beginner", "intermediate", "advanced"]
        if not wizard_data.preparation_level or wizard_data.preparation_level not in valid_levels:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Preparation level must be one of: {', '.join(valid_levels)}"
            )
        
        # Update user with step 3 data
        db_user.target_score = wizard_data.target_score
        db_user.preparation_level = wizard_data.preparation_level
        
        # Commit changes
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User {current_user['id']} completed wizard step 3 - Target: {wizard_data.target_score}%, Level: {wizard_data.preparation_level}")
        
        return {
            "id": str(current_user["id"]),
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "access_token": None
        }
        
    except HTTPException:
        db.rollback() if 'db' in locals() else None
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in wizard step 3: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save wizard data. Please try again."
        )

@router.post("/complete", response_model=schemas.WizardStepResponse)
async def complete_wizard(
    wizard_data: schemas.WizardCompletion,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark the wizard as completed"""
    try:
        # Get user from database
        db_user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please try logging in again."
            )
        
        # Validate that required wizard data exists before completing
        missing_fields = []
        if not db_user.exam_name:
            missing_fields.append("exam_name")
        if not db_user.days_until_exam:
            missing_fields.append("days_until_exam")
        if not db_user.focus_subjects or len(db_user.focus_subjects) == 0:
            missing_fields.append("focus_subjects")
        if not db_user.study_hours_per_day:
            missing_fields.append("study_hours_per_day")
        if not db_user.target_score:
            missing_fields.append("target_score")
        if not db_user.preparation_level:
            missing_fields.append("preparation_level")
        
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot complete wizard. Missing required data: {', '.join(missing_fields)}. Please complete all steps."
            )
        
        # Mark wizard as completed
        db_user.wizard_completed = True
        
        # Commit changes
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User {current_user['id']} successfully completed the setup wizard")
        
        return {
            "id": str(current_user["id"]),
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "access_token": None
        }
        
    except HTTPException:
        db.rollback() if 'db' in locals() else None
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing wizard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete wizard. Please try again."
        )

@router.put("/update", response_model=schemas.WizardStepResponse)
async def update_wizard_data(
    update_data: schemas.UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update wizard data after completion"""
    try:
        # Get user from database
        db_user = db.query(models.User).filter(models.User.id == current_user["id"]).first()
        
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please try logging in again."
            )
        
        # Update allowed fields if provided
        if hasattr(update_data, 'exam_name') and update_data.exam_name:
            db_user.exam_name = update_data.exam_name.strip()
        
        if hasattr(update_data, 'days_until_exam') and update_data.days_until_exam:
            if update_data.days_until_exam < 1 or update_data.days_until_exam > 365:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Days until exam must be between 1 and 365"
                )
            db_user.days_until_exam = update_data.days_until_exam
            # Recalculate exam date
            from datetime import timezone
            exam_date = datetime.now(timezone.utc) + timedelta(days=update_data.days_until_exam)
            db_user.exam_date = exam_date
        
        if hasattr(update_data, 'focus_subjects') and update_data.focus_subjects:
            if len(update_data.focus_subjects) > 10:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot select more than 10 subjects"
                )
            db_user.focus_subjects = update_data.focus_subjects
        
        if hasattr(update_data, 'study_hours_per_day') and update_data.study_hours_per_day:
            if update_data.study_hours_per_day < 1 or update_data.study_hours_per_day > 12:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Study hours must be between 1 and 12"
                )
            db_user.study_hours_per_day = update_data.study_hours_per_day
        
        if hasattr(update_data, 'target_score') and update_data.target_score:
            if update_data.target_score < 1 or update_data.target_score > 100:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Target score must be between 1 and 100"
                )
            db_user.target_score = update_data.target_score
        
        if hasattr(update_data, 'preparation_level') and update_data.preparation_level:
            valid_levels = ["beginner", "intermediate", "advanced"]
            if update_data.preparation_level not in valid_levels:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Preparation level must be one of: {', '.join(valid_levels)}"
                )
            db_user.preparation_level = update_data.preparation_level
        
        # Commit changes
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"User {current_user['id']} updated wizard data")
        
        return {
            "id": str(current_user["id"]),
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "access_token": None
        }
        
    except HTTPException:
        db.rollback() if 'db' in locals() else None
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating wizard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update wizard data. Please try again."
        )
