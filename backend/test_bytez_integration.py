
import sys
import os
import asyncio
import logging

# Add current directory to path
sys.path.append(os.getcwd())

# Mock the bytez module if not installed to avoid ImportErrors during local testing environment checks
# But we want to test the wrapper logic, so we'll try to import the real one if available.
try:
    import bytez
    print("Bytez module found.")
except ImportError:
    print("Bytez module not found. Installing...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "bytez"])
        import bytez
        print("Bytez installed successfully.")
    except Exception as e:
        print(f"Failed to install bytez: {e}")

from app.ml.external_api_wrapper import get_external_api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bytez_models():
    api = get_external_api()
    if not api:
        print("Failed to initialize ExternalAPIWrapper")
        return

    print("Testing Bytez Integration...")

    # Test 1: Chat
    print("\n--- Testing Chat ---")
    messages = [{"role": "user", "content": "Hello, who are you?"}]
    try:
        result = api.chat(messages)
        print(f"Chat Result: {result}")
    except Exception as e:
        print(f"Chat Failed: {e}")

    # Test 2: Text Generation
    print("\n--- Testing Text Generation ---")
    try:
        result = api.text_generation("Once upon a time")
        print(f"Generation Result: {result}")
    except Exception as e:
        print(f"Generation Failed: {e}")

    # Test 3: Translation
    print("\n--- Testing Translation ---")
    try:
        result = api.translation("Hello world", target_lang="es")
        print(f"Translation Result: {result}")
    except Exception as e:
        print(f"Translation Failed: {e}")

    # Test 4: Sentence Similarity
    print("\n--- Testing Sentence Similarity ---")
    try:
        result = api.sentence_similarity(["The cat sits safely", "The cat is safe"])
        print(f"Similarity Result: {result}")
    except Exception as e:
        print(f"Similarity Failed: {e}")
        
    print("\nTests Completed.")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_bytez_models())
