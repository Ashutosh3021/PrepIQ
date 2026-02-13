"""
Test for Text Generation using Gemini 2.5 Flash with prompting
API Key location: .env file (GEMINI_API_KEY)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_text_generation():
    """Test text generation using Gemini 2.5 Flash"""
    print("=" * 60)
    print("Testing Text Generation with Gemini 2.5 Flash")
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
        
        # Test case 1: Creative story
        prompt1 = "Write a short story (3-4 sentences) about a robot learning to paint."
        print(f"Prompt: {prompt1}")
        response1 = model.generate_content(prompt1)
        print(f"Generated:\n{response1.text}\n")
        
        # Test case 2: Technical explanation
        prompt2 = "Explain how blockchain works in simple terms for a beginner."
        print(f"Prompt: {prompt2}")
        response2 = model.generate_content(prompt2)
        print(f"Generated:\n{response2.text}\n")
        
        # Test case 3: List generation
        prompt3 = "Generate 5 creative ideas for a mobile app that helps students study."
        print(f"Prompt: {prompt3}")
        response3 = model.generate_content(prompt3)
        print(f"Generated:\n{response3.text}\n")
        
        # Test case 4: Code generation
        prompt4 = "Write a Python function to calculate the factorial of a number with comments."
        print(f"Prompt: {prompt4}")
        response4 = model.generate_content(prompt4)
        print(f"Generated:\n{response4.text}\n")
        
        print("=" * 60)
        print("✅ Text Generation Test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_text_generation()
    sys.exit(0 if success else 1)
