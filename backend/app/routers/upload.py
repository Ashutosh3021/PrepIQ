"""
Upload and Analysis Router
Handles file uploads and processes them through the ML pipeline.
Text extraction is delegated to PDFParser (pdf_parser.py) which supports
PDF, DOCX, PPTX, XLSX, CSV, images, and plain text.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import os
import shutil
import re
from pathlib import Path
from datetime import datetime
import logging
import asyncio
import sys
import json

# Setup logging first
logger = logging.getLogger(__name__)

# In-memory progress tracking (use Redis in production)
upload_progress: Dict[str, dict] = {}

from ..database import get_db
from .. import models, schemas
from ..pdf_parser import PDFParser

# Import model coordinator using absolute imports
try:
    from app.services.model_coordinator import get_model_coordinator as _get_coordinator
    model_coordinator = _get_coordinator()
except Exception:
    try:
        from services.model_coordinator import get_model_coordinator as _get_coordinator
        model_coordinator = _get_coordinator()
    except Exception:
        model_coordinator = None
        logger.warning("Model coordinator not available - some features may be limited")

# Import from the new Supabase-first auth service
from ..services.supabase_first_auth import get_current_user_from_token

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


@router.post("")
async def upload_and_analyze(
    subject_id: str = Form(...),
    files: List[UploadFile] = File(...),
    material_type: str = Form("pyq"),  # pyq, notes, syllabus, diagram
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload study materials and process through ML pipeline with real-time progress tracking.
    """
    upload_id = f"{current_user['id']}_{datetime.now().timestamp()}"
    
    # Initialize progress tracking
    upload_progress[upload_id] = {
        "status": "initializing",
        "overall_progress": 0,
        "current_file": "",
        "current_step": "Initializing...",
        "files_processed": 0,
        "total_files": len(files),
        "questions_extracted": 0,
        "errors": [],
        "start_time": datetime.now().isoformat()
    }
    
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
        all_text_content: List[str] = []

        logger.info(f"Starting upload processing for user {current_user['id']}, subject {subject_id}")

        # ── Step 1: Save + extract text from every file ───────────────────────
        for file_idx, file in enumerate(files):
            upload_progress[upload_id]["current_file"] = file.filename or f"file_{file_idx+1}"
            upload_progress[upload_id]["current_step"] = f"Saving file {file_idx + 1}/{len(files)}"
            upload_progress[upload_id]["overall_progress"] = int((file_idx / len(files)) * 40)

            timestamp = datetime.now().timestamp()
            safe_name = (file.filename or f"upload_{file_idx}").replace(" ", "_")
            file_path = UPLOAD_DIR / f"{timestamp}_{safe_name}"

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))
            logger.info(f"Saved file: {file.filename}")

            # ── Extract text via PDFParser (handles PDF/DOCX/PPTX/XLSX/images/txt)
            upload_progress[upload_id]["current_step"] = f"Extracting text: {file.filename}"
            upload_progress[upload_id]["overall_progress"] = int(((file_idx + 0.5) / len(files)) * 40)
            try:
                text = PDFParser.extract_text(str(file_path))
                if text and text.strip():
                    all_text_content.append(text)
                    logger.info(f"Extracted {len(text)} chars from {file.filename}")
                else:
                    logger.warning(f"No text extracted from {file.filename}")
                    upload_progress[upload_id]["errors"].append(
                        f"No text found in {file.filename} — file may be image-only or empty"
                    )
            except Exception as exc:
                logger.error(f"Text extraction failed for {file.filename}: {exc}")
                upload_progress[upload_id]["errors"].append(
                    f"Could not extract text from {file.filename}: {str(exc)}"
                )

            upload_progress[upload_id]["files_processed"] = file_idx + 1

        # ── Step 2: Extract questions via Gemini AI ───────────────────────────
        upload_progress[upload_id]["current_step"] = "Extracting questions with AI..."
        upload_progress[upload_id]["overall_progress"] = 60
        logger.info(f"Sending {len(all_text_content)} text block(s) to Gemini for question extraction...")

        combined_text = "\n\n".join(all_text_content)
        parsed_questions = await _extract_questions_with_gemini(combined_text) if combined_text.strip() else []
        upload_progress[upload_id]["questions_extracted"] = len(parsed_questions)
        logger.info(f"Extracted {len(parsed_questions)} questions via Gemini")

        # ── Step 3: Save QuestionPaper + Questions to DB ──────────────────────
        upload_progress[upload_id]["current_step"] = "Saving to database..."
        upload_progress[upload_id]["overall_progress"] = 80

        question_paper = models.QuestionPaper(
            subject_id=subject_id,
            file_name=files[0].filename if files else "uploaded_material",
            file_path=saved_files[0] if saved_files else None,
            processing_status="completed",
            processed_at=datetime.now(),
        )
        db.add(question_paper)
        db.commit()
        db.refresh(question_paper)

        logger.info(f"Saving {len(parsed_questions)} questions to database...")
        for q_idx, q_data in enumerate(parsed_questions):
            question = models.Question(
                paper_id=question_paper.id,
                question_text=q_data["text"],
                marks=q_data.get("marks", 0),
                unit_name=q_data.get("unit") or "Unknown",
                question_type=q_data.get("question_type", "Mixed/other"),
            )
            db.add(question)
            if q_idx % 10 == 0:
                upload_progress[upload_id]["overall_progress"] = 80 + int(
                    (q_idx / max(len(parsed_questions), 1)) * 15
                )

        db.commit()
        
        # ── Step 4: Generate analysis ─────────────────────────────────────────
        upload_progress[upload_id]["current_step"] = "Generating analysis..."
        upload_progress[upload_id]["overall_progress"] = 95
        logger.info("Generating analysis...")
        analysis_result = await generate_upload_analysis(subject_id, parsed_questions, db)

        # Clean up local temp files
        for fp in saved_files:
            try:
                os.unlink(fp)
            except OSError:
                pass

        upload_progress[upload_id]["status"] = "completed"
        upload_progress[upload_id]["overall_progress"] = 100
        upload_progress[upload_id]["current_step"] = "Complete!"
        upload_progress[upload_id]["end_time"] = datetime.now().isoformat()

        return {
            "success": True,
            "upload_id": upload_id,
            "message": f"Processed {len(files)} file{'' if len(files) == 1 else 's'} successfully",
            "files": [],
            "extracted_data": {
                "questions_count": len(parsed_questions),
                "questions": [
                    {"text": q["text"], "type": q.get("question_type", ""), "marks": q.get("marks", 0)}
                    for q in parsed_questions[:20]
                ],
            },
            "analysis": analysis_result,
        }

    except HTTPException:
        upload_progress[upload_id]["status"] = "failed"
        raise
    except Exception as e:
        for fp in saved_files:
            try:
                os.unlink(fp)
            except OSError:
                pass
        logger.error(f"Upload processing error: {str(e)}")
        upload_progress[upload_id]["status"] = "failed"
        upload_progress[upload_id]["errors"].append(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )


