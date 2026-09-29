"""Rubric / distractor generation (implementation-plan.md 1.3).

Produces the gradeability artifact for every bank question:

- **mcq**       -> ``{options[4], correct_index, distractor_rationale[3]}``
- **descriptive`` -> ``{model_answer, rubric_bullets, keyword_anchors}``

LLM calls go through ``llm_cache.cached_json`` (capability ``rubric``) keyed by
the normalized question text — one paid call ever per question/family. When no
LLM is configured (free-tier / offline), a deterministic keyword rubric is
generated instead; every row ships with ``needs_review=true`` for the Phase 4
audit.

Trigger points:
- job ``rubric_backfill`` after upload (papers.py enqueues per paper),
- lazy at ``/tests/generate``: <=5 missing -> sync, else async job.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.llm_provider import get_llm_client
from app.core.text_utils import strip_fences
from app.repositories import questions as questions_repo
from app.repositories import question_rubrics as rubrics_repo
from app.services.llm_cache import cached_json

logger = logging.getLogger(__name__)

SYNC_LIMIT = 5  # plan 1.3: sync batch <=5 at generate, else async

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "was", "were",
    "has", "have", "had", "not", "but", "its", "into", "using", "used", "use",
    "what", "which", "when", "where", "who", "how", "why", "describe",
    "explain", "define", "compare", "list", "give", "write", "any", "all",
    "your", "they", "them", "their", "there", "than", "then", "also", "such",
    "may", "can", "could", "would", "should", "must", "will", "shall",
    "one", "two", "three", "between", "among", "each", "every", "some",
    "problem", "question", "marks", "mark", "suitable", "following",
}


# ── text helpers ──────────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def extract_keywords(text: str, limit: int = 8) -> List[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z-]{2,}", (text or "").lower())
    seen: List[str] = []
    for tok in tokens:
        if tok in _STOPWORDS or tok in seen:
            continue
        seen.append(tok)
        if len(seen) >= limit:
            break
    return seen


def detect_mode(question: Dict[str, Any]) -> str:
    qtype = str(question.get("question_type") or "").lower()
    if qtype == "mcq" or question.get("options"):
        return "mcq"
    return "descriptive"


# ── rubric shapes ─────────────────────────────────────────────────────────────

def _fallback_descriptive(question: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic keyword rubric — honest about being unscored by an LLM."""
    keywords = extract_keywords(str(question.get("question_text") or ""))
    bullets = [f"Addresses {kw}" for kw in keywords[:3]]
    if not bullets:
        bullets = ["Answers the question with relevant detail"]
    return {
        "model_answer": None,
        "rubric_bullets": bullets,
        "keyword_anchors": keywords,
    }


def _fallback_mcq(question: Dict[str, Any]) -> Dict[str, Any]:
    options = question.get("options")
    return {
        "options": list(options) if isinstance(options, list) else None,
        "correct_index": None,
        "distractor_rationale": None,
    }


def _prompt_for(question: Dict[str, Any], mode: str, bullets: int) -> str:
    text = str(question.get("question_text") or "").strip()
    topic = str(question.get("unit_name") or question.get("tagged_unit") or "General")
    if mode == "mcq":
        return (
            "You are an exam setter. For the question below, write one correct "
            "option and three plausible distractors (misapplied formula, sign "
            "flip, or common misconception). Return strict JSON only: "
            '{"options": [correct, d1, d2, d3], "correct_index": 0, '
            '"distractor_rationale": ["why d1 is tempting", "why d2", "why d3"]}\n'
            f"Topic: {topic}\nQuestion: {text}"
        )
    return (
        "You are an exam marker. For the descriptive question below, write a "
        f"concise model answer and {bullets} grading rubric bullets (each bullet "
        "is a point the answer must cover to earn marks), plus short keyword "
        "anchors. Return strict JSON only: "
        '{"model_answer": "...", "rubric_bullets": ["...", "..."], '
        '"keyword_anchors": ["...", "..."]}\n'
        f"Topic: {topic}\nQuestion: {text}"
    )


def _validate_llm_payload(mode: str, payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"rubric LLM payload is not an object: {type(payload)}")
    if mode == "mcq":
        options = payload.get("options")
        idx = payload.get("correct_index")
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError("mcq rubric needs options[4]")
        if not isinstance(idx, int) or not (0 <= idx <= 3):
            raise ValueError("mcq rubric needs correct_index 0..3")
        return payload
    bullets = payload.get("rubric_bullets")
    if not isinstance(bullets, list) or not bullets:
        raise ValueError("descriptive rubric needs non-empty rubric_bullets")
    payload.setdefault("keyword_anchors", [])
    payload.setdefault("model_answer", None)
    return payload


def _llm_rubric(question: Dict[str, Any], mode: str, bullets: int) -> Dict[str, Any]:
    text = normalize_text(str(question.get("question_text") or ""))
    prompt = _prompt_for(question, mode, bullets)

    def _call() -> Any:
        client = get_llm_client("rubric")
        if client is None or not client.is_available:
            # Raise so cached_json never stores a failed/offline attempt.
            raise RuntimeError("rubric LLM unavailable")
        try:
            raw = client.generate_json(prompt)
        except Exception:
            import json

            raw = json.loads(strip_fences(client.generate_text(prompt)))
        return _validate_llm_payload(mode, raw)

    result = cached_json("rubric", "v1", prompt, _call)
    if result is None:
        raise RuntimeError("rubric LLM returned nothing")
    return _validate_llm_payload(mode, result)


# ── per-question ensure ───────────────────────────────────────────────────────

def _bullet_budget(question: Dict[str, Any]) -> int:
    try:
        marks = int(question.get("marks") or 0)
    except (TypeError, ValueError):
        marks = 0
    if marks <= 0:
        return 3
    return max(2, min(marks, 6))


