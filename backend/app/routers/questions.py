import os
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy import cast, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..services.supabase_first_auth import get_current_user_from_token

# Dependency for protected routes
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)

router = APIRouter(
    prefix="/questions",
    tags=["Questions"]
)


@router.get("/important", response_model=List[schemas.ImportantQuestion])
async def get_important_questions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get important/high-probability questions for the user's subjects"""
    try:
        subjects = db.query(models.Subject).filter(
            models.Subject.user_id == current_user["id"]
        ).all()

        if not subjects:
            return []

        subject_ids = [s.id for s in subjects]

        rows = (
            db.query(
                models.Question.id,
                models.Question.question_text,
                models.Question.difficulty,
                models.Question.topics_json,
                models.Question.created_at,
                models.Subject.name.label("subject_name"),
            )
            .join(models.QuestionPaper, models.Question.paper_id == models.QuestionPaper.id)
            .join(models.Subject, models.QuestionPaper.subject_id == models.Subject.id)
            .filter(models.Subject.id.in_(subject_ids))
            .limit(10)
            .all()
        )

        all_questions = []
        for q in rows:
            topics = q[3]
            first_topic = (
                topics[0] if isinstance(topics, list) and topics
                else (str(topics) if topics else "General")
            )
            all_questions.append({
                "id": str(q[0]),
                "subject": q[5],
                "topic": first_topic,
                "question": q[1][:100] + "..." if len(q[1]) > 100 else q[1],
                "difficulty": q[2] or "medium",
                "importance": "High",
                "last_asked": q[4].strftime("%Y-%m-%d") if q[4] else "2025-01-01",
            })

        # M-22: only return placeholder data in non-production environments
        if not all_questions and os.getenv("ENVIRONMENT", "development").lower() != "production":
            return [
                {
                    "id": str(uuid.uuid4()),
                    "subject": "Linear Algebra",
                    "topic": "Eigenvalues and Eigenvectors",
                    "question": "Find the eigenvalues of the matrix A = [[3, 1], [0, 2]]",
                    "difficulty": "medium",
                    "importance": "High",
                    "last_asked": "2025-12-15",
                },
                {
                    "id": str(uuid.uuid4()),
                    "subject": "Calculus",
                    "topic": "Definite Integrals",
                    "question": "Evaluate ∫₀¹ x² dx using fundamental theorem",
                    "difficulty": "easy",
                    "importance": "Very High",
                    "last_asked": "2025-12-20",
                },
            ]

        return all_questions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving important questions: {str(e)}",
        )


@router.get("/search", response_model=List[schemas.Question])
async def search_questions(
    subject: str = None,
    topic: str = None,
    difficulty: str = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search questions based on filters"""
    try:
        query = (
            db.query(models.Question)
            .join(models.QuestionPaper, models.Question.paper_id == models.QuestionPaper.id)
            .join(models.Subject, models.QuestionPaper.subject_id == models.Subject.id)
            # Only return questions belonging to the current user
            .filter(models.Subject.user_id == current_user["id"])
        )

        if subject:
            query = query.filter(models.Subject.name.ilike(f"%{subject}%"))

        if topic:
            # H-04: use PostgreSQL JSONB contains operator instead of cast+ilike.
            # topics_json is a JSON/JSONB column storing a list of strings.
            # The ? operator checks whether the text value exists as a top-level key/element.
            # For a JSON array of strings this correctly matches element membership.
            try:
                query = query.filter(
                    cast(models.Question.topics_json, JSONB).contains(f'"{topic}"')
                )
            except Exception:
                # Fallback for non-JSONB databases: cast to text and use ilike
                query = query.filter(
                    cast(models.Question.topics_json, String).ilike(f"%{topic}%")
                )

        if difficulty:
            query = query.filter(models.Question.difficulty == difficulty.lower())

        questions = query.limit(limit).all()
        return questions

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching questions: {str(e)}",
        )
