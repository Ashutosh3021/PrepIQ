# Phase 0 Inventory & Target Contracts

## 1. LLM / ML / “agent” call sites

| File | Function/class | Capability | Hard-coded provider/model | Env vars used today | Always-on / lazy / optional | Notes (fallback, dead code, broken) |
|---|---|---|---|---|---|---|
| `backend/app/services/model_coordinator.py` | `generate_text` | Generate text | Google Gemini | `GEMINI_API_KEY` | Optional | Part of multi-agent noise. |
| `backend/app/routers/chat.py` | Chat route | Tutor/Chatbot | Google Gemini | `GEMINI_API_KEY` | Optional | Uses `google.generativeai`. |
| `backend/app/routers/upload.py` | `_extract_questions_with_gemini` | Extraction | Google Gemini (`gemini-1.5-flash`) | `GEMINI_API_KEY` | Optional (Fallback) | Falls back to regex parser if API key missing. |
| `backend/app/routers/upload.py` | `_extract_concepts_with_gemini` | Extraction | Google Gemini (`gemini-1.5-flash`) | `GEMINI_API_KEY` | Optional (Fallback) | Falls back to regex parser if API key missing. |
| `backend/app/prediction_engine.py` | `predict_exam_topics` | Prediction | Google Gemini | `GEMINI_API_KEY` | Lazy/Fallback | Heavy Gemini reliance. |
| `backend/app/chatbot.py` | `Chatbot` | Tutor/Chatbot | Google Gemini (`gemini-1.5-flash`) | `GEMINI_API_KEY` | Optional | Agent chatbot code. |
| `backend/app/services.py` | `generate_predictions` | Prediction | Google Gemini | `GEMINI_API_KEY` | Optional | Gemini as fallback. |
| `backend/app/ml_engines/concept_explainer.py` | `_generate_gemini_response` | Tutor | Google Gemini (`gemini-1.5-flash`) | `GEMINI_API_KEY` | Optional | Tutoring feature. |
| `backend/app/ml/external_api_wrapper.py` | `_call_bytez_model` | Translation/Chat/Image | Bytez | `BYTEZ_API_KEY` | Optional | Dead multi-agent / Bytez noise. |
| `backend/app/ml/syllabus_analyzer.py` | `_lazy_import_sentence_transformers` | Similarity | `sentence-transformers` | None | Lazy | Uses sklearn cosine_similarity as well. |
| `backend/app/ml/engines/question_importance.py` | `_lazy_import_transformers` | Importance / similarity | `transformers` / `sentence-transformers` / sklearn | None | Lazy | Has lightweight TF-IDF fallback. |
| `backend/app/ml/engines/progress_forecaster.py` | `ProgressForecaster` | Forecasting | LSTM (TensorFlow/Keras) / RandomForest | None | Always-on | Heavy local ML. |
| `backend/app/ml/engines/topic_recommender.py` | `TopicRecommender` | Recommendation | sklearn TF-IDF/SVD/KNN | None | Always-on | Unused or heavy local engines. |
| `backend/app/ml/engines/focus_area_identifier.py` | `FocusAreaIdentifier` | Classification | sklearn RandomForest/SVC | None | Always-on | |

## 2. Supabase & data-layer touchpoints

| File | What it does | Tables or storage involved | Auth assumption |
|---|---|---|---|
| `backend/app/services/supabase_first_auth.py` | Auth (signup, login, verify token) | `users` (DB) + Supabase Auth | Supabase handles JWTs, local DB syncs lazily. |
| `backend/app/main.py` | Supabase Client Init | None (Config) | Relies on `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`. |
| `backend/app/routers/auth.py` | Refresh sessions | Supabase Auth | Directly uses Supabase client. |
| `backend/app/database.py` | SQLAlchemy Engine | All Tables | Uses `DATABASE_URL` for Postgres. |
| `backend/app/services/supabase_storage.py` | File upload/download | Supabase Storage (`question-papers` bucket) | Uses Service Key for bypass. |

**Logical Tables / Entities actually needed:**
- `users`
- `subjects`
- `question_papers`
- `questions`
- `predictions`
- `mock_tests`

## 3. Core feature reality check

### 3a. Prediction
- **Entry points:** `backend/app/routers/predictions.py` (`generate_prediction`, `get_predictions_for_subject`), `backend/app/services.py` (`generate_predictions`).
- **Data required:** `subject_id`, user ID. Relies on extracted questions from past papers.
- **Actual path when 0 / 1–2 / ≥3 papers:**
  - 0 papers: Service returns short circuit "none" ID, router sends status "no_data" and instruction message.
  - 1-2 papers: Triggers Gemini cold-start prediction based on subject knowledge (warning banner).
  - 3+ papers: Full ML pipeline + Gemini fallback.
