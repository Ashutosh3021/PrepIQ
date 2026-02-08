import logging
import re
from typing import List, Dict, Any, Tuple
import json
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)

# Lazy imports to prevent DLL errors
_spacy = None
_sentence_transformers = None

def _lazy_import_spacy():
    """Lazy import spacy to prevent DLL errors on startup"""
    global _spacy
    if _spacy is None:
        try:
            import spacy
            _spacy = spacy
            return spacy
        except Exception as e:
            logger.warning(f"Failed to import spacy: {e}")
            return None
    return _spacy

def _lazy_import_sentence_transformers():
    """Lazy import sentence_transformers"""
    global _sentence_transformers
    if _sentence_transformers is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_transformers = SentenceTransformer
            return SentenceTransformer
        except Exception as e:
            logger.warning(f"Failed to import sentence_transformers: {e}")
            return None
    return _sentence_transformers

class SyllabusAnalyzer:
    """
    NLP module to parse and understand syllabus documents, implement syllabus-to-question 
    correlation analysis, develop weighted importance scoring for syllabus topics, 
    and add curriculum mapping functionality.
    """
    
    def __init__(self):
        # Load spaCy model for advanced NLP preprocessing (lazy loading)
        self.nlp = None
        try:
            spacy_module = _lazy_import_spacy()
            if spacy_module:
                try:
                    self.nlp = spacy_module.load("en_core_web_sm")
                    logger.info("spaCy model loaded successfully")
                except OSError:
                    logger.warning("spaCy 'en_core_web_sm' model not found. Please install it with: python -m spacy download en_core_web_sm")
                    self.nlp = None
                except Exception as e:
                    logger.warning(f"Failed to load spaCy model: {e}")
                    self.nlp = None
        except Exception as e:
            logger.warning(f"spaCy not available: {e}. Using fallback preprocessing.")
            self.nlp = None
        
        # Load sentence transformer model for semantic similarity (lazy loading)
        self.sentence_model = None
        try:
            SentenceTransformer = _lazy_import_sentence_transformers()
            if SentenceTransformer:
                try:
                    self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("Sentence transformer model loaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to load sentence transformer model: {e}")
                    self.sentence_model = None
        except Exception as e:
            logger.warning(f"Sentence transformers not available: {e}. Using fallback similarity.")
            self.sentence_model = None
            
        # Initialize NLTK components
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            logger.warning("NLTK data not found. Please install NLTK data.")
            self.stop_words = set()
        
        # Predefined weights for different syllabus elements
        self.topic_weights = {
            'learning_objectives': 1.0,
            'course_outline': 0.8,
            'required_readings': 0.7,
            'assignments': 0.9,
            'exams': 1.0,
            'lectures': 0.6
        }
        
        # Patterns to identify important syllabus elements
        self.patterns = {
            'unit_pattern': r'(?:unit|chapter|module|section)\s+\d+[:\-\s]+([A-Za-z\s]+)',
            'topic_pattern': r'(?:topic|subject|theme|concept)\s*[:\-]\s*([A-Za-z\s]+)',
            'learning_objective_pattern': r'(?:learning\s+objective|objective|goal|outcome)\s*[:\-]\s*([A-Za-z\s]+)',
            'keyword_indicators': [
                'important', 'essential', 'critical', 'fundamental', 'key', 'basic', 
                'advanced', 'primary', 'major', 'core', 'required'
            ]
        }
    
    def preprocess_syllabus_text(self, text: str) -> str:
        """Clean and preprocess syllabus text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove page numbers and headers/footers
        text = re.sub(r'\b\d+\b', '', text)  # Remove standalone numbers
        text = re.sub(r'page\s+\d+', '', text, flags=re.IGNORECASE)
        
        return text
    
    def extract_syllabus_structure(self, syllabus_text: str) -> Dict[str, Any]:
        """Extract structural elements from syllabus text"""
        structure = {
            'course_title': '',
            'instructor': '',
            'course_code': '',
            'units': [],
            'topics': [],
            'learning_objectives': [],
            'grading_policy': '',
            'important_dates': []
        }
        
        # Process with spaCy if available
        if self.nlp:
            doc = self.nlp(syllabus_text)
            
            # Extract named entities that might be course information
            for ent in doc.ents:
                if ent.label_ in ['PERSON'] and not structure['instructor']:
                    structure['instructor'] = ent.text
                elif ent.label_ in ['ORG'] and not structure['course_title']:
                    structure['course_title'] = ent.text
            
            # Extract sentences that might contain important information
            sentences = [sent.text for sent in doc.sents]
        else:
            # Fallback: split by sentences
            sentences = sent_tokenize(syllabus_text)
        
        # Extract units and topics using regex patterns
        for sentence in sentences:
            # Extract units
            unit_matches = re.findall(self.patterns['unit_pattern'], sentence, re.IGNORECASE)
            for unit in unit_matches:
                unit_clean = unit.strip()
                if unit_clean and unit_clean not in structure['units']:
                    structure['units'].append(unit_clean)
            
            # Extract topics
            topic_matches = re.findall(self.patterns['topic_pattern'], sentence, re.IGNORECASE)
            for topic in topic_matches:
                topic_clean = topic.strip()
                if topic_clean and topic_clean not in structure['topics']:
                    structure['topics'].append(topic_clean)
            
            # Extract learning objectives
            lo_matches = re.findall(self.patterns['learning_objective_pattern'], sentence, re.IGNORECASE)
            for lo in lo_matches:
                lo_clean = lo.strip()
                if lo_clean and lo_clean not in structure['learning_objectives']:
                    structure['learning_objectives'].append(lo_clean)
            
            # Check for grading policy
            if 'grading' in sentence.lower() or 'grade' in sentence.lower():
                structure['grading_policy'] = sentence.strip()
            
            # Check for important dates
            date_patterns = [
                r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}',
                r'\d{1,2}/\d{1,2}(?:/\d{2,4})?',
                r'\d{4}-\d{2}-\d{2}'
            ]
            for pattern in date_patterns:
                dates = re.findall(pattern, sentence, re.IGNORECASE)
                structure['important_dates'].extend(dates)
        
        # Extract course code from text
        course_code_match = re.search(r'([A-Z]{2,4}\d{3,4})', syllabus_text)
        if course_code_match:
            structure['course_code'] = course_code_match.group(1)
        
        # Extract course title if not found via NER
        if not structure['course_title']:
            title_match = re.search(r'(?:course|subject):\s*([A-Za-z\s]+)', syllabus_text, re.IGNORECASE)
            if title_match:
                structure['course_title'] = title_match.group(1).strip()
        
        return structure
    
    def calculate_topic_importance(self, syllabus_structure: Dict[str, Any]) -> Dict[str, float]:
        """Calculate weighted importance scores for syllabus topics"""
        importance_scores = {}
        
        # Calculate importance based on different sections
        all_topics = []
        
        # Add units with higher weight
        for unit in syllabus_structure.get('units', []):
            all_topics.append(('unit', unit, self.topic_weights.get('course_outline', 0.8)))
        
        # Add topics
        for topic in syllabus_structure.get('topics', []):
            all_topics.append(('topic', topic, 0.5))  # Base weight
        
        # Add learning objectives with high weight
        for objective in syllabus_structure.get('learning_objectives', []):
            all_topics.append(('objective', objective, self.topic_weights.get('learning_objectives', 1.0)))
        
        # Calculate scores
        for category, topic, base_weight in all_topics:
            # Check if topic contains important keywords
            topic_lower = topic.lower()
            keyword_bonus = 0
            for keyword in self.patterns['keyword_indicators']:
                if keyword in topic_lower:
                    keyword_bonus += 0.3
            
            # Calculate final score
            final_score = min(base_weight + keyword_bonus, 1.0)
            importance_scores[topic] = round(final_score, 3)
        
        return importance_scores
    
    def map_syllabus_to_questions(self, syllabus_content: str, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map syllabus content to relevant questions based on semantic similarity"""
        if not self.sentence_model:
            logger.error("Sentence transformer model not available for syllabus-to-question mapping")
            return []
        
        try:
            # Extract syllabus structure
            syllabus_structure = self.extract_syllabus_structure(syllabus_content)
            
            # Calculate topic importance
            topic_importance = self.calculate_topic_importance(syllabus_structure)
            
            # Create embeddings for all syllabus topics
            syllabus_topics = list(topic_importance.keys())
            if not syllabus_topics:
                # If no topics found, use the whole syllabus content
                syllabus_embedding = self.sentence_model.encode([self.preprocess_syllabus_text(syllabus_content)])[0]
            else:
                # Create combined embedding from important topics
                syllabus_embeddings = self.sentence_model.encode(syllabus_topics)
                # Average the embeddings
                syllabus_embedding = np.mean(syllabus_embeddings, axis=0)
            
            mapped_questions = []
            for question in questions:
                question_text = question.get('text', '')
                if not question_text:
                    continue
                
                # Get embedding for question
                question_embedding = self.sentence_model.encode([question_text])[0]
                
                # Calculate similarity
                similarity = cosine_similarity([syllabus_embedding], [question_embedding])[0][0]
                
                # Find the most relevant syllabus topic for this question
                best_topic = None
                best_topic_similarity = 0
                if syllabus_topics:
                    question_vs_topics = self.sentence_model.encode(syllabus_topics + [question_text])
                    question_emb = question_vs_topics[-1].reshape(1, -1)
                    topics_embs = question_vs_topics[:-1]
                    
                    similarities = cosine_similarity(question_emb, topics_embs)[0]
                    best_idx = np.argmax(similarities)
                    best_topic = syllabus_topics[best_idx]
                    best_topic_similarity = float(similarities[best_idx])
                
                mapped_questions.append({
                    "question": question,
                    "overall_syllabus_relevance": float(similarity),
                    "most_relevant_topic": best_topic,
                    "topic_relevance": best_topic_similarity,
                    "topic_importance": topic_importance.get(best_topic, 0) if best_topic else 0,
                    "mapped_to_syllabus": similarity > 0.3,  # Threshold for mapping
                    "comprehensive_score": float(
                        (similarity * 0.4) + 
                        (topic_importance.get(best_topic, 0) * 0.4) + 
                        (best_topic_similarity * 0.2)
                    )
                })
            
            # Sort by comprehensive score
            mapped_questions.sort(key=lambda x: x['comprehensive_score'], reverse=True)
            return mapped_questions
            
        except Exception as e:
            logger.error(f"Error in syllabus-to-question mapping: {e}")
            return []
    
    def analyze_curriculum_alignment(self, syllabus_content: str, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze alignment between syllabus and questions"""
        try:
            # Map syllabus to questions
            mapped_questions = self.map_syllabus_to_questions(syllabus_content, questions)
            
            # Extract syllabus structure
            syllabus_structure = self.extract_syllabus_structure(syllabus_content)
            topic_importance = self.calculate_topic_importance(syllabus_structure)
            
            # Calculate coverage metrics
            covered_topics = set()
            uncovered_questions = []
            covered_questions = []
            
            for mapped_q in mapped_questions:
                if mapped_q['mapped_to_syllabus']:
                    covered_questions.append(mapped_q)
                    if mapped_q['most_relevant_topic']:
                        covered_topics.add(mapped_q['most_relevant_topic'])
                else:
                    uncovered_questions.append(mapped_q)
            
            # Calculate alignment metrics
            total_questions = len(questions)
            covered_count = len(covered_questions)
            coverage_percentage = (covered_count / total_questions * 100) if total_questions > 0 else 0
            
            total_topics = len(topic_importance)
            covered_topics_count = len(covered_topics)
            topic_coverage_percentage = (covered_topics_count / total_topics * 100) if total_topics > 0 else 0
            
            # Calculate average relevance scores
            avg_relevance = np.mean([mq['overall_syllabus_relevance'] for mq in mapped_questions]) if mapped_questions else 0
            avg_comprehensive_score = np.mean([mq['comprehensive_score'] for mq in mapped_questions]) if mapped_questions else 0
            
            # Identify gaps in curriculum
            uncovered_topics = set(topic_importance.keys()) - covered_topics
            gap_analysis = {
                "high_priority_gaps": [topic for topic in uncovered_topics 
                                      if topic_importance.get(topic, 0) > 0.7],
                "medium_priority_gaps": [topic for topic in uncovered_topics 
                                        if 0.4 <= topic_importance.get(topic, 0) <= 0.7],
                "low_priority_gaps": [topic for topic in uncovered_topics 
                                     if topic_importance.get(topic, 0) < 0.4]
            }
            
            return {
                "coverage_metrics": {
                    "total_questions": total_questions,
                    "covered_questions": covered_count,
                    "uncovered_questions": len(uncovered_questions),
                    "coverage_percentage": round(coverage_percentage, 2),
                    "topic_coverage_percentage": round(topic_coverage_percentage, 2),
                    "average_relevance": round(float(avg_relevance), 3),
                    "average_comprehensive_score": round(float(avg_comprehensive_score), 3)
                },
                "alignment_analysis": {
                    "well_aligned_questions": covered_questions[:10],  # Top 10 aligned
                    "poorly_aligned_questions": uncovered_questions[:10],  # Top 10 unaligned
                    "gap_analysis": gap_analysis
                },
                "syllabus_structure": syllabus_structure,
                "topic_importance": topic_importance
            }
            
        except Exception as e:
            logger.error(f"Error in curriculum alignment analysis: {e}")
            return {
                "coverage_metrics": {},
                "alignment_analysis": {},
                "syllabus_structure": {},
                "topic_importance": {}
            }
    
    def get_syllabus_insights(self, syllabus_content: str) -> Dict[str, Any]:
        """Generate insights from syllabus content"""
        try:
            # Extract structure
            structure = self.extract_syllabus_structure(syllabus_content)
            
            # Calculate topic importance
            topic_importance = self.calculate_topic_importance(structure)
            
            # Get important statistics
            stats = {
                "total_units": len(structure.get('units', [])),
                "total_topics": len(structure.get('topics', [])),
                "total_learning_objectives": len(structure.get('learning_objectives', [])),
                "has_grading_policy": bool(structure.get('grading_policy')),
                "important_dates_count": len(structure.get('important_dates', []))
            }
            
            # Identify high-priority topics
            high_priority_topics = {
                topic: score for topic, score in topic_importance.items() 
                if score >= 0.8
            }
            
            # Identify medium-priority topics
            medium_priority_topics = {
                topic: score for topic, score in topic_importance.items() 
                if 0.5 <= score < 0.8
            }
            
            # Identify low-priority topics
            low_priority_topics = {
                topic: score for topic, score in topic_importance.items() 
                if score < 0.5
            }
            
            return {
                "syllabus_structure": structure,
                "topic_importance": topic_importance,
                "statistics": stats,
                "priority_topics": {
                    "high": high_priority_topics,
                    "medium": medium_priority_topics,
                    "low": low_priority_topics
                },
                "recommendations": self._generate_recommendations(high_priority_topics, medium_priority_topics)
            }
            
        except Exception as e:
            logger.error(f"Error in syllabus insights generation: {e}")
            return {
                "syllabus_structure": {},
                "topic_importance": {},
                "statistics": {},
                "priority_topics": {},
                "recommendations": []
            }
    
    def _generate_recommendations(self, high_priority: Dict[str, float], medium_priority: Dict[str, float]) -> List[str]:
        """Generate study recommendations based on topic priorities"""
        recommendations = []
        
        if high_priority:
            recommendations.append(f"Focus heavily on high-priority topics: {', '.join(list(high_priority.keys())[:3])}")
        
        if medium_priority:
            recommendations.append(f"Spend moderate time on medium-priority topics: {', '.join(list(medium_priority.keys())[:3])}")
        
        if len(high_priority) > 3:
            recommendations.append(f"There are {len(high_priority)} high-priority topics that require focused attention")
        
        if not high_priority and not medium_priority:
            recommendations.append("Review the syllabus carefully to identify key topics for study")
        
        return recommendations


# Example usage and testing
if __name__ == "__main__":
    analyzer = SyllabusAnalyzer()
    
    # Sample syllabus content
    sample_syllabus = """
    Course: Introduction to Computer Science
    Course Code: CS101
    Instructor: Dr. Smith
    
    UNIT 1: Introduction to Programming
    - Basic concepts and fundamentals
    - Variables and data types
    - Control structures
    
    UNIT 2: Object-Oriented Programming  
    - Classes and objects (CRITICAL CONCEPT)
    - Inheritance and polymorphism (ESSENTIAL)
    - Encapsulation
    
    UNIT 3: Data Structures
    - Arrays and lists
    - Stacks and queues (IMPORTANT)
    - Trees and graphs
    
    LEARNING OBJECTIVES:
    - Understand fundamental programming concepts
    - Apply object-oriented design principles
    - Implement basic data structures
    """
    
    # Sample questions
    sample_questions = [
        {"text": "Explain object-oriented programming concepts", "marks": 10, "unit": "Unit 2"},
        {"text": "Describe the difference between stack and queue", "marks": 5, "unit": "Unit 3"},
        {"text": "What are variables and data types?", "marks": 3, "unit": "Unit 1"}
    ]
    
    # Test the analyzer
    insights = analyzer.get_syllabus_insights(sample_syllabus)
    print("Syllabus Insights:", json.dumps(insights, indent=2))
    
    alignment = analyzer.analyze_curriculum_alignment(sample_syllabus, sample_questions)
    print("\nCurriculum Alignment:", json.dumps(alignment, indent=2))