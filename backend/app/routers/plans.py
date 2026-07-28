"""
Study plans — deferred (Fix Phase D).
Previously SQLAlchemy-backed PrepIQService.generate_study_plan.
"""
from fastapi import APIRouter, Depends, Header, HTTPException

from ..services.pyronites_auth import get_current_user_from_token

router = APIRouter(prefix="/plan", tags=["Study Plans"])

_MSG = (
    "Study plan endpoints are temporarily unavailable after the Pyronites migration. "
    "Core flow: subjects → papers → predictions → tests."
)


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


def _gone():
    raise HTTPException(status_code=503, detail=_MSG)


@router.post("/generate")
async def generate_study_plan(current_user: dict = Depends(get_current_user)):
    _gone()


@router.get("/me")
async def get_current_study_plan(current_user: dict = Depends(get_current_user)):
    _gone()


@router.get("/subject/{subject_id}")
async def get_study_plan_by_subject(subject_id: str, current_user: dict = Depends(get_current_user)):
    _gone()


@router.put("/{plan_id}")
async def update_study_plan(plan_id: str, current_user: dict = Depends(get_current_user)):
    _gone()
