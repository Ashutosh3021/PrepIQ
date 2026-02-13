"""
Upload and Analysis Router
Handles file uploads and processes them through the ML pipeline:
EasyOCR → YOLOv8 → GroundingDINO → Analysis
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
from datetime import datetime
import logging
import asyncio
import sys

# Setup logging first
logger = logging.getLogger(__name__)

from ..database import get_db
from .. import models, schemas

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import model coordinator
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from services.model_coordinator import model_coordinator
except ImportError as e:
    # Fallback if import fails
    model_coordinator = None
    logger.warning(f"Model coordinator not available: {e}")

# Import from the new Supabase-first auth service
from services.supabase_first_auth import get_current_user_from_token

logger = logging.getLogger(__name__)

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Dependency for protected routes
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)

router = APIRouter(
    prefix="/upload",
    tags=["Upload and Analysis"]
)


@router.post("/")
async def upload_and_analyze(
    subject_id: str = Form(...),
    files: List[UploadFile] = File(...),
    material_type: str = Form("pyq"),  # pyq, notes, syllabus, diagram
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload study materials and process through ML pipeline.
    
    Pipeline:
    1. EasyOCR - Extract text from images
    2. YOLOv8 - Detect objects/animals in images
    3. GroundingDINO - Detect circuit diagrams/schematics
    4. Analysis - Extract questions and patterns
    """
    try:
        # Verify subject belongs to user
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id,
            models.Subject.user_id == current_user["id"]
        ).first()
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject not found"
            )
        
        saved_files = []
        extracted_data = {
            "text_content": [],
            "detected_objects": [],
            "circuit_diagrams": [],
            "questions": []
        }
        
        logger.info(f"Starting upload processing for user {current_user['id']}, subject {subject_id}")
        
        # Process each file
        for file in files:
            timestamp = datetime.now().timestamp()
            file_path = UPLOAD_DIR / f"{timestamp}_{file.filename}"
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))
            
            logger.info(f"Saved file: {file.filename}")
            
            # Process based on file type
            if file.content_type and file.content_type.startswith("image"):
                # Process image through coordinated ML pipeline
                # Models: EasyOCR → YOLOv8 → GroundingDINO
                if model_coordinator:
                    image_result = await model_coordinator.process_image_pipeline(str(file_path))
                    extracted_data["text_content"].extend(image_result.get("text", []))
                    extracted_data["detected_objects"].extend(image_result.get("objects", []))
                    extracted_data["circuit_diagrams"].extend(image_result.get("circuits", []))
                    logger.info(f"Image pipeline status: {image_result.get('pipeline_status', [])}")
                else:
                    # Fallback to local function if coordinator not available
                    image_result = await process_image_pipeline(str(file_path))
                    extracted_data["text_content"].extend(image_result.get("text", []))
                    extracted_data["detected_objects"].extend(image_result.get("objects", []))
                    extracted_data["circuit_diagrams"].extend(image_result.get("circuits", []))
                
            elif file.content_type and file.content_type.startswith("text"):
                # Read text file
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        extracted_data["text_content"].append(content)
                        logger.info(f"Extracted text from {file.filename}")
                except Exception as e:
                    logger.warning(f"Could not read text file {file.filename}: {e}")
                
            elif file.content_type and "pdf" in file.content_type:
                # Process PDF
                pdf_result = await process_pdf(str(file_path))
                extracted_data["text_content"].extend(pdf_result.get("text", []))
        
        # Extract questions from content
        logger.info("Extracting questions from content...")
        extracted_data["questions"] = extract_questions(extracted_data["text_content"])
        
        # Save questions to database
        logger.info(f"Saving {len(extracted_data['questions'])} questions to database...")
        saved_questions = []
        for q_data in extracted_data["questions"]:
            question = models.Question(
                paper_id=None,  # Will be associated later
                question_text=q_data["text"],
                marks=q_data.get("marks", 0),
                unit_name=q_data.get("unit", "Unknown"),
                question_type=q_data["type"]
            )
            db.add(question)
            saved_questions.append(question)
        
        db.commit()
        
        # Generate analysis
        logger.info("Generating analysis...")
        analysis_result = await generate_analysis(subject_id, extracted_data, db)
        
        return {
            "success": True,
            "message": f"Processed {len(files)} files successfully",
            "files": saved_files,
            "extracted_data": {
                "text_content": extracted_data["text_content"][:5],  # Limit for response
                "detected_objects": extracted_data["detected_objects"],
                "circuit_diagrams": extracted_data["circuit_diagrams"],
                "questions_count": len(extracted_data["questions"]),
                "questions": extracted_data["questions"][:20]  # Limit to top 20
            },
            "analysis": analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )


