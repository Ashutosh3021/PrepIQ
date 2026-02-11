import uvicorn
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the backend directory (where this file is located)
backend_dir = Path(__file__).parent.absolute()

# Add backend to Python path for imports
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Add parent directory to allow absolute imports (app.database, etc.)
parent_dir = backend_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Load environment variables from .env file
env_path = backend_dir / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded environment from {env_path}")
else:
    # Try .env.production as fallback
    env_prod_path = backend_dir / '.env.production'
    if env_prod_path.exists():
        load_dotenv(dotenv_path=env_prod_path, override=True)
        print(f"✅ Loaded environment from {env_prod_path}")
    else:
        load_dotenv()  # Load from system environment
        print("⚠️  No .env file found. Using system environment variables.")

if __name__ == "__main__":
    # Use port 8000 as documented default, but allow override via PORT env var
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"🚀 Starting PrepIQ Backend Server on http://{host}:{port}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    print(f"💓 Health Check: http://{host}:{port}/health")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        workers=1
    )
