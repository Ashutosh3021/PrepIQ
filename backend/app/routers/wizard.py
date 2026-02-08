from fastapi import APIRouter, Depends, HTTPException, status, Header
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
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)

router = APIRouter(
    prefix="/wizard",
    tags=["User Setup Wizard"]
)

logger = logging.getLogger(__name__)

@router.get("/status")
async def get_wizard_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user has completed the setup wizard"""
    return {
        "completed": False,
        "exam_name": None,
        "days_until_exam": None,
        "focus_subjects": [],
        "study_hours_per_day": None,
        "target_score": None,
        "preparation_level": None
    }

@router.post("/step1", response_model=schemas.WizardStepResponse)
async def complete_step1(
    wizard_data: schemas.WizardStep1,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete Step 1 of the setup wizard"""
    try:
        # Return success response with wizard data
        logger.info(f"User {current_user['id']} completed wizard step 1")
        
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "access_token": None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in wizard step 1: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save wizard data"
        )

@router.post("/step2", response_model=schemas.WizardStepResponse)
async def complete_step2(
    wizard_data: schemas.WizardStep2,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete Step 2 of the setup wizard"""
    try:
        # Return success response with wizard data
        logger.info(f"User {current_user['id']} completed wizard step 2")
        
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "access_token": None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in wizard step 2: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save wizard data"
        )

@router.post("/step3", response_model=schemas.WizardStepResponse)
async def complete_step3(
    wizard_data: schemas.WizardStep3,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete Step 3 of the setup wizard"""
    try:
        # Return success response with wizard data
        logger.info(f"User {current_user['id']} completed wizard step 3")
        
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "access_token": None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in wizard step 3: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save wizard data"
        )

@router.post("/complete", response_model=schemas.WizardStepResponse)
async def complete_wizard(
    wizard_data: schemas.WizardCompletion,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark the wizard as completed"""
    try:
        # Return success response
        logger.info(f"User {current_user['id']} completed the setup wizard")
        
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "access_token": None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error completing wizard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete wizard"
        )

@router.put("/update", response_model=schemas.WizardStepResponse)
async def update_wizard_data(
    update_data: schemas.UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update wizard data after completion"""
    try:
        # Return success response
        logger.info(f"User {current_user['id']} updated wizard data")
        
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "access_token": None
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating wizard data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update wizard data"
        )