from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import os

Base = declarative_base()

# Check if we're using SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./prepiq_local.db")
IS_SQLITE = DATABASE_URL.startswith("sqlite")

class User(Base):
    __tablename__ = "users"

    # Handle UUID differently for SQLite vs PostgreSQL
    if IS_SQLITE:
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    else:
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255))
    college_name = Column(String(255))
    program = Column(String(100))  # BTech, BSc, MSc
    year_of_study = Column(Integer)

    # Preferences
    theme_preference = Column(String(20), default='system')  # light/dark/system
    language = Column(String(10), default='en')
    exam_date = Column(DateTime)

    # Account
    email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)  # Soft delete

    # Relationships
    subjects = relationship("Subject", back_populates="user")
    predictions = relationship("Prediction", back_populates="user")
    chat_history = relationship("ChatHistory", back_populates="user")
    mock_tests = relationship("MockTest", back_populates="user")
    study_plans = relationship("StudyPlan", back_populates="user")

class Subject(Base):
    __tablename__ = "subjects"

    # Handle UUID differently for SQLite vs PostgreSQL
    if IS_SQLITE:
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    else:
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Subject Info
    name = Column(String(255), nullable=False)  # Linear Algebra, Data Structures
    code = Column(String(50))  # MA201, CS201
    semester = Column(Integer)
    academic_year = Column(String(20))  # 2024-2025

    # Exam Details
    total_marks = Column(Integer)
    exam_date = Column(DateTime)
    exam_duration_minutes = Column(Integer)

    # Syllabus
    syllabus_json = Column(JSON)  # { "units": [{ "name": "Unit 1", "topics": [...] }] }

    # Status
    papers_uploaded = Column(Integer, default=0)
    predictions_generated = Column(Integer, default=0)
    mock_tests_created = Column(Integer, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subjects")
    question_papers = relationship("QuestionPaper", back_populates="subject")
    predictions = relationship("Prediction", back_populates="subject")
    chat_history = relationship("ChatHistory", back_populates="subject")
    mock_tests = relationship("MockTest", back_populates="subject")
    study_plans = relationship("StudyPlan", back_populates="subject")

class QuestionPaper(Base):
    __tablename__ = "question_papers"

    # Handle UUID differently for SQLite vs PostgreSQL
    if IS_SQLITE:
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
    else:
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)

    # File Info
    file_name = Column(String(255))
    file_path = Column(String(512))
    s3_key = Column(String(512))  # Supabase Storage path
    file_size_bytes = Column(Integer)

    # Metadata
    exam_year = Column(Integer)  # 2024
    exam_semester = Column(Integer)
    total_marks = Column(Integer)
    duration_minutes = Column(Integer)

    # Processing
    raw_text = Column(Text)  # Full extracted text
    metadata_json = Column(Text)  # PDF metadata as JSON string
    extraction_confidence = Column(String(5))  # 0-1
    extraction_method = Column(String(50))  # pdfplumber, tesseract

    # Status
    processing_status = Column(String(50), default='pending')  # pending, processing, completed, failed
    error_message = Column(Text)
    processed_at = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    subject = relationship("Subject", back_populates="question_papers")
    questions = relationship("Question", back_populates="paper")

class Question(Base):
    __tablename__ = "questions"

    # Handle UUID differently for SQLite vs PostgreSQL
    if IS_SQLITE:
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        paper_id = Column(String(36), ForeignKey("question_papers.id"), nullable=False)
    else:
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        paper_id = Column(UUID(as_uuid=True), ForeignKey("question_papers.id"), nullable=False)

    # Question Content
    question_text = Column(Text, nullable=False)
    question_number = Column(Integer)
    marks = Column(Integer)

    # Classification
    unit_id = Column(String(50))  # Unit 1, Unit 2
    unit_name = Column(String(255))
    topics_json = Column(JSON)  # ["Binary Search", "Complexity Analysis"]
    question_type = Column(String(50))  # mcq, short_answer, numerical, essay
    difficulty = Column(String(20))  # easy, medium, hard

    # Metadata
    section_name = Column(String(100))  # Part A, Part B, Section I
    has_subparts = Column(Boolean, default=False)
    subparts_count = Column(Integer)

    # Analysis
    is_repeated = Column(Boolean, default=False)
    similar_question_ids = Column(String)  # Array of related questions
    text_length = Column(Integer)  # Length of the question text

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    paper = relationship("QuestionPaper", back_populates="questions")

