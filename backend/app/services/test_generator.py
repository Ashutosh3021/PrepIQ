"""Blueprint-constrained mock test generator (implementation-plan.md 1.2).

Extracted from routers/tests.py (the former /tests/generate body).

Modes
-----
- **blueprint** (default, ``use_blueprint=True``): samples the question bank
  to fill each blueprint section — counts, per-section difficulty, qtype and
  bloom (soft) targets, cross-section family dedupe, and section-default
  marks stamped into the test copy only (bank rows are never mutated).
  A request-level ``blueprint`` dict overrides the subject blueprint.
- **legacy** (``use_blueprint=False``): previous behaviour preserved —
  predictions-weighted sampling or plain random from the bank.

Contracts preserved
-------------------
- empty selection -> ``test_id="none"`` + ``status="error"`` +
  ``error="insufficient_data"``; the message now also lists per-section
  deficits (plan 1.2).
- choice groups travel inside ``questions_json`` as ``{"group", "attempt",
  "of"}`` on each question of a choice section.
"""
from __future__ import annotations

import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from app import blueprints
from app.repositories import mock_tests as mock_tests_repo
from app.repositories import predictions as predictions_repo
from app.repositories import questions as questions_repo
from app.repositories import question_families as families_repo

logger = logging.getLogger(__name__)


# ── shared helpers (formerly in routers/tests.py) ─────────────────────────────

def normalise_question(raw: Dict[str, Any], order: int) -> Dict[str, Any]:
    import uuid as _uuid

    qid = str(raw.get("id") or raw.get("question_id") or _uuid.uuid4())
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
        # choice-group markers survive GET re-normalisation (plan 1.2)
        "group": raw.get("group"),
        "attempt": raw.get("attempt"),
        "of": raw.get("of"),
    }


def parse_json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        import json

        try:
            return json.loads(value)
        except Exception:
            return value
    return value


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


# ── blueprint mode ────────────────────────────────────────────────────────────

def _question_key(q: Dict[str, Any]) -> str:
    """Dedupe key: family id when known, else normalized text hash."""
    fid = q.get("family_id")
    if fid:
        return f"fam:{fid}"
    from app.services.family_assignment import text_hash

    return "txt:" + text_hash(str(q.get("question_text") or q.get("id") or ""))


def _family_bloom_map(user_id: str) -> Dict[str, str]:
    """family_id -> bloom_level for the user's visible families (soft target)."""
    out: Dict[str, str] = {}
    try:
        for fam in families_repo.list_for_user(user_id):
            fid = fam.get("id")
            bloom = fam.get("bloom_level")
            if fid and bloom:
                out[str(fid)] = str(bloom).lower()
    except Exception as e:
        logger.warning("family bloom map failed (continuing without): %s", e)
    return out


def _effective_difficulty(section: Dict[str, Any], request_difficulty: str) -> str:
    sec = str(section.get("difficulty") or "mixed").lower()
    if sec != "mixed":
        return sec
    return (request_difficulty or "mixed").lower()


def _select_for_section(
    pool: List[Dict[str, Any]],
    section: Dict[str, Any],
    request_difficulty: str,
    seen: set,
    bloom_map: Dict[str, str],
) -> Tuple[List[Dict[str, Any]], int]:
    """Sample one section's questions. Returns (selected, filled_count).

    Filters are soft: an empty filter result falls back to the previous stage
    so a thin bank still produces a usable test instead of failing.
    """
    need = int(section.get("count") or 0)
    candidates = [q for q in pool if _question_key(q) not in seen]
    if need <= 0 or not candidates:
        return [], 0

    # qtype (bank rarely carries options — mcq falls back to all)
    qtype = str(section.get("qtype") or "any").lower()
    if qtype == "mcq":
        mcq = [q for q in candidates if q.get("options")]
        candidates = mcq or candidates
    elif qtype == "descriptive":
        desc = [q for q in candidates if not q.get("options")]
        candidates = desc or candidates

    # difficulty (section first, request difficulty only for mixed sections)
    eff = _effective_difficulty(section, request_difficulty)
    if eff and eff != "mixed":
        filtered = [
            q for q in candidates
            if str(q.get("difficulty") or "").lower() == eff
        ]
        candidates = filtered or candidates

    # bloom — soft priority: fill from matching families first, then the rest
    bloom_targets = section.get("bloom") or []
    primary = candidates
    secondary: List[Dict[str, Any]] = []
    if bloom_targets:
        matched = [
            q for q in candidates
            if str(bloom_map.get(str(q.get("family_id") or "")) or "") in bloom_targets
        ]
        if matched and len(matched) < len(candidates):
            matched_ids = {str(q.get("id")) for q in matched}
            primary = matched
            secondary = [q for q in candidates if str(q.get("id")) not in matched_ids]

    picked = _dedupe_and_sample(primary, need, seen)
    if len(picked) < need and secondary:
        extra = _dedupe_and_sample(
            secondary, need - len(picked), seen | {_question_key(q) for q in picked}
        )
        picked.extend(extra)
    return picked, len(picked)


