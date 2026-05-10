from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import os
import logging

from ..database import get_db
from .. import models, schemas
from ..dependencies import get_prepiq_service

# Import from the new Supabase-first auth service
from ..services.supabase_first_auth import get_current_user_from_token

# Import Gemini for AI Tutor
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Generative AI not installed. AI Tutor will use fallback responses.")

logger = logging.getLogger(__name__)

# ── In-memory subject summary cache ──────────────────────────────────────────
# key: subject_id → summarized knowledge base string
_subject_summary_cache: Dict[str, str] = {}

# Dependency for protected routes
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await get_current_user_from_token(authorization, db)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

# ── AI Tutor System Prompt ────────────────────────────────────────────────────
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


def _build_subject_knowledge_base(subject_id: str, db: Session) -> str:
    """
    Pull all extracted content for a subject from the DB and return as a
    single text block ready for summarization.
    Includes: question texts, unit names, and raw_text from papers.
    """
    # Gather raw text from uploaded papers
    papers = db.query(models.QuestionPaper).filter(
        models.QuestionPaper.subject_id == subject_id
    ).all()

    parts = []
    for paper in papers:
        if paper.raw_text and paper.raw_text.strip():
            parts.append(paper.raw_text[:5000])  # cap per paper

    # Gather extracted questions / concepts
    questions = db.query(models.Question).join(models.QuestionPaper).filter(
        models.QuestionPaper.subject_id == subject_id
    ).limit(100).all()

    if questions:
        q_block = "\n".join(
            f"- [{q.question_type or 'item'}] {q.question_text[:300]}"
            for q in questions
        )
        parts.append(f"Extracted items:\n{q_block}")

    return "\n\n".join(parts) if parts else ""


async def _summarize_with_bart(text: str) -> Optional[str]:
    """
    Primary summarizer: facebook/bart-large-cnn via Bytez.
    Returns summary string or None on failure.
    """
    try:
        from ..ml.external_api_wrapper import get_external_api
        api = get_external_api()
        if not api or not api.bytez_sdk:
            return None

        # BART has a ~1024 token input limit — chunk if needed
        chunk = text[:3000]
        result = api.text_summarization(chunk)
        if result.get("success") and result.get("output"):
            summary = result["output"]
            if isinstance(summary, str) and len(summary.strip()) > 20:
                logger.info(f"BART summarization succeeded ({len(summary)} chars)")
                return summary.strip()
        return None
    except Exception as exc:
        logger.warning(f"BART summarization failed: {exc}")
        return None


async def _summarize_with_gemini(text: str, subject_name: str) -> str:
    """
    Fallback summarizer: Gemini.
    Always returns a string (empty string on total failure).
    """
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or not GEMINI_AVAILABLE:
            return ""
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            f"You are summarizing study material for the subject '{subject_name}'.\n"
            f"Create a concise knowledge base summary (max 500 words) covering the key concepts, "
            f"topics, definitions, and important points from the following content.\n\n"
            f"CONTENT:\n{text[:8000]}"
        )
        response = model.generate_content(prompt)
        summary = response.text.strip() if hasattr(response, "text") else ""
        logger.info(f"Gemini fallback summarization succeeded ({len(summary)} chars)")
        return summary
    except Exception as exc:
        logger.warning(f"Gemini summarization fallback failed: {exc}")
        return ""


async def _get_subject_summary(subject_id: str, subject_name: str, db: Session) -> str:
    """
    Returns a cached or freshly generated summary for the subject.
    Pipeline: raw content → BART (primary) → Gemini (fallback).
    """
    if subject_id in _subject_summary_cache:
        return _subject_summary_cache[subject_id]

    raw_text = _build_subject_knowledge_base(subject_id, db)

    if not raw_text.strip():
        summary = f"No uploaded materials found for {subject_name} yet."
    else:
        # Step 1: try BART
        summary = await _summarize_with_bart(raw_text)

        # Step 2: fallback to Gemini
        if not summary:
            logger.info("BART unavailable/failed — using Gemini summarization fallback")
            summary = await _summarize_with_gemini(raw_text, subject_name)

        # Step 3: last resort — truncated raw text
        if not summary:
            summary = raw_text[:1500]

    _subject_summary_cache[subject_id] = summary
    return summary

