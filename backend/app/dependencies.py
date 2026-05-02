import threading

# Thread-safe singleton for PrepIQService
_service_instance = None
_service_lock = threading.Lock()


def get_prepiq_service():
    """
    Return the shared PrepIQService singleton.

    Uses a double-checked locking pattern so that:
    - Only one instance is ever created, even under concurrent first requests.
    - After the first creation, subsequent calls are lock-free (fast path).
    """
    global _service_instance
    if _service_instance is None:
        with _service_lock:
            # Re-check inside the lock to handle the race between the outer
            # None check and acquiring the lock.
            if _service_instance is None:
                from app.services import PrepIQService
                _service_instance = PrepIQService()
    return _service_instance
