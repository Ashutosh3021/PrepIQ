"""
Upload and Analysis Router (Phase 2).
Files → local UPLOAD_ROOT; metadata + questions → Pyronites tables.
Extraction still via Phase 1 LLM provider / regex fallback.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File, Form
from typing import List, Dict
import re
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
upload_progress: Dict[str, dict] = {}

from ..core.llm_provider import get_llm_client
from ..core.local_storage import save_upload, resolve_path
from ..services.pyronites_auth import get_current_user_from_token
from ..services.syllabus_gate import assert_pyq_upload_allowed
from ..services.unit_tagging import tag_after_upload
from ..repositories import subjects as subjects_repo
from ..repositories import papers as papers_repo
from ..repositories import questions as questions_repo


def _get_pdf_parser():
    from ..pdf_parser import PDFParser
    return PDFParser


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


router = APIRouter(prefix="/upload", tags=["Upload and Analysis"])


@router.post("")
async def upload_and_analyze(
    subject_id: str = Form(...),
    files: List[UploadFile] = File(...),
    material_type: str = Form("pyq"),
    current_user: dict = Depends(get_current_user),
):
    upload_id = f"{current_user['id']}_{datetime.now().timestamp()}"
    upload_progress[upload_id] = {
        "status": "initializing",
        "overall_progress": 0,
        "current_file": "",
        "current_step": "Initializing...",
        "files_processed": 0,
        "total_files": len(files),
        "questions_extracted": 0,
        "errors": [],
        "start_time": datetime.now().isoformat(),
    }

    stored_rels: List[str] = []
    try:
        subject = subjects_repo.get_for_user(subject_id, current_user["id"])
        if not subject:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

        if material_type in ("pyq", "question_paper", "past_paper"):
            assert_pyq_upload_allowed(subject)

        all_text_content: List[str] = []
        first_filename = files[0].filename if files else "uploaded_material"

        for file_idx, file in enumerate(files):
            upload_progress[upload_id]["current_file"] = file.filename or f"file_{file_idx+1}"
            upload_progress[upload_id]["current_step"] = f"Saving file {file_idx + 1}/{len(files)}"
            upload_progress[upload_id]["overall_progress"] = int((file_idx / len(files)) * 40)

            content = await file.read()
            rel = save_upload(
                content,
                file.filename or f"upload_{file_idx}",
                current_user["id"],
                subject_id,
            )
            stored_rels.append(rel)

            abs_path = resolve_path(rel)
            upload_progress[upload_id]["current_step"] = f"Extracting text: {file.filename}"
            try:
                text = _get_pdf_parser().extract_text(str(abs_path))
                if text and text.strip():
                    all_text_content.append(text)
                else:
                    upload_progress[upload_id]["errors"].append(
                        f"No text found in {file.filename}"
                    )
            except Exception as exc:
                logger.error("Text extraction failed for %s: %s", file.filename, exc)
                upload_progress[upload_id]["errors"].append(
                    f"Could not extract text from {file.filename}: {str(exc)}"
                )
            upload_progress[upload_id]["files_processed"] = file_idx + 1

        upload_progress[upload_id]["current_step"] = "Extracting with AI..."
        upload_progress[upload_id]["overall_progress"] = 60
        combined_text = "\n\n".join(all_text_content)
        parsed_questions = (
            await _extract_questions_with_gemini(combined_text)
            if material_type == "question_paper"
            else await _extract_concepts_with_gemini(combined_text)
        ) if combined_text.strip() else []
        upload_progress[upload_id]["questions_extracted"] = len(parsed_questions)

        upload_progress[upload_id]["current_step"] = "Saving to database..."
        upload_progress[upload_id]["overall_progress"] = 80

        paper = papers_repo.create({
            "subject_id": subject_id,
            "file_name": first_filename,
            "file_path": stored_rels[0] if stored_rels else None,
            "file_size_bytes": None,
            "raw_text": combined_text[:200000] if combined_text else None,
            "processing_status": "completed",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "extraction_method": "llm_or_regex",
        })
        paper_id = str(paper.get("id"))
        questions_repo.create_many(paper_id, subject_id, parsed_questions)

        # Phase 3: government-track only — tag against syllabus taxonomy
        upload_progress[upload_id]["current_step"] = "Tagging units..."
        tagging_result = tag_after_upload(subject, paper_id)

        analysis_result = await generate_upload_analysis(subject_id, parsed_questions)

        upload_progress[upload_id]["status"] = "completed"
        upload_progress[upload_id]["overall_progress"] = 100
        upload_progress[upload_id]["current_step"] = "Complete!"
        upload_progress[upload_id]["end_time"] = datetime.now().isoformat()

        try:
            from ..routers.chat import _subject_summary_cache
            _subject_summary_cache.pop(subject_id, None)
        except Exception:
            pass

        return {
            "success": True,
            "upload_id": upload_id,
            "paper_id": paper_id,
            "message": f"Processed {len(files)} file{'' if len(files) == 1 else 's'} successfully",
            "material_type": material_type,
            "files": stored_rels,
            "extracted_data": {
                "questions_count": len(parsed_questions),
                "questions": [
                    {"text": q["text"], "type": q.get("question_type", ""), "marks": q.get("marks", 0)}
                    for q in parsed_questions[:20]
                ],
            },
            "analysis": analysis_result,
            "unit_tagging": tagging_result,
        }

    except HTTPException:
        upload_progress[upload_id]["status"] = "failed"
        raise
    except Exception as e:
        logger.error("Upload processing error: %s", e)
        upload_progress[upload_id]["status"] = "failed"
        upload_progress[upload_id]["errors"].append(str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}",
        )


async def _extract_questions_with_gemini(text: str) -> list:
    import json as _json
    client = get_llm_client("extraction")
    if not client.is_available:
        logger.warning("Extraction LLM not set — falling back to regex question parser")
        return _get_pdf_parser().parse_questions_from_text(text)
    try:
        truncated = text[:30_000]
        system_prompt = """Analyze the provided exam paper text and extract every question it contains.

