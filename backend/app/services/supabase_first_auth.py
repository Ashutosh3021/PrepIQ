"""
DEPRECATED (Phase 2).

This module previously implemented Supabase-first auth.
It now re-exports Pyronites email/password auth so legacy imports continue to work:

  from app.services.supabase_first_auth import get_current_user_from_token

New code should import from app.services.pyronites_auth directly.
OAuth (Google/GitHub) is removed — email + password only.
"""
from app.services.pyronites_auth import (  # noqa: F401
    PyronitesAuthService as SupabaseFirstAuthService,
    SignupRequest,
    LoginRequest,
    UserResponse,
    get_current_user_from_token,
)
