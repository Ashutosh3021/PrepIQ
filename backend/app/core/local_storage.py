"""
Local filesystem storage for question papers (Phase 2).

Pyronites has no storage basket — files live under UPLOAD_ROOT only.
DB stores metadata + relative path returned by save_upload.
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


def _upload_root() -> Path:
    root = (os.getenv("UPLOAD_ROOT") or "./uploads").strip()
    path = Path(root).expanduser()
    if not path.is_absolute():
        # Resolve relative to backend/ directory (parent of app/)
        backend_dir = Path(__file__).resolve().parent.parent.parent
        path = (backend_dir / path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sanitize_filename(filename: str) -> str:
    name = Path(filename or "upload.bin").name
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    if not name:
        name = "upload.bin"
    if len(name) > 180:
        stem, ext = os.path.splitext(name)
        name = stem[:160] + ext[:20]
    return name


def save_upload(
    file_bytes: bytes,
    filename: str,
    user_id: str,
    subject_id: str,
) -> str:
    """
    Persist file under UPLOAD_ROOT/{user_id}/{subject_id}/{uuid}_{safe_name}.

    Returns path relative to UPLOAD_ROOT (POSIX-style) for DB storage.
    """
    root = _upload_root()
    safe = _sanitize_filename(filename)
    rel_dir = Path(str(user_id)) / str(subject_id)
    dest_dir = root / rel_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{safe}"
    dest = dest_dir / stored_name
    dest.write_bytes(file_bytes)
    rel = (rel_dir / stored_name).as_posix()
    logger.info("Saved upload to %s (%s bytes)", dest, len(file_bytes))
    return rel


def resolve_path(stored_path: str) -> Path:
    """Resolve a stored relative path to an absolute path under UPLOAD_ROOT."""
    root = _upload_root()
    # Reject path traversal
    cleaned = stored_path.replace("\\", "/").lstrip("/")
    if ".." in cleaned.split("/"):
        raise ValueError("Invalid stored path")
    full = (root / cleaned).resolve()
    if not str(full).startswith(str(root.resolve())):
        raise ValueError("Path escapes upload root")
    return full


def read_upload(stored_path: str) -> bytes:
    path = resolve_path(stored_path)
    if not path.is_file():
        raise FileNotFoundError(f"Upload not found: {stored_path}")
    return path.read_bytes()


def delete_upload(stored_path: str) -> bool:
    try:
        path = resolve_path(stored_path)
        if path.is_file():
            path.unlink()
            return True
    except Exception as e:
        logger.warning("delete_upload failed for %s: %s", stored_path, e)
    return False
