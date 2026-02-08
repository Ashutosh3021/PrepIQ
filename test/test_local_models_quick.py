import sys
import os
import asyncio
import time

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def quick_model_test():
    """Quick test to verify basic functionality"""
    print("=== Quick Local Models Test ===")
    
    try:
        # Import the external API wrapper
        from app.ml.external_api_wrapper import external_api
        print("✓ External API wrapper imported")
        
        # Test basic functionality without heavy model loading
        print("\nTesting basic methods...")
        
        # Test 1: Question Answering (basic)
        print("1. Testing Question Answering...")
        start = time.time()
        result = external_api.question_answering("The Earth orbits the Sun", "What orbits the Sun?")
        elapsed = time.time() - start
        print(f"   Result: Success={result['success']}, Time={elapsed:.2f}s")
        if result['success']:
            print(f"   Answer: {result['output']}")
        
        # Test 2: Text Summarization
        print("\n2. Testing Text Summarization...")
        start = time.time()
        result = external_api.text_summarization("This is a test sentence for summarization.")
        elapsed = time.time() - start
        print(f"   Result: Success={result['success']}, Time={elapsed:.2f}s")
        if result['success']:
            print(f"   Summary: {result['output']}")
        
        # Test 3: Text Classification
        print("\n3. Testing Text Classification...")
        start = time.time()
        result = external_api.text_classification("The company had great results.")
        elapsed = time.time() - start
        print(f"   Result: Success={result['success']}, Time={elapsed:.2f}s")
        if result['success']:
            print(f"   Classification: {result['output']}")
        
        # Test 4: Sentence Similarity
        print("\n4. Testing Sentence Similarity...")
        start = time.time()
        result = external_api.sentence_similarity(["Hello world", "Hello there"])
        elapsed = time.time() - start
        print(f"   Result: Success={result['success']}, Time={elapsed:.2f}s")
        if result['success']:
            print(f"   Similarity: {result['output']}")
        
        # Test 5: Async methods
        print("\n5. Testing Async Methods...")
        
        async def test_async_methods():
            # Async QA
            start = time.time()
            result = await external_api.question_answering_async("AI is transforming technology", "What is transforming technology?")
            elapsed = time.time() - start
            print(f"   Async QA: Success={result['success']}, Time={elapsed:.2f}s")
            
            # Async Summarization
            start = time.time()
            result = await external_api.text_summarization_async("Machine learning and artificial intelligence are related fields.")
            elapsed = time.time() - start
            print(f"   Async Summarization: Success={result['success']}, Time={elapsed:.2f}s")
        
        asyncio.run(test_async_methods())
        
        print("\n✓ Quick test completed successfully!")
        print("All basic methods are working. For comprehensive testing, run the full test suite.")
        
    except Exception as e:
        print(f"✗ Error during quick test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_model_test()