async def _extract_questions_with_gemini(text: str) -> list:
    """
    Send extracted document text to Gemini and parse out all exam questions.
    Falls back to PDFParser regex if Gemini is unavailable or fails.
    """
    import os, json as _json
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.warning("GEMINI_API_KEY not set — falling back to regex question parser")
        return PDFParser.parse_questions_from_text(text)

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Truncate to avoid token limits (~30k chars ≈ ~7500 tokens)
        truncated = text[:30_000]

        system_prompt = """Analyze the provided exam paper text and extract every question it contains.

For each question return a JSON object with these fields:
- "text": the full question text (string, required)
- "marks": marks/points value as integer, 0 if not specified
- "question_type": one of "Conceptual/explanation", "Calculation/problem", "Proof/derivation", "Definition", "Comparison", "Mixed/other"
- "difficulty": one of "Easy", "Medium", "Hard" based on marks and complexity
- "unit": unit or module reference if mentioned (string or null)

Return ONLY a valid JSON array of question objects. No markdown, no explanation, no code fences.
If no questions are found, return an empty array [].

Rules:
- Include ALL questions: numbered, lettered, roman-numeral, sub-parts
- Do NOT include instructions, headers, or boilerplate text
- Merge multi-line questions into a single "text" string
- If marks are in parentheses like (5) or [10M], extract them as integers"""

        response = model.generate_content(
            f"{system_prompt}\n\nEXAM PAPER TEXT:\n{truncated}"
        )

        raw = response.text.strip()
        # Strip markdown code fences if Gemini wraps in ```json ... ```
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

        questions_raw = _json.loads(raw)
        if not isinstance(questions_raw, list):
            raise ValueError("Gemini returned non-list JSON")

        # Normalise to the same shape PDFParser returns
        questions = []
        for q in questions_raw:
            if not isinstance(q, dict) or not q.get("text", "").strip():
                continue
            questions.append({
                "text":          q["text"].strip(),
                "marks":         int(q.get("marks") or 0),
                "question_type": q.get("question_type") or "Mixed/other",
                "difficulty":    q.get("difficulty") or "Medium",
                "unit":          q.get("unit") or None,
                "keywords":      [],
            })

        logger.info(f"Gemini extracted {len(questions)} questions")
        return questions

    except Exception as exc:
        logger.error(f"Gemini question extraction failed: {exc} — falling back to regex parser")
        return PDFParser.parse_questions_from_text(text)


