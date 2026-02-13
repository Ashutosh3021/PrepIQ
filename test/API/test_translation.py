"""
Test for Translation using Gemini 2.5 Flash with prompting
API Key location: .env file (GEMINI_API_KEY)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_translation():
    """Test translation using Gemini 2.5 Flash"""
    print("=" * 60)
    print("Testing Translation with Gemini 2.5 Flash")
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
        
        # Test case 1: English to Spanish
        text1 = "Hello, how are you today? I hope you're having a great day."
        print(f"English: {text1}")
        
        prompt1 = f"Translate the following English text to Spanish:\n\n{text1}"
        response1 = model.generate_content(prompt1)
        print(f"Spanish: {response1.text}\n")
        
        # Test case 2: English to French
        text2 = "The weather is beautiful today. Let's go for a walk in the park."
        print(f"English: {text2}")
        
        prompt2 = f"Translate the following English text to French:\n\n{text2}"
        response2 = model.generate_content(prompt2)
        print(f"French: {response2.text}\n")
        
        # Test case 3: English to German
        text3 = "Thank you very much for your help. I really appreciate it."
        print(f"English: {text3}")
        
        prompt3 = f"Translate the following English text to German:\n\n{text3}"
        response3 = model.generate_content(prompt3)
        print(f"German: {response3.text}\n")
        
        # Test case 4: Technical translation
        text4 = "Machine learning algorithms can analyze large datasets to find patterns."
        print(f"English: {text4}")
        
        prompt4 = f"Translate the following English text to Hindi:\n\n{text4}"
        response4 = model.generate_content(prompt4)
        print(f"Hindi: {response4.text}\n")
        
        print("=" * 60)
        print("✅ Translation Test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_translation()
    sys.exit(0 if success else 1)
