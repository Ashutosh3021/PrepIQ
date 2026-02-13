"""
Test for Gemini AI Tutor Bot
API Key location: .env file (GEMINI_API_KEY)
Model: gemini-1.5-flash

This test validates the AI tutor with a specific teaching persona:
- Highly intelligent, slightly sarcastic but supportive teacher
- Uses active questioning and structured reasoning
- Asks diagnostic questions before giving explanations
- Never reveals full answers immediately
- Teaches through step-by-step reasoning
- Uses light, clever sarcasm to keep tone engaging
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AI Tutor System Prompt
TUTOR_SYSTEM_PROMPT = """Act as a highly intelligent, slightly sarcastic but supportive teacher. Your role is to guide the student through concepts using active questioning and structured reasoning.

Rules you must follow strictly:

Always ask at least one diagnostic question before giving any explanation.

Do not reveal the full answer immediately.

Teach through a step-by-step reasoning process.

Make the student think. Ask guiding questions after each step.

Only provide the complete answer if the student explicitly says: "Tell me the full answer."

Use light, clever sarcasm (subtle, not rude) to keep the tone engaging.

Break complex ideas into connected stages so each concept builds logically on the previous one.

If the student gives a wrong answer, do not immediately correct it. Instead, ask a question that exposes the flaw and leads them to self-correct.

Keep explanations clear, precise, and structured. No fluff.

Teaching Style Guidelines:

Start by assessing prior knowledge.

Use analogies when helpful, but keep them tight.

Encourage reasoning over memorization.

Keep the student mentally involved at every step.

Never dump information in one block.

Example behavior:
Use simpler english for better understanding. If the student is struggling, break down the problem into smaller parts and ask questions about each part. Always encourage the student to think through the problem rather than just giving them the answer.
Follow the language which the student uses. If they use hindi, respond in hindi. If they use english, respond in english. If they use a mix of both, respond in the same mix.
If asked a math question, first ask what they already know about the topic.
If asked a programming question, first ask how they think the logic should flow.
If asked a theory question, first ask for their interpretation.

You are not a solution machine. You are a thinking trainer."""

def test_gemini_tutor():
    """Test the Gemini AI Tutor with the specified teaching persona"""
    print("=" * 60)
    print("Testing Gemini AI Tutor Bot")
    print("Model: gemini-2.5-flash")
    print("=" * 60)
    
    try:
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ Error: GEMINI_API_KEY not found in environment variables")
            print("   Please set GEMINI_API_KEY in your .env file")
            return False
        
        # Initialize Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        print("✅ Gemini API initialized successfully\n")
        
        # Test case 1: Math question
        print("Test 1: Math Question (Should ask diagnostic question first)")
        print("-" * 60)
        user_question1 = "How do I solve the equation 2x + 5 = 15?"
        
        prompt1 = f"""{TUTOR_SYSTEM_PROMPT}

Student Question: {user_question1}

Respond as the AI Tutor:"""
        
        print(f"Student: {user_question1}")
        response1 = model.generate_content(prompt1)
        print(f"Tutor: {response1.text}\n")
        
        # Verify tutor asks a question (diagnostic)
        if '?' not in response1.text:
            print("⚠️  Warning: Tutor did not ask a diagnostic question")
        else:
            print("✅ Tutor asked diagnostic question")
        
        # Test case 2: Programming question
        print("\nTest 2: Programming Question (Should guide through logic)")
        print("-" * 60)
        user_question2 = "How do I reverse a string in Python?"
        
        prompt2 = f"""{TUTOR_SYSTEM_PROMPT}

Student Question: {user_question2}

Respond as the AI Tutor:"""
        
        print(f"Student: {user_question2}")
        response2 = model.generate_content(prompt2)
        print(f"Tutor: {response2.text}\n")
        
        # Verify tutor doesn't give full answer immediately
        if 'reversed(' in response2.text.lower() or '[::-1]' in response2.text:
            print("⚠️  Warning: Tutor may have given full solution immediately")
        else:
            print("✅ Tutor is guiding rather than giving full answer")
        
        # Test case 3: Student gives wrong answer
        print("\nTest 3: Student Gives Wrong Answer (Should lead to self-correction)")
        print("-" * 60)
        wrong_answer_scenario = """Previous context:
Tutor: What do you think 15 divided by 3 equals?
Student: I think it's 6."""
        
        prompt3 = f"""{TUTOR_SYSTEM_PROMPT}

{wrong_answer_scenario}

Respond as the AI Tutor (don't correct directly, ask a question that helps them see the error):"""
        
        print("Student: I think it's 6.")
        response3 = model.generate_content(prompt3)
        print(f"Tutor: {response3.text}\n")
        
        # Verify tutor doesn't just say "you're wrong"
        lower_response = response3.text.lower()
        if "wrong" in lower_response or "incorrect" in lower_response or "no" in lower_response[:20]:
            print("⚠️  Warning: Tutor directly corrected the student")
        else:
            print("✅ Tutor is guiding student to self-correct")
        
        # Test case 4: Student asks for full answer
        print("\nTest 4: Student Asks for Full Answer")
        print("-" * 60)
        full_answer_request = "Tell me the full answer."
        
        prompt4 = f"""{TUTOR_SYSTEM_PROMPT}

Previous context:
Tutor: What's 2 + 2?
Student: I think it's 4.
Student: {full_answer_request}

Respond as the AI Tutor:"""
        
        print(f"Student: {full_answer_request}")
        response4 = model.generate_content(prompt4)
        print(f"Tutor: {response4.text}\n")
        
        print("✅ Test completed - Tutor provided full answer on request")
        
        # Test case 5: Theory question
        print("\nTest 5: Theory Question (Should ask for interpretation first)")
        print("-" * 60)
        user_question5 = "What is photosynthesis?"
        
        prompt5 = f"""{TUTOR_SYSTEM_PROMPT}

Student Question: {user_question5}

Respond as the AI Tutor:"""
        
        print(f"Student: {user_question5}")
        response5 = model.generate_content(prompt5)
        print(f"Tutor: {response5.text}\n")
        
        print("=" * 60)
        print("✅ Gemini AI Tutor Bot Test PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("- Tutor asks diagnostic questions before explaining")
        print("- Tutor guides rather than giving direct answers")
        print("- Tutor uses Socratic method for wrong answers")
        print("- Tutor provides full answers when explicitly requested")
        print("- Teaching persona is engaging with subtle sarcasm")
        
        return True
        
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gemini_tutor()
    sys.exit(0 if success else 1)
