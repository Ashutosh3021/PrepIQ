-- =============================================================================
-- PrepIQ - SQLite Database Schema
-- Generated from: app/models.py + app/models/enhanced_models.py
-- =============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- =============================================================================
-- TABLE: users
-- Core user accounts (auth managed by Supabase; profile stored here)
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id                    TEXT        PRIMARY KEY,           -- UUID stored as text
    email                 TEXT        NOT NULL UNIQUE,
    full_name             TEXT,
    college_name          TEXT,
    program               TEXT        NOT NULL DEFAULT 'BTech',  -- BTech | BSc | MSc
    year_of_study         INTEGER     NOT NULL DEFAULT 1,
    theme_preference      TEXT        NOT NULL DEFAULT 'system', -- light | dark | system
    language              TEXT        NOT NULL DEFAULT 'en',
    exam_date             TEXT,                                   -- ISO-8601 datetime
    wizard_completed      INTEGER     NOT NULL DEFAULT 0,         -- 0=false, 1=true
    -- Wizard fields
    exam_name             TEXT,
    days_until_exam       INTEGER,
    focus_subjects        TEXT,                                   -- JSON array
    study_hours_per_day   INTEGER,
    target_score          INTEGER,
    preparation_level     TEXT,                                   -- beginner | intermediate | advanced
    -- Account status
    email_verified        INTEGER     NOT NULL DEFAULT 0,
    -- Enhanced model fields
    hashed_password       TEXT,
    is_active             INTEGER     NOT NULL DEFAULT 1,
    is_verified           INTEGER     NOT NULL DEFAULT 0,
    last_login            TEXT,
    roles                 TEXT        DEFAULT '["user"]',         -- JSON array
    permissions           TEXT        DEFAULT '[]',              -- JSON array
    -- Timestamps
    created_at            TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at            TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    deleted_at            TEXT                                   -- soft-delete
);

CREATE INDEX IF NOT EXISTS idx_users_email             ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_wizard_completed  ON users (wizard_completed);


