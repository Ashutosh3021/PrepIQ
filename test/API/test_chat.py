"""
Test for Chat using Gemini 2.5 Flash
API Key location: .env file (GEMINI_API_KEY)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_chat():
    """Test chat functionality with Gemini 2.5 Flash"""
    print("=" * 60)
    print("Testing Chat with Gemini 2.5 Flash")
    print("=" * 60)
    
    try:
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Error: GEMINI_API_KEY not found in environment variables")
            return False
        
        # Initialize Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        print("✅ Gemini API initialized successfully\n")
        
        # Test 1: Simple greeting
        print("Test 1: Simple Greeting")
        print("-" * 60)
        chat = model.start_chat(history=[])
        response1 = chat.send_message("Hello! How are you today?")
        print(f"User: Hello! How are you today?")
        print(f"Assistant: {response1.text}\n")
        
        # Test 2: Follow-up question (context retention)
        print("Test 2: Follow-up Question")
        print("-" * 60)
        response2 = chat.send_message("Can you explain what machine learning is?")
        print(f"User: Can you explain what machine learning is?")
        print(f"Assistant: {response2.text}\n")
        
        # Test 3: Programming question
        print("Test 3: Programming Question")
        print("-" * 60)
        response3 = chat.send_message("How do I create a list in Python?")
        print(f"User: How do I create a list in Python?")
        print(f"Assistant: {response3.text}\n")
        
        # Test 4: Multi-turn conversation
        print("Test 4: Multi-turn Conversation")
        print("-" * 60)
        response4 = chat.send_message("What are some good use cases for it?")
        print(f"User: What are some good use cases for it?")
        print(f"Assistant: {response4.text}\n")
        
        print("=" * 60)
        print("✅ Chat Test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_chat()
    sys.exit(0 if success else 1)
