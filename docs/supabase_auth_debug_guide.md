# PrepIQ Supabase Authentication Debug Guide

## Current Architecture Analysis

**Your app uses a hybrid approach:**
- ✅ Frontend → Backend API (FastAPI) for auth
- ✅ Backend → Local SQLite database (primary storage)
- ⚠️ Backend → Supabase (attempted sync, but failing)
- ✅ Frontend → Supabase client (for session/cookies only)

**The Problem:** Users are created in local SQLite but NOT in Supabase because:
1. Network connectivity issues to Supabase
2. Incorrect Supabase method usage (sign_up vs admin.create_user)
3. Silent failure handling masks the errors

## Step-by-Step Debugging & Fix Plan

### 1. Verify Current State

**Check local database users:**
```bash
# In backend directory
python -c "
import sqlite3
conn = sqlite3.connect('prepiq_local.db')
cursor = conn.cursor()
cursor.execute('SELECT id, email, full_name, created_at FROM users ORDER BY created_at DESC LIMIT 5')
users = cursor.fetchall()
print('Local database users:')
for user in users:
    print(f'  {user[1]} ({user[2]}) - {user[3]}')
conn.close()
"
```

**Check Supabase auth.users:**
Run this SQL in Supabase SQL Editor:
```sql
SELECT id, email, created_at, email_confirmed_at 
FROM auth.users 
ORDER BY created_at DESC 
LIMIT 10;
```

### 2. Test Supabase Connection

**Create test script:**
```python
# test_supabase_direct.py
import os
from supabase import create_client, Client

def test_supabase_connection():
    url = "https://cvkvciywqxsktlkigyth.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN2a3ZjaXl3cXhza3Rsa2lneXRoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzY5Mjc0OCwiZXhwIjoyMDgzMjY4NzQ4fQ.fvdB7635gvZ6V10LxY8M9MgNX5gUGQjtTf4DAaX84QE"
    
    print("Testing Supabase connection...")
    try:
        supabase: Client = create_client(url, key)
        print("✅ Supabase client created")
        
        # Test admin access
        response = supabase.auth.admin.list_users()
        print(f"✅ Admin access working - {len(response.data['users'])} users found")
        
        # Test creating a user
        test_email = "test-debug@example.com"
        test_password = "Test123456"
        
        # Clean up existing test user if exists
        try:
            existing = supabase.auth.admin.get_user_by_email(test_email)
            if existing:
                supabase.auth.admin.delete_user(existing.data.user.id)
                print("✅ Cleaned up existing test user")
        except:
            pass
            
        # Create test user
        result = supabase.auth.admin.create_user({
            "email": test_email,
            "password": test_password,
            "email_confirm": True
        })
        print(f"✅ Test user created: {result.data['user']['id']}")
        
        # Verify in auth.users
        users_response = supabase.auth.admin.list_users()
        test_user_exists = any(u['email'] == test_email for u in users_response.data['users'])
        print(f"✅ Test user verified in auth.users: {test_user_exists}")
        
        # Clean up
        supabase.auth.admin.delete_user(result.data['user']['id'])
        print("✅ Test user cleaned up")
        
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    test_supabase_connection()
```

### 3. Fix Backend Supabase Integration

**Update backend/services/supabase_auth.py:**

```python
# Add better error handling and logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SupabaseAuthService:
    @staticmethod
    async def signup(req: SignupRequest, db: Session):
        """Create a new user account with fallback to local database"""
        try:
            # First try to create user in local database
            existing_user = db.query(models.User).filter(models.User.email == req.email).first()
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists"
                )
            
            # Hash password
            hashed_password = SupabaseAuthService.hash_password(req.password)
            
            # Create user in local database
            user = models.User(
                id=str(uuid.uuid4()),
                email=req.email,
                password_hash=hashed_password,
                full_name=req.full_name,
                college_name=req.college_name,
                program=req.program,
                year_of_study=req.year_of_study
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Try to create user in Supabase if available
            if supabase:
                try:
                    logger.info(f"Attempting to create user in Supabase: {req.email}")
                    
                    # Use admin.create_user() instead of sign_up() for service key
                    supabase_response = supabase.auth.admin.create_user({
                        "email": req.email,
                        "password": req.password,
                        "email_confirm": True,  # Skip email confirmation for immediate visibility
                        "user_metadata": {
                            "full_name": req.full_name,
                            "college_name": req.college_name,
                            "program": req.program,
                            "year_of_study": req.year_of_study
                        }
                    })
                    
                    logger.info(f"✅ Supabase user created successfully: {supabase_response.data['user']['id']}")
                    print(f"✅ Supabase user created successfully: {supabase_response.data['user']['id']}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create user in Supabase: {e}")
                    print(f"❌ Failed to create user in Supabase: {e}")
                    print("⚠️  User will only exist in local database")
                    # Don't fail the signup process - local database user is sufficient
            else:
                logger.warning("⚠️  Supabase client not available - user only in local database")
                print("⚠️  Supabase client not available - user only in local database")
            
            # Generate tokens
            access_token = SupabaseAuthService.create_access_token(data={"sub": user.id})
            refresh_token = SupabaseAuthService.create_refresh_token(data={"sub": user.id})
            
            return UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                college_name=user.college_name,
                program=user.program,
                year_of_study=user.year_of_study,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
        except Exception as e:
            db.rollback()
            logger.error(f"Signup failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Signup failed: {str(e)}"
            )
```

