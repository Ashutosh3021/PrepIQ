import sys
import os
import time

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_model_availability():
    """Test which models are available and working"""
    print("=== PrepIQ Local Models Availability Test ===")
    
    try:
        print("1. Testing import...")
        start_time = time.time()
        
        # Test import
        from app.ml.external_api_wrapper import ExternalAPIWrapper
        import_time = time.time() - start_time
        print(f"✓ ExternalAPIWrapper class imported successfully ({import_time:.2f}s)")
        
        print("\n2. Testing instance creation...")
        instance_start = time.time()
        
        # Create instance (this will trigger model loading)
        api = ExternalAPIWrapper()
        instance_time = time.time() - instance_start
        print(f"✓ API instance created successfully ({instance_time:.2f}s)")
        
        print("\n3. Testing basic method availability...")
        
        # Test that all methods exist
        required_methods = [
            'question_answering',
            'text_summarization', 
            'text_classification',
            'text_generation',
            'sentence_similarity',
            'translation',
            'chat',
            'image_captioning',
            'question_answering_async',
            'text_summarization_async',
            'text_classification_async', 
            'text_generation_async',
            'sentence_similarity_async',
            'translation_async',
            'chat_async',
            'image_captioning_async'
        ]
        
        missing_methods = []
        available_methods = []
        
        for method_name in required_methods:
            if hasattr(api, method_name):
                available_methods.append(method_name)
            else:
                missing_methods.append(method_name)
        
        print(f"Available methods: {len(available_methods)}/{len(required_methods)}")
        if available_methods:
            print("  Methods found:")
            for method in sorted(available_methods):
                print(f"    ✓ {method}")
        
        if missing_methods:
            print("  Missing methods:")
            for method in sorted(missing_methods):
                print(f"    ✗ {method}")
        
        print("\n4. Testing basic functionality...")
        
        # Quick functionality tests
        test_results = []
        
        # Test 1: Simple QA
        try:
            qa_start = time.time()
            qa_result = api.question_answering("The sky is blue", "What color is the sky?")
            qa_time = time.time() - qa_start
            qa_success = qa_result.get('success', False) if isinstance(qa_result, dict) else False
            test_results.append(("Question Answering", qa_success, qa_time, qa_result))
            print(f"✓ QA test: {'PASS' if qa_success else 'FAIL'} ({qa_time:.2f}s)")
        except Exception as e:
            test_results.append(("Question Answering", False, 0, {"error": str(e)}))
            print(f"✗ QA test: ERROR - {e}")
        
        # Test 2: Simple classification
        try:
            class_start = time.time()
            class_result = api.text_classification("Good results today")
            class_time = time.time() - class_start
            class_success = class_result.get('success', False) if isinstance(class_result, dict) else False
            test_results.append(("Text Classification", class_success, class_time, class_result))
            print(f"✓ Classification test: {'PASS' if class_success else 'FAIL'} ({class_time:.2f}s)")
        except Exception as e:
            test_results.append(("Text Classification", False, 0, {"error": str(e)}))
            print(f"✗ Classification test: ERROR - {e}")
        
        # Test 3: Simple similarity
        try:
            sim_start = time.time()
            sim_result = api.sentence_similarity(["hello", "hi"])
            sim_time = time.time() - sim_start
            sim_success = sim_result.get('success', False) if isinstance(sim_result, dict) else False
            test_results.append(("Sentence Similarity", sim_success, sim_time, sim_result))
            print(f"✓ Similarity test: {'PASS' if sim_success else 'FAIL'} ({sim_time:.2f}s)")
        except Exception as e:
            test_results.append(("Sentence Similarity", False, 0, {"error": str(e)}))
            print(f"✗ Similarity test: ERROR - {e}")
        
        print("\n" + "="*60)
        print("FINAL RESULTS SUMMARY")
        print("="*60)
        
        # Summary statistics
        total_tests = len(test_results)
        passed_tests = sum(1 for _, success, _, _ in test_results if success)
        failed_tests = total_tests - passed_tests
        
        print(f"Method Availability: {len(available_methods)}/{len(required_methods)} methods found")
        print(f"Functionality Tests: {passed_tests}/{total_tests} tests passed")
        
        if missing_methods:
            print(f"\nMissing Methods ({len(missing_methods)}):")
            for method in missing_methods:
                print(f"  - {method}")
        
        print(f"\nTest Details:")
        for test_name, success, exec_time, result in test_results:
            status = "✓ PASS" if success else "✗ FAIL"
            time_str = f"{exec_time:.2f}s" if exec_time > 0 else "N/A"
            print(f"  {status} {test_name}: {time_str}")
            if not success and 'error' in result:
                print(f"    Error: {result['error']}")
            elif success and 'output' in result:
                output_str = str(result['output'])
                if len(output_str) > 50:
                    output_str = output_str[:50] + "..."
                print(f"    Output: {output_str}")
        
        # Overall assessment
        print(f"\n" + "="*60)
        method_coverage = len(available_methods) / len(required_methods)
        test_success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        if method_coverage == 1.0 and test_success_rate == 1.0:
            print("🎉 EXCELLENT: All methods available and all tests passing!")
        elif method_coverage >= 0.8 and test_success_rate >= 0.8:
            print("✅ GOOD: Most methods available and most tests passing!")
        elif method_coverage >= 0.5 or test_success_rate >= 0.5:
            print("⚠ FAIR: Some methods working, but issues present!")
        else:
            print("❌ POOR: Critical issues detected!")
        
        print("="*60)
        
        return len(available_methods) > 0 and passed_tests > 0
        
    except Exception as e:
        print(f"✗ Critical error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("Starting PrepIQ local models availability test...")
    print("This will check if your local AI models are properly installed and accessible.\n")
    
    success = test_model_availability()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("Your PrepIQ local AI integration appears to be working.")
    else:
        print("\n❌ Test completed with issues.")
        print("Please check your installation and dependencies.")
    
    return success

if __name__ == "__main__":
    main()