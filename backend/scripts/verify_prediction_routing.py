#!/usr/bin/env python3
"""
Offline verification of prediction track routing + response-shape compatibility.

Does not require DB/LLM. Run from backend/:
  python scripts/verify_prediction_routing.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _subject(exam_type: str, exam_name: str, sid: str = "sub-1") -> Dict[str, Any]:
    return {
        "id": sid,
        "user_id": "user-1",
        "name": f"{exam_name} Subject",
        "exam_type": exam_type,
        "exam_name": exam_name,
    }


def test_routing_logic() -> None:
    from app.services import prediction_service as ps

    papers = [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}]
    questions = [
        {"id": "q1", "paper_id": "p1", "question_text": "Q1", "unit_name": "A", "marks": 5},
        {"id": "q2", "paper_id": "p2", "question_text": "Q2", "unit_name": "B", "marks": 5},
    ]

    gov_result = {
        "id": "pred-gov",
        "predictions": [
            {
                "question_number": 1,
                "text": "Unit focus: Human Physiology",
                "topic": "Human Physiology",
                "unit": "Human Physiology",
                "marks": 12,
                "probability": "high",
                "confidence_score": 0.72,
                "reasoning": "recurrence=4, recency_weight=2.1",
                "source": "government_ml",
            }
        ],
        "total_marks": 12,
        "coverage_percentage": 0,
        "unit_coverage": {"Human Physiology": 1},
        "fallback_used": False,
        "source": "government_ml",
        "source_type": "government_ml",
        "model_version": "gov-ml-lr-v1",
    }

    with patch.object(ps, "subjects_repo") as subjects_repo, patch.object(
        ps, "papers_repo"
    ) as papers_repo, patch.object(ps, "questions_repo") as questions_repo, patch.object(
        ps, "_generate_government_predictions", return_value=gov_result
    ) as gov_fn, patch.object(
        ps, "compute_university_topic_features", return_value=[]
    ), patch.object(
        ps, "features_to_prompt_block", return_value="(none)"
    ), patch.object(
        ps, "_call_llm", return_value=[]
    ), patch.object(
        ps, "predictions_repo"
    ) as pred_repo:
        papers_repo.list_completed_for_subject.return_value = papers
        questions_repo.list_for_subject.return_value = questions
        pred_repo.create.return_value = {"id": "pred-uni"}

        subjects_repo.get_for_user.return_value = _subject("government", "NEET")
        out = ps.generate_predictions("user-1", "sub-1")
        assert out["source_type"] == "government_ml", out
        assert gov_fn.called
        print("PASS  government+NEET → government_ml")

        gov_fn.reset_mock()
        subjects_repo.get_for_user.return_value = _subject("government", "JEE")
        out = ps.generate_predictions("user-1", "sub-1")
        assert out["source_type"] == "government_ml"
        assert gov_fn.called
        print("PASS  government+JEE → government_ml")

        gov_fn.reset_mock()
        subjects_repo.get_for_user.return_value = _subject("government", "UPSC")
        try:
            ps.generate_predictions("user-1", "sub-1")
            raise AssertionError("expected ValueError for UPSC")
        except ValueError as e:
            assert "NEET or JEE" in str(e)
            assert not gov_fn.called
            print(f"PASS  government+UPSC rejected: {e}")

        gov_fn.reset_mock()
        subjects_repo.get_for_user.return_value = _subject("university", "Midterm")
        out = ps.generate_predictions("user-1", "sub-1")
        assert not gov_fn.called
        assert out.get("source_type") == "university_llm"
        print("PASS  university → university_llm")

    from app.routers import tests as tests_router

    pool = [
        {"text": "a", "confidence_score": 0.9, "topic": "T1", "marks": 5},
        {"text": "b", "confidence_score": 0.2, "topic": "T2", "marks": 5},
        {"text": "c", "confidence_score": 0.7, "topic": "T3", "marks": 5},
    ]
    selected = tests_router._weighted_sample(pool, 2, weight_key="confidence_score")
    assert len(selected) == 2
    print("PASS  mock-test weighted sample works without source_type")


if __name__ == "__main__":
    test_routing_logic()
    print("\nAll offline routing/contract checks passed.")
