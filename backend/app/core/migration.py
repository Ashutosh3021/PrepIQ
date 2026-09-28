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

_TABLES: List[Tuple[str, str, List[Dict[str, Any]]]] = [
    (
        "subjects",
        "id",
        [
            {"name": "id", "type": "TEXT"},
            {"name": "user_id", "type": "TEXT"},
            {"name": "name", "type": "TEXT"},
            {"name": "code", "type": "TEXT"},
            {"name": "semester", "type": "INTEGER"},
            {"name": "academic_year", "type": "TEXT"},
            {"name": "total_marks", "type": "INTEGER"},
            {"name": "exam_date", "type": "TEXT"},
            {"name": "exam_duration_minutes", "type": "INTEGER"},
            {"name": "syllabus_json", "type": "JSON"},
            {"name": "papers_uploaded", "type": "INTEGER"},
            {"name": "predictions_generated", "type": "INTEGER"},
            {"name": "mock_tests_created", "type": "INTEGER"},
            {"name": "exam_type", "type": "TEXT"},
            {"name": "exam_name", "type": "TEXT"},
            {"name": "university_name", "type": "TEXT"},
            {"name": "created_at", "type": "TEXT"},
            {"name": "updated_at", "type": "TEXT"},
        ],
    ),
    (
        "question_papers",
        "id",
        [
            {"name": "id", "type": "TEXT"},
            {"name": "subject_id", "type": "TEXT"},
            {"name": "file_name", "type": "TEXT"},
            {"name": "file_path", "type": "TEXT"},
            {"name": "file_size_bytes", "type": "INTEGER"},
            {"name": "exam_year", "type": "INTEGER"},
            {"name": "exam_semester", "type": "TEXT"},
            {"name": "total_marks", "type": "INTEGER"},
            {"name": "duration_minutes", "type": "INTEGER"},
            {"name": "raw_text", "type": "TEXT"},
            {"name": "metadata_json", "type": "JSON"},
            {"name": "extraction_confidence", "type": "REAL"},
            {"name": "extraction_method", "type": "TEXT"},
            {"name": "processing_status", "type": "TEXT"},
            {"name": "error_message", "type": "TEXT"},
            {"name": "processed_at", "type": "TEXT"},
            {"name": "created_at", "type": "TEXT"},
            {"name": "updated_at", "type": "TEXT"},
        ],
    ),
    (
        "questions",
        "id",
        [
            {"name": "id", "type": "TEXT"},
            {"name": "paper_id", "type": "TEXT"},
            {"name": "subject_id", "type": "TEXT"},
            {"name": "question_text", "type": "TEXT"},
            {"name": "question_number", "type": "INTEGER"},
            {"name": "marks", "type": "INTEGER"},
            {"name": "unit_name", "type": "TEXT"},
            {"name": "question_type", "type": "TEXT"},
            {"name": "difficulty", "type": "TEXT"},
            {"name": "correct_answer", "type": "TEXT"},
            {"name": "topics_json", "type": "JSON"},
            {"name": "text_length", "type": "INTEGER"},
            {"name": "tagged_unit", "type": "TEXT"},
            {"name": "tagging_confidence", "type": "REAL"},
            {"name": "created_at", "type": "TEXT"},
        ],
    ),
    (
        "predictions",
        "id",
        [
            {"name": "id", "type": "TEXT"},
            {"name": "user_id", "type": "TEXT"},
            {"name": "subject_id", "type": "TEXT"},
            {"name": "predicted_questions_json", "type": "JSON"},
            {"name": "total_questions", "type": "INTEGER"},
            {"name": "total_predicted_marks", "type": "INTEGER"},
            {"name": "unit_coverage_json", "type": "JSON"},
            {"name": "ml_analysis_json", "type": "JSON"},
            {"name": "prediction_accuracy_score", "type": "REAL"},
            {"name": "source_type", "type": "TEXT"},
            {"name": "model_version", "type": "TEXT"},
            {"name": "created_at", "type": "TEXT"},
            {"name": "updated_at", "type": "TEXT"},
        ],
    ),
    (
        "mock_tests",
        "id",
        [
            {"name": "id", "type": "TEXT"},
            {"name": "user_id", "type": "TEXT"},
            {"name": "subject_id", "type": "TEXT"},
            {"name": "total_questions", "type": "INTEGER"},
            {"name": "total_marks", "type": "INTEGER"},
            {"name": "duration_minutes", "type": "INTEGER"},
            {"name": "difficulty_level", "type": "TEXT"},
            {"name": "questions_json", "type": "JSON"},
            {"name": "start_time", "type": "TEXT"},
            {"name": "end_time", "type": "TEXT"},
            {"name": "is_completed", "type": "BOOLEAN"},
            {"name": "user_answers_json", "type": "JSON"},
            {"name": "score", "type": "REAL"},
            {"name": "percentage", "type": "REAL"},
            {"name": "correct_count", "type": "INTEGER"},
            {"name": "incorrect_count", "type": "INTEGER"},
            {"name": "skipped_count", "type": "INTEGER"},
            {"name": "weak_topics_json", "type": "JSON"},
            {"name": "strong_topics_json", "type": "JSON"},
            {"name": "created_at", "type": "TEXT"},
        ],
    ),
    (
        "syllabus",
        "id",
        [
            {"name": "id", "type": "TEXT"},
            {"name": "subject_id", "type": "TEXT"},
            {"name": "raw_pdf_ref", "type": "TEXT"},
            {"name": "extracted_taxonomy", "type": "JSON"},
            {"name": "extracted_at", "type": "TEXT"},
            {"name": "created_at", "type": "TEXT"},
            {"name": "updated_at", "type": "TEXT"},
        ],
    ),
    (
        "unit_features",
        "id",
        [
            {"name": "id", "type": "TEXT"},
            {"name": "subject_id", "type": "TEXT"},
            {"name": "unit_name", "type": "TEXT"},
            {"name": "recurrence_count", "type": "INTEGER"},
            {"name": "recency_weight", "type": "REAL"},
            {"name": "marks_trend", "type": "REAL"},
            {"name": "last_asked_gap", "type": "INTEGER"},
            {"name": "computed_at", "type": "TEXT"},
            {"name": "created_at", "type": "TEXT"},
            {"name": "updated_at", "type": "TEXT"},
        ],
    ),
    (
        "exam_context_cache",
        "id",
        [
            {"name": "id", "type": "TEXT"},
            {"name": "exam_name", "type": "TEXT"},
            {"name": "context_summary", "type": "TEXT"},
            {"name": "fetched_at", "type": "TEXT"},
            {"name": "created_at", "type": "TEXT"},
            {"name": "updated_at", "type": "TEXT"},
        ],
    ),
    # Application user profiles + wizard targeting. This is a *data* table on
    # the project (distinct from PyroCore's auth records — the name "users" is
    # reserved server-side) and is the durable home for wizard state; it used
    # to live in a local SQLite file, which is wiped on every Render redeploy.
    (
        "user_profiles",
        "id",
        [
            {"name": "id", "type": "TEXT"},
            {"name": "email", "type": "TEXT"},
            {"name": "full_name", "type": "TEXT"},
            {"name": "college_name", "type": "TEXT"},
            {"name": "program", "type": "TEXT"},
            {"name": "year_of_study", "type": "INTEGER"},
            {"name": "exam_type", "type": "TEXT"},
            {"name": "exam_name", "type": "TEXT"},
            {"name": "university_name", "type": "TEXT"},
            {"name": "days_until_exam", "type": "INTEGER"},
            {"name": "exam_date", "type": "TEXT"},
            {"name": "focus_subjects", "type": "JSON"},
            {"name": "study_hours_per_day", "type": "INTEGER"},
            {"name": "target_score", "type": "INTEGER"},
            {"name": "preparation_level", "type": "TEXT"},
            {"name": "wizard_completed", "type": "BOOLEAN"},
            {"name": "created_at", "type": "TEXT"},
            {"name": "updated_at", "type": "TEXT"},
        ],
    ),
]


