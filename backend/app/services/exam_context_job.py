"""
Scheduled external context cache for government exams (NEET, JEE).

Purpose
-------
Maintain `exam_context_cache` rows (exam_name, context_summary, fetched_at) with
qualitative, cycle-level signal: paper-setter / board news, difficulty commentary,
syllabus-change notes. This is an *internal* signal only — never returned
verbatim on user-facing APIs.

Schedule (reuse keep-alive / lifespan thread pattern from trigger.py + main.py)
-----------------------------------------------------------------------------
Cadence: **monthly** by default (EXAM_CONTEXT_REFRESH_DAYS=30).

A single daemon thread started from FastAPI lifespan wakes every
EXAM_CONTEXT_CHECK_HOURS (default 24). On each wake it refreshes any exam whose
`fetched_at` is older than EXAM_CONTEXT_REFRESH_DAYS (or missing).

Why monthly: syllabus/board announcements are sparse; daily refresh wastes LLM
budget and adds noise. Adjust via env without code changes.

Web grounding: see exam_context_fetch.py (DuckDuckGo HTML + existing LLM client).
"""
from __future__ import annotations

import logging
import os
import re
import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Sequence

from app.services.exam_context_fetch import gather_raw_context, summarize_context

logger = logging.getLogger(__name__)

GOVERNMENT_EXAMS_V1: tuple = ("NEET", "JEE")

REFRESH_DAYS = int(os.getenv("EXAM_CONTEXT_REFRESH_DAYS", "30") or "30")
CHECK_HOURS = float(os.getenv("EXAM_CONTEXT_CHECK_HOURS", "24") or "24")
RUN_ON_STARTUP = (os.getenv("EXAM_CONTEXT_RUN_ON_STARTUP", "0") or "0").strip().lower() in (
    "1", "true", "yes", "on",
)

