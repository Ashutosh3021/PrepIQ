from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime, timezone

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
    prefix="/tests",
    tags=["Tests"]
)

@router.post("/generate", response_model=schemas.MockTestResponse)
def generate_mock_test(
    test_request: schemas.MockTestRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subject belongs to user
    subject = db.query(models.Subject).filter(
        models.Subject.id == test_request.subject_id,
        models.Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Create mock test record
    mock_test = models.MockTest(
        user_id=current_user.id,
        subject_id=test_request.subject_id,
        total_questions=test_request.num_questions,
        total_marks=100,  # Calculate based on question marks
        duration_minutes=test_request.time_limit_minutes,
        difficulty_level=test_request.difficulty,
        start_time=datetime.now(timezone.utc)
    )
    db.add(mock_test)
    db.commit()
    db.refresh(mock_test)
    
    # In a real implementation, we would select questions based on the criteria
    # For now, return mock questions
    questions = []
    for i in range(test_request.num_questions):
        marks = 2 if i < test_request.num_questions//2 else 5 if i < test_request.num_questions*4//5 else 10
        questions.append({
            "id": str(uuid.uuid4()),
            "number": i+1,
            "text": f"Sample question {i+1} for {subject.name}",
            "marks": marks,
            "unit": f"Unit {((i % 3) + 1)}",
            "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"] if marks == 2 else None,
            "type": "mcq" if marks == 2 else "descriptive"
        })
    
    return {
        "test_id": mock_test.id,
        "total_questions": test_request.num_questions,
        "total_marks": 100,
        "time_limit_minutes": test_request.time_limit_minutes,
        "start_time": mock_test.start_time,
        "questions": questions
    }

@router.post("/{test_id}/submit", response_model=schemas.TestSubmissionResponse)
def submit_test(
    test_id: str,
    submission: schemas.TestSubmission,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify test belongs to user
    test = db.query(models.MockTest).filter(
        models.MockTest.id == test_id,
        models.MockTest.user_id == current_user.id
    ).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    # Update test with submission
    test.user_answers_json = submission.answers
    test.end_time = submission.end_time
    test.is_completed = True
    
    # Calculate score (mock implementation)
    test.score = 72  # Mock score
    test.percentage = 72.0
    test.correct_count = 18
    test.incorrect_count = 5
    test.skipped_count = 2
    
    db.commit()
    db.refresh(test)
    
    return {
        "test_id": test.id,
        "score": test.score,
        "total_marks": test.total_marks,
        "percentage": test.percentage,
        "duration_minutes": (test.end_time - test.start_time).seconds // 60,
        "results": {
            "correct": test.correct_count,
            "incorrect": test.incorrect_count,
            "skipped": test.skipped_count
        }
    }

@router.get("/", response_model=List[schemas.MockTestResponse])
def get_user_tests(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tests for the current user"""
    tests = db.query(models.MockTest).filter(
        models.MockTest.user_id == current_user.id
    ).all()
    
    return [
        {
            "test_id": test.id,
            "total_questions": test.total_questions,
            "total_marks": test.total_marks,
            "time_limit_minutes": test.duration_minutes,
            "start_time": test.start_time,
            "is_completed": test.is_completed,
            "score": test.score,
            "percentage": test.percentage
        }
        for test in tests
    ]

@router.get("/{test_id}/results", response_model=schemas.TestResultsResponse)
def get_test_results(
    test_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify test belongs to user
    test = db.query(models.MockTest).filter(
        models.MockTest.id == test_id,
        models.MockTest.user_id == current_user.id
    ).first()
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    if not test.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test has not been completed yet"
        )
    
    # Mock question analysis
    question_analysis = []
    for i in range(test.total_questions):
        question_analysis.append({
            "question_id": f"q{i+1}",
            "marks": 5,
            "status": "correct" if i < 18 else "incorrect",
            "user_answer": "A" if i < 18 else "B",
            "correct_answer": "A",
            "explanation": f"Explanation for question {i+1}"
        })
    
    return {
        "test_id": test.id,
        "score": test.score,
        "percentage": test.percentage,
        "question_analysis": question_analysis,
        "weak_topics": ["Linear Transformations", "Eigenvalues"],
        "strong_topics": ["Matrix Operations", "Determinants"],
        "recommendations": ["Focus more on weak topics", "Practice more problems"]
    }