-- =============================================================================
-- TABLE: subjects
-- Subjects belong to a user (user-scoped syllabus / exam subjects)
-- =============================================================================
CREATE TABLE IF NOT EXISTS subjects (
    id                      TEXT    PRIMARY KEY,
    user_id                 TEXT    NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name                    TEXT    NOT NULL,
    code                    TEXT,
    semester                INTEGER,
    academic_year           TEXT,
    total_marks             INTEGER,
    exam_date               TEXT,
    exam_duration_minutes   INTEGER,
    syllabus_json           TEXT,   -- JSON: { "units": [{ "name": "...", "topics": [...] }] }
    -- Cached counters
    papers_uploaded         INTEGER NOT NULL DEFAULT 0,
    predictions_generated   INTEGER NOT NULL DEFAULT 0,
    mock_tests_created      INTEGER NOT NULL DEFAULT 0,
    -- Enhanced model extra fields
    description             TEXT,
    credits                 INTEGER,
    department              TEXT,
    is_active               INTEGER NOT NULL DEFAULT 1,
    -- Timestamps
    created_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_subjects_user_id        ON subjects (user_id);
CREATE INDEX IF NOT EXISTS idx_subjects_user_semester  ON subjects (user_id, semester);


-- =============================================================================
-- TABLE: topics
-- Fine-grained topics inside a subject (enhanced model)
-- =============================================================================
CREATE TABLE IF NOT EXISTS topics (
    id                  TEXT    PRIMARY KEY,
    subject_id          TEXT    NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    name                TEXT    NOT NULL,
    description         TEXT,
    difficulty_level    INTEGER,    -- 1-5 scale
    estimated_hours     REAL,
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_topics_subject_id ON topics (subject_id);


-- =============================================================================
-- TABLE: question_papers
-- Uploaded past-paper PDF files linked to a subject
-- =============================================================================
CREATE TABLE IF NOT EXISTS question_papers (
    id                      TEXT    PRIMARY KEY,
    subject_id              TEXT    NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    -- File info
    file_name               TEXT    NOT NULL,
    file_path               TEXT,
    s3_key                  TEXT,
    file_size_bytes         INTEGER,
    -- Exam metadata
    exam_year               INTEGER,
    exam_semester           INTEGER,
    total_marks             INTEGER,
    duration_minutes        INTEGER,
    -- Extraction output
    raw_text                TEXT,
    metadata_json           TEXT,   -- PDF metadata as JSON string
    extraction_confidence   REAL,   -- 0.00 – 1.00
    extraction_method       TEXT,   -- pdfplumber | tesseract
    -- Processing state
    processing_status       TEXT    NOT NULL DEFAULT 'pending', -- pending | processing | completed | failed
    error_message           TEXT,
    processed_at            TEXT,
    -- Timestamps
    created_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_question_papers_subject_id ON question_papers (subject_id);
CREATE INDEX IF NOT EXISTS idx_question_papers_status     ON question_papers (processing_status);


-- =============================================================================
-- TABLE: questions
-- Individual questions extracted from question papers
-- =============================================================================
CREATE TABLE IF NOT EXISTS questions (
    id                      TEXT    PRIMARY KEY,
    paper_id                TEXT    NOT NULL REFERENCES question_papers (id) ON DELETE CASCADE,
    -- Optional FK to support enhanced-model subject-level queries
    subject_id              TEXT    REFERENCES subjects (id) ON DELETE CASCADE,
    -- Optional FK to topic (enhanced model)
    topic_id                TEXT    REFERENCES topics (id) ON DELETE SET NULL,
    -- Content
    question_text           TEXT    NOT NULL,
    question_number         INTEGER,
    marks                   INTEGER NOT NULL DEFAULT 0,
    -- Classification
    unit_id                 TEXT,
    unit_name               TEXT,
    unit                    TEXT,
    chapter                 TEXT,
    topics_json             TEXT,   -- JSON array: ["Binary Search", ...]
    question_type           TEXT,   -- mcq | short_answer | numerical | essay
    difficulty              TEXT,   -- easy | medium | hard  (also stored as 1-5 integer in enhanced model)
    correct_answer          TEXT,
    explanation             TEXT,
    options                 TEXT,   -- JSON array for MCQ options
    tags                    TEXT    DEFAULT '[]',   -- JSON array
    -- Metadata
    section_name            TEXT,
    has_subparts            INTEGER NOT NULL DEFAULT 0,
    subparts_count          INTEGER,
    text_length             INTEGER,
    -- Analysis
    is_repeated             INTEGER NOT NULL DEFAULT 0,
    similar_question_ids    TEXT,   -- JSON array of related question UUIDs
    is_active               INTEGER NOT NULL DEFAULT 1,
    -- Timestamps
    created_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at              TEXT    DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_questions_paper_id   ON questions (paper_id);
CREATE INDEX IF NOT EXISTS idx_questions_subject_id ON questions (subject_id);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions (difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_unit       ON questions (unit_id);


-- =============================================================================
-- TABLE: predictions
-- AI-generated question predictions for a subject
-- =============================================================================
CREATE TABLE IF NOT EXISTS predictions (
    id                          TEXT    PRIMARY KEY,
    subject_id                  TEXT    NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    user_id                     TEXT    NOT NULL REFERENCES users (id)    ON DELETE CASCADE,
    -- Prediction payload
    predicted_questions_json    TEXT,   -- large JSON with all predictions
    total_questions             INTEGER,
    total_predicted_marks       INTEGER,
    -- Probability distribution
    very_high_count             INTEGER,
    high_count                  INTEGER,
    moderate_count              INTEGER,
    -- Coverage
    unit_coverage_json          TEXT,   -- JSON: { "Unit 1": 45, "Unit 2": 30 }
    topic_coverage_percentage   TEXT,
    -- Analysis
    analysis_summary            TEXT,
    key_insights_json           TEXT,   -- JSON array
    ml_analysis_json            TEXT,   -- ML analysis results as JSON string
    -- Post-exam accuracy tracking
    actual_exam_questions_json  TEXT,
    accuracy_score              REAL,   -- % of predictions that appeared
    prediction_accuracy_score   REAL,
    -- Timestamps
    created_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_predictions_subject_id    ON predictions (subject_id);
CREATE INDEX IF NOT EXISTS idx_predictions_user_id       ON predictions (user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_user_subject  ON predictions (user_id, subject_id);


-- =============================================================================
-- TABLE: chat_history
-- Conversation messages between user and AI tutor per subject
-- =============================================================================
CREATE TABLE IF NOT EXISTS chat_history (
    id                      TEXT    PRIMARY KEY,
    user_id                 TEXT    NOT NULL REFERENCES users (id)    ON DELETE CASCADE,
    subject_id              TEXT    NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    -- Message content
    user_message            TEXT    NOT NULL,
    bot_response            TEXT    NOT NULL,
    -- Context
    message_type            TEXT,   -- concept_explanation | question_analysis | study_planning
    relevant_question_ids   TEXT,   -- JSON array of referenced question UUIDs
    -- Metadata
    response_time_seconds   TEXT,
    user_feedback           TEXT,   -- positive | negative | neutral
    -- Timestamps
    created_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_id    ON chat_history (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_subject_id ON chat_history (subject_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created    ON chat_history (created_at);


-- =============================================================================
-- TABLE: mock_tests
-- Mock exams generated for a user per subject
-- =============================================================================
CREATE TABLE IF NOT EXISTS mock_tests (
    id                  TEXT    PRIMARY KEY,
    user_id             TEXT    NOT NULL REFERENCES users (id)    ON DELETE CASCADE,
    subject_id          TEXT    NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    -- Configuration
    total_questions     INTEGER NOT NULL DEFAULT 0,
    total_marks         INTEGER,
    duration_minutes    INTEGER,
    difficulty_level    TEXT,   -- easy | medium | hard
    -- Questions list
    questions_json      TEXT    NOT NULL,   -- JSON array of question objects
    -- Execution
    start_time          TEXT,
    end_time            TEXT,
    is_completed        INTEGER NOT NULL DEFAULT 0,
    -- Results
    user_answers_json   TEXT,   -- JSON: { "q1": "A", "q2": "C" }
    score               REAL,
    percentage          REAL,
    -- Analysis
    correct_count       INTEGER,
    incorrect_count     INTEGER,
    skipped_count       INTEGER,
    weak_topics_json    TEXT,   -- JSON array
    strong_topics_json  TEXT,   -- JSON array
    -- Timestamps
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_mock_tests_user_id    ON mock_tests (user_id);
CREATE INDEX IF NOT EXISTS idx_mock_tests_subject_id ON mock_tests (subject_id);
CREATE INDEX IF NOT EXISTS idx_mock_tests_completed  ON mock_tests (is_completed);


-- =============================================================================
-- TABLE: study_plans
-- AI-generated day-by-day study schedule per subject
-- =============================================================================
CREATE TABLE IF NOT EXISTS study_plans (
    id                      TEXT    PRIMARY KEY,
    user_id                 TEXT    NOT NULL REFERENCES users (id)    ON DELETE CASCADE,
    subject_id              TEXT    NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    -- Plan details
    plan_name               TEXT,
    start_date              TEXT,
    exam_date               TEXT,
    total_days              INTEGER,
    -- Schedule
    daily_schedule_json     TEXT,   -- JSON: [{ "day":1, "date":"...", "topics":[...], "duration_hours":2 }]
    -- Progress
    days_completed          INTEGER NOT NULL DEFAULT 0,
    completion_percentage   REAL    NOT NULL DEFAULT 0.0,
    on_track                INTEGER NOT NULL DEFAULT 1,
    last_update_date        TEXT,
    -- Timestamps
    created_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_study_plans_user_id    ON study_plans (user_id);
CREATE INDEX IF NOT EXISTS idx_study_plans_subject_id ON study_plans (subject_id);


-- =============================================================================
-- TABLE: study_sessions
-- Individual timed study sessions (enhanced model)
-- =============================================================================
CREATE TABLE IF NOT EXISTS study_sessions (
    id                  TEXT    PRIMARY KEY,
    user_id             TEXT    NOT NULL REFERENCES users (id)    ON DELETE CASCADE,
    subject_id          TEXT    NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    topic_id            TEXT    REFERENCES topics (id) ON DELETE SET NULL,
    start_time          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    end_time            TEXT,
    duration_minutes    INTEGER,
    focus_level         INTEGER,    -- 1-5 scale
    notes               TEXT,
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_study_sessions_user_id    ON study_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_study_sessions_subject_id ON study_sessions (subject_id);


-- =============================================================================
-- TABLE: test_results
-- Full test result records (enhanced model — complements mock_tests)
-- =============================================================================
CREATE TABLE IF NOT EXISTS test_results (
    id              TEXT    PRIMARY KEY,
    user_id         TEXT    NOT NULL REFERENCES users (id)    ON DELETE CASCADE,
    subject_id      TEXT    NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    test_name       TEXT,
    total_marks     INTEGER,
    obtained_marks  INTEGER,
    percentage      REAL,
    time_taken      INTEGER,    -- minutes
    completed_at    TEXT        DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    answers         TEXT,       -- JSON: user answers
    review_notes    TEXT,
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_test_results_user_id    ON test_results (user_id);
CREATE INDEX IF NOT EXISTS idx_test_results_subject_id ON test_results (subject_id);


-- =============================================================================
-- TABLE: test_questions
-- Per-question answer breakdown for a test result (enhanced model)
-- =============================================================================
CREATE TABLE IF NOT EXISTS test_questions (
    id                  TEXT    PRIMARY KEY,
    test_result_id      TEXT    NOT NULL REFERENCES test_results (id) ON DELETE CASCADE,
    question_id         TEXT    NOT NULL REFERENCES questions (id)    ON DELETE CASCADE,
    user_answer         TEXT,
    is_correct          INTEGER,    -- 0 | 1
    time_spent          INTEGER,    -- seconds
    confidence_level    INTEGER,    -- 1-5 scale
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_test_questions_test_result_id ON test_questions (test_result_id);
CREATE INDEX IF NOT EXISTS idx_test_questions_question_id    ON test_questions (question_id);


-- =============================================================================
-- TABLE: user_progress
-- Aggregate daily progress snapshot per user per subject (enhanced model)
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_progress (
    id                      TEXT    PRIMARY KEY,
    user_id                 TEXT    NOT NULL REFERENCES users (id)    ON DELETE CASCADE,
    subject_id              TEXT    NOT NULL REFERENCES subjects (id) ON DELETE CASCADE,
    date                    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    completion_percentage   REAL,   -- 0-100
    study_hours             REAL,
    topics_covered          INTEGER,
    practice_tests_taken    INTEGER,
    average_score           REAL,
    streak_days             INTEGER,
    created_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at              TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_user_progress_user_id    ON user_progress (user_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_subject_id ON user_progress (subject_id);


-- =============================================================================
-- TABLE: topic_performance
-- Per-user, per-topic accuracy and confidence tracking (enhanced model)
-- =============================================================================
CREATE TABLE IF NOT EXISTS topic_performance (
    id                          TEXT    PRIMARY KEY,
    user_id                     TEXT    NOT NULL REFERENCES users (id)   ON DELETE CASCADE,
    topic_id                    TEXT    NOT NULL REFERENCES topics (id)  ON DELETE CASCADE,
    accuracy                    REAL,       -- 0-100
    attempts                    INTEGER,
    average_time                REAL,       -- minutes
    last_practiced              TEXT,
    confidence_level            INTEGER,    -- 1-5 scale
    weak_areas                  TEXT        DEFAULT '[]',           -- JSON array
    improvement_suggestions     TEXT        DEFAULT '[]',           -- JSON array
    created_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at                  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_topic_performance_user_id  ON topic_performance (user_id);
CREATE INDEX IF NOT EXISTS idx_topic_performance_topic_id ON topic_performance (topic_id);


-- =============================================================================
-- TABLE: model_predictions
-- Cached ML model outputs (progress forecast, topic recommendation, etc.)
-- =============================================================================
CREATE TABLE IF NOT EXISTS model_predictions (
    id                  TEXT    PRIMARY KEY,
    user_id             TEXT    NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    model_type          TEXT,   -- progress_forecast | topic_recommendation | focus_area | …
    input_data          TEXT,   -- JSON
    prediction_result   TEXT,   -- JSON
    confidence_score    REAL,   -- 0-1
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    expires_at          TEXT
);

CREATE INDEX IF NOT EXISTS idx_model_predictions_user_id ON model_predictions (user_id);


-- =============================================================================
-- TABLE: user_preferences
-- Arbitrary key-value preference store per user (enhanced model)
-- =============================================================================
CREATE TABLE IF NOT EXISTS user_preferences (
    id                  TEXT    PRIMARY KEY,
    user_id             TEXT    NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    preference_type     TEXT,   -- study_time | difficulty_level | question_type | …
    preference_value    TEXT,   -- JSON value
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences (user_id);


-- =============================================================================
-- TABLE: question_ratings
-- Crowd-sourced difficulty / quality ratings on questions (enhanced model)
-- =============================================================================
CREATE TABLE IF NOT EXISTS question_ratings (
    id                  TEXT    PRIMARY KEY,
    question_id         TEXT    NOT NULL REFERENCES questions (id) ON DELETE CASCADE,
    user_id             TEXT    REFERENCES users (id) ON DELETE SET NULL,   -- nullable = anonymous
    difficulty_rating   INTEGER,    -- 1-5 scale
    quality_rating      INTEGER,    -- 1-5 scale
    usefulness_rating   INTEGER,    -- 1-5 scale
    tags                TEXT    DEFAULT '[]',   -- JSON array
    feedback            TEXT,
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_question_ratings_question_id ON question_ratings (question_id);
CREATE INDEX IF NOT EXISTS idx_question_ratings_user_id     ON question_ratings (user_id);

-- =============================================================================
-- End of PrepIQ schema
-- =============================================================================
