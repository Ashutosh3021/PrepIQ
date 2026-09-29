"""
Mock tests API — Pyronites (Fix Phase C).
Honest null scores; no fake test_id; reject submit on test_id=none.
Generation lives in services/test_generator.py (plan 1.2); hybrid grading
math in services/hybrid_grading.py (plan 1.4).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from .. import schemas
from .. import blueprints
from ..services.pyronites_auth import get_current_user_from_token
from ..services.test_generator import generate, normalise_question, parse_json_field
from ..services import hybrid_grading
from ..services import rubric_generation
from ..repositories import subjects as subjects_repo
from ..repositories import mock_tests as mock_tests_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tests", tags=["Tests"])


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


def _load_test(test_id: str, user_id: str, *, require_completed: bool = False) -> Dict[str, Any]:
    if not test_id or test_id in ("none", "null", "undefined"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    test = mock_tests_repo.get_for_user(test_id, user_id)
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
    if require_completed and not test.get("is_completed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Test has not been completed yet"
        )
    return test


def _artifacts_for(test: Dict[str, Any], questions_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Rubric artifacts for the test's questions — grading must never 500 on a
    rubric read failure (falls back to empty anchors)."""
    try:
        ids = [str(q.get("id")) for q in questions_data if isinstance(q, dict) and q.get("id")]
        return rubric_generation.get_artifacts(ids)
    except Exception:
        return {}


def _normalise_answers(answers: Any) -> Dict[str, str]:
    if isinstance(answers, dict):
        return {str(k): str(v) for k, v in answers.items()}
    out: Dict[str, str] = {}
    if isinstance(answers, list):
        for item in answers:
            if isinstance(item, dict):
                qid = str(item.get("question_id") or item.get("id") or "")
                if qid:
                    out[qid] = str(item.get("answer") or "")
    return out


@router.get("/blueprints/presets", response_model=List[schemas.BlueprintPreset])
async def get_blueprint_presets(current_user: dict = Depends(get_current_user)):
    """Blueprint presets for the test-builder drawer (implementation-plan 1.1)."""
    return blueprints.list_presets()


