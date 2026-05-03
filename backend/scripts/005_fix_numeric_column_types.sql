-- =============================================================================
-- Migration 005: Fix numeric column types to match SQLAlchemy Numeric models
-- Covers: BUG-M03, BUG-M05, BUG-M06, BUG-M07
-- All ALTER COLUMN statements use USING to safely cast existing string data.
-- =============================================================================

-- BUG-M07: question_papers.extraction_confidence  String(5) → DECIMAL(3,2)
ALTER TABLE question_papers
    ALTER COLUMN extraction_confidence TYPE DECIMAL(3,2)
    USING CASE
        WHEN extraction_confidence IS NULL THEN NULL
        ELSE ROUND(extraction_confidence::NUMERIC, 2)
    END;

-- BUG-M06: predictions.accuracy_score  String(5) → DECIMAL(5,2)
ALTER TABLE predictions
    ALTER COLUMN accuracy_score TYPE DECIMAL(5,2)
    USING CASE
        WHEN accuracy_score IS NULL THEN NULL
        ELSE ROUND(accuracy_score::NUMERIC, 2)
    END;

-- BUG-M06: predictions.prediction_accuracy_score  String(5) → DECIMAL(5,2)
-- (column was added in migration 004 as VARCHAR(5); change it now)
ALTER TABLE predictions
    ALTER COLUMN prediction_accuracy_score TYPE DECIMAL(5,2)
    USING CASE
        WHEN prediction_accuracy_score IS NULL THEN NULL
        ELSE ROUND(prediction_accuracy_score::NUMERIC, 2)
    END;

-- BUG-M03: mock_tests.score  INTEGER → DECIMAL(5,2)
ALTER TABLE mock_tests
    ALTER COLUMN score TYPE DECIMAL(5,2)
    USING CASE
        WHEN score IS NULL THEN NULL
        ELSE score::DECIMAL(5,2)
    END;

-- BUG-M03: mock_tests.percentage  String(5) → DECIMAL(5,2)
ALTER TABLE mock_tests
    ALTER COLUMN percentage TYPE DECIMAL(5,2)
    USING CASE
        WHEN percentage IS NULL THEN NULL
        ELSE ROUND(percentage::NUMERIC, 2)
    END;

-- BUG-M05: study_plans.completion_percentage  String(5) → DECIMAL(5,2)
ALTER TABLE study_plans
    ALTER COLUMN completion_percentage TYPE DECIMAL(5,2)
    USING CASE
        WHEN completion_percentage IS NULL THEN 0.00
        ELSE ROUND(completion_percentage::NUMERIC, 2)
    END;

-- BUG-M01: questions.question_number  VARCHAR(20) → INTEGER (model uses Integer)
ALTER TABLE questions
    ALTER COLUMN question_number TYPE INTEGER
    USING CASE
        WHEN question_number IS NULL THEN NULL
        WHEN question_number ~ '^\d+$' THEN question_number::INTEGER
        ELSE NULL
    END;
