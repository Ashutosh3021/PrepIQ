from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime, timezone

from ..database import get_db
from .. import models, schemas

# Import from the new Supabase-first auth service
from ..services.supabase_first_auth import get_current_user_from_token

# Dependency for protected routes
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)

router = APIRouter(
    prefix="/tests",
    tags=["Tests"]
)

@router.post("/generate", response_model=schemas.MockTestResponse)
async def generate_mock_test(
    test_request: schemas.MockTestRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subject belongs to user
    subject = db.query(models.Subject).filter(
        models.Subject.id == test_request.subject_id,
        models.Subject.user_id == current_user["id"]
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Get completed papers for this subject
    papers = db.query(models.QuestionPaper).filter(
        models.QuestionPaper.subject_id == test_request.subject_id,
        models.QuestionPaper.processing_status == "completed"
    ).all()
    
    if not papers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No processed question papers found for this subject. Please upload papers first."
        )
    
    # Get questions from these papers
    query = db.query(models.Question).filter(
        models.Question.paper_id.in_([p.id for p in papers])
    )
    
    # Filter by difficulty if specified
    if test_request.difficulty:
        difficulty_map = {"easy": 1, "medium": 2, "hard": 3}
        target_diff = difficulty_map.get(test_request.difficulty.lower(), 2)
        # Allow ±1 difficulty level
        query = query.filter(models.Question.difficulty.in_([target_diff - 1, target_diff, target_diff + 1]))
    
    # Get questions
    all_questions = query.all()
    
    if not all_questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions found in uploaded papers. Please upload more papers."
        )
    
    # Shuffle and select required number of questions
    import random
    selected_questions = random.sample(
        all_questions, 
        min(test_request.num_questions, len(all_questions))
    )
    
    # Calculate total marks
    total_marks = sum(q.marks for q in selected_questions)
    
    # Create test record
    mock_test = models.MockTest(
        user_id=current_user["id"],
        subject_id=test_request.subject_id,
        total_questions=len(selected_questions),
        total_marks=total_marks,
        duration_minutes=test_request.time_limit_minutes,
        difficulty_level=test_request.difficulty,
        start_time=datetime.now(timezone.utc)
    )
    db.add(mock_test)
    db.commit()
    db.refresh(mock_test)
    
    # Format questions for response
    questions = []
    for i, q in enumerate(selected_questions):
        questions.append({
            "id": str(q.id),
            "number": i+1,
            "text": q.question_text[:500] if q.question_text else "",
            "marks": q.marks,
            "unit": q.unit_name or "General",
            "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"] if q.marks <= 2 else None,
            "type": "mcq" if q.marks <= 2 else "descriptive"
        })
    
    return {
        "test_id": mock_test.id,
        "total_questions": len(selected_questions),
        "total_marks": total_marks,
        "time_limit_minutes": test_request.time_limit_minutes,
        "start_time": mock_test.start_time,
        "questions": questions
    }

@router.post("/{test_id}/submit", response_model=schemas.TestSubmissionResponse)
async def submit_test(
    test_id: str,
    submission: schemas.TestSubmission,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify test belongs to user
    test = db.query(models.MockTest).filter(
        models.MockTest.id == test_id,
        models.MockTest.user_id == current_user["id"]
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
async def get_user_tests(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tests for the current user"""
    tests = db.query(models.MockTest).filter(
        models.MockTest.user_id == current_user["id"]
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
async def get_test_results(
    test_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify test belongs to user
    test = db.query(models.MockTest).filter(
        models.MockTest.id == test_id,
        models.MockTest.user_id == current_user["id"]
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