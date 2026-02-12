# PrepIQ Production Readiness - Repository Analysis Report

**Date:** 2026-02-12  
**Repository:** https://github.com/Ashutosh3021/PrepIQ

---

## 📁 Project Structure

### Frontend (Next.js 16 + React 19)
**Location:** `frontend/`  
**Tech Stack:**
- Next.js 16.0.10 (App Router)
- React 19.2.0
- TypeScript 5.x
- Tailwind CSS 4.1.9
- Supabase SSR/Client SDK
- Radix UI Components
- Zod (validation)
- React Hook Form

**Key Frontend Files:**
- `frontend/app/wizard/page.tsx` - Wizard page wrapper
- `frontend/components/wizard/WizardForm.tsx` - Multi-step wizard form
- `frontend/app/protected/page.tsx` - Main dashboard (authenticated)
- `frontend/app/dashboard/page.tsx` - Legacy dashboard
- `frontend/src/lib/api.ts` - API service layer
- `frontend/components/dashboard-sidebar.tsx` - Navigation sidebar

### Backend (FastAPI + PostgreSQL)
**Location:** `backend/`  
**Tech Stack:**
- FastAPI
- SQLAlchemy ORM
- PostgreSQL (Supabase)
- Python 3.11+
- Bytez SDK (external ML API)

**Key Backend Files:**
- `backend/main.py` - FastAPI application entry point
- `backend/app/routers/wizard.py` - Wizard API endpoints
- `backend/app/routers/dashboard.py` - Dashboard statistics API
- `backend/app/models.py` - SQLAlchemy database models
- `backend/app/ml/external_api_wrapper.py` - Bytez ML models wrapper

---

## 🔍 Key Components Analysis

### 1. Wizard Form Component
**File:** `frontend/components/wizard/WizardForm.tsx`

**Current Implementation:**
- 3-step wizard (Exam Info → Study Focus → Goals)
- Step 1 captures: `exam_name` and `days_until_exam`
- Step 2 captures: `focus_subjects` and `study_hours_per_day`
- Step 3 captures: `target_score` and `preparation_level`
- Data is stored in local state (`wizardData`)
- Calls API endpoints: `authService.completeWizardStep1/2/3()` and `authService.completeWizard()`

**Issues Identified:**
- API calls don't actually save data to database (see Backend section)
- No validation on exam date/day relationship
- No confirmation before completion

### 2. Dashboard Component
**File:** `frontend/app/protected/page.tsx`

**Current Implementation:**
- Fetches user profile and dashboard stats on mount
- Displays `days_to_exam` from `dashboardStats?.days_to_exam`
- Shows study streak from `dashboardStats?.study_streak`
- Displays real user data when available

**Status:** ✅ **Already using dynamic data from API**

### 3. Dashboard Stats API
**File:** `backend/app/routers/dashboard.py`

**Current Implementation:**
- Calculates `days_to_exam` from user's `exam_date` or `days_until_exam` field
- Calculates real study streak from user activity (chat, tests, predictions)
- Fetches real recent activity from database

**Status:** ✅ **Already calculating real data**

### 4. Wizard API Endpoints
**File:** `backend/app/routers/wizard.py`

**Current Implementation:**
- Endpoints: `GET /wizard/status`, `POST /wizard/step1`, `POST /wizard/step2`, `POST /wizard/step3`, `POST /wizard/complete`, `PUT /wizard/update`
- **CRITICAL ISSUE:** All endpoints just return user data WITHOUT saving wizard data to database
- No database persistence for: `exam_name`, `days_until_exam`, `focus_subjects`, `study_hours_per_day`, `target_score`, `preparation_level`
- `wizard_completed` flag is never set to `True`

**Status:** ❌ **NOT SAVING DATA TO DATABASE**

---

## 🗄️ Database Schema

### User Model (`backend/app/models.py`)
```python
class User(Base):
    # ... existing fields ...
    
    # Wizard Data - All present in schema
    exam_name = Column(String(255), nullable=True)
    days_until_exam = Column(Integer, nullable=True)
    focus_subjects = Column(JSON, nullable=True)
    study_hours_per_day = Column(Integer, nullable=True)
    target_score = Column(Integer, nullable=True)
    preparation_level = Column(String(50), nullable=True)
    wizard_completed = Column(Boolean, default=False, nullable=False)
```

