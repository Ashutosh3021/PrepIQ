"""
Test for Text Classification using distilbert-base-uncased-finetuned-sst-2-english
API Key location: API folder and .env files
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from bytez import Bytez
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Key from API folder
BYTEZ_API_KEY = "d02578a68c2621c9fdac702219d0722e"
MODEL_NAME = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"

def test_text_classification():
    """Test the text classification model for sentiment analysis"""
    print("=" * 60)
    print("Testing Text Classification Model")
    print(f"Model: {MODEL_NAME}")
    print("=" * 60)
    
    try:
        # Initialize Bytez SDK
        sdk = Bytez(BYTEZ_API_KEY)
        model = sdk.model(MODEL_NAME)
        
        print("✅ Bytez SDK initialized successfully\n")
        
        # Test case 1: Positive sentiment
        text1 = "I love this product! It's absolutely amazing and works perfectly."
        print(f"Text: {text1}")
        results1 = model.run(text1)
        
        if results1.error:
            print(f"❌ Error: {results1.error}")
            return False
        
        print(f"✅ Classification: {results1.output}\n")
        
        # Test case 2: Negative sentiment
        text2 = "This is terrible. I hate it and it doesn't work at all."
        print(f"Text: {text2}")
        results2 = model.run(text2)
        
        if results2.error:
            print(f"❌ Error: {results2.error}")
            return False
        
        print(f"✅ Classification: {results2.output}\n")
        
        # Test case 3: Neutral sentiment
        text3 = "The weather is cloudy today."
        print(f"Text: {text3}")
        results3 = model.run(text3)
        
        if results3.error:
            print(f"❌ Error: {results3.error}")
            return False
        
        print(f"✅ Classification: {results3.output}\n")
        
        # Test case 4: Mixed sentiment
        text4 = "The movie was okay, not great but not bad either."
        print(f"Text: {text4}")
        results4 = model.run(text4)
        
        if results4.error:
            print(f"❌ Error: {results4.error}")
            return False
        
        print(f"✅ Classification: {results4.output}\n")
        
        print("=" * 60)
        print("✅ Text Classification Model Test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_text_classification()
    sys.exit(0 if success else 1)