_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _parse_fetched_at(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def is_stale(row: Optional[Dict[str, Any]], *, refresh_days: int = REFRESH_DAYS) -> bool:
    if not row:
        return True
    fetched = _parse_fetched_at(row.get("fetched_at") or row.get("updated_at"))
    if fetched is None:
        return True
    return (_now() - fetched) >= timedelta(days=max(1, refresh_days))


def refresh_exam_context(exam_name: str, *, force: bool = False) -> Dict[str, Any]:
    from app.repositories import exam_context_cache as cache_repo

    name = (exam_name or "").strip().upper()
    if name not in GOVERNMENT_EXAMS_V1:
        raise ValueError(f"Unsupported exam_name {exam_name!r}; v1 allows {GOVERNMENT_EXAMS_V1}")

    existing = cache_repo.get_by_exam_name(name)
    if not force and not is_stale(existing):
        logger.info("exam_context skip %s (fresh)", name)
        return existing or {}

    raw = gather_raw_context(name)
    summary = summarize_context(name, raw)
    row = cache_repo.upsert_by_exam_name(name, summary, fetched_at=_now_iso())
    logger.info("exam_context refreshed %s summary_len=%d", name, len(summary or ""))
    return row


def run_exam_context_job(*, force: bool = False, exams: Optional[Sequence[str]] = None) -> List[Dict[str, Any]]:
    targets = [e.upper() for e in (exams or GOVERNMENT_EXAMS_V1)]
    out: List[Dict[str, Any]] = []
    for name in targets:
        try:
            out.append(refresh_exam_context(name, force=force))
        except Exception as e:
            logger.exception("exam_context job failed for %s: %s", name, e)
    return out


def _loop(logger_: logging.Logger) -> None:
    interval_sec = max(3600.0, CHECK_HOURS * 3600.0)
    logger_.info(
        "[exam-context] thread started refresh_days=%s check_hours=%s run_on_startup=%s",
        REFRESH_DAYS, CHECK_HOURS, RUN_ON_STARTUP,
    )
    if RUN_ON_STARTUP:
        try:
            run_exam_context_job(force=False)
        except Exception as e:
            logger_.exception("[exam-context] startup run failed: %s", e)

    while not _stop_event.is_set():
        _stop_event.wait(interval_sec)
        if _stop_event.is_set():
            break
        try:
            run_exam_context_job(force=False)
        except Exception as e:
            logger_.exception("[exam-context] scheduled run failed: %s", e)
    logger_.info("[exam-context] thread stopped")


def start_exam_context_thread(*, logger_: Optional[logging.Logger] = None) -> threading.Thread:
    global _thread
    log = logger_ or logger
    with _lock:
        if _thread is not None and _thread.is_alive():
            return _thread
        _stop_event.clear()
        t = threading.Thread(target=_loop, args=(log,), name="exam-context-cache", daemon=True)
        t.start()
        _thread = t
        return t


def stop_exam_context_thread() -> None:
    global _thread
    _stop_event.set()
    t = _thread
    if t is not None and t.is_alive():
        t.join(timeout=5.0)
    _thread = None


# Post-hoc adjustment (government_ml) — NOT a regression feature.
_HARDER_RE = re.compile(
    r"\b(harder|tougher|more\s+difficult|increased\s+difficulty|application[- ]heavy|"
    r"conceptual\s+shift|higher\s+order)\b",
    re.I,
)
_EASIER_RE = re.compile(
    r"\b(easier|simpler|lower\s+difficulty|more\s+scoring|straightforward)\b",
    re.I,
)
_SYLLABUS_RE = re.compile(
    r"\b(syllabus\s+chang|reduced\s+syllabus|deleted\s+topic|new\s+topic|"
    r"curriculum\s+update|NTA\s+notification)\b",
    re.I,
)


def parse_context_signals(summary: str) -> Dict[str, float]:
    text = summary or ""
    harder = len(_HARDER_RE.findall(text))
    easier = len(_EASIER_RE.findall(text))
    churn = len(_SYLLABUS_RE.findall(text))
    return {
        "difficulty_bias": max(-1.0, min(1.0, 0.25 * (harder - easier))),
        "syllabus_churn": max(0.0, min(1.0, 0.2 * churn)),
        "has_context": 1.0 if text.strip() else 0.0,
    }


def apply_context_post_hoc(
    predictions: List[Dict[str, Any]],
    context_summary: str,
) -> List[Dict[str, Any]]:
    """
    Soft post-hoc adjustment of ranked government_ml predictions.

    External context is exam-level qualitative text, not per-unit history.
    Using it as a 5th regression feature would be constant across units (no
    information) or require invented unit labels. Keep Logistic/Linear pure on
    the four hard signals; apply a small post-hoc nudge only:
      - difficulty_bias → ±8% on predicted marks
      - syllabus_churn → slight confidence damp
    Max |Δ confidence| ≈ 0.05. Reasoning notes the adjustment.
    """
    signals = parse_context_signals(context_summary)
    if not signals["has_context"]:
        return predictions

    diff = signals["difficulty_bias"]
    churn = signals["syllabus_churn"]
    out: List[Dict[str, Any]] = []
    for p in predictions:
        item = dict(p)
        conf = float(item.get("confidence_score") or 0.5)
        marks = float(item.get("predicted_marks") or item.get("marks") or 5)
        marks_adj = max(1.0, marks * (1.0 + 0.08 * diff))
        conf_adj = max(0.05, min(0.95, conf * (1.0 - 0.05 * churn) + 0.02 * diff))
        item["confidence_score"] = round(conf_adj, 4)
        item["predicted_marks"] = round(marks_adj, 2)
        item["marks"] = max(1, int(round(marks_adj)))
        item["reasoning"] = str(item.get("reasoning") or "") + (
            f" [external_context_adj difficulty_bias={diff:+.2f} syllabus_churn={churn:.2f}]"
        )
        item["context_adjustment"] = {"difficulty_bias": diff, "syllabus_churn": churn}
        out.append(item)

    out.sort(
        key=lambda x: (
            float(x.get("p_appear") or x.get("confidence_score") or 0),
            float(x.get("predicted_marks") or 0),
        ),
        reverse=True,
    )
    for i, it in enumerate(out, start=1):
        it["question_number"] = i
    return out


def load_context_summary_for_exam(exam_name: Optional[str]) -> str:
    if not exam_name:
        return ""
    try:
        from app.repositories import exam_context_cache as cache_repo
        row = cache_repo.get_by_exam_name(str(exam_name).strip())
        if row:
            return str(row.get("context_summary") or "")
    except Exception as e:
        logger.warning("load exam_context_cache failed: %s", e)
    return ""
