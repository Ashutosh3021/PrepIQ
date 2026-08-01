from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File
from typing import List, Any, Dict
import logging

from .. import schemas
from ..services.pyronites_auth import get_current_user_from_token
from ..services.syllabus_gate import get_syllabus_status, subject_requires_syllabus_gate
from ..core.local_storage import save_upload
from ..repositories import subjects as subjects_repo
from ..repositories import papers as papers_repo
from ..repositories import predictions as predictions_repo
from ..repositories import syllabus as syllabus_repo

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
    if subject_requires_syllabus_gate(subject):
        subject["syllabus_status"] = get_syllabus_status(sid)
        subject["pyq_upload_blocked"] = not subject["syllabus_status"]["taxonomy_ready"]
    else:
        subject["syllabus_status"] = None
        subject["pyq_upload_blocked"] = False
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


@router.post("/{subject_id}/syllabus")
async def upload_syllabus(
    subject_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Store syllabus PDF reference only. OCR/taxonomy extraction is Phase 2."""
    subject = subjects_repo.get_for_user(subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    if not subject_requires_syllabus_gate(subject):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Syllabus upload is only required for government-track (NEET/JEE) subjects.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    rel = save_upload(
        content,
        file.filename or "syllabus.pdf",
        current_user["id"],
        subject_id,
    )
    row = syllabus_repo.upsert_for_subject(
        subject_id,
        {
            "raw_pdf_ref": rel,
            "extracted_taxonomy": None,
            "extracted_at": None,
        },
    )
    return {
        "success": True,
        "subject_id": subject_id,
        "syllabus_id": str(row.get("id")),
        "raw_pdf_ref": rel,
        "extracted_taxonomy": None,
        "message": (
            "Syllabus file stored. Taxonomy extraction runs in a later step — "
            "PYQ upload stays blocked until extracted_taxonomy is populated."
        ),
        "pyq_upload_blocked": True,
    }


@router.get("/{subject_id}/syllabus")
async def get_subject_syllabus(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    subject = subjects_repo.get_for_user(subject_id, current_user["id"])
    if not subject:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subject not found")
    st = get_syllabus_status(subject_id)
    return {
        "subject_id": subject_id,
        "exam_type": subject.get("exam_type"),
        "requires_syllabus": subject_requires_syllabus_gate(subject),
        **st,
        "pyq_upload_blocked": subject_requires_syllabus_gate(subject) and not st["taxonomy_ready"],
    }
