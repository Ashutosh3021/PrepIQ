"""
Test script to verify all Bytez models are working correctly
Run this after starting the server to test all 8 models
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.ml.external_api_wrapper import get_external_api
import json

def test_all_models():
    """Test all 8 Bytez models"""
    print("=" * 60)
    print("Testing Bytez Models Integration")
    print("=" * 60)
    
    api = get_external_api()
    
    if not api.bytez_sdk:
        print("❌ Bytez SDK not initialized!")
        print("Please install: pip install bytez")
        return False
    
    print("✅ Bytez SDK initialized successfully\n")
    
    results = {}
    
    # Test 1: Question Answering
    print("1. Testing Question Answering...")
    try:
        result = api.question_answering(
            context="Python is a high-level programming language. It was created by Guido van Rossum.",
            question="Who created Python?"
        )
        results['qa'] = result['success']
        print(f"   {'✅' if result['success'] else '❌'} QA: {result.get('output', 'N/A')[:50]}...")
    except Exception as e:
        results['qa'] = False
        print(f"   ❌ QA Error: {e}")
    
    # Test 2: Text Summarization
    print("\n2. Testing Text Summarization...")
    try:
        long_text = "Python is a high-level, interpreted programming language. It was created by Guido van Rossum and first released in 1991. Python's design philosophy emphasizes code readability with its notable use of significant whitespace. Its language constructs and object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects."
        result = api.text_summarization(long_text)
        results['summarization'] = result['success']
        print(f"   {'✅' if result['success'] else '❌'} Summarization: {result.get('output', 'N/A')[:50]}...")
    except Exception as e:
        results['summarization'] = False
        print(f"   ❌ Summarization Error: {e}")
    
    # Test 3: Text Classification
    print("\n3. Testing Text Classification...")
    try:
        result = api.text_classification("This is a positive review about a great product!")
        results['classification'] = result['success']
        print(f"   {'✅' if result['success'] else '❌'} Classification: {result.get('output', {})}")
    except Exception as e:
        results['classification'] = False
        print(f"   ❌ Classification Error: {e}")
    
    # Test 4: Text Generation
    print("\n4. Testing Text Generation...")
    try:
        result = api.text_generation("The future of AI is", max_length=50)
        results['generation'] = result['success']
        print(f"   {'✅' if result['success'] else '❌'} Generation: {result.get('output', 'N/A')[:50]}...")
    except Exception as e:
        results['generation'] = False
        print(f"   ❌ Generation Error: {e}")
    
    # Test 5: Sentence Similarity
    print("\n5. Testing Sentence Similarity...")
    try:
        result = api.sentence_similarity([
            "Python is a programming language",
            "Python is used for software development"
        ])
        results['similarity'] = result['success']
        similarity_score = result.get('output', [0])[0] if result.get('output') else 0
        print(f"   {'✅' if result['success'] else '❌'} Similarity Score: {similarity_score:.3f}")
    except Exception as e:
        results['similarity'] = False
        print(f"   ❌ Similarity Error: {e}")
    
    # Test 6: Translation
    print("\n6. Testing Translation...")
    try:
        result = api.translation("Hello, how are you?", source_lang="en", target_lang="es")
        results['translation'] = result['success']
        print(f"   {'✅' if result['success'] else '❌'} Translation: {result.get('output', 'N/A')}")
    except Exception as e:
        results['translation'] = False
        print(f"   ❌ Translation Error: {e}")
    
    # Test 7: Chat
    print("\n7. Testing Chat...")
    try:
        result = api.chat([
            {"role": "user", "content": "Hello, what can you do?"}
        ])
        results['chat'] = result['success']
        print(f"   {'✅' if result['success'] else '❌'} Chat Response: {result.get('output', 'N/A')[:50]}...")
    except Exception as e:
        results['chat'] = False
        print(f"   ❌ Chat Error: {e}")
    
    # Test 8: Image Captioning
    print("\n8. Testing Image Captioning...")
    try:
        # Using a test image URL
        result = api.image_captioning("https://ocean.si.edu/sites/default/files/styles/3_2_largest/public/2023-11/Screen_Shot_2018-04-16_at_1_42_56_PM.png.webp")
        results['image_captioning'] = result['success']
        print(f"   {'✅' if result['success'] else '❌'} Caption: {result.get('output', 'N/A')[:50]}...")
    except Exception as e:
        results['image_captioning'] = False
        print(f"   ❌ Image Captioning Error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for model, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{model.upper():20} {status}")
    
    print(f"\nTotal: {passed}/{total} models working")
    
    if passed == total:
        print("\n🎉 All models are working perfectly with Bytez!")
        return True
    else:
        print(f"\n⚠️  {total - passed} model(s) need attention")
        return False

if __name__ == "__main__":
    success = test_all_models()
    sys.exit(0 if success else 1)
