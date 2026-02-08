import logging
from typing import Dict, Any, List
import os
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
import re
from sqlalchemy.orm import Session
import json
from ..ml.external_api_wrapper import external_api

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConceptExplainer:
    """AI-powered concept explanation engine with personalized learning paths"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        # Configure the Gemini API and initialize model
        try:
            genai.configure(api_key=api_key)
            
            # Use a more capable model for concept explanations
            self.model = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                }
            )
            logger.info("ConceptExplainer Gemini API connection configured")
        except Exception as e:
            logger.error(f"ConceptExplainer Gemini API connection failed: {str(e)}")
            self.model = None
        
        # Define learning styles and difficulty levels
        self.learning_styles = {
            'visual': "Use diagrams, charts, and visual examples when explaining concepts.",
            'auditory': "Provide clear verbal explanations with analogies and examples.",
            'kinesthetic': "Include practical examples and hands-on approaches.",
            'reading_writing': "Provide detailed written explanations with examples."
        }
        
        self.difficulty_levels = {
            'beginner': "Explain in simple terms with basic examples.",
            'intermediate': "Include moderate complexity with some examples.",
            'advanced': "Provide in-depth explanations with complex examples."
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _generate_gemini_response(self, prompt: str) -> str:
        """Generate response from Gemini with retry logic"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema={
                        "type": "object",
                        "properties": {
                            "explanation": {"type": "string"},
                            "examples": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "key_points": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "difficulty_level": {"type": "string"},
                            "estimated_reading_time": {"type": "number"},
                            "related_concepts": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["explanation", "key_points", "difficulty_level", "estimated_reading_time"]
                    }
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating Gemini response: {str(e)}")
            raise
    
    def explain_concept(self, concept: str, subject: str, user_profile: Dict[str, Any] = None, 
                       context: str = "", db: Session = None) -> Dict[str, Any]:
        """Generate personalized concept explanation using external APIs or fallback to local model"""
        
        # Try external API first for enhanced explanation
        try:
            # Use text generation API for better explanations
            prompt = f"Explain the concept '{concept}' in {subject} subject. {context}"
            if user_profile:
                prompt += f" Tailor the explanation for a {user_profile.get('knowledge_level', 'intermediate')} level student."
            
            response = external_api.text_generation(prompt, max_length=500)
            
            if response["success"] and response["output"]:
                # Parse the API response
                explanation_text = response["output"]
                
                # Use QA API to extract key points
                try:
                    qa_response = external_api.question_answering(
                        context=explanation_text,
                        question=f"What are the key points about {concept}?"
                    )
                    key_points = [qa_response["output"]] if qa_response["success"] else []
                except:
                    key_points = []
                
                # Use classification API for difficulty assessment
                try:
                    classification_response = external_api.text_classification(explanation_text)
                    difficulty_level = classification_response["output"]["label"].lower() if classification_response["success"] else "intermediate"
                except:
                    difficulty_level = "intermediate"
                
                return {
                    "explanation": explanation_text,
                    "examples": [],
                    "key_points": key_points,
                    "difficulty_level": difficulty_level,
                    "estimated_reading_time": len(explanation_text.split()) // 100 + 1,
                    "related_concepts": [],
                    "concept": concept,
                    "subject": subject,
                    "explained_at": datetime.now().isoformat(),
                    "personalized_for": user_profile or {},
                    "source": "external_api"
                }
                
        except Exception as e:
            logger.warning(f"External API explanation failed, using local method: {e}")
        
        # Get user learning preferences if available
        learning_style = "general"
        difficulty_pref = "intermediate"
        user_level = "intermediate"
        
        if user_profile:
            learning_style = user_profile.get('learning_style', 'general')
            user_level = user_profile.get('knowledge_level', 'intermediate')
            difficulty_pref = user_profile.get('preferred_difficulty', 'intermediate')
        
        # Get related concepts from database if available
        related_concepts = []
        if db and subject:
            # Query for related concepts in the same subject
            try:
                # This would be customized based on actual database structure
                # For now, we'll simulate getting related concepts
                related_concepts = self._get_related_concepts_from_db(db, subject, concept)
            except Exception as e:
                logger.warning(f"Could not fetch related concepts from DB: {e}")
        
        # Create prompt with user context
        style_instruction = self.learning_styles.get(learning_style, "")
        difficulty_instruction = self.difficulty_levels.get(difficulty_pref, "")
        
        prompt = f"""
        Explain the concept '{concept}' in the subject '{subject}'.
        
        Context: {context}
        
        User Learning Style: {style_instruction}
        Desired Difficulty: {difficulty_instruction}
        User Knowledge Level: {user_level}
        
        Related Concepts: {', '.join(related_concepts) if related_concepts else 'None available'}
        
        Provide your response in the following JSON format:
        {{
            "explanation": "Detailed explanation of the concept with examples",
            "examples": ["Example 1", "Example 2", "Example 3"],
            "key_points": ["Key point 1", "Key point 2", "Key point 3"],
            "difficulty_level": "beginner|intermediate|advanced",
            "estimated_reading_time": "Estimated time in minutes",
            "related_concepts": ["Related concept 1", "Related concept 2"]
        }}
        """
        
        try:
            response_text = self._generate_gemini_response(prompt)
            
            # Parse the JSON response
            try:
                result = json.loads(response_text)
                
                # Enhance with additional metadata
                result['concept'] = concept
                result['subject'] = subject
                result['explained_at'] = datetime.now().isoformat()
                result['personalized_for'] = user_profile or {}
                result['source'] = 'gemini_local'
                
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Gemini response as JSON: {str(e)}")
                # Return a structured response even if parsing fails
                return {
                    "explanation": f"Concept explanation for {concept} in {subject}",
                    "examples": [],
                    "key_points": [],
                    "difficulty_level": difficulty_pref,
                    "estimated_reading_time": 5,
                    "related_concepts": related_concepts,
                    "concept": concept,
                    "subject": subject,
                    "explained_at": datetime.now().isoformat(),
                    "personalized_for": user_profile or {},
                    "error": "Response parsing error, returning template",
                    "source": "local_fallback"
                }
                
        except Exception as e:
            logger.error(f"Error in concept explanation: {str(e)}")
            return {
                "explanation": f"Sorry, I couldn't generate a detailed explanation for '{concept}' at the moment. Please try again later.",
                "examples": [],
                "key_points": [],
                "difficulty_level": difficulty_pref,
                "estimated_reading_time": 1,
                "related_concepts": related_concepts,
                "concept": concept,
                "subject": subject,
                "explained_at": datetime.now().isoformat(),
                "personalized_for": user_profile or {},
                "error": str(e),
                "source": "error_fallback"
            }
    
    def _get_related_concepts_from_db(self, db: Session, subject: str, current_concept: str) -> List[str]:
        """Get related concepts from database based on subject"""
        # This is a placeholder implementation - would be customized based on actual DB schema
        # For now, return some sample related concepts
        related = []
        
        # Example: query for concepts in the same subject
        # This would involve actual database queries based on your schema
        # related = db.query(SomeConceptModel).filter(
        #     SomeConceptModel.subject == subject,
        #     SomeConceptModel.concept != current_concept
        # ).limit(5).all()
        
        # For demonstration, return some sample related concepts
        concept_mappings = {
            "object oriented programming": ["encapsulation", "inheritance", "polymorphism", "abstraction"],
            "algorithms": ["data structures", "complexity analysis", "sorting", "searching"],
            "machine learning": ["neural networks", "regression", "classification", "clustering"],
            "database systems": ["sql", "normalization", "transactions", "indexes"]
        }
        
        related = concept_mappings.get(current_concept.lower(), [])
        
        return related
    
    def generate_learning_path(self, concepts: List[str], subject: str, user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a personalized learning path for multiple concepts"""
        
        user_level = user_profile.get('knowledge_level', 'intermediate') if user_profile else 'intermediate'
        learning_goals = user_profile.get('learning_goals', []) if user_profile else []
        
        prompt = f"""
        Create a personalized learning path for the following concepts in '{subject}':
        Concepts: {', '.join(concepts)}
        
        User Level: {user_level}
        Learning Goals: {', '.join(learning_goals) if learning_goals else 'General understanding'}
        
        Provide your response in the following JSON format:
        {{
            "learning_path": [
                {{
                    "step": 1,
                    "concept": "Concept name",
                    "estimated_time_minutes": 30,
                    "prerequisites": ["Prerequisite concept 1"],
                    "resources": ["Resource 1", "Resource 2"],
                    "difficulty_level": "beginner|intermediate|advanced",
                    "learning_objectives": ["Objective 1", "Objective 2"]
                }}
            ],
            "total_estimated_time": 120,
            "recommended_order": ["Concept 1", "Concept 2"],
            "prerequisite_map": {{"Concept 2": ["Concept 1"]}}
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # For now, return a mock response since we're not guaranteed JSON schema
            return {
                "learning_path": [
                    {
                        "step": i+1,
                        "concept": concept,
                        "estimated_time_minutes": 30,
                        "prerequisites": [],
                        "resources": [f"Textbook Chapter for {concept}", f"Video Tutorial: {concept}"],
                        "difficulty_level": user_level,
                        "learning_objectives": [f"Understand the basics of {concept}", f"Apply {concept} in practice"]
                    }
                    for i, concept in enumerate(concepts)
                ],
                "total_estimated_time": len(concepts) * 30,
                "recommended_order": concepts,
                "prerequisite_map": {},
                "generated_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating learning path: {str(e)}")
            return {
                "learning_path": [],
                "total_estimated_time": 0,
                "recommended_order": concepts,
                "prerequisite_map": {},
                "error": str(e),
                "generated_at": datetime.now().isoformat()
            }
    
    def adapt_difficulty(self, explanation: Dict[str, Any], user_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt explanation difficulty based on user performance"""
        
        current_difficulty = explanation.get('difficulty_level', 'intermediate')
        performance_score = user_performance.get('understanding_score', 0.5)  # 0-1 scale
        
        # Adjust difficulty based on performance
        if performance_score > 0.8:
            # User is doing well, increase difficulty
            new_difficulty = 'advanced'
        elif performance_score > 0.5:
            # User is doing okay, keep current difficulty
            new_difficulty = current_difficulty
        else:
            # User is struggling, decrease difficulty
            new_difficulty = 'beginner'
        
        # Modify the explanation based on new difficulty
        adapted_explanation = explanation.copy()
        adapted_explanation['difficulty_level'] = new_difficulty
        adapted_explanation['adapted_from_original'] = current_difficulty
        adapted_explanation['performance_based_adaptation'] = True
        
        return adapted_explanation

# Example usage
if __name__ == "__main__":
    explainer = ConceptExplainer()
    
    # Example user profile
    user_profile = {
        'learning_style': 'visual',
        'knowledge_level': 'beginner',
        'preferred_difficulty': 'beginner',
        'learning_goals': ['understand basics', 'apply in projects']
    }
    
    # Explain a concept
    explanation = explainer.explain_concept(
        concept="Object Oriented Programming",
        subject="Computer Science",
        user_profile=user_profile,
        context="Fundamental programming paradigm"
    )
    
    print("Concept Explanation:")
    print(explanation)