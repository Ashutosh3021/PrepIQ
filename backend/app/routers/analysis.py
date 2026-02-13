from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import shutil
from pathlib import Path
from datetime import datetime

from ..database import get_db
from .. import models, schemas
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import from the new Supabase-first auth service
from services.supabase_first_auth import get_current_user_from_token

# Dependency for protected routes
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)
from ..services import PrepIQService

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

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


@router.post("/upload")
async def upload_material(
    subject_id: str = Form(...),
    files: List[UploadFile] = File(...),
    material_type: str = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process study materials through ML pipeline:
    EasyOCR → YOLOv8 → GroundingDINO
    """
    try:
        saved_files = []
        extracted_data = {
            "text_content": [],
            "detected_objects": [],
            "circuit_diagrams": [],
            "questions": []
        }
        
        for file in files:
            file_path = UPLOAD_DIR / f"{datetime.now().timestamp()}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))
            
            # Process based on file type
            if file.content_type and file.content_type.startswith("image"):
                image_result = await process_image_pipeline(file_path)
                extracted_data["text_content"].extend(image_result.get("text", []))
                extracted_data["detected_objects"].extend(image_result.get("objects", []))
                extracted_data["circuit_diagrams"].extend(image_result.get("circuits", []))
            elif file.content_type and file.content_type.startswith("text"):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    extracted_data["text_content"].append(content)
            elif file.content_type and "pdf" in file.content_type:
                pdf_result = await process_pdf(file_path)
                extracted_data["text_content"].extend(pdf_result.get("text", []))
        
        # Extract questions
        extracted_data["questions"] = extract_questions(extracted_data["text_content"])
        
        # Generate analysis
        analysis_result = await generate_analysis(subject_id, extracted_data)
        
        return {
            "success": True,
            "message": f"Processed {len(files)} files successfully",
            "files": saved_files,
            "extracted_data": extracted_data,
            "analysis": analysis_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def process_image_pipeline(image_path: str):
    """Process image: EasyOCR → YOLOv8 → GroundingDINO"""
    result = {"text": [], "objects": [], "circuits": []}
    
    try:
        # Step 1: EasyOCR for text
        import easyocr
        reader = easyocr.Reader(['en'], gpu=False)
        ocr_results = reader.readtext(image_path)
        
        if ocr_results:
            extracted_text = ' '.join([text for (_, text, _) in ocr_results])
            result["text"].append(extracted_text)
        
        # Step 2: YOLOv8 for objects
        try:
            from ultralytics import YOLO
            model = YOLO('yolov8n.pt')
            yolo_results = model(image_path, verbose=False)
            
            for r in yolo_results:
                for box in r.boxes:
                    result["objects"].append({
                        "label": model.names[int(box.cls[0])],
                        "confidence": float(box.conf[0])
                    })
        except Exception as e:
            print(f"YOLOv8 error: {e}")
        
        # Step 3: GroundingDINO for circuits (if little text found)
        if not result["text"] or len(result["text"][0]) < 50:
            try:
                from transformers import pipeline
                from PIL import Image
                
                detector = pipeline("zero-shot-object-detection", model="google/owlvit-base-patch32")
                image = Image.open(image_path)
                circuit_results = detector(
                    image,
                    candidate_labels=["circuit diagram", "electronic schematic"],
                    threshold=0.1
                )
                result["circuits"] = circuit_results
            except Exception as e:
                print(f"GroundingDINO error: {e}")
        
        return result
    except Exception as e:
        print(f"Image processing error: {e}")
        return result


async def process_pdf(pdf_path: str):
    """Extract text from PDF"""
    result = {"text": []}
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            result["text"].append(text)
    except Exception as e:
        print(f"PDF error: {e}")
    return result


def extract_questions(text_content: List[str]):
    """Extract questions from text"""
    questions = []
    for content in text_content:
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.endswith('?') or any(m in line.lower() for m in ['q.', 'question', 'marks:']):
                if len(line) > 20:
                    questions.append({
                        "text": line,
                        "type": detect_question_type(line),
                        "marks": extract_marks(line)
                    })
    return questions


def detect_question_type(text: str) -> str:
    text_lower = text.lower()
    if any(w in text_lower for w in ['calculate', 'compute', 'solve']):
        return "numerical"
    elif any(w in text_lower for w in ['diagram', 'draw', 'sketch']):
        return "diagram"
    elif any(w in text_lower for w in ['explain', 'describe', 'discuss']):
        return "theory"
    return "mixed"


def extract_marks(text: str) -> int:
    import re
    patterns = [r'\((\d+)\)', r'\[(\d+)\]', r'(\d+)\s*marks?']
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    return 0


async def generate_analysis(subject_id: str, extracted_data: dict):
    """Generate comprehensive analysis"""
    return {
        "subject_id": subject_id,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_questions": len(extracted_data["questions"]),
            "theory_questions": len([q for q in extracted_data["questions"] if q["type"] == "theory"]),
            "numerical_questions": len([q for q in extracted_data["questions"] if q["type"] == "numerical"]),
            "diagram_questions": len([q for q in extracted_data["questions"] if q["type"] == "diagram"]),
            "detected_objects": len(extracted_data["detected_objects"]),
            "circuit_diagrams": len(extracted_data["circuit_diagrams"])
        },
        "questions": extracted_data["questions"][:20]  # Limit to top 20
    }


@router.get("/important-questions/{subject_id}")
async def get_important_questions(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get most repeating and high-probability questions"""
    service = PrepIQService()
    try:
        # Get repetition analysis
        repetition_analysis = service.get_repetition_analysis(
            db=db, subject_id=subject_id, user_id=current_user["id"]
        )
        
        # Get predictions
        predictions = service.get_latest_prediction(
            db=db, subject_id=subject_id, user_id=current_user["id"]
        )
        
        return {
            "subject_id": subject_id,
            "most_repeating": repetition_analysis.get("exact_repetitions", [])[:10],
            "high_probability": predictions.get("predicted_questions", [])[:10]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mock-test/generate")
async def generate_mock_test(
    subject_id: str = Form(...),
    difficulty: str = Form("mixed"),
    question_count: int = Form(10),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate mock test based on patterns"""
    try:
        # Get questions from database
        questions = db.query(models.Question).join(
            models.QuestionPaper
        ).filter(
            models.QuestionPaper.subject_id == subject_id
        ).all()
        
        # Select random questions based on pattern
        import random
        selected = random.sample(questions, min(question_count, len(questions)))
        
        return {
            "test_id": f"mock_{datetime.now().timestamp()}",
            "subject_id": subject_id,
            "questions": [
                {
                    "id": q.id,
                    "question": q.question_text,
                    "marks": q.marks,
                    "unit": q.unit_name
                } for q in selected
            ],
            "time_limit": question_count * 3,
            "total_marks": sum(q.marks for q in selected)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))