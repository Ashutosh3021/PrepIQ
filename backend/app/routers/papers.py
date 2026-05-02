from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Header, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import os
from datetime import datetime, timezone
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import mimetypes

logger = logging.getLogger(__name__)

from ..database import get_db, get_new_db_session
from .. import models, schemas
from ..dependencies import get_prepiq_service

# Import from the new Supabase-first auth service
from ..services.supabase_first_auth import get_current_user_from_token

# Dependency for protected routes
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)

# Import SupabaseStorageService
from ..services.supabase_storage import SupabaseStorageService

router = APIRouter(
    prefix="/papers",
    tags=["Papers"]
)

# Supabase Storage bucket for question papers
STORAGE_BUCKET = "question-papers"

# File size limit (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf"}

@router.post("/upload", response_model=schemas.PaperUploadResponse)
async def upload_paper(
    file: UploadFile = File(...),
    subject_id: str = Form(...),   # H-25: must be Form(...) for multipart uploads
    exam_year: int = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {', '.join(ALLOWED_EXTENSIONS)} files are allowed"
        )
    
    # Validate file content type
    content_type = file.content_type
    if content_type != "application/pdf":
        # Try to detect content type from file extension if not provided
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a valid PDF"
            )
    
    # Check file size (10MB limit)
    # Read file in chunks to avoid memory issues
    file_content = b""
    total_size = 0
    
    while True:
        chunk = await file.read(8192)  # Read 8KB at a time
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds 10MB limit"
            )
        file_content += chunk
    
    # Reset file pointer to beginning
    await file.seek(0)
    
    # Validate subject exists and belongs to user
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.user_id == current_user["id"]
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Generate unique filename to avoid conflicts
    unique_filename = f"{uuid.uuid4()}_{current_user['id']}_{subject_id}_{file.filename}"
    
    # Upload file to Supabase Storage
    try:
        public_url = SupabaseStorageService.upload_file(
            file_content, 
            unique_filename, 
            STORAGE_BUCKET
        )
        s3_key = unique_filename  # Store the key used in Supabase
    except Exception as e:
        logger.error(f"Error uploading file to Supabase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error uploading file to storage"
        )
    
    # Create paper record
    paper = models.QuestionPaper(
        subject_id=subject_id,
        file_name=file.filename,
        file_path=public_url,  # Store the public URL
        s3_key=s3_key,  # Store the key used in Supabase
        file_size_bytes=total_size,
        exam_year=exam_year,
        processing_status="processing"
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)
    
    # Process the paper asynchronously with a NEW session for the thread
    try:
        service = get_prepiq_service()
        
        # Create a wrapper that creates its own session for thread-safe DB access
        def process_with_new_session():
            thread_db = get_new_db_session()
            try:
                return service.process_uploaded_paper(thread_db, paper.id)
            finally:
                thread_db.close()
        
        result = await asyncio.get_event_loop().run_in_executor(
            ThreadPoolExecutor(),
            process_with_new_session
        )
        
        paper.processing_status = "completed"
        paper.processed_at = datetime.now(timezone.utc)
        db.commit()
        
        return {
            "paper_id": paper.id,
            "status": "completed",
            "message": result["message"],
            "estimated_time": "2-3 minutes",
            "questions_count": result.get("questions_count", 0),
            "metadata": result.get("metadata", {}),
            "images_extracted": result.get("images_extracted", 0)
        }
    except Exception as e:
        paper.processing_status = "failed"
        paper.error_message = str(e)
        db.commit()
        
        logger.error(f"Error processing paper {paper.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing paper: {str(e)}"
        )

# More specific routes must come before parameterized routes to avoid conflicts

@router.get("/{paper_id}/preview", response_model=schemas.PaperPreviewResponse)
async def get_paper_preview(
    paper_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify paper belongs to user
    paper = db.query(models.QuestionPaper).join(models.Subject).filter(
        models.QuestionPaper.id == paper_id,
        models.Subject.user_id == current_user["id"]
    ).first()
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    
    # Get associated questions
    questions = db.query(models.Question).filter(
        models.Question.paper_id == paper_id
    ).limit(5).all()  # Limit to first 5 questions for preview
    
    return {
        "file_name": paper.file_name,
        "text_preview": paper.raw_text[:500] if paper.raw_text else "No text extracted yet",
        "questions_extracted": [
            {
                "number": q.question_number,
                "text": q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
                "marks": q.marks,
                "unit": q.unit_name
            }
            for q in questions
        ]
    }


@router.get("/by-subject/{subject_id}", response_model=List[schemas.PaperResponse])
async def get_papers_by_subject(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
    
    papers = db.query(models.QuestionPaper).filter(
        models.QuestionPaper.subject_id == subject_id
    ).all()

    # H-26: compute question counts in a single query instead of N+1 per-paper queries
    paper_ids = [p.id for p in papers]
    counts = dict(
        db.query(models.Question.paper_id, func.count(models.Question.id))
        .filter(models.Question.paper_id.in_(paper_ids))
        .group_by(models.Question.paper_id)
        .all()
    ) if paper_ids else {}

    for paper in papers:
        paper.questions_extracted = counts.get(paper.id, 0)

    return papers

@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify paper belongs to user
    paper = db.query(models.QuestionPaper).join(models.Subject).filter(
        models.QuestionPaper.id == paper_id,
        models.Subject.user_id == current_user["id"]
    ).first()
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    
    # Delete the file from Supabase Storage
    try:
        if paper.s3_key:  # Use the s3_key to identify the file in Supabase
            SupabaseStorageService.delete_file(paper.s3_key, STORAGE_BUCKET)
    except Exception as e:
        logger.error(f"Error deleting file from Supabase: {str(e)}")
        # Continue with database deletion even if storage deletion fails
    
    # Delete the database record
    db.delete(paper)
    db.commit()
    
    return {"message": "Paper deleted successfully"}


@router.get("/upload-progress/{paper_id}", response_model=schemas.UploadProgressResponse)
async def get_upload_progress(
    paper_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify paper belongs to user
    paper = db.query(models.QuestionPaper).join(models.Subject).filter(
        models.QuestionPaper.id == paper_id,
        models.Subject.user_id == current_user["id"]
    ).first()
    
    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found"
        )
    
    # Get progress from database (BUG-B12 fix - use DB instead of in-memory dict)
    status = paper.processing_status or "pending"
    progress = 0 if status != "completed" else 100
    message = "Processing..." if status != "completed" else "Processing completed"
    
    return {
        "paper_id": paper_id,
        "status": status,
        "progress": progress,
        "message": message
    }