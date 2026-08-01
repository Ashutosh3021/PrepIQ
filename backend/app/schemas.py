from pydantic import BaseModel, ConfigDict, EmailStr, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
import uuid as uuid_module

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
    exam_name: Optional[str] = None
    days_until_exam: Optional[int] = None
    focus_subjects: Optional[List[str]] = None
    study_hours_per_day: Optional[int] = None
    target_score: Optional[int] = None
    preparation_level: Optional[str] = None
    wizard_completed: Optional[bool] = None
    exam_type: Optional[str] = None
    university_name: Optional[str] = None

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v

class WizardStepResponse(BaseModel):
    """Response for wizard steps - doesn't require created_at"""
    id: str
    email: str
    full_name: Optional[str] = None
    access_token: Optional[str] = None
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v

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
    exam_type: Optional[str] = None
    exam_name: Optional[str] = None
    university_name: Optional[str] = None

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
    exam_type: Optional[str] = None
    exam_name: Optional[str] = None
    university_name: Optional[str] = None

class SubjectResponse(SubjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    papers_uploaded: Optional[int] = 0
    predictions_generated: Optional[int] = 0
    created_at: Optional[datetime] = None
    
    @field_validator('id', 'user_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v

# Paper Schemas
class PaperUploadResponse(BaseModel):
    paper_id: str
    status: str
    message: str
    estimated_time: str
    questions_count: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = None
    images_extracted: Optional[int] = 0
    
    @field_validator('paper_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v

class PaperResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    file_name: str
    exam_year: Optional[int] = None
    total_marks: Optional[int] = None
    duration_minutes: Optional[int] = None
    processing_status: str = "pending"
    questions_extracted: Optional[int] = 0
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v

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
    
    @field_validator('prediction_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v

class PredictedQuestion(BaseModel):
    question_number: int
    text: str
    marks: int
    unit: str
    probability: str
    reasoning: str

class PredictionResponse(BaseModel):
    """Used by GET /predictions/{id} and GET /predictions/{subject_id}/latest."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject_id: str
    predicted_questions: List[PredictedQuestion]
    total_marks: int
    coverage_percentage: int
    unit_coverage: Dict[str, int]
    generated_at: Optional[datetime] = None
    fallback_used: bool = False
    message: Optional[str] = None

    @field_validator('id', 'subject_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v

class PredictionUpdate(BaseModel):
    notes: Optional[str] = None
    feedback: Optional[str] = None


class PredictedQuestionFull(BaseModel):
    """Richer question shape returned by the two-tier prediction system."""
    question_number: int = 0
    text: str = ""
    topic: Optional[str] = None
    unit: Optional[str] = None
    marks: int = 5
    probability: str = "moderate"
    confidence_score: float = 0.0
    reasoning: str = ""
    source: Optional[str] = None


class SubjectPredictionResponse(BaseModel):
    """Response shape for GET /predictions/subject/{subject_id}."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    subject_id: str
    predictions: List[PredictedQuestionFull] = []
    total_marks: int = 0
    coverage_percentage: int = 0
    unit_coverage: Dict[str, int] = {}
    generated_at: Optional[datetime] = None

    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    warning: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None

    @field_validator("id", "subject_id", mode="before")
    @classmethod
    def _coerce_uuid(cls, v):
        import uuid as _uuid
        if isinstance(v, _uuid.UUID):
            return str(v)
        return v

# Chat Schemas
class ChatRequest(BaseModel):
    subject_id: str
    message: str
    context: Optional[Dict[str, Any]] = None


class TutorChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, Any]]] = []
    subject_id: Optional[str] = None
    
    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        if len(v) > 5000:
            raise ValueError('Message cannot exceed 5000 characters')
        return v.strip()
    
    @field_validator('conversation_history')
    @classmethod
    def validate_conversation_history(cls, v):
        if v is not None and len(v) > 50:
            raise ValueError('Conversation history cannot exceed 50 messages')
        return v

class ChatResponse(BaseModel):
    message_id: str
    response: str
    related_questions: List[Dict[str, Any]]
    references: List[Dict[str, Any]]
    suggested_actions: List[str]
    
    @field_validator('message_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v

class ChatHistoryResponse(BaseModel):
    id: str
    timestamp: datetime
    user_message: str
    bot_response: str
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v

# Test Schemas
class MockTestRequest(BaseModel):
    subject_id: str
    num_questions: int = 10
    difficulty: str = "mixed"
    source: str = "predictions"
    time_limit_minutes: int = 90
    question_source: Optional[str] = None

    @field_validator("num_questions")
    @classmethod
    def _cap_questions(cls, v: int) -> int:
        if v < 1:
            raise ValueError("num_questions must be at least 1")
        return min(v, 30)

    @field_validator("difficulty")
    @classmethod
    def _validate_difficulty(cls, v: str) -> str:
        allowed = {"easy", "medium", "hard", "mixed"}
        if v.lower() not in allowed:
            raise ValueError(f"difficulty must be one of {allowed}")
        return v.lower()

    @field_validator("source")
    @classmethod
    def _validate_source(cls, v: str) -> str:
        allowed = {"predictions", "all_questions"}
        if v.lower() not in allowed:
            raise ValueError(f"source must be one of {allowed}")
        return v.lower()


class MockTestQuestion(BaseModel):
    id: str
    question_number: int
    question_text: str
    topic: str
    difficulty: str
    marks: int
    correct_answer: Optional[str] = None
    options: Optional[List[str]] = None
    number: Optional[int] = None
    text: Optional[str] = None
    unit: Optional[str] = None
    type: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_uuid(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v


class MockTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    test_id: str
    subject_id: str
    status: str
    total_questions: int
    total_marks: int
    time_limit_minutes: int
    created_at: Optional[datetime] = None
    score_percentage: Optional[float] = None
    questions: List[MockTestQuestion] = []
    error: Optional[str] = None
    message: Optional[str] = None

    @field_validator("test_id", "subject_id", mode="before")
    @classmethod
    def _coerce_uuid(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v


class MockTestListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    test_id: str
    subject_id: str
    status: str
    total_questions: int
    total_marks: int
    score_percentage: Optional[float] = None
    created_at: Optional[datetime] = None

    @field_validator("test_id", "subject_id", mode="before")
    @classmethod
    def _coerce_uuid(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v


class TestSubmission(BaseModel):
    answers: List[Dict[str, str]]


class TestSubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    test_id: str
    score_percentage: Optional[float] = None
    total_questions: int
    answers_graded: int

    @field_validator("test_id", mode="before")
    @classmethod
    def _coerce_uuid(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v


MockTestCreate = MockTestRequest
TestSubmitRequest = TestSubmission
TestSubmitResponse = TestSubmissionResponse


class QuestionAnalysis(BaseModel):
    question_id: str
    marks: int
    status: str
    user_answer: str
    correct_answer: str
    explanation: str

    @field_validator("question_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v


class TestResultsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    test_id: str
    score: int
    percentage: Optional[float] = None  # null when not gradeable
    question_analysis: List[QuestionAnalysis]
    weak_topics: List[str]
    strong_topics: List[str]
    recommendations: List[str]

    @field_validator("test_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v


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
    model_config = ConfigDict(from_attributes=True)

    plan_id: str
    subject_id: str
    total_days: int
    daily_schedule: List[StudyPlanDay]

    @field_validator('plan_id', 'subject_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v

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

    @field_validator('paper_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v


class ImportantQuestion(BaseModel):
    id: str
    subject: str
    topic: str
    question: str
    difficulty: str
    importance: str
    last_asked: str
    
    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v


class Question(BaseModel):
    id: str
    text: str
    marks: int
    difficulty: str
    subject_id: str
    topic: str
    created_at: Optional[datetime] = None
    
    @field_validator('id', 'subject_id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid_module.UUID):
            return str(v)
        return v


GOVERNMENT_EXAMS_V1 = frozenset({"NEET", "JEE"})


class WizardStep1(BaseModel):
    """Step 1: track selection + exam timing.

    exam_type:
      government → exam_name must be NEET or JEE (v1)
      university  → exam_name free text + optional university_name
    """
    exam_type: Literal["government", "university"]
    exam_name: str
    days_until_exam: int
    university_name: Optional[str] = None

    @field_validator("exam_name")
    @classmethod
    def validate_exam_name(cls, v: str) -> str:
        if not v or len(v.strip()) < 2:
            raise ValueError("Exam name must be at least 2 characters long")
        return v.strip()

    @field_validator("days_until_exam")
    @classmethod
    def validate_days_until_exam(cls, v: int) -> int:
        if v < 1 or v > 365:
            raise ValueError("Days until exam must be between 1 and 365")
        return v

    @model_validator(mode="after")
    def validate_track_rules(self):
        et = self.exam_type
        name = self.exam_name.strip()
        if et == "government":
            upper = name.upper()
            if upper not in GOVERNMENT_EXAMS_V1:
                raise ValueError(
                    f"Government track v1 only supports NEET or JEE "
                    f"(got {name!r}). Other exams are not supported yet."
                )
            self.exam_name = upper
            self.university_name = None
        else:
            # university — free text exam_name; university_name optional but recommended
            if self.university_name is not None:
                self.university_name = self.university_name.strip() or None
        return self


class WizardStep2(BaseModel):
    focus_subjects: List[str]
    study_hours_per_day: int
    
    @field_validator('focus_subjects')
    @classmethod
    def validate_focus_subjects(cls, v):
        if not v or len(v) == 0:
            raise ValueError('You must select at least one subject')
        if len(v) > 10:
            raise ValueError('You can select up to 10 subjects')
        return v
    
    @field_validator('study_hours_per_day')
    @classmethod
    def validate_study_hours(cls, v):
        if v < 1 or v > 24:
            raise ValueError('Study hours per day must be between 1 and 24')
        return v


class WizardStep3(BaseModel):
    target_score: int
    preparation_level: str
    
    @field_validator('target_score')
    @classmethod
    def validate_target_score(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Target score must be between 1 and 100')
        return v
    
    @field_validator('preparation_level')
    @classmethod
    def validate_preparation_level(cls, v):
        valid_levels = ['beginner', 'intermediate', 'advanced']
        if v not in valid_levels:
            raise ValueError('Preparation level must be beginner, intermediate, or advanced')
        return v


class WizardCompletion(BaseModel):
    wizard_completed: bool = True
