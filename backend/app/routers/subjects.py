from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import List, Any, Dict
import logging

from .. import schemas
from ..services.pyronites_auth import get_current_user_from_token
from ..repositories import subjects as subjects_repo
from ..repositories import papers as papers_repo
from ..repositories import predictions as predictions_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subjects", tags=["Subjects"])


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


def _enrich(subject: Dict[str, Any]) -> Dict[str, Any]:
    sid = str(subject.get("id"))
    subject = dict(subject)
    try:
        subject["papers_uploaded"] = len(papers_repo.list_for_subject(sid))
    except Exception:
        subject["papers_uploaded"] = subject.get("papers_uploaded") or 0
    try:
        subject["predictions_generated"] = len(
            predictions_repo.list_for_user_subject(str(subject.get("user_id")), sid)
        )
    except Exception:
        subject["predictions_generated"] = subject.get("predictions_generated") or 0
    return subject


@router.get("")
async def get_subjects(
    skip: int = 0,
    limit: int = 100,
    semester: int = None,
    year: str = None,
    search: str = None,
    current_user: dict = Depends(get_current_user),
):
    try:
        rows = subjects_repo.list_for_user(current_user["id"])
        if semester is not None:
            rows = [r for r in rows if r.get("semester") == semester]
        if year:
            rows = [r for r in rows if r.get("academic_year") == year]
        if search:
            q = search.lower()
            rows = [r for r in rows if q in str(r.get("name") or "").lower()]
        rows = rows[skip : skip + limit]
        return [_enrich(r) for r in rows]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subjects: {str(e)}",
        )


@router.post("")
async def create_subject(
    subject: schemas.SubjectCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        data = subject.model_dump() if hasattr(subject, "model_dump") else subject.dict()
        created = subjects_repo.create(current_user["id"], data)
        return _enrich(created)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subject: {str(e)}",
        )


@router.get("/{subject_id}")
async def get_subject(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    subject = subjects_repo.get_for_user(subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    return _enrich(subject)


@router.put("/{subject_id}")
async def update_subject(
    subject_id: str,
    subject_update: schemas.SubjectUpdate,
    current_user: dict = Depends(get_current_user),
):
    subject = subjects_repo.get_for_user(subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    data = subject_update.model_dump(exclude_unset=True) if hasattr(subject_update, "model_dump") else {
        k: v for k, v in vars(subject_update).items() if v is not None
    }
    updated = subjects_repo.update(subject_id, data) or {**subject, **data}
    return _enrich(updated)


@router.delete("/{subject_id}")
async def delete_subject(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    subject = subjects_repo.get_for_user(subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    subjects_repo.delete(subject_id)
    return {"message": "Subject deleted successfully"}
