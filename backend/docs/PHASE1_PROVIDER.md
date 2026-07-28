# Phase 1 — Env-driven LLM provider layer

## How to set env vars

Copy `backend/.env.example` → `backend/.env` and set at least one API key path:

```env
# Shared defaults (used when capability-specific vars are empty)
LLM_DEFAULT_PROVIDER=gemini
LLM_DEFAULT_MODEL=gemini-1.5-flash
LLM_DEFAULT_API_KEY=
LLM_DEFAULT_BASE_URL=

# Per capability (optional overrides)
PREDICTION_PROVIDER=
PREDICTION_MODEL=
PREDICTION_API_KEY=
PREDICTION_BASE_URL=

EXTRACTION_PROVIDER=
EXTRACTION_MODEL=
EXTRACTION_API_KEY=
EXTRACTION_BASE_URL=

CHAT_PROVIDER=
CHAT_MODEL=
CHAT_API_KEY=
CHAT_BASE_URL=

# Legacy: still accepted as API key fallback when capability / default keys are empty
GEMINI_API_KEY=
```

Provider implementation lives in `backend/app/core/llm_provider.py`.
Settings mirrors are listed on `backend/app/core/config.py` (`Settings`).

## Resolution order

For capability `prediction` | `extraction` | `chat`:

1. `{CAP}_PROVIDER` / `{CAP}_MODEL` / `{CAP}_API_KEY` / `{CAP}_BASE_URL` if set  
2. Else `LLM_DEFAULT_*`  
3. Else `GEMINI_API_KEY` as the **API key only** (provider/model still default to gemini / `LLM_DEFAULT_MODEL` or built-in default `gemini-1.5-flash`)  
4. Else client `is_available == False` → callers keep existing graceful fallbacks (regex extract, empty prediction tiers, “tutor unavailable”, etc.)

Supported provider string today: `gemini` (aliases: `google`, `google-generativeai`).

## Files created / changed

| Path | Change |
|------|--------|
| `backend/app/core/llm_provider.py` | **Created** — registry, `LLMClient`, `get_llm_client`, Gemini backend |
| `backend/app/core/config.py` | Documented capability-scoped + default LLM settings |
| `backend/.env.example` | Documented new env vars |
| `backend/app/prediction_engine.py` | Prediction LLM via `get_llm_client("prediction")` |
| `backend/app/chatbot.py` | Chat LLM via `get_llm_client("chat")` |
| `backend/app/routers/upload.py` | Extraction via `get_llm_client("extraction")`; dead model_coordinator path quarantined |
| `backend/app/routers/chat.py` | Tutor + summary fallback via `get_llm_client("chat")` |
| `backend/docs/PHASE1_PROVIDER.md` | **Created** (this file) |

## Call sites rewired

| Capability | Call site |
|------------|-----------|
| prediction | `PredictionEngine.__init__`, `_generate_gemini_response`, revision guide, study-plan prompt |
| prediction | Cold-start in `PrepIQService._cold_start_prediction` uses `prediction_engine.model.generate_content` — `LLMClient` exposes a compatible `generate_content` so behavior is unchanged without rewriting the large services module |
| extraction | `routers/upload.py` `_extract_questions_with_gemini`, `_extract_concepts_with_gemini` |
| chat | `chatbot.Chatbot.get_response` / `explain_concept` |
| chat | `routers/chat.py` `_summarize_with_chat_llm`, `ai_tutor_chat` |

## Removed / quarantined

- **Hard-coded** `GenerativeModel("gemini-1.5-flash")` / `gemini-2.5-flash` removed from routers/engines/chatbot (model names only in provider + env defaults).
- **model_coordinator** import attempts in `upload.py` replaced with a no-op quarantine note (module was never present in tree).
- **Bytez** remains optional/non-default (chat still tries BART via missing `external_api_wrapper` then falls back to chat LLM). Not expanded.

## How to verify

1. **With keys**  
   Set `GEMINI_API_KEY` (or `PREDICTION_API_KEY` / `EXTRACTION_API_KEY` / `CHAT_API_KEY`).  
   - Prediction: generate with ≥0 / 1–2 / ≥3 papers — same response shapes as before.  
   - Upload: question_paper material type returns extracted questions when LLM works.  
   - Chat `/chat/tutor`: returns tutor text; `context.model` reflects resolved `CHAT_MODEL` / default.

2. **Without keys**  
   Unset all LLM keys. App still imports/starts.  
   - Prediction tier 0 still returns instructional empty payload.  
   - Extraction falls back to regex parser.  
   - Tutor returns the existing “trouble accessing teaching capabilities” style message.

3. **Model override without code edits**  
   Set `PREDICTION_MODEL=...` (and key) and restart — prediction calls use the new model via the provider only.

## Out of scope (unchanged)

Pyronites, auth, storage, prediction tier logic, mock-test scoring, frontend.
