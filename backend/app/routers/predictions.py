import json
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas
from ..dependencies import get_prepiq_service
from ..services.supabase_first_auth import get_current_user_from_token


async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)


router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"]
)


@router.get("/subject/{subject_id}", response_model=schemas.SubjectPredictionResponse)
async def get_predictions_for_subject(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate (or retrieve) predictions for a subject.

    Always returns HTTP 200.  Inspect ``fallback_used`` and ``message`` to
    decide what the frontend should display.

    * 0 papers  → empty predictions list with instructional message
    * 1-2 papers → Gemini cold-start from subject knowledge, warning banner
    * 3+ papers  → full ML + Gemini pipeline (ML fallback if Gemini fails)
    """
    # Verify subject belongs to the authenticated user
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.user_id == current_user["id"],
    ).first()
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    service = get_prepiq_service()
    try:
        result = service.generate_predictions(
            db=db,
            subject_id=subject_id,
            user_id=current_user["id"],
        )
    except Exception as e:
        # Should not reach here under normal operation, but guard defensively
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction generation error: {str(e)}",
        )

    # Normalise predictions to SubjectPredictionResponse shape
    coerced: List[schemas.PredictedQuestionFull] = []
    for p in result.get("predictions", []):
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

    return schemas.SubjectPredictionResponse(
        id=result.get("id"),
        subject_id=subject_id,
        predictions=coerced,
        total_marks=int(result.get("total_marks", 0)),
        coverage_percentage=int(result.get("coverage_percentage", 0)),
        unit_coverage=result.get("unit_coverage", {}),
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
    db: Session = Depends(get_db)
):
    subject = db.query(models.Subject).filter(
        models.Subject.id == prediction_request.subject_id,
        models.Subject.user_id == current_user["id"]
    ).first()

    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    # NOTE: the service now handles all paper-count tiers (0, 1-2, 3+) internally.
    # We no longer block here on "no papers" — the service returns a structured
    # response for every case. Only a hard 500 surfaces as an error.
    service = get_prepiq_service()
    try:
        result = service.generate_predictions(
            db,
            prediction_request.subject_id,
            current_user["id"],
            existing_prediction_id=None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating prediction: {str(e)}"
        )

    # Tier 0 (no papers) returns id=None — surface a helpful message instead
    # of crashing the response model validation.
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

    # The service already committed a Prediction row; fetch the latest one.
    prediction = (
        db.query(models.Prediction)
        .filter(
            models.Prediction.subject_id == prediction_request.subject_id,
            models.Prediction.user_id == current_user["id"],
        )
        .order_by(models.Prediction.created_at.desc())
        .first()
    )

    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction record not found after generation."
        )

    return {
        "prediction_id": prediction.id,
        "status": "completed",
        "message": result.get("warning") or "Prediction generated successfully.",
        "progress": 100,
    }


def _safe_coverage_percentage(value) -> int:
    """H-23: coerce coverage_percentage to int regardless of source type."""
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _build_prediction_response(result: dict) -> dict:
    """Build a PredictionResponse-compatible dict from service output."""
    predicted_questions = []
    for q in result.get("predicted_questions", []):
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
        "coverage_percentage": _safe_coverage_percentage(result.get("coverage_percentage")),
        "unit_coverage": result.get("unit_coverage") or {},
        "generated_at": result["generated_at"],
    }


@router.get("/{prediction_id}", response_model=schemas.PredictionResponse)
async def get_prediction(
    prediction_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_prepiq_service()
    try:
        result = service.get_prediction(
            db=db,
            prediction_id=prediction_id,
            user_id=current_user["id"]
        )
        return _build_prediction_response(result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{subject_id}/latest", response_model=schemas.PredictionResponse)
async def get_latest_prediction(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_prepiq_service()
    try:
        result = service.get_latest_prediction(
            db=db,
            subject_id=subject_id,
            user_id=current_user["id"]
        )
        return _build_prediction_response(result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{prediction_id}")
async def update_prediction(
    prediction_id: str,
    prediction_update: schemas.PredictionUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prediction = db.query(models.Prediction).join(models.Subject).filter(
        models.Prediction.id == prediction_id,
        models.Subject.user_id == current_user["id"]
    ).first()

    if not prediction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")

    for var, value in vars(prediction_update).items():
        if value is not None:
            setattr(prediction, var, value)

    db.commit()
    db.refresh(prediction)
    return {"message": "Prediction updated successfully", "prediction_id": str(prediction.id)}
