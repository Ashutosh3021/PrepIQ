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

class PredictionEngine:
    """AI-powered prediction engine using Google's Gemini API"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        # Test the API key by configuring and testing a simple request
        try:
            genai.configure(api_key=api_key)
            # Test API connection with a simple request
            test_model = genai.GenerativeModel('gemini-pro')
            test_response = test_model.generate_content("Hello")
            logger.info("Gemini API connection successful")
        except Exception as e:
            logger.error(f"Gemini API connection failed: {str(e)}")
            raise ValueError(f"Invalid GEMINI_API_KEY: {str(e)}")
        
        self.model = genai.GenerativeModel('gemini-pro')
    
    def _calculate_confidence_score(self, prediction: Dict[str, Any], historical_data: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for a prediction based on historical patterns"""
        confidence_score = 0.5  # Base confidence
        
        # Increase confidence if the prediction matches historical patterns
        if historical_data:
            for hist in historical_data:
                if hist.get('unit') == prediction.get('unit'):
                    confidence_score += 0.1  # Higher confidence for matching units
                if hist.get('marks') == prediction.get('marks'):
                    confidence_score += 0.05  # Higher confidence for matching marks
                
                # Check for keyword matches
                pred_keywords = set(prediction.get('text', '').lower().split())
                hist_keywords = set(hist.get('text', '').lower().split())
                common_keywords = pred_keywords.intersection(hist_keywords)
                if common_keywords:
                    confidence_score += 0.02 * len(common_keywords)
        
        # Cap confidence at 1.0
        return min(confidence_score, 1.0)
    
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
                            "predictions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "question_number": {"type": "integer"},
                                        "text": {"type": "string"},
                                        "marks": {"type": "integer"},
                                        "unit": {"type": "string"},
                                        "probability": {"type": "string", "enum": ["very_high", "high", "moderate", "low"]},
                                        "reasoning": {"type": "string"},
                                        "confidence_score": {"type": "number"}
                                    },
                                    "required": ["question_number", "text", "marks", "unit", "probability", "reasoning", "confidence_score"]
                                }
                            },
                            "total_marks": {"type": "integer"},
                            "coverage_percentage": {"type": "number"},
                            "unit_coverage": {
                                "type": "object",
                                "additionalProperties": {"type": "number"}
                            },
                            "generated_at": {"type": "string"}
                        },
                        "required": ["predictions", "total_marks", "coverage_percentage", "unit_coverage", "generated_at"]
                    }
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating Gemini response: {str(e)}")
            raise

    def predict_exam_topics(self, study_material: str, db: Session, subject_id: str) -> Dict[str, Any]:
        """Predict likely exam topics based on study material and historical data"""
        # Get historical data for the subject
        historical_questions = db.query(models.Question).join(
            models.QuestionPaper
        ).filter(
            models.QuestionPaper.subject_id == subject_id
        ).all()
        
        # Format historical data
        historical_data = []
        for q in historical_questions:
            historical_data.append({
                "text": q.question_text,
                "marks": q.marks,
                "unit": q.unit_name,
                "type": q.question_type
            })
        
        # Create prompt with historical context
        historical_context = json.dumps(historical_data[:10])  # Limit to first 10 for context
        
        # Calculate trend analysis for better predictions
        trend_analysis = self._analyze_trends(historical_data)
        
        prompt = f"""
        Analyze the following study material and historical question patterns to predict the most likely exam topics with confidence scores:
        Study Material: {study_material}
        
        Historical Questions: {historical_context}
        
        Trend Analysis: {json.dumps(trend_analysis)}
        
        Provide your response in the following JSON format:
        {{
            "predictions": [
                {{
                    "question_number": "integer",
                    "text": "string",
                    "marks": "integer",
                    "unit": "string",
                    "probability": "very_high|high|moderate|low",
                    "reasoning": "string",
                    "confidence_score": "number between 0 and 1"
                }}
            ],
            "total_marks": "integer",
            "coverage_percentage": "float",
            "unit_coverage": {{
                "Unit Name": "percentage"
            }},
            "generated_at": "timestamp"
        }}
        """
        
        try:
            # Use the Gemini API with retry logic
            response_text = self._generate_gemini_response(prompt)
            
            # Parse the JSON response
            try:
                result = json.loads(response_text)
                
                # Calculate and add confidence scores for each prediction
                if historical_data:
                    for prediction in result.get('predictions', []):
                        confidence_score = self._calculate_confidence_score(prediction, historical_data)
                        prediction['confidence_score'] = confidence_score
                
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Gemini response as JSON: {str(e)}")
                # Return a structured response even if parsing fails
                return {
                    "predictions": [
                        {
                            "question_number": 1,
                            "text": f"Error parsing response: {response_text[:200]}...",
                            "marks": 5,
                            "unit": "Error",
                            "probability": "moderate",
                            "reasoning": "Response parsing error",
                            "confidence_score": 0.0
                        }
                    ],
                    "total_marks": 100,
                    "coverage_percentage": 0,
                    "unit_coverage": {},
                    "generated_at": str(time.time())
                }
                
        except Exception as e:
            logger.error(f"Error in prediction after retries: {str(e)}")
            # Return a fallback response
            return {
                "predictions": [
                    {
                        "question_number": 1,
                        "text": f"Prediction temporarily unavailable due to API error: {str(e)}",
                        "marks": 5,
                        "unit": "API Error",
                        "probability": "low",
                        "reasoning": "API connection error",
                        "confidence_score": 0.0
                    }
                ],
                "total_marks": 100,
                "coverage_percentage": 0,
                "unit_coverage": {},
                "generated_at": str(time.time())
            }

    def _analyze_trends(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in historical question data"""
        if not historical_data:
            return {}
        
        # Analyze unit frequency
        unit_frequency = {}
        mark_distribution = {}
        
        for q in historical_data:
            unit = q.get('unit', 'Unknown')
            marks = q.get('marks', 0)
            
            unit_frequency[unit] = unit_frequency.get(unit, 0) + 1
            mark_distribution[marks] = mark_distribution.get(marks, 0) + 1
        
        # Calculate percentages
        total_questions = len(historical_data)
        unit_percentages = {unit: (count / total_questions) * 100 for unit, count in unit_frequency.items()}
        
        # Identify most frequent units
        most_frequent_units = sorted(unit_percentages.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Identify common mark patterns
        most_common_marks = sorted(mark_distribution.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "unit_frequency": unit_frequency,
            "unit_percentages": unit_percentages,
            "most_frequent_units": most_frequent_units,
            "mark_distribution": mark_distribution,
            "most_common_marks": most_common_marks,
            "total_questions_analyzed": total_questions
        }
    
    def generate_study_plan(self, subject: str, available_time: int, current_level: str, db: Session, user_id: str) -> Dict[str, Any]:
        """Generate a personalized study plan"""
        # Get user's performance data to personalize the plan
        user_tests = db.query(models.MockTest).filter(
            models.MockTest.user_id == user_id
        ).all()
        
        # Analyze weak areas
        weak_topics = []
        if user_tests:
            # Calculate weak topics based on test performance
            # This is a simplified example
            for test in user_tests[-3:]:  # Look at last 3 tests
                if test.weak_topics_json:
                    weak_topics.extend(test.weak_topics_json)
        
        prompt = f"""
        Create a personalized study plan for {subject} with {available_time} days available and current level {current_level}.
        User's weak topics: {', '.join(set(weak_topics)) if weak_topics else 'None identified yet'}
        
        Provide your response in the following JSON format:
        {{
            "plan_id": "string",
            "subject": "string",
            "start_date": "date",
            "exam_date": "date",
            "total_days": "int",
            "daily_schedule": [
                {{
                    "day": "int",
                    "date": "date",
                    "topics": ["string"],
                    "recommended_hours": "float",
                    "priority_topics": ["string"],
                    "confidence_score": "number between 0 and 1"
                }}
            ]
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Mock response for now
            return {
                "plan_id": "plan-123",
                "subject": subject,
                "start_date": "2025-01-06",
                "exam_date": "2025-02-15",
                "total_days": available_time,
                "daily_schedule": [
                    {
                        "day": 1,
                        "date": "2025-01-06",
                        "topics": ["Introduction", "Basic Concepts"],
                        "recommended_hours": 2.0,
                        "priority_topics": ["Basic Concepts"],
                        "confidence_score": 0.8
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Error in study plan generation: {str(e)}")
            raise e