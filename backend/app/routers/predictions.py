from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas
from ..services import PrepIQService
from ..routers.auth import get_current_user

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"]
)

@router.post("/generate", response_model=schemas.PredictionGenerationResponse)
def generate_prediction(
    prediction_request: schemas.PredictionRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subject belongs to user
    subject = db.query(models.Subject).filter(
        models.Subject.id == prediction_request.subject_id,
        models.Subject.user_id == current_user.id
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Check if papers exist for this subject
    papers = db.query(models.QuestionPaper).filter(
        models.QuestionPaper.subject_id == prediction_request.subject_id,
        models.QuestionPaper.processing_status == "completed"
    ).all()
    
    if not papers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No processed papers found for this subject. Please upload and process papers first."
        )
    
    # Create prediction record
    prediction = models.Prediction(
        subject_id=prediction_request.subject_id,
        user_id=current_user.id,
        total_questions=0,  # Will be updated after generation
        total_predicted_marks=0,  # Will be updated after generation
        processing_status="generating"
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    
    # Generate predictions using the service
    service = PrepIQService()
    try:
        result = service.generate_predictions(db, prediction_request.subject_id, current_user.id)
        
        # Update the prediction record with results
        prediction.predicted_questions_json = str(result.get("predictions", []))
        prediction.total_questions = len(result.get("predictions", []))
        prediction.total_predicted_marks = result.get("total_marks", 0)
        prediction.processing_status = "completed"
        
        db.commit()
        db.refresh(prediction)
        
        return {
            "prediction_id": prediction.id,
            "status": "completed",
            "message": "Prediction generated successfully.",
            "progress": 100
        }
    except Exception as e:
        prediction.processing_status = "failed"
        prediction.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating prediction: {str(e)}"
        )

@router.get("/{prediction_id}", response_model=schemas.PredictionResponse)
def get_prediction(
    prediction_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.get_prediction(
            db=db,
            prediction_id=prediction_id,
            user_id=current_user.id
        )
        
        return {
            "id": result["id"],
            "subject_id": result["subject_id"],
            "predicted_questions": [
                schemas.PredictedQuestion(
                    question_number=q["question_number"],
                    text=q["text"],
                    marks=q["marks"],
                    unit=q["unit"],
                    probability=q["probability"],
                    reasoning=q["reasoning"]
                ) for q in result["predicted_questions"]
            ],
            "total_marks": result["total_marks"],
            "coverage_percentage": result["coverage_percentage"],
            "unit_coverage": result["unit_coverage"],
            "generated_at": result["generated_at"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/{subject_id}/latest", response_model=schemas.PredictionResponse)
def get_latest_prediction(
    subject_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.get_latest_prediction(
            db=db,
            subject_id=subject_id,
            user_id=current_user.id
        )
        
        return {
            "id": result["id"],
            "subject_id": result["subject_id"],
            "predicted_questions": [
                schemas.PredictedQuestion(
                    question_number=q["question_number"],
                    text=q["text"],
                    marks=q["marks"],
                    unit=q["unit"],
                    probability=q["probability"],
                    reasoning=q["reasoning"]
                ) for q in result["predicted_questions"]
            ],
            "total_marks": result["total_marks"],
            "coverage_percentage": result["coverage_percentage"],
            "unit_coverage": result["unit_coverage"],
            "generated_at": result["generated_at"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/{prediction_id}")
def update_prediction(
    prediction_id: str,
    prediction_update: schemas.PredictionUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify prediction belongs to user
    prediction = db.query(models.Prediction).join(models.Subject).filter(
        models.Prediction.id == prediction_id,
        models.Subject.user_id == current_user.id
    ).first()
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    # Update fields
    for var, value in vars(prediction_update).items():
        if value is not None:
            setattr(prediction, var, value)
    
    db.commit()
    db.refresh(prediction)
    
    return {"message": "Prediction updated successfully", "prediction": prediction}