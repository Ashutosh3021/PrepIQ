"""
Papers API — local disk + Pyronites (Fix Phase A).
No Supabase Storage / SQLAlchemy.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status

from .. import schemas
from ..core.local_storage import delete_upload, resolve_path, save_upload
from ..services.pyronites_auth import get_current_user_from_token
from ..services.syllabus_gate import assert_pyq_upload_allowed
from ..repositories import subjects as subjects_repo
from ..repositories import papers as papers_repo
from ..repositories import questions as questions_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/papers", tags=["Papers"])

MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".txt",
}


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


def _safe_ext(filename: str) -> str:
    if not filename:
        return ""
    clean = filename.split("?")[0].rstrip()
    _, ext = os.path.splitext(clean)
    return ext.lower()


def _get_pdf_parser():
    from ..pdf_parser import PDFParser

    return PDFParser


@router.post("/upload", response_model=List[schemas.PaperUploadResponse])
async def upload_papers(
    files: List[UploadFile] = File(...),
    subject_id: str = Form(...),
    exam_year: Optional[int] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files provided")

    subject = subjects_repo.get_for_user(subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    assert_pyq_upload_allowed(subject)

    results = []
    for file in files:
        file_ext = _safe_ext(file.filename or "")
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{file.filename}': unsupported type '{file_ext}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

        file_content = b""
        total_size = 0
        while True:
            chunk = await file.read(8192)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File '{file.filename}' exceeds {MAX_FILE_SIZE // (1024 * 1024)} MB limit",
                )
            file_content += chunk

        clean_filename = (file.filename or "upload").split("?")[0].rstrip()
        try:
            rel_path = save_upload(file_content, clean_filename, current_user["id"], subject_id)
        except Exception as e:
            logger.error("Local save failed for %s: %s", file.filename, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Storage error for '{file.filename}': {str(e)}",
            )

        paper = papers_repo.create(
            {
                "subject_id": subject_id,
                "file_name": clean_filename,
                "file_path": rel_path,
                "file_size_bytes": total_size,
                "exam_year": exam_year,
                "processing_status": "processing",
            }
        )
        paper_id = str(paper.get("id"))

        try:
            abs_path = resolve_path(rel_path)
            parser = _get_pdf_parser()
            text_content = parser.extract_text(str(abs_path))
            questions_data = parser.parse_questions_from_text(text_content or "")
            # de-dupe lightly by normalized text
            seen = set()
            unique = []
            for q in questions_data:
                key = " ".join(str(q.get("text") or "").lower().split())
                if key and key not in seen:
                    seen.add(key)
                    unique.append(q)

            questions_repo.create_many(paper_id, subject_id, unique)
            papers_repo.update(
                paper_id,
                {
                    "raw_text": (text_content or "")[:200000],
                    "processing_status": "completed",
                    "processed_at": datetime.now(timezone.utc).isoformat(),
                    "extraction_method": "local_parser",
                },
            )
            results.append(
                {
                    "paper_id": paper_id,
                    "status": "completed",
                    "message": f"Successfully processed {len(unique)} questions",
                    "estimated_time": "0",
                    "questions_count": len(unique),
                    "metadata": {},
                    "images_extracted": 0,
                }
            )
        except Exception as e:
            logger.error("Processing failed for paper %s: %s", paper_id, e)
            papers_repo.update(
                paper_id,
                {
                    "processing_status": "failed",
                    "error_message": str(e),
                },
            )
            results.append(
                {
                    "paper_id": paper_id,
                    "status": "failed",
                    "message": f"Processing failed: {str(e)}",
                    "estimated_time": "0",
                    "questions_count": 0,
                    "metadata": {},
                    "images_extracted": 0,
                }
            )

    return results


@router.get("/{paper_id}/preview", response_model=schemas.PaperPreviewResponse)
async def get_paper_preview(
    paper_id: str,
    current_user: dict = Depends(get_current_user),
):
    paper = papers_repo.get(paper_id)
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    subject = subjects_repo.get_for_user(str(paper.get("subject_id")), current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    qs = questions_repo.list_for_paper(paper_id)[:5]
    raw = paper.get("raw_text") or ""
    return {
        "file_name": paper.get("file_name"),
        "text_preview": (raw[:500] if raw else "No text extracted yet"),
        "questions_extracted": [
            {
                "number": q.get("question_number"),
                "text": (str(q.get("question_text") or "")[:100] + "...")
                if len(str(q.get("question_text") or "")) > 100
                else q.get("question_text"),
                "marks": q.get("marks"),
                "unit": q.get("unit_name"),
            }
            for q in qs
        ],
    }


@router.get("/by-subject/{subject_id}", response_model=List[schemas.PaperResponse])
async def get_papers_by_subject(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    subject = subjects_repo.get_for_user(subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")

    papers = papers_repo.list_for_subject(subject_id)
    out = []
    for p in papers:
        pid = str(p.get("id"))
        count = len(questions_repo.list_for_paper(pid))
        row = dict(p)
        row["questions_extracted"] = count
        out.append(row)
    return out


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: str,
    current_user: dict = Depends(get_current_user),
):
    paper = papers_repo.get(paper_id)
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    subject = subjects_repo.get_for_user(str(paper.get("subject_id")), current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    if paper.get("file_path"):
        try:
            delete_upload(str(paper["file_path"]))
        except Exception as e:
            logger.warning("Local file delete failed: %s", e)

    # Best-effort: delete paper row (questions may remain orphaned if cascade absent)
    from app.repositories import base

    base.delete_eq("question_papers", "id", paper_id)
    return {"message": "Paper deleted successfully"}


@router.get("/upload-progress/{paper_id}", response_model=schemas.UploadProgressResponse)
async def get_upload_progress(
    paper_id: str,
    current_user: dict = Depends(get_current_user),
):
    paper = papers_repo.get(paper_id)
    if not paper:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    subject = subjects_repo.get_for_user(str(paper.get("subject_id")), current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")

    st = paper.get("processing_status") or "pending"
    progress = 100 if st == "completed" else (50 if st == "processing" else 0)
    message = "Processing completed" if st == "completed" else ("Processing..." if st == "processing" else st)
    return {
        "paper_id": paper_id,
        "status": st,
        "progress": progress,
        "message": message,
    }
