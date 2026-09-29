"""
Hybrid grading tests (implementation-plan.md 1.4) — no network, no real DB.

Part A: pure grading math (auto / provisional / finalisation).
Part B: endpoint contracts via TestClient with mocked repos.

Run from backend/:
  python -m pytest tests/test_hybrid_grading.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.repositories import mock_tests as mock_tests_repo  # noqa: E402
from app.services import hybrid_grading as hg  # noqa: E402
from app.services import job_queue  # noqa: E402
from app.services import rubric_generation  # noqa: E402
from app.routers import tests as tests_router  # noqa: E402

USER = {"id": "u1", "email": "u1@example.com"}


# ── Part A: pure math ─────────────────────────────────────────────────────────

def test_coverage_points_matches_ratio():
    assert hg.coverage_points("deadlock and pacing", ["deadlock", "pacing", "thrash", "set"], 5) == 2.5
    assert hg.coverage_points("", ["a", "b"], 4) == 0.0
    assert hg.coverage_points("x", [], 4) == 0.0
    assert hg.coverage_points("x", ["x"], 0) == 0.0


def _questions():
    return [
        {"id": "a1", "question_text": "Auto right", "correct_answer": "B", "marks": 5, "topic": "OS"},
        {"id": "a2", "question_text": "Auto wrong", "correct_answer": "B", "marks": 5, "topic": "OS"},
        {"id": "a3", "question_text": "Auto skipped", "correct_answer": "B", "marks": 5, "topic": "DB"},
        {"id": "d1", "question_text": "Descriptive answered", "marks": 10, "topic": "CN"},
        {"id": "d2", "question_text": "Descriptive skipped", "marks": 10, "topic": "CN"},
    ]


def _answers():
    return {"a1": "b", "a2": "C", "d1": "the answer covers pacing and thrashing well"}


def _artifacts():
    return {"d1": {"keyword_anchors": ["pacing", "thrashing", "working", "set"]}}


def test_grade_submission_auto_plus_pending():
    graded = hg.grade_submission(_questions(), _answers(), _artifacts())
    assert graded["auto_points"] == 5
    assert graded["correct_count"] == 1
    assert graded["gradeable"] == 3
    assert graded["answers_graded"] == 3
    assert graded["skipped"] == 2
    assert graded["pending"] == ["d1"]
    assert graded["provisional"]["d1"] == 5.0  # 2/4 anchors of 10 marks
    assert graded["strong_topics"] == ["OS"]
    # a3 was skipped, not wrong -> only a2 (OS) is weak
    assert graded["weak_topics"] == ["OS"]


def test_grade_submission_all_unanswered():
    graded = hg.grade_submission(_questions(), {}, _artifacts())
    assert graded["answers_graded"] == 0
    assert graded["pending"] == []
    assert graded["auto_points"] == 0
    assert graded["skipped"] == 5


def test_recompute_topics_with_verification():
    weak, strong = hg.recompute_topics(_questions(), _answers(), {}, {"d1": 9.0})
    assert "CN" in strong
    weak2, strong2 = hg.recompute_topics(_questions(), _answers(), {}, {"d1": 2.0})
    assert "CN" in weak2 and "CN" not in strong2


def test_self_grade_outcome_full_and_partial():
    full = hg.self_grade_outcome(
        auto_points=5, items=[{"question_id": "d1", "points_hit": 8.0}],
        pending=["d1"], total_marks=35,
    )
    assert full["final_points"] == 13.0
    assert full["pending"] == []
    assert full["percentage"] == round(13.0 / 35 * 100, 1)

    partial = hg.self_grade_outcome(
        auto_points=5, items=[{"question_id": "d1", "points_hit": 8.0}],
        pending=["d1", "d2"], total_marks=35,
    )
    assert partial["pending"] == ["d2"]
    assert partial["percentage"] is None


# ── Part B: endpoints ─────────────────────────────────────────────────────────

def _artifacts_for_ids(ids):
    out = {}
    for qid in ids:
        if str(qid) == "d1":
            out[str(qid)] = {
                "mode": "descriptive",
                "model_answer": "Model answer text",
                "rubric_bullets": ["Covers pacing", "Covers thrashing"],
                "keyword_anchors": ["pacing", "thrashing", "working", "set"],
                "needs_review": True,
            }
        elif str(qid) in ("a1", "a2", "a3"):
            out[str(qid)] = {"mode": "descriptive", "keyword_anchors": ["auto"],
                             "rubric_bullets": [], "model_answer": None,
                             "needs_review": True}
    return out


@pytest.fixture()
def store(monkeypatch):
    """In-memory mock_tests rows + captured updates."""
    class _Rows(dict):
        pass

    rows = _Rows()
    updates: list = []

    def _get(tid, uid):
        row = rows.get(str(tid))
        if not row or str(uid) != USER["id"]:
            return None
        if str(row.get("user_id") or USER["id"]) != str(uid):
            return None  # ownership: row belongs to someone else
        return row

    monkeypatch.setattr(mock_tests_repo, "get_for_user", _get)

    def _update(tid, fields):
        updates.append((str(tid), fields))
        if str(tid) in rows:
            rows[str(tid)].update(fields)
        return rows.get(str(tid))

    monkeypatch.setattr(mock_tests_repo, "update", _update)
    monkeypatch.setattr(rubric_generation, "get_artifacts", _artifacts_for_ids)
    monkeypatch.setattr(job_queue, "enqueue",
                        lambda kind, payload: updates.append(("enqueue", {"kind": kind, **payload})))
    rows._updates = updates  # type: ignore[attr-defined]
    return rows


def _make_app(auth: bool = True) -> TestClient:
    app = FastAPI()
    app.include_router(tests_router.router)
    if auth:
        app.dependency_overrides[tests_router.get_current_user] = lambda: USER
    return TestClient(app)


def _pending_test_row():
    return {
        "id": "t1", "user_id": USER["id"], "subject_id": "s1",
        "questions_json": _questions(),
        "total_marks": 35, "total_questions": 5,
        "is_completed": False, "percentage": None, "score": 0,
    }


def test_review_requires_auth():
    client = _make_app(auth=False)
    r = client.get("/tests/t1/review")
    assert r.status_code == 401


def test_review_ownership_404(store):
    store["other"] = dict(_pending_test_row(), id="other", user_id="someone-else")
    client = _make_app()
    r = client.get("/tests/other/review")
    assert r.status_code == 404


def test_review_requires_completed(store):
    store["t1"] = _pending_test_row()
    client = _make_app()
    r = client.get("/tests/t1/review")
    assert r.status_code == 400 and "completed" in r.json()["detail"].lower()


def test_review_returns_rubrics(store):
    row = _pending_test_row()
    row.update({
        "is_completed": True,
        "user_answers_json": _answers(),
        "grading_mode": "pending_self_grade",
        "self_grade_json": {"stage": "provisional", "auto_points": 5,
                            "provisional": {"d1": 5.0}, "pending": ["d1"], "items": {}},
    })
    store["t1"] = row
    client = _make_app()
    r = client.get("/tests/t1/review")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["grading_mode"] == "pending_self_grade"
    assert body["pending_self_grade"] == 1
    assert body["percentage"] is None
    by_id = {i["question_id"]: i for i in body["items"]}
    assert by_id["a1"]["auto_result"] == "correct"
    assert by_id["a2"]["auto_result"] == "incorrect"
    assert by_id["a3"]["auto_result"] == "skipped"
    assert by_id["d1"]["model_answer"] == "Model answer text"
    assert by_id["d1"]["rubric_bullets"] == ["Covers pacing", "Covers thrashing"]
    assert by_id["d1"]["provisional_points"] == 5.0
    assert by_id["d1"]["keyword_anchors"] == ["pacing", "thrashing", "working", "set"]


def test_submit_pending_descriptive(store):
    store["t1"] = _pending_test_row()
    client = _make_app()
    r = client.post("/tests/t1/submit", json={"answers": _answers()})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["grading_mode"] == "pending_self_grade"
    assert body["pending_self_grade"] == 1
    assert body["score_percentage"] is None
    assert body["answers_graded"] == 3
    _, fields = store._updates[-1]
    assert fields["grading_mode"] == "pending_self_grade"
    assert fields["percentage"] is None
    assert fields["self_grade_json"]["stage"] == "provisional"
    assert fields["self_grade_json"]["pending"] == ["d1"]
    assert fields["self_grade_json"]["auto_points"] == 5


def test_submit_auto_only_scores(store):
    row = _pending_test_row()
    row["questions_json"] = [
        {"id": "a1", "question_text": "x", "correct_answer": "B", "marks": 5, "topic": "OS"},
        {"id": "a2", "question_text": "y", "correct_answer": "B", "marks": 5, "topic": "OS"},
    ]
    row["total_marks"] = 10
    store["t1"] = row
    client = _make_app()
    r = client.post("/tests/t1/submit", json={"answers": {"a1": "b", "a2": "C"}})
    body = r.json()
    assert body["grading_mode"] == "auto"
    assert body["pending_self_grade"] == 0
    assert body["score_percentage"] == 50.0


def test_submit_rejects_none_test_id(store):
    client = _make_app()
    r = client.post("/tests/none/submit", json={"answers": {}})
    assert r.status_code == 400


def _completed_store_row():
    row = _pending_test_row()
    row.update({
        "is_completed": True,
        "user_answers_json": _answers(),
        "grading_mode": "pending_self_grade",
        "score": 5,
        "self_grade_json": {"stage": "provisional", "auto_points": 5,
                            "provisional": {"d1": 5.0}, "pending": ["d1"], "items": {}},
    })
    return row


def test_self_grade_full_verification(store):
    store["t1"] = _completed_store_row()
    client = _make_app()
    r = client.post("/tests/t1/self-grade",
                    json={"items": [{"question_id": "d1", "points_hit": 9,
                                     "error_class": "conceptual"}]})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["grading_mode"] == "self_verified"
    assert body["pending_self_grade"] == 0
    assert body["score_percentage"] == round(14 / 35 * 100, 1)

    enq = [u for u in store._updates if u[0] == "enqueue"]
    assert enq and enq[-1][1]["kind"] == "revision_seed"
    fields = [u[1] for u in store._updates if u[0] != "enqueue"][-1]
    assert fields["grading_mode"] == "self_verified"
    assert fields["self_grade_json"]["stage"] == "verified"
    assert fields["self_grade_json"]["items"]["d1"]["error_class"] == "Conceptual"


def test_self_grade_partial_stays_pending(store):
    row = _completed_store_row()
    row["self_grade_json"]["pending"] = ["d1", "d2"]
    row["questions_json"] = _questions() + [
        {"id": "d2", "question_text": "Another descriptive", "marks": 10, "topic": "CN"}
    ]
    row["total_marks"] = 45
    store["t1"] = row
    client = _make_app()
    r = client.post("/tests/t1/self-grade",
                    json={"items": [{"question_id": "d1", "points_hit": 8,
                                     "error_class": "retrieval"}]})
    body = r.json()
    assert body["grading_mode"] == "pending_self_grade"
    assert body["pending_self_grade"] == 1
    assert body["score_percentage"] is None


def test_self_grade_unknown_question_400(store):
    store["t1"] = _completed_store_row()
    client = _make_app()
    r = client.post("/tests/t1/self-grade",
                    json={"items": [{"question_id": "nope", "points_hit": 1,
                                     "error_class": "knowledge"}]})
    assert r.status_code == 400 and "unknown" in r.json()["detail"].lower()


def test_self_grade_points_over_marks_400(store):
    store["t1"] = _completed_store_row()
    client = _make_app()
    r = client.post("/tests/t1/self-grade",
                    json={"items": [{"question_id": "d1", "points_hit": 99,
                                     "error_class": "knowledge"}]})
    assert r.status_code == 400 and "0..10" in r.json()["detail"]


def test_self_grade_bad_error_class_422(store):
    store["t1"] = _completed_store_row()
    client = _make_app()
    r = client.post("/tests/t1/self-grade",
                    json={"items": [{"question_id": "d1", "points_hit": 5,
                                     "error_class": "vibes"}]})
    assert r.status_code == 422


def test_self_grade_not_awaiting_400(store):
    row = _completed_store_row()
    row["self_grade_json"]["pending"] = []
    store["t1"] = row
    client = _make_app()
    r = client.post("/tests/t1/self-grade",
                    json={"items": [{"question_id": "d1", "points_hit": 5,
                                     "error_class": "knowledge"}]})
    assert r.status_code == 400 and "awaiting" in r.json()["detail"].lower()


# ── GET /tests/{id}/results — honest hybrid statuses ─────────────────────────

def test_results_pending_descriptive_honest_status(store):
    store["t1"] = _completed_store_row()
    client = _make_app()
    r = client.get("/tests/t1/results")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["percentage"] is None  # honest: null until self-verified
    assert body["grading_mode"] == "pending_self_grade"
    by_id = {i["question_id"]: i for i in body["question_analysis"]}
    assert by_id["a1"]["status"] == "correct"
    assert by_id["a2"]["status"] == "incorrect"
    assert by_id["a3"]["status"] == "skipped"
    assert by_id["d1"]["status"] == "pending_self_grade"  # NOT "incorrect"
    assert by_id["d1"]["points"] is None
    assert by_id["d2"]["status"] == "skipped"  # unanswered descriptive
    # descriptive answer text must not be uppercased
    assert by_id["d1"]["user_answer"] == _answers()["d1"]
    # fallback topics come from auto items only
    assert body["weak_topics"] == ["OS"]


def test_results_verified_status_points_and_stored_topics(store):
    row = _completed_store_row()
    row.update({
        "grading_mode": "self_verified",
        "percentage": round(14 / 35 * 100, 1),
        "score": 14,
        "self_grade_json": {"stage": "verified", "auto_points": 5, "pending": [],
                            "items": {"d1": {"points_hit": 9.0, "error_class": "Conceptual"}}},
        "weak_topics_json": ["CN"],
        "strong_topics_json": ["OS"],
    })
    store["t1"] = row
    client = _make_app()
    r = client.get("/tests/t1/results")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["percentage"] == round(14 / 35 * 100, 1)
    assert body["grading_mode"] == "self_verified"
    by_id = {i["question_id"]: i for i in body["question_analysis"]}
    assert by_id["d1"]["status"] == "verified"
    assert by_id["d1"]["points"] == 9.0
    # stored (graded) topics preferred over auto-only computation
    assert body["weak_topics"] == ["CN"]
    assert body["strong_topics"] == ["OS"]
