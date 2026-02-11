# PREPIQ FULL CODE AUDIT REPORT
## Comprehensive Security, Performance & Quality Analysis

**Date:** 2026-01-06  
**Auditor:** Principal Engineer  
**Scope:** Complete codebase audit - Frontend (Next.js 14) + Backend (FastAPI)  

---

## EXECUTIVE SUMMARY

This audit identified **47 issues** across the PrepIQ codebase, categorized as:
- **Critical (5):** Security vulnerabilities, data integrity risks
- **High (12):** Performance bottlenecks, error handling gaps  
- **Medium (18):** Code quality, maintainability issues
- **Low (12):** Best practice violations, minor optimizations

**Overall Risk Level:** MODERATE-HIGH  
**Immediate Action Required:** Critical and High priority items

---

## CRITICAL PRIORITY ISSUES (Fix Immediately)

### C1: XSS Vulnerability in Chart Components
**Location:** 
- `frontend/src/components/ui/chart.tsx:83`
- `frontend/components/ui/chart.tsx:83`

**Issue:** Using `dangerouslySetInnerHTML` without sanitization allows XSS attacks if user data is rendered in charts.

**Impact:** Attackers could inject malicious JavaScript through crafted data points.

**Fix:**
```typescript
// BEFORE (Vulnerable):
dangerouslySetInnerHTML={{ __html: generatedContent }}

// AFTER (Safe):
import DOMPurify from 'dompurify';
dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(generatedContent) }}
```

**Files to Modify:**
- `frontend/src/components/ui/chart.tsx`
- `frontend/components/ui/chart.tsx`

---

### C2: Missing CSRF Protection on State-Changing Endpoints
**Location:** All backend routers (`/backend/app/routers/*.py`)

**Issue:** No CSRF tokens or SameSite cookie policies for POST/PUT/DELETE endpoints.

**Impact:** Cross-site request forgery attacks possible.

**Fix:** Add to `backend/app/main.py`:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="session",
    same_site="lax",  # or "strict" for production
    https_only=True   # for production
)
```

---

### C3: Unvalidated File Upload Could Lead to DoS
**Location:** `backend/app/routers/papers.py:80-95`

**Issue:** Reading entire file into memory before size check allows memory exhaustion.

**Impact:** Malicious actors could upload huge files to crash the server.

**Fix:**
```python
# Validate size BEFORE reading content
file_size = 0
max_size = 10 * 1024 * 1024  # 10MB
chunk_size = 8192

# First pass: check size only
while True:
    chunk = await file.read(chunk_size)
    if not chunk:
        break
    file_size += len(chunk)
    if file_size > max_size:
        raise HTTPException(413, "File too large")

await file.seek(0)
```

---

### C4: Race Condition in File Upload Progress Tracking
**Location:** `backend/app/routers/papers.py:51, 145, 162, 179, 306`

**Issue:** Using global dictionary `upload_progress` without thread-safe access.

**Impact:** Concurrent uploads can corrupt progress state or cause crashes.

**Fix:**
```python
import asyncio
from threading import Lock

upload_progress = {}
progress_lock = Lock()

# In upload endpoint:
with progress_lock:
    upload_progress[paper.id] = {...}
```

---

### C5: Hardcoded JWT Secret in Settings
**Location:** `backend/app/core/config.py:17`

**Issue:** Default fallback secret key is insecure.

**Impact:** If environment variable not set, predictable secret allows token forgery.

**Fix:**
```python
SECRET_KEY: str = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")
```

---

## HIGH PRIORITY ISSUES

### H1: Inconsistent Error Handling Returns 200 for Errors
**Location:** Multiple routers

**Issue:** Some endpoints return 200 status with error messages in body instead of proper HTTP codes.

**Example:** `backend/app/routers/auth.py:80`
```python
# Wrong:
except HTTPException:
    return {"valid": False}  # Returns 200!
```

**Fix:**
```python
# Correct:
except HTTPException as e:
    raise e  # Preserve original status code
