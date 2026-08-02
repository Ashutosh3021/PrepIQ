"""Web fetch + LLM summarize for exam_context_cache (internal only)."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import List

import requests

logger = logging.getLogger(__name__)

_DDG_URL = "https://html.duckduckgo.com/html/"
_USER_AGENT = (
    "Mozilla/5.0 (compatible; PrepIQExamContext/1.0; +https://github.com/Ashutosh3021/PrepIQ)"
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def search_web_snippets(query: str, *, max_results: int = 6) -> List[str]:
    """DuckDuckGo HTML snippets (no API key). Failures return []."""
    snippets: List[str] = []
    try:
        resp = requests.post(
            _DDG_URL,
            data={"q": query},
            headers={"User-Agent": _USER_AGENT},
            timeout=20,
        )
        resp.raise_for_status()
        html = resp.text
        titles = re.findall(
            r'class="result__a"[^>]*>(.*?)</a>',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        bodies = re.findall(
            r'class="result__snippet"[^>]*>(.*?)</(?:a|td|div)',
            html,
            flags=re.IGNORECASE | re.DOTALL,
        )

        def _clean(s: str) -> str:
            s = re.sub(r"<[^>]+>", " ", s)
            s = re.sub(r"\s+", " ", s).strip()
            return s

        n = min(max_results, max(len(titles), len(bodies)))
        for i in range(n):
            title = _clean(titles[i]) if i < len(titles) else ""
            body = _clean(bodies[i]) if i < len(bodies) else ""
            line = " — ".join(x for x in (title, body) if x)
            if line and line not in snippets:
                snippets.append(line[:400])
    except Exception as e:
        logger.warning("exam_context web search failed for %r: %s", query, e)
    return snippets


def search_queries_for_exam(exam_name: str) -> List[str]:
    year = datetime.now(timezone.utc).year
    name = exam_name.upper()
    return [
        f"{name} {year} exam syllabus change notification",
        f"{name} {year} paper difficulty analysis NTA",
        f"{name} {year} question paper pattern news",
        f"{name} exam latest updates paper setters",
    ]


def gather_raw_context(exam_name: str) -> str:
    lines: List[str] = []
    for q in search_queries_for_exam(exam_name):
        for snip in search_web_snippets(q, max_results=4):
            if snip not in lines:
                lines.append(snip)
        if len(lines) >= 12:
            break
    if not lines:
        return f"(no web snippets retrieved for {exam_name} at {_now_iso()})"
    return "\n".join(f"- {s}" for s in lines[:12])


def summarize_context(exam_name: str, raw_snippets: str) -> str:
    """Compact internal summary via existing LLM provider; snippet digest fallback."""
    from app.core.llm_provider import get_llm_client

    client = get_llm_client("prediction")
    prompt = f"""You are summarizing public news for an INTERNAL exam-prediction system.
Exam: {exam_name} (India medical/engineering entrance).

Raw web snippets:
{raw_snippets[:6000]}

Write a compact internal context_summary (120–220 words) covering only:
1. Any syllabus or exam-pattern change signals for the current/next cycle
2. Difficulty / paper-style commentary (harder/easier, more application-based, etc.)
3. Institutional/board (e.g. NTA) process notes that could affect paper direction
4. Explicit "no clear signal" if snippets are noise or unrelated

Rules:
- Factual, cautious language; do not invent specific dates or circular numbers not present.
- No advice to students; no marketing tone.
- Plain text only (no markdown headings, no bullet lists longer than 5 items).
- Do not quote long passages; paraphrase.
"""
    if client.is_available:
        try:
            text = client.generate_text(prompt)
            text = (text or "").strip()
            if text:
                return text[:2500]
        except Exception as e:
            logger.warning("exam_context LLM summarize failed for %s: %s", exam_name, e)

    clipped = raw_snippets.strip()
    if len(clipped) > 1200:
        clipped = clipped[:1200] + "…"
    return (
        f"{exam_name} external context digest (LLM unavailable; raw snippet compress). "
        f"Fetched {_now_iso()[:10]}. Sources:\n{clipped}"
    )
