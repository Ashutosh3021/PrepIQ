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
from .ml_models.enhanced_question_analyzer import EnhancedQuestionAnalyzer
from .ml.syllabus_analyzer import SyllabusAnalyzer
from .ml.correlation_analyzer import CorrelationAnalyzer
from .ml_engines.concept_explainer import ConceptExplainer

# Safe import of external_api
try:
    from .ml.external_api_wrapper import get_external_api
    external_api = get_external_api()
except Exception as e:
    logger.warning(f"Failed to import external_api: {e}")
    external_api = None

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionEngine:
    """AI-powered prediction engine using Google's Gemini API with enhanced ML capabilities"""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        # Test the API key by configuring and testing a simple request
        # Test the API key by configuring and testing a simple request
        try:
            genai.configure(api_key=api_key)
            # Test API connection with a simple request
            test_model = genai.GenerativeModel('gemini-1.5-flash')
            # test_response = test_model.generate_content("Hello") # Skip actual call to save quota/time during init
            logger.info("Gemini API connection configured")
            self.model = test_model
        except Exception as e:
            logger.error(f"Gemini API connection failed: {str(e)}")
            # Don't raise, just log and set model to None to allow server to start
            self.model = None
            # raise ValueError(f"Invalid GEMINI_API_KEY: {str(e)}")
        
        # Initialize enhanced ML components with error handling
        try:
            self.question_analyzer = EnhancedQuestionAnalyzer()
        except Exception as e:
            logger.warning(f"Failed to initialize EnhancedQuestionAnalyzer: {e}")
            self.question_analyzer = None
        
        try:
            self.syllabus_analyzer = SyllabusAnalyzer()
        except Exception as e:
            logger.warning(f"Failed to initialize SyllabusAnalyzer: {e}")
            self.syllabus_analyzer = None
        
        try:
            self.correlation_analyzer = CorrelationAnalyzer()
        except Exception as e:
            logger.warning(f"Failed to initialize CorrelationAnalyzer: {e}")
            self.correlation_analyzer = None
        
        try:
            self.concept_explainer = ConceptExplainer()
        except Exception as e:
            logger.warning(f"Failed to initialize ConceptExplainer: {e}")
            self.concept_explainer = None
    
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
        """Predict likely exam topics using external APIs with RAG and personalization"""
        
        # Try external API approach first
        try:
            # Use text summarization to condense study material
            summary_response = external_api.text_summarization(study_material[:2000])  # Limit input size
            summary = summary_response["output"] if summary_response["success"] else study_material[:500]
            
            # Use QA API to extract key topics from study material
            qa_response = external_api.question_answering(
                context=summary,
                question="What are the most important topics covered in this study material?"
            )
            
            key_topics = qa_response["output"] if qa_response["success"] else "General topics"
            
            # Use text classification to assess difficulty and importance
            classification_response = external_api.text_classification(summary)
            difficulty_level = classification_response["output"]["label"] if classification_response["success"] else "intermediate"
            
            # Generate enhanced prompt for prediction
            enhanced_prompt = f"""
            Based on the following study material summary and key topics, predict likely exam questions:
            
            Summary: {summary}
            Key Topics: {key_topics}
            Difficulty Level: {difficulty_level}
            
            Provide predictions in JSON format with questions, probability, and reasoning.
            """
            
            # Use text generation API for predictions
            generation_response = external_api.text_generation(enhanced_prompt, max_length=1000)
            
            if generation_response["success"] and generation_response["output"]:
                # Try to parse the generated response as JSON
                try:
                    result = json.loads(generation_response["output"])
                    if isinstance(result, dict) and "predictions" in result:
                        result["source"] = "external_api"
                        result["generated_at"] = datetime.now().isoformat()
                        return result
                except json.JSONDecodeError:
                    # If parsing fails, create structured response from generated text
                    return {
                        "predictions": [
                            {
                                "question_number": 1,
                                "text": generation_response["output"][:200],
                                "marks": 5,
                                "unit": "General",
                                "probability": "moderate",
                                "reasoning": "Generated from external API analysis",
                                "confidence_score": 0.7
                            }
                        ],
                        "total_marks": 100,
                        "coverage_percentage": 80,
                        "unit_coverage": {"General": 100},
                        "source": "external_api_text",
                        "generated_at": datetime.now().isoformat()
                    }
                    
        except Exception as e:
            logger.warning(f"External API prediction failed, using local method: {e}")
        
        # Get historical data for the subject
        historical_questions = db.query(models.Question).join(
            models.QuestionPaper
        ).filter(
            models.QuestionPaper.subject_id == subject_id
        ).all()
        
        # Get subject information
        subject = db.query(models.Subject).filter(
            models.Subject.id == subject_id
        ).first()
        
        # Format historical data
        historical_data = []
        for q in historical_questions:
            historical_data.append({
                "text": q.question_text,
                "marks": q.marks,
                "unit": q.unit_name,
                "type": q.question_type,
                "difficulty": q.difficulty_level
            })
        
        # Get syllabus information if available
        syllabus_content = ""
        if subject and subject.syllabus_json:
            # Extract syllabus content from JSON
            syllabus_content = json.dumps(subject.syllabus_json) if isinstance(subject.syllabus_json, dict) else str(subject.syllabus_json)
        
        # Perform enhanced analysis using ML components (with null checks)
        if self.question_analyzer:
            try:
                question_analysis = self.question_analyzer.analyze_patterns(historical_data)
            except Exception as e:
                logger.warning(f"Question analysis failed: {e}")
                question_analysis = {}
        else:
            question_analysis = {}
        
        if self.syllabus_analyzer and syllabus_content:
            try:
                syllabus_analysis = self.syllabus_analyzer.analyze_curriculum_alignment(syllabus_content, historical_data)
            except Exception as e:
                logger.warning(f"Syllabus analysis failed: {e}")
                syllabus_analysis = {}
        else:
            syllabus_analysis = {}
        
        # Perform correlation analysis (with null checks)
        if self.correlation_analyzer:
            try:
                correlation_results = self.correlation_analyzer.comprehensive_correlation_analysis(
                    historical_data,
                    syllabus_analysis.get('topic_importance', {}) if syllabus_analysis else {}
                )
                high_impact_topics = self.correlation_analyzer.predict_high_impact_topics(correlation_results)
            except Exception as e:
                logger.warning(f"Correlation analysis failed: {e}")
                correlation_results = {}
                high_impact_topics = []
        else:
            correlation_results = {}
            high_impact_topics = []
        
        # Create prompt with enhanced context from RAG
        rag_context = {
            "historical_patterns": question_analysis,
            "syllabus_alignment": syllabus_analysis,
            "correlation_analysis": correlation_results,
            "high_impact_topics": high_impact_topics[:5],  # Top 5 high-impact topics
            "study_material_summary": study_material[:1000]  # Limit study material for context
        }
        
        prompt = f"""
        Analyze the following comprehensive context to predict the most likely exam topics with personalized recommendations:
        
        STUDY MATERIAL: {study_material}
        
        HISTORICAL QUESTION PATTERNS: {json.dumps(question_analysis, default=str)}
        
        SYLLABUS ALIGNMENT ANALYSIS: {json.dumps(syllabus_analysis, default=str)}
        
        CORRELATION ANALYSIS: {json.dumps(correlation_results, default=str)}
        
        HIGH IMPACT TOPICS: {json.dumps(high_impact_topics[:5])}
        
        Based on this analysis, provide predictions with the following requirements:
        1. Prioritize topics that appear frequently in historical exams
        2. Give higher weight to topics with strong syllabus alignment
        3. Highlight topics with high correlation to exam performance
        4. Recommend personalized study focus areas based on patterns
        
        Provide your response in the following JSON format:
        {{
            "predictions": [
                {{
                    "question_number": "integer",
                    "text": "predicted question text",
                    "marks": "integer",
                    "unit": "string",
                    "probability": "very_high|high|moderate|low",
                    "reasoning": "detailed reasoning based on analysis",
                    "confidence_score": "number between 0 and 1",
                    "topic_importance": "high|medium|low based on correlation analysis"
                }}
            ],
            "total_marks": "integer",
            "coverage_percentage": "float",
            "unit_coverage": {{
                "Unit Name": "percentage"
            }},
            "topic_prioritization": [
                {{
                    "topic": "topic name",
                    "priority_level": "high|medium|low",
                    "reason": "why this topic is prioritized",
                    "estimated_weightage": "percentage estimate",
                    "study_recommendation": "specific study advice for this topic"
                }}
            ],
            "personalized_guidance": {{
                "focus_areas": ["area1", "area2"],
                "avoidance_areas": ["area1"],
                "study_schedule_recommendation": "general study timeline advice",
                "revision_strategy": "how to approach revision for this subject"
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
                
                # Add topic prioritization if not present
                if 'topic_prioritization' not in result:
                    result['topic_prioritization'] = self._generate_topic_prioritization(high_impact_topics[:3])
                
                # Add personalized guidance if not present
                if 'personalized_guidance' not in result:
                    result['personalized_guidance'] = self._generate_personalized_guidance(high_impact_topics[:3])
                
                result['source'] = 'gemini_local'
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Gemini response as JSON: {str(e)}")
                # Return a structured response with enhanced analysis
                return {
                    "predictions": [
                        {
                            "question_number": 1,
                            "text": f"Error parsing response: {response_text[:200]}...",
                            "marks": 5,
                            "unit": "Error",
                            "probability": "moderate",
                            "reasoning": "Response parsing error",
                            "confidence_score": 0.0,
                            "topic_importance": "unknown"
                        }
                    ],
                    "total_marks": 100,
                    "coverage_percentage": 0,
                    "unit_coverage": {},
                    "topic_prioritization": self._generate_topic_prioritization(high_impact_topics[:3]),
                    "personalized_guidance": self._generate_personalized_guidance(high_impact_topics[:3]),
                    "generated_at": str(datetime.now().isoformat()),
                    "source": "local_fallback"
                }
                
        except Exception as e:
            logger.error(f"Error in prediction after retries: {str(e)}")
            # Return a fallback response with analysis results
            return {
                "predictions": [
                    {
                        "question_number": 1,
                        "text": f"Prediction temporarily unavailable due to API error: {str(e)}",
                        "marks": 5,
                        "unit": "API Error",
                        "probability": "low",
                        "reasoning": "API connection error",
                        "confidence_score": 0.0,
                        "topic_importance": "unknown"
                    }
                ],
                "total_marks": 100,
                "coverage_percentage": 0,
                "unit_coverage": {},
                "topic_prioritization": self._generate_topic_prioritization(high_impact_topics[:3]),
                "personalized_guidance": self._generate_personalized_guidance(high_impact_topics[:3]),
                "generated_at": str(datetime.now().isoformat()),
                "source": "error_fallback"
            }
    
    def _generate_topic_prioritization(self, high_impact_topics: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Generate topic prioritization based on high-impact analysis"""
        prioritization = []
        
        for i, topic_info in enumerate(high_impact_topics):
            topic = topic_info.get('topic', f'Topic {i+1}')
            impact_score = topic_info.get('impact_score', 0.5)
            
            if impact_score >= 0.7:
                priority = "high"
                reason = "High correlation with exam performance and frequent appearance in past papers"
                estimated_weightage = "25-35%"
                study_recommendation = "Focus extensively on this topic; practice multiple problem types"
            elif impact_score >= 0.4:
                priority = "medium"
                reason = "Moderate correlation with exam performance"
                estimated_weightage = "15-25%"
                study_recommendation = "Cover fundamental concepts thoroughly"
            else:
                priority = "low"
                reason = "Lower correlation with exam performance"
                estimated_weightage = "5-15%"
                study_recommendation = "Review basic concepts but don't spend excessive time"
            
            prioritization.append({
                "topic": topic,
                "priority_level": priority,
                "reason": reason,
                "estimated_weightage": estimated_weightage,
                "study_recommendation": study_recommendation
            })
        
        return prioritization
    
    def _generate_personalized_guidance(self, high_impact_topics: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Generate personalized study guidance based on analysis"""
        focus_areas = []
        avoidance_areas = []
        
        for topic_info in high_impact_topics:
            topic = topic_info.get('topic', '')
            impact_score = topic_info.get('impact_score', 0)
            
            if impact_score >= 0.7:
                focus_areas.append(topic)
            elif impact_score <= 0.3:
                avoidance_areas.append(topic)
        
        return {
            "focus_areas": focus_areas,
            "avoidance_areas": avoidance_areas,
            "study_schedule_recommendation": f"Allocate 60% of study time to high-impact topics: {', '.join(focus_areas[:2])}",
            "revision_strategy": "Use spaced repetition for high-impact topics and practice past exam questions"
        }
    
    def generate_personalized_revision_guide(self, subject_id: str, user_performance: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Generate personalized revision guidance based on user performance"""
        # Get subject and historical data
        subject = db.query(models.Subject).filter(models.Subject.id == subject_id).first()
        historical_questions = db.query(models.Question).join(
            models.QuestionPaper
        ).filter(models.QuestionPaper.subject_id == subject_id).all()
        
        # Format questions
        questions_data = []
        for q in historical_questions:
            questions_data.append({
                "text": q.question_text,
                "marks": q.marks,
                "unit": q.unit_name,
                "difficulty": q.difficulty_level
            })
        
        # Analyze user's weak areas
        weak_areas = user_performance.get('weak_topics', [])
        strong_areas = user_performance.get('strong_topics', [])
        
        # Create prompt for personalized revision guide
        prompt = f"""
        Create a personalized revision guide for the subject: {subject.name if subject else 'Unknown Subject'}
        
        User's Weak Areas: {', '.join(weak_areas)}
        User's Strong Areas: {', '.join(strong_areas)}
        Overall Performance Score: {user_performance.get('overall_score', 'N/A')}
        
        Historical Questions: {json.dumps(questions_data[:10])}
        
        Based on the user's performance, provide a detailed revision guide with:
        1. Specific focus areas for improvement
        2. Recommended study sequence
        3. Time allocation suggestions
        4. Practice question recommendations
        5. Confidence-building strategies
        
        Provide your response in the following JSON format:
        {{
            "revision_guide": {{
                "focus_areas": ["area1", "area2"],
                "study_sequence": ["topic1", "topic2", "topic3"],
                "time_allocation": {{
                    "weak_areas_percentage": 60,
                    "strong_areas_review": 25,
                    "practice_tests": 15
                }},
                "recommended_practice": [
                    {{
                        "topic": "topic name",
                        "question_types": ["type1", "type2"],
                        "difficulty_level": "level"
                    }}
                ],
                "confidence_building_tips": ["tip1", "tip2"],
                "revision_timeline": "suggested timeline for revision"
            }}
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text) if response.text.strip() else {}
            
            # Fallback if parsing fails
            if not result:
                result = {
                    "revision_guide": {
                        "focus_areas": weak_areas,
                        "study_sequence": weak_areas + strong_areas,
                        "time_allocation": {
                            "weak_areas_percentage": 60,
                            "strong_areas_review": 25,
                            "practice_tests": 15
                        },
                        "recommended_practice": [
                            {
                                "topic": area,
                                "question_types": ["conceptual", "application"],
                                "difficulty_level": "medium"
                            }
                            for area in weak_areas
                        ],
                        "confidence_building_tips": [
                            "Start with easier problems in weak areas",
                            "Practice consistently rather than cramming",
                            "Review mistakes regularly"
                        ],
                        "revision_timeline": "4-week plan focusing on weak areas initially"
                    }
                }
            
            return result
        except Exception as e:
            logger.error(f"Error generating revision guide: {str(e)}")
            return {
                "revision_guide": {
                    "focus_areas": weak_areas,
                    "study_sequence": weak_areas + strong_areas,
                    "time_allocation": {
                        "weak_areas_percentage": 60,
                        "strong_areas_review": 25,
                        "practice_tests": 15
                    },
                    "recommended_practice": [],
                    "confidence_building_tips": [],
                    "revision_timeline": "Standard 4-week revision plan"
                }
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