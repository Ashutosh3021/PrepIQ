"""
Test script to verify Bytez API integration
Tests Q&A, Chat, and Summarization models
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.external_api_wrapper import external_api

def test_qa_model():
    """Test Question Answering model"""
    print("\n" + "="*60)
    print("Testing Q&A Model")
    print("="*60)
    
    context = """
    Python is a high-level, interpreted programming language known for its simplicity and readability.
    It was created by Guido van Rossum and first released in 1991. Python supports multiple programming
    paradigms including procedural, object-oriented, and functional programming.
    """
    
    question = "Who created Python?"
    
    print(f"\nContext: {context.strip()}")
    print(f"\nQuestion: {question}")
    
    result = external_api.question_answering(context, question)
    
    print(f"\nResult: {result}")
    print(f"Success: {result['success']}")
    print(f"Answer: {result['output']}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    
    return result['success']

def test_chat_model():
    """Test Chat model"""
    print("\n" + "="*60)
    print("Testing Chat Model")
    print("="*60)
    
    messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    print(f"\nMessages: {messages}")
    
    result = external_api.chat(messages)
    
    print(f"\nResult: {result}")
    print(f"Success: {result['success']}")
    print(f"Response: {result['output']}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    
    return result['success']

def test_summarization_model():
    """Test Summarization model"""
    print("\n" + "="*60)
    print("Testing Summarization Model")
    print("="*60)
    
    text = """
    Artificial Intelligence (AI) is revolutionizing the way we live and work. From healthcare to finance,
    AI applications are becoming increasingly prevalent. Machine learning, a subset of AI, enables computers
    to learn from data without being explicitly programmed. Deep learning, which uses neural networks with
    multiple layers, has achieved remarkable success in areas like image recognition and natural language
    processing. However, AI also raises important ethical questions about privacy, bias, and the future of
    employment. As AI continues to advance, it's crucial that we develop it responsibly and ensure it
    benefits all of humanity.
    """
    
    print(f"\nText to summarize: {text.strip()}")
    
    result = external_api.text_summarization(text)
    
    print(f"\nResult: {result}")
    print(f"Success: {result['success']}")
    print(f"Summary: {result['output']}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    
    return result['success']

def test_text_generation():
    """Test Text Generation model"""
    print("\n" + "="*60)
    print("Testing Text Generation Model")
    print("="*60)
    
    prompt = "The future of education will be"
    
    print(f"\nPrompt: {prompt}")
    
    result = external_api.text_generation(prompt, max_length=50)
    
    print(f"\nResult: {result}")
    print(f"Success: {result['success']}")
    print(f"Generated text: {result['output']}")
    
    if result['error']:
        print(f"Error: {result['error']}")
    
    return result['success']

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("BYTEZ API INTEGRATION TEST")
    print("="*60)
    
    # Check if external_api is initialized
    if external_api is None:
        print("\n[ERROR] external_api is None. Bytez SDK not initialized.")
        return False
    
    print(f"\n[OK] External API initialized")
    print(f"[OK] Models available: {external_api.models_available}")
    print(f"[OK] Bytez SDK: {external_api.bytez_sdk is not None}")
    
    # Run tests
    results = {
        "Q&A": test_qa_model(),
        "Chat": test_chat_model(),
        "Summarization": test_summarization_model(),
        "Generation": test_text_generation()
    }
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n[OK] All tests passed!")
    else:
        print("\n[ERROR] Some tests failed. Check logs above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
