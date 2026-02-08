
import sys
import os
import asyncio

# Add current directory to path
sys.path.append(os.getcwd())

from app.routers.dashboard import get_dashboard_stats
from app.database import SessionLocal
from fastapi import HTTPException

# Mock user
mock_user = {"id": "test_user_id", "email": "test@example.com"}

# Get DB session
db = SessionLocal()

async def run_test():
    try:
        print("Calling get_dashboard_stats with mock user...")
        result = await get_dashboard_stats(current_user=mock_user, db=db)
        print("Success!")
        print(result)
    except HTTPException as e:
        print(f"Caught HTTPException: {e.detail}")
    except Exception as e:
        import traceback
        print(f"Caught Exception: {str(e)}")
        print(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_test())
