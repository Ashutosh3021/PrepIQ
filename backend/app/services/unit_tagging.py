"""
Phase 3 — tag PYQ questions to official syllabus units (government track only).

Each question is classified into exactly one unit from syllabus.extracted_taxonomy,
or left unmatched (tagged_unit=null) when confidence is below threshold or the
model returns unmatched.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.core.llm_provider import get_llm_client
from app.repositories import questions as questions_repo
from app.repositories import subjects as subjects_repo
from app.repositories import syllabus as syllabus_repo
from app.services.syllabus_gate import subject_requires_syllabus_gate, _taxonomy_ready

logger = logging.getLogger(__name__)

# Named constant — tags below this are stored as unmatched (null unit).
TAGGING_CONFIDENCE_THRESHOLD = 0.55

# Soft batch size for multi-question LLM calls (keeps prompts manageable).
_TAG_BATCH_SIZE = 8
_TEXT_SNIPPET = 400


def _strip_fences(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _normalize_taxonomy(tax: Any) -> List[str]:
    if not tax:
        return []
    if isinstance(tax, str):
        try:
            tax = json.loads(tax)
        except Exception:
            return [tax] if tax.strip() else []
    out: List[str] = []
    if isinstance(tax, list):
        for item in tax:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif isinstance(item, dict):
                name = str(item.get("name") or item.get("unit") or item.get("unit_name") or "").strip()
                if name:
                    out.append(name)
    return out


def _match_unit_name(chosen: str, taxonomy: List[str]) -> Optional[str]:
    if not chosen or chosen.strip().lower() in ("unmatched", "none", "unknown", "n/a"):
        return None
    chosen_norm = re.sub(r"\s+", " ", chosen.strip().lower())
    for unit in taxonomy:
        if re.sub(r"\s+", " ", unit.lower()) == chosen_norm:
            return unit
    # Soft prefix / containment match against official names only
    for unit in taxonomy:
        u = re.sub(r"\s+", " ", unit.lower())
        if chosen_norm in u or u in chosen_norm:
            return unit
    return None


def tag_question_text(
    question_text: str,
    taxonomy: List[str],
    *,
    exam_name: Optional[str] = None,
) -> Tuple[Optional[str], float]:
    """
    Classify one question into a taxonomy unit.

    Returns (tagged_unit | None, confidence).
    Unit is None when unmatched or confidence < TAGGING_CONFIDENCE_THRESHOLD.
    """
    text = (question_text or "").strip()
    if not text or not taxonomy:
        return None, 0.0

    client = get_llm_client("extraction")
    if not client.is_available:
        logger.warning("unit tagging skipped — extraction LLM unavailable")
        return None, 0.0

    units_block = "\n".join(f"- {u}" for u in taxonomy)
    prompt = f"""You map an exam question to exactly one syllabus UNIT from the official list.

Exam: {exam_name or "government exam"}

ALLOWED UNITS (choose only from this list, or unmatched):
{units_block}

Rules:
- Return ONLY JSON: {{"unit": "<exact unit name or unmatched>", "confidence": <0.0-1.0>}}
- unit must be copied exactly from the list, or the string "unmatched".
- confidence is how sure you are the question belongs to that unit.
- If unsure, prefer unmatched with lower confidence rather than guessing.

QUESTION:
{text[:_TEXT_SNIPPET * 2]}
"""
    try:
        try:
            parsed = client.generate_json(prompt)
        except Exception:
            raw = client.generate_text(prompt)
            parsed = json.loads(_strip_fences(raw))
        if not isinstance(parsed, dict):
            return None, 0.0
        unit_raw = str(parsed.get("unit") or parsed.get("tagged_unit") or "unmatched")
        try:
            conf = float(parsed.get("confidence") if parsed.get("confidence") is not None else 0.0)
        except (TypeError, ValueError):
            conf = 0.0
        conf = max(0.0, min(1.0, conf))
        matched = _match_unit_name(unit_raw, taxonomy)
        if matched is None or conf < TAGGING_CONFIDENCE_THRESHOLD:
            return None, conf
        return matched, conf
    except Exception as e:
        logger.warning("tag_question_text failed: %s", e)
        return None, 0.0


def _tag_batch(
    items: List[Dict[str, Any]],
    taxonomy: List[str],
    exam_name: Optional[str],
) -> List[Tuple[Optional[str], float]]:
    """Tag a small batch of questions in one LLM call; falls back to per-question."""
    if not items:
        return []
    client = get_llm_client("extraction")
    if not client.is_available:
        return [(None, 0.0) for _ in items]

    units_block = "\n".join(f"- {u}" for u in taxonomy)
    q_block = []
    for i, it in enumerate(items):
        t = str(it.get("question_text") or it.get("text") or "")[:_TEXT_SNIPPET]
        q_block.append(f"{i}. {t}")
    prompt = f"""Map each exam question to exactly one syllabus UNIT from the official list.

Exam: {exam_name or "government exam"}

ALLOWED UNITS (choose only from this list, or unmatched):
{units_block}

Return ONLY a JSON array with one object per question index:
[{{"index": 0, "unit": "<exact unit name or unmatched>", "confidence": 0.0-1.0}}, ...]

Rules:
- unit must be copied exactly from the list, or "unmatched".
- Prefer unmatched over a weak guess.

