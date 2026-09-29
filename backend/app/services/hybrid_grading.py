"""Hybrid grading math (implementation-plan.md 1.4 / D4).

Zero LLM cost at submit:

- **auto**          — questions carrying ``correct_answer`` grade by exact match.
- **provisional**   — answered descriptive questions get a deterministic
  keyword-coverage score (never final) and enter ``pending_self_grade``.
- **finalisation**  — the student self-verifies (points + error class); the
  score becomes ``Self-Verified``. Percentages stay ``None`` until every
  pending item is verified.

Pure functions — routers handle HTTP, this module never touches the DB.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.services.rubric_generation import extract_keywords

# Descriptive answers at >=60% of the question's marks count as strong.
STRONG_RATIO = 0.6


def coverage_points(answer: str, anchors: Optional[List[str]], marks: int) -> float:
    """Deterministic keyword-coverage provisional score (0..marks)."""
    if not anchors or marks <= 0:
        return 0.0
    hay = (answer or "").lower()
    matched = sum(1 for a in anchors if a and str(a).lower() in hay)
    return round(marks * (matched / len(anchors)), 1)


def _is_correct(user_answer: str, correct: Any) -> bool:
    return bool(user_answer) and user_answer.strip().lower() == str(correct).strip().lower()


def grade_submission(
    questions_data: List[Dict[str, Any]],
    answer_map: Dict[str, str],
    artifacts: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Full submit-time grading pass. Pure — see module docstring."""
    answers_graded = 0
    gradeable = 0
    correct_count = 0
    auto_points = 0.0
    pending: List[str] = []
    provisional: Dict[str, float] = {}
    weak: List[str] = []
    strong: List[str] = []

    for q in questions_data:
        if not isinstance(q, dict):
            continue
        qid = str(q.get("id") or "")
        topic = str(q.get("topic") or q.get("unit") or "General")
        try:
            marks = int(q.get("marks") or 1)
        except (TypeError, ValueError):
            marks = 1
        user_raw = str(answer_map.get(qid, "") or "").strip()
        answered = bool(user_raw)
        if answered:
            answers_graded += 1

        correct = q.get("correct_answer")
        if correct:
            # auto exact-match path (preserves pre-Phase-1 behaviour)
            gradeable += 1
            if not answered:
                continue
            if _is_correct(user_raw, correct):
                correct_count += 1
                auto_points += marks
                if topic not in strong:
                    strong.append(topic)
            elif topic not in weak:
                weak.append(topic)
            continue

        # descriptive with no stored answer key -> self-verify flow
        if not answered:
            continue
        anchors = (artifacts.get(qid) or {}).get("keyword_anchors") or []
        provisional[qid] = coverage_points(user_raw, anchors, marks)
        pending.append(qid)

    skipped = sum(
        1 for q in questions_data
        if isinstance(q, dict) and not str(answer_map.get(str(q.get("id") or ""), "") or "").strip()
    )

    return {
        "answers_graded": answers_graded,
        "gradeable": gradeable,
        "correct_count": correct_count,
        "auto_points": auto_points,
        "skipped": skipped,
        "pending": pending,
        "provisional": provisional,
        "weak_topics": weak[:5],
        "strong_topics": strong[:5],
    }


def recompute_topics(
    questions_data: List[Dict[str, Any]],
    answer_map: Dict[str, str],
    artifacts: Dict[str, Dict[str, Any]],
    verified_points: Optional[Dict[str, float]] = None,
) -> Tuple[List[str], List[str]]:
    """Weak/strong topics. ``verified_points`` = self-grade outcomes; without
    it, descriptive questions are excluded (submit-time behaviour)."""
    verified = verified_points or {}
    weak: List[str] = []
    strong: List[str] = []

    for q in questions_data:
        if not isinstance(q, dict):
            continue
        qid = str(q.get("id") or "")
        topic = str(q.get("topic") or q.get("unit") or "General")
        try:
            marks = int(q.get("marks") or 1)
        except (TypeError, ValueError):
            marks = 1
        user_raw = str(answer_map.get(qid, "") or "").strip()
        correct = q.get("correct_answer")

        if correct:
            if not user_raw:
                continue
            bucket = strong if _is_correct(user_raw, correct) else weak
        elif qid in verified and user_raw:
            ratio = (float(verified[qid]) / marks) if marks else 0.0
            bucket = strong if ratio >= STRONG_RATIO else weak
        else:
            continue
        if topic not in bucket:
            bucket.append(topic)

    return weak[:5], strong[:5]


def self_grade_outcome(
    auto_points: float,
    items: List[Dict[str, Any]],
    pending: List[str],
    total_marks: int,
) -> Dict[str, Any]:
    """Combine auto points + student-verified points (plan 1.4 finalisation).

    Returns final_points, remaining pending ids, percentage (None while any
    pending item is still unverified).
    """
    points = sum(float(it.get("points_hit") or 0) for it in items)
    verified_ids = [str(it.get("question_id") or "") for it in items]
    remaining = [qid for qid in pending if qid not in verified_ids]
    final_points = round(auto_points + points, 1)
    percentage: Optional[float] = None
    if not remaining and total_marks > 0:
        percentage = round(final_points / total_marks * 100, 1)
    return {
        "final_points": final_points,
        "verified_points": {str(it.get("question_id")): float(it.get("points_hit") or 0) for it in items},
        "pending": remaining,
        "percentage": percentage,
    }


def fallback_anchors(question_text: str) -> List[str]:
    return extract_keywords(question_text or "", limit=8)
