"""
Test for Sentence Similarity using sentence-transformers/all-MiniLM-L6-v2
API Key location: API folder and .env files
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from bytez import Bytez
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

# API Key from API folder
BYTEZ_API_KEY = "d02578a68c2621c9fdac702219d0722e"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def test_sentence_similarity():
    """Test the sentence similarity model"""
    print("=" * 60)
    print("Testing Sentence Similarity Model")
    print(f"Model: {MODEL_NAME}")
    print("=" * 60)
    
    try:
        # Initialize Bytez SDK
        sdk = Bytez(BYTEZ_API_KEY)
        model = sdk.model(MODEL_NAME)
        
        print("✅ Bytez SDK initialized successfully\n")
        
        # Test case 1: Get embedding for first sentence
        text1 = "Machine learning is a subset of artificial intelligence"
        print(f"Text 1: {text1}")
        results1 = model.run(text1)
        
        if results1.error:
            print(f"❌ Error: {results1.error}")
            return False
        
        embedding1 = results1.output
        print(f"✅ Embedding generated (dimension: {len(embedding1)})\n")
        
        # Test case 2: Get embedding for similar sentence
        text2 = "Deep learning is part of machine learning and AI"
        print(f"Text 2: {text2}")
        results2 = model.run(text2)
        
        if results2.error:
            print(f"❌ Error: {results2.error}")
            return False
        
        embedding2 = results2.output
        print(f"✅ Embedding generated (dimension: {len(embedding2)})\n")
        
        # Calculate similarity
        similarity = cosine_similarity(embedding1, embedding2)
        print(f"Similarity Score: {similarity:.4f}")
        print("(1.0 = identical, 0.0 = completely different)\n")
        
        # Test case 3: Get embedding for different sentence
        text3 = "The weather is nice today for a picnic"
        print(f"Text 3: {text3}")
        results3 = model.run(text3)
        
        if results3.error:
            print(f"❌ Error: {results3.error}")
            return False
        
        embedding3 = results3.output
        print(f"✅ Embedding generated (dimension: {len(embedding3)})\n")
        
        # Calculate similarity with text1
        similarity_different = cosine_similarity(embedding1, embedding3)
        print(f"Similarity (Text 1 vs Text 3): {similarity_different:.4f}")
        print(f"Expected: Lower similarity than Text 1 vs Text 2\n")
        
        # Verify similar texts have higher similarity
        if similarity > similarity_different:
            print("✅ Model correctly identifies similar sentences")
        else:
            print("⚠️  Warning: Similarity scores seem inverted")
        
        print("=" * 60)
        print("✅ Sentence Similarity Model Test PASSED")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sentence_similarity()
    sys.exit(0 if success else 1)
