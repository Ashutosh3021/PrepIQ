-- PrepIQ Application Database Schema
-- Creates all necessary tables with proper relationships and constraints

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension if needed for ML features
CREATE EXTENSION IF NOT EXISTS "vector";

-- 1. Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    college_name VARCHAR(255),
    program VARCHAR(100),
    year_of_study INTEGER,
    theme_preference VARCHAR(20) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'en',
    exam_date TIMESTAMP WITH TIME ZONE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for users table
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_college_name ON users(college_name);
CREATE INDEX idx_users_program ON users(program);
CREATE INDEX idx_users_year_of_study ON users(year_of_study);

-- 2. Subjects table
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(100),
    semester VARCHAR(20),
    academic_year VARCHAR(20),
    total_marks INTEGER,
    exam_date DATE,
    exam_duration_minutes INTEGER,
    syllabus_json JSONB,
    papers_uploaded BOOLEAN DEFAULT FALSE,
    predictions_generated BOOLEAN DEFAULT FALSE,
    mock_tests_created BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for subjects table
CREATE INDEX idx_subjects_user_id ON subjects(user_id);
CREATE INDEX idx_subjects_name ON subjects(name);
CREATE INDEX idx_subjects_code ON subjects(code);
CREATE INDEX idx_subjects_academic_year ON subjects(academic_year);

-- 3. Question Papers table
CREATE TABLE question_papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000),
    s3_key VARCHAR(1000),
    file_size_bytes BIGINT,
    exam_year INTEGER,
    exam_semester VARCHAR(20),
    total_marks INTEGER,
    duration_minutes INTEGER,
    raw_text TEXT,
    extraction_confidence DECIMAL(3,2),
    extraction_method VARCHAR(50),
    processing_status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for question_papers table
CREATE INDEX idx_question_papers_subject_id ON question_papers(subject_id);
CREATE INDEX idx_question_papers_exam_year ON question_papers(exam_year);
CREATE INDEX idx_question_papers_processing_status ON question_papers(processing_status);
CREATE INDEX idx_question_papers_created_at ON question_papers(created_at);

-- 4. Questions table
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id UUID NOT NULL REFERENCES question_papers(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_number VARCHAR(20),
    marks DECIMAL(5,2),
    unit_id VARCHAR(50),
    unit_name VARCHAR(255),
    topics_json JSONB,
    question_type VARCHAR(50),
    difficulty VARCHAR(20),
    section_name VARCHAR(100),
    has_subparts BOOLEAN DEFAULT FALSE,
    subparts_count INTEGER DEFAULT 0,
    is_repeated BOOLEAN DEFAULT FALSE,
    similar_question_ids UUID[],
    embedding vector(768), -- Assuming 768-dimensional embeddings for similarity search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for questions table
CREATE INDEX idx_questions_paper_id ON questions(paper_id);
CREATE INDEX idx_questions_unit_id ON questions(unit_id);
CREATE INDEX idx_questions_question_type ON questions(question_type);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_embedding ON questions USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100); -- For similarity search

-- 5. Predictions table
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    predicted_questions_json JSONB,
    total_questions INTEGER,
    total_predicted_marks INTEGER,
    very_high_count INTEGER DEFAULT 0,
    high_count INTEGER DEFAULT 0,
    moderate_count INTEGER DEFAULT 0,
    unit_coverage_json JSONB,
    topic_coverage_percentage DECIMAL(5,2),
    analysis_summary TEXT,
    key_insights_json JSONB,
    actual_exam_questions_json JSONB,
    accuracy_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for predictions table
CREATE INDEX idx_predictions_subject_id ON predictions(subject_id);
CREATE INDEX idx_predictions_user_id ON predictions(user_id);
CREATE INDEX idx_predictions_created_at ON predictions(created_at);

-- 6. Mock Tests table
CREATE TABLE mock_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    total_questions INTEGER NOT NULL,
    total_marks INTEGER NOT NULL,
    duration_minutes INTEGER,
    difficulty_level VARCHAR(20) DEFAULT 'moderate',
    questions_json JSONB NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN DEFAULT FALSE,
    user_answers_json JSONB,
    score DECIMAL(5,2),
    percentage DECIMAL(5,2),
    correct_count INTEGER DEFAULT 0,
    incorrect_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    weak_topics_json JSONB,
    strong_topics_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for mock_tests table
CREATE INDEX idx_mock_tests_user_id ON mock_tests(user_id);
CREATE INDEX idx_mock_tests_subject_id ON mock_tests(subject_id);
CREATE INDEX idx_mock_tests_is_completed ON mock_tests(is_completed);
CREATE INDEX idx_mock_tests_created_at ON mock_tests(created_at);

-- 7. Chat History table
CREATE TABLE chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'general',
    relevant_question_ids UUID[],
    response_time_seconds DECIMAL(6,3),
    user_feedback VARCHAR(20), -- 'positive', 'negative', 'neutral'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for chat_history table
CREATE INDEX idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX idx_chat_history_subject_id ON chat_history(subject_id);
CREATE INDEX idx_chat_history_created_at ON chat_history(created_at);
CREATE INDEX idx_chat_history_message_type ON chat_history(message_type);

-- 8. Study Plans table
CREATE TABLE study_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    plan_name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    exam_date DATE NOT NULL,
    total_days INTEGER NOT NULL,
    daily_schedule_json JSONB NOT NULL,
    days_completed INTEGER DEFAULT 0,
    completion_percentage DECIMAL(5,2) DEFAULT 0.00,
    on_track BOOLEAN DEFAULT TRUE,
    last_update_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for study_plans table
CREATE INDEX idx_study_plans_user_id ON study_plans(user_id);
CREATE INDEX idx_study_plans_subject_id ON study_plans(subject_id);
CREATE INDEX idx_study_plans_start_date ON study_plans(start_date);
CREATE INDEX idx_study_plans_exam_date ON study_plans(exam_date);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Attach the trigger to tables that have updated_at column
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_subjects_updated_at BEFORE UPDATE ON subjects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_question_papers_updated_at BEFORE UPDATE ON question_papers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_questions_updated_at BEFORE UPDATE ON questions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON predictions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_mock_tests_updated_at BEFORE UPDATE ON mock_tests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_study_plans_updated_at BEFORE UPDATE ON study_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Additional indexes for common query patterns
CREATE INDEX idx_questions_topics_gin ON questions USING gin(topics_json);
CREATE INDEX idx_predictions_key_insights_gin ON predictions USING gin(key_insights_json);
CREATE INDEX idx_mock_tests_weak_topics_gin ON mock_tests USING gin(weak_topics_json);
CREATE INDEX idx_mock_tests_strong_topics_gin ON mock_tests USING gin(strong_topics_json);
CREATE INDEX idx_study_plans_daily_schedule_gin ON study_plans USING gin(daily_schedule_json);

-- Grant permissions (adjust as needed for your setup)
GRANT ALL PRIVILEGES ON TABLE users TO postgres;
GRANT ALL PRIVILEGES ON TABLE subjects TO postgres;
GRANT ALL PRIVILEGES ON TABLE question_papers TO postgres;
GRANT ALL PRIVILEGES ON TABLE questions TO postgres;
GRANT ALL PRIVILEGES ON TABLE predictions TO postgres;
GRANT ALL PRIVILEGES ON TABLE mock_tests TO postgres;
GRANT ALL PRIVILEGES ON TABLE chat_history TO postgres;
GRANT ALL PRIVILEGES ON TABLE study_plans TO postgres;

-- Grant usage on sequences if any (for uuid_generate_v4)
GRANT USAGE ON SCHEMA public TO postgres;