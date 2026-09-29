"""Background job worker (implementation-plan.md 0.5).

Single daemon thread (Render runs --workers 1) drains the ``jobs`` table:
  family_assign   -> family_assignment.assign_for_paper
  rubric_backfill -> rubric_generation.backfill_for_paper   (Phase 1)

Thread pattern mirrors services/exam_context_job.py (start/stop from FastAPI
lifespan). Handlers must never raise out of their own module contract — but if
they do, the job is requeued with backoff up to MAX_ATTEMPTS, then failed.

Poll interval defaults to 15s to stay friendly to PyroCore free-tier rate
limits (base.read cache coalesces reads, but keep the steady-state floor high).
"""
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

from app.repositories import jobs as jobs_repo

logger = logging.getLogger(__name__)

POLL_SECONDS = float(os.getenv("JOB_POLL_SECONDS", "15") or "15")
MAX_ATTEMPTS = int(os.getenv("JOB_MAX_ATTEMPTS", "3") or "3")

# Plan 0.6 — nightly prune of uploads whose OCR text is already persisted.
PRUNE_INTERVAL_HOURS = float(os.getenv("JOB_PRUNE_INTERVAL_HOURS", "24") or "24")
PRUNE_AGE_DAYS = int(os.getenv("JOB_PRUNE_AGE_DAYS", "7") or "7")
# Keep the file when OCR looks mangled (short raw_text) — manual recovery path.
PRUNE_MIN_RAW_CHARS = 200

Handler = Callable[[Dict[str, Any]], Any]
_HANDLERS: Dict[str, Handler] = {}


