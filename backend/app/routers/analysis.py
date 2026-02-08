from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from .. import models, schemas
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import from the new Supabase-first auth service
from services.supabase_first_auth import get_current_user_from_token

# Dependency for protected routes
async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)
from ..services import PrepIQService

router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"]
)

@router.get("/{subject_id}/frequency")
async def get_frequency_analysis(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.get_frequency_analysis(
            db=db,
            subject_id=subject_id,
            user_id=current_user["id"]
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/{subject_id}/weightage")
async def get_weightage_analysis(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.get_weightage_analysis(
            db=db,
            subject_id=subject_id,
            user_id=current_user["id"]
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/{subject_id}/repetitions")
async def get_repetition_analysis(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.get_repetition_analysis(
            db=db,
            subject_id=subject_id,
            user_id=current_user["id"]
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/{subject_id}/trends")
async def get_trend_analysis(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = PrepIQService()
    try:
        result = service.get_trend_analysis(
            db=db,
            subject_id=subject_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/data")
async def get_analysis_data(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import datetime
    import numpy as np
    service = PrepIQService()
    try:
        # Get all analysis data for the user
        # Get user's subjects
        subjects = db.query(models.Subject).filter(models.Subject.user_id == current_user["id"]).all()
        
        if not subjects:
            # Return empty data if no subjects
            return {
                "performanceData": [],
                "subjectPerformance": [],
                "weeklyProgress": [],
                "predictionsAccuracy": [],
                "topicMastery": [],
                "studyInsights": {}
            }
        
        # Aggregate analysis across all subjects
        all_subject_analysis = []
        for subject in subjects:
            try:
                # Get comprehensive trend analysis for each subject
                trend_analysis = service.get_trend_analysis(db=db, subject_id=subject.id)
                try:
                    predictions = service.get_latest_prediction(db=db, subject_id=subject.id, user_id=current_user["id"])
                except ValueError:
                    predictions = {}
                all_subject_analysis.append({
                    "subject_id": subject.id,
                    "subject_name": subject.name,
                    "trend_analysis": trend_analysis,
                    "predictions": predictions
                })
            except ValueError:
                # Skip subjects that don't have enough data
                continue
        
        # Format the data for the frontend
        performance_data = []
        predictions_accuracy = []
        topic_mastery = []
        subject_performance = []
        
        for analysis_item in all_subject_analysis:
            subject_name = analysis_item["subject_name"]
            trend_analysis = analysis_item["trend_analysis"]
            predictions = analysis_item.get("predictions", {})
            
            # Performance data based on trend analysis
            basic_analysis = trend_analysis.get("basic_analysis", {})
            unit_weightage = basic_analysis.get("unit_weightage", {})
            
            # Create performance data points
            for unit, weight in list(unit_weightage.items())[:5]:  # Limit to top 5 units
                performance_data.append({
                    "subject": subject_name,
                    "unit": unit,
                    "weightage": weight,
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
            
            # Predictions accuracy
            if predictions:
                predictions_accuracy.append({
                    "subject": subject_name,
                    "accuracy_score": predictions.get("accuracy_score", 0),
                    "total_predictions": predictions.get("total_marks", 0)
                })
            
            # Topic mastery based on enhanced analysis
            enhanced_analysis = trend_analysis.get("enhanced_analysis", {})
            topics_info = enhanced_analysis.get("topics", [])
            for topic in topics_info[:3]:  # Top 3 topics
                topic_mastery.append({
                    "subject": subject_name,
                    "topic": f"Topic {topic.get('topic_id', 'N/A')}",
                    "mastery_level": topic.get("percentage", 0),
                    "frequency": topic.get("frequency", 0)
                })
            
            # Subject performance
            subject_performance.append({
                "subject": subject_name,
                "performance": min(100, max(0, basic_analysis.get("total_questions_analyzed", 0) * 2)),
                "total_questions": basic_analysis.get("total_questions_analyzed", 0),
                "color": "#3b82f6"  # Blue
            })
        
        # Create weekly progress data
        weekly_progress = []
        for i in range(1, 7):
            weekly_progress.append({
                "week": f"Week {i}",
                "progress": min(100, 60 + (i * 5))  # Increasing trend
            })
        
        # Study insights
        study_insights = {
            "total_subjects": len(subjects),
            "total_questions_analyzed": sum(
                analysis["trend_analysis"].get("total_questions_analyzed", 0) 
                for analysis in all_subject_analysis
            ),
            "average_accuracy": np.mean([
                analysis.get("predictions", {}).get("accuracy_score", 0) 
                for analysis in all_subject_analysis 
                if "predictions" in analysis and analysis["predictions"]
            ]).item() if any("predictions" in analysis and analysis["predictions"] for analysis in all_subject_analysis) else 0,
            "high_priority_topics": [],
            "recommended_focus_areas": []
        }
        
        # Extract high priority topics from correlation analysis
        for analysis in all_subject_analysis:
            correlation_analysis = analysis["trend_analysis"].get("correlation_analysis", {})
            high_impact_topics = correlation_analysis.get("high_impact_topics", [])
            for topic in high_impact_topics[:2]:  # Top 2 high impact topics per subject
                study_insights["high_priority_topics"].append({
                    "subject": analysis["subject_name"],
                    "topic": topic.get("topic", "Unknown"),
                    "impact_score": topic.get("impact_score", 0)
                })
        
        return {
            "performanceData": performance_data,
            "subjectPerformance": subject_performance,
            "weeklyProgress": weekly_progress,
            "predictionsAccuracy": predictions_accuracy,
            "topicMastery": topic_mastery,
            "studyInsights": study_insights
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        print(f"Analysis data error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis error: {str(e)}"
        )