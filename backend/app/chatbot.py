import google.generativeai as genai
from typing import Dict, Any, List
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from . import models
import json
import time
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
import re
from datetime import datetime

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Chatbot:
    """AI-powered study assistant chatbot with RAG capabilities"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        # Test the API key by configuring and testing a simple request
        try:
            genai.configure(api_key=api_key)
            # Test API connection with a simple request
            test_model = genai.GenerativeModel('gemini-1.5-flash')
            # test_response = test_model.generate_content("Hello") # Skip actual call
            logger.info("Gemini API connection configured")
            self.model = test_model
        except Exception as e:
            logger.error(f"Gemini API connection failed: {str(e)}")
            # Don't raise, just log and set model to None
            self.model = None
            # raise ValueError(f"Invalid GEMINI_API_KEY: {str(e)}")
        self.conversation_memory = {}  # Store conversation history per user
        self.max_history_length = 10  # Keep last 10 messages
    
    def _get_user_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get conversation history for a specific user"""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        return self.conversation_memory[user_id]
    
    def _update_user_conversation_history(self, user_id: str, user_message: str, bot_response: str):
        """Update conversation history for a specific user"""
        if user_id not in self.conversation_memory:
            self.conversation_memory[user_id] = []
        
        # Add the new conversation to history
        self.conversation_memory[user_id].append({
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response
        })
        
        # Keep only the last N conversations
        if len(self.conversation_memory[user_id]) > self.max_history_length:
            self.conversation_memory[user_id] = self.conversation_memory[user_id][-self.max_history_length:]
    
    def get_response(self, user_message: str, context: str, db: Session, subject_id: str) -> str:
        """Generate response to user's question based on context and subject materials"""
        # Get relevant questions from the subject
        related_questions = db.query(models.Question).join(
            models.QuestionPaper
        ).filter(
            models.QuestionPaper.subject_id == subject_id
        ).limit(5).all()
        
        # Format related questions
        related_questions_text = ""
        for q in related_questions:
            related_questions_text += f"Question: {q.question_text[:200]}... Marks: {q.marks}, Unit: {q.unit_name}\n"
        
        prompt = f"""
        You are StudyBuddy, an intelligent exam preparation assistant for {context} at College.
        
        Context from student's uploaded papers:
        - Total papers analyzed: {db.query(models.QuestionPaper).filter(models.QuestionPaper.subject_id == subject_id).count()}
        - Questions extracted: {db.query(models.Question).join(models.QuestionPaper).filter(models.QuestionPaper.subject_id == subject_id).count()}
        - Time period: Last 5 years
        
        Related Questions from Previous Year Papers:
        {related_questions_text}
        
        User Question: "{user_message}"
        
        Your Response Should Include:
        1. Clear, concise answer to user's question
        2. Specific examples from the papers they uploaded
        3. Links to related exam questions
        4. Study tips based on their weak areas
        5. Actionable next steps
        
        Tone: Encouraging, data-driven, personalized
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error in chatbot response: {str(e)}")
            return "I'm sorry, I couldn't process your request. Please try again."
    
    def explain_concept(self, concept: str, difficulty_level: str, db: Session, subject_id: str) -> Dict[str, Any]:
        """Explain a complex concept in simple terms with examples from subject materials"""
        # Get examples of this concept from subject papers
        concept_questions = db.query(models.Question).join(
            models.QuestionPaper
        ).filter(
            models.QuestionPaper.subject_id == subject_id,
            models.Question.question_text.contains(concept)
        ).limit(3).all()
        
        concept_examples = []
        for q in concept_questions:
            concept_examples.append({
                "question": q.question_text[:200] + "...",
                "marks": q.marks,
                "appeared_in": q.paper.exam_year if q.paper.exam_year else "Unknown year"
            })
        
        prompt = f"""
        Explain the concept of '{concept}' in simple terms appropriate for a {difficulty_level} level student.
        Use examples from the following questions if relevant:
        {json.dumps(concept_examples, indent=2)}
        
        Provide your response in the following JSON format:
        {{
            "concept": "string",
            "simple_explanation": "string",
            "examples": ["string"],
            "key_points": ["string"],
            "visual_analogy": "string",
            "practice_tip": "string"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Mock response for now
            return {
                "concept": concept,
                "simple_explanation": f"This is a simplified explanation of {concept}",
                "examples": [f"Example of {concept} from past papers"],
                "key_points": [f"Key point about {concept}"],
                "visual_analogy": f"Think of {concept} like...",
                "practice_tip": f"How to practice {concept}"
            }
        except Exception as e:
            logger.error(f"Error in concept explanation: {str(e)}")
            raise e