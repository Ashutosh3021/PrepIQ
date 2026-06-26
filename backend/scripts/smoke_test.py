"""
PrepIQ Smoke Test
-----------------
Direct (no-HTTP, no-model-loading) test for the prediction and mock test
pipelines.  Uses a stub DB and patches out heavy ML constructors so the
test completes in seconds without GPU/model downloads.
"""
from __future__ import annotations

import sys
import os
import types
import unittest.mock as mock
from datetime import datetime, timezone
from pathlib import Path

# ── Bootstrap ────────────────────────────────────────────────────────────────
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")

print(f"PrepIQ Smoke Test — {datetime.now(timezone.utc).isoformat()}")
print("=" * 60)

PASS = True
results: list[str] = []


# ─────────────────────────────────────────────────────────────────────────────
# Minimal stub DB (no real database needed)
# ─────────────────────────────────────────────────────────────────────────────
class _Q:
    def filter(self, *a, **kw):  return self
    def join(self, *a, **kw):    return self
    def order_by(self, *a, **kw): return self
    def options(self, *a, **kw): return self
    def first(self):  return None
    def all(self):    return []
    def count(self):  return 0

class _DB:
    def query(self, _m): return _Q()
    def add(self, o):    pass
    def commit(self):    pass
    def refresh(self, o): pass


# ─────────────────────────────────────────────────────────────────────────────
# Section 1 — PredictionEngine import
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1] PredictionEngine import …")
try:
    from app.prediction_engine import PredictionEngine
    # Instantiate with Gemini disabled (no API key in smoke-test env)
    with mock.patch.dict(os.environ, {"GEMINI_API_KEY": ""}, clear=False):
        pe = PredictionEngine()
    print(f"    PredictionEngine instantiated  (model={'configured' if pe.model else 'None — no API key'})")
    results.append("prediction_engine_import: PASS")
except Exception as exc:
    import traceback; traceback.print_exc()
    results.append(f"prediction_engine_import: FAIL — {exc}")
    PASS = False
    pe = None


# ─────────────────────────────────────────────────────────────────────────────
# Section 2 — generate_predictions (Tier-0: count==0 path, no ML models)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2] generate_predictions — Tier-0 (no papers) …")
try:
    # Patch heavy constructors before importing PrepIQService
    _noop = mock.MagicMock()
    patches = [
        mock.patch("app.ml_models.enhanced_question_analyzer.EnhancedQuestionAnalyzer.__init__",
                   return_value=None),
        mock.patch("app.ml_models.question_analyzer.QuestionAnalyzer.__init__",
                   return_value=None),
        mock.patch("app.ml.syllabus_analyzer.SyllabusAnalyzer.__init__",
                   return_value=None),
        mock.patch("app.ml.correlation_analyzer.CorrelationAnalyzer.__init__",
                   return_value=None),
        mock.patch("app.ml_engines.study_planner.StudyPlanner.__init__",
                   return_value=None),
        mock.patch("app.chatbot.Chatbot.__init__", return_value=None),
        mock.patch("app.pdf_parser.PDFParser.__init__", return_value=None),
    ]
    for p in patches:
        p.start()

    from app.services import PrepIQService
    svc = PrepIQService.__new__(PrepIQService)
    # Manually set attributes to avoid running __init__ ML loading
    svc.prediction_engine = pe
    svc.chatbot = None
    svc.pdf_parser = None
    svc.question_analyzer = None
    svc.enhanced_question_analyzer = None
    svc.syllabus_analyzer = None
    svc.correlation_analyzer = None
    svc.study_planner = None

    for p in patches:
        p.stop()

    result = svc.generate_predictions(
        db=_DB(),
        subject_id="smoke-subject",
        user_id="smoke-user",
    )

    tier   = result.get("source", "unknown")
    pcount = len(result.get("predictions", []))
    fb     = result.get("fallback_used", False)

    tier_label = {
        "no_data":          "no_papers (Tier-0)",
        "syllabus_fallback": "cold-start (Tier-2)",
    }.get(tier, f"full (Tier-1) source={tier}")

    print(f"    tier used     : {tier_label}")
    print(f"    prediction cnt: {pcount}")
    print(f"    fallback_used : {fb}")

    assert fb is True,                       "Expected fallback_used=True for no-papers path"
    assert isinstance(result["predictions"], list), "predictions must be list"
    assert result.get("subject_id") == "smoke-subject", "subject_id mismatch"

    results.append("generate_predictions: PASS")
    print("    → PASS")