class Prediction(Base):
    __tablename__ = "predictions"

    # Handle UUID differently for SQLite vs PostgreSQL
    if IS_SQLITE:
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
        user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    else:
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
        user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Prediction Data
    predicted_questions_json = Column(Text)  # Large JSON with all predictions
    total_questions = Column(Integer)
    total_predicted_marks = Column(Integer)

    # Probability Distribution
    very_high_count = Column(Integer)
    high_count = Column(Integer)
    moderate_count = Column(Integer)

    # Coverage
    unit_coverage_json = Column(JSON)  # { "Unit 1": 45%, "Unit 2": 30% }
    topic_coverage_percentage = Column(String(5))

    # Analysis
    analysis_summary = Column(Text)
    key_insights_json = Column(JSON)
    ml_analysis_json = Column(Text)  # ML analysis results as JSON string

    # Accuracy Tracking (filled after exam)
    actual_exam_questions_json = Column(Text)
    accuracy_score = Column(String(5))  # % of predictions that appeared
    prediction_accuracy_score = Column(String(5))  # Estimated accuracy of predictions

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    subject = relationship("Subject", back_populates="predictions")
    user = relationship("User", back_populates="predictions")

class ChatHistory(Base):
    __tablename__ = "chat_history"

    # Handle UUID differently for SQLite vs PostgreSQL
    if IS_SQLITE:
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
        subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
    else:
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
        subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)

    # Message Content
    user_message = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)

    # Context
    message_type = Column(String(50))  # concept_explanation, question_analysis, study_planning
    relevant_question_ids = Column(String)  # Referenced questions

    # Metadata
    response_time_seconds = Column(String(5))
    user_feedback = Column(Integer)  # -1: unhelpful, 0: neutral, 1: helpful

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="chat_history")
    subject = relationship("Subject", back_populates="chat_history")

class MockTest(Base):
    __tablename__ = "mock_tests"

    # Handle UUID differently for SQLite vs PostgreSQL
    if IS_SQLITE:
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
        subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
    else:
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
        subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)

    # Test Configuration
    total_questions = Column(Integer)
    total_marks = Column(Integer)
    duration_minutes = Column(Integer)
    difficulty_level = Column(String(50))  # easy, medium, hard

    # Question Selection
    questions_json = Column(JSON)  # Array of question objects with options

    # Test Execution
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_completed = Column(Boolean, default=False)

    # Results
    user_answers_json = Column(JSON)  # { "q1": "A", "q2": "C" }
    score = Column(Integer)
    percentage = Column(String(5))

    # Analysis
    correct_count = Column(Integer)
    incorrect_count = Column(Integer)
    skipped_count = Column(Integer)

    weak_topics_json = Column(JSON)  # Topics user got wrong
    strong_topics_json = Column(JSON)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="mock_tests")
    subject = relationship("Subject", back_populates="mock_tests")


class StudyPlan(Base):
    __tablename__ = "study_plans"

    # Handle UUID differently for SQLite vs PostgreSQL
    if IS_SQLITE:
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
        subject_id = Column(String(36), ForeignKey("subjects.id"), nullable=False)
    else:
        id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
        subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)

    # Plan Details
    plan_name = Column(String(255))
    start_date = Column(DateTime)
    exam_date = Column(DateTime)
    total_days = Column(Integer)

    # Daily Schedule
    daily_schedule_json = Column(JSON)  # [ { "day": 1, "date": "2025-01-06", "topics": [...], "duration_hours": 2 } ]

    # Progress Tracking
    days_completed = Column(Integer, default=0)
    completion_percentage = Column(String(5), default="0")

    # Adherence
    on_track = Column(Boolean, default=True)
    last_update_date = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="study_plans")
    subject = relationship("Subject", back_populates="study_plans")