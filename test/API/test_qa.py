"""
Test for Bytez Q&A Model (roberta-base-squad2)
API Key location: API/- for Q&A.txt and .env files
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
MODEL_NAME = "deepset/roberta-base-squad2"

def test_qa():
    """Test the Q&A model with context and questions"""
    print("=" * 60)
    print("Testing Bytez Q&A Model")
    print(f"Model: {MODEL_NAME}")
    print("=" * 60)
    
    try:
        # Initialize Bytez SDK
        sdk = Bytez(BYTEZ_API_KEY)
        model = sdk.model(MODEL_NAME)
        
        print("✅ Bytez SDK initialized successfully\n")
        
        # Test case 1: Simple Q&A
        context1 = "My name is Simon and I live in London. I work as a software engineer at a tech company."
        question1 = "Where do I live?"
        
        print(f"Context: {context1}")
        print(f"Question: {question1}")
        
        results1 = model.run({
            "context": context1,
            "question": question1
        })
        
        if results1.error:
            print(f"❌ Error: {results1.error}")
            return False
        
        print(f"✅ Answer: {results1.output}\n")
        
        # Test case 2: Different question
        question2 = "What is my name?"
        print(f"Question: {question2}")
        
        results2 = model.run({
            "context": context1,
            "question": question2
        })
        
        if results2.error:
            print(f"❌ Error: {results2.error}")
            return False
        
        print(f"✅ Answer: {results2.output}\n")
        
        # Test case 3: Technical context
        context3 = "Python is a high-level programming language. It was created by Guido van Rossum and first released in 1991. Python is known for its readable syntax."
        question3 = "Who created Python?"
        
        print(f"Context: {context3}")
        print(f"Question: {question3}")
        
        results3 = model.run({
            "context": context3,
            "question": question3
        })
        
        if results3.error:
            print(f"❌ Error: {results3.error}")
            return False
        
        print(f"✅ Answer: {results3.output}\n")
        
        print("=" * 60)
        print("✅ Q&A Model Test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_qa()
    sys.exit(0 if success else 1)
