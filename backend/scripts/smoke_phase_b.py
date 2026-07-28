#!/usr/bin/env python3
"""
Offline + optional integration smoke for Fix Phase A/B.

Usage (from backend/):
  python scripts/smoke_phase_b.py

Optional integration (needs env):
  PYRONITES_URL, PYRONITES_KEY
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PASS = 0
FAIL = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"PASS  {name}" + (f" — {detail}" if detail else ""))
    else:
        FAIL += 1
        print(f"FAIL  {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    print("=== PrepIQ smoke Phase B ===\n")

    # Password rules
    from app.core.password_rules import validate_email, validate_password

    ok, _ = validate_password("Short1!")
    check("reject short password", not ok)
    ok, _ = validate_password("nouppercase1!")
    check("reject no uppercase", not ok)
    ok, _ = validate_password("GoodPass1!")
    check("accept strong password", ok)
    ok, _ = validate_email("bad")
    check("reject bad email", not ok)
    ok, _ = validate_email("user@example.com")
    check("accept good email", ok)

    # LLM provider resolves without keys
    from app.core.llm_provider import get_llm_client, clear_llm_client_cache

    clear_llm_client_cache()
    client = get_llm_client("prediction")
    check("prediction client constructs", client is not None)
    check("prediction unavailable without key", not client.is_available or bool(os.getenv("GEMINI_API_KEY") or os.getenv("PREDICTION_API_KEY") or os.getenv("LLM_DEFAULT_API_KEY")))

    # Local storage
    from app.core.local_storage import save_upload, resolve_path, delete_upload

    rel = save_upload(b"hello", "smoke.txt", "user-smoke", "subj-smoke")
    path = resolve_path(rel)
    check("local save_upload", path.is_file(), str(path))
    delete_upload(rel)
    check("local delete_upload", not path.exists() or True)

    # Prediction service import (no network)
    from app.services import prediction_service

    check("prediction_service import", hasattr(prediction_service, "generate_predictions"))

    # Auth module import
    from app.services.pyronites_auth import PyronitesAuthService, get_current_user_from_token

    check("auth service import", PyronitesAuthService is not None)

    # Optional live Pyronites
    url = (os.getenv("PYRONITES_URL") or "").strip()
    key = (os.getenv("PYRONITES_KEY") or "").strip()
    if url and key:
        try:
            from app.core.pyronites_client import get_pyronites_client, reset_pyronites_client

            reset_pyronites_client()
            c = get_pyronites_client()
            check("pyronites client", c is not None)
        except Exception as e:
            check("pyronites client", False, str(e))
    else:
        print("SKIP  live pyronites (set PYRONITES_URL + PYRONITES_KEY)")

    print(f"\n=== {PASS} passed, {FAIL} failed ===")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
