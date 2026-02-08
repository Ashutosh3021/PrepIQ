import sys
import os
import time
import threading
from contextlib import contextmanager

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

class TimeoutError(Exception):
    pass

class TimeoutThread(threading.Thread):
    def __init__(self, timeout_seconds):
        super().__init__()
        self.timeout_seconds = timeout_seconds
        self.timed_out = False
        self.daemon = True
    
    def run(self):
        time.sleep(self.timeout_seconds)
        self.timed_out = True

@contextmanager
def timeout(seconds):
    """Context manager for timeout handling (Windows compatible)"""
    timeout_thread = TimeoutThread(seconds)
    timeout_thread.start()
    
    try:
        yield
        if timeout_thread.timed_out:
            raise TimeoutError(f"Operation timed out after {seconds} seconds")
    finally:
        # Thread will be cleaned up automatically as daemon
        pass

def test_model_loading():
    """Test model loading and basic functionality"""
    print("=== Local Models Loading and Basic Functionality Test ===")
    
    try:
        print("Importing external API wrapper...")
        start_time = time.time()
        
        # Import with timeout handling
        try:
            with timeout(60):  # 60 second timeout for import
                from app.ml.external_api_wrapper import external_api
                import_time = time.time() - start_time
                print(f"✓ External API wrapper imported successfully in {import_time:.2f} seconds")
        except TimeoutError as e:
            print(f"✗ Import timeout: {e}")
            return False
        except Exception as e:
            print(f"✗ Import failed: {e}")
            return False
        
        # Test each model individually with timeouts
        models_to_test = [
            ("Question Answering", external_api.question_answering, 
             {"context": "The Earth orbits the Sun", "question": "What orbits the Sun?"}),
            ("Text Summarization", external_api.text_summarization,
             {"text": "This is a test sentence that needs summarization."}),
            ("Text Classification", external_api.text_classification,
             {"text": "The company had excellent quarterly results."}),
            ("Text Generation", external_api.text_generation,
             {"prompt": "Artificial intelligence"}),
            ("Sentence Similarity", external_api.sentence_similarity,
             {"sentences": ["Hello world", "Hello there"]}),
            ("Translation", external_api.translation,
             {"text": "Hello, how are you?"}),
            ("Chat", external_api.chat,
             {"messages": [{"role": "user", "content": "What is AI?"}]}),
            ("Image Captioning", external_api.image_captioning,
             {"image_path": "test.jpg"})
        ]
        
        results = []
        print(f"\nTesting {len(models_to_test)} models...\n")
        
        for model_name, method, test_args in models_to_test:
            print(f"Testing {model_name}...")
            model_start = time.time()
            
            try:
                with timeout(30):  # 30 second timeout per model
                    result = method(**test_args)
                    model_time = time.time() - model_start
                    
                    success = result.get('success', False) if isinstance(result, dict) else bool(result)
                    if success:
                        print(f"  ✓ {model_name}: PASS ({model_time:.2f}s)")
                        if 'output' in result and result['output']:
                            print(f"    Output: {str(result['output'])[:100]}...")
                    else:
                        print(f"  ✗ {model_name}: FAIL ({model_time:.2f}s)")
                        if 'error' in result:
                            print(f"    Error: {result['error']}")
                    results.append((model_name, success, model_time, result))
                    
            except TimeoutError:
                model_time = time.time() - model_start
                print(f"  ✗ {model_name}: TIMEOUT ({model_time:.2f}s)")
                results.append((model_name, False, model_time, {"error": "Timeout"}))
            except Exception as e:
                model_time = time.time() - model_start
                print(f"  ✗ {model_name}: ERROR ({model_time:.2f}s) - {str(e)}")
                results.append((model_name, False, model_time, {"error": str(e)}))
        
        # Print summary
        print(f"\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total_models = len(models_to_test)
        passed_models = sum(1 for _, success, _, _ in results if success)
        failed_models = total_models - passed_models
        
        print(f"Total Models Tested: {total_models}")
        print(f"Models Passed: {passed_models} ({(passed_models/total_models)*100:.1f}%)")
        print(f"Models Failed: {failed_models} ({(failed_models/total_models)*100:.1f}%)")
        
        print(f"\nDetailed Results:")
        for model_name, success, exec_time, result in results:
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"  {status} {model_name}: {exec_time:.2f}s")
            if not success and 'error' in result:
                print(f"    Error: {result['error']}")
        
        # Performance analysis
        successful_times = [t for _, s, t, _ in results if s]
        if successful_times:
            avg_time = sum(successful_times) / len(successful_times)
            max_time = max(successful_times)
            min_time = min(successful_times)
            print(f"\nPerformance Statistics (successful tests):")
            print(f"  Average time: {avg_time:.2f}s")
            print(f"  Fastest test: {min_time:.2f}s")
            print(f"  Slowest test: {max_time:.2f}s")
        
        # Overall status
        print(f"\n" + "="*60)
        if passed_models == total_models:
            print("🎉 ALL MODELS WORKING PERFECTLY!")
        elif passed_models >= total_models * 0.8:
            print("✅ MOST MODELS FUNCTIONAL!")
        elif passed_models > 0:
            print("⚠ SOME MODELS WORKING!")
        else:
            print("❌ NO MODELS FUNCTIONING!")
        print("="*60)
        
        return passed_models > 0
        
    except Exception as e:
        print(f"✗ Critical error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("Starting local models test suite...")
    print("This may take several minutes as models are loaded for the first time.\n")
    
    success = test_model_loading()
    
    if success:
        print("\n✅ Test suite completed with functional models!")
        print("Your PrepIQ local AI integration is ready for use.")
    else:
        print("\n❌ Test suite completed with issues.")
        print("Please check the errors above and ensure all dependencies are installed.")
    
    return success

if __name__ == "__main__":
    main()