def enqueue(kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Plan 0.5 contract: enqueue from routers without importing the repo."""
    return jobs_repo.enqueue(kind, payload)


def prune_stale_uploads() -> int:
    """Delete files of papers completed > PRUNE_AGE_DAYS with sane raw_text.

    Returns number of files deleted. Failures are logged per-paper and never
    raised — pruning is best-effort housekeeping.
    """
    from app.core.local_storage import delete_upload
    from app.repositories import base as base_repo
    from app.repositories import papers as papers_repo

    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, PRUNE_AGE_DAYS))
    deleted = 0
    rows = base_repo.select_eq("question_papers", "processing_status", "completed")
    for row in rows:
        try:
            file_path = str(row.get("file_path") or "")
            raw_text = str(row.get("raw_text") or "")
            if not file_path or len(raw_text) < PRUNE_MIN_RAW_CHARS:
                continue
            processed_raw = row.get("processed_at")
            if not processed_raw:
                continue
            text = str(processed_raw).replace("Z", "+00:00")
            processed = datetime.fromisoformat(text)
            if processed.tzinfo is None:
                processed = processed.replace(tzinfo=timezone.utc)
            if processed > cutoff:
                continue
            delete_upload(file_path)
            papers_repo.update(str(row.get("id")), {"file_path": None})
            deleted += 1
        except Exception as e:
            logger.warning("[jobs] prune skipped paper %s: %s", row.get("id"), e)
    if deleted:
        logger.info("[jobs] prune removed %d stale upload file(s)", deleted)
    return deleted


_last_prune = 0.0


def _maybe_prune() -> None:
    global _last_prune
    now = time.time()
    if now - _last_prune < PRUNE_INTERVAL_HOURS * 3600.0:
        return
    _last_prune = now
    try:
        prune_stale_uploads()
    except Exception as e:
        logger.exception("[jobs] prune run failed: %s", e)


def register_handler(kind: str, handler: Handler) -> None:
    _HANDLERS[kind] = handler


def _register_default_handlers() -> None:
    if "family_assign" not in _HANDLERS:
        def _family_assign(payload: Dict[str, Any]) -> Any:
            from app.services.family_assignment import assign_for_paper

            paper_id = str(payload.get("paper_id") or "")
            if not paper_id:
                raise ValueError("family_assign payload missing paper_id")
            return assign_for_paper(paper_id)

        register_handler("family_assign", _family_assign)

    if "rubric_backfill" not in _HANDLERS:
        def _rubric_backfill(payload: Dict[str, Any]) -> Any:
            from app.services.rubric_generation import backfill_for_paper, backfill_for_subject

            paper_id = str(payload.get("paper_id") or "")
            if paper_id:
                return backfill_for_paper(paper_id)
            subject_id = str(payload.get("subject_id") or "")
            if subject_id:
                return backfill_for_subject(subject_id)
            raise ValueError("rubric_backfill payload missing paper_id|subject_id")

        register_handler("rubric_backfill", _rubric_backfill)

    if "revision_seed" not in _HANDLERS:
        def _revision_seed(payload: Dict[str, Any]) -> Any:
            # Phase 3 (learning guide) implements the real seed; the stub
            # exists now so self-grade completion never trips "unknown kind".
            logger.info("[jobs] revision_seed stub (Phase 3): %s", payload)
            return {"stub": True, "phase": 3}

        register_handler("revision_seed", _revision_seed)


def _run_one(job: Dict[str, Any]) -> None:
    job_id = str(job.get("id"))
    kind = str(job.get("kind") or "")
    payload = jobs_repo.parse_payload(job)
    attempts = int(job.get("attempts") or 0) + 1

    handler = _HANDLERS.get(kind)
    if handler is None:
        jobs_repo.mark_failed(job_id, f"unknown job kind: {kind}")
        logger.error("[jobs] unknown kind %r (job %s)", kind, job_id)
        return

    try:
        result = handler(payload)
        jobs_repo.mark_done(job_id)
        logger.info("[jobs] %s done (job %s): %s", kind, job_id, str(result)[:300])
    except Exception as e:
        if attempts >= MAX_ATTEMPTS:
            jobs_repo.mark_failed(job_id, f"attempt {attempts}/{MAX_ATTEMPTS}: {e}")
            logger.error(
                "[jobs] %s FAILED permanently (job %s) after %d attempts: %s",
                kind, job_id, attempts, e,
            )
        else:
            jobs_repo.requeue(job_id, attempts, f"attempt {attempts}/{MAX_ATTEMPTS}: {e}")
            logger.warning(
                "[jobs] %s failed (job %s, attempt %d/%d) — requeued: %s",
                kind, job_id, attempts, MAX_ATTEMPTS, e,
            )


def drain_once(limit: int = 10) -> int:
    """Process queued jobs until empty (or limit). Returns processed count."""
    processed = 0
    attempted_ids = set()
    while processed < limit:
        job = jobs_repo.claim_next()
        if not job:
            break
        job_id = str(job.get("id"))
        if job_id in attempted_ids:
            # Requeued by a failure earlier in this drain (claim flipped it to
            # running again) — put it back and let the next wake handle it.
            jobs_repo.update(job_id, {"status": jobs_repo.STATUS_QUEUED})
            break
        attempted_ids.add(job_id)
        _run_one(job)
        processed += 1
    return processed


_stop_event = threading.Event()
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()


def _loop(log: logging.Logger) -> None:
    log.info("[jobs] worker thread started (poll=%ss max_attempts=%d)", POLL_SECONDS, MAX_ATTEMPTS)
    _register_default_handlers()
    while not _stop_event.is_set():
        _stop_event.wait(POLL_SECONDS)
        if _stop_event.is_set():
            break
        try:
            drain_once()
        except Exception as e:
            log.exception("[jobs] drain failed: %s", e)
        try:
            _maybe_prune()
        except Exception as e:
            log.exception("[jobs] prune tick failed: %s", e)
    log.info("[jobs] worker thread stopped")


def start_job_worker_thread(*, logger_: Optional[logging.Logger] = None) -> threading.Thread:
    global _thread
    log = logger_ or logger
    with _lock:
        if _thread is not None and _thread.is_alive():
            return _thread
        _stop_event.clear()
        t = threading.Thread(target=_loop, args=(log,), name="job-worker", daemon=True)
        t.start()
        _thread = t
        return t


def stop_job_worker_thread() -> None:
    global _thread
    _stop_event.set()
    t = _thread
    if t is not None and t.is_alive():
        t.join(timeout=5.0)
    _thread = None