except Exception as exc:
    import traceback; traceback.print_exc()
    results.append(f"generate_predictions: FAIL — {exc}")
    PASS = False


# ─────────────────────────────────────────────────────────────────────────────
# Section 3 — Mock test generation (no-questions path)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3] generate_mock_test — no questions in DB …")
try:
    test_result = svc.generate_mock_test(
        db=_DB(),
        subject_id="smoke-subject",
        user_id="smoke-user",
        num_questions=5,
        difficulty="mixed",
    )

    created   = test_result is not None
    q_count   = len(test_result.get("questions", []))
    err_field = test_result.get("error")

    print(f"    test returned  : {created}")
    print(f"    question count : {q_count}")
    if err_field:
        print(f"    note           : error='{err_field}' (no DB questions — expected)")
    else:
        print(f"    test_id        : {test_result.get('test_id', 'n/a')}")

    assert created, "generate_mock_test must return a dict"

    results.append("generate_mock_test: PASS")
    print("    → PASS")

except Exception as exc:
    import traceback; traceback.print_exc()
    results.append(f"generate_mock_test: FAIL — {exc}")
    PASS = False


# ─────────────────────────────────────────────────────────────────────────────
# Section 4 — Schema aliases & field checks
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4] Schema aliases & Pydantic v2 model_config …")
try:
    from app.schemas import (
        PredictionResponse,
        MockTestCreate,
        MockTestResponse,
        TestSubmitRequest,
        TestSubmitResponse,
    )

    pr_fields = PredictionResponse.model_fields
    assert "fallback_used" in pr_fields, "PredictionResponse missing fallback_used"
    assert "message"       in pr_fields, "PredictionResponse missing message"

    # Verify model_config from_attributes on ORM-bound schemas
    for cls in (PredictionResponse, MockTestResponse):
        cfg = getattr(cls, "model_config", {})
        assert cfg.get("from_attributes"), f"{cls.__name__} missing model_config from_attributes=True"

    print("    PredictionResponse  (fallback_used, message, from_attributes) — OK")
    print("    MockTestCreate      — OK")
    print("    MockTestResponse    (from_attributes)                          — OK")
    print("    TestSubmitRequest   — OK")
    print("    TestSubmitResponse  — OK")

    results.append("schema_aliases: PASS")
    print("    → PASS")

except Exception as exc:
    import traceback; traceback.print_exc()
    results.append(f"schema_aliases: FAIL — {exc}")
    PASS = False


# ─────────────────────────────────────────────────────────────────────────────
# Section 5 — Router registration & prefixes
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5] Router registration …")
try:
    from app.routers.predictions import router as pred_router
    from app.routers.tests       import router as test_router

    pred_paths = [r.path for r in pred_router.routes]
    test_paths = [r.path for r in test_router.routes]

    print(f"    predictions prefix : {pred_router.prefix}")
    print(f"    predictions routes : {pred_paths}")
    print(f"    tests prefix       : {test_router.prefix}")
    print(f"    tests routes       : {test_paths}")

    # Routers are mounted under settings.API_V1_STR (/api/v1) in main.py
    # Their own prefix is /predictions and /tests
    assert pred_router.prefix == "/predictions", \
        f"Expected /predictions, got '{pred_router.prefix}'"
    assert test_router.prefix == "/tests", \
        f"Expected /tests, got '{test_router.prefix}'"

    # Verify key routes exist
    assert any("/generate" in p for p in test_paths), \
        "POST /tests/generate route missing"
    assert any("/submit" in p for p in test_paths), \
        "POST /tests/{id}/submit route missing"
    assert any("/subject/" in p for p in pred_paths), \
        "GET /predictions/subject/{id} route missing"

    results.append("router_registration: PASS")
    print("    → PASS")

except Exception as exc:
    import traceback; traceback.print_exc()
    results.append(f"router_registration: FAIL — {exc}")
    PASS = False


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
for r in results:
    mark = "✓" if "PASS" in r else "✗"
    print(f"  {mark}  {r}")

print()
if PASS:
    print("OVERALL: PASS — all checks succeeded")
    sys.exit(0)
else:
    failed = [r for r in results if "FAIL" in r]
    print(f"OVERALL: FAIL — {len(failed)} check(s) failed")
    sys.exit(1)
