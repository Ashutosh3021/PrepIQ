"""
Signup validation helpers (Phase 2).

Password rules (enforced on signup):
  - length >= 8
  - at least one uppercase letter (A-Z)
  - at least one lowercase letter (a-z)
  - at least one digit (0-9)
  - at least one special character from: !@#$%^&*()_+-=[]{}|;:',.<>?/`~

Email: standard format check (local@domain.tld).
"""
from __future__ import annotations

import re
from typing import List, Tuple

SPECIAL_CHARS = set("!@#$%^&*()_+-=[]{}|;:',.<>?/`~")
SPECIAL_CHARS_DISPLAY = "!@#$%^&*()_+-=[]{}|;:',.<>?/`~"

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)


def validate_email(email: str) -> Tuple[bool, str]:
    if not email or not isinstance(email, str):
        return False, "Email is required"
    email = email.strip()
    if len(email) > 254:
        return False, "Email is too long"
    if not _EMAIL_RE.match(email):
        return False, "Invalid email format"
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    if not password or not isinstance(password, str):
        return False, "Password is required"
    errors: List[str] = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("one digit")
    if not any(c in SPECIAL_CHARS for c in password):
        errors.append(f"one special character ({SPECIAL_CHARS_DISPLAY})")
    if errors:
        return False, "Password must contain " + "; ".join(errors)
    return True, ""
