"""
Test for Text Summarization using Gemini 2.5 Flash with prompting
API Key location: .env file (GEMINI_API_KEY)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_summarization():
    """Test text summarization using Gemini 2.5 Flash"""
    print("=" * 60)
    print("Testing Text Summarization with Gemini 2.5 Flash")
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
        
        # Test case 1: News article summary
        text1 = """The tower is 324 metres (1,063 ft) tall, about the same height as an 81-storey building, 
        and the tallest structure in Paris. Its base is square, measuring 125 metres (410 ft) on each side. 
        It was the first structure to reach a height of 300 metres. Excluding transmitters, the Eiffel Tower 
        is the second tallest free-standing structure in France after the Millau Viaduct. The tower has three 
        levels for visitors, with restaurants on the first and second levels. The top level's upper platform 
        is 276 m (906 ft) above the ground."""
        
        print("Test 1: Summarize News Article")
        print(f"Original text length: {len(text1)} characters")
        
        prompt1 = f"Summarize the following text in 2-3 sentences:\n\n{text1}"
        response1 = model.generate_content(prompt1)
        
        print(f"Summary: {response1.text}")
        print(f"Summary length: {len(response1.text)} characters\n")
        
        # Test case 2: Technical documentation
        text2 = """Python is a high-level, interpreted programming language. It was created by Guido van Rossum 
        and first released in 1991. Python's design philosophy emphasizes code readability with its notable use 
        of significant whitespace. Its language constructs and object-oriented approach aim to help programmers 
        write clear, logical code for small and large-scale projects. Python is dynamically typed and 
        garbage-collected. It supports multiple programming paradigms, including structured, object-oriented, 
        and functional programming."""
        
        print("Test 2: Summarize Technical Documentation")
        print(f"Original text length: {len(text2)} characters")
        
        prompt2 = f"Provide a brief summary of this technical text:\n\n{text2}"
        response2 = model.generate_content(prompt2)
        
        print(f"Summary: {response2.text}")
        print(f"Summary length: {len(response2.text)} characters\n")
        
        # Test case 3: Bullet point summary
        text3 = """Machine learning is transforming industries across the globe. In healthcare, it helps doctors 
        diagnose diseases faster and more accurately. In finance, algorithms detect fraud and predict market trends. 
        In transportation, self-driving cars use ML to navigate roads safely. In education, personalized learning 
        systems adapt to individual student needs. In agriculture, farmers use ML to optimize crop yields and predict 
        weather patterns. The technology continues to evolve and impact more sectors every day."""
        
        print("Test 3: Bullet Point Summary")
        print(f"Original text length: {len(text3)} characters")
        
        prompt3 = f"Summarize the following text as 3-4 bullet points:\n\n{text3}"
        response3 = model.generate_content(prompt3)
        
        print(f"Summary:\n{response3.text}\n")
        
        print("=" * 60)
        print("✅ Summarization Test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_summarization()
    sys.exit(0 if success else 1)
