"""Exam blueprints (implementation-plan.md 1.1).

A blueprint is a test structure: ordered sections with count/marks/attempt,
difficulty target, question type and optional bloom (cognitive) mix. The test
generator (services/test_generator.py) samples the bank to satisfy it.

Resolve order — resolve()/resolve_with_source():
  1. subject override (subjects.blueprint_json — user-edited, stored validated)
  2. track preset (derived from the subject's exam track)
  3. generic preset

This module is the single source of truth for validation: pydantic schemas in
schemas.py check field types/ranges; every cross-field rule lives here so
stored JSON, presets and request payloads all pass the same validator.
"""
from __future__ import annotations

import copy
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

DIFFICULTIES = ("easy", "medium", "hard", "mixed")
QTYPES = ("any", "mcq", "descriptive")
BLOOMS = ("recall", "understand", "apply", "analyze")

MAX_SECTIONS = 4
MAX_SECTION_QUESTIONS = 30
MAX_TOTAL_QUESTIONS = 30  # matches MockTestRequest num_questions cap
MAX_SECTION_MARKS = 100
MAX_TOTAL_MARKS = 400
MAX_DURATION_MINUTES = 600

# Expert-seeded v1 presets (CSE/Electrical university + NEET-UG government).
PRESETS: Dict[str, Dict[str, Any]] = {
    "generic": {
        "preset": "generic",
        "duration_minutes": 60,
        "sections": [
            {
                "name": "Mixed Practice",
                "count": 10,
                "marks": 5,
                "difficulty": "mixed",
                "qtype": "any",
            }
        ],
    },
    "university_standard": {
        "preset": "university_standard",
        "duration_minutes": 90,
        "sections": [
            {
                "name": "Section A — Short Answer",
                "count": 4,
                "marks": 5,
                "difficulty": "easy",
                "qtype": "any",
                "bloom": ["recall", "understand"],
            },
            {
                "name": "Section B — Long Answer",
                "count": 4,
                "marks": 10,
                "difficulty": "mixed",
                "qtype": "any",
                "bloom": ["apply", "analyze"],
            },
        ],
    },
    "neet_ug": {
        "preset": "neet_ug",
        "duration_minutes": 120,
        "sections": [
            {
                "name": "Section A — MCQ Practice",
                "count": 15,
                "marks": 4,
                "difficulty": "mixed",
                "qtype": "any",
                "bloom": ["recall", "understand"],
            },
            {
                "name": "Section B — Case-based",
                "count": 5,
                "marks": 4,
                "difficulty": "medium",
                "qtype": "any",
                "bloom": ["apply", "analyze"],
            },
        ],
    },
}

PRESET_LABELS: Dict[str, Dict[str, str]] = {
    "generic": {
        "label": "Generic practice",
        "description": "One mixed section — safe default when the exam pattern is unknown.",
    },
    "university_standard": {
        "label": "University standard",
        "description": "Short answers (5 marks, recall/understand) + long answers (10 marks, apply/analyze).",
    },
    "neet_ug": {
        "label": "NEET-UG pattern",
        "description": "MCQ practice + case-based questions, 4 marks each, two sections.",
    },
}


# ── validation ────────────────────────────────────────────────────────────────

def _as_int(value: Any, field: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field} must be an integer, got {value!r}")


def _validate_section(raw: Any, index: int) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"section {index + 1} must be an object")
    where = f"section {index + 1}"

    name = str(raw.get("name") or f"Section {chr(65 + index)}").strip()
    if not name:
        name = f"Section {chr(65 + index)}"

    count = _as_int(raw.get("count"), f"{where}.count")
    if not 1 <= count <= MAX_SECTION_QUESTIONS:
        raise ValueError(f"{where}.count must be 1..{MAX_SECTION_QUESTIONS}, got {count}")

    marks = _as_int(raw.get("marks"), f"{where}.marks")
    if not 1 <= marks <= MAX_SECTION_MARKS:
        raise ValueError(f"{where}.marks must be 1..{MAX_SECTION_MARKS}, got {marks}")

    attempt = raw.get("attempt")
    if attempt is not None:
        attempt = _as_int(attempt, f"{where}.attempt")
        if not 1 <= attempt <= count:
            raise ValueError(f"{where}.attempt must be 1..count ({count}), got {attempt}")

    difficulty = str(raw.get("difficulty") or "mixed").lower()
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"{where}.difficulty must be one of {DIFFICULTIES}, got {difficulty!r}")

    qtype = str(raw.get("qtype") or "any").lower()
    if qtype not in QTYPES:
        raise ValueError(f"{where}.qtype must be one of {QTYPES}, got {qtype!r}")

    bloom_raw = raw.get("bloom") or []
    if not isinstance(bloom_raw, list):
        raise ValueError(f"{where}.bloom must be a list")
    bloom: List[str] = []
    for b in bloom_raw:
        b_lower = str(b).lower()
        if b_lower not in BLOOMS:
            raise ValueError(f"{where}.bloom entries must be one of {BLOOMS}, got {b!r}")
        if b_lower not in bloom:
            bloom.append(b_lower)

    section: Dict[str, Any] = {
        "name": name,
        "count": count,
        "marks": marks,
        "difficulty": difficulty,
        "qtype": qtype,
    }
    if attempt is not None:
        section["attempt"] = attempt
    if bloom:
        section["bloom"] = bloom
    return section


