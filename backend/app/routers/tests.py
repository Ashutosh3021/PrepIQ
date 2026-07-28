"""
Mock tests API — Pyronites (Fix Phase C).
Honest null scores; no fake test_id; reject submit on test_id=none.
"""
from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from .. import schemas
from ..services.pyronites_auth import get_current_user_from_token
from ..repositories import subjects as subjects_repo
from ..repositories import predictions as predictions_repo
from ..repositories import questions as questions_repo
from ..repositories import mock_tests as mock_tests_repo

router = APIRouter(prefix="/tests", tags=["Tests"])


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


def _normalise_question(raw: Dict[str, Any], order: int) -> Dict[str, Any]:
    qid = str(raw.get("id") or raw.get("question_id") or uuid.uuid4())
    text = str(raw.get("question_text") or raw.get("text") or "")
    topic = str(raw.get("topic") or raw.get("unit") or raw.get("unit_name") or "General")
    difficulty = str(raw.get("difficulty") or "medium").lower()
    try:
        marks = int(raw.get("marks") or 1)
    except (TypeError, ValueError):
        marks = 1
    return {
        "id": qid,
        "question_number": order,
        "question_text": text,
        "topic": topic,
        "difficulty": difficulty,
        "marks": marks,
        "correct_answer": raw.get("correct_answer") or None,
        "options": raw.get("options") or None,
        "number": order,
        "text": text,
        "unit": topic,
        "type": "mcq" if raw.get("options") else "descriptive",
        "confidence_score": float(raw.get("confidence_score") or 0),
    }


def _weighted_sample(
    items: List[Dict[str, Any]],
    k: int,
    weight_key: str = "confidence_score",
) -> List[Dict[str, Any]]:
    if not items:
        return []
    k = min(k, len(items))
    weights = [max(float(it.get(weight_key) or 0), 0.01) for it in items]
    chosen: List[Dict[str, Any]] = []
    pool = list(zip(weights, items))
    for _ in range(k):
        if not pool:
            break
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


def _parse_json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return value
    return value