```

---

### H2: Missing Input Validation on Query Parameters
**Location:** Multiple routers with `skip`, `limit`, `subject_id` params

**Issue:** No bounds checking on pagination parameters or UUID validation.

**Fix Example:**
```python
from pydantic import validator
from uuid import UUID

class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0, le=10000)
    limit: int = Field(100, ge=1, le=1000)
    
@router.get("/")
async def list_items(
    pagination: PaginationParams = Depends(),
    subject_id: UUID = Query(..., description="Subject UUID")
):
    ...
```

---

### H3: Missing Metadata Exports on Pages
**Location:** Multiple frontend pages

**Issue:** Several pages lack proper Next.js metadata exports for SEO.

**Affected Files:**
- `frontend/app/protected/page.tsx`
- `frontend/app/protected/subjects/page.tsx`
- `frontend/app/protected/predictions/page.tsx`
- `frontend/app/dashboard/page.tsx`

**Fix Example:**
```typescript
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Dashboard - PrepIQ',
  description: 'View your exam preparation progress',
  robots: { index: false, follow: false } // Protected page
};
```

---

### H4: Password Hashing Uses Weak Algorithm Check Missing
**Location:** `backend/services/supabase_first_auth.py`

**Issue:** No verification that bcrypt is actually being used.

**Fix:** Add verification:
```python
import bcrypt

# Ensure bcrypt is being used
password_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Ensure sufficient rounds
)
```

---

### H5: JWT Token Validation Missing Edge Cases
**Location:** `backend/services/supabase_first_auth.py:215-255`

**Issue:** No handling for:
- Expired tokens
- Malformed tokens  
- Algorithm confusion attacks

**Fix:**
```python
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

try:
    user_response = supabase.auth.get_user(token)
except ExpiredSignatureError:
    raise HTTPException(401, "Token has expired")
except InvalidTokenError:
    raise HTTPException(401, "Invalid token")