@router.post("/message", response_model=schemas.ChatResponse)
async def send_message(
    chat_request: schemas.ChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subject belongs to user
    subject = db.query(models.Subject).filter(
        models.Subject.id == chat_request.subject_id,
        models.Subject.user_id == current_user["id"]
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Process the message using the service
    service = get_prepiq_service()
    result = service.chat_with_bot(
        db=db,
        user_id=current_user["id"],
        subject_id=chat_request.subject_id,
        message=chat_request.message
    )
    
    # Get the bot response
    bot_response = result["response"]
    
    # Find related questions from the subject's papers
    # H-09: eager-load the paper relationship to avoid N+1 lazy loads
    from sqlalchemy.orm import joinedload
    related_questions = (
        db.query(models.Question)
        .options(joinedload(models.Question.paper))
        .join(models.QuestionPaper)
        .filter(models.QuestionPaper.subject_id == chat_request.subject_id)
        .limit(3)
        .all()
    )

    # Prepare response with related questions
    related_questions_list = []
    for q in related_questions:
        appeared_years = []
        if q.paper and q.paper.exam_year:
            appeared_years.append(q.paper.exam_year)

        # H-10: similar_question_ids may contain strings; cast to str for .in_() safety
        if q.similar_question_ids:
            try:
                similar_ids = [str(sid) for sid in q.similar_question_ids]
                similar_questions = (
                    db.query(models.Question)
                    .options(joinedload(models.Question.paper))
                    .join(models.QuestionPaper)
                    .filter(models.Question.id.in_(similar_ids))
                    .all()
                )
                for sq in similar_questions:
                    if sq.paper and sq.paper.exam_year and sq.paper.exam_year not in appeared_years:
                        appeared_years.append(sq.paper.exam_year)
            except Exception:
                pass  # non-fatal — just skip similar question years

        appeared_years.sort()

        related_questions_list.append({
            "text": q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
            "marks": q.marks,
            "appeared_years": appeared_years,
            "probability": "high" if q.is_repeated else "medium",
        })
    
    # Get real references from papers
    references = []
    recent_papers = db.query(models.QuestionPaper).filter(
        models.QuestionPaper.subject_id == chat_request.subject_id
    ).order_by(models.QuestionPaper.exam_year.desc()).limit(2).all()
    
    for paper in recent_papers:
        if paper.exam_year:
            # Get a sample question from this paper
            sample_q = db.query(models.Question).filter(
                models.Question.paper_id == paper.id
            ).first()
            
            if sample_q:
                references.append({
                    "type": "paper",
                    "paper_year": paper.exam_year,
                    "question": sample_q.question_text[:100] + "..." if len(sample_q.question_text) > 100 else sample_q.question_text
                })
    
    return {
        "message_id": result["message_id"],
        "response": bot_response,
        "related_questions": related_questions_list,
        "references": references,
        "suggested_actions": [
            "Add to revision",
            "Practice similar questions",
            "Take targeted mock test"
        ]
    }

@router.get("/history/{subject_id}", response_model=List[schemas.ChatHistoryResponse])
async def get_chat_history(
    subject_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subject belongs to user
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.user_id == current_user["id"]
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Get chat history for the subject
    chat_history = db.query(models.ChatHistory).filter(
        models.ChatHistory.subject_id == subject_id,
        models.ChatHistory.user_id == current_user["id"]
    ).order_by(models.ChatHistory.created_at.desc()).offset(offset).limit(limit).all()
    
    # Format the response
    history_list = []
    for chat in chat_history:
        history_list.append({
            "id": chat.id,
            "timestamp": chat.created_at,
            "user_message": chat.user_message,
            "bot_response": chat.bot_response
        })
    
    return history_list

@router.delete("/history/{subject_id}")
async def clear_chat_history(
    subject_id: str,  # BUG-M10: path param, not query param
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify subject belongs to user
    subject = db.query(models.Subject).filter(
        models.Subject.id == subject_id,
        models.Subject.user_id == current_user["id"]
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Delete chat history for the subject
    db.query(models.ChatHistory).filter(
        models.ChatHistory.subject_id == subject_id,
        models.ChatHistory.user_id == current_user["id"]
    ).delete()
    
    db.commit()
    
    return {"message": "Chat history cleared successfully"}


@router.post("/tutor")
async def ai_tutor_chat(
    request: schemas.TutorChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI Tutor endpoint.
    Pipeline:
      1. If subject_id provided → build knowledge base from DB content
      2. Summarize with BART (primary) → fallback to Gemini
      3. Inject summary + TUTOR_SYSTEM_PROMPT into Gemini tutor model
      4. Return Socratic teaching response
    """
    try:
        message = request.message
        conversation_history = request.conversation_history or []
        subject_id = request.subject_id

        if not message:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Message is required"
            )

        if not GEMINI_AVAILABLE:
            return {
                "response": "AI tutor is currently unavailable. Please ensure the Gemini API is configured.",
                "context": None
            }

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {
                "response": "I'm having trouble accessing my teaching capabilities. Please try again later.",
                "context": None
            }

        # ── Step 1: Get subject context (summary) ─────────────────────────────
        subject_context_block = ""
        subject_name = "this subject"

        if subject_id:
            subject = db.query(models.Subject).filter(
                models.Subject.id == subject_id,
                models.Subject.user_id == current_user["id"]
            ).first()

            if subject:
                subject_name = subject.name
                summary = await _get_subject_summary(subject_id, subject_name, db)
                if summary:
                    subject_context_block = (
                        f"\n\n--- SUBJECT KNOWLEDGE BASE: {subject_name} ---\n"
                        f"{summary}\n"
                        f"--- END KNOWLEDGE BASE ---\n"
                    )

        # ── Step 2: Build conversation history block ───────────────────────────
        history_block = ""
        if conversation_history:
            history_block = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-5:]:
                role = "Student" if msg.get("role") == "user" else "Tutor"
                history_block += f"{role}: {msg.get('content', '')}\n"

        # ── Step 3: Build full prompt ──────────────────────────────────────────
        full_prompt = (
            f"{TUTOR_SYSTEM_PROMPT}"
            f"{subject_context_block}"
            f"{history_block}"
            f"\nStudent's current question: {message}"
            f"\n\nRespond as the AI Tutor:"
        )

        # ── Step 4: Generate response ──────────────────────────────────────────
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(full_prompt)
        tutor_response = response.text if hasattr(response, "text") else str(response)

        # ── Step 5: Persist to chat history ───────────────────────────────────
        if subject_id:
            existing = db.query(models.ChatHistory).filter(
                models.ChatHistory.user_id == current_user["id"],
                models.ChatHistory.user_message == message,
                models.ChatHistory.bot_response == tutor_response
            ).count()
            if existing == 0:
                db.add(models.ChatHistory(
                    user_id=current_user["id"],
                    subject_id=subject_id,
                    user_message=message,
                    bot_response=tutor_response,
                ))
                db.commit()

        return {
            "response": tutor_response,
            "context": {
                "conversation_length": len(conversation_history) + 1,
                "tutor_mode": "socratic",
                "subject": subject_name,
                "knowledge_base_active": bool(subject_context_block),
                "model": "gemini-2.5-flash",
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI Tutor error: {str(e)}")
        return {
            "response": "I'm having trouble formulating a response right now. What specific aspect of this topic would you like to explore first?",
            "context": None
        }


@router.post("/tutor/invalidate-cache")
async def invalidate_subject_cache(
    subject_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Invalidate the summary cache for a subject (call after uploading new materials)."""
    _subject_summary_cache.pop(subject_id, None)
    return {"message": f"Cache cleared for subject {subject_id}"}