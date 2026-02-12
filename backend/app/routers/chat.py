from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from .. import models, schemas
from ..services import PrepIQService
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

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.post("/message", response_model=schemas.ChatResponse)
async def send_message(
    chat_request: schemas.ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subject belongs to user
    subject = db.query(models.Subject).filter(
        models.Subject.id == chat_request.subject_id,
        models.Subject.user_id == current_user["id"]
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Process the message using the service
    service = PrepIQService()
    result = service.chat_with_bot(
        db=db,
        user_id=current_user["id"],
        subject_id=chat_request.subject_id,
        message=chat_request.message
    )
    
    # Get the bot response
    bot_response = result["response"]
    
    # Find related questions from the subject's papers
    related_questions = db.query(models.Question).join(
        models.QuestionPaper
    ).filter(
        models.QuestionPaper.subject_id == chat_request.subject_id
    ).limit(3).all()
    
    # Prepare response with related questions
    related_questions_list = []
    for q in related_questions:
        # Get all years this question (or similar) appeared
        appeared_years = []
        if q.paper and q.paper.exam_year:
            appeared_years.append(q.paper.exam_year)
        
        # Find similar questions and their years
        if q.similar_question_ids:
            similar_questions = db.query(models.Question).join(
                models.QuestionPaper
            ).filter(
                models.Question.id.in_(q.similar_question_ids)
            ).all()
            
            for sq in similar_questions:
                if sq.paper and sq.paper.exam_year and sq.paper.exam_year not in appeared_years:
                    appeared_years.append(sq.paper.exam_year)
        
        # Sort years
        appeared_years.sort()
        
        related_questions_list.append({
            "text": q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
            "marks": q.marks,
            "appeared_years": appeared_years,
            "probability": "high" if q.is_repeated else "medium"
        })
    
    # Get real references from papers
    references = []
    recent_papers = db.query(models.QuestionPaper).filter(
        models.QuestionPaper.subject_id == chat_request.subject_id
    ).order_by(models.QuestionPaper.exam_year.desc()).limit(2).all()
    
    for paper in recent_papers:
        if paper.exam_year:
            # Get a sample question from this paper
            sample_q = db.query(models.Question).filter(
                models.Question.paper_id == paper.id
            ).first()
            
            if sample_q:
                references.append({
                    "type": "paper",
                    "paper_year": paper.exam_year,
                    "question": sample_q.question_text[:100] + "..." if len(sample_q.question_text) > 100 else sample_q.question_text
                })
    
    return {
        "message_id": result["message_id"],
        "response": bot_response,
        "related_questions": related_questions_list,
        "references": references,
        "suggested_actions": [
            "Add to revision",
            "Practice similar questions",
            "Take targeted mock test"
        ]
    }

@router.get("/history/{subject_id}", response_model=List[schemas.ChatHistoryResponse])
async def get_chat_history(
    subject_id: str,
    limit: int = 50,
    offset: int = 0,
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
    
    # Get chat history for the subject
    chat_history = db.query(models.ChatHistory).filter(
        models.ChatHistory.subject_id == subject_id,
        models.ChatHistory.user_id == current_user["id"]
    ).order_by(models.ChatHistory.created_at.desc()).offset(offset).limit(limit).all()
    
    # Format the response
    history_list = []
    for chat in chat_history:
        history_list.append({
            "id": chat.id,
            "timestamp": chat.created_at,
            "user_message": chat.user_message,
            "bot_response": chat.bot_response
        })
    
    return history_list

@router.delete("/clear")
async def clear_chat_history(
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
    
    # Delete chat history for the subject
    db.query(models.ChatHistory).filter(
        models.ChatHistory.subject_id == subject_id,
        models.ChatHistory.user_id == current_user["id"]
    ).delete()
    
    db.commit()
    
    return {"message": "Chat history cleared successfully"}