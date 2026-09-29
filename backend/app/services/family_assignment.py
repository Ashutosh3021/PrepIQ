"""Question-family assignment (implementation-plan.md 0.4).

Pipeline per question (in order):
  1. exact normalized-hash match against families the user may see (free)
  2. seed keyword match against expert-seeded families (free)
  3. LLM produces a canonical family descriptor (cached — one call ever per
     unique question), then deterministic reuse (hash / Jaccard) or create of
     a user-scoped derived family.

Cross-tenant rule (expert decision D2): derived families carry user_id and are
visible only to their owner; seed families (scope="seed", user_id NULL) are
shared knowledge. The service never raises into an HTTP path — callers get a
stats dict.
"""
from __future__ import annotations

import json
import logging
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.llm_provider import get_llm_client
from app.core.text_utils import strip_fences as _strip_fences
from app.repositories import question_families as families_repo
from app.repositories import questions as questions_repo
from app.repositories import subjects as subjects_repo
from app.services.llm_cache import cached_json

logger = logging.getLogger(__name__)

_SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "seed_question_families.json"

KEYWORD_HIT_RATIO = 0.6
MIN_KEYWORD_HITS = 2
CANONICAL_JACCARD_REUSE = 0.7
_LLM_TEXT_LIMIT = 600
_JACCARD_CAP = 400  # cap visible families considered for canonical reuse

_seeds_cache: Optional[List[Dict[str, Any]]] = None
_seeds_lock = threading.Lock()


# ── text helpers ─────────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    lowered = (text or "").lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", lowered)).strip()


def text_hash(text: str) -> str:
    import hashlib

    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if not inter:
        return 0.0
    return inter / len(a | b)


def _has_keyword(normalized_text: str, keyword: str) -> bool:
    kw = (keyword or "").strip().lower()
    if not kw:
        return False
    return re.search(r"\b" + re.escape(kw) + r"\b", normalized_text) is not None


# ── seed loading ─────────────────────────────────────────────────────────────

def load_seeds() -> List[Dict[str, Any]]:
    global _seeds_cache
    if _seeds_cache is not None:
        return _seeds_cache
    with _seeds_lock:
        if _seeds_cache is not None:
            return _seeds_cache
        try:
            raw = json.loads(_SEED_FILE.read_text(encoding="utf-8"))
            seeds = raw.get("seeds") if isinstance(raw, dict) else raw
            _seeds_cache = [s for s in seeds if isinstance(s, dict)] if isinstance(seeds, list) else []
        except Exception as e:
            logger.warning("seed_question_families load failed: %s", e)
            _seeds_cache = []
        return _seeds_cache


def ensure_seeds() -> int:
    """Insert any seed families not yet present. Idempotent; returns inserted count."""
    inserted = 0
    for seed in load_seeds():
        canonical = str(seed.get("canonical_text") or "").strip()
        if not canonical:
            continue
        try:
            if families_repo.seed_exists(text_hash(canonical)):
                continue
            families_repo.create(
                {
                    "scope": "seed",
                    "canonical_text": canonical,
                    "normalized_hash": text_hash(canonical),
                    "topic": seed.get("topic"),
                    "bloom_level": seed.get("bloom_level"),
                    "command_verb": seed.get("command_verb"),
                    "marks_typical": seed.get("marks_typical"),
                    "difficulty": seed.get("difficulty"),
                    "branch": seed.get("branch"),
                    "seed_source": "seed_question_families.json",
                }
            )
            inserted += 1
        except Exception as e:
            logger.warning("seed insert failed for %r: %s", canonical[:60], e)
    if inserted:
        logger.info("[families] inserted %d seed families", inserted)
    return inserted


# ── matching ─────────────────────────────────────────────────────────────────

