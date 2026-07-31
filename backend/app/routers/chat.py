"""
Chat / AI Tutor router.

Pyronites data plane for `/tutor` + `/tutor/invalidate-cache`.
Legacy `/message` and `/history/*` are unused by the current frontend
(tutor keeps history client-side) and return 501 until a later rewrite.
No SQLAlchemy / DATABASE_URL required for any route in this module.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import List, Optional, Dict
import logging

from .. import schemas
from ..core.llm_provider import get_llm_client
from ..services.supabase_first_auth import get_current_user_from_token
from ..repositories import subjects as subjects_repo
from ..repositories import papers as papers_repo
from ..repositories import questions as questions_repo

logger = logging.getLogger(__name__)

# ── In-memory subject summary cache (keyed by subject_id only) ───────────────
_subject_summary_cache: Dict[str, str] = {}

_LEGACY_MSG = (
    "This chat endpoint is not implemented after the Pyronites migration. "
    "Use POST /api/v1/chat/tutor (client-side conversation history). "
    "Server-backed /message and /history will return in a later phase."
)


async def get_current_user(authorization: str = Header(None)):
    """Bearer auth via Pyronites shim — no DATABASE_URL / get_db."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization)


def _not_implemented():
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_LEGACY_MSG)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

TUTOR_SYSTEM_PROMPT = """You are an expert academic tutor. Your personality is calm, patient, and supportive, with a touch of gentle warmth. You speak clearly and concisely, using simple language. Your teaching style is Socratic: you guide students to discover answers through thoughtful questions rather than just providing solutions.

Rules you must follow strictly:
- Always start by asking a diagnostic question to assess the student's current understanding.
- Never give the full answer immediately. Break problems into small, logical steps.
- After each step, ask a guiding question to keep the student engaged and thinking.
- Only provide the complete answer if the student explicitly asks for it (e.g., "Tell me the full answer" or "I give up").
- When the student makes a mistake, do not correct them directly. Instead, ask a question that leads them to recognize the error themselves.
- Use analogies and real-world examples when helpful, but keep them brief.
- Acknowledge correct answers with genuine, measured encouragement (e.g., "That's right," "Good reasoning," "Exactly").
- Maintain a warm, encouraging tone. Use occasional light humor, but never sarcasm or condescension.
- If the student seems frustrated, offer reassurance and suggest breaking the problem down further.
- Keep responses concise. Avoid long paragraphs. Prefer bullet points or numbered steps when listing multiple items.
- End each response with a question that moves the student to the next logical step.

Teaching guidelines:
- For math/science problems: ask what formulas or principles might apply, then guide through substitution and calculation.
- For conceptual questions: ask the student to explain the concept in their own words first, then fill gaps with targeted questions.
- For test preparation: ask about the student's current confidence level, then suggest targeted practice.

Your ultimate goal is to make the student feel supported, capable, and eager to learn. You are not a solution machine – you are a thinking coach."""


def _build_subject_knowledge_base(subject_id: str) -> str:
    """Build tutor KB text from Pyronites papers + questions (no SQLAlchemy)."""
    parts: List[str] = []

    try:
        papers = papers_repo.list_for_subject(subject_id) or []
    except Exception as exc:
        logger.warning("papers_repo.list_for_subject failed for %s: %s", subject_id, exc)
        papers = []

    for paper in papers:
        if not isinstance(paper, dict):
            continue
        raw = paper.get("raw_text") or ""
        if isinstance(raw, str) and raw.strip():
            parts.append(raw[:5000])

    try:
        questions = questions_repo.list_for_subject(subject_id) or []
    except Exception as exc:
        logger.warning("questions_repo.list_for_subject failed for %s: %s", subject_id, exc)
        questions = []

    q_lines: List[str] = []
    for q in questions[:100]:
        if not isinstance(q, dict):
            continue
        text = str(q.get("question_text") or "").strip()
        if not text:
            continue
        qtype = q.get("question_type") or "item"
        q_lines.append(f"- [{qtype}] {text[:300]}")

    if q_lines:
        parts.append("Extracted items:\n" + "\n".join(q_lines))

    return "\n\n".join(parts) if parts else ""


async def _summarize_with_bart(text: str) -> Optional[str]:
    """Optional Bytez summarizer — left non-default; returns None if missing."""
    try:
        from ..ml.external_api_wrapper import get_external_api

        api = get_external_api()
        if not api or not api.bytez_sdk:
            return None

        chunk = text[:3000]
        result = api.text_summarization(chunk)
        if result.get("success") and result.get("output"):
            summary = result["output"]
            if isinstance(summary, str) and len(summary.strip()) > 20:
                logger.info("BART summarization succeeded (%s chars)", len(summary))
                return summary.strip()
        return None
    except Exception as exc:
        logger.warning("BART summarization failed: %s", exc)
        return None


