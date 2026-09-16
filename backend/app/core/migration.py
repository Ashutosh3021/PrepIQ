"""
Startup migration — auto-provision missing Pyronites/PyroCore tables.

On every app start we verify that each required data table exists on the
connected PyroCore project. If a table is missing we attempt to create it
via the Pyronites management API (POST /api/projects/{pid}/tables).

This is idempotent: existing tables are left untouched.

Env vars required:
  PYRONITES_URL
  PYRONITES_KEY
  PYRONITES_PROJECT_ID
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_ran = False

# ── Required table schemas ────────────────────────────────────────────────────
# Each entry: (table_name, column_definitions)
# PyroCore accepts {"columns": [...]} for table creation.

_TABLES: List[Tuple[str, List[Dict[str, Any]]]] = [
    (
        "subjects",
        [
            {"name": "id", "type": "string", "primary_key": True},
            {"name": "user_id", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "code", "type": "string"},
            {"name": "semester", "type": "number"},
            {"name": "academic_year", "type": "string"},
            {"name": "exam_type", "type": "string"},
            {"name": "exam_name", "type": "string"},
            {"name": "university_name", "type": "string"},
            {"name": "total_marks", "type": "number"},
            {"name": "exam_date", "type": "string"},
            {"name": "exam_duration_minutes", "type": "number"},
            {"name": "papers_uploaded", "type": "number"},
            {"name": "predictions_generated", "type": "number"},
            {"name": "mock_tests_created", "type": "number"},
            {"name": "syllabus_json", "type": "json"},
            {"name": "created_at", "type": "string"},
            {"name": "updated_at", "type": "string"},
        ],
    ),
    (
        "question_papers",
        [
            {"name": "id", "type": "string", "primary_key": True},
            {"name": "subject_id", "type": "string"},
            {"name": "file_name", "type": "string"},
            {"name": "file_path", "type": "string"},
            {"name": "file_size_bytes", "type": "number"},
            {"name": "exam_year", "type": "number"},
            {"name": "exam_semester", "type": "number"},
            {"name": "total_marks", "type": "number"},
            {"name": "duration_minutes", "type": "number"},
            {"name": "raw_text", "type": "string"},
            {"name": "metadata_json", "type": "json"},
            {"name": "extraction_confidence", "type": "number"},
            {"name": "extraction_method", "type": "string"},
            {"name": "processing_status", "type": "string"},
            {"name": "error_message", "type": "string"},
            {"name": "processed_at", "type": "string"},
            {"name": "created_at", "type": "string"},
            {"name": "updated_at", "type": "string"},
        ],
    ),
    (
        "questions",
        [
            {"name": "id", "type": "string", "primary_key": True},
            {"name": "paper_id", "type": "string"},
            {"name": "subject_id", "type": "string"},
            {"name": "question_text", "type": "string"},
            {"name": "question_number", "type": "number"},
            {"name": "marks", "type": "number"},
            {"name": "unit_name", "type": "string"},
            {"name": "question_type", "type": "string"},
            {"name": "difficulty", "type": "string"},
            {"name": "correct_answer", "type": "string"},
            {"name": "topics_json", "type": "json"},
            {"name": "text_length", "type": "number"},
            {"name": "tagged_unit", "type": "string"},
            {"name": "tagging_confidence", "type": "number"},
            {"name": "created_at", "type": "string"},
        ],
    ),
    (
        "predictions",
        [
            {"name": "id", "type": "string", "primary_key": True},
            {"name": "user_id", "type": "string"},
            {"name": "subject_id", "type": "string"},
            {"name": "predicted_questions_json", "type": "json"},
            {"name": "total_questions", "type": "number"},
            {"name": "total_predicted_marks", "type": "number"},
            {"name": "unit_coverage_json", "type": "json"},
            {"name": "ml_analysis_json", "type": "json"},
            {"name": "prediction_accuracy_score", "type": "number"},
            {"name": "source_type", "type": "string"},
            {"name": "model_version", "type": "string"},
            {"name": "created_at", "type": "string"},
            {"name": "updated_at", "type": "string"},
        ],
    ),
    (
        "mock_tests",
        [
            {"name": "id", "type": "string", "primary_key": True},
            {"name": "user_id", "type": "string"},
            {"name": "subject_id", "type": "string"},
            {"name": "total_questions", "type": "number"},
            {"name": "total_marks", "type": "number"},
            {"name": "duration_minutes", "type": "number"},
            {"name": "difficulty_level", "type": "string"},
            {"name": "questions_json", "type": "json"},
            {"name": "start_time", "type": "string"},
            {"name": "end_time", "type": "string"},
            {"name": "is_completed", "type": "boolean"},
            {"name": "user_answers_json", "type": "json"},
            {"name": "score", "type": "number"},
            {"name": "percentage", "type": "number"},
            {"name": "correct_count", "type": "number"},
            {"name": "incorrect_count", "type": "number"},
            {"name": "skipped_count", "type": "number"},
            {"name": "weak_topics_json", "type": "json"},
            {"name": "strong_topics_json", "type": "json"},
            {"name": "created_at", "type": "string"},
        ],
    ),
    (
        "study_plans",
        [
            {"name": "id", "type": "string", "primary_key": True},
            {"name": "user_id", "type": "string"},
            {"name": "subject_id", "type": "string"},
            {"name": "total_days", "type": "number"},
            {"name": "daily_schedule_json", "type": "json"},
            {"name": "days_completed", "type": "number"},
            {"name": "on_track", "type": "boolean"},
            {"name": "created_at", "type": "string"},
            {"name": "updated_at", "type": "string"},
        ],
    ),
    (
        "chat_history",
        [
            {"name": "id", "type": "string", "primary_key": True},
            {"name": "user_id", "type": "string"},
            {"name": "subject_id", "type": "string"},
            {"name": "role", "type": "string"},
            {"name": "content", "type": "string"},
            {"name": "created_at", "type": "string"},
        ],
    ),
    (
        "syllabus",
        [
            {"name": "id", "type": "string", "primary_key": True},
            {"name": "subject_id", "type": "string"},
            {"name": "raw_pdf_ref", "type": "string"},
            {"name": "extracted_taxonomy", "type": "json"},
            {"name": "extracted_at", "type": "string"},
            {"name": "created_at", "type": "string"},
            {"name": "updated_at", "type": "string"},
        ],
    ),
]


def _check_table_exists_http(project_id: str, table_name: str, url: str, key: str) -> bool:
    """Check if a table exists via a lightweight GET request."""
    import httpx

    try:
        resp = httpx.get(
            f"{url.rstrip('/')}/api/projects/{project_id}/tables/{table_name}",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        # 200 = exists, 404 = not found
        if resp.status_code == 200:
            return True
        if resp.status_code == 404:
            return False
        # Other codes (429, 500) — assume exists to avoid false creation attempts
        logger.debug("Table %s check returned %s — assuming exists", table_name, resp.status_code)
        return True
    except Exception as e:
        logger.debug("Table %s existence check failed: %s", table_name, e)
        return True  # assume exists on network errors to avoid spurious creation


def _create_table_http(
    project_id: str, table_name: str, columns: List[Dict[str, Any]], url: str, key: str
) -> bool:
    """Create a table via the Pyronites/PyroCore management API."""
    import httpx

    payload = {"columns": columns}
    try:
        resp = httpx.post(
            f"{url.rstrip('/')}/api/projects/{project_id}/tables",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
            params={"table_name": table_name},
            timeout=15,
        )
        if resp.status_code in (200, 201):
            logger.info("[migration] Created table '%s' successfully", table_name)
            return True
        if resp.status_code == 409:
            # Table already exists — not an error
            logger.debug("[migration] Table '%s' already exists (409)", table_name)
            return True
        logger.warning(
            "[migration] Failed to create table '%s': HTTP %s — %s",
            table_name, resp.status_code, resp.text[:200],
        )
        return False
    except Exception as e:
        logger.warning("[migration] Failed to create table '%s': %s", table_name, e)
        return False


def _create_table_via_sdk(table_name: str, columns: List[Dict[str, Any]]) -> bool:
    """Try creating a table via the Pyronites SDK client (if available)."""
    try:
        from app.core.pyronites_client import get_pyronites_client

        client = get_pyronites_client()
        # Some pyronites SDK versions expose a table creation method
        if hasattr(client, "create_table"):
            client.create_table(table_name, columns)
            logger.info("[migration] SDK created table '%s'", table_name)
            return True
        if hasattr(client, "schema") and hasattr(client.schema, "create_table"):
            client.schema.create_table(table_name, columns)
            logger.info("[migration] SDK schema created table '%s'", table_name)
            return True
    except Exception as e:
        logger.debug("[migration] SDK table creation not available: %s", e)
    return False


def run_startup_migration() -> None:
    """Verify and auto-provision required Pyronites data tables.

    Called once during FastAPI lifespan startup. Safe to call multiple times
    (thread-safe, idempotent).
    """
    global _ran
    with _lock:
        if _ran:
            return
        _ran = True

    url = (os.getenv("PYRONITES_URL") or "").strip()
    key = (os.getenv("PYRONITES_KEY") or "").strip()
    project_id = (os.getenv("PYRONITES_PROJECT_ID") or "").strip()

    if not url or not key or not project_id:
        logger.warning(
            "[migration] Skipping — PYRONITES_URL, PYRONITES_KEY, or "
            "PYRONITES_PROJECT_ID not set"
        )
        return

    logger.info(
        "[migration] Checking %d required tables on project %s",
        len(_TABLES), project_id,
    )

    created_count = 0
    failed_count = 0

    for table_name, columns in _TABLES:
        if _check_table_exists_http(project_id, table_name, url, key):
            continue

        logger.info("[migration] Table '%s' not found — attempting creation", table_name)

        # Try SDK first, then raw HTTP
        success = _create_table_via_sdk(table_name, columns)
        if not success:
            success = _create_table_http(project_id, table_name, columns, url, key)

        if success:
            created_count += 1
        else:
            failed_count += 1
            logger.warning(
                "[migration] Could not create table '%s'. "
                "Create it manually via the PyroCore dashboard for project %s",
                table_name, project_id,
            )

    if created_count or failed_count:
        logger.info(
            "[migration] Done — created: %d, failed: %d, already existed: %d",
            created_count, failed_count, len(_TABLES) - created_count - failed_count,
        )
    else:
        logger.info("[migration] All %d tables present — no action needed", len(_TABLES))
