from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from .. import models, schemas
from ..routers.auth import get_current_user
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