-- =============================================================================
-- Migration 004: Add missing columns to align schema.sql with SQLAlchemy models
-- Covers: BUG-C07 (users wizard columns) + BUG-C08 (question_papers, questions)
--         + BUG-H01 (predictions ml columns)
-- All statements use IF NOT EXISTS / DO $$ blocks so this script is idempotent.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- BUG-C07: users table — wizard flow, dashboard, study plan columns
-- -----------------------------------------------------------------------------

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS wizard_completed     BOOLEAN     NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS exam_name            VARCHAR(255),
    ADD COLUMN IF NOT EXISTS days_until_exam      INTEGER,
    ADD COLUMN IF NOT EXISTS focus_subjects       JSONB,
    ADD COLUMN IF NOT EXISTS study_hours_per_day  INTEGER,
    ADD COLUMN IF NOT EXISTS target_score         INTEGER,
    ADD COLUMN IF NOT EXISTS preparation_level    VARCHAR(50);

-- Index used by wizard status queries
CREATE INDEX IF NOT EXISTS idx_users_wizard_completed ON users(wizard_completed);

-- -----------------------------------------------------------------------------
-- BUG-C08: question_papers table — metadata_json column
-- -----------------------------------------------------------------------------

ALTER TABLE question_papers
    ADD COLUMN IF NOT EXISTS metadata_json TEXT;

-- -----------------------------------------------------------------------------
-- BUG-C08: questions table — text_length column
-- -----------------------------------------------------------------------------

ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS text_length INTEGER;

-- -----------------------------------------------------------------------------
-- BUG-H01: predictions table — ml_analysis_json + prediction_accuracy_score
-- (included here so a single migration run covers all Sprint-1 schema gaps)
-- -----------------------------------------------------------------------------

ALTER TABLE predictions
    ADD COLUMN IF NOT EXISTS ml_analysis_json          TEXT,
    ADD COLUMN IF NOT EXISTS prediction_accuracy_score VARCHAR(5);
