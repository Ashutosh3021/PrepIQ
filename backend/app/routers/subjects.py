from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas
from ..routers.auth import get_current_user

router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"]
)

@router.get("/", response_model=List[schemas.SubjectResponse])
def get_subjects(
    skip: int = 0, 
    limit: int = 100, 
    semester: int = None,
    year: str = None,
    search: str = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(models.Subject).filter(models.Subject.user_id == current_user.id)
    
    if semester:
        query = query.filter(models.Subject.semester == semester)
    if year:
        query = query.filter(models.Subject.academic_year == year)
    if search:
        query = query.filter(models.Subject.name.contains(search))
    
    subjects = query.offset(skip).limit(limit).all()
    
    # Add paper counts to each subject
    for subject in subjects:
        subject.papers_uploaded = db.query(models.QuestionPaper).filter(
            models.QuestionPaper.subject_id == subject.id
        ).count()
        
        subject.predictions_generated = db.query(models.Prediction).filter(
            models.Prediction.subject_id == subject.id
        ).count()
    
    return subjects

@router.post("/", response_model=schemas.SubjectResponse)
def create_subject(
    subject: schemas.SubjectCreate, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db_subject = models.Subject(
        user_id=current_user.id,
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
    
    return db_subject

@router.get("/{subject_id}", response_model=schemas.SubjectResponse)
def get_subject(
    subject_id: str, 
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Add paper counts
    subject.papers_uploaded = db.query(models.QuestionPaper).filter(
        models.QuestionPaper.subject_id == subject.id
    ).count()
    
    subject.predictions_generated = db.query(models.Prediction).filter(
        models.Prediction.subject_id == subject.id
    ).count()
    
    return subject

@router.put("/{subject_id}", response_model=schemas.SubjectResponse)
def update_subject(
    subject_id: str,
    subject_update: schemas.SubjectUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.user_id == current_user.id
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

@router.delete("/{subject_id}")
def delete_subject(
    subject_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    db.delete(subject)
    db.commit()
    return {"message": "Subject deleted successfully"}