- **What is real vs fallback vs placeholder text:** 0 papers response is real fallback message. Gemini cold start relies heavily on LLM hallucinating relevant questions.
- **Response shape returned to the client today:** `SubjectPredictionResponse` containing a list of `PredictedQuestionFull` (question text, topic, marks, probability, confidence, reasoning, source).

### 3b. Mock test generate + submit
- **Entry points:** `backend/app/routers/tests.py` (`generate_mock_test`, `submit_test`).
- **Where questions come from:** Fetches from previously generated predictions or the general question bank (`models.Question`).
- **Scoring behavior when `correct_answer` is missing:** `score_pct` only computes when `gradeable > 0` (meaning at least one question had a `correct_answer`). Otherwise returns explicit null for score (no fake percentages).
- **Response shapes:** `MockTestResponse` for generation, detailed JSON dictionary with `test_id`, `score_percentage`, `total_questions`, `answers_graded` for submission.

### 3c. Upload / paper processing
- **All upload routes:** `backend/app/routers/upload.py` (`upload_and_analyze`), `backend/app/routers/papers.py` (`upload_papers`).
- **How text/questions are extracted:** Texts are extracted via `pdf_parser.py` (PyMuPDF/PyPDF2/etc.), and questions are parsed either by `_extract_questions_with_gemini` or fallback regex inside `pdf_parser.py`.
- **Where files are stored today:** Supabase Storage (`question-papers` bucket) via `SupabaseStorageService`.
- **What ends up in DB:** `QuestionPaper` rows and the extracted `Question` objects.

## 4. Target contracts (write these as the new source of truth)

### 4.1 Provider config (env-driven)
```env
# Prediction
PREDICTION_PROVIDER=...
PREDICTION_MODEL=...
PREDICTION_API_KEY=...
PREDICTION_BASE_URL=   # optional

# Extraction (paper → questions)
EXTRACTION_PROVIDER=...
EXTRACTION_MODEL=...
EXTRACTION_API_KEY=...
EXTRACTION_BASE_URL=

# (Defer tutor/chat to later phases; note only)
```
State: no hard-coded model names in code after Phase 1; provider layer is the only place that talks to external LLMs.

### 4.2 Auth (confirmed product decision)
- Remove Google + GitHub OAuth completely
- Email + password only (Pyronites auth)
- Email validation + strong password rules on signup
- Note current auth files that must be replaced later (`backend/app/services/supabase_first_auth.py`, `backend/app/routers/auth.py`)

### 4.3 Storage (confirmed product decision)
- Pyronites has no storage basket
- Paper files = local filesystem only; DB stores metadata + local path
- Note current storage code to replace (`backend/app/services/supabase_storage.py`)

### 4.4 Database
- Target: Pyronites client (`PYRONITES_URL`, `PYRONITES_KEY`) as the data + auth layer
- List logical tables the app must keep for prediction + tests: `users`, `subjects`, `question_papers`, `questions`, `predictions`, `mock_tests`.
- Note: SQLAlchemy/Supabase coupling to remove in Phase 2.

### 4.5 Prediction API contract (stable response intent)
Define fields the client should always get, including:
- empty / insufficient data
- cold-start
- full prediction
- source, fallback_used, confidence, reasoning
- No fake high accuracy when data is missing.

### 4.6 Mock test API contract
- generate: sources (predictions vs question bank), empty-bank behavior
- submit: score only when answers exist; otherwise explicit null / no fake %

## 5. Recommended kill / keep / adapt list

- **Kill**
  - Dead multi-agent/Bytez noise (`external_api_wrapper.py`, `model_coordinator.py`)
  - Unused ML engines (LSTM forecaster, recommender, etc. in `app/ml/engines/`)
  - OAuth providers
- **Keep**
  - Thin shells worth keeping (`pdf_parser.py`, basic route structure)
- **Adapt**
  - Must wrap behind provider layer or Pyronites (prediction logic, DB access, Storage service to local files)

## Phase 1 ready checklist
- Create Provider configuration abstraction (env-driven).
- Refactor prediction API + Mock Test API to match target contracts.
- Strip out unused ML (LSTM/Recommenders/Bytez SDK) and external gateways.
