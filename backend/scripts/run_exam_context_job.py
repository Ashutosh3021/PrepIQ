#!/usr/bin/env python3
"""
Manual one-shot refresh of exam_context_cache for NEET / JEE.

Usage (from backend/):
  python scripts/run_exam_context_job.py
  python scripts/run_exam_context_job.py --force
  python scripts/run_exam_context_job.py --exam NEET

Does not start the scheduler; only runs the job body once.
Requires network + (optional) LLM API key for best summaries.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh exam_context_cache")
    parser.add_argument("--force", action="store_true", help="Ignore freshness window")
    parser.add_argument(
        "--exam",
        action="append",
        dest="exams",
        help="Exam name (repeatable). Default: NEET and JEE",
    )
    args = parser.parse_args()

    from app.services.exam_context_job import run_exam_context_job

    rows = run_exam_context_job(force=args.force, exams=args.exams)
    for row in rows:
        name = row.get("exam_name")
        summary = row.get("context_summary") or ""
        fetched = row.get("fetched_at")
        print("=" * 72)
        print(f"exam_name={name}  fetched_at={fetched}")
        print("-" * 72)
        print(summary)
        print()
    print(json.dumps(
        [
            {
                "exam_name": r.get("exam_name"),
                "fetched_at": r.get("fetched_at"),
                "summary_len": len(r.get("context_summary") or ""),
            }
            for r in rows
        ],
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
