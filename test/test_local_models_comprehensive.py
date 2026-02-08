import sys
import os
import asyncio
import time
from typing import Dict, Any, List

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

class ModelTestResult:
    """Class to store individual test results"""
    def __init__(self, model_name: str, method_name: str, test_type: str):
        self.model_name = model_name
        self.method_name = method_name
        self.test_type = test_type  # 'sync' or 'async'
        self.success = False
        self.output = None
        self.error = None
        self.execution_time = 0.0
        self.details = ""

    def __str__(self):
        status = "✓ PASS" if self.success else "✗ FAIL"
        return f"{status} | {self.model_name} | {self.method_name} ({self.test_type}) | {self.execution_time:.2f}s"

class ComprehensiveModelTester:
    """Comprehensive tester for all local AI models"""
    
    def __init__(self):
        self.results: List[ModelTestResult] = []
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test environment and import required modules"""
        print("=== PrepIQ Local Models Comprehensive Test Suite ===")
        print("Setting up test environment...")
        
        try:
            # Import the external API wrapper
            from app.ml.external_api_wrapper import external_api
            self.api = external_api
            print("✓ External API wrapper imported successfully")
        except Exception as e:
            print(f"✗ Failed to import external API wrapper: {e}")
            raise
    
    def run_test(self, model_name: str, method_name: str, test_func, *args, **kwargs):
        """Run a single test and record results"""
        result = ModelTestResult(model_name, method_name, 'sync')
        start_time = time.time()
        
        try:
            output = test_func(*args, **kwargs)
            result.execution_time = time.time() - start_time
            result.output = output
            result.success = output.get('success', False) if isinstance(output, dict) else bool(output)
            if not result.success and 'error' in output:
                result.error = output['error']
        except Exception as e:
            result.execution_time = time.time() - start_time
            result.error = str(e)
            result.success = False
        
        self.results.append(result)
        print(result)
        return result
    
    async def run_async_test(self, model_name: str, method_name: str, test_func, *args, **kwargs):
        """Run a single async test and record results"""
        result = ModelTestResult(model_name, method_name, 'async')
        start_time = time.time()
        
        try:
            output = await test_func(*args, **kwargs)
            result.execution_time = time.time() - start_time
            result.output = output
            result.success = output.get('success', False) if isinstance(output, dict) else bool(output)
            if not result.success and 'error' in output:
                result.error = output['error']
        except Exception as e:
            result.execution_time = time.time() - start_time
            result.error = str(e)
            result.success = False
        
        self.results.append(result)
        print(result)
        return result
    
    def test_question_answering(self):
        """Test Question Answering model (RoBERTa-based)"""
        print("\n--- Testing Question Answering (RoBERTa) ---")
        
        # Test 1: Basic QA
        self.run_test(
            "Question Answering", 
            "Basic QA", 
            self.api.question_answering,
            context="The Earth orbits the Sun in our solar system. It is the third planet from the Sun.",
            question="What orbits the Sun?"
        )
        
        # Test 2: Complex QA
        self.run_test(
            "Question Answering",
            "Complex QA",
            self.api.question_answering,
            context="Machine learning is a subset of artificial intelligence that focuses on algorithms and statistical models that computer systems use to perform a specific task without using explicit instructions, relying on patterns and inference instead.",
            question="What is machine learning?"
        )
        
        # Test 3: Edge case - empty context
        self.run_test(
            "Question Answering",
            "Empty Context",
            self.api.question_answering,
            context="",
            question="What is 2+2?"
        )
        
        # Async tests
        print("  Async tests:")
        asyncio.run(self.run_async_test(
            "Question Answering",
            "Async Basic QA",
            self.api.question_answering_async,
            context="Python is a high-level programming language.",
            question="What is Python?"
        ))
    
    def test_text_summarization(self):
        """Test Text Summarization model (BART-based)"""
        print("\n--- Testing Text Summarization (BART) ---")
        
        long_text = """
        Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence 
        displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": 
        any device that perceives its environment and takes actions that maximize its chance of successfully achieving 
        its goals. Colloquially, the term "artificial intelligence" is often used to describe machines that mimic 
        "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving".
        """
        
        # Test 1: Long text summarization
        self.run_test(
            "Text Summarization",
            "Long Text",
            self.api.text_summarization,
            text=long_text
        )
        
        # Test 2: Short text (should return original)
        self.run_test(
            "Text Summarization",
            "Short Text",
            self.api.text_summarization,
            text="This is a short sentence."
        )
        
        # Test 3: Edge case - empty text
        self.run_test(
            "Text Summarization",
            "Empty Text",
            self.api.text_summarization,
            text=""
        )
        
        # Async tests
        print("  Async tests:")
        asyncio.run(self.run_async_test(
            "Text Summarization",
            "Async Long Text",
            self.api.text_summarization_async,
            text=long_text
        ))
    
    def test_text_classification(self):
        """Test Text Classification model (FinBERT)"""
        print("\n--- Testing Text Classification (FinBERT) ---")
        
        # Test 1: Positive financial sentiment
        self.run_test(
            "Text Classification",
            "Positive Sentiment",
            self.api.text_classification,
            text="The company's quarterly earnings exceeded expectations by 15%"
        )
        
        # Test 2: Negative financial sentiment
        self.run_test(
            "Text Classification",
            "Negative Sentiment",
            self.api.text_classification,
            text="The stock price plummeted after the disappointing earnings report"
        )
        
        # Test 3: Neutral text
        self.run_test(
            "Text Classification",
            "Neutral Text",
            self.api.text_classification,
            text="The meeting is scheduled for 3 PM tomorrow"
        )
        
        # Test 4: Edge case - empty text
        self.run_test(
            "Text Classification",
            "Empty Text",
            self.api.text_classification,
            text=""
        )
        
        # Async tests
        print("  Async tests:")
        asyncio.run(self.run_async_test(
            "Text Classification",
            "Async Positive",
            self.api.text_classification_async,
            text="Great quarterly results announced"
        ))
    
    def test_text_generation(self):
        """Test Text Generation model (GPT-2)"""
        print("\n--- Testing Text Generation (GPT-2) ---")
        
        # Test 1: Basic text generation
        self.run_test(
            "Text Generation",
            "Basic Generation",
            self.api.text_generation,
            prompt="The future of artificial intelligence"
        )
        
        # Test 2: Short prompt
        self.run_test(
            "Text Generation",
            "Short Prompt",
            self.api.text_generation,
            prompt="AI"
        )
        
        # Test 3: Custom max_length
        self.run_test(
            "Text Generation",
            "Custom Length",
            self.api.text_generation,
            prompt="Machine learning",
            max_length=50
        )
        
        # Test 4: Edge case - empty prompt
        self.run_test(
            "Text Generation",
            "Empty Prompt",
            self.api.text_generation,
            prompt=""
        )
        
        # Async tests
        print("  Async tests:")
        asyncio.run(self.run_async_test(
            "Text Generation",
            "Async Generation",
            self.api.text_generation_async,
            prompt="The impact of technology on education"
        ))
    
    def test_sentence_similarity(self):
        """Test Sentence Similarity model (Sentence Transformers)"""
        print("\n--- Testing Sentence Similarity (Sentence Transformers) ---")
        
        # Test 1: High similarity
        self.run_test(
            "Sentence Similarity",
            "High Similarity",
            self.api.sentence_similarity,
            sentences=["The cat sat on the mat", "A feline rested on the rug"]
        )
        
        # Test 2: Low similarity
        self.run_test(
            "Sentence Similarity",
            "Low Similarity",
            self.api.sentence_similarity,
            sentences=["The weather is sunny", "Programming requires logical thinking"]
        )
        
        # Test 3: Identical sentences
        self.run_test(
            "Sentence Similarity",
            "Identical Sentences",
            self.api.sentence_similarity,
            sentences=["Hello world", "Hello world"]
        )
        
        # Test 4: Single sentence
        self.run_test(
            "Sentence Similarity",
            "Single Sentence",
            self.api.sentence_similarity,
            sentences=["This is a single sentence"]
        )
        
        # Test 5: Edge case - empty list
        self.run_test(
            "Sentence Similarity",
            "Empty List",
            self.api.sentence_similarity,
            sentences=[]
        )
        
        # Async tests
        print("  Async tests:")
        asyncio.run(self.run_async_test(
            "Sentence Similarity",
            "Async Similarity",
            self.api.sentence_similarity_async,
            sentences=["Artificial intelligence", "Machine learning"]
        ))
    
    def test_translation(self):
        """Test Translation model (MarianMT)"""
        print("\n--- Testing Translation (MarianMT) ---")
        
        # Test 1: English to Spanish translation
        self.run_test(
            "Translation",
            "English to Spanish",
            self.api.translation,
            text="Hello, how are you today?"
        )
        
        # Test 2: Longer text translation
        self.run_test(
            "Translation",
            "Long Text",
            self.api.translation,
            text="Machine learning is transforming the way we solve complex problems in various industries."
        )
        
        # Test 3: Edge case - empty text
        self.run_test(
            "Translation",
            "Empty Text",
            self.api.translation,
            text=""
        )
        
        # Test 4: Unsupported language combination (should fallback)
        self.run_test(
            "Translation",
            "Unsupported Language",
            self.api.translation,
            text="Hello",
            source_lang="fr",
            target_lang="de"
        )
        
        # Async tests
        print("  Async tests:")
        asyncio.run(self.run_async_test(
            "Translation",
            "Async Translation",
            self.api.translation_async,
            text="Good morning"
        ))
    
    def test_chat_functionality(self):
        """Test Chat functionality"""
        print("\n--- Testing Chat Functionality ---")
        
        # Test 1: Basic chat
        chat_messages = [
            {"role": "user", "content": "What is artificial intelligence?"}
        ]
        self.run_test(
            "Chat",
            "Basic Chat",
            self.api.chat,
            messages=chat_messages
        )
        
        # Test 2: Multi-turn conversation
        multi_turn_chat = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "Tell me about machine learning"}
        ]
        self.run_test(
            "Chat",
            "Multi-turn Chat",
            self.api.chat,
            messages=multi_turn_chat
        )
        
        # Test 3: Edge case - empty messages
        self.run_test(
            "Chat",
            "Empty Messages",
            self.api.chat,
            messages=[]
        )
        
        # Async tests
        print("  Async tests:")
        asyncio.run(self.run_async_test(
            "Chat",
            "Async Chat",
            self.api.chat_async,
            messages=[{"role": "user", "content": "Explain neural networks"}]
        ))
    
    def test_image_captioning(self):
        """Test Image Captioning functionality"""
        print("\n--- Testing Image Captioning ---")
        
        # Test 1: Basic image captioning (placeholder)
        self.run_test(
            "Image Captioning",
            "Basic Captioning",
            self.api.image_captioning,
            image_path="test_image.jpg"
        )
        
        # Test 2: Edge case - empty path
        self.run_test(
            "Image Captioning",
            "Empty Path",
            self.api.image_captioning,
            image_path=""
        )
        
        # Async tests
        print("  Async tests:")
        asyncio.run(self.run_async_test(
            "Image Captioning",
            "Async Captioning",
            self.api.image_captioning_async,
            image_path="sample_image.png"
        ))
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("Starting comprehensive model testing...\n")
        
        start_time = time.time()
        
        # Run all test methods
        test_methods = [
            self.test_question_answering,
            self.test_text_summarization,
            self.test_text_classification,
            self.test_text_generation,
            self.test_sentence_similarity,
            self.test_translation,
            self.test_chat_functionality,
            self.test_image_captioning
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"Error running {test_method.__name__}: {e}")
        
        total_time = time.time() - start_time
        self.print_summary(total_time)
    
    def print_summary(self, total_time: float):
        """Print comprehensive test results summary"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST RESULTS SUMMARY")
        print("="*80)
        
        # Group results by model
        model_results = {}
        for result in self.results:
            if result.model_name not in model_results:
                model_results[result.model_name] = []
            model_results[result.model_name].append(result)
        
        # Print results for each model
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - passed_tests
        
        for model_name, results in model_results.items():
            print(f"\n{model_name}:")
            model_passed = sum(1 for r in results if r.success)
            model_total = len(results)
            
            status = "✓ PASS" if model_passed == model_total else "⚠ PARTIAL" if model_passed > 0 else "✗ FAIL"
            print(f"  {status} ({model_passed}/{model_total} tests passed)")
            
            for result in results:
                icon = "✓" if result.success else "✗"
                print(f"    {icon} {result.method_name} ({result.test_type}): {result.execution_time:.2f}s")
                if not result.success and result.error:
                    print(f"      Error: {result.error}")
        
        # Overall statistics
        print(f"\n" + "="*80)
        print("OVERALL STATISTICS")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ({(passed_tests/total_tests)*100:.1f}%)")
        print(f"Failed: {failed_tests} ({(failed_tests/total_tests)*100:.1f}%)")
        print(f"Total Execution Time: {total_time:.2f} seconds")
        
        # Performance summary
        avg_time = total_time / total_tests if total_tests > 0 else 0
        print(f"Average Test Time: {avg_time:.2f} seconds")
        
        # Slowest tests
        slowest_tests = sorted(self.results, key=lambda x: x.execution_time, reverse=True)[:5]
        print(f"\nSlowest Tests:")
        for test in slowest_tests:
            print(f"  {test.model_name} - {test.method_name}: {test.execution_time:.2f}s")
        
        # Final status
        print(f"\n" + "="*80)
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED! The local model integration is working perfectly.")
        elif passed_tests > total_tests * 0.8:
            print("✅ MOST TESTS PASSED! The system is functioning well with minor issues.")
        elif passed_tests > 0:
            print("⚠ SOME TESTS PASSED! There are significant issues that need attention.")
        else:
            print("❌ ALL TESTS FAILED! Critical issues detected in the model integration.")
        print("="*80)

def main():
    """Main function to run the comprehensive tests"""
    try:
        tester = ComprehensiveModelTester()
        tester.run_all_tests()
    except Exception as e:
        print(f"Critical error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()