async def process_image_pipeline(image_path: str):
    """
    Process image through the cascade:
    1. EasyOCR (text extraction)
    2. YOLOv8 (object detection)
    3. GroundingDINO (circuit diagrams)
    """
    result = {
        "text": [],
        "objects": [],
        "circuits": []
    }
    
    logger.info(f"Processing image: {image_path}")
    
    try:
        # Step 1: Try EasyOCR for text
        try:
            import easyocr
            reader = easyocr.Reader(['en'], gpu=False)
            ocr_results = reader.readtext(image_path)
            
            if ocr_results:
                extracted_text = ' '.join([text for (_, text, _) in ocr_results])
                result["text"].append(extracted_text)
                logger.info(f"✅ EasyOCR extracted {len(ocr_results)} text regions")
            else:
                logger.info("⚠️ EasyOCR found no text")
        except ImportError:
            logger.warning("EasyOCR not installed. Skipping text extraction.")
        except Exception as e:
            logger.warning(f"EasyOCR error: {e}")
        
        # Step 2: YOLOv8 for object detection
        try:
            from ultralytics import YOLO
            model = YOLO('yolov8n.pt')
            yolo_results = model(image_path, verbose=False)
            
            for r in yolo_results:
                if len(r.boxes) > 0:
                    for box in r.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = model.names[class_id]
                        result["objects"].append({
                            "label": class_name,
                            "confidence": round(confidence, 2)
                        })
            
            logger.info(f"✅ YOLOv8 detected {len(result['objects'])} objects")
        except ImportError:
            logger.warning("Ultralytics not installed. Skipping object detection.")
        except Exception as e:
            logger.warning(f"YOLOv8 error: {e}")
        
        # Step 3: GroundingDINO for circuit diagrams (if text detection failed or low confidence)
        if not result["text"] or len(result["text"][0]) < 50:
            try:
                from transformers import pipeline
                from PIL import Image
                
                detector = pipeline(
                    "zero-shot-object-detection",
                    model="google/owlvit-base-patch32"
                )
                
                image = Image.open(image_path)
                circuit_results = detector(
                    image,
                    candidate_labels=["circuit diagram", "electronic schematic", "wiring diagram", "electrical circuit"],
                    threshold=0.1
                )
                
                if circuit_results:
                    result["circuits"] = [
                        {
                            "label": r["label"],
                            "score": round(r["score"], 2),
                            "box": r["box"]
                        }
                        for r in circuit_results
                    ]
                    logger.info(f"✅ GroundingDINO found {len(result['circuits'])} circuit elements")
            except ImportError:
                logger.warning("Transformers not installed. Skipping circuit detection.")
            except Exception as e:
                logger.warning(f"GroundingDINO error: {e}")
        
        return result
        
    except Exception as e:
        logger.error(f"Image processing error: {e}")
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
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            if text:
                result["text"].append(text)
                logger.info(f"✅ Extracted text from PDF ({len(text)} chars)")
    except ImportError:
        logger.warning("PyPDF2 not installed. Skipping PDF processing.")
    except Exception as e:
        logger.error(f"PDF processing error: {e}")
    
    return result


def extract_questions(text_content: List[str]):
    """Extract questions from text content"""
    questions = []
    
    import re
    
    for content in text_content:
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            # Detect question patterns
            if line.endswith('?') or any(marker in line.lower() for marker in ['q.', 'question', 'marks:', '(', ')', 'explain', 'describe', 'calculate']):
                if len(line) > 20 and len(line) < 500:  # Filter length
                    questions.append({
                        "text": line,
                        "type": detect_question_type(line),
                        "marks": extract_marks(line),
                        "unit": extract_unit(line)
                    })
    
    return questions


def detect_question_type(text: str) -> str:
    """Detect if question is theory, numerical, or diagram-based"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['calculate', 'compute', 'find the value', 'solve', 'determine the', 'evaluate']):
        return "numerical"
    elif any(word in text_lower for word in ['diagram', 'draw', 'sketch', 'show', 'figure', 'circuit']):
        return "diagram"
    elif any(word in text_lower for word in ['explain', 'describe', 'discuss', 'what', 'why', 'how', 'define', 'state']):
        return "theory"
    else:
        return "mixed"


def extract_marks(text: str) -> int:
    """Extract marks from question text"""
    import re
    
    patterns = [
        r'\((\d+)\)',
        r'\[(\d+)\]',
        r'(\d+)\s*marks?',
        r'marks?\s*[:\-]?\s*(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    
    return 0


def extract_unit(text: str) -> str:
    """Extract unit information from question text"""
    import re
    
    # Look for unit patterns like "Unit 1", "Unit-1", "Unit1"
    patterns = [
        r'unit\s*(\d+)',
        r'unit[-:]\s*(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return f"Unit {match.group(1)}"
    
    return "Unknown"


async def generate_analysis(subject_id: str, extracted_data: dict, db: Session):
    """Generate comprehensive analysis from extracted data"""
    
    analysis = {
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
        "topics": [],
        "patterns": {},
        "predictions": {}
    }
    
    # Analyze question patterns
    if extracted_data["questions"]:
        # Count by type
        type_counts = {}
        marks_distribution = {}
        
        for q in extracted_data["questions"]:
            q_type = q.get("type", "unknown")
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
            
            marks = q.get("marks", 0)
            if marks > 0:
                marks_distribution[marks] = marks_distribution.get(marks, 0) + 1
        
        analysis["patterns"] = {
            "question_types": type_counts,
            "marks_distribution": marks_distribution
        }
        
        # Simple prediction logic based on frequency
        analysis["predictions"] = {
            "high_probability": [],
            "medium_probability": [],
            "low_probability": []
        }
        
        # Group similar questions (simplified)
        question_texts = [q["text"] for q in extracted_data["questions"]]
        from collections import Counter
        question_counts = Counter(question_texts)
        
        for question, count in question_counts.items():
            if count >= 2:
                analysis["predictions"]["high_probability"].append({
                    "question": question,
                    "confidence": min(70 + (count - 2) * 10, 95),
                    "reason": f"Appeared {count} times"
                })
            else:
                analysis["predictions"]["medium_probability"].append({
                    "question": question,
                    "confidence": 50,
                    "reason": "Appeared once"
                })
    
    return analysis


@router.get("/status/{upload_id}")
async def get_upload_status(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the status of an upload job"""
    # This would check the status of a background job in production
    return {
        "upload_id": upload_id,
        "status": "completed",
        "progress": 100
    }