def _list_tables_http(project_id: str, url: str, key: str) -> List[str]:
    """Return the set of table names on the project.

    Raises RuntimeError when the listing cannot be obtained: a failed existence
    check used to be treated as "table exists", which is how a project with
    *zero* app tables booted "successfully" and 500'd on every request.
    """
    import httpx

    try:
        resp = httpx.get(
            f"{url.rstrip('/')}/api/projects/{project_id}/tables",
            headers={"Authorization": f"Bearer {key}"},
            timeout=15,
        )
    except Exception as e:
        raise RuntimeError(
            f"Could not list tables for project {project_id}: {e}"
        ) from e

    if resp.status_code == 429:
        raise RuntimeError(
            "PyroCore rate-limited the table listing (429) — cannot verify schema"
        )
    if resp.status_code >= 500:
        raise RuntimeError(
            f"PyroCore returned HTTP {resp.status_code} for the table listing"
        )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Unexpected HTTP {resp.status_code} listing tables: {resp.text[:200]}"
        )

    try:
        payload = resp.json()
    except ValueError as e:
        raise RuntimeError("PyroCore table listing was not valid JSON") from e

    names: List[str] = []
    for entry in payload if isinstance(payload, list) else payload.get("tables", []):
        if isinstance(entry, dict):
            name = entry.get("name") or entry.get("table")
            if name:
                names.append(str(name))
        elif isinstance(entry, str):
            names.append(entry)
    # An empty list is a valid answer (brand-new project) — the caller creates
    # whatever is missing. Only *unobtainable* answers are fatal.
    return names