async def generate_upload_analysis(subject_id: str, parsed_questions: list, db: Session):
    """Generate summary analysis from parsed questions."""
    analysis = {
        "subject_id": subject_id,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_questions": len(parsed_questions),
            "theory_questions":     len([q for q in parsed_questions if "Conceptual" in q.get("question_type", "") or "Definition" in q.get("question_type", "")]),
            "numerical_questions":  len([q for q in parsed_questions if "Calculation" in q.get("question_type", "")]),
            "proof_questions":      len([q for q in parsed_questions if "Proof" in q.get("question_type", "")]),
        },
        "patterns": {},
        "predictions": {},
    }

    if parsed_questions:
        type_counts: Dict[str, int] = {}
        marks_dist:  Dict[int, int] = {}
        for q in parsed_questions:
            qt = q.get("question_type", "Mixed/other")
            type_counts[qt] = type_counts.get(qt, 0) + 1
            m = q.get("marks", 0)
            if m:
                marks_dist[m] = marks_dist.get(m, 0) + 1

        analysis["patterns"] = {
            "question_types":    type_counts,
            "marks_distribution": marks_dist,
        }

        from collections import Counter
        text_counts = Counter(q["text"] for q in parsed_questions)
        high, medium = [], []
        for text, count in text_counts.items():
            if count >= 2:
                high.append({"question": text, "confidence": min(70 + (count - 2) * 10, 95), "reason": f"Appeared {count} times"})
            else:
                medium.append({"question": text, "confidence": 50, "reason": "Appeared once"})

        analysis["predictions"] = {
            "high_probability":   high[:10],
            "medium_probability": medium[:20],
            "low_probability":    [],
        }

    return analysis


@router.get("/status/{upload_id}")
async def get_upload_status(
    upload_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get real-time progress of an upload job"""
    if upload_id not in upload_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload not found"
        )
    
    progress_data = upload_progress[upload_id]
    
    return {
        "upload_id": upload_id,
        "status": progress_data.get("status", "unknown"),
        "overall_progress": progress_data.get("overall_progress", 0),
        "current_file": progress_data.get("current_file", ""),
        "current_step": progress_data.get("current_step", ""),
        "files_processed": progress_data.get("files_processed", 0),
        "total_files": progress_data.get("total_files", 0),
        "questions_extracted": progress_data.get("questions_extracted", 0),
        "errors": progress_data.get("errors", []),
        "start_time": progress_data.get("start_time"),
        "end_time": progress_data.get("end_time")
    }
