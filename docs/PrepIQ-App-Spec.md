# 🎯 PrepIQ - Complete Enhanced App Specification

**Version:** 1.0  
**Last Updated:** January 5, 2026  
**Status:** Production Ready Specification  
**Target Timeline:** 4 weeks MVP

---

## TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [Core Vision & Mission](#2-core-vision--mission)
3. [Technical Architecture](#3-technical-architecture)
4. [Database Design](#4-database-design)
5. [Frontend UI/UX Specification](#5-frontend-uiux-specification)
6. [Backend API Documentation](#6-backend-api-documentation)
7. [AI/ML Capabilities](#7-aiml-capabilities)
8. [Feature Deep-Dives](#8-feature-deep-dives)
9. [Security & Performance](#9-security--performance)
10. [Testing Strategy](#10-testing-strategy)
11. [Deployment Guide](#11-deployment-guide)
12. [Post-Launch Roadmap](#12-post-launch-roadmap)

---

## 1. PROJECT OVERVIEW

### 1.1 Executive Summary

**PrepIQ** is an AI-powered exam preparation platform that transforms how college students prepare for exams by analyzing historical question patterns and predicting high-probability questions with remarkable accuracy.

Instead of students wasting time on low-probability topics, PrepIQ uses machine learning to:
- Analyze previous year question papers (PYQs)
- Identify recurring patterns and topics
- Generate predicted question papers matching exact university formats
- Provide personalized AI study guidance
- Generate adaptive mock tests

### 1.2 Problem Statement

**Current Student Reality:**
- 📚 Students study 100% of syllabus but 60% never appears in exams
- ⏰ Inefficient time management due to lack of strategic focus
- 😰 Exam anxiety from not knowing what to expect
- 🎲 Guessing which topics/chapters are important
- 🔄 Repeating same mistakes across mock tests without targeted improvement
- 💻 No personalized guidance on weak areas
- 📊 No visibility into question paper patterns

**Market Gap:**
- Current solutions are generic (no university customization)
- Expensive paid coaching doesn't guarantee strategic preparation
- Online platforms lack AI-driven predictions
- No unified platform combining predictions + study guidance + mock tests

### 1.3 Solution Overview

**PrepIQ delivers:**
1. **Smart Predictions** - AI analyzes 5+ years of PYQs to predict questions with 80%+ accuracy
2. **Pattern Intelligence** - Visual trends showing which topics repeat, unit weightage, difficulty patterns
3. **Personalized Guidance** - AI chatbot creates custom study plans and explains concepts in context
4. **Adaptive Testing** - Mock tests that match predicted patterns and difficulty
5. **Performance Analytics** - Track improvement across multiple attempts

### 1.4 Target Users

| User Type | Needs | Pain Points |
|-----------|-------|-------------|
| **First-Year Students** | Understand exam patterns early | Don't know what to expect |
| **Struggling Students** | Focused preparation on high-yield topics | Wasting time on unimportant chapters |
| **High-Achievers** | Optimize time to score even higher | Need advanced problem sets |
| **Exam Repeaters** | Strategic improvement in weak areas | Don't know what went wrong |
| **Working Professionals** | Limited time, maximum ROI | Can't afford to study everything |

### 1.5 Success Metrics

**Engagement Metrics:**
- Daily Active Users (DAU)
- Papers uploaded per user (target: 3+ per subject)
- Predictions generated (target: 2+ per exam)
- Mock tests taken (target: 5+ per exam)
- Chat interactions (target: 10+ per student)

**Accuracy Metrics:**
- Prediction accuracy (% of predicted questions in actual exams)
- Coverage percentage (% of syllabus covered by predictions)
- User satisfaction (NPS score > 50)

**Impact Metrics:**
- Correlation with improved exam scores
- CGPA improvement reported by users
- Retention rate (users returning for next semester)
- Referral rate (word-of-mouth growth)

---

## 2. CORE VISION & MISSION

### 2.1 Vision Statement

> **"Democratize strategic exam preparation for every college student in India by leveraging AI to predict question papers, eliminate guesswork, and enable smart studying."**

### 2.2 Mission Statement

> **"Build an AI-powered platform that analyzes historical exam patterns to predict questions, guide personalized study strategies, and help students achieve their academic potential."**

### 2.3 Core Values

1. **Student-First** - Every feature designed for student benefit, not profit
2. **Accuracy** - Predictions backed by data, not guesses
3. **Accessibility** - 100% free tier, no paywalls for core features
4. **Privacy** - User data is sacred, never sold or misused
5. **Innovation** - Constantly improve AI predictions and features
6. **Transparency** - Users see exactly how predictions are calculated

### 2.4 Key Differentiators

| Feature | PrepIQ | Competitors |
|---------|--------|-------------|
| **AI Predictions** | Customized per college/university | Generic across all colleges |
| **Mock Tests** | Adaptive based on predictions | Static question banks |
| **Chatbot** | Context-aware from uploaded papers | Generic Q&A bot |
| **Cost** | 100% free tier forever | Freemium with paywall |
| **Trend Analysis** | Visual heatmaps, detailed insights | Basic statistics |
| **Personalization** | AI study plans + recommendations | One-size-fits-all approach |

---

## 3. TECHNICAL ARCHITECTURE

### 3.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  React 18 PWA (Vite)   │  Offline Support  │  Mobile-First  │
└────────────┬────────────────────────────────────────────────┘
             │ HTTPS
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                         │
├─────────────────────────────────────────────────────────────┤
│  FastAPI + Uvicorn  │  Rate Limiting  │  CORS  │  Auth JWT  │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┴────────┬─────────────┬──────────────┐
    ▼                 ▼             ▼              ▼
┌─────────┐      ┌──────────┐  ┌────────┐   ┌──────────┐
│ PDF     │      │ Pattern  │  │ Gemini │   │Database  │
│ Parser  │      │ Analysis │  │ API    │   │ Layer    │
└─────────┘      │ Engine   │  └────────┘   │(Supabase)│
                 └──────────┘              └──────────┘
                      │
    ┌─────────────────┼─────────────────┐
    ▼                 ▼                 ▼
┌─────────┐      ┌──────────┐      ┌──────────┐
│Frequency│      │Unit-wise │      │Question  │
│Analysis │      │Weightage │      │Rotation  │
└─────────┘      │Patterns  │      │Detection │
                 └──────────┘      └──────────┘
```

### 3.2 Frontend Stack

**Core Framework:**
- React 18.2+ (latest hooks API)
- Vite (fast dev server, optimized builds)
- TypeScript (optional but recommended for type safety)

**State Management:**
- React Context API (global: auth, subject selection)
- useState/useReducer (local component state)
- Custom hooks for reusable logic

**HTTP Client:**
- Axios with interceptors for JWT refresh

**UI Components:**
- Custom components (no heavy UI libraries)
- Recharts for data visualizations
- React Router v6 for navigation

**Styling:**
- CSS3 with CSS Variables (design system)
- Mobile-first responsive design
- Dark mode support via data-attributes

**PWA Features:**
- Workbox service workers (offline caching)
- Web manifest (installable)
- Service worker registration

**Build & Deploy:**
- Vite for bundling
- ESLint + Prettier for code quality
- GitHub Actions for CI/CD

### 3.3 Backend Stack

**Web Framework:**
- FastAPI 0.104+ (async Python)
- Uvicorn as ASGI server

**PDF Processing:**
```python
PyPDF2 >= 3.0.1          # Extract text from text PDFs
pdfplumber >= 0.10.3     # Better text extraction
pdf2image >= 1.16.3      # Convert PDF to images
pytesseract >= 0.3.10    # OCR for scanned images
python-magic-bin >= 0.4  # File type detection
```

**NLP & Text Processing:**
```python
spacy >= 3.7.2           # Named entity recognition, tokenization
nltk >= 3.8              # Natural language processing
google-generativeai >= 0.3.1  # Gemini API client
langchain >= 0.1.0       # RAG pipeline, prompt management
```

**Database & Storage:**
```python
supabase >= 2.0.3        # PostgreSQL client, file storage
asyncpg >= 0.29          # Async PostgreSQL driver
sqlalchemy >= 2.0        # ORM (optional, for complex queries)
```

**Authentication:**
```python
python-jose >= 3.3.0     # JWT token handling
passlib >= 1.7.4         # Password hashing
python-multipart >= 0.0.6  # Form file uploads
```

**Data Processing:**
```python
pandas >= 2.0            # Data analysis (optional)
numpy >= 1.24           # Numerical operations
scikit-learn >= 1.3     # ML for pattern detection
```

**Development & Testing:**
```python
pytest >= 7.4           # Testing framework
pytest-asyncio >= 0.21  # Async test support
httpx >= 0.24           # HTTP client for testing
python-dotenv >= 1.0    # Environment variables
```

### 3.4 AI/ML Stack

**Primary LLM:**
- Google Gemini API (free tier: 1,500 requests/day, 1M tokens/min)
  - Model: gemini-pro (text), gemini-pro-vision (images)
  - Context window: 2M tokens (can fit entire semester's papers)

**Pattern Recognition:**
- scikit-learn for clustering and classification
- Custom algorithms for frequency analysis
- TensorFlow Lite for lightweight models

**NLP Libraries:**
- spaCy for tokenization, NER, lemmatization
- NLTK for semantic similarity

**Vector Embeddings:**
- Google's Gemini embedding API (through generativeai library)
- Store in Supabase via pgvector extension

**RAG Pipeline:**
- LangChain for orchestration
- Custom prompt templates
- Context retrieval from uploaded PDFs

### 3.5 Database Stack

**Primary Database:**
- PostgreSQL 14+ via Supabase
- pgvector extension for semantic search
- Full-text search capabilities

**Storage:**
- Supabase Storage (S3-compatible)
- Separate buckets for PDFs, exports, logs

**Caching (Optional):**
- Redis for session management (future scale-up)
- Browser cache for static assets

### 3.6 Deployment & Infrastructure

**Frontend Hosting:**
- Vercel (free tier)
  - Auto-deploy on GitHub push
  - CDN distribution
  - Environment variables via dashboard
  - Preview deployments for PRs

**Backend Hosting:**
- Railway.app (free tier: $5 credit/month)
  - Deploy directly from GitHub
  - Auto-restart on crash
  - Environment secrets management
  - Logs accessible via CLI

**Database:**
- Supabase (free tier: 500MB storage, 1GB bandwidth)
  - Hosted PostgreSQL
  - Automatic backups
  - REST API auto-generated

**File Storage:**
- Supabase Storage (same as database)
- 1GB free tier
- CDN-backed URLs

**Monitoring & Logging:**
- Sentry (free tier) for error tracking
- Vercel Analytics for frontend performance
- Railway logs for backend monitoring

### 3.7 Environment Configuration

**Frontend `.env`:**
```
VITE_API_URL=https://prepiq-backend.railway.app
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=xxxxx
```

**Backend `.env`:**
```
GEMINI_API_KEY=xxxxx
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=xxxxx
JWT_SECRET=xxxxx
DATABASE_URL=postgresql://user:pass@host/db
ALLOWED_ORIGINS=https://prepiq.vercel.app
ENVIRONMENT=production
```

---

## 4. DATABASE DESIGN

### 4.1 Complete Schema

#### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  
  -- Profile
  full_name VARCHAR(255),
  college_name VARCHAR(255),
  program VARCHAR(100), -- BTech, BSc, MSc
  year_of_study INT,
  
  -- Preferences
  theme_preference VARCHAR(20) DEFAULT 'system', -- light/dark/system
  language VARCHAR(10) DEFAULT 'en',
  exam_date DATE,
  
  -- Account
  email_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP, -- Soft delete
  
  -- Indexes
  INDEX idx_email (email),
  INDEX idx_college (college_name)
);
```

#### Subjects Table
```sql
CREATE TABLE subjects (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Subject Info
  name VARCHAR(255) NOT NULL, -- Linear Algebra, Data Structures
  code VARCHAR(50), -- MA201, CS201
  semester INT,
  academic_year VARCHAR(20), -- 2024-2025
  
  -- Exam Details
  total_marks INT,
  exam_date DATE,
  exam_duration_minutes INT,
  
  -- Syllabus
  syllabus_json JSONB, -- { "units": [{ "name": "Unit 1", "topics": [...] }] }
  
  -- Status
  papers_uploaded INT DEFAULT 0,
  predictions_generated INT DEFAULT 0,
  mock_tests_created INT DEFAULT 0,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id, code, academic_year),
  INDEX idx_user_subject (user_id, id)
);
```

#### Question Papers Table
```sql
CREATE TABLE question_papers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  
  -- File Info
  file_name VARCHAR(255),
  file_path VARCHAR(512),
  s3_key VARCHAR(512), -- Supabase Storage path
  file_size_bytes INT,
  
  -- Metadata
  exam_year INT, -- 2024
  exam_semester INT,
  total_marks INT,
  duration_minutes INT,
  
  -- Processing
  raw_text LONGTEXT, -- Full extracted text
  extraction_confidence DECIMAL(3,2), -- 0-1
  extraction_method VARCHAR(50), -- pdfplumber, tesseract
  
  -- Status
  processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
  error_message TEXT,
  processed_at TIMESTAMP,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_subject_year (subject_id, exam_year)
);
```

#### Questions Table
```sql
CREATE TABLE questions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  paper_id UUID NOT NULL REFERENCES question_papers(id) ON DELETE CASCADE,
  
  -- Question Content
  question_text LONGTEXT NOT NULL,
  question_number INT,
  marks INT,
  
  -- Classification
  unit_id VARCHAR(50), -- Unit 1, Unit 2
  unit_name VARCHAR(255),
  topics_json JSONB, -- ["Binary Search", "Complexity Analysis"]
  question_type VARCHAR(50), -- mcq, short_answer, numerical, essay
  difficulty VARCHAR(20), -- easy, medium, hard
  
  -- Metadata
  section_name VARCHAR(100), -- Part A, Part B, Section I
  has_subparts BOOLEAN DEFAULT FALSE,
  subparts_count INT,
  
  -- Analysis
  is_repeated BOOLEAN DEFAULT FALSE,
  similar_question_ids UUID[], -- Array of related questions
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_paper_unit (paper_id, unit_id),
  INDEX idx_topics (topics_json),
  FULLTEXT INDEX idx_text (question_text) -- For text search
);
```

#### Predictions Table
```sql
CREATE TABLE predictions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- Prediction Data
  predicted_questions_json LONGTEXT, -- Large JSON with all predictions
  total_questions INT,
  total_predicted_marks INT,
  
  -- Probability Distribution
  very_high_count INT,
  high_count INT,
  moderate_count INT,
  
  -- Coverage
  unit_coverage_json JSONB, -- { "Unit 1": 45%, "Unit 2": 30% }
  topic_coverage_percentage DECIMAL(5,2),
  
  -- Analysis
  analysis_summary TEXT,
  key_insights_json JSONB,
  
  -- Accuracy Tracking (filled after exam)
  actual_exam_questions_json LONGTEXT,
  accuracy_score DECIMAL(5,2), -- % of predictions that appeared
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_subject_user (subject_id, user_id),
  INDEX idx_created (created_at DESC)
);
```

#### Trend Analysis Table
```sql
CREATE TABLE trend_analysis (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  
  -- Frequency Data
  topic_frequency_json JSONB, -- { "Topic A": 5, "Topic B": 3 }
  unit_frequency_json JSONB,
  
  -- Weightage
  unit_weightage_json JSONB, -- { "Unit 1": { "total_marks": 45, "percentage": 45 } }
  mark_type_distribution_json JSONB, -- { "2": 30, "5": 40, "10": 30 }
  
  -- Patterns
  question_repetition_json JSONB, -- Exact repeated questions
  similar_questions_json JSONB, -- Semantic duplicates
  repetition_cycle_years INT, -- Questions repeat every N years
  
  -- Trends
  difficulty_trend VARCHAR(50), -- increasing, decreasing, stable
  topic_trend_json JSONB, -- Which topics are rising/declining
  
  -- Insights
  must_study_topics_json JSONB,
  never_repeated_topics_json JSONB,
  
  analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_subject (subject_id)
);
```

#### Mock Tests Table
```sql
CREATE TABLE mock_tests (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  
  -- Test Configuration
  total_questions INT,
  total_marks INT,
  duration_minutes INT,
  difficulty_level VARCHAR(50), -- easy, medium, hard
  
  -- Question Selection
  questions_json JSONB, -- Array of question objects with options
  
  -- Test Execution
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  is_completed BOOLEAN DEFAULT FALSE,
  
  -- Results
  user_answers_json JSONB, -- { "q1": "A", "q2": "C" }
  score INT,
  percentage DECIMAL(5,2),
  
  -- Analysis
  correct_count INT,
  incorrect_count INT,
  skipped_count INT,
  
  weak_topics_json JSONB, -- Topics user got wrong
  strong_topics_json JSONB,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_user_subject (user_id, subject_id),
  INDEX idx_completed (is_completed)
);
```

#### Chat History Table
```sql
CREATE TABLE chat_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  
  -- Message Content
  user_message TEXT NOT NULL,
  bot_response LONGTEXT NOT NULL,
  
  -- Context
  message_type VARCHAR(50), -- concept_explanation, question_analysis, study_planning
  relevant_question_ids UUID[], -- Referenced questions
  
  -- Metadata
  response_time_seconds DECIMAL(5,2),
  user_feedback INT, -- -1: unhelpful, 0: neutral, 1: helpful
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_user_subject (user_id, subject_id),
  INDEX idx_created (created_at DESC)
);
```

#### Study Plans Table
```sql
CREATE TABLE study_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  
  -- Plan Details
  plan_name VARCHAR(255),
  start_date DATE,
  exam_date DATE,
  total_days INT,
  
  -- Daily Schedule
  daily_schedule_json JSONB, -- [ { "day": 1, "date": "2025-01-06", "topics": [...], "duration_hours": 2 } ]
  
  -- Progress Tracking
  days_completed INT DEFAULT 0,
  completion_percentage DECIMAL(5,2) DEFAULT 0,
  
  -- Adherence
  on_track BOOLEAN DEFAULT TRUE,
  last_update_date DATE,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_user_subject (user_id, subject_id)
);
```

### 4.2 Indexes for Performance

```sql
-- Fast user lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_college ON users(college_name);

-- Subject queries
CREATE INDEX idx_subjects_user ON subjects(user_id);
CREATE INDEX idx_subjects_exam_date ON subjects(exam_date);

-- Paper processing
CREATE INDEX idx_papers_subject ON question_papers(subject_id);
CREATE INDEX idx_papers_year ON question_papers(exam_year);

-- Question retrieval
CREATE INDEX idx_questions_paper ON questions(paper_id);
CREATE INDEX idx_questions_unit ON questions(unit_id);
CREATE FULLTEXT INDEX idx_questions_text ON questions(question_text);

-- Prediction lookups
CREATE INDEX idx_predictions_subject ON predictions(subject_id);
CREATE INDEX idx_predictions_user ON predictions(user_id);
CREATE INDEX idx_predictions_created ON predictions(created_at DESC);

-- Mock test queries
CREATE INDEX idx_tests_user ON mock_tests(user_id);
CREATE INDEX idx_tests_completed ON mock_tests(is_completed);

-- Chat history
CREATE INDEX idx_chat_user ON chat_history(user_id);
CREATE INDEX idx_chat_subject ON chat_history(subject_id);
```

---

## 5. FRONTEND UI/UX SPECIFICATION

### 5.1 Page Structure & Navigation

#### Navigation Hierarchy
```
PrepIQ (Root)
├─ Auth
│  ├─ Login
│  ├─ Signup
│  └─ Forgot Password
├─ Dashboard
│  ├─ Main Dashboard
│  ├─ Subject Detail
│  └─ Quick Stats
├─ Papers
│  ├─ Upload Papers
│  ├─ Paper List
│  └─ Paper Preview
├─ Predictions
│  ├─ Generate Prediction
│  ├─ Prediction Results
│  └─ Download/Export
├─ Analysis
│  ├─ Trend Dashboard
│  ├─ Topic Heatmap
│  └─ Unit Weightage
├─ Study
│  ├─ AI Chatbot
│  ├─ Study Plans
│  └─ Important Questions
├─ Tests
│  ├─ Create Mock Test
│  ├─ Test Interface
│  ├─ Results Page
│  └─ Performance Analytics
└─ Settings
   ├─ Profile
   ├─ Subjects
   ├─ Notifications
   └─ Privacy
```

### 5.2 Detailed Page Specifications

#### 5.2.1 Login Page
```
Layout: Center-aligned, 400px max-width card

Header:
├─ PrepIQ Logo (120px)
├─ "Study Smart. Score High."
└─ "AI-Powered Exam Preparation"

Form:
├─ Email input
│  ├─ Placeholder: "your.email@college.ac.in"
│  ├─ Icon: envelope
│  └─ Validation: Real-time email format check
│
├─ Password input
│  ├─ Placeholder: "Enter your password"
│  ├─ Icon: lock
│  ├─ Show/hide toggle
│  └─ Validation: Length check
│
├─ "Remember me" checkbox
│
├─ "Forgot password?" link (right-aligned, secondary color)
│
└─ Sign In button (primary, full-width, 48px height)

Divider: "OR"

Social Login:
├─ Google Sign In button (icon + text)
└─ GitHub Sign In button (icon + text)

Footer:
├─ "Don't have an account?"
├─ "Sign up now" link (highlighted)
└─ Terms & Privacy links

Error Handling:
├─ Toast notifications (top-right)
├─ Form field error messages (below input)
└─ Loading state: Button shows spinner
```

#### 5.2.2 Dashboard Page
```
Layout: Sidebar (240px) + Main Content (responsive)

TOP NAVIGATION BAR:
├─ Left:
│  └─ "PrepIQ" logo + hamburger menu (mobile only)
├─ Center:
│  └─ Search bar (search subjects, papers)
└─ Right:
   ├─ User avatar (clickable dropdown)
   ├─ Notification bell (with badge count)
   └─ Settings icon

LEFT SIDEBAR:
├─ Navigation items (with active state highlight):
│  ├─ 📚 My Subjects (current count badge)
│  ├─ 🔮 Predictions
│  ├─ 🤖 Study Buddy (with unread message badge)
│  ├─ 📝 Mock Tests
│  ├─ 🎯 Important Questions
│  ├─ 📈 Trend Analysis
│  └─ ⚙️ Settings
│
└─ Bottom section:
   ├─ Theme toggle (light/dark)
   ├─ Help & Feedback button
   └─ Logout button

MAIN CONTENT AREA:

Welcome Card (if first visit):
├─ Heading: "Welcome back, [Name]!"
├─ Countdown: "Exam in [N] days" (prominent, red if <7 days)
├─ Quick action buttons:
│  ├─ "+ Upload Papers"
│  └─ "Generate Prediction"
└─ Animation: Subtle fade-in

Quick Stats Section:
├─ 4-column grid (stacking on mobile):
│  ├─ Card 1: Subjects (count + "View all" link)
│  ├─ Card 2: Papers uploaded (count + last upload date)
│  ├─ Card 3: Predictions generated (count + accuracy badge)
│  └─ Card 4: Mock tests completed (count + avg score)
└─ Each card has icon, number, label, mini sparkline chart

Subjects Grid:
├─ Title: "My Subjects" + "Add Subject +" button
│
└─ 3-column grid (responsive):
   ├─ Subject Card 1:
   │  ├─ Subject name (large, bold)
   │  ├─ Code: "MA201" (muted text)
   │  ├─ Semester badge
   │  │
   │  ├─ Quick Stats (mini cards):
   │  │  ├─ Papers: N uploaded
   │  │  ├─ Predictions: Generated [date]
   │  │  └─ Exams: In N days (red if <7)
   │  │
   │  ├─ Progress bar: "Predictions readiness: 65%"
   │  │
   │  └─ Action buttons (full-width):
   │     ├─ 📤 Upload Paper
   │     ├─ 🔮 View Prediction
   │     └─ 🎯 Start Mock Test
   │
   ├─ Subject Card 2: [similar]
   └─ Subject Card 3: [similar]

Recent Activity Section:
├─ Title: "Recent Activity"
└─ Timeline:
   ├─ "Jan 5, 8:30 PM - Generated prediction for Linear Algebra"
   ├─ "Jan 5, 7:45 PM - Uploaded 2025 exam paper"
   ├─ "Jan 4, 3:20 PM - Scored 85/100 in mock test"
   └─ "Show more" link

Help Section (collapsible):
├─ Title: "Getting Started?"
├─ Quick tips:
│  ├─ "1. Upload 3-5 previous year papers"
│  ├─ "2. Run prediction to see high-probability questions"
│  └─ "3. Take mock tests to practice"
└─ Video tutorial link
```

#### 5.2.3 Upload Papers Page
```
Layout: Full width with centered content

HEADER SECTION:
├─ Title: "[Subject Name] - Upload Question Papers"
├─ Subtitle: "Upload 3-5 previous year papers for accurate predictions"
└─ Info box: "Supported formats: PDF (max 10MB per file)"

UPLOAD AREA (Main Section):
├─ Large drag-drop zone:
│  ├─ Icon: Document upload icon (animated)
│  ├─ Primary text: "Drag & drop PDF files here"
│  ├─ Secondary text: "or click to select from computer"
│  └─ Supported: "PDF files, 10MB max each"
│
├─ File input (hidden)
│
└─ "Or select multiple files" button (secondary)

UPLOADED FILES LIST (Below):
├─ Title: "Uploaded Papers ([N])"
│
└─ List of files:
   ├─ Each file row:
   │  ├─ File icon + name (truncated)
   │  ├─ File size (small, muted)
   │  ├─ Upload date
   │  ├─ Processing status:
   │  │  ├─ Pending: Spinner + "Processing..."
   │  │  ├─ Completed: Checkmark + "Extracted [N] questions"
   │  │  └─ Failed: Error icon + error message
   │  │
   │  ├─ Progress bar (if processing):
   │  │  └─ Shows: Text extraction → Question parsing → Analysis
   │  │
   │  └─ Actions:
   │     ├─ Preview button (shows text snippet in modal)
   │     ├─ Delete button (trash icon)
   │     └─ Reprocess button (if failed)

STATISTICS SECTION (Right side or below, responsive):
├─ Total papers uploaded: [N]
├─ Total questions extracted: [N]
├─ Questions by marks:
│  ├─ 2-mark: N questions
│  ├─ 5-mark: N questions
│  └─ 10-mark: N questions
└─ Questions by unit:
   ├─ Unit 1: N questions
   ├─ Unit 2: N questions
   └─ [more units...]

ACTION BUTTONS (Bottom):
├─ "Generate Prediction" (primary, full-width)
├─ "View Extracted Questions" (secondary, full-width)
└─ "Back to Subject" (link)
```

#### 5.2.4 Prediction Results Page
```
Layout: Multi-section, scrollable

HEADER SECTION:
├─ Title: "Predicted Question Paper - [Subject]"
├─ Generation info: "Generated [date] • Confidence: 85%"
├─ Summary badge: "Covers 95% of likely topics"
│
└─ Action buttons:
   ├─ Download PDF
   ├─ Download Excel
   ├─ Print
   ├─ Share
   └─ View Analysis

CONFIDENCE INDICATOR (Prominent):
├─ Circular progress ring (80% filled, teal color)
├─ Text: "85% Confidence"
├─ Tooltip: "Based on analysis of 5 previous year papers"
└─ Breakdown:
   ├─ "Very High Probability: 15 questions"
   ├─ "High Probability: 25 questions"
   └─ "Moderate Probability: 10 questions"

RECOMMENDED STRATEGY CARD:
├─ "📋 Study Recommendation"
├─ Priority: "1. Unit 3 (45% weightage) - FOCUS HERE"
├─ Secondary: "2. Unit 2 (30% weightage) - Important"
├─ Tertiary: "3. Unit 1 (25% weightage) - Standard"
│
└─ Time allocation:
   ├─ "10 days till exam?"
   ├─ "Day 1-5: Deep dive into Unit 3"
   ├─ "Day 6-8: Unit 2 concepts + practice"
   └─ "Day 9-10: Revision + full mock tests"

PREDICTED QUESTIONS BY SECTION:

SECTION 1: Part A (2-Mark Questions) - Total: 30 marks
├─ Section info: "10 × 2-mark questions"
├─ Probability breakdown: "Very High: 6, High: 3, Moderate: 1"
│
└─ Expandable question cards (initial: collapsed, show number + unit):
   ├─ Q1 [Very High Probability] 🔴
   │  └─ Click to expand:
   │     ├─ Question text
   │     ├─ Unit: "Data Structures"
   │     ├─ Topic: "Linked Lists"
   │     ├─ Appeared in: 2020, 2022, 2024 (4 times)
   │     ├─ Difficulty: Easy
   │     ├─ Expected answer: [snippet]
   │     └─ "Add to revision" button
   │
   ├─ Q2 [High Probability] 🟠
   └─ Q3 [Moderate Probability] 🟡

SECTION 2: Part B (5-Mark Questions) - Total: 40 marks
├─ [Similar structure to Part A]
└─ Questions Q4-Q12 (expandable)

SECTION 3: Part C (10-Mark Questions) - Total: 30 marks
├─ [Similar structure]
└─ Questions Q13-Q15 (expandable)

TOPIC HEATMAP VISUALIZATION:
├─ Title: "Topic Probability Heatmap"
├─ X-axis: Units (Unit 1, 2, 3, 4)
├─ Y-axis: Probability level (Very High, High, Moderate)
├─ Cells: Color-coded by probability (intensity)
├─ Tooltip: Shows question count + percentage
└─ Interactive: Click to filter predictions

STUDY PRIORITY MATRIX:
├─ 2D plot:
│  ├─ X-axis: "Frequency (how often appears)"
│  ├─ Y-axis: "Importance (marks weightage)"
│  │
│  └─ Quadrants:
│     ├─ Top-right (Must Study): "Unit 3, Data Structures"
│     ├─ Top-left (Important): "Unit 2, Algorithms"
│     ├─ Bottom-right (Regular): "Unit 1, Basics"
│     └─ Bottom-left (Optional): "Advanced Topics"

NEXT STEPS SECTION:
├─ "What to do next?"
├─ Option 1: "Take a mock test" → Button "Start Mock Test"
├─ Option 2: "Chat with AI" → Button "Ask Study Buddy"
├─ Option 3: "View detailed analysis" → Button "Trend Report"
└─ Option 4: "Download full report" → Button "Export PDF"

EXPORT/DOWNLOAD OPTIONS (Bottom):
├─ Download as PDF (full paper with solutions)
├─ Download as Excel (structured data)
├─ Share via link (generate shareable URL)
└─ Print (optimized for paper)
```

#### 5.2.5 Trend Analysis Dashboard
```
Layout: Full-width with multiple charts

SUMMARY CARDS (Top, 4-column grid):
├─ Card 1: "Most Frequent Unit"
│  ├─ Value: "Unit 3"
│  ├─ Metric: "45% of papers"
│  └─ Icon: 📊
│
├─ Card 2: "Question Repetition Rate"
│  ├─ Value: "25%"
│  ├─ Metric: "Questions repeat"
│  └─ Icon: 🔄
│
├─ Card 3: "Average Marks per Unit"
│  ├─ Value: "36"
│  ├─ Metric: "marks expected"
│  └─ Icon: 📐
│
└─ Card 4: "Coverage Pattern"
   ├─ Value: "95%"
   ├─ Metric: "syllabus covered"
   └─ Icon: ✅

FILTERS (Below summary):
├─ Year filter: "2020 | 2021 | 2022 | 2023 | 2024 | All"
├─ Unit filter: Dropdown with checkboxes
├─ Mark type filter: "2-mark | 5-mark | 10-mark | All"
└─ Apply button

CHART 1: TOPIC FREQUENCY HEATMAP
├─ Title: "Topic Frequency Over Years"
├─ Description: "How many times each topic appeared"
├─ Visualization:
│  ├─ Y-axis: Units (Unit 1 to Unit 4)
│  ├─ X-axis: Years (2020, 2021, 2022, 2023, 2024)
│  ├─ Cells: Color intensity represents frequency
│  │  ├─ Dark Teal: 4-5 appearances
│  │  ├─ Teal: 3 appearances
│  │  ├─ Light Teal: 2 appearances
│  │  └─ Very Light: 1 appearance
│  │
│  └─ Interactive:
│     ├─ Hover: Shows exact count + percentage
│     ├─ Click: Drills down to specific questions
│     └─ Export: Save as image
│
└─ Insight: "Unit 3 appears consistently every year - Must prioritize"

CHART 2: UNIT-WISE WEIGHTAGE (Pie/Donut)
├─ Title: "Total Marks Distribution by Unit"
├─ Chart:
│  ├─ Segments: Each unit as a slice
│  ├─ Color: Different color per unit
│  ├─ Labels: Unit name + % + marks
│  └─ Animation: Smooth rotation on load
│
├─ Legend:
│  ├─ Unit 1: 25% (90 marks)
│  ├─ Unit 2: 30% (108 marks)
│  ├─ Unit 3: 45% (162 marks) [highlighted in bright color]
│  └─ Unit 4: [if exists]
│
└─ Interaction:
   ├─ Click slice: Highlights that unit's questions
   └─ Double-click: Drills to unit detail

CHART 3: QUESTION REPETITION TIMELINE
├─ Title: "Exact & Similar Question Repetitions"
├─ Chart: Stacked bar chart
│  ├─ X-axis: Years
│  ├─ Y-axis: # of repeated questions
│  ├─ Bars:
│  │  ├─ Red segment: Exact repeats
│  │  └─ Orange segment: Similar questions (reworded)
│  │
│  └─ Tooltip: Shows exact count + question examples
│
├─ Insight line: "Questions repeat every 2-3 years on average"
└─ Pattern detected: "Questions from 2021 likely to repeat in 2025"

CHART 4: MARKS DISTRIBUTION (Stacked Bar Chart)
├─ Title: "Mark-wise Distribution by Unit"
├─ Chart:
│  ├─ X-axis: Units (Unit 1, 2, 3, 4)
│  ├─ Y-axis: Total marks
│  ├─ Stacked bars (colors for 2-mark, 5-mark, 10-mark)
│  │  ├─ Blue: 2-mark questions
│  │  ├─ Green: 5-mark questions
│  │  └─ Orange: 10-mark questions
│  │
│  └─ Hover: Shows breakdown per mark type
│
└─ Average line: Shows expected distribution (dotted)

INSIGHTS PANEL (Right sidebar or below):
├─ 📌 Key Insight Cards (collapsible):
│  │
│  ├─ Card 1: "High-Focus Units"
│  │  ├─ "Unit 3 appears in 4/5 papers - MUST FOCUS"
│  │  ├─ "Unit 2 appears in 4/5 papers - Important"
│  │  └─ "Recommendation: Allocate 60% study time to Unit 3"
│  │
│  ├─ Card 2: "Question Types Analysis"
│  │  ├─ "2-mark questions: 50% of paper (easiest)"
│  │  ├─ "5-mark questions: 35% (medium difficulty)"
│  │  └─ "10-mark questions: 15% (hardest, few but important)"
│  │
│  ├─ Card 3: "Repeated Questions Alert"
│  │  ├─ "25% of questions are repeated from 2023-2024"
│  │  ├─ "Study these 8 questions - high probability!"
│  │  └─ "Link: View repeated questions"
│  │
│  ├─ Card 4: "Rare Topics"
│  │  ├─ "Topics never repeated: [List 3-4 topics]"
│  │  ├─ "These are low-priority"
│  │  └─ "Estimated probability: <5%"
│  │
│  └─ Card 5: "Predictions Recommendation"
│     ├─ "Based on trends:"
│     ├─ "Very High Probability: Unit 3, Topics A, B, C"
│     ├─ "High Probability: Unit 2, Topics D, E, F"
│     └─ "Create mock test with these topics"

DIFFICULTY TREND SECTION:
├─ Title: "Difficulty Trend Analysis"
├─ Question: "Are questions getting harder or easier?"
├─ Chart: Line chart showing avg difficulty over years
│  ├─ Y-axis: Average difficulty (1-10 scale)
│  ├─ Trend arrow: ↗️ Increasing, ↘️ Decreasing, ➡️ Stable
│  └─ Insight: "Questions are getting 15% harder - prepare well!"
│
└─ Implication: "2024 exam likely to be harder than 2023"

EXPORT & SHARE OPTIONS:
├─ Download full analysis as PDF
├─ Download data as Excel
├─ Generate shareable dashboard link
└─ Print optimized version

ACTION BUTTONS (Bottom):
├─ "Create Prediction" (if not yet done)
├─ "View Predicted Questions"
├─ "Take Mock Test"
└─ "Study Plan"
```

#### 5.2.6 AI Chatbot Interface
```
Layout: Full-height chat interface with sidebar

HEADER SECTION:
├─ Left:
│  ├─ "🤖 Study Buddy"
│  ├─ Subject: "[Linear Algebra]" (dropdown)
│  └─ Status: "Online • Ready to help"
│
└─ Right:
   ├─ Clear chat button (trash icon, tooltip: "Clear history")
   ├─ Info button (shows chatbot capabilities)
   └─ Close/minimize button (mobile)

CHAT AREA (Main, scrollable):
├─ System message: "Study Buddy initialized for [Subject]"
├─ Greeting: "Hi [Name]! 👋 Ready to study smarter?"
├─ Suggestion cards:
│  ├─ "📚 Explain a concept"
│  ├─ "📊 Analyze my weakness"
│  ├─ "🗓️ Create study plan"
│  └─ "❓ Question analysis"
│
└─ Conversation threads:
   ├─ User message (right-aligned, teal background):
   │  └─ "Explain Binary Search Tree in simple terms"
   │
   ├─ Bot response (left-aligned, light gray background):
   │  ├─ Message text with formatting
   │  ├─ Examples from uploaded papers (quoted):
   │  │  ├─ 📄 "Question from 2023 paper:"
   │  │  ├─ Full question text
   │  │  └─ "Appeared 3 times in past 5 years"
   │  │
   │  ├─ Links to relevant content:
   │  │  ├─ "🎯 High-probability question on this topic"
   │  │  └─ "📝 Add to revision list"
   │  │
   │  └─ Quick reactions: 👍 👎 (helpful/not helpful)
   │
   ├─ User message: "Is this important for the exam?"
   │
   ├─ Bot response:
   │  ├─ "Yes! This topic has high priority because:"
   │  ├─ "Frequency: Appeared 4/5 years"
   │  ├─ "Weightage: 10-15 marks in typical papers"
   │  ├─ "Difficulty: Medium (good for scoring)"
   │  └─ "🎯 Add to must-study list"
   │
   └─ [More conversation threads...]

SIDEBAR - QUICK ACTIONS (Left, collapsible):
├─ Title: "Quick Actions"
│
├─ 📋 "Create Study Plan"
│  └─ Click → Opens study plan generator
│
├─ 📊 "Analyze My Performance"
│  └─ Click → Shows weak areas from mock tests
│
├─ 🎯 "View Weak Topics"
│  └─ Click → Lists topics from failed mock questions
│
├─ 📚 "Revise This Topic"
│  └─ Click → Generates practice questions
│
├─ 🔄 "Suggest Next Steps"
│  └─ Click → AI recommends what to do next
│
├─ 💾 "Save Conversation"
│  └─ Click → Exports chat as PDF
│
└─ 📌 "Important Messages"
   └─ Shows saved messages with timestamps

SAVED MESSAGES SECTION:
├─ Title: "Saved from Chat"
├─ Messages:
│  ├─ "[Timestamp] - Study plan for 10 days"
│  ├─ "[Timestamp] - Concept explanation: Linked Lists"
│  └─ "View all" link
└─ Export all → PDF download

MESSAGE INPUT AREA (Bottom):
├─ Text input field:
│  ├─ Placeholder: "Ask me anything about [Subject]..."
│  ├─ Multiline (expands as typing)
│  └─ Focus state: Border highlight, focus ring
│
├─ Formatting toolbar (optional):
│  ├─ Bold button
│  ├─ Code block button
│  └─ List button
│
├─ Action buttons (right of input):
│  ├─ Attach image (📎) - Upload question screenshot
│  ├─ Voice input (🎤) - Speech-to-text (optional)
│  └─ Send button (►)
│     └─ Disabled until input has text
│     └─ Shows sending spinner on click
│
└─ Keyboard: Enter to send, Shift+Enter for new line

SUGGESTIONS (Below input):
├─ "Popular questions:"
├─ "How to manage exam time?"
├─ "Solve this numerical"
├─ "Last-minute revision tips"
└─ [More suggestions based on context]

CHATBOT CAPABILITIES (Info modal):
├─ Title: "How can Study Buddy help?"
├─ Capabilities list:
│  ├─ "💡 Concept Explanations"
│  │  └─ "Explain any concept with real exam examples"
│  │
│  ├─ "📋 Question Analysis"
│  │  └─ "Is this important? Will it come in exam?"
│  │
│  ├─ "🗓️ Study Planning"
│  │  └─ "Create personalized day-by-day study schedule"
│  │
│  ├─ "📊 Performance Analysis"
│  │  └─ "Identify weak areas from mock tests"
│  │
│  ├─ "🎯 Exam Strategy"
│  │  └─ "Tips on time management, question selection"
│  │
│  └─ "💬 General Discussion"
│     └─ "Discuss any exam-related topic"
└─ Close button
```

#### 5.2.7 Mock Test Interface
```
BEFORE TEST STARTS:
Layout: Card-based, centered

Configuration Panel:
├─ Title: "Create Mock Test - [Subject]"
│
├─ # of Questions:
│  ├─ Label: "Number of Questions"
│  ├─ Slider: 10-50 (default: 25)
│  └─ Display: "Selected: 25 questions"
│
├─ Difficulty Level:
│  ├─ Easy (30% 2-mark, 40% 5-mark, 30% 10-mark)
│  ├─ Medium (20% 2-mark, 50% 5-mark, 30% 10-mark)
│  ├─ Hard (10% 2-mark, 40% 5-mark, 50% 10-mark)
│  └─ Mixed (30%, 40%, 30%) [default]
│
├─ Time Limit:
│  ├─ Options: 30 min, 60 min, 90 min, Unlimited
│  └─ Display: "90 minutes"
│
├─ Question Source:
│  ├─ ⭐ High-Probability (from predictions)
│  ├─ 📚 Previous Year Papers
│  ├─ 🎯 Weak Areas (topics you scored low in)
│  └─ 🔀 Mixed [default]
│
├─ Info box: "Questions generated based on your predictions and past performance"
│
└─ Action buttons:
   ├─ "Start Mock Test" (primary, large)
   └─ "Cancel" (secondary)

---

DURING TEST:

TOP BAR (Fixed):
├─ Left:
│  ├─ "Mock Test #5 - Linear Algebra"
│  └─ "Question 5 of 25"
│
├─ Center:
│  └─ Timer (large, prominent, color changes):
│     ├─ >5 mins: Green (#22C55E)
│     ├─ 2-5 mins: Orange (#FF6B35)
│     └─ <2 mins: Red (#C01540)
│
└─ Right:
   ├─ "Save & Exit" button (warning before exit)
   └─ "Settings" button (font size, theme)

MAIN TEST AREA:
├─ Question section (65% width on desktop):
│  │
│  ├─ Question header:
│  │  ├─ "Question 5 [5 marks]"
│  │  ├─ Topic badge: "Data Structures"
│  │  └─ Status: "Not answered | Answered | Marked for review"
│  │
│  ├─ Question text (formatted, readable):
│  │  ├─ "Write a function to implement..."
│  │  ├─ Code blocks (if any)
│  │  └─ Diagrams (if any)
│  │
│  ├─ Options (for MCQ):
│  │  ├─ Radio button + Label
│  │  ├─ (A) First option [clickable area]
│  │  ├─ (B) Second option
│  │  ├─ (C) Third option
│  │  └─ (D) Fourth option
│  │
│  ├─ Answer area (for descriptive):
│  │  └─ Large textarea with syntax highlighting
│  │
│  └─ Action buttons:
│     ├─ "Mark for Review" (flag icon)
│     ├─ "Clear Answer" (eraser icon)
│     └─ "[Save answer automatically]" (background, no button)

QUESTION NAVIGATION (35% width on desktop, or below on mobile):
├─ Title: "Question Palette"
├─ Grid of question boxes (5 columns):
│  ├─ Not answered: White box with number
│  ├─ Answered: Blue box with number + checkmark
│  ├─ Marked for review: Orange box with flag + number
│  └─ Current question: Highlighted border
│
├─ Legend:
│  ├─ ⬜ Unanswered
│  ├─ 🟦 Answered
│  ├─ 🟧 Marked for Review
│  └─ ⬛ Current
│
└─ Summary:
   ├─ "Answered: 12 / 25"
   ├─ "Not answered: 8"
   ├─ "Marked: 5"
   └─ "Complete all questions before submitting"

BOTTOM ACTION BUTTONS:
├─ "< Previous" (disabled on Q1)
├─ "Next >" (disabled on last question)
├─ "[Question number indicator: 5/25]"
└─ "Review & Submit" (goes to review page)

---

REVIEW BEFORE SUBMIT:
Layout: Summary with all answers

Review Screen:
├─ Title: "Review Your Answers"
├─ Message: "Check your answers before final submission. You cannot change after submission."
│
└─ List of all questions:
   ├─ Q1 [5 marks] - "Your Answer: C" ✓
   ├─ Q2 [5 marks] - "Not answered" ⚠️ [Edit button]
   ├─ Q3 [5 marks] - "Your Answer: [Text snippet]" ✓
   ├─ [Continue for all questions...]
   │
   └─ Summary: "You have 1 unanswered question. Continue?"

Buttons:
├─ "Go back & answer" (edit mode)
├─ "Confirm & Submit" (final submission)
└─ Confirmation dialog before final submit

---

AFTER TEST - RESULTS PAGE:

Results Card (Top, prominent):
├─ Large score display: "Score: 72 / 100"
├─ Percentage: "72%"
├─ Grade badge: "B+" (based on percentage)
├─ Attempt info: "Attempt #5 • Jan 5, 2025 • 45 mins"
│
├─ Score comparison:
│  ├─ "Your score: 72"
│  ├─ "Class average: 75"
│  ├─ "Your best: 85"
│  └─ "Previous: 68 (↑ +4 points!)" [highlighted in green]
│
└─ Performance vs Predicted:
   ├─ "Predictions Accuracy: 90%"
   ├─ "Of 25 predicted questions, 22 were similar to actual"
   └─ "Recommendation: 95% ready for exam!"

QUESTION-WISE BREAKDOWN:
├─ Title: "Question Analysis"
│
└─ For each question:
   ├─ Q1 [5 marks] ✅ Correct
   │  ├─ "Your answer: C"
   │  ├─ "Correct answer: C"
   │  ├─ Explanation: "[Detailed explanation]"
   │  └─ "Topic: Data Structures • Difficulty: Medium"
   │
   ├─ Q2 [5 marks] ❌ Incorrect
   │  ├─ "Your answer: B"
   │  ├─ "Correct answer: D"
   │  ├─ Explanation: "[Why your answer was wrong, why D is correct]"
   │  ├─ "Concept needed: Queue implementation"
   │  └─ Links: "🎯 Practice this topic | 📚 View in notes"
   │
   └─ Q3 [5 marks] ⏭️ Skipped
      ├─ "You skipped this question"
      ├─ "Correct answer: [Answer]"
      ├─ Explanation: "[Full explanation]"
      └─ "Recommendation: This topic (Recursion) needs practice"

PERFORMANCE ANALYTICS:
├─ Section: "Performance Insights"
│
├─ Accuracy by topic:
│  ├─ Data Structures: 80% (4/5 correct)
│  ├─ Algorithms: 60% (3/5 correct) [Weak - highlighted]
│  ├─ Complexity Analysis: 100% (3/3 correct) [Strong]
│  └─ [Other topics...]
│
├─ Accuracy by question type:
│  ├─ 2-mark questions: 90% (9/10)
│  ├─ 5-mark questions: 70% (7/10)
│  └─ 10-mark questions: 50% (2/4) [Needs improvement]
│
├─ Time analysis:
│  ├─ Average time per question: 1 min 48 sec
│  ├─ Time spent on correct answers: 1 min 30 sec (efficient)
│  ├─ Time spent on incorrect answers: 2 min 45 sec (overthinking?)
│  └─ Recommendation: "Work faster on easy questions"
│
└─ Weak areas identified:
   ├─ 🔴 Algorithms (60% accuracy)
   ├─ 🟠 Recursion (50% accuracy)
   ├─ 🟡 Dynamic Programming (67% accuracy)
   └─ Action: "Take targeted practice on these topics"

STUDY RECOMMENDATIONS:
├─ Title: "What to do next?"
├─ Based on performance:
│  ├─ "1. 🎯 Practice Algorithms"
│  │  └─ Button: "View weak-area questions"
│  │
│  ├─ "2. 💬 Chat with Study Buddy"
│  │  └─ Button: "Ask about Algorithms concepts"
│  │
│  ├─ "3. 📝 Take targeted mock test"
│  │  └─ Button: "Create Algorithms-focused test"
│  │
│  └─ "4. 📊 View trend analysis"
│     └─ Button: "See difficulty distribution"
│
└─ Comparison with prediction:
   ├─ "Predicted accuracy: 90%"
   ├─ "Your actual accuracy: 72%"
   ├─ "Insight: Questions were harder than predicted"
   └─ "Recommendation: Focus more on Algorithms before exam"

HISTORICAL PERFORMANCE (Graph):
├─ Title: "Your Progress"
├─ Line chart:
│  ├─ X-axis: Test attempts (1, 2, 3, 4, 5)
│  ├─ Y-axis: Score (0-100)
│  ├─ Line: 60 → 68 → 65 → 72 [current]
│  └─ Tooltip: Click point to see details
│
├─ Trend: "↗️ Trending upward (+12 points in 5 tests)"
└─ Prediction: "At this rate, you'll score 80+ on exam!"

ACTION BUTTONS (Bottom):
├─ "Take Another Test" (primary)
├─ "Review Solutions" (view detailed explanations)
├─ "Practice Weak Topics" (targeted practice)
├─ "Download Report" (PDF with all details)
├─ "Share Results" (optional, encrypted link)
└─ "Back to Dashboard" (secondary)
```

### 5.3 Design System

#### Color Palette
```
Primary Colors:
- Teal #208091 (main action, highlights)
- Warm Brown #5E5240 (secondary)

Status Colors:
- Success Green #22C55E (correct, positive)
- Warning Orange #FF6B35 (incomplete, caution)
- Error Red #C01540 (incorrect, urgent)
- Info Blue #3B82F6 (information)

Neutral Colors:
- Cream 50 #FFFCF9 (light background, light mode)
- Gray 200 #F5F5F5 (card background)
- Gray 400 #777C7C (text secondary)
- Charcoal 700 #1F2121 (dark background, dark mode)
- Charcoal 900 #134252 (text dark)
```

#### Typography
```
Headlines: Inter 600 • 24px • Line-height 1.2
Body: Inter 400 • 14px • Line-height 1.5
Labels: Inter 500 • 12px
Links: Underline, hover color change
Code: Monospace font, light background
```

#### Spacing System
```
8px base unit
- xs: 4px (tight)
- sm: 8px (standard)
- md: 16px (comfortable)
- lg: 24px (spacious)
- xl: 32px (wide)
```

#### Components
```
Buttons:
- Primary: Teal background, white text
- Secondary: Transparent, teal border
- Disabled: 50% opacity, no hover

Forms:
- Input: Light background, 8px radius
- Labels: Bold, 12px
- Error: Red text, red border

Cards:
- Background: White (light) / Charcoal (dark)
- Border: 1px light gray
- Radius: 8px
- Shadow: Subtle (0 2px 4px)

Modals:
- Overlay: Black 30% opacity
- Card: Centered, max 500px width
- Close: X button top-right
```

---

## 6. BACKEND API DOCUMENTATION

### 6.1 Authentication Endpoints

#### POST /auth/signup
**Request:**
```json
{
  "email": "student@college.ac.in",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "college_name": "GITA Autonomous",
  "program": "BTech",
  "year": 1
}
```

**Response (201 Created):**
```json
{
  "id": "user-uuid",
  "email": "student@college.ac.in",
  "full_name": "John Doe",
  "message": "Account created. Please verify your email.",
  "token": "jwt-token"
}
```

#### POST /auth/login
**Request:**
```json
{
  "email": "student@college.ac.in",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "student@college.ac.in",
  "full_name": "John Doe",
  "token": "jwt-token",
  "refresh_token": "refresh-jwt-token"
}
```

#### POST /auth/logout
**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

#### POST /auth/refresh-token
**Request:**
```json
{
  "refresh_token": "refresh-jwt-token"
}
```

**Response (200 OK):**
```json
{
  "token": "new-jwt-token"
}
```

#### GET /auth/profile
**Response (200 OK):**
```json
{
  "id": "user-uuid",
  "email": "student@college.ac.in",
  "full_name": "John Doe",
  "college_name": "GITA Autonomous",
  "program": "BTech",
  "year": 1,
  "exam_date": "2025-02-15"
}
```

#### PUT /auth/profile
**Request:**
```json
{
  "full_name": "Jane Doe",
  "exam_date": "2025-02-20"
}
```

**Response (200 OK):**
```json
{
  "message": "Profile updated successfully",
  "user": { /* updated profile */ }
}
```

### 6.2 Subject Endpoints

#### GET /subjects
**Query Params:** `?semester=2&year=2024-2025`

**Response (200 OK):**
```json
{
  "total": 3,
  "subjects": [
    {
      "id": "subject-uuid",
      "name": "Linear Algebra",
      "code": "MA201",
      "semester": 2,
      "total_marks": 100,
      "exam_date": "2025-02-15",
      "papers_uploaded": 5,
      "predictions_generated": 1,
      "created_at": "2025-01-05"
    }
  ]
}
```

#### POST /subjects
**Request:**
```json
{
  "name": "Linear Algebra",
  "code": "MA201",
  "semester": 2,
  "total_marks": 100,
  "exam_date": "2025-02-15",
  "exam_duration_minutes": 180,
  "syllabus_json": {
    "units": [
      {
        "name": "Unit 1",
        "topics": ["Matrices", "Determinants", "Inverse"]
      }
    ]
  }
}
```

**Response (201 Created):**
```json
{
  "id": "subject-uuid",
  "message": "Subject created successfully"
}
```

#### GET /subjects/{id}
**Response (200 OK):**
```json
{
  "id": "subject-uuid",
  "name": "Linear Algebra",
  "/* ... full subject details ... */
}
```

#### PUT /subjects/{id}
**Request:** (send fields to update)
**Response (200 OK):** Updated subject object

#### DELETE /subjects/{id}
**Response (204 No Content)**

### 6.3 Paper Upload Endpoints

#### POST /papers/upload
**Request:** (form-data)
```
file: [PDF file]
subject_id: subject-uuid
exam_year: 2024
```

**Response (202 Accepted):** (async processing)
```json
{
  "paper_id": "paper-uuid",
  "status": "processing",
  "message": "Paper received. Processing started.",
  "estimated_time": "2-3 minutes"
}
```

#### GET /papers/{subject_id}
**Response (200 OK):**
```json
{
  "total": 5,
  "papers": [
    {
      "id": "paper-uuid",
      "file_name": "2024_exam_paper.pdf",
      "exam_year": 2024,
      "total_marks": 100,
      "processing_status": "completed",
      "questions_extracted": 25,
      "processed_at": "2025-01-05T10:30:00Z"
    }
  ]
}
```

#### GET /papers/{id}/preview
**Response (200 OK):**
```json
{
  "file_name": "2024_exam_paper.pdf",
  "text_preview": "Question 1: ... [first 500 chars]",
  "questions_extracted": [
    {
      "number": 1,
      "text": "...",
      "marks": 5,
      "unit": "Unit 1"
    }
  ]
}
```

#### DELETE /papers/{id}
**Response (204 No Content)**

### 6.4 Prediction Endpoints

#### POST /predictions/generate
**Request:**
```json
{
  "subject_id": "subject-uuid",
  "use_all_papers": true,
  "force_regenerate": false
}
```

**Response (202 Accepted):** (async processing)
```json
{
  "prediction_id": "prediction-uuid",
  "status": "generating",
  "message": "Prediction in progress. Check back in 2-3 minutes.",
  "progress": 0
}
```

#### GET /predictions/{id}
**Response (200 OK):**
```json
{
  "id": "prediction-uuid",
  "subject_id": "subject-uuid",
  "predicted_questions": [
    {
      "question_number": 1,
      "text": "...",
      "marks": 5,
      "unit": "Unit 1",
      "probability": "very_high",
      "reasoning": "Appeared 4/5 years consecutively"
    }
  ],
  "total_marks": 100,
  "coverage_percentage": 95,
  "unit_coverage": {
    "Unit 1": 45,
    "Unit 2": 30,
    "Unit 3": 25
  },
  "generated_at": "2025-01-05T10:30:00Z"
}
```

#### GET /predictions/{subject_id}/latest
**Response (200 OK):** Latest prediction for subject

#### PUT /predictions/{id}
**Request:** (update feedback/notes)
**Response (200 OK)**

### 6.5 Trend Analysis Endpoints

#### GET /analysis/{subject_id}/frequency
**Response (200 OK):**
```json
{
  "topic_frequency": {
    "Binary Search": 5,
    "Linked Lists": 4,
    "Sorting": 3
  },
  "unit_frequency": {
    "Unit 1": 5,
    "Unit 2": 4
  },
  "total_questions_analyzed": 25
}
```

#### GET /analysis/{subject_id}/weightage
**Response (200 OK):**
```json
{
  "unit_weightage": {
    "Unit 1": {
      "total_marks": 45,
      "percentage": 45,
      "question_count": 9
    }
  },
  "mark_distribution": {
    "2": 30,
    "5": 40,
    "10": 30
  }
}
```

#### GET /analysis/{subject_id}/repetitions
**Response (200 OK):**
```json
{
  "exact_repetitions": [
    {
      "question": "...",
      "appeared_years": [2022, 2023, 2024],
      "frequency": 3
    }
  ],
  "similar_questions": [
    {
      "question": "...",
      "similarity_score": 0.85,
      "variants": ["variant 1", "variant 2"]
    }
  ],
  "repetition_cycle_years": 2
}
```

#### GET /analysis/{subject_id}/trends
**Response (200 OK):**
```json
{
  "difficulty_trend": "increasing",
  "topic_trends": {
    "Binary Search": {
      "trend": "stable",
      "frequency_2020": 3,
      "frequency_2024": 3
    }
  },
  "insights": [
    "Questions are getting 15% harder",
    "Unit 2 topics are rising in importance"
  ]
}
```

### 6.6 Mock Test Endpoints

#### POST /tests/generate
**Request:**
```json
{
  "subject_id": "subject-uuid",
  "num_questions": 25,
  "difficulty": "medium",
  "time_limit_minutes": 90,
  "question_source": "mixed"
}
```

**Response (201 Created):**
```json
{
  "test_id": "test-uuid",
  "total_questions": 25,
  "total_marks": 100,
  "time_limit_minutes": 90,
  "start_time": "2025-01-05T10:30:00Z",
  "questions": [
    {
      "id": "q1-uuid",
      "number": 1,
      "text": "...",
      "marks": 5,
      "unit": "Unit 1",
      "options": ["A", "B", "C", "D"], // only for MCQ
      "type": "mcq"
    }
  ]
}
```

#### POST /tests/{id}/submit
**Request:**
```json
{
  "answers": {
    "q1-uuid": "A",
    "q2-uuid": "Text answer...",
    "q3-uuid": "B"
  },
  "end_time": "2025-01-05T11:30:00Z"
}
```

**Response (200 OK):**
```json
{
  "test_id": "test-uuid",
  "score": 72,
  "total_marks": 100,
  "percentage": 72,
  "duration_minutes": 45,
  "results": {
    "correct": 18,
    "incorrect": 5,
    "skipped": 2
  }
}
```

#### GET /tests/{id}/results
**Response (200 OK):**
```json
{
  "test_id": "test-uuid",
  "score": 72,
  "percentage": 72,
  "question_analysis": [
    {
      "question_id": "q1-uuid",
      "marks": 5,
      "status": "correct",
      "user_answer": "A",
      "correct_answer": "A",
      "explanation": "..."
    }
  ],
  "weak_topics": ["Dynamic Programming"],
  "strong_topics": ["Sorting"],
  "recommendations": [...]
}
```

### 6.7 Chatbot Endpoints

#### POST /chat/message
**Request:**
```json
{
  "subject_id": "subject-uuid",
  "message": "Explain binary search tree",
  "context": {
    "previous_messages_count": 5,
    "last_message_type": "question_analysis"
  }
}
```

**Response (200 OK):**
```json
{
  "message_id": "msg-uuid",
  "response": "A Binary Search Tree (BST) is a tree where...",
  "related_questions": [
    {
      "text": "...",
      "marks": 5,
      "appeared_years": [2023, 2024],
      "probability": "very_high"
    }
  ],
  "references": [
    {
      "type": "paper",
      "paper_year": 2024,
      "question": "..."
    }
  ],
  "suggested_actions": [
    "Add to revision",
    "Practice similar questions",
    "Take targeted mock test"
  ]
}
```

#### GET /chat/history/{subject_id}
**Query Params:** `?limit=50&offset=0`

**Response (200 OK):**
```json
{
  "total": 100,
  "messages": [
    {
      "id": "msg-uuid",
      "timestamp": "2025-01-05T10:30:00Z",
      "user_message": "Explain binary search tree",
      "bot_response": "..."
    }
  ]
}
```

#### DELETE /chat/clear
**Request:**
```json
{
  "subject_id": "subject-uuid"
}
```

**Response (204 No Content)**

### 6.8 Study Plan Endpoints

#### POST /plan/generate
**Request:**
```json
{
  "subject_id": "subject-uuid",
  "start_date": "2025-01-06",
  "exam_date": "2025-02-15"
}
```

**Response (201 Created):**
```json
{
  "plan_id": "plan-uuid",
  "subject_id": "subject-uuid",
  "total_days": 40,
  "daily_schedule": [
    {
      "day": 1,
      "date": "2025-01-06",
      "topics": ["Unit 1: Matrices", "Unit 1: Determinants"],
      "recommended_hours": 3,
      "priority_topics": ["Matrices"]
    },
    {
      "day": 2,
      "date": "2025-01-07",
      "topics": ["Unit 1: Inverse", "Unit 2: Vector Spaces"],
      "recommended_hours": 2.5
    }
  ]
}
```

#### GET /plan/{user_id}
**Response (200 OK):** Current active plan

#### PUT /plan/{id}
**Request:** (mark days complete, adjust schedule)
**Response (200 OK)**

---

## 7. AI/ML CAPABILITIES

### 7.1 Pattern Recognition Engine

#### Algorithm: Topic Frequency Analysis
```python
def analyze_topic_frequency(questions_list):
    """
    Input: List of extracted questions with topics
    Output: Frequency map of topics across papers
    
    Process:
    1. Extract topics from each question
    2. Count occurrences per topic
    3. Calculate percentage
    4. Sort by frequency
    5. Return: { "Topic": count, "Percentage": % }
    """
```

#### Algorithm: Question Similarity Detection
```python
def detect_similar_questions(questions):
    """
    Detect repeated or semantically similar questions
    
    Process:
    1. Generate embeddings for each question
    2. Calculate cosine similarity between all pairs
    3. Cluster similar questions (threshold: 0.85)
    4. Mark as "repeated" if 4+ words overlap
    5. Mark as "similar" if embedding similarity > 0.75
    """
```

#### Algorithm: Unit-wise Weightage Calculation
```python
def calculate_unit_weightage(papers_data):
    """
    Calculate marks distribution per unit
    
    Process:
    1. Sum marks for each unit across all papers
    2. Calculate average per unit
    3. Calculate percentage of total
    4. Return: { "Unit": {"total": X, "avg": Y, "%": Z} }
    """
```

### 7.2 Prediction Engine

#### Algorithm: Question Probability Scoring
```python
def score_question_probability(question, historical_data):
    """
    Score probability of question appearing in future exams
    
    Factors:
    - Frequency: How many times appeared (weight: 40%)
    - Recency: Year of last appearance (weight: 25%)
    - Cycle: Question repetition pattern (weight: 20%)
    - Importance: Marks/weightage (weight: 15%)
    
    Score calculation:
    frequency_score = (appearances / total_papers) * 40
    recency_score = (years_since_last / total_years) * 25
    cycle_score = (expected_in_pattern) * 20
    importance_score = (marks / max_marks) * 15
    
    total = sum(all_scores)
    
    Probability:
    if total > 75: "very_high"
    elif total > 50: "high"
    else: "moderate"
    """
```

#### Algorithm: Predicted Question Paper Generation
```python
def generate_predicted_paper(subject, probabilities):
    """
    Generate full predicted question paper
    
    Input:
    - Subject details (total marks, format)
    - Question probabilities (very_high, high, moderate)
    
    Process:
    1. Filter questions by probability (prioritize very_high)
    2. Maintain mark distribution:
       - 2-mark: 30% of paper
       - 5-mark: 40% of paper
       - 10-mark: 30% of paper
    3. Maintain unit distribution (from weightage analysis)
    4. Randomize order
    5. Format matching university template
    
    Output:
    - Complete question paper with marks, units, probabilities
    """
```

### 7.3 RAG Pipeline (Chatbot Context)

#### Architecture
```
User Input (Question) 
    ↓
Vector Embedding (Gemini API)
    ↓
Retrieval (Search uploaded PDFs)
    ↓
Context Assembly (Top 3 relevant documents)
    ↓
Prompt Enrichment:
    - User question
    - Retrieved context
    - Question metadata (marks, year, unit)
    - Student's weak areas
    ↓
Gemini API (Generate response)
    ↓
Response Formatting:
    - Explanation
    - References to PYQs
    - Related practice questions
    - Study recommendations
```

#### Sample Prompt Template
```
You are StudyBuddy, an intelligent exam preparation assistant for [Subject] at [College].

Context from student's uploaded papers:
- Total papers analyzed: 5
- Questions extracted: 127
- Time period: 2020-2024

Student Profile:
- Weak areas: [List from mock tests]
- Strong areas: [List from mock tests]
- Exam date: [Date]
- Days remaining: [Count]

User Question: "[User's question]"

Related Questions from Previous Year Papers:
1. "[Question 1]" - Appeared 3 times, Probability: Very High
2. "[Question 2]" - Appeared 2 times, Probability: High

Your Response Should Include:
1. Clear, concise answer to user's question
2. Specific examples from the papers they uploaded
3. Links to related exam questions
4. Study tips based on their weak areas
5. Actionable next steps

Tone: Encouraging, data-driven, personalized
```

### 7.4 Mock Test Generation

#### Algorithm: Adaptive Question Selection
```python
def generate_adaptive_test(user_profile, difficulty, num_questions):
    """
    Generate test based on user's weak areas and difficulty
    
    Process:
    1. Get user's weak topics from previous tests
    2. Get predicted high-probability questions
    3. Select questions:
       - 60% from predicted high-probability
       - 25% from weak areas (focused practice)
       - 15% new/challenging questions
    4. Maintain mark distribution
    5. Sort by difficulty
    6. Randomize order
    
    Difficulty levels:
    - Easy: 30% 2-mark, 40% 5-mark, 30% 10-mark
    - Medium: 20% 2-mark, 50% 5-mark, 30% 10-mark
    - Hard: 10% 2-mark, 40% 5-mark, 50% 10-mark
    """
```

### 7.5 Performance Analytics

#### Weak Area Detection
```python
def detect_weak_areas(test_results):
    """
    Identify topics where student struggled
    
    Process:
    1. Get all incorrect/skipped questions
    2. Extract topics from these questions
    3. Calculate accuracy per topic
    4. Flag as "weak" if accuracy < 60%
    5. Generate practice recommendations
    """
```

#### Progress Tracking
```python
def track_progress(user_test_history):
    """
    Analyze improvement over time
    
    Calculate:
    - Score trend (linear regression)
    - Improvement rate (% per test)
    - Consistency (std deviation)
    - Predicted final score (extrapolation)
    
    Output:
    - Trend direction (improving/declining/stable)
    - Areas of improvement
    - Areas needing attention
    - Estimated exam performance
    """
```

---

## 8. FEATURE DEEP-DIVES

### 8.1 Smart Question Paper Prediction

**Process Flow:**

```
1. PDF Upload
   └─ User uploads 5 previous year papers
   
2. Text Extraction
   ├─ PyPDF2 for text-based PDFs
   ├─ Tesseract OCR for scanned images
   └─ Output: Raw text of entire paper
   
3. Question Parsing
   ├─ Use Gemini to identify question boundaries
   ├─ Extract: question number, marks, text
   ├─ Output: Structured question list
   
4. Topic Classification
   ├─ Use spaCy NER for unit/topic extraction
   ├─ Match against syllabus topics
   ├─ Assign unit and sub-topics
   
5. Pattern Analysis
   ├─ Frequency: How many times appears
   ├─ Recency: Year of last appearance
   ├─ Cycle: Expected repetition pattern
   ├─ Similarity: Semantic duplicates
   
6. Probability Scoring
   ├─ Weight factors (frequency 40%, recency 25%, etc.)
   ├─ Score: 0-100 scale
   ├─ Tag: Very High (>75), High (50-75), Moderate (<50)
   
7. Paper Generation
   ├─ Select questions by probability
   ├─ Maintain mark distribution
   ├─ Maintain unit distribution
   ├─ Format as official exam paper
```

**Accuracy Improvement:**
- Version 1: 60-70% accuracy (basic frequency)
- Version 2: 75-80% accuracy (with recency + cycle)
- Version 3: 80-85% accuracy (with semantic similarity)

### 8.2 Trend Analysis & Visualization

**Charts Provided:**

1. **Heatmap** (Topic vs Year)
   - Shows which topics appear each year
   - Color intensity = frequency
   - Interactive filtering

2. **Pie Chart** (Unit Distribution)
   - Percentage of marks per unit
   - Click to filter predictions

3. **Bar Chart** (Marks Distribution)
   - 2-mark, 5-mark, 10-mark breakdown
   - Per unit or overall

4. **Line Chart** (Trends)
   - Difficulty trend over years
   - Topic importance trend
   - Score improvement trend (personal)

5. **Sankey Diagram** (Unit → Topic → Questions)
   - Flow visualization
   - Click to drill down

**Insights Generated:**
- Top 3 must-study units
- Question repetition rate
- Difficulty trend (getting harder?)
- Topics never repeated (low priority)
- Optimal time allocation

### 8.3 AI Study Chatbot

**Conversation Types:**

1. **Concept Explanation**
   ```
   User: "Explain Binary Search Tree"
   Bot: [Definition] → [Real exam example] → [Practice question]
   
   Data: Uses uploaded PYQs as examples
   ```

2. **Question Analysis**
   ```
   User: "Is this question important?" [pastes Q]
   Bot: [Frequency] → [Probability] → [Recommendation]
   
   Data: Checks historical patterns
   ```

3. **Study Planning**
   ```
   User: "I have 10 days to exam"
   Bot: [Day-by-day plan] → [Topics] → [Mock tests]
   
   Data: Uses predictions + exam date
   ```

4. **Performance Analysis**
   ```
   User: "Why am I weak in Unit 2?"
   Bot: [Mock test analysis] → [Error patterns] → [Practice plan]
   
   Data: Mock test history + incorrect questions
   ```

5. **Exam Strategy**
   ```
   User: "How to manage time in exam?"
   Bot: [Time allocation per section] → [Question selection order]
   
   Data: Question distribution + difficulty
   ```

**Memory Management:**
- Context window: Last 10 messages
- Vector embeddings: All chat messages (searchable)
- Session: 24-hour conversation history
- Persistence: Save to database for learning

### 8.4 Mock Test System

**Test Generation:**
- Questions from predictions (prioritized)
- Mix of known + challenging questions
- Adaptive based on previous performance
- Maintains mark/unit distribution

**Test Format:**
- Multiple choice + descriptive
- Timer with alerts
- Question navigation palette
- Review before submit

**Instant Feedback:**
- Score + percentage
- Question-by-question analysis
- Correct answer + explanation
- Weak area identification
- Comparison with past attempts

**Progress Tracking:**
- Score history (graph)
- Topic-wise accuracy
- Time management analysis
- Improvement trajectory
- Predicted exam performance

---

## 9. SECURITY & PERFORMANCE

### 9.1 Security Implementation

**Authentication & Authorization:**
- JWT tokens (24-hour expiry)
- Refresh tokens (7-day expiry)
- Password hashing (bcrypt, 10 rounds)
- Rate limiting (100 req/min per user)
- CORS enabled only for frontend

**Data Protection:**
- HTTPS/TLS only
- Encryption at rest (Supabase)
- Encryption in transit (HTTPS)
- SQL injection prevention (parameterized queries)
- XSS prevention (input sanitization)

**File Security:**
- File type validation (PDF only)
- File size limit (10MB)
- Virus scanning (optional, integrate VirusTotal)
- Secure storage (Supabase Storage, private bucket)
- Signed URLs for file access

**User Privacy:**
- No tracking or analytics without consent
- GDPR compliant (data export, deletion)
- No third-party sharing
- Clear privacy policy
- User control over data

### 9.2 Performance Optimization

**Frontend:**
- Code splitting (route-based)
- Lazy loading images
- Minified CSS/JS
- Service worker caching
- Local storage for auth
- Debouncing search

**Backend:**
- Database indexing (optimized queries)
- API response caching (Redis - future)
- PDF processing async (Celery - future)
- Connection pooling
- Query optimization
- Response pagination

**Database:**
- Connection pooling (max 20)
- Index on frequently queried fields
- Soft deletes (paranoia)
- Archival for old data
- Backups (auto, hourly)

**CDN:**
- Vercel CDN for frontend
- Supabase Storage CDN for files
- Browser caching headers

**Monitoring:**
- Error tracking (Sentry)
- Performance monitoring (Vercel Analytics)
- Log aggregation (CloudWatch - optional)
- Uptime monitoring (StatusPage - optional)

### 9.3 Scalability

**Current (Free Tier):**
- 100-200 concurrent users
- 500MB database
- 1GB storage
- 1,500 Gemini API calls/day

**Scale-up Strategy:**
1. **Database:** Supabase → AWS RDS (managed)
2. **Cache:** Redis for session/query caching
3. **Queue:** Celery + RabbitMQ for async tasks
4. **Storage:** S3 for PDFs (unlimited)
5. **Compute:** Railway → AWS EC2/ECS
6. **Load Balancing:** AWS ALB

---

## 10. TESTING STRATEGY

### 10.1 Unit Tests

**Backend:**
```python
# tests/test_pdf_parser.py
def test_extract_text_from_pdf():
    # Test PDF text extraction
    
def test_parse_questions():
    # Test question parsing from text
    
def test_calculate_probability():
    # Test probability scoring algorithm
```

**Frontend:**
```javascript
// tests/components/Dashboard.test.jsx
test('renders dashboard with subjects', () => {
  // Test dashboard rendering
})
```

### 10.2 Integration Tests

```python
# tests/test_prediction_flow.py
def test_complete_prediction_flow():
    """
    1. Upload PDF
    2. Extract questions
    3. Calculate probabilities
    4. Generate prediction
    5. Verify output format
    """
```

### 10.3 E2E Tests (Selenium/Playwright)

```javascript
// tests/e2e/upload.test.js
test('User can upload paper and get prediction', () => {
  1. Login
  2. Navigate to upload
  3. Select PDF file
  4. Submit
  5. Wait for processing
  6. Verify prediction page
})
```

### 10.4 Performance Tests

```python
# tests/test_performance.py
def test_pdf_parsing_time():
    # Should complete in <30 seconds for 10MB PDF
    
def test_api_response_time():
    # GET requests: <200ms
    # POST requests: <500ms
```

---

## 11. DEPLOYMENT GUIDE

### 11.1 Pre-Deployment Checklist

- [ ] All tests passing (unit + integration + E2E)
- [ ] No hardcoded secrets (use .env)
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Error handling complete
- [ ] Logging configured
- [ ] Security headers set
- [ ] Rate limiting enabled
- [ ] Monitoring configured
- [ ] Backup strategy defined

### 11.2 Deployment Process

**Frontend (Vercel):**
```bash
# Connect GitHub repo to Vercel
# Set environment variables in Vercel dashboard
# Auto-deploy on push to main branch
```

**Backend (Railway):**
```bash
# Connect GitHub repo to Railway
# Set environment variables
# Deploy from main branch
# Auto-restart on failure
```

**Database (Supabase):**
```bash
# Create project
# Run migrations
# Configure backups
# Enable SSL
```

**Post-Deployment:**
```bash
1. Verify frontend at prepiq.vercel.app
2. Verify API at railway backend URL
3. Run smoke tests
4. Monitor error logs
5. Check performance metrics
6. Alert team if issues
```

---

## 12. POST-LAUNCH ROADMAP

### Phase 2 (Month 2-3)
- [ ] Community features (student forums)
- [ ] Leaderboards (anonymized)
- [ ] Video explanations (YouTube integration)
- [ ] Browser extension (auto-categorize saved questions)
- [ ] Email notifications (study reminders)

### Phase 3 (Month 4-6)
- [ ] Mobile app (React Native)
- [ ] WhatsApp bot (send study tips)
- [ ] Collaborative study groups
- [ ] Professor integration (verify papers)
- [ ] Advanced analytics (predictive modeling)

### Phase 4 (Month 7-12)
- [ ] Multi-university support
- [ ] Multiple languages support
- [ ] Internationalization (beyond India)
- [ ] Enterprise (schools/coaching centers)
- [ ] API for third-party integration

---

## CONCLUSION

PrepIQ is a comprehensive, feature-rich exam preparation platform with:
- ✅ AI-powered predictions (80%+ accuracy)
- ✅ Intelligent trend analysis
- ✅ Personalized AI chatbot guidance
- ✅ Adaptive mock tests
- ✅ 100% free, no paywalls
- ✅ Built for scale and reliability

This specification provides everything needed to build a production-grade application that helps millions of students study smarter and achieve better results.

---

**Document prepared for:** PrepIQ Development Team  
**Version:** 1.0  
**Last Updated:** January 5, 2026  
**Status:** Ready for Development