def _dedupe_and_sample(
    ordered: List[Dict[str, Any]], need: int, seen: set
) -> List[Dict[str, Any]]:
    """Drop same-family duplicates (within this section AND across sections
    already picked), then take up to `need` in priority order."""
    deduped: List[Dict[str, Any]] = []
    local: set = set()
    for q in ordered:
        key = _question_key(q)
        if key in seen or key in local:
            continue
        local.add(key)
        deduped.append(q)
    if not deduped:
        return []
    return random.sample(deduped, min(need, len(deduped)))


def _none_response(subject_id: str, notes: List[str]) -> Dict[str, Any]:
    base_msg = "No questions available for this subject yet. Upload past papers first."
    if notes:
        base_msg = base_msg + " (" + "; ".join(notes) + ")"
    return {
        "test_id": "none",
        "subject_id": subject_id,
        "status": "error",
        "total_questions": 0,
        "total_marks": 0,
        "time_limit_minutes": 0,
        "created_at": datetime.now(timezone.utc),
        "score_percentage": None,
        "questions": [],
        "error": "insufficient_data",
        "message": base_msg,
    }


def _resolve_blueprint(subject: Dict[str, Any], request) -> Dict[str, Any]:
    custom = getattr(request, "blueprint", None)
    if custom:
        if not isinstance(custom, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="blueprint must be an object",
            )
        try:
            return blueprints.validate_blueprint(custom)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return blueprints.resolve(subject)


