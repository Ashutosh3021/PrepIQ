from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
import uuid
import json
import random
from datetime import datetime, timezone

from ..database import get_db
from .. import models, schemas
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
    subject = db.query(models.Subject).filter(
        models.Subject.id == test_request.subject_id,
        models.Subject.user_id == current_user["id"]
    ).first()

    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    papers = db.query(models.QuestionPaper).filter(
        models.QuestionPaper.subject_id == test_request.subject_id,
        models.QuestionPaper.processing_status == "completed"
    ).all()

    if not papers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No processed question papers found for this subject. Please upload papers first."
        )

    query = db.query(models.Question).filter(
        models.Question.paper_id.in_([p.id for p in papers])
    )

    if test_request.difficulty:
        query = query.filter(models.Question.difficulty == test_request.difficulty.lower())

    all_questions = query.all()

    if not all_questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions found in uploaded papers. Please upload more papers."
        )

    selected_questions = random.sample(
        all_questions,
        min(test_request.num_questions, len(all_questions))
    )

    # M-02: guard against None marks
    total_marks = sum((q.marks or 0) for q in selected_questions)

    mock_test = models.MockTest(
        user_id=current_user["id"],
        subject_id=test_request.subject_id,
        total_questions=len(selected_questions),
        total_marks=total_marks,
        duration_minutes=test_request.time_limit_minutes,
        difficulty_level=test_request.difficulty,
        start_time=datetime.now(timezone.utc)
    )

    questions_for_storage = []
    for q in selected_questions:
        marks = q.marks or 0
        # M-01: guard against None marks before comparison
        is_mcq = (marks <= 2)
        questions_for_storage.append({
            "id": str(q.id),
            "number": q.question_number,
            "text": q.question_text[:500] if q.question_text else "",
            "marks": marks,
            "unit": q.unit_name or "General",
            "type": "mcq" if is_mcq else "descriptive",
            "correct_answer": "A",
            "explanation": f"Question from {q.unit_name or 'the paper'}"
        })
    mock_test.questions_json = json.dumps(questions_for_storage)

    db.add(mock_test)
    db.commit()
    db.refresh(mock_test)

    questions = []
    for i, q in enumerate(selected_questions):
        marks = q.marks or 0
        is_mcq = (marks <= 2)
        questions.append({
            "id": str(q.id),
            "number": i + 1,
            "text": q.question_text[:500] if q.question_text else "",
            "marks": marks,
            "unit": q.unit_name or "General",
            "options": ["A) Option A", "B) Option B", "C) Option C", "D) Option D"] if is_mcq else None,
            "type": "mcq" if is_mcq else "descriptive"
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
    test = db.query(models.MockTest).filter(
        models.MockTest.id == test_id,
        models.MockTest.user_id == current_user["id"]
    ).first()

    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    test.user_answers_json = submission.answers
    test.end_time = submission.end_time
    test.is_completed = True

    questions_data = []
    if test.questions_json:
        try:
            questions_data = (
                json.loads(test.questions_json)
                if isinstance(test.questions_json, str)
                else test.questions_json
            )
        except Exception:
            questions_data = []

    if questions_data and submission.answers:
        correct_count = 0
        incorrect_count = 0
        skipped_count = 0
        total_marks_obtained = 0
        weak_topics = []
        strong_topics = []

        for q in questions_data:
            q_id = str(q.get("id", ""))
            user_answer = (
                submission.answers.get(q_id, "").strip().upper()
                if submission.answers.get(q_id)
                else ""
            )
            correct_answer = (
                str(q.get("correct_answer", "")).strip().upper()
                if q.get("correct_answer")
                else ""
            )
            unit = q.get("unit", "General")

            if not user_answer:
                skipped_count += 1
                if unit not in weak_topics:
                    weak_topics.append(unit)
            elif user_answer == correct_answer:
                correct_count += 1
                total_marks_obtained += q.get("marks", 0)
                if unit not in strong_topics:
                    strong_topics.append(unit)
            else:
                incorrect_count += 1
                if unit not in weak_topics:
                    weak_topics.append(unit)

        percentage = (
            (total_marks_obtained / test.total_marks * 100) if test.total_marks > 0 else 0
        )
        test.score = total_marks_obtained
        test.percentage = round(percentage, 1)
        test.correct_count = correct_count
        test.incorrect_count = incorrect_count
        test.skipped_count = skipped_count
        test.weak_topics_json = json.dumps(weak_topics[:5])
        test.strong_topics_json = json.dumps(strong_topics[:5])
    else:
        # C-08: no fake scores — mark everything as skipped/zero
        test.score = 0
        test.percentage = 0.0
        test.correct_count = 0
        test.incorrect_count = 0
        test.skipped_count = test.total_questions or 0

    db.commit()
    db.refresh(test)

    # M-03: guard against None start_time
    if test.start_time and test.end_time:
        duration_minutes = (test.end_time - test.start_time).seconds // 60
    else:
        duration_minutes = 0

    return {
        "test_id": test.id,
        "score": test.score,
        "total_marks": test.total_marks,
        "percentage": test.percentage,
        "duration_minutes": duration_minutes,
        "results": {
            "correct": test.correct_count,
            "incorrect": test.incorrect_count,
            "skipped": test.skipped_count,
        },
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

    result = []
    for test in tests:
        # H-06: MockTestResponse requires a `questions` field — provide empty list
        # when the test is already completed (questions are stored in questions_json)
        questions_list = []
        if test.questions_json:
            try:
                raw = (
                    json.loads(test.questions_json)
                    if isinstance(test.questions_json, str)
                    else test.questions_json
                )
                for q in raw:
                    questions_list.append({
                        "id": q.get("id", str(uuid.uuid4())),
                        "number": q.get("number", 0),
                        "text": q.get("text", ""),
                        "marks": q.get("marks", 0),
                        "unit": q.get("unit", "General"),
                        "options": None,
                        "type": q.get("type", "descriptive"),
                    })
            except Exception:
                questions_list = []

        result.append({
            "test_id": test.id,
            "total_questions": test.total_questions,
            "total_marks": test.total_marks,
            "time_limit_minutes": test.duration_minutes,
            "start_time": test.start_time or datetime.now(timezone.utc),
            "questions": questions_list,
        })

    return result


@router.get("/{test_id}/results", response_model=schemas.TestResultsResponse)
async def get_test_results(
    test_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    test = db.query(models.MockTest).filter(
        models.MockTest.id == test_id,
        models.MockTest.user_id == current_user["id"]
    ).first()

    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    if not test.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test has not been completed yet"
        )

    questions_data = []
    if test.questions_json:
        try:
            questions_data = (
                json.loads(test.questions_json)
                if isinstance(test.questions_json, str)
                else test.questions_json
            )
        except Exception:
            questions_data = []

    user_answers = test.user_answers_json if test.user_answers_json else {}

    question_analysis = []
    weak_topics: List[str] = []
    strong_topics: List[str] = []

    if questions_data and user_answers:
        for q in questions_data:
            q_id = str(q.get("id", ""))
            user_answer = (
                str(user_answers.get(q_id, "")).strip().upper()
                if user_answers.get(q_id)
                else ""
            )
            correct_answer = (
                str(q.get("correct_answer", "")).strip().upper()
                if q.get("correct_answer")
                else ""
            )
            is_correct = bool(user_answer and user_answer == correct_answer)
            unit = q.get("unit", "General")

            if is_correct:
                if unit not in strong_topics:
                    strong_topics.append(unit)
            else:
                if unit not in weak_topics:
                    weak_topics.append(unit)

            question_analysis.append({
                "question_id": q_id,
                "marks": q.get("marks", 0),
                "status": "correct" if is_correct else "incorrect",
                "user_answer": user_answer if user_answer else "Skipped",
                "correct_answer": correct_answer if correct_answer else "N/A",
                "explanation": q.get("explanation", f"Question about {unit}"),
            })
    else:
        # C-09: return empty analysis instead of fake data
        question_analysis = []

    return {
        "test_id": test.id,
        "score": test.score or 0,
        "percentage": float(test.percentage or 0),
        "question_analysis": question_analysis,
        "weak_topics": weak_topics[:5],
        "strong_topics": strong_topics[:5],
        "recommendations": (
            ["Focus more on weak topics", "Practice more problems"]
            if weak_topics
            else ["Keep up the good work!", "Try a harder difficulty level"]
        ),
    }


@router.get("/progress", response_model=dict)
async def get_test_progress(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get test progress and analytics for the current user"""
    tests = db.query(models.MockTest).filter(
        models.MockTest.user_id == current_user["id"],
        models.MockTest.is_completed == True
    ).order_by(models.MockTest.created_at).all()

    if not tests:
        return {
            "total_tests": 0,
            "average_score": 0,
            "average_percentage": 0,
            "trend": [],
            "weak_topics": {},
            "strong_topics": {},
        }

    total_tests = len(tests)
    total_score = sum(test.score or 0 for test in tests)
    average_score = total_score / total_tests if total_tests > 0 else 0
    average_percentage = sum(test.percentage or 0 for test in tests) / total_tests if total_tests > 0 else 0

    # Build trend data
    trend = []
    for i, test in enumerate(tests):
        trend.append({
            "test_number": i + 1,
            "score": float(test.score or 0),
            "percentage": float(test.percentage or 0),
            "date": test.created_at.isoformat() if test.created_at else None,
            "total_marks": test.total_marks or 0,
        })

    # Aggregate weak and strong topics
    weak_topics_dict = {}
    strong_topics_dict = {}

    for test in tests:
        if test.weak_topics_json:
            try:
                weak = json.loads(test.weak_topics_json) if isinstance(test.weak_topics_json, str) else test.weak_topics_json
                for topic in weak:
                    weak_topics_dict[topic] = weak_topics_dict.get(topic, 0) + 1
            except Exception:
                pass

        if test.strong_topics_json:
            try:
                strong = json.loads(test.strong_topics_json) if isinstance(test.strong_topics_json, str) else test.strong_topics_json
                for topic in strong:
                    strong_topics_dict[topic] = strong_topics_dict.get(topic, 0) + 1
            except Exception:
                pass

    return {
        "total_tests": total_tests,
        "average_score": round(average_score, 2),
        "average_percentage": round(average_percentage, 2),
        "trend": trend,
        "weak_topics": weak_topics_dict,
        "strong_topics": strong_topics_dict,
    }