async def _summarize_with_chat_llm(text: str, subject_name: str) -> str:
    """Summarize via chat capability provider."""
    try:
        client = get_llm_client("chat")
        if not client.is_available:
            return ""
        prompt = (
            f"You are summarizing study material for the subject '{subject_name}'.\n"
            f"Create a concise knowledge base summary (max 500 words) covering the key concepts, "
            f"topics, definitions, and important points from the following content.\n\n"
            f"CONTENT:\n{text[:8000]}"
        )
        summary = client.generate_text(prompt)
        logger.info("Chat LLM summarization succeeded (%s chars)", len(summary))
        return summary
    except Exception as exc:
        logger.warning("Chat LLM summarization failed: %s", exc)
        return ""


async def _get_subject_summary(subject_id: str, subject_name: str) -> str:
    """
    Return a summarized KB string, or empty string when no materials exist.

    Empty string (not a placeholder sentence) so /tutor can omit KB context
    entirely when the subject has zero uploaded papers/questions.
    """
    if subject_id in _subject_summary_cache:
        return _subject_summary_cache[subject_id]

    raw_text = _build_subject_knowledge_base(subject_id)

    if not raw_text.strip():
        summary = ""
    else:
        summary = await _summarize_with_bart(raw_text)

        if not summary:
            logger.info("BART unavailable/failed — using chat LLM summarization fallback")
            summary = await _summarize_with_chat_llm(raw_text, subject_name)

        if not summary:
            summary = raw_text[:1500]

    _subject_summary_cache[subject_id] = summary
    return summary


# ── Legacy routes (unused by current FE) — deferred ──────────────────────────


@router.post("/message", response_model=schemas.ChatResponse)
async def send_message(
    chat_request: schemas.ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    _not_implemented()


@router.get("/history/{subject_id}", response_model=List[schemas.ChatHistoryResponse])
async def get_chat_history(
    subject_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    _not_implemented()


@router.delete("/history/{subject_id}")
async def clear_chat_history(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    _not_implemented()


# ── AI Tutor (Pyronites data plane) ──────────────────────────────────────────


@router.post("/tutor")
async def ai_tutor_chat(
    request: schemas.TutorChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    AI Tutor endpoint (Pyronites-backed).

    Pipeline:
      1. If subject_id provided → ownership-checked subject via subjects repo
      2. Build KB from papers/questions repos → summarize (BART optional / chat LLM)
      3. Inject summary + TUTOR_SYSTEM_PROMPT into chat LLM
      4. Return Socratic teaching response

    Zero papers → responds without KB context (no 500).
    No DATABASE_URL required.
    """
    try:
        message = request.message
        conversation_history = request.conversation_history or []
        subject_id = request.subject_id

        if not message:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Message is required",
            )

        client = get_llm_client("chat")
        if not client.is_available:
            return {
                "response": (
                    "I'm having trouble accessing my teaching capabilities. "
                    "Please try again later."
                ),
                "context": None,
            }

        subject_context_block = ""
        subject_name = "this subject"
        knowledge_base_active = False

        if subject_id:
            subject = subjects_repo.get_for_user(str(subject_id), current_user["id"])
            if subject:
                subject_name = str(subject.get("name") or "this subject")
                summary = await _get_subject_summary(str(subject_id), subject_name)
                # Only inject real material; empty summary = no papers → no KB block
                if summary and summary.strip():
                    knowledge_base_active = True
                    subject_context_block = (
                        f"\n\n--- SUBJECT KNOWLEDGE BASE: {subject_name} ---\n"
                        f"{summary}\n"
                        f"--- END KNOWLEDGE BASE ---\n"
                    )

        history_block = ""
        if conversation_history:
            history_block = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-5:]:
                role = "Student" if msg.get("role") == "user" else "Tutor"
                history_block += f"{role}: {msg.get('content', '')}\n"

        full_prompt = (
            f"{TUTOR_SYSTEM_PROMPT}"
            f"{subject_context_block}"
            f"{history_block}"
            f"\nStudent's current question: {message}"
            f"\n\nRespond as the AI Tutor:"
        )

        tutor_response = client.generate_text(full_prompt)

        return {
            "response": tutor_response,
            "context": {
                "conversation_length": len(conversation_history) + 1,
                "tutor_mode": "socratic",
                "subject": subject_name,
                "knowledge_base_active": knowledge_base_active,
                "model": client.model_name,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("AI Tutor error: %s", e)
        return {
            "response": (
                "I'm having trouble formulating a response right now. "
                "What specific aspect of this topic would you like to explore first?"
            ),
            "context": None,
        }


@router.post("/tutor/invalidate-cache")
async def invalidate_subject_cache(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Clear in-memory KB summary for a subject. No DATABASE_URL."""
    _subject_summary_cache.pop(subject_id, None)
    return {"message": f"Cache cleared for subject {subject_id}"}
