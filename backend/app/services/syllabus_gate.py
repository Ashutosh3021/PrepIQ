"""Hard gate: government-track subjects require syllabus taxonomy before PYQ upload."""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import HTTPException, status

from app.repositories import syllabus as syllabus_repo

logger = logging.getLogger(__name__)

GATE_MESSAGE = (
    "Upload your official syllabus first. "
    "Government-track subjects (NEET/JEE) require a processed syllabus "
    "before past-paper (PYQ) upload."
)


def _taxonomy_ready(tax: Any) -> bool:
    if tax is None:
        return False
    if isinstance(tax, list):
        return len(tax) > 0
    if isinstance(tax, dict):
        return len(tax) > 0
    if isinstance(tax, str):
        return bool(tax.strip()) and tax.strip() not in ("null", "[]", "{}")
    return False


def subject_requires_syllabus_gate(subject: Dict[str, Any]) -> bool:
    return str(subject.get("exam_type") or "").strip().lower() == "government"


def get_syllabus_status(subject_id: str) -> Dict[str, Any]:
    try:
        row = syllabus_repo.get_for_subject(subject_id)
    except Exception as e:
        # Table missing / PyroCore 404 — treat as no syllabus yet, do not 500 the request
        logger.warning("get_syllabus_status failed for %s: %s", subject_id, e)
        return {
            "has_row": False,
            "raw_pdf_ref": None,
            "extracted_taxonomy": None,
            "taxonomy_ready": False,
            "extracted_at": None,
            "error": str(e),
        }
    tax = row.get("extracted_taxonomy") if row else None
    return {
        "has_row": row is not None,
        "raw_pdf_ref": (row or {}).get("raw_pdf_ref"),
        "extracted_taxonomy": tax,
        "taxonomy_ready": _taxonomy_ready(tax),
        "extracted_at": (row or {}).get("extracted_at"),
    }


def assert_pyq_upload_allowed(subject: Dict[str, Any]) -> None:
    """Raise 400 if government subject has no non-empty extracted_taxonomy."""
    if not subject_requires_syllabus_gate(subject):
        return
    status_info = get_syllabus_status(str(subject.get("id")))
    if not status_info["taxonomy_ready"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=GATE_MESSAGE,
        )