def _create_row(
    question: Dict[str, Any],
    mode: str,
    artifacts: Dict[str, Any],
    copied_from_family: bool,
) -> Dict[str, Any]:
    row = {
        "question_id": str(question.get("id")),
        "family_id": question.get("family_id"),
        "mode": mode,
        "model_answer": artifacts.get("model_answer"),
        "rubric_json": artifacts.get("rubric_bullets")
        if mode == "descriptive" else artifacts,
        "keywords_json": artifacts.get("keyword_anchors"),
        "options_json": artifacts.get("options") if mode == "mcq" else None,
        "needs_review": True,  # plan 1.3: Phase 4 audit
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    return rubrics_repo.create(row)


def ensure_for_question(question: Dict[str, Any]) -> str:
    """Create the rubric row if missing. Returns created|reused|copied."""
    qid = str(question.get("id") or "")
    if not qid:
        return "skipped"
    existing = rubrics_repo.find_by_question(qid)
    if existing:
        return "reused"

    # family-level reuse: one LLM call per family, copies stay per-question
    family_id = question.get("family_id")
    if family_id:
        family_row = rubrics_repo.find_by_family(str(family_id))
        if family_row:
            _create_row(
                question,
                str(family_row.get("mode") or "descriptive"),
                _artifacts_from_row(family_row),
                copied_from_family=True,
            )
            return "copied"

    mode = detect_mode(question)
    bullets = _bullet_budget(question)
    try:
        artifacts = _llm_rubric(question, mode, bullets)
    except Exception as e:
        logger.debug("rubric LLM miss for %s (%s) — deterministic fallback", qid, e)
        artifacts = (
            _fallback_mcq(question) if mode == "mcq" else _fallback_descriptive(question)
        )

    _create_row(question, mode, artifacts, copied_from_family=False)
    return "created"


def _artifacts_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    mode = str(row.get("mode") or "descriptive")
    rubric = row.get("rubric_json")
    if isinstance(rubric, str):
        from app.services.test_generator import parse_json_field

        rubric = parse_json_field(rubric)
    keywords = row.get("keywords_json")
    if isinstance(keywords, str):
        from app.services.test_generator import parse_json_field

        keywords = parse_json_field(keywords)
    options = row.get("options_json")
    if isinstance(options, str):
        from app.services.test_generator import parse_json_field

        options = parse_json_field(options)

    if mode == "mcq":
        return {
            "options": options,
            "correct_index": (rubric or {}).get("correct_index")
            if isinstance(rubric, dict) else None,
            "distractor_rationale": (rubric or {}).get("distractor_rationale")
            if isinstance(rubric, dict) else None,
            "model_answer": row.get("model_answer"),
            "rubric_bullets": None,
            "keyword_anchors": keywords,
        }
    return {
        "model_answer": row.get("model_answer"),
        "rubric_bullets": rubric if isinstance(rubric, list) else None,
        "keyword_anchors": keywords if isinstance(keywords, list) else None,
        "options": options,
    }


# ── batch backfill ────────────────────────────────────────────────────────────

def _run_batch(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    stats = {"processed": 0, "created": 0, "reused": 0, "copied": 0,
             "skipped": 0, "failed": 0}
    for q in questions:
        if not isinstance(q, dict) or not q.get("id"):
            stats["skipped"] += 1
            continue
        try:
            outcome = ensure_for_question(q)
            stats["processed"] += 1
            stats[outcome] = stats.get(outcome, 0) + 1
        except Exception as e:
            stats["failed"] += 1
            logger.error("rubric ensure failed for %s: %s", q.get("id"), e)
    return stats


def backfill_for_paper(paper_id: str) -> Dict[str, Any]:
    """Job handler target (plan 1.3): rubrics for every question of a paper."""
    return _run_batch(questions_repo.list_for_paper(str(paper_id)))


def backfill_for_subject(subject_id: str, limit: Optional[int] = None) -> Dict[str, Any]:
    questions = questions_repo.list_for_subject(str(subject_id))
    if limit is not None:
        questions = questions[: int(limit)]
    return _run_batch(questions)


def lazy_for_subject(subject_id: str) -> Dict[str, Any]:
    """Called from /tests/generate: <=5 missing rubrics -> fill sync,
    more -> enqueue async (plan 1.3). Never raises."""
    try:
        questions = questions_repo.list_for_subject(str(subject_id))
        missing = [
            q for q in questions
            if isinstance(q, dict)
            and q.get("id")
            and rubrics_repo.find_by_question(str(q["id"])) is None
        ]
        if not missing:
            return {"missing": 0, "action": "none"}
        if len(missing) <= SYNC_LIMIT:
            stats = _run_batch(missing)
            stats.update({"missing": len(missing), "action": "sync"})
            return stats
        from app.services import job_queue

        job_queue.enqueue("rubric_backfill", {"subject_id": str(subject_id)})
        return {"missing": len(missing), "action": "async"}
    except Exception as e:
        # Rubrics are an enhancement — generation must always proceed.
        logger.warning("lazy rubric backfill failed for %s: %s", subject_id, e)
        return {"action": "error", "error": str(e)}


# ── reads (grading / review) ──────────────────────────────────────────────────

def get_artifacts(question_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """question_id -> {mode, model_answer, rubric_bullets, keyword_anchors,
    options, correct_index, needs_review} (JSON-coerced)."""
    out: Dict[str, Dict[str, Any]] = {}
    for qid, row in rubrics_repo.list_for_questions(question_ids).items():
        artifacts = _artifacts_from_row(row)
        artifacts["mode"] = str(row.get("mode") or "descriptive")
        artifacts["needs_review"] = bool(row.get("needs_review"))
        out[qid] = artifacts
    return out
