from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    college_name: Optional[str] = None
    program: Optional[str] = None
    year_of_study: Optional[int] = None
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        if not v or '@' not in v or '.' not in v:
            raise ValueError('Invalid email format')
        return v.lower()

class UserCreate(UserBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    college_name: Optional[str] = None
    program: Optional[str] = None
    year_of_study: Optional[int] = None
    exam_date: Optional[str] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


class RefreshToken(BaseModel):
    refresh_token: str

# Subject Schemas
class SubjectBase(BaseModel):
    name: str
    code: Optional[str] = None
    semester: Optional[int] = None
    academic_year: Optional[str] = None
    total_marks: Optional[int] = None
    exam_date: Optional[str] = None
    exam_duration_minutes: Optional[int] = None
    syllabus_json: Optional[Dict[str, Any]] = None

class SubjectCreate(SubjectBase):
    name: str
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Subject name must be at least 2 characters long')
        return v.strip()

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    semester: Optional[int] = None
    academic_year: Optional[str] = None
    total_marks: Optional[int] = None
    exam_date: Optional[str] = None
    exam_duration_minutes: Optional[int] = None
    syllabus_json: Optional[Dict[str, Any]] = None

class SubjectResponse(SubjectBase):
    id: str
    user_id: str
    papers_uploaded: Optional[int] = 0
    predictions_generated: Optional[int] = 0
    created_at: datetime
    
    class Config:
        from_attributes = True

# Paper Schemas
class PaperUploadResponse(BaseModel):
    paper_id: str
    status: str
    message: str
    estimated_time: str
    questions_count: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = None
    images_extracted: Optional[int] = 0

class PaperResponse(BaseModel):
    id: str
    file_name: str
    exam_year: Optional[int] = None
    total_marks: Optional[int] = None
    duration_minutes: Optional[int] = None
    processing_status: str
    questions_extracted: Optional[int] = 0
    processed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaperPreviewResponse(BaseModel):
    file_name: str
    text_preview: str
    questions_extracted: List[Dict[str, Any]]

# Prediction Schemas
class PredictionRequest(BaseModel):
    subject_id: str
    use_all_papers: bool = True
    force_regenerate: bool = False

class PredictionGenerationResponse(BaseModel):
    prediction_id: str
    status: str
    message: str
    progress: int

class PredictedQuestion(BaseModel):
    question_number: int
    text: str
    marks: int
    unit: str
    probability: str
    reasoning: str

class PredictionResponse(BaseModel):
    id: str
    subject_id: str
    predicted_questions: List[PredictedQuestion]
    total_marks: int
    coverage_percentage: int
    unit_coverage: Dict[str, int]
    generated_at: datetime

class PredictionUpdate(BaseModel):
    notes: Optional[str] = None
    feedback: Optional[str] = None

# Chat Schemas
class ChatRequest(BaseModel):
    subject_id: str
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    message_id: str
    response: str
    related_questions: List[Dict[str, Any]]
    references: List[Dict[str, Any]]
    suggested_actions: List[str]

class ChatHistoryResponse(BaseModel):
    id: str
    timestamp: datetime
    user_message: str
    bot_response: str

# Test Schemas
class MockTestRequest(BaseModel):
    subject_id: str
    num_questions: int = 25
    difficulty: str = "medium"
    time_limit_minutes: int = 90
    question_source: str = "mixed"

class MockTestQuestion(BaseModel):
    id: str
    number: int
    text: str
    marks: int
    unit: str
    options: Optional[List[str]] = None
    type: str

class MockTestResponse(BaseModel):
    test_id: str
    total_questions: int
    total_marks: int
    time_limit_minutes: int
    start_time: datetime
    questions: List[MockTestQuestion]

class TestSubmission(BaseModel):
    answers: Dict[str, str]
    end_time: datetime

class TestSubmissionResponse(BaseModel):
    test_id: str
    score: int
    total_marks: int
    percentage: float
    duration_minutes: int
    results: Dict[str, int]

class QuestionAnalysis(BaseModel):
    question_id: str
    marks: int
    status: str
    user_answer: str
    correct_answer: str
    explanation: str

class TestResultsResponse(BaseModel):
    test_id: str
    score: int
    percentage: float
    question_analysis: List[QuestionAnalysis]
    weak_topics: List[str]
    strong_topics: List[str]
    recommendations: List[str]


# Study Plan Schemas
class StudyPlanRequest(BaseModel):
    subject_id: str
    start_date: str
    exam_date: str
    
    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v):
        from datetime import datetime
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('Start date must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)')
        return v
    
    @field_validator('exam_date')
    @classmethod
    def validate_exam_date(cls, v):
        from datetime import datetime
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('Exam date must be in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)')
        return v

class StudyPlanDay(BaseModel):
    day: int
    date: str
    topics: List[str]
    recommended_hours: float
    priority_topics: List[str]

class StudyPlanResponse(BaseModel):
    plan_id: str
    subject_id: str
    total_days: int
    daily_schedule: List[StudyPlanDay]

class StudyPlanUpdate(BaseModel):
    days_completed: Optional[int] = None
    on_track: Optional[bool] = None

class StudyPlanUpdateResponse(BaseModel):
    message: str
    plan: StudyPlanResponse


class UploadProgressResponse(BaseModel):
    paper_id: str
    status: str
    progress: int
    message: str