**Status:** ✅ **Schema supports all wizard fields**

---

## 🤖 ML Models (Bytze API)

**File:** `backend/app/ml/external_api_wrapper.py`

**8 Models Configured:**

| Model Type | Bytez Model Name | Purpose | Status |
|------------|------------------|---------|--------|
| 1. QA | `deepset/roberta-base-squad2` | Question answering from context | ✅ Configured |
| 2. Summarization | `facebook/bart-large-cnn` | Text summarization | ✅ Configured |
| 3. Classification | `ProsusAI/finbert` | Text classification | ✅ Configured |
| 4. Generation | `meta-llama/Meta-Llama-3-8B` | Text generation | ✅ Configured |
| 5. Sentence Similarity | `google/embeddinggemma-300m` | Semantic similarity | ✅ Configured |
| 6. Translation | `google/madlad400-3b-mt` | Language translation | ✅ Configured |
| 7. Image Captioning | `Salesforce/blip-image-captioning-large` | Image descriptions | ✅ Configured |
| 8. Chat | `meta-llama/Llama-2-7b-chat-hf` | Conversational AI | ✅ Configured |

**Issues Identified:**
- Hardcoded Bytez API key in code (line 29)
- Missing environment variable validation
- Fallback methods don't use ML, just basic heuristics
- No rate limiting or quota management

---

## 📊 Mock/Demo Data Analysis

**From:** `docs/MOCK_DATA_CATALOG.md`

### Found Issues:

1. **Predictions Pages** - Hardcoded prediction data with static questions
2. **User Profile** - "John Doe" placeholder names
3. **Dashboard** - Static greeting messages ("Hi Ashu!")
4. **Analysis Pages** - Fixed chart data arrays
5. **Questions Pages** - Static important questions

### Search Results for Demo/Mock Data:
- 83 matches found in frontend for placeholder/demo patterns
- Placeholder images: `/placeholder-user.jpg`, `/placeholder-bot.png`
- Mock test data in `frontend/app/tests/page.tsx`
- Static sample recommendations in predictions page

---

## 🐛 Critical Issues Summary

### Issue 1: Wizard Data Not Persisting (CRITICAL)
**Impact:** HIGH - User's exam setup is lost after completing wizard  
**Root Cause:** Backend wizard endpoints don't save to database  
**Fix Required:** Update all wizard endpoints to persist data

### Issue 2: Hardcoded API Key (SECURITY)
**Impact:** HIGH - Bytez API key exposed in source code  
**Location:** `backend/app/ml/external_api_wrapper.py:29`  
**Fix Required:** Move to environment variables

### Issue 3: Mock Data in Frontend (QUALITY)
**Impact:** MEDIUM - Demo data shown instead of real data  
**Files:** Predictions, Analysis, Questions pages  
**Fix Required:** Replace with real API calls

---

## ✅ What's Working Well

1. **Dashboard Stats API** - Correctly calculates days_to_exam and streaks from real data
2. **Database Schema** - Properly supports all required fields
3. **Frontend API Layer** - Well-structured with error handling
4. **Authentication** - Supabase integration complete
5. **ML Model Configuration** - All 8 models properly mapped

---

## 🎯 Recommended Implementation Order

### Phase 1: Fix Data Persistence (CRITICAL)
1. Fix wizard endpoints to save to database
2. Add validation for exam dates
3. Test end-to-end wizard → dashboard flow

### Phase 2: Security & Configuration
1. Move API keys to environment variables
2. Add input validation middleware
3. Error handling improvements

### Phase 3: Remove Mock Data
1. Update predictions page with real API calls
2. Update analysis page with real data
3. Remove placeholder images

### Phase 4: ML Model Optimization
1. Add retry logic with exponential backoff
2. Implement response caching
3. Add rate limiting

---

## 📋 Next Steps

**Awaiting approval to proceed with Phase 1 (Exam Days Left Fix)**

Once approved, I will:
1. Fix the backend wizard endpoints to persist data
2. Verify the dashboard correctly displays the saved exam days
3. Test the complete user flow

---

**Report Generated By:** AI Development Assistant  
**Total Analysis Time:** ~15 minutes  
**Files Examined:** 15+ core files
