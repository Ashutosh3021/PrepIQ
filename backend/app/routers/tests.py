"""
Mock Test router  —  POST /generate, POST /{id}/submit, GET /, GET /{id}

Question storage: questions are serialised into MockTest.questions_json (JSON
column) because a separate mock_test_questions table does not yet exist in the
deployed schema.  The column already carries all required fields so no
migration is needed.
"""
from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..services.supabase_first_auth import get_current_user_from_token


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)


router = APIRouter(prefix="/tests", tags=["Tests"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalise_question(raw: Dict[str, Any], order: int) -> Dict[str, Any]:
    """Return a dict that satisfies MockTestQuestion regardless of source shape."""
    qid = str(raw.get("id") or raw.get("question_id") or uuid.uuid4())
    text = str(
        raw.get("question_text") or raw.get("text") or ""
    )
    topic = str(
        raw.get("topic") or raw.get("unit") or raw.get("unit_name") or "General"
    )
    difficulty = str(raw.get("difficulty") or "medium").lower()
    marks = int(raw.get("marks") or 1)
    correct_answer = raw.get("correct_answer") or None
    options = raw.get("options") or None

    return {
        "id": qid,
        "question_number": order,
        "question_text": text,
        "topic": topic,
        "difficulty": difficulty,
        "marks": marks,
        "correct_answer": correct_answer,
        "options": options,
        # legacy aliases kept so existing code that reads these keys still works
        "number": order,
        "text": text,
        "unit": topic,
        "type": "mcq" if options else "descriptive",
    }


def _weighted_sample(
    items: List[Dict[str, Any]],
    k: int,
    weight_key: str = "confidence_score",
) -> List[Dict[str, Any]]:
    """Random sample weighted by weight_key (falls back to uniform if missing)."""
    if not items:
        return []
    k = min(k, len(items))
    weights = [max(float(it.get(weight_key) or 0), 0.01) for it in items]
    chosen: List[Dict[str, Any]] = []
    pool = list(zip(weights, items))
    for _ in range(k):
        total = sum(w for w, _ in pool)
        r = random.uniform(0, total)
        cumulative = 0.0
        for idx, (w, item) in enumerate(pool):
            cumulative += w
            if cumulative >= r:
                chosen.append(item)
                pool.pop(idx)
                break
    return chosen


def _build_test_response(
    test: models.MockTest, questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build a MockTestResponse-compatible dict from a MockTest ORM row."""
    return {
        "test_id": test.id,
        "subject_id": test.subject_id,
        "status": "completed" if test.is_completed else "pending",
        "total_questions": test.total_questions or len(questions),
        "total_marks": test.total_marks or 0,
        "time_limit_minutes": test.duration_minutes or (len(questions) * 3),
        "created_at": test.created_at or datetime.now(timezone.utc),
        "score_percentage": (
            float(test.percentage) if test.percentage is not None else None
        ),
        "questions": [_normalise_question(q, i + 1) for i, q in enumerate(questions)],
    }


# ---------------------------------------------------------------------------
# POST /tests/generate
# ---------------------------------------------------------------------------
@router.post("/generate", response_model=schemas.MockTestResponse)
async def generate_mock_test(
    test_request: schemas.MockTestRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Two-source question selection with weighted sampling from predictions."""

    # ── Verify subject ownership ──────────────────────────────────────────
    subject = db.query(models.Subject).filter(
        models.Subject.id == test_request.subject_id,
        models.Subject.user_id == current_user["id"],
    ).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    num_q = test_request.num_questions          # already capped at 30 by schema
    difficulty = test_request.difficulty        # already lower-cased by schema
    source = test_request.source               # "predictions" | "all_questions"

    selected: List[Dict[str, Any]] = []

    # ── SOURCE A: predictions ─────────────────────────────────────────────
    if source == "predictions":
        latest_pred = (
            db.query(models.Prediction)
            .filter(
                models.Prediction.subject_id == test_request.subject_id,
                models.Prediction.user_id == current_user["id"],
            )
            .order_by(models.Prediction.created_at.desc())
            .first()
        )

        pred_pool: List[Dict[str, Any]] = []
        if latest_pred and latest_pred.predicted_questions_json:
            try:
                raw = (
                    json.loads(latest_pred.predicted_questions_json)
                    if isinstance(latest_pred.predicted_questions_json, str)
                    else latest_pred.predicted_questions_json
                )
                pred_pool = raw if isinstance(raw, list) else []
            except Exception:
                pred_pool = []

        # Apply difficulty filter for predictions (best-effort: topic match)
        if difficulty != "mixed" and pred_pool:
            filtered = [
                p for p in pred_pool
                if str(p.get("difficulty") or "").lower() == difficulty
            ]
            pred_pool = filtered if filtered else pred_pool  # no-match → keep all

        # Weighted sample from predictions
        selected = _weighted_sample(pred_pool, num_q, weight_key="confidence_score")

        # Backfill from questions table if predictions don't cover num_q
        deficit = num_q - len(selected)
        if deficit > 0:
            q_query = (
                db.query(models.Question)
                .join(models.QuestionPaper)
                .filter(models.QuestionPaper.subject_id == test_request.subject_id)
            )
            if difficulty != "mixed":
                q_query = q_query.filter(models.Question.difficulty == difficulty)
            all_db_qs = q_query.all()
            # exclude IDs already in selected (best-effort, predictions won't have real UUIDs)
            backfill = random.sample(all_db_qs, min(deficit, len(all_db_qs)))
            for q in backfill:
                selected.append({
                    "id": str(q.id),
                    "question_text": q.question_text,
                    "topic": q.unit_name or "General",
                    "unit": q.unit_name or "General",
                    "difficulty": q.difficulty or "medium",
                    "marks": q.marks or 1,
                    "correct_answer": q.correct_answer or None,
                    "options": None,
                    "confidence_score": 0.0,
                    "source": "backfill",
                })

    # ── SOURCE B: all_questions ───────────────────────────────────────────
    else:
        q_query = (
            db.query(models.Question)
            .join(models.QuestionPaper)
            .filter(models.QuestionPaper.subject_id == test_request.subject_id)
        )
        if difficulty != "mixed":
            filtered_q = q_query.filter(models.Question.difficulty == difficulty).all()
            all_db_qs = filtered_q if filtered_q else q_query.all()  # fallback if empty
        else:
            all_db_qs = q_query.all()

        sampled = random.sample(all_db_qs, min(num_q, len(all_db_qs)))
        for q in sampled:
            selected.append({
                "id": str(q.id),
                "question_text": q.question_text,
                "topic": q.unit_name or "General",
                "unit": q.unit_name or "General",
                "difficulty": q.difficulty or "medium",
                "marks": q.marks or 1,
                "correct_answer": q.correct_answer or None,
                "options": None,
            })

    # ── Zero questions — return HTTP 200 with error payload ───────────────
    if not selected:
        return {
            "test_id": str(uuid.uuid4()),
            "subject_id": test_request.subject_id,
            "status": "error",
            "total_questions": 0,
            "total_marks": 0,
            "time_limit_minutes": 0,
            "created_at": datetime.now(timezone.utc),
            "score_percentage": None,
            "questions": [],
            # non-schema keys surfaced as extra fields (FastAPI drops unknown)
            "error": "insufficient_data",
            "message": (
                "No questions available for this subject yet. "
                "Upload past papers first."
            ),
        }

    # ── Normalise and cap ─────────────────────────────────────────────────
    normalised = [_normalise_question(q, i + 1) for i, q in enumerate(selected)]
    total_marks = sum(q["marks"] for q in normalised)

    # ── Persist mock_test record ──────────────────────────────────────────
    mock_test = models.MockTest(
        user_id=current_user["id"],
        subject_id=test_request.subject_id,
        total_questions=len(normalised),
        total_marks=total_marks,
        duration_minutes=test_request.time_limit_minutes,
        difficulty_level=difficulty,
        questions_json=normalised,          # stored as JSON column
        start_time=datetime.now(timezone.utc),
        is_completed=False,
    )
    db.add(mock_test)
    db.commit()
    db.refresh(mock_test)

    return {
        "test_id": mock_test.id,
        "subject_id": mock_test.subject_id,
        "status": "pending",
        "total_questions": mock_test.total_questions,
        "total_marks": mock_test.total_marks,
        "time_limit_minutes": mock_test.duration_minutes,
        "created_at": mock_test.created_at,
        "score_percentage": None,
        "questions": normalised,
    }


# ---------------------------------------------------------------------------
# POST /tests/{test_id}/submit
# ---------------------------------------------------------------------------
@router.post("/{test_id}/submit", response_model=schemas.TestSubmissionResponse)
async def submit_test(
    test_id: str,
    submission: schemas.TestSubmission,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Score a test and mark it completed.

    - Answers are matched against correct_answer where available.
    - If no correct_answer is stored, score_percentage is null (not faked).
    """
    test = db.query(models.MockTest).filter(
        models.MockTest.id == test_id,
        models.MockTest.user_id == current_user["id"],
    ).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    if test.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test has already been submitted.",
        )

    # Build answer lookup: question_id → answer string
    answer_map: Dict[str, str] = {}
    for item in submission.answers:
        qid = str(item.get("question_id", ""))
        ans = str(item.get("answer", ""))
        if qid:
            answer_map[qid] = ans

    # Retrieve stored questions
    questions_data: List[Dict[str, Any]] = []
    if test.questions_json:
        try:
            raw = (
                json.loads(test.questions_json)
                if isinstance(test.questions_json, str)
                else test.questions_json
            )
            questions_data = raw if isinstance(raw, list) else []
        except Exception:
            questions_data = []

    # Grade
    answers_graded = 0
    gradeable = 0          # questions that have a stored correct_answer
    correct_count = 0
    total_marks_earned = 0
    weak_topics: List[str] = []
    strong_topics: List[str] = []

    for q in questions_data:
        qid = str(q.get("id", ""))
        correct = q.get("correct_answer")
        topic = q.get("topic") or q.get("unit") or "General"
        marks = int(q.get("marks") or 1)
        user_ans = answer_map.get(qid, "").strip().upper()

        answers_graded += 1

        if correct:
            gradeable += 1
            if user_ans and user_ans == str(correct).strip().upper():
                correct_count += 1
                total_marks_earned += marks
                if topic not in strong_topics:
                    strong_topics.append(topic)
            else:
                if topic not in weak_topics:
                    weak_topics.append(topic)

    # Only compute a percentage when at least one question had a correct_answer
    score_pct: Optional[float]
    if gradeable > 0 and test.total_marks and test.total_marks > 0:
        score_pct = round(total_marks_earned / test.total_marks * 100, 1)
    else:
        score_pct = None   # no fake score

    # Persist
    test.user_answers_json = answer_map
    test.end_time = datetime.now(timezone.utc)
    test.is_completed = True
    test.score = total_marks_earned
    test.percentage = score_pct
    test.correct_count = correct_count
    test.incorrect_count = max(gradeable - correct_count, 0)
    test.skipped_count = max(len(questions_data) - answers_graded, 0)
    test.weak_topics_json = weak_topics[:5]
    test.strong_topics_json = strong_topics[:5]

    db.commit()
    db.refresh(test)

    return {
        "test_id": test.id,
        "score_percentage": score_pct,
        "total_questions": test.total_questions or len(questions_data),
        "answers_graded": answers_graded,
    }


# ---------------------------------------------------------------------------
# GET /tests/   — all tests for current user
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[schemas.MockTestListItem])
async def get_user_tests(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all mock tests for the authenticated user, newest first."""
    tests = (
        db.query(models.MockTest)
        .filter(models.MockTest.user_id == current_user["id"])
        .order_by(models.MockTest.created_at.desc())
        .all()
    )

    return [
        {
            "test_id": t.id,
            "subject_id": t.subject_id,
            "status": "completed" if t.is_completed else "pending",
            "total_questions": t.total_questions or 0,
            "total_marks": t.total_marks or 0,
            "score_percentage": (
                float(t.percentage) if t.percentage is not None else None
            ),
            "created_at": t.created_at or datetime.now(timezone.utc),
        }
        for t in tests
    ]


# ---------------------------------------------------------------------------
# GET /tests/{test_id}   — full test with all questions
# ---------------------------------------------------------------------------
@router.get("/{test_id}", response_model=schemas.MockTestResponse)
async def get_test(
    test_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a single test with all questions."""
    test = db.query(models.MockTest).filter(
        models.MockTest.id == test_id,
        models.MockTest.user_id == current_user["id"],
    ).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")

    questions_data: List[Dict[str, Any]] = []
    if test.questions_json:
        try:
            raw = (
                json.loads(test.questions_json)
                if isinstance(test.questions_json, str)
                else test.questions_json
            )
            questions_data = raw if isinstance(raw, list) else []
        except Exception:
            questions_data = []

    return _build_test_response(test, questions_data)


# ---------------------------------------------------------------------------
# GET /tests/{test_id}/results   — detailed results (kept for compat)
# ---------------------------------------------------------------------------
@router.get("/{test_id}/results", response_model=schemas.TestResultsResponse)
async def get_test_results(
    test_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    test = db.query(models.MockTest).filter(
        models.MockTest.id == test_id,
        models.MockTest.user_id == current_user["id"],
    ).first()
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    if not test.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test has not been completed yet",
        )

    questions_data: List[Dict[str, Any]] = []
    if test.questions_json:
        try:
            raw = (
                json.loads(test.questions_json)
                if isinstance(test.questions_json, str)
                else test.questions_json
            )
            questions_data = raw if isinstance(raw, list) else []
        except Exception:
            questions_data = []

    user_answers: Dict[str, str] = test.user_answers_json or {}

    question_analysis = []
    weak_topics: List[str] = []
    strong_topics: List[str] = []

    for q in questions_data:
        qid = str(q.get("id", ""))
        user_ans = str(user_answers.get(qid, "")).strip().upper()
        correct = str(q.get("correct_answer") or "").strip().upper()
        topic = q.get("topic") or q.get("unit") or "General"
        is_correct = bool(user_ans and correct and user_ans == correct)

        if is_correct:
            if topic not in strong_topics:
                strong_topics.append(topic)
        else:
            if topic not in weak_topics:
                weak_topics.append(topic)

        question_analysis.append({
            "question_id": qid,
            "marks": int(q.get("marks") or 0),
            "status": "correct" if is_correct else ("skipped" if not user_ans else "incorrect"),
            "user_answer": user_ans or "Skipped",
            "correct_answer": correct or "N/A",
            "explanation": f"Question about {topic}",
        })

    return {
        "test_id": test.id,
        "score": int(test.score or 0),
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


# ---------------------------------------------------------------------------
# GET /tests/progress   — analytics (kept for compat)
# ---------------------------------------------------------------------------
@router.get("/progress", response_model=dict)
async def get_test_progress(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate test analytics for the current user."""
    tests = (
        db.query(models.MockTest)
        .filter(
            models.MockTest.user_id == current_user["id"],
            models.MockTest.is_completed == True,
        )
        .order_by(models.MockTest.created_at)
        .all()
    )

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
    avg_pct = sum(float(t.percentage or 0) for t in tests) / total_tests

    trend = [
        {
            "test_number": i + 1,
            "score": float(t.score or 0),
            "percentage": float(t.percentage or 0),
            "date": t.created_at.isoformat() if t.created_at else None,
            "total_marks": t.total_marks or 0,
        }
        for i, t in enumerate(tests)
    ]

    weak_dict: Dict[str, int] = {}
    strong_dict: Dict[str, int] = {}
    for t in tests:
        for col, target in ((t.weak_topics_json, weak_dict), (t.strong_topics_json, strong_dict)):
            if not col:
                continue
            try:
                topics = json.loads(col) if isinstance(col, str) else col
                for topic in (topics or []):
                    target[topic] = target.get(topic, 0) + 1
            except Exception:
                pass

    return {
        "total_tests": total_tests,
        "average_score": round(sum(float(t.score or 0) for t in tests) / total_tests, 2),
        "average_percentage": round(avg_pct, 2),
        "trend": trend,
        "weak_topics": weak_dict,
        "strong_topics": strong_dict,
    }
