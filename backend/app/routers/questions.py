"""Questions browse — Pyronites (Fix Phase D)."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, status

from .. import schemas
from ..services.pyronites_auth import get_current_user_from_token
from ..repositories import subjects as subjects_repo
from ..repositories import questions as questions_repo

router = APIRouter(prefix="/questions", tags=["Questions"])


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


@router.get("/important", response_model=List[schemas.ImportantQuestion])
async def get_important_questions(current_user: dict = Depends(get_current_user)):
    try:
        subjects = subjects_repo.list_for_user(current_user["id"])
        out = []
        for s in subjects:
            qs = questions_repo.list_for_subject(str(s.get("id")))[:10]
            for q in qs:
                text = str(q.get("question_text") or "")
                out.append(
                    {
                        "id": str(q.get("id")),
                        "subject": s.get("name") or "",
                        "topic": q.get("unit_name") or "General",
                        "question": text[:100] + ("..." if len(text) > 100 else ""),
                        "difficulty": str(q.get("difficulty") or "medium"),
                        "importance": "High",
                        "last_asked": str(q.get("created_at") or "")[:10] or "2025-01-01",
                    }
                )
                if len(out) >= 10:
                    return out
        return out
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
):
    try:
        subjects = subjects_repo.list_for_user(current_user["id"])
        if subject:
            subjects = [s for s in subjects if subject.lower() in str(s.get("name") or "").lower()]
        results = []
        for s in subjects:
            for q in questions_repo.list_for_subject(str(s.get("id"))):
                if difficulty and str(q.get("difficulty") or "").lower() != difficulty.lower():
                    continue
                if topic and topic.lower() not in str(q.get("unit_name") or "").lower():
                    continue
                results.append(
                    {
                        "id": str(q.get("id")),
                        "text": q.get("question_text") or "",
                        "marks": int(q.get("marks") or 0),
                        "difficulty": str(q.get("difficulty") or "medium"),
                        "subject_id": str(s.get("id")),
                        "topic": q.get("unit_name") or "General",
                        "created_at": q.get("created_at"),
                    }
                )
                if len(results) >= limit:
                    return results
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching questions: {str(e)}",
        )
