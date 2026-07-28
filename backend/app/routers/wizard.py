"""User setup wizard — Pyronites users table (Fix Phase D)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status

from .. import schemas
from ..services.pyronites_auth import get_current_user_from_token
from ..repositories import users as users_repo
from ..repositories import subjects as subjects_repo

router = APIRouter(prefix="/wizard", tags=["User Setup Wizard"])
logger = logging.getLogger(__name__)


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


@router.get("/status")
async def get_wizard_status(current_user: dict = Depends(get_current_user)):
    profile = users_repo.get(current_user["id"]) or {}
    days_until_exam = current_user.get("days_until_exam") or profile.get("days_until_exam")
    exam_date = current_user.get("exam_date") or profile.get("exam_date")
    if exam_date and not days_until_exam:
        try:
            if isinstance(exam_date, str):
                exam_dt = datetime.fromisoformat(exam_date.replace("Z", "+00:00"))
            else:
                exam_dt = exam_date
            if exam_dt.tzinfo is None:
                exam_dt = exam_dt.replace(tzinfo=timezone.utc)
            days_until_exam = max(0, (exam_dt - datetime.now(timezone.utc)).days)
        except Exception:
            pass
    return {
        "completed": bool(current_user.get("wizard_completed") or profile.get("wizard_completed")),
        "exam_name": current_user.get("exam_name") or profile.get("exam_name"),
        "days_until_exam": days_until_exam,
        "focus_subjects": current_user.get("focus_subjects") or profile.get("focus_subjects") or [],
        "study_hours_per_day": current_user.get("study_hours_per_day")
        or profile.get("study_hours_per_day"),
        "target_score": current_user.get("target_score") or profile.get("target_score"),
        "preparation_level": current_user.get("preparation_level")
        or profile.get("preparation_level"),
    }


@router.post("/step1", response_model=schemas.WizardStepResponse)
async def complete_step1(
    wizard_data: schemas.WizardStep1,
    current_user: dict = Depends(get_current_user),
):
    exam_date = datetime.now(timezone.utc) + timedelta(days=wizard_data.days_until_exam)
    users_repo.update(
        current_user["id"],
        {
            "exam_name": wizard_data.exam_name.strip(),
            "days_until_exam": wizard_data.days_until_exam,
            "exam_date": exam_date.isoformat(),
        },
    )
    return {
        "id": str(current_user["id"]),
        "email": current_user["email"],
        "full_name": current_user.get("full_name", ""),
        "access_token": None,
    }


@router.post("/step2", response_model=schemas.WizardStepResponse)
async def complete_step2(
    wizard_data: schemas.WizardStep2,
    current_user: dict = Depends(get_current_user),
):
    users_repo.update(
        current_user["id"],
        {
            "focus_subjects": wizard_data.focus_subjects,
            "study_hours_per_day": wizard_data.study_hours_per_day,
        },
    )
    existing = {str(s.get("name") or "").lower() for s in subjects_repo.list_for_user(current_user["id"])}
    for name in wizard_data.focus_subjects:
        if name and name.lower() not in existing:
            subjects_repo.create(
                current_user["id"],
                {
                    "name": name,
                    "code": f"SUB-{(name[:3] if len(name) >= 3 else name.ljust(3, 'X')).upper()}-{datetime.now().year}",
                    "semester": 1,
                    "academic_year": str(datetime.now().year),
                },
            )
    return {
        "id": str(current_user["id"]),
        "email": current_user["email"],
        "full_name": current_user.get("full_name", ""),
        "access_token": None,
    }


@router.post("/step3", response_model=schemas.WizardStepResponse)
async def complete_step3(
    wizard_data: schemas.WizardStep3,
    current_user: dict = Depends(get_current_user),
):
    users_repo.update(
        current_user["id"],
        {
            "target_score": wizard_data.target_score,
            "preparation_level": wizard_data.preparation_level,
        },
    )
    return {
        "id": str(current_user["id"]),
        "email": current_user["email"],
        "full_name": current_user.get("full_name", ""),
        "access_token": None,
    }


@router.post("/complete", response_model=schemas.WizardStepResponse)
async def complete_wizard(
    wizard_data: schemas.WizardCompletion,
    current_user: dict = Depends(get_current_user),
):
    profile = users_repo.get(current_user["id"]) or {}
    missing = []
    if not (profile.get("exam_name") or current_user.get("exam_name")):
        missing.append("exam_name")
    if not (profile.get("days_until_exam") or current_user.get("days_until_exam")):
        missing.append("days_until_exam")
    if not (profile.get("focus_subjects") or current_user.get("focus_subjects")):
        missing.append("focus_subjects")
    if not (profile.get("study_hours_per_day") or current_user.get("study_hours_per_day")):
        missing.append("study_hours_per_day")
    if not (profile.get("target_score") or current_user.get("target_score")):
        missing.append("target_score")
    if not (profile.get("preparation_level") or current_user.get("preparation_level")):
        missing.append("preparation_level")
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Cannot complete wizard. Missing: {', '.join(missing)}",
        )
    users_repo.update(current_user["id"], {"wizard_completed": True})
    return {
        "id": str(current_user["id"]),
        "email": current_user["email"],
        "full_name": current_user.get("full_name", ""),
        "access_token": None,
    }


@router.put("/update", response_model=schemas.WizardStepResponse)
async def update_wizard_data(
    update_data: schemas.UserUpdate,
    current_user: dict = Depends(get_current_user),
):
    fields = {}
    data = update_data.model_dump(exclude_unset=True) if hasattr(update_data, "model_dump") else {
        k: v for k, v in vars(update_data).items() if v is not None
    }
    for key in (
        "full_name",
        "college_name",
        "program",
        "year_of_study",
        "exam_name",
        "days_until_exam",
        "focus_subjects",
        "study_hours_per_day",
        "target_score",
        "preparation_level",
        "wizard_completed",
    ):
        if key in data and data[key] is not None:
            fields[key] = data[key]
    if "days_until_exam" in fields:
        fields["exam_date"] = (
            datetime.now(timezone.utc) + timedelta(days=int(fields["days_until_exam"]))
        ).isoformat()
    if fields:
        users_repo.update(current_user["id"], fields)
    return {
        "id": str(current_user["id"]),
        "email": current_user["email"],
        "full_name": fields.get("full_name") or current_user.get("full_name", ""),
        "access_token": None,
    }