For each question return a JSON object with these fields:
- "text": the full question text (string, required)
- "marks": marks/points value as integer, 0 if not specified
- "question_type": one of "Conceptual/explanation", "Calculation/problem", "Proof/derivation", "Definition", "Comparison", "Mixed/other"
- "difficulty": one of "Easy", "Medium", "Hard" based on marks and complexity
- "unit": unit or module reference if mentioned (string or null)

Return ONLY a valid JSON array of question objects. No markdown, no explanation, no code fences.
If no questions are found, return an empty array []."""
        raw = client.generate_text(f"{system_prompt}\n\nEXAM PAPER TEXT:\n{truncated}")
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        questions_raw = _json.loads(raw)
        if not isinstance(questions_raw, list):
            raise ValueError("Extraction LLM returned non-list JSON")
        questions = []
        for q in questions_raw:
            if not isinstance(q, dict) or not q.get("text", "").strip():
                continue
            questions.append({
                "text": q["text"].strip(),
                "marks": int(q.get("marks") or 0),
                "question_type": q.get("question_type") or "Mixed/other",
                "difficulty": q.get("difficulty") or "Medium",
                "unit": q.get("unit") or None,
                "keywords": [],
            })
        return questions
    except Exception as exc:
        logger.error("Extraction LLM failed: %s — regex fallback", exc)
        return _get_pdf_parser().parse_questions_from_text(text)


async def _extract_concepts_with_gemini(text: str) -> list:
    import json as _json
    client = get_llm_client("extraction")
    if not client.is_available:
        return _get_pdf_parser().parse_questions_from_text(text)
    try:
        truncated = text[:30_000]
        system_prompt = """Analyze the study material and extract key learning items as a JSON array with fields text, marks, question_type, difficulty, unit. Return ONLY JSON."""
        raw = client.generate_text(f"{system_prompt}\n\nSTUDY MATERIAL TEXT:\n{truncated}")
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        items_raw = _json.loads(raw)
        if not isinstance(items_raw, list):
            raise ValueError("non-list")
        items = []
        for item in items_raw:
            if not isinstance(item, dict) or not item.get("text", "").strip():
                continue
            items.append({
                "text": item["text"].strip(),
                "marks": 0,
                "question_type": item.get("question_type") or "Key Point",
                "difficulty": item.get("difficulty") or "Medium",
                "unit": item.get("unit") or None,
                "keywords": [],
            })
        return items
    except Exception as exc:
        logger.error("Concept extract failed: %s", exc)
        return _get_pdf_parser().parse_questions_from_text(text)


async def generate_upload_analysis(subject_id: str, parsed_questions: list):
    analysis = {
        "subject_id": subject_id,
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_questions": len(parsed_questions),
            "theory_questions": len([q for q in parsed_questions if "Conceptual" in q.get("question_type", "") or "Definition" in q.get("question_type", "")]),
            "numerical_questions": len([q for q in parsed_questions if "Calculation" in q.get("question_type", "")]),
            "proof_questions": len([q for q in parsed_questions if "Proof" in q.get("question_type", "")]),
        },
        "patterns": {},
        "predictions": {},
    }
    if parsed_questions:
        type_counts: Dict[str, int] = {}
        for q in parsed_questions:
            qt = q.get("question_type", "Mixed/other")
            type_counts[qt] = type_counts.get(qt, 0) + 1
        analysis["patterns"] = {"question_types": type_counts}
    return analysis


@router.get("/status/{upload_id}")
async def get_upload_status(upload_id: str, current_user: dict = Depends(get_current_user)):
    if upload_id not in upload_progress:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload not found")
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
        "end_time": progress_data.get("end_time"),
    }
