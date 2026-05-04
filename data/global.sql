-- =============================================================================
-- PrepIQ — Consolidated Schema
-- global.sql
--
-- Single source of truth. Run this on a fresh Supabase project.
-- Idempotent: every statement uses IF NOT EXISTS / OR REPLACE so it is safe
-- to re-run without dropping data.
--
-- Execution order matters — run this file before rls.sql.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Extensions
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";    -- gen_random_uuid() (Supabase default)
CREATE EXTENSION IF NOT EXISTS "vector";      -- pgvector for embedding similarity search

-- ---------------------------------------------------------------------------
-- 1. users
--    Mirrors auth.users via Supabase OAuth.
--    The trigger at the bottom auto-creates a row here on first sign-in.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.users (
    -- Primary key matches auth.users.id so JOINs are free
    id                   UUID         PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Identity
    email                VARCHAR(255) UNIQUE NOT NULL,
    full_name            VARCHAR(255) NOT NULL DEFAULT '',
    college_name         VARCHAR(255) NOT NULL DEFAULT '',

    -- Academic profile
    program              VARCHAR(100) NOT NULL DEFAULT 'BTech',  -- BTech | BSc | MSc | BCA | MCA
    year_of_study        INTEGER      NOT NULL DEFAULT 1,

    -- Preferences
    theme_preference     VARCHAR(20)  NOT NULL DEFAULT 'system', -- light | dark | system
    language             VARCHAR(10)  NOT NULL DEFAULT 'en',

    -- Wizard / onboarding
    wizard_completed     BOOLEAN      NOT NULL DEFAULT FALSE,
    exam_name            VARCHAR(255),
    exam_date            TIMESTAMPTZ,
    days_until_exam      INTEGER,
    focus_subjects       JSONB,                                  -- ["Linear Algebra", ...]
    study_hours_per_day  INTEGER,
    target_score         INTEGER,                                -- 0-100 percentage
    preparation_level    VARCHAR(50),                            -- beginner | intermediate | advanced

    -- Account state
    email_verified       BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_at           TIMESTAMPTZ,                            -- soft-delete

    -- Timestamps
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email             ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_wizard_completed  ON public.users(wizard_completed);
CREATE INDEX IF NOT EXISTS idx_users_deleted_at        ON public.users(deleted_at) WHERE deleted_at IS NULL;

-- ---------------------------------------------------------------------------
-- 2. subjects
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.subjects (
    id                   UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id              UUID         NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    name                 VARCHAR(255) NOT NULL,
    code                 VARCHAR(100),
    semester             INTEGER,
    academic_year        VARCHAR(20),                            -- "2025-2026"

    -- Exam details
    total_marks          INTEGER,
    exam_date            DATE,
    exam_duration_minutes INTEGER,

    -- Syllabus
    syllabus_json        JSONB,                                  -- { "units": [...] }

    -- Cached counters (updated by application layer)
    papers_uploaded      INTEGER      NOT NULL DEFAULT 0,
    predictions_generated INTEGER     NOT NULL DEFAULT 0,
    mock_tests_created   INTEGER      NOT NULL DEFAULT 0,

    created_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subjects_user_id        ON public.subjects(user_id);
CREATE INDEX IF NOT EXISTS idx_subjects_user_semester  ON public.subjects(user_id, semester);
CREATE INDEX IF NOT EXISTS idx_subjects_name           ON public.subjects(name);

-- ---------------------------------------------------------------------------
-- 3. question_papers
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.question_papers (
    id                   UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id           UUID         NOT NULL REFERENCES public.subjects(id) ON DELETE CASCADE,

    -- File
    file_name            VARCHAR(500) NOT NULL,
    file_path            VARCHAR(1000),                          -- public URL from Supabase Storage
    s3_key               VARCHAR(1000),                         -- storage object key
    file_size_bytes      BIGINT,

    -- Paper metadata
    exam_year            INTEGER,
    exam_semester        VARCHAR(20),
    total_marks          INTEGER,
    duration_minutes     INTEGER,

    -- Extracted content
    raw_text             TEXT,
    metadata_json        TEXT,                                   -- PDF metadata as JSON string
    extraction_confidence DECIMAL(3,2),                         -- 0.00–1.00
    extraction_method    VARCHAR(50),                            -- pdfplumber | tesseract

    -- Processing state
    processing_status    VARCHAR(20)  NOT NULL DEFAULT 'pending', -- pending | processing | completed | failed
    error_message        TEXT,
    processed_at         TIMESTAMPTZ,

    created_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_qp_subject_id           ON public.question_papers(subject_id);
CREATE INDEX IF NOT EXISTS idx_qp_exam_year            ON public.question_papers(exam_year);
CREATE INDEX IF NOT EXISTS idx_qp_processing_status    ON public.question_papers(processing_status);
CREATE INDEX IF NOT EXISTS idx_qp_created_at           ON public.question_papers(created_at);

-- ---------------------------------------------------------------------------
-- 4. questions
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.questions (
    id                   UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id             UUID         NOT NULL REFERENCES public.question_papers(id) ON DELETE CASCADE,

    -- Content
    question_text        TEXT         NOT NULL,
    question_number      INTEGER,                                -- numeric for correct sort order
    marks                DECIMAL(5,2) NOT NULL DEFAULT 0,

    -- Classification
    unit_id              VARCHAR(50),
    unit_name            VARCHAR(255),
    topics_json          JSONB,                                  -- ["Binary Search", ...]
    question_type        VARCHAR(50),                            -- mcq | short_answer | numerical | essay
    difficulty           VARCHAR(20),                            -- easy | medium | hard

    -- Structure
    section_name         VARCHAR(100),
    has_subparts         BOOLEAN      NOT NULL DEFAULT FALSE,
    subparts_count       INTEGER,

    -- Analysis
    is_repeated          BOOLEAN      NOT NULL DEFAULT FALSE,
    similar_question_ids UUID[],
    text_length          INTEGER,

    -- Embedding for semantic similarity search (pgvector)
    embedding            vector(768),

    created_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_questions_paper_id      ON public.questions(paper_id);
CREATE INDEX IF NOT EXISTS idx_questions_unit_id       ON public.questions(unit_id);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty    ON public.questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_question_type ON public.questions(question_type);
CREATE INDEX IF NOT EXISTS idx_questions_topics_gin    ON public.questions USING gin(topics_json);
-- Vector index — only useful once you have > ~1000 rows; safe to add now
CREATE INDEX IF NOT EXISTS idx_questions_embedding     ON public.questions
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ---------------------------------------------------------------------------
-- 5. predictions
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.predictions (
    id                        UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id                UUID         NOT NULL REFERENCES public.subjects(id) ON DELETE CASCADE,
    user_id                   UUID         NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    -- Prediction payload
    predicted_questions_json  TEXT,                              -- large JSON stored as text
    total_questions           INTEGER,
    total_predicted_marks     INTEGER,

    -- Probability buckets
    very_high_count           INTEGER      DEFAULT 0,
    high_count                INTEGER      DEFAULT 0,
    moderate_count            INTEGER      DEFAULT 0,

    -- Coverage
    unit_coverage_json        JSONB,                             -- { "Unit 1": 45, ... }
    topic_coverage_percentage DECIMAL(5,2),

    -- Analysis
    analysis_summary          TEXT,
    key_insights_json         JSONB,
    ml_analysis_json          TEXT,                              -- ML analysis as JSON string

    -- Post-exam accuracy tracking
    actual_exam_questions_json TEXT,
    accuracy_score            DECIMAL(5,2),                     -- % of predictions that appeared
    prediction_accuracy_score DECIMAL(5,2),                     -- estimated accuracy at generation time

    created_at                TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_subject_id      ON public.predictions(subject_id);
CREATE INDEX IF NOT EXISTS idx_predictions_user_id         ON public.predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_user_subject    ON public.predictions(user_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at      ON public.predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_predictions_insights_gin    ON public.predictions USING gin(key_insights_json);

-- ---------------------------------------------------------------------------
-- 6. mock_tests
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.mock_tests (
    id                   UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id              UUID         NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    subject_id           UUID         NOT NULL REFERENCES public.subjects(id) ON DELETE CASCADE,

    -- Configuration
    total_questions      INTEGER      NOT NULL,
    total_marks          INTEGER      NOT NULL,
    duration_minutes     INTEGER,
    difficulty_level     VARCHAR(20)  DEFAULT 'moderate',        -- easy | moderate | hard

    -- Questions snapshot (stored so results survive paper deletion)
    questions_json       JSONB        NOT NULL,

    -- Execution
    start_time           TIMESTAMPTZ,
    end_time             TIMESTAMPTZ,
    is_completed         BOOLEAN      NOT NULL DEFAULT FALSE,

    -- Results
    user_answers_json    JSONB,
    score                DECIMAL(5,2),
    percentage           DECIMAL(5,2),
    correct_count        INTEGER      DEFAULT 0,
    incorrect_count      INTEGER      DEFAULT 0,
    skipped_count        INTEGER      DEFAULT 0,

    -- Topic analysis
    weak_topics_json     JSONB,
    strong_topics_json   JSONB,

    created_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mock_tests_user_id          ON public.mock_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_mock_tests_subject_id       ON public.mock_tests(subject_id);
CREATE INDEX IF NOT EXISTS idx_mock_tests_is_completed     ON public.mock_tests(is_completed);
CREATE INDEX IF NOT EXISTS idx_mock_tests_created_at       ON public.mock_tests(created_at);
CREATE INDEX IF NOT EXISTS idx_mock_tests_weak_gin         ON public.mock_tests USING gin(weak_topics_json);
CREATE INDEX IF NOT EXISTS idx_mock_tests_strong_gin       ON public.mock_tests USING gin(strong_topics_json);

-- ---------------------------------------------------------------------------
-- 7. chat_history
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.chat_history (
    id                      UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID         NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    subject_id              UUID         REFERENCES public.subjects(id) ON DELETE SET NULL,

    -- Message
    user_message            TEXT         NOT NULL,
    bot_response            TEXT         NOT NULL,
    message_type            VARCHAR(50)  DEFAULT 'general',      -- general | concept_explanation | ...
    relevant_question_ids   UUID[],

    -- Metadata
    response_time_seconds   DECIMAL(6,3),
    user_feedback           VARCHAR(20),                         -- positive | negative | neutral

    created_at              TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
    -- No updated_at — chat messages are immutable
);

CREATE INDEX IF NOT EXISTS idx_chat_user_id                ON public.chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_subject_id             ON public.chat_history(subject_id);
CREATE INDEX IF NOT EXISTS idx_chat_created_at             ON public.chat_history(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_message_type           ON public.chat_history(message_type);

-- ---------------------------------------------------------------------------
-- 8. study_plans
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS public.study_plans (
    id                   UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id              UUID         NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    subject_id           UUID         NOT NULL REFERENCES public.subjects(id) ON DELETE CASCADE,

    plan_name            VARCHAR(255),
    start_date           DATE         NOT NULL,
    exam_date            DATE         NOT NULL,
    total_days           INTEGER      NOT NULL,

    -- Schedule
    daily_schedule_json  JSONB        NOT NULL,                  -- [{ day, date, topics, hours }]

    -- Progress
    days_completed       INTEGER      NOT NULL DEFAULT 0,
    completion_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    on_track             BOOLEAN      NOT NULL DEFAULT TRUE,
    last_update_date     DATE         DEFAULT CURRENT_DATE,

    created_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_study_plans_user_id         ON public.study_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_study_plans_subject_id      ON public.study_plans(subject_id);
CREATE INDEX IF NOT EXISTS idx_study_plans_start_date      ON public.study_plans(start_date);
CREATE INDEX IF NOT EXISTS idx_study_plans_exam_date       ON public.study_plans(exam_date);
CREATE INDEX IF NOT EXISTS idx_study_plans_schedule_gin    ON public.study_plans USING gin(daily_schedule_json);

-- ---------------------------------------------------------------------------
-- 9. updated_at trigger
--    Single function shared by all tables that have an updated_at column.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

DO $$
DECLARE
    t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY[
        'users', 'subjects', 'question_papers', 'questions',
        'predictions', 'mock_tests', 'study_plans'
    ]
    LOOP
        -- Drop first so re-runs don't error on "trigger already exists"
        EXECUTE format('DROP TRIGGER IF EXISTS trg_%s_updated_at ON public.%I', t, t);
        EXECUTE format(
            'CREATE TRIGGER trg_%s_updated_at
             BEFORE UPDATE ON public.%I
             FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()',
            t, t
        );
    END LOOP;
END;
$$;

-- ---------------------------------------------------------------------------
-- 10. Auto-create user row on OAuth sign-in
--     Supabase fires this trigger after every INSERT into auth.users.
--     Reads full_name and avatar_url from OAuth metadata.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', '')
    )
    ON CONFLICT (id) DO NOTHING;   -- idempotent: re-runs on token refresh events
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_auth_user();

-- ---------------------------------------------------------------------------
-- 11. Backend service-role grants
--     The FastAPI backend connects with the service role key and bypasses RLS,
--     so it only needs basic schema access.
-- ---------------------------------------------------------------------------

GRANT USAGE ON SCHEMA public TO postgres, service_role;
GRANT ALL   ON ALL TABLES    IN SCHEMA public TO postgres, service_role;
GRANT ALL   ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
