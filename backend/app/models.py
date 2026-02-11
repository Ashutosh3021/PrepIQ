"""
PrepIQ Database Models
SQLAlchemy models for PostgreSQL with Supabase
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, LargeBinary, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.database import Base


class User(Base):
    __tablename__ = "users"

    # Primary Key - PostgreSQL UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Required fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile - Required fields for registration
    full_name = Column(String(255), nullable=False)
    college_name = Column(String(255), nullable=False)
    program = Column(String(100), nullable=False, default='BTech')  # BTech, BSc, MSc
    year_of_study = Column(Integer, nullable=False, default=1)

    # Preferences - Optional
    theme_preference = Column(String(20), default='system', nullable=False)  # light/dark/system
    language = Column(String(10), default='en', nullable=False)
    exam_date = Column(DateTime, nullable=True)
    
    # Wizard Completion Flag
    wizard_completed = Column(Boolean, default=False, nullable=False)
    
    # Wizard Data - Optional
    exam_name = Column(String(255), nullable=True)
    days_until_exam = Column(Integer, nullable=True)
    focus_subjects = Column(JSON, nullable=True)  # Array of subject names/IDs
    study_hours_per_day = Column(Integer, nullable=True)
    target_score = Column(Integer, nullable=True)  # Percentage target
    preparation_level = Column(String(50), nullable=True)  # beginner, intermediate, advanced

    # Account
    email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    mock_tests = relationship("MockTest", back_populates="user", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_wizard_completed', 'wizard_completed'),
    )


class Subject(Base):
    __tablename__ = "subjects"

    # Primary Key - PostgreSQL UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key - Required
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Subject Info - Required
    name = Column(String(255), nullable=False)  # Linear Algebra, Data Structures
    code = Column(String(50), nullable=True)  # MA201, CS201
    semester = Column(Integer, nullable=True)
    academic_year = Column(String(20), nullable=True)  # 2024-2025

    # Exam Details - Optional
    total_marks = Column(Integer, nullable=True)
    exam_date = Column(DateTime, nullable=True)
    exam_duration_minutes = Column(Integer, nullable=True)

    # Syllabus
    syllabus_json = Column(JSON, nullable=True)  # { "units": [{ "name": "Unit 1", "topics": [...] }] }

    # Status - Computed fields (kept for caching)
    papers_uploaded = Column(Integer, default=0, nullable=False)
    predictions_generated = Column(Integer, default=0, nullable=False)
    mock_tests_created = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="subjects")
    question_papers = relationship("QuestionPaper", back_populates="subject", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="subject", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="subject", cascade="all, delete-orphan")
    mock_tests = relationship("MockTest", back_populates="subject", cascade="all, delete-orphan")
    study_plans = relationship("StudyPlan", back_populates="subject", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_subjects_user_id', 'user_id'),
        Index('idx_subjects_user_semester', 'user_id', 'semester'),
    )


class QuestionPaper(Base):
    __tablename__ = "question_papers"

    # Primary Key - PostgreSQL UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key - Required
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)

    # File Info
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)
    s3_key = Column(String(512), nullable=True)  # Supabase Storage path
    file_size_bytes = Column(Integer, nullable=True)

    # Metadata
    exam_year = Column(Integer, nullable=True)  # 2024
    exam_semester = Column(Integer, nullable=True)
    total_marks = Column(Integer, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    # Processing
    raw_text = Column(Text, nullable=True)  # Full extracted text
    metadata_json = Column(Text, nullable=True)  # PDF metadata as JSON string
    extraction_confidence = Column(String(5), nullable=True)  # 0-1
    extraction_method = Column(String(50), nullable=True)  # pdfplumber, tesseract

    # Status
    processing_status = Column(String(50), default='pending', nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="question_papers")
    questions = relationship("Question", back_populates="paper", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_question_papers_subject_id', 'subject_id'),
        Index('idx_question_papers_status', 'processing_status'),
    )


class Question(Base):
    __tablename__ = "questions"

    # Primary Key - PostgreSQL UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key - Required
    paper_id = Column(UUID(as_uuid=True), ForeignKey("question_papers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Question Content - Required
    question_text = Column(Text, nullable=False)
    question_number = Column(Integer, nullable=True)
    marks = Column(Integer, nullable=False, default=0)

    # Classification
    unit_id = Column(String(50), nullable=True)  # Unit 1, Unit 2
    unit_name = Column(String(255), nullable=True)
    topics_json = Column(JSON, nullable=True)  # ["Binary Search", "Complexity Analysis"]
    question_type = Column(String(50), nullable=True)  # mcq, short_answer, numerical, essay
    difficulty = Column(String(20), nullable=True)  # easy, medium, hard

    # Metadata
    section_name = Column(String(100), nullable=True)  # Part A, Part B, Section I
    has_subparts = Column(Boolean, default=False, nullable=False)
    subparts_count = Column(Integer, nullable=True)

    # Analysis
    is_repeated = Column(Boolean, default=False, nullable=False)
    similar_question_ids = Column(JSON, nullable=True)  # Array of related question UUIDs
    text_length = Column(Integer, nullable=True)  # Length of the question text

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    paper = relationship("QuestionPaper", back_populates="questions")

    # Indexes
    __table_args__ = (
        Index('idx_questions_paper_id', 'paper_id'),
        Index('idx_questions_difficulty', 'difficulty'),
        Index('idx_questions_unit', 'unit_id'),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    # Primary Key - PostgreSQL UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys - Required
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Prediction Data
    predicted_questions_json = Column(Text, nullable=True)  # Large JSON with all predictions
    total_questions = Column(Integer, nullable=True)
    total_predicted_marks = Column(Integer, nullable=True)

    # Probability Distribution
    very_high_count = Column(Integer, nullable=True)
    high_count = Column(Integer, nullable=True)
    moderate_count = Column(Integer, nullable=True)

    # Coverage
    unit_coverage_json = Column(JSON, nullable=True)  # { "Unit 1": 45%, "Unit 2": 30% }
    topic_coverage_percentage = Column(String(5), nullable=True)

    # Analysis
    analysis_summary = Column(Text, nullable=True)
    key_insights_json = Column(JSON, nullable=True)
    ml_analysis_json = Column(Text, nullable=True)  # ML analysis results as JSON string

    # Accuracy Tracking (filled after exam)
    actual_exam_questions_json = Column(Text, nullable=True)
    accuracy_score = Column(String(5), nullable=True)  # % of predictions that appeared
    prediction_accuracy_score = Column(String(5), nullable=True)  # Estimated accuracy of predictions

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    subject = relationship("Subject", back_populates="predictions")
    user = relationship("User", back_populates="predictions")

    # Indexes
    __table_args__ = (
        Index('idx_predictions_subject_id', 'subject_id'),
        Index('idx_predictions_user_id', 'user_id'),
        Index('idx_predictions_user_subject', 'user_id', 'subject_id'),
    )


class ChatHistory(Base):
    __tablename__ = "chat_history"

    # Primary Key - PostgreSQL UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys - Required
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Message Content - Required
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)

    # Context
    message_type = Column(String(50), nullable=True)  # concept_explanation, question_analysis, study_planning
    relevant_question_ids = Column(JSON, nullable=True)  # Referenced questions

    # Metadata
    response_time_seconds = Column(String(5), nullable=True)
    user_feedback = Column(Integer, nullable=True)  # -1: unhelpful, 0: neutral, 1: helpful

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="chat_history")
    subject = relationship("Subject", back_populates="chat_history")

    # Indexes
    __table_args__ = (
        Index('idx_chat_history_user_id', 'user_id'),
        Index('idx_chat_history_subject_id', 'subject_id'),
        Index('idx_chat_history_created', 'created_at'),
    )


class MockTest(Base):
    __tablename__ = "mock_tests"

    # Primary Key - PostgreSQL UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys - Required
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Test Configuration
    total_questions = Column(Integer, nullable=False, default=0)
    total_marks = Column(Integer, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    difficulty_level = Column(String(50), nullable=True)  # easy, medium, hard

    # Question Selection
    questions_json = Column(JSON, nullable=True)  # Array of question objects with options

    # Test Execution
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)

    # Results
    user_answers_json = Column(JSON, nullable=True)  # { "q1": "A", "q2": "C" }
    score = Column(Integer, nullable=True)
    percentage = Column(String(5), nullable=True)

    # Analysis
    correct_count = Column(Integer, nullable=True)
    incorrect_count = Column(Integer, nullable=True)
    skipped_count = Column(Integer, nullable=True)

    weak_topics_json = Column(JSON, nullable=True)  # Topics user got wrong
    strong_topics_json = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="mock_tests")
    subject = relationship("Subject", back_populates="mock_tests")

    # Indexes
    __table_args__ = (
        Index('idx_mock_tests_user_id', 'user_id'),
        Index('idx_mock_tests_subject_id', 'subject_id'),
        Index('idx_mock_tests_completed', 'is_completed'),
    )


class StudyPlan(Base):
    __tablename__ = "study_plans"

    # Primary Key - PostgreSQL UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys - Required
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Plan Details
    plan_name = Column(String(255), nullable=True)
    start_date = Column(DateTime, nullable=True)
    exam_date = Column(DateTime, nullable=True)
    total_days = Column(Integer, nullable=True)

    # Daily Schedule
    daily_schedule_json = Column(JSON, nullable=True)  # [ { "day": 1, "date": "2025-01-06", "topics": [...], "duration_hours": 2 } ]

    # Progress Tracking
    days_completed = Column(Integer, default=0, nullable=False)
    completion_percentage = Column(String(5), default="0", nullable=False)

    # Adherence
    on_track = Column(Boolean, default=True, nullable=False)
    last_update_date = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="study_plans")
    subject = relationship("Subject", back_populates="study_plans")

    # Indexes
    __table_args__ = (
        Index('idx_study_plans_user_id', 'user_id'),
        Index('idx_study_plans_subject_id', 'subject_id'),
    )


# Standalone function to create all tables
def create_tables(engine):
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
