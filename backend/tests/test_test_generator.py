"""
Blueprint-constrained test generator tests (implementation-plan.md 1.2) —
no network, no real DB.

Run from backend/:
  python -m pytest tests/test_test_generator.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from fastapi import HTTPException  # noqa: E402

from app.repositories import mock_tests as mock_tests_repo  # noqa: E402
from app.repositories import questions as questions_repo  # noqa: E402
from app.schemas import MockTestRequest  # noqa: E402
from app.services import rubric_generation  # noqa: E402
from app.services import test_generator as tg  # noqa: E402

SUBJECT = {"id": "s1", "subject_name": "OS"}


@pytest.fixture(autouse=True)
def _no_lazy_rubrics(monkeypatch):
    """generate() kicks lazy rubric backfill — keep these tests offline."""
    monkeypatch.setattr(rubric_generation, "lazy_for_subject", lambda sid: {"action": "none"})


def _bank(n: int = 6, difficulty: str = "medium", family_prefix: str = "fam") -> list:
    return [
        {
            "id": f"q{i}",
            "question_text": f"Question {i} — explain deadlock",
            "unit_name": "Concurrency",
            "difficulty": difficulty if i % 2 == 0 else "medium",
            "marks": 0,  # unknown marks -> section default must be stamped
            "correct_answer": None,
            "family_id": f"{family_prefix}-{i}",
        }
        for i in range(n)
    ]


@pytest.fixture()
def created_rows(monkeypatch):
    rows = []

    def _create(user_id, subject_id, fields):
        row = {"id": f"mt-{len(rows) + 1}", "created_at": "2026-01-01T00:00:00Z"}
        row.update(fields)
        rows.append(row)
        return row

    monkeypatch.setattr(mock_tests_repo, "create", _create)
    return rows


def _patch_bank(monkeypatch, bank):
    monkeypatch.setattr(tg.questions_repo, "list_for_subject", lambda sid: list(bank))
    monkeypatch.setattr(tg.families_repo, "list_for_user", lambda uid: [])


# ── blueprint mode ────────────────────────────────────────────────────────────

def test_blueprint_fills_sections_with_group_markers(monkeypatch, created_rows):
    _patch_bank(monkeypatch, _bank(8))
    req = MockTestRequest(
        subject_id="s1",
        blueprint={
            "duration_minutes": 45,
            "sections": [
                {"name": "Sec A", "count": 3, "marks": 2, "attempt": 2},
                {"name": "Sec B", "count": 2, "marks": 5, "difficulty": "medium"},
            ],
        },
    )
    out = tg.generate("u1", SUBJECT, req)

    assert out["test_id"] == "mt-1"  # real id, not "none"
    assert out["total_questions"] == 5
    # marks: bank rows have 0 -> section defaults stamped (2*3 + 5*2 = 16)
    assert out["total_marks"] == 16
    assert out["time_limit_minutes"] == 45  # blueprint duration (no explicit request)

    choice = [q for q in out["questions"] if q.get("group") == 0]
    plain = [q for q in out["questions"] if q.get("group") == 1]
    assert len(choice) == 3 and len(plain) == 2
    assert all(q.get("attempt") == 2 and q.get("of") == 3 for q in choice)
    assert all(q.get("attempt") is None for q in plain)  # no choice -> no markers


def test_bank_rows_never_mutated(monkeypatch, created_rows):
    bank = _bank(4)
    _patch_bank(monkeypatch, bank)
    req = MockTestRequest(
        subject_id="s1",
        blueprint={"sections": [{"count": 2, "marks": 7}]},
    )
    tg.generate("u1", SUBJECT, req)
    # all bank rows still marks=0 (stamping happens on the test copy only)
    assert all(row["marks"] == 0 for row in bank)


def test_family_dedupe_across_sections(monkeypatch, created_rows):
    bank = [
        {"id": "q1", "question_text": "A", "difficulty": "easy", "marks": 1, "family_id": "fam-x"},
        {"id": "q2", "question_text": "A dup", "difficulty": "easy", "marks": 1, "family_id": "fam-x"},
        {"id": "q3", "question_text": "B", "difficulty": "easy", "marks": 1, "family_id": "fam-y"},
    ]
    _patch_bank(monkeypatch, bank)
    req = MockTestRequest(
        subject_id="s1",
        blueprint={"sections": [{"name": "Sec", "count": 3, "marks": 1, "difficulty": "easy"}]},
    )
    out = tg.generate("u1", SUBJECT, req)

    # only 2 unique families available -> partial fill with an honest note
    assert out["test_id"] == "mt-1"
    assert out["total_questions"] == 2
    assert out["message"] and "2/3" in out["message"]
    assert {q["id"] for q in out["questions"]} == {"q1", "q3"}


def test_difficulty_filter_soft_falls_back(monkeypatch, created_rows):
    _patch_bank(monkeypatch, _bank(5, difficulty="medium"))
    req = MockTestRequest(
        subject_id="s1",
        blueprint={"sections": [{"count": 3, "marks": 1, "difficulty": "easy"}]},
    )
    out = tg.generate("u1", SUBJECT, req)
    # no easy questions exist -> falls back to whatever the bank has
    assert out["test_id"] != "none"
    assert out["total_questions"] == 3


def test_empty_bank_none_contract_with_section_note(monkeypatch, created_rows):
    _patch_bank(monkeypatch, [])
    req = MockTestRequest(
        subject_id="s1",
        blueprint={"sections": [{"name": "Section A", "count": 4, "marks": 5}]},
    )
    out = tg.generate("u1", SUBJECT, req)

    assert out["test_id"] == "none"
    assert out["status"] == "error"
    assert out["error"] == "insufficient_data"
    assert out["message"].startswith("No questions available")
    assert "Section A: 0/4" in out["message"]
    assert created_rows == []  # nothing persisted


def test_invalid_custom_blueprint_400(monkeypatch, created_rows):
    _patch_bank(monkeypatch, _bank(3))
    req = MockTestRequest(
        subject_id="s1",
        blueprint={"sections": [{"count": 99, "marks": 5}]},  # over cap
    )
    with pytest.raises(HTTPException) as exc:
        tg.generate("u1", SUBJECT, req)
    assert exc.value.status_code == 400


def test_subject_blueprint_used_when_no_request_override(monkeypatch, created_rows):
    _patch_bank(monkeypatch, _bank(6))
    subject = dict(SUBJECT)
    subject["blueprint_json"] = {
        "preset": "custom",
        "duration_minutes": 30,
        "sections": [{"name": "Solo", "count": 4, "marks": 3}],
    }
    req = MockTestRequest(subject_id="s1")
    out = tg.generate("u1", subject, req)
    assert out["total_questions"] == 4
    assert out["total_marks"] == 12
    assert out["time_limit_minutes"] == 30


def test_explicit_time_limit_beats_blueprint(monkeypatch, created_rows):
    _patch_bank(monkeypatch, _bank(6))
    req = MockTestRequest(
        subject_id="s1",
        time_limit_minutes=25,
        blueprint={"duration_minutes": 90, "sections": [{"count": 3, "marks": 2}]},
    )
    out = tg.generate("u1", SUBJECT, req)
    assert out["time_limit_minutes"] == 25


# ── legacy mode ───────────────────────────────────────────────────────────────

def test_legacy_mode_preserved(monkeypatch, created_rows):
    _patch_bank(monkeypatch, _bank(10))
    req = MockTestRequest(
        subject_id="s1",
        num_questions=4,
        use_blueprint=False,
        source="all_questions",
    )
    out = tg.generate("u1", SUBJECT, req)

    assert out["test_id"] == "mt-1"
    assert out["total_questions"] == 4
    # legacy: request duration default (90), no group markers
    assert out["time_limit_minutes"] == 90
    assert all(q.get("group") is None for q in out["questions"])


def test_legacy_empty_bank_none_contract(monkeypatch, created_rows):
    _patch_bank(monkeypatch, [])
    req = MockTestRequest(subject_id="s1", use_blueprint=False)
    out = tg.generate("u1", SUBJECT, req)
    assert out["test_id"] == "none"
    assert out["error"] == "insufficient_data"
    # legacy message has no section note suffix
    assert out["message"] == (
        "No questions available for this subject yet. Upload past papers first."
    )


def test_bloom_soft_priority(monkeypatch, created_rows):
    bank = _bank(6)
    for i, row in enumerate(bank):
        row["family_id"] = f"fam-{i}"
    _patch_bank(monkeypatch, bank)
    # families map: fam-0/fam-1 are "recall", others "understand"
    monkeypatch.setattr(
        tg.families_repo,
        "list_for_user",
        lambda uid: [
            {"id": "fam-0", "bloom_level": "recall"},
            {"id": "fam-1", "bloom_level": "recall"},
        ] + [{"id": f"fam-{i}", "bloom_level": "understand"} for i in range(2, 6)],
    )
    req = MockTestRequest(
        subject_id="s1",
        blueprint={"sections": [{"count": 2, "marks": 1, "bloom": ["recall"]}]},
    )
    out = tg.generate("u1", SUBJECT, req)
    picked_families = {q["id"].replace("q", "fam-") for q in out["questions"]}
    assert picked_families == {"fam-0", "fam-1"}
