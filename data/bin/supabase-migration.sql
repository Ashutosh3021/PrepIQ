# Supabase SQL Migration for PrepIQ Production
# Run this in Supabase Dashboard → SQL Editor

-- ============================================
-- EXTENSIONS
-- ============================================
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    college_name VARCHAR(255) NOT NULL,
    program VARCHAR(100) NOT NULL DEFAULT 'BTech',
    year_of_study INTEGER NOT NULL DEFAULT 1,
    theme_preference VARCHAR(20) NOT NULL DEFAULT 'system',
    language VARCHAR(10) NOT NULL DEFAULT 'en',
    exam_date TIMESTAMP WITH TIME ZONE,
    wizard_completed BOOLEAN NOT NULL DEFAULT FALSE,
    exam_name VARCHAR(255),
    days_until_exam INTEGER,
    focus_subjects JSONB,
    study_hours_per_day INTEGER,
    target_score INTEGER,
    preparation_level VARCHAR(50),
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_wizard_completed ON users(wizard_completed);

-- ============================================
-- SUBJECTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50),
    semester INTEGER,
    academic_year VARCHAR(20),
    total_marks INTEGER,
    exam_date TIMESTAMP WITH TIME ZONE,
    exam_duration_minutes INTEGER,
    syllabus_json JSONB,
    papers_uploaded INTEGER NOT NULL DEFAULT 0,
    predictions_generated INTEGER NOT NULL DEFAULT 0,
    mock_tests_created INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for subjects table
CREATE INDEX IF NOT EXISTS idx_subjects_user_id ON subjects(user_id);
CREATE INDEX IF NOT EXISTS idx_subjects_user_semester ON subjects(user_id, semester);

-- ============================================
-- QUESTION PAPERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS question_papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512),
    s3_key VARCHAR(512),
    file_size_bytes INTEGER,
    exam_year INTEGER,
    exam_semester INTEGER,
    total_marks INTEGER,
    duration_minutes INTEGER,
    raw_text TEXT,
    metadata_json TEXT,
    extraction_confidence VARCHAR(5),
    extraction_method VARCHAR(50),
    processing_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for question_papers table
CREATE INDEX IF NOT EXISTS idx_question_papers_subject_id ON question_papers(subject_id);
CREATE INDEX IF NOT EXISTS idx_question_papers_status ON question_papers(processing_status);

-- ============================================
-- QUESTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES question_papers(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_number INTEGER,
    marks INTEGER NOT NULL DEFAULT 0,
    unit_id VARCHAR(50),
    unit_name VARCHAR(255),
    topics_json JSONB,
    question_type VARCHAR(50),
    difficulty VARCHAR(20),
    section_name VARCHAR(100),
    has_subparts BOOLEAN NOT NULL DEFAULT FALSE,
    subparts_count INTEGER,
    is_repeated BOOLEAN NOT NULL DEFAULT FALSE,
    similar_question_ids JSONB,
    text_length INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for questions table
CREATE INDEX IF NOT EXISTS idx_questions_paper_id ON questions(paper_id);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX IF NOT EXISTS idx_questions_unit ON questions(unit_id);

-- ============================================
-- PREDICTIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    predicted_questions_json TEXT,
    total_questions INTEGER,
    total_predicted_marks INTEGER,
    very_high_count INTEGER,
    high_count INTEGER,
    moderate_count INTEGER,
    unit_coverage_json JSONB,
    topic_coverage_percentage VARCHAR(5),
    analysis_summary TEXT,
    key_insights_json JSONB,
    ml_analysis_json TEXT,
    actual_exam_questions_json TEXT,
    accuracy_score VARCHAR(5),
    prediction_accuracy_score VARCHAR(5),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for predictions table
CREATE INDEX IF NOT EXISTS idx_predictions_subject_id ON predictions(subject_id);
CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_user_subject ON predictions(user_id, subject_id);

-- ============================================
-- CHAT HISTORY TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    message_type VARCHAR(50),
    relevant_question_ids JSONB,
    response_time_seconds VARCHAR(5),
    user_feedback INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for chat_history table
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_subject_id ON chat_history(subject_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_created ON chat_history(created_at);

-- ============================================
-- MOCK TESTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS mock_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    total_questions INTEGER NOT NULL DEFAULT 0,
    total_marks INTEGER,
    duration_minutes INTEGER,
    difficulty_level VARCHAR(50),
    questions_json JSONB,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    user_answers_json JSONB,
    score INTEGER,
    percentage VARCHAR(5),
    correct_count INTEGER,
    incorrect_count INTEGER,
    skipped_count INTEGER,
    weak_topics_json JSONB,
    strong_topics_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for mock_tests table
CREATE INDEX IF NOT EXISTS idx_mock_tests_user_id ON mock_tests(user_id);
CREATE INDEX IF NOT EXISTS idx_mock_tests_subject_id ON mock_tests(subject_id);
CREATE INDEX IF NOT EXISTS idx_mock_tests_completed ON mock_tests(is_completed);

-- ============================================
-- STUDY PLANS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS study_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    plan_name VARCHAR(255),
    start_date TIMESTAMP WITH TIME ZONE,
    exam_date TIMESTAMP WITH TIME ZONE,
    total_days INTEGER,
    daily_schedule_json JSONB,
    days_completed INTEGER NOT NULL DEFAULT 0,
    completion_percentage VARCHAR(5) NOT NULL DEFAULT '0',
    on_track BOOLEAN NOT NULL DEFAULT TRUE,
    last_update_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for study_plans table
CREATE INDEX IF NOT EXISTS idx_study_plans_user_id ON study_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_study_plans_subject_id ON study_plans(subject_id);

-- ============================================
-- RLS POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE mock_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_plans ENABLE ROW LEVEL SECURITY;

-- Users table policies
CREATE POLICY "Users can view own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id);

-- Subjects table policies
CREATE POLICY "Users can manage own subjects"
    ON subjects FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Question Papers table policies
CREATE POLICY "Users can manage own papers"
    ON question_papers FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM subjects
            WHERE subjects.id = question_papers.subject_id
            AND subjects.user_id = auth.uid()
        )
    );

-- Questions table policies
CREATE POLICY "Users can view own questions"
    ON questions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM question_papers
            JOIN subjects ON question_papers.subject_id = subjects.id
            WHERE questions.paper_id = question_papers.id
            AND subjects.user_id = auth.uid()
        )
    );

-- Predictions table policies
CREATE POLICY "Users can manage own predictions"
    ON predictions FOR ALL
    USING (auth.uid() = user_id);

-- Chat History table policies
CREATE POLICY "Users can manage own chat history"
    ON chat_history FOR ALL
    USING (auth.uid() = user_id);

-- Mock Tests table policies
CREATE POLICY "Users can manage own tests"
    ON mock_tests FOR ALL
    USING (auth.uid() = user_id);

-- Study Plans table policies
CREATE POLICY "Users can manage own study plans"
    ON study_plans FOR ALL
    USING (auth.uid() = user_id);

-- ============================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subjects_updated_at BEFORE UPDATE ON subjects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_question_papers_updated_at BEFORE UPDATE ON question_papers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON predictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_study_plans_updated_at BEFORE UPDATE ON study_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- COMPLETION MESSAGE
-- ============================================
SELECT '✅ PrepIQ database schema created successfully!' as status;