@router.post("/generate", response_model=schemas.MockTestResponse)
async def generate_mock_test(
    test_request: schemas.MockTestRequest,
    current_user: dict = Depends(get_current_user),
):
    subject = subjects_repo.get_for_user(test_request.subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    num_q = test_request.num_questions
    difficulty = (test_request.difficulty or "mixed").lower()
    source = getattr(test_request, "source", None) or "all_questions"

    selected: List[Dict[str, Any]] = []

    if source == "predictions":
        latest = predictions_repo.get_latest(current_user["id"], test_request.subject_id)
        pred_pool: List[Dict[str, Any]] = []
        if latest:
            raw = _parse_json_field(latest.get("predicted_questions_json"))
            pred_pool = [p for p in (raw if isinstance(raw, list) else []) if isinstance(p, dict)]
        if difficulty != "mixed" and pred_pool:
            filtered = [
                p for p in pred_pool if str(p.get("difficulty") or "").lower() == difficulty
            ]
            pred_pool = filtered if filtered else pred_pool
        selected = _weighted_sample(pred_pool, num_q, weight_key="confidence_score")
        deficit = num_q - len(selected)
        if deficit > 0:
            bank = questions_repo.list_for_subject(test_request.subject_id)
            if difficulty != "mixed":
                fb = [q for q in bank if str(q.get("difficulty") or "").lower() == difficulty]
                bank = fb if fb else bank
            for q in random.sample(bank, min(deficit, len(bank))):
                selected.append(
                    {
                        "id": str(q.get("id")),
                        "question_text": q.get("question_text"),
                        "topic": q.get("unit_name") or "General",
                        "difficulty": q.get("difficulty") or "medium",
                        "marks": q.get("marks") or 1,
                        "correct_answer": q.get("correct_answer"),
                        "confidence_score": 0.0,
                        "source": "backfill",
                    }
                )
    else:
        bank = questions_repo.list_for_subject(test_request.subject_id)
        if difficulty != "mixed":
            fb = [q for q in bank if str(q.get("difficulty") or "").lower() == difficulty]
            bank = fb if fb else bank
        for q in random.sample(bank, min(num_q, len(bank))):
            selected.append(
                {
                    "id": str(q.get("id")),
                    "question_text": q.get("question_text"),
                    "topic": q.get("unit_name") or "General",
                    "difficulty": q.get("difficulty") or "medium",
                    "marks": q.get("marks") or 1,
                    "correct_answer": q.get("correct_answer"),
                }
            )

    if not selected:
        return {
            "test_id": "none",
            "subject_id": test_request.subject_id,
            "status": "error",
            "total_questions": 0,
            "total_marks": 0,
            "time_limit_minutes": 0,
            "created_at": datetime.now(timezone.utc),
            "score_percentage": None,
            "questions": [],
            "error": "insufficient_data",
            "message": "No questions available for this subject yet. Upload past papers first.",
        }

    normalised = [_normalise_question(q, i + 1) for i, q in enumerate(selected)]
    total_marks = sum(q["marks"] for q in normalised)
    duration = test_request.time_limit_minutes or max(len(normalised) * 3, 1)

    row = mock_tests_repo.create(
        current_user["id"],
        test_request.subject_id,
        {
            "total_questions": len(normalised),
            "total_marks": total_marks,
            "duration_minutes": duration,
            "difficulty_level": difficulty,
            "questions_json": normalised,
            "is_completed": False,
            "start_time": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {
        "test_id": str(row.get("id")),
        "subject_id": test_request.subject_id,
        "status": "pending",
        "total_questions": len(normalised),
        "total_marks": total_marks,
        "time_limit_minutes": duration,
        "created_at": row.get("created_at") or datetime.now(timezone.utc),
        "score_percentage": None,
        "questions": normalised,
    }


@router.post("/{test_id}/submit", response_model=schemas.TestSubmissionResponse)
async def submit_test(
    test_id: str,
    submission: schemas.TestSubmission,
    current_user: dict = Depends(get_current_user),
):
    if not test_id or test_id in ("none", "null", "undefined"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid test_id. Generate a test with available questions first.",
        )

    test = mock_tests_repo.get_for_user(test_id, current_user["id"])
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    if test.get("is_completed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Test has already been submitted.")

    answer_map: Dict[str, str] = {}
    answers = submission.answers
    if isinstance(answers, dict):
        answer_map = {str(k): str(v) for k, v in answers.items()}
    elif isinstance(answers, list):
        for item in answers:
            if isinstance(item, dict):
                qid = str(item.get("question_id") or item.get("id") or "")
                ans = str(item.get("answer") or "")
                if qid:
                    answer_map[qid] = ans

    questions_data = _parse_json_field(test.get("questions_json")) or []
    if not isinstance(questions_data, list):
        questions_data = []

    answers_graded = 0
    gradeable = 0
    correct_count = 0
    total_marks_earned = 0
    weak_topics: List[str] = []
    strong_topics: List[str] = []

    for q in questions_data:
        if not isinstance(q, dict):
            continue
        qid = str(q.get("id", ""))
        correct = q.get("correct_answer")
        topic = q.get("topic") or q.get("unit") or "General"
        try:
            marks = int(q.get("marks") or 1)
        except (TypeError, ValueError):
            marks = 1
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

    total_marks = int(test.get("total_marks") or 0)
    score_pct: Optional[float]
    if gradeable > 0 and total_marks > 0:
        score_pct = round(total_marks_earned / total_marks * 100, 1)
    else:
        score_pct = None

    mock_tests_repo.update(
        test_id,
        {
            "user_answers_json": answer_map,
            "end_time": datetime.now(timezone.utc).isoformat(),
            "is_completed": True,
            "score": total_marks_earned,
            "percentage": score_pct,
            "correct_count": correct_count,
            "incorrect_count": max(gradeable - correct_count, 0),
            "skipped_count": max(len(questions_data) - answers_graded, 0),
            "weak_topics_json": weak_topics[:5],
            "strong_topics_json": strong_topics[:5],
        },
    )

    return {
        "test_id": test_id,
        "score_percentage": score_pct,
        "total_questions": int(test.get("total_questions") or len(questions_data)),
        "answers_graded": answers_graded,
    }


@router.get("/", response_model=List[schemas.MockTestListItem])
async def get_user_tests(current_user: dict = Depends(get_current_user)):
    tests = mock_tests_repo.list_for_user(current_user["id"])

    def _key(t: Dict[str, Any]) -> str:
        return str(t.get("created_at") or "")

    tests = sorted(tests, key=_key, reverse=True)
    out = []
    for t in tests:
        pct = t.get("percentage")
        out.append(
            {
                "test_id": str(t.get("id")),
                "subject_id": str(t.get("subject_id")),
                "status": "completed" if t.get("is_completed") else "pending",
                "total_questions": int(t.get("total_questions") or 0),
                "total_marks": int(t.get("total_marks") or 0),
                "score_percentage": float(pct) if pct is not None else None,
                "created_at": t.get("created_at") or datetime.now(timezone.utc),
            }
        )
    return out


@router.get("/{test_id}", response_model=schemas.MockTestResponse)
async def get_test(test_id: str, current_user: dict = Depends(get_current_user)):
    if test_id in ("none", "null", "undefined"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    test = mock_tests_repo.get_for_user(test_id, current_user["id"])
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    questions_data = _parse_json_field(test.get("questions_json")) or []
    if not isinstance(questions_data, list):
        questions_data = []
    normalised = [_normalise_question(q, i + 1) for i, q in enumerate(questions_data) if isinstance(q, dict)]
    pct = test.get("percentage")
    return {
        "test_id": str(test.get("id")),
        "subject_id": str(test.get("subject_id")),
        "status": "completed" if test.get("is_completed") else "pending",
        "total_questions": int(test.get("total_questions") or len(normalised)),
        "total_marks": int(test.get("total_marks") or 0),
        "time_limit_minutes": int(test.get("duration_minutes") or max(len(normalised) * 3, 1)),
        "created_at": test.get("created_at") or datetime.now(timezone.utc),
        "score_percentage": float(pct) if pct is not None else None,
        "questions": normalised,
    }


@router.get("/{test_id}/results", response_model=schemas.TestResultsResponse)
async def get_test_results(test_id: str, current_user: dict = Depends(get_current_user)):
    if test_id in ("none", "null", "undefined"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    test = mock_tests_repo.get_for_user(test_id, current_user["id"])
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    if not test.get("is_completed"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Test has not been completed yet")

    questions_data = _parse_json_field(test.get("questions_json")) or []
    if not isinstance(questions_data, list):
        questions_data = []
    user_answers = _parse_json_field(test.get("user_answers_json")) or {}
    if not isinstance(user_answers, dict):
        user_answers = {}

    question_analysis = []
    weak_topics: List[str] = []
    strong_topics: List[str] = []

    for q in questions_data:
        if not isinstance(q, dict):
            continue
        qid = str(q.get("id", ""))
        user_ans = str(user_answers.get(qid, "")).strip().upper()
        correct = str(q.get("correct_answer") or "").strip().upper()
        topic = q.get("topic") or q.get("unit") or "General"
        is_correct = bool(user_ans and correct and user_ans == correct)
        if correct:
            if is_correct:
                if topic not in strong_topics:
                    strong_topics.append(topic)
            else:
                if topic not in weak_topics:
                    weak_topics.append(topic)
        question_analysis.append(
            {
                "question_id": qid,
                "marks": int(q.get("marks") or 0),
                "status": "correct" if is_correct else ("skipped" if not user_ans else "incorrect"),
                "user_answer": user_ans or "Skipped",
                "correct_answer": correct or "N/A",
                "explanation": f"Question about {topic}",
            }
        )

    pct = test.get("percentage")
    return {
        "test_id": test_id,
        "score": int(test.get("score") or 0),
        "percentage": float(pct) if pct is not None else None,
        "question_analysis": question_analysis,
        "weak_topics": weak_topics[:5],
        "strong_topics": strong_topics[:5],
        "recommendations": (
            ["Focus more on weak topics", "Practice more problems"]
            if weak_topics
            else ["Keep up the good work!", "Try a harder difficulty level"]
        ),
    }
