"""
Blueprint tests (implementation-plan.md 1.1) — no network, no DB.

Run from backend/:
  python -m pytest tests/test_blueprints.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app import blueprints  # noqa: E402


# ── validation ────────────────────────────────────────────────────────────────

def test_valid_custom_blueprint_normalizes():
    bp = blueprints.validate_blueprint(
        {
            "preset": "custom",
            "duration_minutes": 60,
            "sections": [
                {"count": 5, "marks": 2},  # name/difficulty/qtype defaulted
            ],
        }
    )
    assert bp["preset"] == "custom"
    assert bp["duration_minutes"] == 60
    section = bp["sections"][0]
    assert section["name"] == "Section A"
    assert section["difficulty"] == "mixed"
    assert section["qtype"] == "any"
    assert section["count"] == 5 and section["marks"] == 2


def test_preset_reference_expands():
    bp = blueprints.validate_blueprint({"preset": "university_standard"})
    assert bp["preset"] == "university_standard"
    assert len(bp["sections"]) == 2
    assert bp["sections"][0]["count"] * bp["sections"][0]["marks"] == 20
    assert bp["sections"][1]["marks"] == 10
    assert bp["duration_minutes"] == 90


def test_unknown_preset_rejected():
    with pytest.raises(ValueError, match="Unknown blueprint preset"):
        blueprints.validate_blueprint({"preset": "does_not_exist"})


def test_neither_sections_nor_preset_rejected():
    with pytest.raises(ValueError, match="needs 'sections' or"):
        blueprints.validate_blueprint({})


def test_attempt_must_not_exceed_count():
    with pytest.raises(ValueError, match="attempt must be 1..count"):
        blueprints.validate_blueprint(
            {"sections": [{"count": 2, "marks": 5, "attempt": 3}]}
        )


def test_too_many_sections_rejected():
    sections = [{"count": 1, "marks": 1} for _ in range(blueprints.MAX_SECTIONS + 1)]
    with pytest.raises(ValueError, match="at most"):
        blueprints.validate_blueprint({"sections": sections})


def test_total_questions_cap():
    sections = [{"count": 15, "marks": 1} for _ in range(3)]  # 45 > 30
    with pytest.raises(ValueError, match="total questions"):
        blueprints.validate_blueprint({"sections": sections})


def test_invalid_bloom_rejected():
    with pytest.raises(ValueError, match="bloom entries"):
        blueprints.validate_blueprint(
            {"sections": [{"count": 1, "marks": 1, "bloom": ["remember"]}]}
        )


def test_invalid_difficulty_rejected():
    with pytest.raises(ValueError, match="difficulty"):
        blueprints.validate_blueprint(
            {"sections": [{"count": 1, "marks": 1, "difficulty": "brutal"}]}
        )


def test_non_dict_rejected():
    with pytest.raises(ValueError, match="must be an object"):
        blueprints.validate_blueprint(["nope"])


# ── resolve priority ──────────────────────────────────────────────────────────

def test_subject_override_wins():
    subject = {
        "id": "s1",
        "exam_type": "government",
        "blueprint_json": {"sections": [{"count": 3, "marks": 7}]},
    }
    bp, source = blueprints.resolve_with_source(subject)
    assert source == "subject"
    assert bp["sections"][0]["marks"] == 7


def test_blueprint_json_as_string_parses():
    subject = {
        "id": "s1",
        "blueprint_json": json.dumps({"preset": "neet_ug"}),
    }
    bp, source = blueprints.resolve_with_source(subject)
    assert source == "subject"
    assert bp["preset"] == "neet_ug"


def test_invalid_stored_blueprint_falls_back_to_track_preset():
    subject = {
        "id": "s1",
        "exam_type": "university",
        "blueprint_json": {"sections": [{"count": 0, "marks": 1}]},  # invalid
    }
    bp, source = blueprints.resolve_with_source(subject)
    assert source == "preset"
    assert bp["preset"] == "university_standard"


def test_track_preset_detection():
    assert blueprints.preset_for_subject({"exam_name": "NEET"}) == "neet_ug"
    assert blueprints.preset_for_subject({"exam_type": "government"}) == "neet_ug"
    assert blueprints.preset_for_subject({"exam_type": "university"}) == "university_standard"
    assert blueprints.preset_for_subject({"name": "DBMS"}) is None
    assert blueprints.preset_for_subject(None) is None


def test_resolve_without_subject_is_generic():
    bp, source = blueprints.resolve_with_source(None)
    assert source == "generic"
    assert bp["preset"] == "generic"


def test_resolve_never_raises_on_garbage_override():
    subject = {"id": "s1", "blueprint_json": "not-json{{{"}
    bp, source = blueprints.resolve_with_source(subject)
    assert source == "generic"  # no track info either
    assert bp["sections"]


# ── presets ───────────────────────────────────────────────────────────────────

def test_list_presets_ships_v1_set():
    presets = blueprints.list_presets()
    ids = {p["id"] for p in presets}
    assert ids == {"generic", "university_standard", "neet_ug"}
    for p in presets:
        assert p["label"] and p["description"]
        # every shipped preset must pass validation
        blueprints.validate_blueprint(p["blueprint"])


def test_list_presets_returns_copies():
    first = blueprints.list_presets()
    first[0]["blueprint"]["sections"][0]["count"] = 999
    second = blueprints.list_presets()
    assert second[0]["blueprint"]["sections"][0]["count"] != 999


def test_blueprint_totals():
    bp = blueprints.validate_blueprint(
        {"sections": [{"count": 4, "marks": 5}, {"count": 4, "marks": 10}]}
    )
    q, m = blueprints.blueprint_totals(bp)
    assert q == 8
    assert m == 60
