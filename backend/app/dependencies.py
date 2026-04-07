from functools import lru_cache
from app.database import get_db

@lru_cache()
def get_prepiq_service():
    from app.services import PrepIQService
    return PrepIQService()
