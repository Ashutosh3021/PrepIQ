"""
Phase 0 tests (implementation-plan.md Part D) — no network, no real DB:
  1. family assignment: hash/seed reuse without LLM; offline fallback
  2. llm_cache: miss/hit, never caches None or exceptions
  3. migration _ensure_columns: idempotent with mocked PyroCore client
  4. job queue: enqueue -> claim -> done / requeue -> failed round-trip

Run from backend/:
  python -m pytest tests/test_phase0.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core import migration  # noqa: E402
from app.core import pyronites_client  # noqa: E402
from app.repositories import llm_cache as llm_cache_repo  # noqa: E402
from app.services import family_assignment as fa  # noqa: E402
from app.services import job_queue  # noqa: E402
from app.services import llm_cache  # noqa: E402


# ── 1. family assignment ──────────────────────────────────────────────────────

def _no_llm(monkeypatch):
    """Make any LLM touch raise immediately."""
    def _boom(*_a, **_k):
        raise AssertionError("LLM must not be called in this test")

    monkeypatch.setattr(fa, "_llm_descriptor", _boom)


def test_hash_reuse_assign_without_llm(monkeypatch):
    _no_llm(monkeypatch)
    existing = {"id": "fam-hash", "canonical_text": "What is OS deadlock?"}
    monkeypatch.setattr(fa.families_repo, "find_by_hash", lambda h, u: existing)

    out = fa._assign_one(
        {"id": "q1", "question_text": "What is OS deadlock?", "family_id": None},
        "u1", "s1", "university",
    )
    assert out == {"family_id": "fam-hash", "via": "hash"}


def test_seed_match_assign_without_llm(monkeypatch):
    _no_llm(monkeypatch)
    seed = {
        "canonical_text": "Trace page replacement for a reference string",
        "keywords": ["lru", "page", "faults", "reference"],
    }
    seed_family = {"id": "fam-seed"}
    monkeypatch.setattr(fa, "load_seeds", lambda: [seed])
    # hash path (raw text) misses; seed path resolves through find_by_hash
    monkeypatch.setattr(
        fa.families_repo,
        "find_by_hash",
        lambda h, u: None if h == fa.text_hash("trace LRU page faults") else seed_family,
    )

    out = fa._assign_one(
        {"id": "q2", "question_text": "trace LRU page faults", "family_id": None},
        "u1", "s1", "university",
    )
    assert out["via"] == "seed"
    assert out["family_id"] == "fam-seed"


def test_offline_fallback_creates_family(monkeypatch):
    """LLM unavailable -> deterministic fallback descriptor, no exception."""
    monkeypatch.setattr(fa, "_llm_descriptor", lambda t: None)
    monkeypatch.setattr(fa, "get_llm_client", lambda cap: SimpleNamespace(is_available=False))
    monkeypatch.setattr(fa.families_repo, "find_by_hash", lambda h, u: None)
    monkeypatch.setattr(fa.families_repo, "list_for_user", lambda u: [])
    created = {}

    def _create(data):
        created.update(data)
        return {"id": "fam-new"}

    monkeypatch.setattr(fa.families_repo, "create", _create)
    monkeypatch.setattr(fa.families_repo, "update", lambda fid, fields: None)

    out = fa._assign_one(
        {"id": "q3", "question_text": "Explain the producer consumer problem", "family_id": None},
        "u1", "s1", "university",
    )
    assert out == {"family_id": "fam-new", "via": "llm_create"}
    assert created.get("scope") == "user"
    assert created.get("user_id") == "u1"
    assert created.get("bloom_level") == "understand"


def test_assign_rows_stats_hash_path(monkeypatch):
    rows = [
        {"id": "q1", "subject_id": "s1", "question_text": "A", "family_id": None},
        {"id": "q2", "subject_id": "s1", "question_text": "B", "family_id": None},
        {"id": "q3", "subject_id": "s1", "question_text": "C", "family_id": "already"},
    ]
    updated = {}
    monkeypatch.setattr(fa, "ensure_seeds", lambda: 0)
    monkeypatch.setattr(fa, "subjects_repo", SimpleNamespace(get=lambda sid: {"user_id": "u1"}))
    monkeypatch.setattr(
        fa, "questions_repo",
        SimpleNamespace(
            list_for_paper=lambda pid: rows,
            update=lambda qid, fields: updated.update({qid: fields}),
        ),
    )
    monkeypatch.setattr(fa, "_llm_descriptor", lambda t: (_ for _ in ()).throw(AssertionError("LLM")))
    fams = {"A": {"id": "fa"}, "B": {"id": "fb"}}
    monkeypatch.setattr(
        fa.families_repo, "find_by_hash",
        lambda h, u: next((v for k, v in fams.items() if h == fa.text_hash(k)), None),
    )

    stats = fa.assign_for_paper("p1")
    assert stats["total"] == 3
    assert stats["assigned"] == 3
    assert stats["via_hash"] == 2
    assert stats["failed"] == 0
    assert updated == {"q1": {"family_id": "fa"}, "q2": {"family_id": "fb"}}


# ── 2. llm_cache ──────────────────────────────────────────────────────────────

def _fake_cache_store(monkeypatch):
    store = {}

    def _get(capability, key):
        return store.get((capability, key))

    def _put(capability, key, response):
        store[(capability, key)] = {"response_json": response}

    monkeypatch.setattr(llm_cache_repo, "get", _get)
    monkeypatch.setattr(llm_cache_repo, "put", _put)
    return store


def test_llm_cache_miss_then_hit(monkeypatch):
    store = _fake_cache_store(monkeypatch)
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        return {"answer": 42}

    first = llm_cache.cached_json("family", "ns", "prompt-1", fn)
    second = llm_cache.cached_json("family", "ns", "prompt-1", fn)
    assert first == {"answer": 42}
    assert second == {"answer": 42}
    assert calls["n"] == 1
    assert len(store) == 1


def test_llm_cache_never_caches_none_or_errors(monkeypatch):
    _fake_cache_store(monkeypatch)

    def boom():
        raise RuntimeError("llm down")

    with pytest.raises(RuntimeError):
        llm_cache.cached_json("family", "ns", "prompt-err", boom)

    assert llm_cache.cached_json("family", "ns", "prompt-none", lambda: None) is None

    # both still miss — a later good call must compute fresh
    good = llm_cache.cached_json("family", "ns", "prompt-err", lambda: {"ok": True})
    assert good == {"ok": True}


def test_prompt_hash_keys_by_capability_and_prompt():
    a = llm_cache.prompt_hash("family", "ns", "p")
    b = llm_cache.prompt_hash("rubric", "ns", "p")
    c = llm_cache.prompt_hash("family", "ns", "p2")
    assert a != b != c


# ── 3. migration _ensure_columns (mocked PyroCore client) ────────────────────

class _FakeTable:
    def __init__(self, fake, name):
        self._fake = fake
        self._name = name

    def schema(self):
        return [{"name": c} for c in self._fake.columns.get(self._name, set())]


class _FakePyroClient:
    def __init__(self, columns_by_table):
        self.columns = {t: set(cols) for t, cols in columns_by_table.items()}
        self.sql_calls = []

    def sql(self, stmt):
        self.sql_calls.append(stmt)
        # ALTER TABLE <t> ADD COLUMN <c> <type>
        parts = stmt.split()
        table = parts[2]
        column = parts[5]
        self.columns.setdefault(table, set()).add(column)
        return {"ok": True}

    def table(self, name):
        return _FakeTable(self, name)


def _all_columns_spec():
    return {(t, c): ty for t, c, ty in migration._COLUMNS}


def test_ensure_columns_idempotent_when_present(monkeypatch):
    spec = _all_columns_spec()
    by_table = {}
    for (t, c) in spec:
        by_table.setdefault(t, set()).add(c)
    fake = _FakePyroClient(by_table)
    monkeypatch.setattr(pyronites_client, "get_pyronites_client", lambda: fake)

    migration._ensure_columns()
    assert fake.sql_calls == []

    # second run is a no-op too
    migration._ensure_columns()
    assert fake.sql_calls == []


def test_ensure_columns_adds_missing_then_skips(monkeypatch):
    spec = _all_columns_spec()
    by_table = {}
    for (t, c) in spec:
        by_table.setdefault(t, set()).add(c)
    # remove two known Phase 0 columns
    by_table["questions"].discard("family_id")
    by_table["mock_tests"].discard("grading_mode")
    fake = _FakePyroClient(by_table)
    monkeypatch.setattr(pyronites_client, "get_pyronites_client", lambda: fake)

    migration._ensure_columns()
    assert len(fake.sql_calls) == 2
    joined = " ".join(fake.sql_calls)
    assert "family_id" in joined and "grading_mode" in joined

    # re-run: everything present now
    before = len(fake.sql_calls)
    migration._ensure_columns()
    assert len(fake.sql_calls) == before


def test_ensure_columns_fails_hard_when_probe_unavailable(monkeypatch):
    def _raise(name):
        raise RuntimeError("schema endpoint down")

    class _BrokenTable:
        def schema(self):
            raise RuntimeError("schema endpoint down")

    class _BrokenClient:
        def sql(self, stmt):
            raise AssertionError("must not ALTER when probe failed")

        def table(self, name):
            return _BrokenTable()

    monkeypatch.setattr(pyronites_client, "get_pyronites_client", lambda: _BrokenClient())
    with pytest.raises(RuntimeError, match="Could not verify columns"):
        migration._ensure_columns()


# ── 4. job queue round-trip ───────────────────────────────────────────────────

class _FakeJobsRepo:
    STATUS_QUEUED = "queued"

    def __init__(self):
        self.rows = {}
        self._n = 0

    def enqueue(self, kind, payload):
        self._n += 1
        row = {
            "id": f"job-{self._n}",
            "kind": kind,
            "payload_json": payload,
            "status": "queued",
            "attempts": 0,
        }
        self.rows[row["id"]] = row
        return dict(row)

    def update(self, job_id, fields):
        self.rows[job_id].update({k: v for k, v in fields.items() if v is not None})
        return dict(self.rows[job_id])

    def claim_next(self):
        for row in self.rows.values():
            if row["status"] == "queued":
                row["status"] = "running"
                return dict(row)
        return None

    def mark_done(self, job_id):
        self.rows[job_id]["status"] = "done"
        return dict(self.rows[job_id])

    def mark_failed(self, job_id, error):
        self.rows[job_id].update({"status": "failed", "last_error": error})
        return dict(self.rows[job_id])

    def requeue(self, job_id, attempts, error):
        self.rows[job_id].update({"status": "queued", "attempts": attempts, "last_error": error})
        return dict(self.rows[job_id])

    def parse_payload(self, job):
        return job.get("payload_json") or {}


@pytest.fixture
def fake_jobs(monkeypatch):
    repo = _FakeJobsRepo()
    monkeypatch.setattr(job_queue, "jobs_repo", repo)
    added = []

    def _register(kind, handler):
        job_queue.register_handler(kind, handler)
        added.append(kind)

    yield repo, _register
    for kind in added:
        job_queue._HANDLERS.pop(kind, None)


def test_job_enqueue_round_trip(fake_jobs):
    repo, register = fake_jobs
    register("test_ok", lambda payload: {"echo": payload.get("x")})

    job = job_queue.enqueue("test_ok", {"x": 1})
    assert repo.rows[job["id"]]["status"] == "queued"

    processed = job_queue.drain_once()
    assert processed == 1
    assert repo.rows[job["id"]]["status"] == "done"


def test_job_failure_requeues_then_fails(fake_jobs):
    repo, register = fake_jobs

    def _always_fails(payload):
        raise ValueError("permanent")

    register("test_fail", _always_fails)
    job = job_queue.enqueue("test_fail", {})

    # attempt 1 -> requeue
    job_queue.drain_once()
    assert repo.rows[job["id"]]["status"] == "queued"
    assert repo.rows[job["id"]]["attempts"] == 1
    # attempt 2 -> requeue
    job_queue.drain_once()
    assert repo.rows[job["id"]]["status"] == "queued"
    assert repo.rows[job["id"]]["attempts"] == 2
    # attempt 3 (== MAX_ATTEMPTS) -> failed
    job_queue.drain_once()
    assert repo.rows[job["id"]]["status"] == "failed"
    assert "permanent" in repo.rows[job["id"]]["last_error"]


def test_job_unknown_kind_fails(fake_jobs):
    repo, _ = fake_jobs
    job = job_queue.enqueue("test_unknown_kind_never_registered", {})
    job_queue.drain_once()
    assert repo.rows[job["id"]]["status"] == "failed"
    assert "unknown job kind" in repo.rows[job["id"]]["last_error"]


def test_drain_empty_queue_is_noop(fake_jobs):
    repo, _ = fake_jobs
    assert job_queue.drain_once() == 0
