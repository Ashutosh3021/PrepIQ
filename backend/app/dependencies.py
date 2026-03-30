from functools import lru_cache
from .services import PrepIQService

@lru_cache()
def get_prepiq_service() -> PrepIQService:
    return PrepIQService()