@router.post("/generate", response_model=schemas.MockTestResponse)
async def generate_mock_test(
    test_request: schemas.MockTestRequest,
    current_user: dict = Depends(get_current_user),
):
    subject = subjects_repo.get_for_user(test_request.subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    return generate(current_user["id"], subject, test_request)


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

    answer_map = _normalise_answers(submission.answers)
    questions_data = parse_json_field(test.get("questions_json")) or []
    if not isinstance(questions_data, list):
        questions_data = []

    artifacts = _artifacts_for(test, questions_data)
    graded = hybrid_grading.grade_submission(questions_data, answer_map, artifacts)

    total_marks = int(test.get("total_marks") or 0)
    auto_points = float(graded["auto_points"])
    pending = graded["pending"]
    score_pct: Optional[float]
    self_grade_json: Optional[Dict[str, Any]] = None

    if pending:
        # Honest nulls until every pending answer is self-verified (plan 1.4).
        score_pct = None
        grading_mode = "pending_self_grade"
        self_grade_json = {
            "stage": "provisional",
            "auto_points": auto_points,
            "provisional": graded["provisional"],
            "pending": pending,
            "items": {},
        }
    elif graded["gradeable"] > 0 and total_marks > 0:
        score_pct = round(auto_points / total_marks * 100, 1)
        grading_mode = "auto"
    else:
        score_pct = None
        grading_mode = "none"

    update: Dict[str, Any] = {
        "user_answers_json": answer_map,
        "end_time": datetime.now(timezone.utc).isoformat(),
        "is_completed": True,
        "score": int(round(auto_points)),
        "percentage": score_pct,
        "correct_count": int(graded["correct_count"]),
        "incorrect_count": max(int(graded["gradeable"]) - int(graded["correct_count"]), 0),
        "skipped_count": int(graded["skipped"]),
        "weak_topics_json": graded["weak_topics"],
        "strong_topics_json": graded["strong_topics"],
        "grading_mode": grading_mode,
    }
    if self_grade_json is not None:
        update["self_grade_json"] = self_grade_json
    mock_tests_repo.update(test_id, update)

    return {
        "test_id": test_id,
        "score_percentage": score_pct,
        "total_questions": int(test.get("total_questions") or len(questions_data)),
        "answers_graded": int(graded["answers_graded"]),
        "grading_mode": grading_mode,
        "pending_self_grade": len(pending),
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
    questions_data = parse_json_field(test.get("questions_json")) or []
    if not isinstance(questions_data, list):
        questions_data = []
    normalised = [normalise_question(q, i + 1) for i, q in enumerate(questions_data) if isinstance(q, dict)]
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

    questions_data = parse_json_field(test.get("questions_json")) or []
    if not isinstance(questions_data, list):
        questions_data = []
    user_answers = parse_json_field(test.get("user_answers_json")) or {}
    if not isinstance(user_answers, dict):
        user_answers = {}
    self_grade = parse_json_field(test.get("self_grade_json")) or {}
    if not isinstance(self_grade, dict):
        self_grade = {}
    verified_points = self_grade.get("items") or {}

    question_analysis = []
    weak_topics: List[str] = []
    strong_topics: List[str] = []

    for q in questions_data:
        if not isinstance(q, dict):
            continue
        qid = str(q.get("id", ""))
        user_raw = str(user_answers.get(qid, "") or "").strip()
        user_ans = user_raw.upper()
        correct = str(q.get("correct_answer") or "").strip().upper()
        topic = q.get("topic") or q.get("unit") or "General"
        is_correct = bool(user_ans and correct and user_ans == correct)
        v = verified_points.get(qid) if isinstance(verified_points.get(qid), dict) else None

        # status (hybrid grading plan 1.4): auto-corrected questions keep
        # correct/incorrect; descriptive answers are honest — pending until the
        # student self-verifies, then "verified" with awarded points.
        pts: Optional[float] = None
        if not user_raw:
            status = "skipped"
        elif correct:
            status = "correct" if is_correct else "incorrect"
        elif v is not None:
            status = "verified"
            pts = float(v.get("points_hit") or 0)
        else:
            status = "pending_self_grade"

        if status == "correct" and topic not in strong_topics:
            strong_topics.append(topic)
        if status == "incorrect" and topic not in weak_topics:
            weak_topics.append(topic)

        question_analysis.append(
            {
                "question_id": qid,
                "marks": int(q.get("marks") or 0),
                "status": status,
                "user_answer": user_raw or "Skipped",
                "correct_answer": correct or "N/A",
                "explanation": f"Question about {topic}",
                "points": pts,
            }
        )

    # Topics: prefer the stored (graded) sets — they include self-verified
    # weak/strong recomputation; fall back to auto-only computation above.
    stored_weak = parse_json_field(test.get("weak_topics_json")) or []
    stored_strong = parse_json_field(test.get("strong_topics_json")) or []
    if isinstance(stored_weak, list) and stored_weak:
        weak_topics = [str(t) for t in stored_weak]
    if isinstance(stored_strong, list) and stored_strong:
        strong_topics = [str(t) for t in stored_strong]

    pct = test.get("percentage")
    return {
        "test_id": test_id,
        "score": int(test.get("score") or 0),
        "percentage": float(pct) if pct is not None else None,
        "grading_mode": str(
            test.get("grading_mode")
            or ("auto" if pct is not None else "none")
        ),
        "question_analysis": question_analysis,
        "weak_topics": weak_topics[:5],
        "strong_topics": strong_topics[:5],
        "recommendations": (
            ["Focus more on weak topics", "Practice more problems"]
            if weak_topics
            else ["Keep up the good work!", "Try a harder difficulty level"]
        ),
    }


# ── Phase 1.4: review + self-grade (hybrid grading) ──────────────────────────

@router.get("/{test_id}/review", response_model=schemas.TestReviewResponse)
async def get_test_review(test_id: str, current_user: dict = Depends(get_current_user)):
    """Model answers + rubrics for every question (completed tests only)."""
    test = _load_test(test_id, current_user["id"], require_completed=True)
    questions_data = parse_json_field(test.get("questions_json")) or []
    if not isinstance(questions_data, list):
        questions_data = []
    answer_map = parse_json_field(test.get("user_answers_json")) or {}
    if not isinstance(answer_map, dict):
        answer_map = {}
    self_grade = parse_json_field(test.get("self_grade_json")) or {}
    if not isinstance(self_grade, dict):
        self_grade = {}
    artifacts = _artifacts_for(test, questions_data)

    provisional = self_grade.get("provisional") or {}
    verified = self_grade.get("items") or {}
    pending = [str(q) for q in (self_grade.get("pending") or [])]
    grading_mode = str(
        test.get("grading_mode")
        or ("auto" if test.get("percentage") is not None else "none")
    )

    items: List[Dict[str, Any]] = []
    for i, q in enumerate(questions_data):
        if not isinstance(q, dict):
            continue
        qid = str(q.get("id") or "")
        art = artifacts.get(qid) or {}
        try:
            marks = int(q.get("marks") or 1)
        except (TypeError, ValueError):
            marks = 1
        user_raw = str(answer_map.get(qid, "") or "").strip()
        correct = q.get("correct_answer")
        mode = str(art.get("mode") or ("mcq" if q.get("options") else "descriptive"))
        anchors = art.get("keyword_anchors") or []
        if not anchors and mode == "descriptive":
            anchors = hybrid_grading.fallback_anchors(str(q.get("question_text") or ""))

        auto_result: Optional[str] = None
        if correct:
            if not user_raw:
                auto_result = "skipped"
            elif user_raw.lower() == str(correct).strip().lower():
                auto_result = "correct"
            else:
                auto_result = "incorrect"

        v = verified.get(qid) or {}
        items.append(
            {
                "question_id": qid,
                "question_number": int(q.get("question_number") or i + 1),
                "question_text": str(q.get("question_text") or ""),
                "topic": str(q.get("topic") or q.get("unit") or "General"),
                "marks": marks,
                "mode": mode,
                "user_answer": user_raw or None,
                "auto_result": auto_result,
                "provisional_points": provisional.get(qid),
                "verified_points": v.get("points_hit") if v else None,
                "error_class": v.get("error_class") if v else None,
                "model_answer": art.get("model_answer"),
                "rubric_bullets": art.get("rubric_bullets"),
                "keyword_anchors": anchors or None,
                "needs_review": bool(art.get("needs_review")),
            }
        )

    pct = test.get("percentage")
    return {
        "test_id": str(test.get("id")),
        "grading_mode": grading_mode,
        "percentage": float(pct) if pct is not None else None,
        "pending_self_grade": len(pending),
        "total_questions": int(test.get("total_questions") or len(items)),
        "total_marks": int(test.get("total_marks") or 0),
        "items": items,
    }


@router.post("/{test_id}/self-grade", response_model=schemas.TestSubmissionResponse)
async def self_grade_test(
    test_id: str,
    body: schemas.SelfGradeRequest,
    current_user: dict = Depends(get_current_user),
):
    """Student self-verification: award points + error class per pending
    answer -> final Self-Verified score (plan 1.4 / D4)."""
    test = _load_test(test_id, current_user["id"], require_completed=True)
    questions_data = parse_json_field(test.get("questions_json")) or []
    if not isinstance(questions_data, list):
        questions_data = []
    answer_map = parse_json_field(test.get("user_answers_json")) or {}
    if not isinstance(answer_map, dict):
        answer_map = {}
    self_grade = parse_json_field(test.get("self_grade_json")) or {}
    if not isinstance(self_grade, dict):
        self_grade = {}

    qmap: Dict[str, Dict[str, Any]] = {
        str(q["id"]): q for q in questions_data if isinstance(q, dict) and q.get("id")
    }
    pending = [str(x) for x in (self_grade.get("pending") or [])]
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test has no answers awaiting self-grade.",
        )

    # validate items strictly: known question, still pending, points in 0..marks
    seen: set = set()
    for item in body.items:
        qid = str(item.question_id)
        if qid in seen:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"duplicate question_id {qid}")
        seen.add(qid)
        if qid not in qmap:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"unknown question_id {qid}")
        if qid not in pending:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"question {qid} is not awaiting self-grade")
        try:
            marks = int(qmap[qid].get("marks") or 1)
        except (TypeError, ValueError):
            marks = 1
        if item.points_hit > marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"points_hit for {qid} must be 0..{marks}, got {item.points_hit}",
            )

    auto_points = float(self_grade.get("auto_points") or test.get("score") or 0)
    previous_items = self_grade.get("items") or {}
    merged = dict(previous_items)
    for item in body.items:
        merged[str(item.question_id)] = {
            "points_hit": float(item.points_hit),
            "error_class": item.error_class,
        }

    all_items = [{"question_id": k, **v} for k, v in merged.items()]
    total_marks = int(test.get("total_marks") or 0)
    outcome = hybrid_grading.self_grade_outcome(auto_points, all_items, pending, total_marks)
    remaining = outcome["pending"]
    final_points = float(outcome["final_points"])
    verified_points = {
        k: float(v.get("points_hit") or 0) for k, v in merged.items()
    }
    weak, strong = hybrid_grading.recompute_topics(
        questions_data, answer_map, {}, verified_points
    )

    grading_mode = "self_verified" if not remaining else "pending_self_grade"
    pct = outcome["percentage"]  # None while anything is still pending
    now = datetime.now(timezone.utc).isoformat()
    update: Dict[str, Any] = {
        "score": int(round(final_points)),
        "percentage": pct,
        "grading_mode": grading_mode,
        "self_grade_json": {
            "stage": "verified" if not remaining else "partial",
            "auto_points": auto_points,
            "provisional": self_grade.get("provisional") or {},
            "pending": remaining,
            "items": merged,
            "final_points": final_points,
            "verified_at": now,
        },
        "weak_topics_json": weak,
        "strong_topics_json": strong,
    }
    mock_tests_repo.update(test_id, update)

    if not remaining:
        # Phase 3 learning-guide seed (stub handler now, real impl later).
        try:
            from ..services import job_queue

            job_queue.enqueue("revision_seed", {
                "test_id": str(test.get("id")),
                "user_id": str(current_user["id"]),
                "subject_id": str(test.get("subject_id")),
                "weak_topics": weak,
                "strong_topics": strong,
            })
        except Exception as job_err:
            logger.warning("revision_seed enqueue failed for %s: %s", test_id, job_err)

    answered = sum(1 for qid in qmap if str(answer_map.get(qid, "") or "").strip())
    return {
        "test_id": str(test.get("id")),
        "score_percentage": pct,
        "total_questions": int(test.get("total_questions") or len(qmap)),
        "answers_graded": answered,
        "grading_mode": grading_mode,
        "pending_self_grade": len(remaining),
    }
