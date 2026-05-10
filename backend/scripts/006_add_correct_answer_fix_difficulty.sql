-- =============================================================================
-- Migration 006: Add correct_answer column + fix difficulty column name
-- =============================================================================

-- Migration 002 renamed difficulty → difficulty_level but the SQLAlchemy model
-- still maps to "difficulty". Rename it back so model and DB are in sync.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'questions' AND column_name = 'difficulty_level'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'questions' AND column_name = 'difficulty'
    ) THEN
        ALTER TABLE questions RENAME COLUMN difficulty_level TO difficulty;
    END IF;
END $$;

-- Add correct_answer column (used for mock test scoring)
ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS correct_answer VARCHAR(500);