def _match_seed(text: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Free keyword-based match of a question against shared seed families."""
    normalized = (text or "").lower()
    best: Optional[Dict[str, Any]] = None
    best_hits = 0
    for seed in load_seeds():
        keywords = [str(k) for k in (seed.get("keywords") or []) if k]
        if not keywords:
            continue
        hits = sum(1 for kw in keywords if _has_keyword(normalized, kw))
        if hits < MIN_KEYWORD_HITS:
            continue
        if hits / len(keywords) >= KEYWORD_HIT_RATIO and hits > best_hits:
            best_hits = hits
            best = seed
    if best is None:
        return None
    return families_repo.find_by_hash(text_hash(str(best["canonical_text"])), user_id)


def _match_canonical(descriptor_text: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Deterministic reuse of an existing visible family by hash or Jaccard."""
    h = text_hash(descriptor_text)
    fam = families_repo.find_by_hash(h, user_id)
    if fam:
        return fam
    desc_tokens = _tokens(descriptor_text)
    best: Optional[Dict[str, Any]] = None
    best_score = 0.0
    for row in families_repo.list_for_user(user_id)[:_JACCARD_CAP]:
        score = _jaccard(desc_tokens, _tokens(str(row.get("canonical_text") or "")))
        if score >= CANONICAL_JACCARD_REUSE and score > best_score:
            best_score = score
            best = row
    return best


# ── LLM descriptor ───────────────────────────────────────────────────────────

_BLOOMS = {"recall", "understand", "apply", "analyze"}


def _fallback_descriptor(question_text: str, unit: str, marks: Any) -> Dict[str, Any]:
    """Deterministic descriptor when the LLM is unavailable (never cached)."""
    lowered = (question_text or "").lower()
    if re.match(r"\s*(define|what is|distinguish|explain|compare)", lowered):
        bloom, verb = "understand", "explain"
    elif re.search(r"\b(prove|show that|analyze|minimi[sz]e|optimize)\b", lowered):
        bloom, verb = "analyze", "analyze"
    else:
        bloom, verb = "apply", "solve"
    try:
        marks_typical = int(marks) if int(marks or 0) > 0 else None
    except (TypeError, ValueError):
        marks_typical = None
    return {
        "canonical_text": question_text.strip()[:400],
        "topic": unit or None,
        "bloom_level": bloom,
        "command_verb": verb,
        "marks_typical": marks_typical,
        "difficulty": "medium",
    }


def _family_client() -> Any:
    """LLM client for capability 'family', or None on any construction error.

    Capability errors (e.g. unregistered capability) or env problems must
    degrade to the deterministic offline fallback — never abort assignment.
    """
    try:
        return get_llm_client("family")
    except Exception as e:
        logger.warning("family LLM client unavailable: %s", e)
        return None


def _llm_descriptor(question_text: str) -> Optional[Dict[str, Any]]:
    client = _family_client()
    if client is None or not client.is_available:
        return None
    prompt = f"""You create a canonical "question family" template for one exam question.

Return ONLY JSON:
{{"canonical_text": "...", "topic": "...", "bloom_level": "recall|understand|apply|analyze", "command_verb": "...", "difficulty": "easy|medium|hard"}}

Rules:
- canonical_text describes the GENERATIVE template (parameterized), not this exact instance.
  Example: "Trace LRU for reference string 1 2 3 1 4 with 3 frames and find faults"
  becomes "Trace page replacement (LRU/FIFO) for a given reference string and compute page faults and hits".
- topic: one short syllabus topic (2-4 words).
- bloom_level: recall (definitions/memorize), understand (explain/compare), apply (compute/design steps), analyze (prove/minimize/optimize).
- command_verb: the single main academic verb (calculate, explain, design, prove, normalize...).
- difficulty: easy | medium | hard.

QUESTION:
{question_text[:_LLM_TEXT_LIMIT]}
"""
    try:
        try:
            parsed = client.generate_json(prompt)
        except Exception:
            raw = client.generate_text(prompt)
            parsed = json.loads(_strip_fences(raw))
        if not isinstance(parsed, dict):
            return None
        canonical = str(parsed.get("canonical_text") or "").strip()
        if not canonical:
            return None
        bloom = str(parsed.get("bloom_level") or "apply").lower()
        if bloom not in _BLOOMS:
            bloom = "apply"
        difficulty = str(parsed.get("difficulty") or "medium").lower()
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "medium"
        try:
            marks_typical = int(parsed.get("marks_typical")) if parsed.get("marks_typical") else None
        except (TypeError, ValueError):
            marks_typical = None
        return {
            "canonical_text": canonical,
            "topic": str(parsed.get("topic") or "").strip() or None,
            "bloom_level": bloom,
            "command_verb": str(parsed.get("command_verb") or "solve").strip().lower(),
            "marks_typical": marks_typical,
            "difficulty": difficulty,
        }
    except Exception as e:
        logger.warning("family descriptor LLM failed: %s", e)
        return None


def _create_derived(descriptor: Dict[str, Any], user_id: str, subject_id: str, branch: Optional[str]) -> str:
    fam = families_repo.create(
        {
            "scope": "user",
            "user_id": user_id,
            "subject_id": subject_id,
            "branch": branch,
            "canonical_text": descriptor["canonical_text"],
            "normalized_hash": text_hash(descriptor["canonical_text"]),
            "topic": descriptor.get("topic"),
            "bloom_level": descriptor.get("bloom_level"),
            "command_verb": descriptor.get("command_verb"),
            "marks_typical": descriptor.get("marks_typical"),
            "difficulty": descriptor.get("difficulty"),
            "seed_source": "llm",
        }
    )
    return str(fam.get("id"))


# ── public API ───────────────────────────────────────────────────────────────

def resolve_branch(subject: Dict[str, Any]) -> Optional[str]:
    blob = " ".join(
        str(subject.get(k) or "") for k in ("exam_name", "exam_type", "code", "name")
    ).lower()
    if "neet" in blob:
        return "neet"
    if "jee" in blob:
        return "jee"
    return "university"


def _assign_one(
    qrow: Dict[str, Any],
    user_id: str,
    subject_id: str,
    branch: Optional[str],
) -> Dict[str, Any]:
    """Returns {"family_id": str|None, "via": str}."""
    text = str(qrow.get("question_text") or "").strip()
    if not text:
        return {"family_id": None, "via": "empty"}

    # 1. exact hash of the raw question (repeated questions across papers)
    fam = families_repo.find_by_hash(text_hash(text), user_id)
    if fam:
        return {"family_id": str(fam.get("id")), "via": "hash"}

    # 2. free seed keyword match
    fam = _match_seed(text, user_id)
    if fam:
        return {"family_id": str(fam.get("id")), "via": "seed"}

    # 3. LLM descriptor (cached per unique question) -> reuse or create
    unit = str(qrow.get("tagged_unit") or qrow.get("unit_name") or "") or None
    try:
        marks = int(qrow.get("marks") or 0)
    except (TypeError, ValueError):
        marks = 0

    def _compute(use_fallback: bool) -> Dict[str, Any]:
        descriptor = _llm_descriptor(text)
        if descriptor is None:
            if not use_fallback:
                # Never cache an LLM failure — raise so cached_json skips it.
                raise RuntimeError("family descriptor LLM unavailable")
            descriptor = _fallback_descriptor(text, unit, marks)
        reuse = _match_canonical(descriptor["canonical_text"], user_id)
        if reuse:
            return {"family_id": str(reuse.get("id")), "via": "llm_reuse"}
        fid = _create_derived(descriptor, user_id, subject_id, branch)
        if descriptor.get("topic") is None and unit:
            families_repo.update(fid, {"topic": unit})
        return {"family_id": fid, "via": "llm_create"}

    client = _family_client()
    if client is not None and client.is_available:
        try:
            result = cached_json(
                "family",
                f"q:{qrow.get('id')}",
                text[:_LLM_TEXT_LIMIT],
                lambda: _compute(use_fallback=False),
            )
            if isinstance(result, dict) and result.get("family_id"):
                return result
        except Exception as e:
            logger.warning("cached family assign failed (%s) — offline fallback", e)
    return _compute(use_fallback=True)


def assign_for_paper(paper_id: str) -> Dict[str, Any]:
    """Job handler entry: assign families to every question of one paper."""
    rows = questions_repo.list_for_paper(paper_id)
    return _assign_rows(rows)


def assign_for_subject(subject_id: str) -> Dict[str, Any]:
    """Backfill entry: assign families to subject questions missing one."""
    rows = [q for q in questions_repo.list_for_subject(subject_id) if not q.get("family_id")]
    return _assign_rows(rows)


def _assign_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    stats = {
        "total": len(rows),
        "assigned": 0,
        "via_hash": 0,
        "via_seed": 0,
        "via_llm_reuse": 0,
        "via_llm_create": 0,
        "failed": 0,
    }
    if not rows:
        return stats

    ensure_seeds()

    subject_id = str(rows[0].get("subject_id") or "")
    subject = subjects_repo.get(subject_id) if subject_id else None
    if not subject:
        stats["failed"] = len(rows)
        stats["error"] = "subject_not_found"
        return stats
    user_id = str(subject.get("user_id") or "")
    if not user_id:
        stats["failed"] = len(rows)
        stats["error"] = "subject_has_no_user"
        return stats
    branch = resolve_branch(subject)

    for row in rows:
        qid = str(row.get("id"))
        if row.get("family_id"):
            stats["assigned"] += 1
            continue
        try:
            outcome = _assign_one(row, user_id, subject_id, branch)
            family_id = outcome.get("family_id")
            if family_id:
                questions_repo.update(qid, {"family_id": str(family_id)})
                stats["assigned"] += 1
                via = str(outcome.get("via") or "")
                if via in ("hash", "seed", "llm_reuse", "llm_create"):
                    stats[f"via_{via}"] += 1
            else:
                stats["failed"] += 1
        except Exception as e:
            stats["failed"] += 1
            logger.warning("family assign failed for question %s: %s", qid, e)

    return stats


def assign_after_upload(subject: Dict[str, Any], paper_id: str) -> Dict[str, Any]:
    """Upload-router hook — never raises into the HTTP path (mirrors unit_tagging)."""
    try:
        return assign_for_paper(paper_id)
    except Exception as e:
        logger.exception("assign_after_upload failed: %s", e)
        return {"skipped": True, "reason": "error", "error": str(e)}
