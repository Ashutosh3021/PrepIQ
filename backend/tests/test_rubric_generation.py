"""
Rubric backfill tests (implementation-plan.md 1.3) — no network, no real DB.

Run from backend/:
  python -m pytest tests/test_rubric_generation.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.services import job_queue  # noqa: E402
from app.services import rubric_generation as rg  # noqa: E402

Q = {
    "id": "q1",
    "question_text": "Explain deadlock prevention techniques in operating systems.",
    "unit_name": "Concurrency",
    "marks": 5,
    "family_id": "fam-1",
}


def _client(payload=None, available=True, calls=None):
    def generate_json(prompt):
        if calls is not None:
            calls.append(prompt)
        if isinstance(payload, Exception):
            raise payload
        return payload

    return SimpleNamespace(is_available=available, generate_json=generate_json)


@pytest.fixture()
def store(monkeypatch):
    """In-memory question_rubrics store behind the repo functions."""
    rows: dict = {}

    def _find_by_question(qid):
        return rows.get(str(qid))

    def _find_by_family(fid):
        return next(
            (r for r in rows.values() if str(r.get("family_id") or "") == str(fid)),
            None,
        )

    def _create(data):
        row = {"id": f"r{len(rows) + 1}"}
        row.update(data)
        rows[str(data.get("question_id"))] = row
        return row

    monkeypatch.setattr(rg.rubrics_repo, "find_by_question", _find_by_question)
    monkeypatch.setattr(rg.rubrics_repo, "find_by_family", _find_by_family)
    monkeypatch.setattr(rg.rubrics_repo, "create", _create)
    monkeypatch.setattr(rg.rubrics_repo, "list_for_questions",
                        lambda ids: {i: rows[str(i)] for i in ids if str(i) in rows})
    return rows


@pytest.fixture()
def no_llm_cache(monkeypatch):
    """Pass-through cache: fn() directly (llm_cache tested in Phase 0)."""
    monkeypatch.setattr(rg, "cached_json", lambda cap, ns, prompt, fn: fn())


def _offline(monkeypatch):
    monkeypatch.setattr(rg, "get_llm_client", lambda cap: SimpleNamespace(is_available=False))


# ── generation ────────────────────────────────────────────────────────────────

def test_offline_fallback_creates_keyword_rubric(monkeypatch, store, no_llm_cache):
    _offline(monkeypatch)
    outcome = rg.ensure_for_question(Q)

    assert outcome == "created"
    row = store["q1"]
    assert row["mode"] == "descriptive"
    assert row["needs_review"] is True
    assert row["rubric_json"] and all(isinstance(b, str) for b in row["rubric_json"])
    anchors = row["keywords_json"]
    assert anchors and "deadlock" in anchors  # stopword-filtered content words


def test_llm_success_path(monkeypatch, store, no_llm_cache):
    calls: list = []
    payload = {
        "model_answer": "Deadlock prevention avoids one of Coffman conditions.",
        "rubric_bullets": ["Names mutex/hold-and-wait", "Gives an example"],
        "keyword_anchors": ["deadlock", "prevention"],
    }
    monkeypatch.setattr(
        rg, "get_llm_client",
        lambda cap: _client(payload=payload, calls=calls),
    )
    outcome = rg.ensure_for_question(Q)

    assert outcome == "created"
    assert len(calls) == 1
    row = store["q1"]
    assert row["model_answer"] == payload["model_answer"]
    assert row["rubric_json"] == payload["rubric_bullets"]
    assert row["keywords_json"] == payload["keyword_anchors"]


def test_invalid_llm_payload_falls_back(monkeypatch, store, no_llm_cache):
    calls: list = []
    monkeypatch.setattr(
        rg, "get_llm_client",
        lambda cap: _client(payload={"garbage": True}, calls=calls),
    )
    outcome = rg.ensure_for_question(Q)

    assert outcome == "created"
    assert len(calls) == 1  # attempted once, then deterministic fallback
    row = store["q1"]
    assert row["rubric_json"] and row["model_answer"] is None
    assert row["needs_review"] is True


def test_idempotent_second_run_zero_llm_calls(monkeypatch, store, no_llm_cache):
    calls: list = []
    monkeypatch.setattr(
        rg, "get_llm_client",
        lambda cap: _client(
            payload={"model_answer": "a", "rubric_bullets": ["b"], "keyword_anchors": ["k"]},
            calls=calls,
        ),
    )
    assert rg.ensure_for_question(Q) == "created"
    assert rg.ensure_for_question(Q) == "reused"
    assert rg.ensure_for_question(Q) == "reused"
    assert len(calls) == 1  # plan: one paid call ever per question


def test_family_reuse_copies_without_llm(monkeypatch, store, no_llm_cache):
    # an existing rubric for another question of the same family
    store["q0"] = {
        "id": "r0", "question_id": "q0", "family_id": "fam-1", "mode": "descriptive",
        "model_answer": "shared answer", "rubric_json": ["bullet"], "keywords_json": ["kw"],
    }

    def _boom(cap):
        raise AssertionError("LLM must not be called on family reuse")

    monkeypatch.setattr(rg, "get_llm_client", _boom)
    outcome = rg.ensure_for_question(Q)

    assert outcome == "copied"
    row = store["q1"]
    assert row["model_answer"] == "shared answer"
    assert row["rubric_json"] == ["bullet"]


# ── batch backfill ────────────────────────────────────────────────────────────

def test_backfill_for_paper_stats(monkeypatch, store, no_llm_cache):
    _offline(monkeypatch)
    monkeypatch.setattr(
        rg.questions_repo, "list_for_paper",
        lambda pid: [Q, {"id": "q2", "question_text": "What is paging?"}],
    )
    # q1 already has a rubric -> reused; q2 -> created
    store["q1"] = {"id": "r0", "question_id": "q1", "family_id": "fam-1"}

    stats = rg.backfill_for_paper("p1")
    assert stats == {
        "processed": 2, "created": 1, "reused": 1, "copied": 0,
        "skipped": 0, "failed": 0,
    }


def test_backfill_survives_one_bad_question(monkeypatch, store, no_llm_cache):
    _offline(monkeypatch)
    monkeypatch.setattr(
        rg.questions_repo, "list_for_paper",
        lambda pid: [None, {"id": None}, Q],
    )
    stats = rg.backfill_for_paper("p1")
    assert stats["failed"] == 0 and stats["skipped"] == 2 and stats["created"] == 1


# ── lazy at generate ──────────────────────────────────────────────────────────

def test_lazy_sync_when_missing_le_5(monkeypatch, store, no_llm_cache):
    _offline(monkeypatch)
    monkeypatch.setattr(
        rg.questions_repo, "list_for_subject",
        lambda sid: [{"id": f"q{i}", "question_text": f"Question {i} about kernels"}
                     for i in range(1, 6)],
    )
    enqueued = []
    monkeypatch.setattr(job_queue, "enqueue", lambda kind, payload: enqueued.append((kind, payload)))

    out = rg.lazy_for_subject("s1")
    assert out["action"] == "sync" and out["created"] == 5
    assert enqueued == []


def test_lazy_async_when_missing_gt_5(monkeypatch, store, no_llm_cache):
    _offline(monkeypatch)
    monkeypatch.setattr(
        rg.questions_repo, "list_for_subject",
        lambda sid: [{"id": f"q{i}", "question_text": f"Question {i} about kernels"}
                     for i in range(1, 7)],
    )
    enqueued = []
    monkeypatch.setattr(job_queue, "enqueue", lambda kind, payload: enqueued.append((kind, payload)))

    out = rg.lazy_for_subject("s1")
    assert out["action"] == "async" and out["missing"] == 6
    assert enqueued == [("rubric_backfill", {"subject_id": "s1"})]


def test_lazy_none_when_bank_covered(monkeypatch, store, no_llm_cache):
    store["q1"] = {"id": "r0", "question_id": "q1"}
    monkeypatch.setattr(rg.questions_repo, "list_for_subject", lambda sid: [Q])
    out = rg.lazy_for_subject("s1")
    assert out == {"missing": 0, "action": "none"}


def test_lazy_never_raises(monkeypatch, store):
    def _boom(sid):
        raise RuntimeError("PyroCore down")

    monkeypatch.setattr(rg.questions_repo, "list_for_subject", _boom)
    out = rg.lazy_for_subject("s1")
    assert out["action"] == "error" and "PyroCore" in out["error"]


# ── reads ─────────────────────────────────────────────────────────────────────

def test_get_artifacts_coerces_json_strings(monkeypatch, store):
    import json

    store["q1"] = {
        "id": "r0", "question_id": "q1", "mode": "descriptive",
        "model_answer": None,
        "rubric_json": json.dumps(["b1", "b2"]),
        "keywords_json": json.dumps(["k1"]),
        "needs_review": True,
    }
    out = rg.get_artifacts(["q1"])
    assert out["q1"]["rubric_bullets"] == ["b1", "b2"]
    assert out["q1"]["keyword_anchors"] == ["k1"]
    assert out["q1"]["mode"] == "descriptive" and out["q1"]["needs_review"] is True
