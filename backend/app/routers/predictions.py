"""Predictions API — Pyronites data plane (Fix Phase A)."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, status

from .. import schemas
from ..services.pyronites_auth import get_current_user_from_token
from ..services import prediction_service
from ..repositories import subjects as subjects_repo

router = APIRouter(prefix="/predictions", tags=["Predictions"])


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


def _coerce_full(preds: list) -> List[schemas.PredictedQuestionFull]:
    coerced: List[schemas.PredictedQuestionFull] = []
    for p in preds or []:
        if not isinstance(p, dict):
            continue
        try:
            coerced.append(
                schemas.PredictedQuestionFull(
                    question_number=int(p.get("question_number", 0)),
                    text=str(p.get("text", "")),
                    topic=p.get("topic") or p.get("unit") or "General",
                    unit=p.get("unit") or p.get("topic") or "General",
                    marks=int(p.get("marks", 5)),
                    probability=str(p.get("probability", "moderate")),
                    confidence_score=float(p.get("confidence_score", 0.0)),
                    reasoning=str(p.get("reasoning", "")),
                    source=p.get("source"),
                )
            )
        except Exception:
            continue
    return coerced


@router.get("/subject/{subject_id}", response_model=schemas.SubjectPredictionResponse)
async def get_predictions_for_subject(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    subject = subjects_repo.get_for_user(subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    try:
        result = prediction_service.generate_predictions(current_user["id"], subject_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction generation error: {str(e)}",
        )

    return schemas.SubjectPredictionResponse(
        id=result.get("id"),
        subject_id=subject_id,
        predictions=_coerce_full(result.get("predictions", [])),
        total_marks=int(result.get("total_marks", 0) or 0),
        coverage_percentage=int(result.get("coverage_percentage", 0) or 0),
        unit_coverage=result.get("unit_coverage") or {},
        generated_at=result.get("generated_at"),
        fallback_used=bool(result.get("fallback_used", False)),
        fallback_reason=result.get("fallback_reason"),
        warning=result.get("warning"),
        message=result.get("message"),
        source=result.get("source"),
    )


@router.post("/generate", response_model=schemas.PredictionGenerationResponse)
async def generate_prediction(
    prediction_request: schemas.PredictionRequest,
    current_user: dict = Depends(get_current_user),
):
    subject = subjects_repo.get_for_user(prediction_request.subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    try:
        result = prediction_service.generate_predictions(
            current_user["id"], prediction_request.subject_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating prediction: {str(e)}",
        )

    if result.get("id") is None:
        return {
            "prediction_id": "none",
            "status": "no_data",
            "message": result.get(
                "message",
                "Upload at least one past paper to get predictions.",
            ),
            "progress": 0,
        }

    return {
        "prediction_id": result["id"],
        "status": "completed",
        "message": result.get("warning") or "Prediction generated successfully.",
        "progress": 100,
    }


def _build_prediction_response(result: dict) -> dict:
    predicted_questions = []
    for q in result.get("predicted_questions") or result.get("predictions") or []:
        if not isinstance(q, dict):
            continue
        try:
            predicted_questions.append(
                schemas.PredictedQuestion(
                    question_number=int(q.get("question_number", 0)),
                    text=str(q.get("text", "")),
                    marks=int(q.get("marks", 0)),
                    unit=str(q.get("unit", "")),
                    probability=str(q.get("probability", "low")),
                    reasoning=str(q.get("reasoning", "")),
                )
            )
        except Exception:
            continue
    return {
        "id": result["id"],
        "subject_id": result["subject_id"],
        "predicted_questions": predicted_questions,
        "total_marks": int(result.get("total_marks") or 0),
        "coverage_percentage": int(float(result.get("coverage_percentage") or 0)),
        "unit_coverage": result.get("unit_coverage") or {},
        "generated_at": result["generated_at"],
    }


@router.get("/{prediction_id}", response_model=schemas.PredictionResponse)
async def get_prediction(
    prediction_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = prediction_service.get_prediction(prediction_id, current_user["id"])
        return _build_prediction_response(result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{subject_id}/latest", response_model=schemas.PredictionResponse)
async def get_latest_prediction(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = prediction_service.get_latest_prediction(subject_id, current_user["id"])
        return _build_prediction_response(result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