QUESTIONS:
{chr(10).join(q_block)}
"""
    try:
        try:
            parsed = client.generate_json(prompt, expect_list=True)
            arr = parsed.get("items") if isinstance(parsed, dict) else parsed
            if isinstance(parsed, dict) and isinstance(parsed.get("items"), list):
                arr = parsed["items"]
            elif isinstance(parsed, list):
                arr = parsed
            else:
                arr = None
        except Exception:
            raw = client.generate_text(prompt)
            arr = json.loads(_strip_fences(raw))

        if not isinstance(arr, list):
            raise ValueError("batch tag non-list")

        by_idx: Dict[int, Tuple[Optional[str], float]] = {}
        for row in arr:
            if not isinstance(row, dict):
                continue
            try:
                idx = int(row.get("index"))
            except Exception:
                continue
            unit_raw = str(row.get("unit") or "unmatched")
            try:
                conf = float(row.get("confidence") if row.get("confidence") is not None else 0.0)
            except (TypeError, ValueError):
                conf = 0.0
            conf = max(0.0, min(1.0, conf))
            matched = _match_unit_name(unit_raw, taxonomy)
            if matched is None or conf < TAGGING_CONFIDENCE_THRESHOLD:
                by_idx[idx] = (None, conf)
            else:
                by_idx[idx] = (matched, conf)

        out: List[Tuple[Optional[str], float]] = []
        for i in range(len(items)):
            if i in by_idx:
                out.append(by_idx[i])
            else:
                # Missing index — single-question fallback
                out.append(
                    tag_question_text(
                        str(items[i].get("question_text") or items[i].get("text") or ""),
                        taxonomy,
                        exam_name=exam_name,
                    )
                )
        return out
    except Exception as e:
        logger.warning("batch tagging failed (%s) — per-question fallback", e)
        return [
            tag_question_text(
                str(it.get("question_text") or it.get("text") or ""),
                taxonomy,
                exam_name=exam_name,
            )
            for it in items
        ]


def _persist_tag(question_id: str, unit: Optional[str], conf: float) -> None:
    fields = {
        "tagged_unit": unit,
        "tagging_confidence": float(conf),
    }
    try:
        questions_repo.update(question_id, fields)
    except Exception as e:
        # Columns may be missing on older questions tables
        msg = str(e)
        if "tagged_unit" in msg or "Identifier" in msg:
            logger.warning(
                "Could not persist tagged_unit (add columns on questions table): %s", e
            )
        else:
            logger.warning("persist tag failed for %s: %s", question_id, e)


def tag_questions_for_subject(
    subject_id: str,
    *,
    question_ids: Optional[List[str]] = None,
    paper_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tag government-track questions for a subject. No-op for university subjects.

    If question_ids is set, only those rows are tagged.
    If paper_id is set, only questions for that paper.
    Otherwise all subject questions (backfill).
    """
    subject = subjects_repo.get(subject_id) or {}
    if not subject_requires_syllabus_gate(subject):
        return {
            "skipped": True,
            "reason": "not_government",
            "subject_id": subject_id,
            "tagged": 0,
            "unmatched": 0,
            "total": 0,
        }

    syl = syllabus_repo.get_for_subject(subject_id)
    taxonomy = _normalize_taxonomy((syl or {}).get("extracted_taxonomy"))
    if not _taxonomy_ready(taxonomy):
        return {
            "skipped": True,
            "reason": "no_taxonomy",
            "subject_id": subject_id,
            "tagged": 0,
            "unmatched": 0,
            "total": 0,
            "message": "Syllabus taxonomy missing — complete Phase 2 extraction first.",
        }

    if question_ids:
        rows = []
        for qid in question_ids:
            row = questions_repo.get(qid)
            if row and str(row.get("subject_id")) == str(subject_id):
                rows.append(row)
    elif paper_id:
        rows = questions_repo.list_for_paper(paper_id)
    else:
        rows = questions_repo.list_for_subject(subject_id)

    exam_name = str(subject.get("exam_name") or "")
    tagged = 0
    unmatched = 0
    samples: List[Dict[str, Any]] = []

    for start in range(0, len(rows), _TAG_BATCH_SIZE):
        batch = rows[start : start + _TAG_BATCH_SIZE]
        results = _tag_batch(batch, taxonomy, exam_name)
        for row, (unit, conf) in zip(batch, results):
            qid = str(row.get("id"))
            _persist_tag(qid, unit, conf)
            if unit:
                tagged += 1
            else:
                unmatched += 1
            if len(samples) < 12:
                samples.append(
                    {
                        "id": qid,
                        "text": str(row.get("question_text") or "")[:160],
                        "tagged_unit": unit,
                        "tagging_confidence": conf,
                    }
                )

    return {
        "skipped": False,
        "subject_id": subject_id,
        "taxonomy_units": len(taxonomy),
        "total": len(rows),
        "tagged": tagged,
        "unmatched": unmatched,
        "threshold": TAGGING_CONFIDENCE_THRESHOLD,
        "samples": samples,
    }


def tag_after_upload(subject: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
    """Hook for upload routers — government only; never raises into the HTTP path."""
    try:
        if not subject_requires_syllabus_gate(subject):
            return {"skipped": True, "reason": "not_government"}
        return tag_questions_for_subject(str(subject.get("id")), paper_id=paper_id)
    except Exception as e:
        logger.exception("tag_after_upload failed: %s", e)
        return {"skipped": True, "reason": "error", "error": str(e)}