def generate_blueprint_test(user_id: str, subject: Dict[str, Any], request) -> Dict[str, Any]:
    subject_id = str(subject.get("id"))
    bp = _resolve_blueprint(subject, request)
    difficulty = (getattr(request, "difficulty", None) or "mixed").lower()

    bank = questions_repo.list_for_subject(subject_id)
    bloom_map = _family_bloom_map(user_id)

    seen: set = set()
    picked_per_section: List[Tuple[Dict[str, Any], List[Dict[str, Any]], int]] = []
    for section in bp.get("sections") or []:
        selected, filled = _select_for_section(bank, section, difficulty, seen, bloom_map)
        for q in selected:
            seen.add(_question_key(q))
        picked_per_section.append((section, selected, filled))

    all_selected = [q for _, sel, _ in picked_per_section for q in sel]
    notes = [
        f"{sec.get('name')}: {filled}/{sec.get('count')}"
        for sec, _, filled in picked_per_section
        if filled < int(sec.get("count") or 0)
    ]

    if not all_selected:
        return _none_response(subject_id, notes)

    normalised: List[Dict[str, Any]] = []
    order = 0
    for group_index, (section, selected, _filled) in enumerate(picked_per_section):
        section_default_marks = int(section.get("marks") or 1)
        attempt = section.get("attempt")
        group_of = int(section.get("count") or len(selected))
        is_choice = attempt is not None and int(attempt) < group_of
        for q in selected:
            order += 1
            entry = normalise_question(q, order)
            # unknown-marks questions get the section default — stamp the test
            # copy only; the bank row is never mutated (plan 1.2)
            try:
                bank_marks = int(q.get("marks") or 0)
            except (TypeError, ValueError):
                bank_marks = 0
            if bank_marks <= 0:
                entry["marks"] = section_default_marks
            entry["group"] = group_index
            if is_choice:
                entry["attempt"] = int(attempt)
                entry["of"] = group_of
            normalised.append(entry)

    # duration: explicit request wins; else blueprint; else heuristic
    if "time_limit_minutes" in getattr(request, "model_fields_set", set()):
        duration = int(getattr(request, "time_limit_minutes", 0) or 0) or max(len(normalised) * 3, 1)
    else:
        duration = int(bp.get("duration_minutes") or 0) or max(len(normalised) * 3, 1)

    total_marks = sum(int(q["marks"]) for q in normalised)
    planned_q = sum(int(sec.get("count") or 0) for sec, _, _ in picked_per_section)

    row = mock_tests_repo.create(
        user_id,
        subject_id,
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

    message: Optional[str] = None
    if notes:
        message = (
            f"Filled {len(normalised)}/{planned_q} planned questions — "
            + "; ".join(notes)
            + ". Upload more papers to fill every section."
        )

    return {
        "test_id": str(row.get("id")),
        "subject_id": subject_id,
        "status": "pending",
        "total_questions": len(normalised),
        "total_marks": total_marks,
        "time_limit_minutes": duration,
        "created_at": row.get("created_at") or datetime.now(timezone.utc),
        "score_percentage": None,
        "questions": normalised,
        "message": message,
    }


# ── legacy mode (verbatim behaviour of the old /tests/generate body) ──────────

def generate_legacy_test(user_id: str, subject: Dict[str, Any], request) -> Dict[str, Any]:
    subject_id = str(subject.get("id"))
    num_q = request.num_questions
    difficulty = (request.difficulty or "mixed").lower()
    source = getattr(request, "source", None) or "all_questions"

    selected: List[Dict[str, Any]] = []

    if source == "predictions":
        latest = predictions_repo.get_latest(user_id, subject_id)
        pred_pool: List[Dict[str, Any]] = []
        if latest:
            raw = parse_json_field(latest.get("predicted_questions_json"))
            pred_pool = [p for p in (raw if isinstance(raw, list) else []) if isinstance(p, dict)]
        if difficulty != "mixed" and pred_pool:
            filtered = [
                p for p in pred_pool if str(p.get("difficulty") or "").lower() == difficulty
            ]
            pred_pool = filtered if filtered else pred_pool
        selected = _weighted_sample(pred_pool, num_q, weight_key="confidence_score")
        deficit = num_q - len(selected)
        if deficit > 0:
            bank = questions_repo.list_for_subject(subject_id)
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
        bank = questions_repo.list_for_subject(subject_id)
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
        return _none_response(subject_id, [])

    normalised = [normalise_question(q, i + 1) for i, q in enumerate(selected)]
    total_marks = sum(q["marks"] for q in normalised)
    duration = request.time_limit_minutes or max(len(normalised) * 3, 1)

    row = mock_tests_repo.create(
        user_id,
        subject_id,
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
        "subject_id": subject_id,
        "status": "pending",
        "total_questions": len(normalised),
        "total_marks": total_marks,
        "time_limit_minutes": duration,
        "created_at": row.get("created_at") or datetime.now(timezone.utc),
        "score_percentage": None,
        "questions": normalised,
    }


# ── public API ────────────────────────────────────────────────────────────────

def generate(user_id: str, subject: Dict[str, Any], request) -> Dict[str, Any]:
    """Generate a mock test payload for /tests/generate (implementation-plan 1.2).

    Also kicks the plan 1.3 lazy rubric backfill (<=5 sync, else async) —
    failures there never block generation.
    """
    from app.services.rubric_generation import lazy_for_subject

    try:
        lazy_for_subject(str(subject.get("id")))
    except Exception as e:
        logger.warning("lazy rubric backfill skipped (non-fatal): %s", e)

    if bool(getattr(request, "use_blueprint", True)):
        return generate_blueprint_test(user_id, subject, request)
    return generate_legacy_test(user_id, subject, request)
