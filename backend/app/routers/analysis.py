"""
Analysis routes — deferred (Fix Phase D).

Core product path is predictions + tests on Pyronites.
These endpoints previously required SQLAlchemy/Supabase Postgres.
They return 503 until a full Pyronites rewrite (not in scope of A–D).
"""
from fastapi import APIRouter, Depends, Header, HTTPException

from ..services.pyronites_auth import get_current_user_from_token

router = APIRouter(prefix="/analysis", tags=["Analysis"])

_MSG = (
    "Analysis endpoints are temporarily unavailable after the Pyronites migration. "
    "Use /predictions and /tests. Analysis will return in a later phase."
)


async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


def _gone():
    raise HTTPException(status_code=503, detail=_MSG)


@router.get("/data")
async def get_analysis_data(current_user: dict = Depends(get_current_user)):
    _gone()


@router.get("/{subject_id}/frequency")
async def get_frequency_analysis(subject_id: str, current_user: dict = Depends(get_current_user)):
    _gone()


@router.get("/{subject_id}/weightage")
async def get_weightage_analysis(subject_id: str, current_user: dict = Depends(get_current_user)):
    _gone()


@router.get("/{subject_id}/repetitions")
async def get_repetition_analysis(subject_id: str, current_user: dict = Depends(get_current_user)):
    _gone()


@router.get("/{subject_id}/trends")
async def get_trend_analysis(subject_id: str, current_user: dict = Depends(get_current_user)):
    _gone()


@router.get("/important-questions/{subject_id}")
async def get_important_questions(subject_id: str, current_user: dict = Depends(get_current_user)):
    _gone()
