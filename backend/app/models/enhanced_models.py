from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    college_name = Column(String)
    program = Column(String)
    year_of_study = Column(Integer)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    theme_preference = Column(String, default="system")
    language = Column(String, default="en")
    roles = Column(JSON, default=["user"])  # Store as JSON array
    permissions = Column(JSON, default=[])  # Store as JSON array
    
    # Relationships
    study_sessions = relationship("StudySession", back_populates="user")
    test_results = relationship("TestResult", back_populates="user")
    user_progress = relationship("UserProgress", back_populates="user")
    topic_performance = relationship("TopicPerformance", back_populates="user")
    model_predictions = relationship("ModelPrediction", back_populates="user")
    user_preferences = relationship("UserPreference", back_populates="user")


class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(String, primary_key=True)
    name = Column(String, index=True)
    code = Column(String, unique=True)
    description = Column(Text)
    credits = Column(Integer)
    semester = Column(Integer)
    department = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    topics = relationship("Topic", back_populates="subject")
    questions = relationship("Question", back_populates="subject")


class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(String, primary_key=True)
    subject_id = Column(String, ForeignKey("subjects.id"))
    name = Column(String, index=True)
    description = Column(Text)
    difficulty_level = Column(Integer)  # 1-5 scale
    estimated_hours = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subject = relationship("Subject", back_populates="topics")
    questions = relationship("Question", back_populates="topic")
    topic_performance = relationship("TopicPerformance", back_populates="topic")


class Question(Base):
    __tablename__ = "questions"
    
    id = Column(String, primary_key=True)
    subject_id = Column(String, ForeignKey("subjects.id"))
    topic_id = Column(String, ForeignKey("topics.id"))
    text = Column(Text)
    marks = Column(Integer)
    difficulty = Column(Integer)  # 1-5 scale
    question_type = Column(String)  # MCQ, Short Answer, Long Answer, etc.
    options = Column(JSON)  # For MCQ questions
    correct_answer = Column(Text)
    explanation = Column(Text)
    unit = Column(String)
    chapter = Column(String)
    tags = Column(JSON, default=[])  # Store as JSON array
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subject = relationship("Subject", back_populates="questions")
    topic = relationship("Topic", back_populates="questions")
    test_questions = relationship("TestQuestion", back_populates="question")


class StudySession(Base):
    __tablename__ = "study_sessions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    subject_id = Column(String, ForeignKey("subjects.id"))
    topic_id = Column(String, ForeignKey("topics.id"), nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    duration_minutes = Column(Integer)
    focus_level = Column(Integer)  # 1-5 scale
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="study_sessions")
    subject = relationship("Subject")
    topic = relationship("Topic")


class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    test_name = Column(String)
    subject_id = Column(String, ForeignKey("subjects.id"))
    total_marks = Column(Integer)
    obtained_marks = Column(Integer)
    percentage = Column(Float)
    time_taken = Column(Integer)  # in minutes
    completed_at = Column(DateTime, default=datetime.utcnow)
    answers = Column(JSON)  # Store user answers
    review_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="test_results")
    subject = relationship("Subject")
    test_questions = relationship("TestQuestion", back_populates="test_result")


class TestQuestion(Base):
    __tablename__ = "test_questions"
    
    id = Column(String, primary_key=True)
    test_result_id = Column(String, ForeignKey("test_results.id"))
    question_id = Column(String, ForeignKey("questions.id"))
    user_answer = Column(Text)
    is_correct = Column(Boolean)
    time_spent = Column(Integer)  # in seconds
    confidence_level = Column(Integer)  # 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    test_result = relationship("TestResult", back_populates="test_questions")
    question = relationship("Question", back_populates="test_questions")


# New ML-enhanced models

class UserProgress(Base):
    __tablename__ = "user_progress"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    subject_id = Column(String, ForeignKey("subjects.id"))
    date = Column(DateTime, default=datetime.utcnow)
    completion_percentage = Column(Float)  # 0-100
    study_hours = Column(Float)
    topics_covered = Column(Integer)
    practice_tests_taken = Column(Integer)
    average_score = Column(Float)
    streak_days = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_progress")
    subject = relationship("Subject")


class TopicPerformance(Base):
    __tablename__ = "topic_performance"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    topic_id = Column(String, ForeignKey("topics.id"))
    accuracy = Column(Float)  # 0-100
    attempts = Column(Integer)
    average_time = Column(Float)  # in minutes
    last_practiced = Column(DateTime)
    confidence_level = Column(Integer)  # 1-5 scale
    weak_areas = Column(JSON, default=[])  # Store as JSON array
    improvement_suggestions = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="topic_performance")
    topic = relationship("Topic", back_populates="topic_performance")


class ModelPrediction(Base):
    __tablename__ = "model_predictions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    model_type = Column(String)  # progress_forecast, topic_recommendation, focus_area, etc.
    input_data = Column(JSON)
    prediction_result = Column(JSON)
    confidence_score = Column(Float)  # 0-1
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # For caching purposes
    
    # Relationships
    user = relationship("User", back_populates="model_predictions")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    preference_type = Column(String)  # study_time, difficulty_level, question_type, etc.
    preference_value = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_preferences")


class QuestionRating(Base):
    __tablename__ = "question_ratings"
    
    id = Column(String, primary_key=True)
    question_id = Column(String, ForeignKey("questions.id"))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Can be anonymous
    difficulty_rating = Column(Integer)  # 1-5 scale
    quality_rating = Column(Integer)  # 1-5 scale
    usefulness_rating = Column(Integer)  # 1-5 scale
    tags = Column(JSON, default=[])
    feedback = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    question = relationship("Question")
    user = relationship("User")


# Utility functions for database operations
def create_tables(engine):
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def drop_tables(engine):
    """Drop all tables from the database."""
    Base.metadata.drop_all(bind=engine)


def get_db_session():
    """Get database session - this should be implemented based on your database setup."""
    # This is a placeholder - implement based on your actual database configuration
    pass