### 4. Add Network Diagnostics

**Create network test script:**
```python
# test_network_connectivity.py
import socket
import ssl
import requests
from urllib.parse import urlparse

def test_dns_resolution(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS resolution: {hostname} -> {ip}")
        return True
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
        return False

def test_https_connection(url):
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"✅ HTTPS connection to {hostname}:{port}")
                return True
    except Exception as e:
        print(f"❌ HTTPS connection failed: {e}")
        return False

def test_supabase_api_direct():
    try:
        response = requests.get(
            "https://cvkvciywqxsktlkigyth.supabase.co/rest/v1/",
            headers={"apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN2a3ZjaXl3cXhza3Rsa2lneXRoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzY5Mjc0OCwiZXhwIjoyMDgzMjY4NzQ4fQ.fvdB7635gvZ6V10LxY8M9MgNX5gUGQjtTf4DAaX84QE"},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Supabase API accessible")
            return True
        else:
            print(f"❌ Supabase API returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Supabase API test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Network Connectivity Tests ===")
    supabase_host = "cvkvciywqxsktlkigyth.supabase.co"
    
    dns_ok = test_dns_resolution(supabase_host)
    https_ok = test_https_connection(f"https://{supabase_host}")
    api_ok = test_supabase_api_direct()
    
    if dns_ok and https_ok and api_ok:
        print("\n✅ All network tests passed")
    else:
        print("\n❌ Network issues detected - check your internet connection and firewall")
```

### 5. Dashboard Verification Checklist

**In Supabase Dashboard:**

1. **Authentication → Users**
   - [ ] Toggle "Show unconfirmed users" 
   - [ ] Check if users appear with email_confirmed_at = NULL
   - [ ] Run SQL: `SELECT * FROM auth.users ORDER BY created_at DESC LIMIT 10;`

2. **Authentication → Providers → Email**
   - [ ] Disable "Enable email confirmations" if you want immediate user visibility
   - [ ] Or keep enabled but check unconfirmed users

3. **Database → Tables → auth.users**
   - [ ] Verify table exists and has proper RLS policies
   - [ ] Check for any failing triggers on auth.users

4. **Settings → API**
   - [ ] Verify your service key is correct
   - [ ] Check project URL matches your .env

### 6. Common Fixes

**Option 1: Fix the hybrid approach (Recommended)**
- Keep local database as primary
- Fix Supabase sync with proper error handling
- Users exist in both places

**Option 2: Go fully Supabase (Alternative)**
- Remove local database auth
- Use Supabase directly from frontend
- Handle all auth in Supabase

**Option 3: Disable Supabase sync (Simplest)**
- Remove Supabase integration entirely
- Use local database only
- Simpler but loses Supabase benefits

### 7. Verification Steps After Fix

1. **Test signup:**
   ```bash
   # Create a test user
   curl -X POST http://localhost:8000/auth/signup \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "Test123456",
       "full_name": "Test User",
       "college_name": "Test College",
       "program": "BTech",
       "year_of_study": 2
     }'
   ```

2. **Check local database:**
   ```sql
   SELECT * FROM users WHERE email = 'test@example.com';
   ```

3. **Check Supabase dashboard:**
   - Refresh Authentication → Users
   - Look for the new user
   - Check if email is confirmed

4. **Test login:**
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "Test123456"
     }'
   ```

### 8. Final Code Snippets

**Improved signup with logging:**
```python
# In your signup handler
async def signup(req: SignupRequest, db: Session = Depends(get_db)):
    logger.info(f"Signup attempt for: {req.email}")
    
    try:
        result = await SupabaseAuthService.signup(req, db)
        logger.info(f"Signup successful for: {req.email}")
        return result
    except Exception as e:
        logger.error(f"Signup failed for {req.email}: {e}")
        raise e
```

**Frontend signup with better error handling:**
```javascript
// In frontend signup page
const handleSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);
  setError('');
  
  try {
    console.log('Attempting signup for:', formData.email);
    
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    
    const data = await response.json();
    console.log('Signup response:', data);
    
    if (response.ok) {
      console.log('✅ Signup successful');
      // Success handling...
    } else {
      console.error('❌ Signup failed:', data);
      setError(data.detail || 'Signup failed');
    }
  } catch (err) {
    console.error('❌ Network error:', err);
    setError('Network error - check console for details');
  } finally {
    setLoading(false);
  }
};
```

## Quick Fix Commands

```bash
# 1. Test current setup
cd backend
python test_supabase_direct.py

# 2. Check network
python test_network_connectivity.py

# 3. Apply fixes to backend
# Update services/supabase_auth.py with improved error handling

# 4. Restart backend
uvicorn main:app --reload

# 5. Test signup
# Use the curl command above or frontend form
```

This approach will make the issue visible and fix the Supabase integration properly.