def _create_table_http(
    project_id: str, table_name: str, primary_key: str, columns: List[Dict[str, Any]], url: str, key: str
) -> bool:
    """Create a table via the Pyronites/PyroCore management API.

    Body format (verified):
        {"table": "<name>", "primary_key": "<pk>", "columns": [{"name":"...", "type":"TEXT|INTEGER|REAL|JSON|BOOLEAN"}]}
    """
    import httpx

    payload = {"table": table_name, "primary_key": primary_key, "columns": columns}
    try:
        resp = httpx.post(
            f"{url.rstrip('/')}/api/projects/{project_id}/tables",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
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

    Raises RuntimeError when the schema cannot be verified or a required table
    cannot be created — the app must not serve traffic against a schema it
    cannot see. The guard flag is only latched on success so a transient
    PyroCore outage does not permanently mark the schema as verified.
    """
    global _ran
    with _lock:
        if _ran:
            return

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

    existing = set(_list_tables_http(project_id, url, key))
    missing = [t for t in _TABLES if t[0] not in existing]

    if not missing:
        logger.info("[migration] All %d tables present — no action needed", len(_TABLES))
        with _lock:
            _ran = True
        return

    logger.info(
        "[migration] Missing tables: %s — attempting creation",
        ", ".join(t[0] for t in missing),
    )

    created: List[str] = []
    failed: List[str] = []
    for table_name, primary_key, columns in missing:
        # SDK first, then raw HTTP
        success = _create_table_via_sdk(table_name, columns)
        if not success:
            success = _create_table_http(project_id, table_name, primary_key, columns, url, key)
        (created if success else failed).append(table_name)

    # Verify against the data plane rather than trusting creation responses.
    verified = set(_list_tables_http(project_id, url, key))
    still_missing = [name for name, _, _ in missing if name not in verified]

    if created:
        logger.info("[migration] Created: %s", ", ".join(created))
    if failed:
        logger.warning(
            "[migration] Create reported failure for: %s", ", ".join(failed)
        )

    if still_missing:
        raise RuntimeError(
            "Required tables missing on PyroCore project "
            f"{project_id}: {', '.join(still_missing)}. "
            "Create them via the PyroCore dashboard or fix Pyronites permissions."
        )

    logger.info("[migration] Verified %d tables present", len(verified))
    with _lock:
        _ran = True
