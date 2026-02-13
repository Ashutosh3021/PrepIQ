from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ..database import get_db
from .. import models, schemas
# Import from the new Supabase-first auth service
from services.supabase_first_auth import get_current_user_from_token

router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"]
)

# Dependency for protected routes
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)

@router.get("", response_model=List[schemas.SubjectResponse])
async def get_subjects(
    skip: int = 0, 
    limit: int = 100, 
    semester: int = None,
    year: str = None,
    search: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all subjects for the current user with counts (optimized query)"""
    try:
        # Use subqueries to count papers and predictions in a single query
        papers_count = (
            db.query(
                models.QuestionPaper.subject_id,
                func.count(models.QuestionPaper.id).label("count")
            )
            .group_by(models.QuestionPaper.subject_id)
            .subquery()
        )
        
        predictions_count = (
            db.query(
                models.Prediction.subject_id,
                func.count(models.Prediction.id).label("count")
            )
            .group_by(models.Prediction.subject_id)
            .subquery()
        )
        
        # Main query with joined counts
        query = (
            db.query(
                models.Subject,
                func.coalesce(papers_count.c.count, 0).label("papers_count"),
                func.coalesce(predictions_count.c.count, 0).label("predictions_count")
            )
            .outerjoin(papers_count, models.Subject.id == papers_count.c.subject_id)
            .outerjoin(predictions_count, models.Subject.id == predictions_count.c.subject_id)
            .filter(models.Subject.user_id == current_user["id"])
        )
        
        # Apply filters
        if semester:
            query = query.filter(models.Subject.semester == semester)
        if year:
            query = query.filter(models.Subject.academic_year == year)
        if search:
            query = query.filter(models.Subject.name.ilike(f"%{search}%"))
        
        # Execute query
        results = query.offset(skip).limit(limit).all()
        
        # Convert results to response model
        subjects = []
        for subject, papers_count_val, predictions_count_val in results:
            subject.papers_uploaded = papers_count_val
            subject.predictions_generated = predictions_count_val
            subjects.append(subject)
        
        return subjects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subjects: {str(e)}"
        )

@router.post("", response_model=schemas.SubjectResponse)
async def create_subject(
    subject: schemas.SubjectCreate, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new subject"""
    try:
        db_subject = models.Subject(
            user_id=current_user["id"],
            name=subject.name,
            code=subject.code,
            semester=subject.semester,
            total_marks=subject.total_marks,
            exam_date=subject.exam_date,
            exam_duration_minutes=subject.exam_duration_minutes,
            syllabus_json=subject.syllabus_json
        )
        db.add(db_subject)
        db.commit()
        db.refresh(db_subject)
        
        # Initialize counts
        db_subject.papers_uploaded = 0
        db_subject.predictions_generated = 0
        
        return db_subject
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subject: {str(e)}"
        )

@router.get("/{subject_id}", response_model=schemas.SubjectResponse)
async def get_subject(
    subject_id: str, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific subject by ID with counts"""
    try:
        # Use subqueries for efficient counting
        papers_count = (
            db.query(func.count(models.QuestionPaper.id))
            .filter(models.QuestionPaper.subject_id == subject_id)
            .scalar_subquery()
        )
        
        predictions_count = (
            db.query(func.count(models.Prediction.id))
            .filter(models.Prediction.subject_id == subject_id)
            .scalar_subquery()
        )
        
        subject = (
            db.query(models.Subject)
            .filter(
                models.Subject.id == subject_id,
                models.Subject.user_id == current_user["id"]
            )
            .first()
        )
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        # Add counts
        subject.papers_uploaded = db.query(func.count(models.QuestionPaper.id)).filter(
            models.QuestionPaper.subject_id == subject.id
        ).scalar() or 0
        
        subject.predictions_generated = db.query(func.count(models.Prediction.id)).filter(
            models.Prediction.subject_id == subject.id
        ).scalar() or 0
        
        return subject
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subject: {str(e)}"
        )

@router.put("/{subject_id}", response_model=schemas.SubjectResponse)
async def update_subject(
    subject_id: str,
    subject_update: schemas.SubjectUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a subject"""
    try:
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id,
            models.Subject.user_id == current_user["id"]
        ).first()
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        # Update fields
        for var, value in vars(subject_update).items():
            if value is not None:
                setattr(subject, var, value)
        
        db.commit()
        db.refresh(subject)
        return subject
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subject: {str(e)}"
        )

@router.delete("/{subject_id}")
async def delete_subject(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a subject"""
    try:
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id,
            models.Subject.user_id == current_user["id"]
        ).first()
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        db.delete(subject)
        db.commit()
        return {"message": "Subject deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete subject: {str(e)}"
        )
