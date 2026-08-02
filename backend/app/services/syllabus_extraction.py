"""
Syllabus taxonomy extraction (Phase 2 — government track).

Pipeline:
  1. Resolve raw_pdf_ref under UPLOAD_ROOT
  2. PDFParser.extract_text (same stack as paper /upload)
  3. get_llm_client("extraction") → ordered Unit name list
  4. Validate; refuse empty/garbage → caller keeps extracted_taxonomy null
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.local_storage import resolve_path
from app.core.llm_provider import get_llm_client
from app.repositories import syllabus as syllabus_repo

logger = logging.getLogger(__name__)

MIN_UNITS = 3
MAX_UNITS = 80
TEXT_LIMIT = 40_000
MIN_TEXT_CHARS = 80


class SyllabusExtractionError(Exception):
    """User-facing extraction failure — do not persist a fake taxonomy."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _get_pdf_parser():
    from app.pdf_parser import PDFParser

    return PDFParser


def _strip_fences(raw: str) -> str:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def extract_text_from_syllabus_file(raw_pdf_ref: str) -> str:
    path = resolve_path(raw_pdf_ref)
    if not path.is_file():
        raise SyllabusExtractionError(
            "file_missing",
            f"Syllabus file not found on disk ({raw_pdf_ref}). Re-upload the PDF.",
        )
    try:
        # Prefer OCR fallback for scanned NTA PDFs when text layer is thin
        text = _get_pdf_parser().extract_text(str(path), ocr=False)
        if not (text or "").strip() or len(re.sub(r"\s+", "", text or "")) < 40:
            logger.info("Syllabus text thin — retrying with ocr=True")
            text = _get_pdf_parser().extract_text(str(path), ocr=True)
    except SyllabusExtractionError:
        raise
    except Exception as e:
        logger.error("Syllabus PDF text extraction failed: %s", e)
        raise SyllabusExtractionError(
            "text_extract_failed",
            f"Could not read text from the syllabus PDF: {e}. Try a clearer PDF or re-upload.",
        ) from e

    cleaned = (text or "").strip()
    if len(cleaned) < MIN_TEXT_CHARS:
        raise SyllabusExtractionError(
            "text_too_short",
            "Extracted almost no text from the syllabus PDF. "
            "It may be a scanned image without OCR support, or the wrong file. "
            "Re-upload a text-based official syllabus PDF.",
        )
    return cleaned[:TEXT_LIMIT]


def _normalize_units(raw_units: List[Any]) -> List[str]:
    out: List[str] = []
    seen = set()
    for item in raw_units:
        name = ""
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, dict):
            name = str(
                item.get("name")
                or item.get("unit")
                or item.get("unit_name")
                or item.get("title")
                or ""
            ).strip()
        if not name or len(name) < 2:
            continue
        # Drop pure page numbers / noise
        if re.fullmatch(r"\d+", name):
            continue
        key = re.sub(r"\s+", " ", name.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(name)
        if len(out) >= MAX_UNITS:
            break
    return out


def parse_taxonomy_with_llm(syllabus_text: str, exam_name: Optional[str] = None) -> List[str]:
    client = get_llm_client("extraction")
    if not client.is_available:
        raise SyllabusExtractionError(
            "llm_unavailable",
            "Extraction LLM is not configured (set GEMINI_API_KEY or EXTRACTION_API_KEY). "
            "Cannot build syllabus taxonomy without the model.",
        )

    exam_hint = (exam_name or "NEET/JEE").strip()
    prompt = f"""You extract the official UNIT-level syllabus taxonomy from exam syllabus text.

Exam context: {exam_hint}

Rules:
- Return ONLY a JSON object: {{"units": ["Unit 1 name", "Unit 2 name", ...]}}
- units must be an ordered list of top-level Unit (or Module/Chapter) titles as they appear.
- Prefer coarse unit headings (typically 8–30 items for NEET/JEE subjects), not every sub-point.
- Preserve official wording where possible; do not invent units that are not in the text.
- If the document is not a syllabus or units cannot be determined confidently, return:
  {{"units": [], "error": "short reason"}}
- No markdown fences, no commentary outside JSON.

SYLLABUS TEXT:
{syllabus_text}
"""

    try:
        try:
            parsed = client.generate_json(prompt, expect_list=False)
        except Exception:
            raw = client.generate_text(prompt)
            parsed = json.loads(_strip_fences(raw))

        if not isinstance(parsed, dict):
            raise SyllabusExtractionError(
                "parse_failed",
                "Model returned an unexpected shape. Re-upload or retry extraction.",
            )

        units_raw = parsed.get("units") or parsed.get("taxonomy") or parsed.get("items")
        if units_raw is None and isinstance(parsed.get("error"), str):
            raise SyllabusExtractionError(
                "llm_uncertain",
                f"Could not extract units from this PDF: {parsed.get('error')}. "
                "Try a clearer official syllabus PDF.",
            )

        if not isinstance(units_raw, list):
            raise SyllabusExtractionError(
                "parse_failed",
                "Model did not return a units list. Retry extraction or re-upload the syllabus.",
            )

        units = _normalize_units(units_raw)
        if len(units) < MIN_UNITS:
            err = parsed.get("error")
            extra = f" ({err})" if err else ""
            raise SyllabusExtractionError(
                "taxonomy_too_thin",
                f"Only found {len(units)} unit heading(s){extra}. "
                f"Need at least {MIN_UNITS} clear units. "
                "Re-upload the official subject syllabus PDF or retry after fixing the file.",
            )
        return units
    except SyllabusExtractionError:
        raise
    except Exception as e:
        logger.warning("Syllabus LLM taxonomy parse failed: %s", e)
        raise SyllabusExtractionError(
            "llm_failed",
            f"Syllabus unit extraction failed: {e}. Retry or re-upload a clearer PDF.",
        ) from e


def run_syllabus_extraction(
    subject_id: str,
    *,
    exam_name: Optional[str] = None,
    raw_pdf_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract taxonomy for an existing syllabus row (or provided raw_pdf_ref).

    On success: persists extracted_taxonomy + extracted_at.
    On failure: does NOT write an empty list; leaves taxonomy null; raises SyllabusExtractionError.
    """
    row = syllabus_repo.get_for_subject(subject_id)
    ref = raw_pdf_ref or (row or {}).get("raw_pdf_ref")
    if not ref:
        raise SyllabusExtractionError(
            "no_file",
            "No syllabus PDF on file for this subject. Upload the official syllabus first.",
        )

    text = extract_text_from_syllabus_file(str(ref))
    units = parse_taxonomy_with_llm(text, exam_name=exam_name)
    now = datetime.now(timezone.utc).isoformat()

    saved = syllabus_repo.upsert_for_subject(
        subject_id,
        {
            "raw_pdf_ref": str(ref),
            "extracted_taxonomy": units,
            "extracted_at": now,
        },
    )

    return {
        "success": True,
        "subject_id": subject_id,
        "syllabus_id": str(saved.get("id")),
        "raw_pdf_ref": str(ref),
        "extracted_taxonomy": units,
        "unit_count": len(units),
        "extracted_at": now,
        "pyq_upload_blocked": False,
        "message": f"Extracted {len(units)} syllabus units. PYQ upload is now allowed for this subject.",
    }
