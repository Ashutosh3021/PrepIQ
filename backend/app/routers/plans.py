from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from ..database import get_db
from .. import models, schemas
from ..dependencies import get_prepiq_service
from ..services.supabase_first_auth import get_current_user_from_token


async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)


router = APIRouter(
    prefix="/plan",
    tags=["Study Plans"]
)


def _build_schedule_day(item: Dict[str, Any]) -> schemas.StudyPlanDay:
    """
    Convert a raw daily-schedule item from StudyPlanner into a StudyPlanDay schema.

    StudyPlanner returns:
      - "topics"          : list of dicts  {name, unit, importance, ...}
      - "recommended_hours": float
      - "focus_topics"    : list of str    (weak-area topic names)

    StudyPlanDay schema expects:
      - topics            : List[str]
      - recommended_hours : float
      - priority_topics   : List[str]
    """
    raw_topics = item.get("topics", [])
    # Convert topic dicts to plain strings; plain strings pass through unchanged
    topic_strings: List[str] = []
    for t in raw_topics:
        if isinstance(t, dict):
            topic_strings.append(t.get("name", str(t)))
        else:
            topic_strings.append(str(t))

    # C-12 / H-07: planner uses "focus_topics", schema uses "priority_topics"
    priority_topics = item.get("focus_topics", item.get("priority_topics", []))

    return schemas.StudyPlanDay(
        day=item["day"],
        date=item["date"],
        topics=topic_strings,
        recommended_hours=float(item.get("recommended_hours", 0)),
        priority_topics=priority_topics,
    )


@router.post("/generate", response_model=schemas.StudyPlanResponse)
async def generate_study_plan(
    plan_request: schemas.StudyPlanRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_prepiq_service()
    try:
        result = service.generate_study_plan(
            db=db,
            user_id=current_user["id"],
            subject_id=plan_request.subject_id,
            start_date=plan_request.start_date,
            exam_date=plan_request.exam_date
        )

        return {
            "plan_id": result["plan_id"],
            "subject_id": result["subject_id"],
            "total_days": result["total_days"],
            "daily_schedule": [
                _build_schedule_day(item) for item in result["daily_schedule"]
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/me", response_model=schemas.StudyPlanResponse)
async def get_current_study_plan(
    # BUG-L07: use /plan/me — no user_id in URL; identity comes from the token
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_prepiq_service()
    try:
        result = service.get_user_study_plan(db=db, user_id=current_user["id"])

        return {
            "plan_id": result["plan_id"],
            "subject_id": result["subject_id"],
            "total_days": result["total_days"],
            "daily_schedule": [
                _build_schedule_day(item) for item in result["daily_schedule"]
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{plan_id}", response_model=schemas.StudyPlanUpdateResponse)
async def update_study_plan(
    plan_id: str,
    plan_update: schemas.StudyPlanUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_prepiq_service()
    try:
        result = service.update_study_plan_progress(
            db=db,
            plan_id=plan_id,
            user_id=current_user["id"],
            days_completed=plan_update.days_completed,
            on_track=plan_update.on_track
        )

        # H-08: get updated plan and apply the same key-mapping fix
        updated_plan = service.get_user_study_plan(db=db, user_id=current_user["id"])

        return {
            "message": result["message"],
            "plan": {
                "plan_id": updated_plan["plan_id"],
                "subject_id": updated_plan["subject_id"],
                "total_days": updated_plan["total_days"],
                "daily_schedule": [
                    _build_schedule_day(item) for item in updated_plan["daily_schedule"]
                ],
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
