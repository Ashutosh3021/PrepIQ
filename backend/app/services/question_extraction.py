"""Question/concept extraction — LLM phrasing pass over raw extracted text.

Inspired by the STT reference project's ``pipeline.py``: instead of feeding
raw (often OCR-mangled) text straight to the line-anchored regex parser, a
per-material-type prompt repairs the text and returns structured JSON.

Free-tier guards (implementation-plan 0.3):
  - every call goes through ``llm_cache.cached_json`` — one payment per
    distinct chunk prompt, ever;
  - no API key or any failure falls back to the deterministic regex parser
    (``PDFParser.parse_questions_from_text``), so uploads never block on LLM.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

from app.core.llm_provider import get_llm_client
from app.pdf_parser import PDFParser
from app.services import llm_cache

logger = logging.getLogger(__name__)

_CHUNK_LIMIT = 24_000
_NS = "extraction"

QUESTION_PROMPT = """You are an exam-paper OCR phraser. The input is raw text from a university exam paper (often scanned), so it may contain OCR artefacts.

Repair the text and extract every question:
- Fix OCR errors: split or glued words, line-break damage, common confusions (l/1/I, O/0, rn/m), stray dots and artefacts.
- Rejoin each question into one flowing paragraph; preserve original wording apart from OCR repair.
- Normalise numbering (1., Q1, (a), i)); use section/unit headers to attribute "unit" to the questions that follow.
- Some exports delimit questions with metadata chips like "2025 · Q141 · MCQ" instead of numbers — split on those too, and drop the chip lines.
- Discard headers, footers, dates, roll numbers, instructions, "answer all/any" lines, site chrome ("Includes diagram", "Quick practice", "All papers"), lone option-label/value fragments, and answer-key or explanatory text.
- Never invent questions. Skip any that are unrecoverable.
- Take marks and unit/module from the text when present; otherwise use 0 and null.

Return ONLY a valid JSON array, no markdown fences and no commentary:
[{"text": "...", "marks": 0, "unit": null, "question_type": "Conceptual/explanation", "difficulty": "Medium"}]
question_type must be one of: "Conceptual/explanation", "Calculation/problem", "Proof/derivation", "Definition", "Comparison", "Mixed/other".
difficulty must be one of: "Easy", "Medium", "Hard"."""

CONCEPT_PROMPT = """You are a study-material analyst. Extract the key learning items (concepts, definitions, formulas, procedures) worth revising from the input text.

- Repair OCR artefacts (split words, line-break damage) before writing each item.
- One self-contained item per entry; do not merge unrelated ideas.
- Never invent content that is not present in the input.

Return ONLY a valid JSON array, no markdown fences and no commentary:
[{"text": "...", "marks": 0, "unit": null, "question_type": "Definition", "difficulty": "Easy"}]
question_type must be one of: "Conceptual/explanation", "Calculation/problem", "Proof/derivation", "Definition", "Comparison", "Mixed/other".
difficulty must be one of: "Easy", "Medium", "Hard"."""


def _chunks(text: str, limit: int = _CHUNK_LIMIT) -> List[str]:
    """Split on page markers when possible; hard-split pathological pages."""
    if len(text) <= limit:
        return [text]
    pieces = re.split(r"(?=\[Page \d)", text)
    out: List[str] = []
    buf = ""
    for piece in pieces:
        while len(piece) > limit:
            if buf:
                out.append(buf)
                buf = ""
            out.append(piece[:limit])
            piece = piece[limit:]
        if len(buf) + len(piece) <= limit:
            buf += piece
        else:
            if buf:
                out.append(buf)
            buf = piece
    if buf:
        out.append(buf)
    return [c for c in out if c.strip()]


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _parse_items(raw: str) -> List[Dict[str, Any]]:
    parsed = json.loads(_strip_fences(raw))
    if isinstance(parsed, dict):
        parsed = parsed.get("questions") or parsed.get("items") or []
    if not isinstance(parsed, list):
        raise ValueError("extraction LLM returned non-list JSON")
    items: List[Dict[str, Any]] = []
    for q in parsed:
        if not isinstance(q, dict):
            continue
        q_text = str(q.get("text") or "").strip()
        if not q_text:
            continue
        try:
            marks = int(q.get("marks") or 0)
        except (TypeError, ValueError):
            marks = 0
        items.append({
            "text": q_text,
            "marks": marks,
            "question_type": q.get("question_type") or "Mixed/other",
            "difficulty": q.get("difficulty") or "Medium",
            "unit": q.get("unit") or None,
            "keywords": [],
        })
    return items


def _llm_chunk(client: Any, prompt: str, chunk: str) -> List[Dict[str, Any]]:
    full_prompt = f"{prompt}\n\nSOURCE TEXT:\n{chunk}"

    def fn() -> List[Dict[str, Any]]:
        return _parse_items(client.generate_text(full_prompt))

    cached = llm_cache.cached_json(_NS, _NS, full_prompt, fn)
    return [dict(q) for q in cached]


def extract_questions(
    text: str, material_type: str = "question_paper"
) -> List[Dict[str, Any]]:
    """Return structured items for uploaded material.

    material_type == "question_paper" → exam questions; anything else →
    study-material learning items (same output schema).
    """
    if not text or not text.strip():
        return []

    prompt = QUESTION_PROMPT if material_type == "question_paper" else CONCEPT_PROMPT
    client = get_llm_client("extraction")
    if not client.is_available:
        logger.info(
            "Extraction LLM not set — regex fallback (material_type=%s)",
            material_type,
        )
        return PDFParser.parse_questions_from_text(text)

    results: List[Dict[str, Any]] = []
    chunks = _chunks(text)
    for idx, chunk in enumerate(chunks):
        try:
            items = _llm_chunk(client, prompt, chunk)
        except Exception as exc:
            logger.warning(
                "Extraction LLM failed chunk %d/%d: %s — regex fallback",
                idx + 1, len(chunks), exc,
            )
            items = PDFParser.parse_questions_from_text(chunk)
        results.extend(items)

    seen: set = set()
    merged: List[Dict[str, Any]] = []
    for q in results:
        key = " ".join(str(q.get("text") or "").lower().split())[:120]
        if not key or key in seen:
            continue
        seen.add(key)
        if "number" not in q:
            q["number"] = len(merged) + 1
        merged.append(q)
    return merged