def expand_preset(preset_id: str) -> Dict[str, Any]:
    preset = PRESETS.get(str(preset_id or "").strip().lower())
    if preset is None:
        raise ValueError(
            f"Unknown blueprint preset {preset_id!r}; expected one of {sorted(PRESETS)}"
        )
    return copy.deepcopy(preset)


def validate_blueprint(data: Any) -> Dict[str, Any]:
    """Normalize + validate a blueprint dict. Raises ValueError on bad input."""
    if not isinstance(data, dict):
        raise ValueError("blueprint must be an object")

    preset_id = str(data.get("preset") or "").strip().lower() or None
    sections_raw = data.get("sections")

    if sections_raw is None:
        if preset_id is None:
            raise ValueError("blueprint needs 'sections' or a known 'preset'")
        # preset reference only — expand (keeps stored overrides small)
        expanded = expand_preset(preset_id)
        duration = data.get("duration_minutes")
        if duration is not None:
            expanded["duration_minutes"] = _as_int(duration, "duration_minutes")
        data = expanded
        preset_id = data.get("preset")
        sections_raw = data.get("sections")

    if not isinstance(sections_raw, list) or not sections_raw:
        raise ValueError("blueprint.sections must be a non-empty list")
    if len(sections_raw) > MAX_SECTIONS:
        raise ValueError(f"blueprint.sections supports at most {MAX_SECTIONS} sections")

    sections = [_validate_section(s, i) for i, s in enumerate(sections_raw)]

    total_q = sum(s["count"] for s in sections)
    if total_q > MAX_TOTAL_QUESTIONS:
        raise ValueError(
            f"blueprint total questions {total_q} exceeds cap {MAX_TOTAL_QUESTIONS}"
        )
    total_m = sum(s["count"] * s["marks"] for s in sections)
    if total_m > MAX_TOTAL_MARKS:
        raise ValueError(f"blueprint total marks {total_m} exceeds cap {MAX_TOTAL_MARKS}")

    duration: Optional[int]
    if data.get("duration_minutes") is None:
        duration = None
    else:
        duration = _as_int(data.get("duration_minutes"), "duration_minutes")
        if not 1 <= duration <= MAX_DURATION_MINUTES:
            raise ValueError(
                f"blueprint.duration_minutes must be 1..{MAX_DURATION_MINUTES}, got {duration}"
            )

    out: Dict[str, Any] = {"preset": preset_id or "custom", "sections": sections}
    if duration is not None:
        out["duration_minutes"] = duration
    return out


# ── presets ───────────────────────────────────────────────────────────────────

def list_presets() -> List[Dict[str, Any]]:
    out = []
    for preset_id, bp in PRESETS.items():
        meta = PRESET_LABELS.get(preset_id, {})
        out.append(
            {
                "id": preset_id,
                "label": meta.get("label", preset_id),
                "description": meta.get("description", ""),
                "blueprint": copy.deepcopy(bp),
            }
        )
    return out


# ── resolve ───────────────────────────────────────────────────────────────────

def preset_for_subject(subject: Optional[Dict[str, Any]]) -> Optional[str]:
    """Track preset for a subject, or None when the track is unknown."""
    if not subject:
        return None
    blob = " ".join(
        str(subject.get(k) or "")
        for k in ("exam_name", "exam_type", "code", "name")
    ).lower()
    if "neet" in blob:
        return "neet_ug"
    if str(subject.get("exam_type") or "").strip().lower() == "government":
        return "neet_ug"  # v1 government track ships the NEET-UG pattern
    if str(subject.get("exam_type") or "").strip().lower() == "university":
        return "university_standard"
    return None


def resolve_with_source(subject: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], str]:
    """Returns (validated blueprint, source) — never raises for stored data."""
    if subject:
        override = subject.get("blueprint_json")
        if isinstance(override, str) and override.strip():
            import json

            try:
                override = json.loads(override)
            except Exception:
                override = None
        if isinstance(override, dict) and override:
            try:
                return validate_blueprint(override), "subject"
            except ValueError as e:
                logger.warning(
                    "stored blueprint invalid for subject %s (%s) — falling back",
                    subject.get("id"), e,
                )

    preset_id = preset_for_subject(subject)
    if preset_id is not None:
        try:
            return validate_blueprint({"preset": preset_id}), "preset"
        except ValueError as e:  # pragma: no cover — presets are validated at import
            logger.error("track preset %r invalid: %s", preset_id, e)

    return validate_blueprint({"preset": "generic"}), "generic"


def resolve(subject: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    blueprint, _source = resolve_with_source(subject)
    return blueprint


def blueprint_totals(blueprint: Dict[str, Any]) -> Tuple[int, int]:
    sections = blueprint.get("sections") or []
    total_q = sum(int(s.get("count") or 0) for s in sections if isinstance(s, dict))
    total_m = sum(
        int(s.get("count") or 0) * int(s.get("marks") or 0)
        for s in sections if isinstance(s, dict)
    )
    return total_q, total_m