```

---

### H6: Print Statements in Production Code (Backend)
**Location:** 17 instances across backend

**Issue:** Using `print()` instead of structured logging.

**Affected Files:**
- `backend/app/database.py:57,64`
- `backend/app/routers/dashboard.py:71,122-123,165-166`
- `backend/app/routers/analysis.py:250-251`
- `backend/app/ml/engines/*.py` (multiple)

**Fix:** Replace with structured logger:
```python
import logging

logger = logging.getLogger(__name__)

# Replace:
print(f"Error: {e}")

# With:
logger.error("Operation failed", exc_info=e, operation="database_query")
```

---

### H7: PDF Parser Memory Exhaustion Risk
**Location:** `backend/app/pdf_parser.py:42-69`

**Issue:** PDF bytes written to temp file without size limits; temp file not deleted on exception.

**Fix:**
```python
import tempfile
import os

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    # Check size first
    max_pdf_size = 50 * 1024 * 1024  # 50MB
    if len(pdf_bytes) > max_pdf_size:
        raise ValueError("PDF too large")
    
    tmp_filename = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_filename = tmp_file.name
        # ... processing ...
    finally:
        if tmp_filename and os.path.exists(tmp_filename):
            os.unlink(tmp_filename)
```

---

### H8: No Rate Limiting on Auth Endpoints
**Location:** `backend/app/routers/auth.py`

**Issue:** Login/signup endpoints vulnerable to brute force attacks.

**Fix:** Add rate limiting middleware:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

---

### H9: Frontend Console.log Statements in Production
**Location:** To be identified in components

**Issue:** Debug console.log statements expose implementation details.

**Fix:** Create logger utility that disables in production:
```typescript
// utils/logger.ts
const isDev = process.env.NODE_ENV === 'development';

export const logger = {
  log: (...args: any[]) => isDev && console.log(...args),
  error: (...args: any[]) => console.error(...args), // Keep errors
  warn: (...args: any[]) => isDev && console.warn(...args),
};
```

---

### H10: Missing Global Exception Handler in FastAPI
**Location:** `backend/app/main.py`

**Issue:** No catch-all exception handler returns 500 with stack traces.

**Fix:** Add to main.py:
```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}  # Don't expose details
    )
```

---

### H11: Database Connection Not Validated Before Use
**Location:** `backend/app/database.py`

**Issue:** No health check for database connection on startup.

**Fix:**
```python
@app.on_event("startup")
async def startup_event():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise RuntimeError("Cannot start without database")
```

---

### H12: Sensitive Data Logging
**Location:** Various files

**Issue:** Potential logging of JWT tokens, passwords, or PII.

**Fix:** Audit all log statements to ensure they don't include:
- Authorization headers
- Password fields
- Personal information (emails can be logged but hashed/anonymized)

---

## MEDIUM PRIORITY ISSUES

### M1: Duplicate Frontend Component Files
**Location:** 
- `frontend/components/ui/*` and `frontend/src/components/ui/*`

**Issue:** Two copies of same components - maintenance nightmare.

**Fix:** Consolidate into single location (`frontend/src/components/ui/`), update imports.

---

### M2: Missing React Keys in List Renders
**Location:** To be identified in component audit

**Fix:** Ensure all `.map()` calls have unique `key` props.

---

### M3: ML Model Loading Per Request
**Location:** `backend/app/ml/training/model_trainer.py`

**Issue:** Models should be loaded at startup, not per-request.

**Current Status:** ✅ Already fixed - models loaded in main.py lifespan

---

### M4: Unused Imports
**Location:** Multiple files

**Fix:** Run `ruff check --select F401` and remove unused imports.

---

### M5: Missing Type Hints
**Location:** Multiple backend files

**Fix:** Add comprehensive type hints for better IDE support and error catching.

---

### M6: Frontend Image Optimization
**Location:** Multiple pages using `<img>` instead of Next.js `<Image>`

**Fix:** Replace with:
```typescript
import Image from 'next/image';

<Image src="/path" alt="desc" width={800} height={600} />
```

---

### M7: No Input Sanitization on Chat Messages
**Location:** `backend/app/routers/chat.py`

**Issue:** User messages stored/displayed without sanitization.

**Fix:** Strip HTML, limit length:
```python
import bleach
from pydantic import constr

message: constr(strip_whitespace=True, min_length=1, max_length=2000)
sanitized = bleach.clean(message, tags=[], strip=True)
```

---

### M8: Weak CORS Configuration in Development
**Location:** `backend/app/main.py:14`

**Issue:** `allow_origins` uses wildcard effectively in development.

**Fix:** Enforce strict origins even in dev:
```python
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", 
    "http://localhost:3000"  # Only default frontend
).split(",")
```

---

### M9: No API Versioning
**Location:** Backend routers

**Issue:** No version prefix on API routes.

**Fix:** Add version prefix in main.py:
```python
app.include_router(auth.router, prefix="/api/v1")
```

---

### M10: Missing Pagination on List Endpoints
**Location:** Multiple list endpoints without pagination

**Fix:** Add pagination to all list endpoints.

---

### M11: No Request ID Tracking
**Location:** Backend

**Issue:** Cannot trace requests through logs.

**Fix:** Add request ID middleware:
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

---

### M12: Frontend Error Boundary Missing
**Location:** Frontend

**Issue:** No global error boundary to catch React errors.

**Fix:** Create error boundary component and wrap layout.

---

### M13-18: Additional Code Quality Issues
- Inconsistent naming conventions
- Missing docstrings on public methods
- Hardcoded magic numbers
- Missing database transaction management
- No API documentation beyond OpenAPI
- Missing health check endpoint details

---

## LOW PRIORITY ISSUES

### L1: Deprecated PyPDF2 Usage
**Location:** `backend/app/pdf_parser.py:32-34`

**Issue:** PyPDF2 deprecated methods used.

**Fix:** Use PyMuPDF (fitz) exclusively or update PyPDF2 usage.

---

### L2: start_all.py Hardcoded Ports
**Location:** `start_all.py:5-6`

**Issue:** Ports hardcoded in documentation comments.

**Fix:** Read from environment variables.

---

### L3: Test Endpoints Hardcoded URL
**Location:** `test_endpoints.py:5`

**Issue:** `base_url = "http://localhost:8000"` hardcoded.

**Fix:** Read from env or command line argument.

---

### L4-12: Minor Issues
- Missing pre-commit hooks
- No linting configuration file
- Unused variables
- Commented-out code
- TODO comments without issue tracking
- Inconsistent quote styles
- Missing .editorconfig
- No CHANGELOG.md
- Missing architecture documentation

---

## FILES REQUIRING MODIFICATION

### Critical Priority:
1. `frontend/src/components/ui/chart.tsx` - XSS fix
2. `frontend/components/ui/chart.tsx` - XSS fix
3. `backend/app/main.py` - CSRF protection, global exception handler
4. `backend/app/routers/papers.py` - File upload validation, race condition fix
5. `backend/app/core/config.py` - JWT secret validation

### High Priority:
6. All backend routers - Error handling standardization
7. `backend/app/routers/auth.py` - Rate limiting
8. `backend/app/pdf_parser.py` - Memory safety
9. `backend/app/database.py` - Connection validation
10. `backend/services/supabase_first_auth.py` - JWT edge cases
11. Multiple frontend pages - Metadata exports
12. Backend ML files - Replace print with logging

### Medium Priority:
13. Frontend component consolidation
14. Chat message sanitization
15. CORS configuration tightening
16. API versioning
17. Pagination implementation
18. Request ID middleware
19. Frontend error boundary

### Low Priority:
20. Code style consistency
21. Documentation improvements
22. Test configuration

---

## MANUAL STEPS REQUIRED

1. **Install DOMPurify:**
   ```bash
   cd frontend && npm install dompurify @types/dompurify
   ```

2. **Install Rate Limiting:**
   ```bash
   cd backend && pip install slowapi
   ```

3. **Install Logging:**
   ```bash
   cd backend && pip install structlog
   ```

4. **Update Environment Variables:**
   Add to `.env`:
   ```
   SECRET_KEY=your-secure-random-key-here
   RATE_LIMIT_ENABLED=true
   ```

5. **Set Up Pre-commit Hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

6. **Run Security Scans:**
   ```bash
   # Backend
   bandit -r backend/app
   
   # Frontend
   cd frontend && npm audit
   ```

---

## COMPLIANCE CHECKLIST

- [ ] XSS vulnerabilities fixed
- [ ] CSRF protection implemented
- [ ] Rate limiting on auth endpoints
- [ ] File upload validation hardened
- [ ] JWT validation edge cases handled
- [ ] Print statements replaced with logging
- [ ] Global exception handler added
- [ ] Database connection validated on startup
- [ ] API versioning implemented
- [ ] Frontend metadata exports complete
- [ ] Error boundaries implemented
- [ ] Security headers configured
- [ ] Sensitive data not logged
- [ ] Input validation on all endpoints
- [ ] React keys present on all lists

---

## RECOMMENDED PRIORITY ORDER

### Week 1 (Critical):
1. Fix XSS vulnerabilities (C1)
2. Fix file upload DoS vulnerability (C3)
3. Fix JWT secret validation (C5)
4. Add CSRF protection (C2)
5. Fix race condition (C4)

### Week 2 (High):
6. Standardize error handling (H1)
7. Add rate limiting (H8)
8. Fix JWT edge cases (H5)
9. Replace print statements (H6)
10. Add global exception handler (H10)

### Week 3 (Medium):
11. Fix metadata exports (H3)
12. Add input validation (H2)
13. Implement API versioning (M9)
14. Add pagination (M10)

### Week 4 (Cleanup):
15. Code consolidation (M1)
16. Performance optimizations (M6)
17. Documentation updates

---

**Next Steps:**
1. Create GitHub issues for each Critical and High priority item
2. Assign owners and set deadlines
3. Run automated security scans weekly
4. Schedule follow-up audit in 1 month

---

*End of Audit Report*
