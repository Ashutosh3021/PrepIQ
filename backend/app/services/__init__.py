# PrepIQ App Services package
#
# Python resolves `app.services` to this package (services/) rather than the
# flat services.py file. PrepIQService lives in services.py, so we re-export
# it here so that `from app.services import PrepIQService` works correctly.
import importlib as _importlib
import sys as _sys
import os as _os

# Load the flat services.py as a separate module to avoid shadowing this package
_flat_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "services.py")
_spec = _importlib.util.spec_from_file_location("app._services_flat", _flat_path)
_flat = _importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_flat)  # type: ignore[union-attr]

PrepIQService = _flat.PrepIQService

from app.services.supabase_first_auth import get_current_user_from_token  # noqa: F401
