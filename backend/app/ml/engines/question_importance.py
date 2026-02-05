from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
import re
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from transformers import AutoTokenizer, AutoModel
import torch
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings('ignore')

from .core.base_model import BaseModel
from .core.config import settings


class EnhancedQuestionAnalyzer(BaseModel):
    """Enhanced question importance predictor using hybrid NLP approach (TF-IDF + Transformers)."""
    
    def __init__(self, version: str = "2.0.0"):
        super().__init__("enhanced_question_analyzer", version)
        self.vectorizer = TfidfVectorizer(
            max_features=2000,
            stop_words='english',
            ngram_range=(1, 3),
            lowercase=True,
            min_df=2,
            max_df=0.95
        )
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.transformer_model = None
        self.transformer_tokenizer = None
        self.sentence_transformer = None
        self.is_transformer_loaded = False
        self.feature_columns = [
            'frequency_score', 'topic_importance', 'difficulty_level', 
            'marks_weight', 'concept_density', 'past_appearance_count'
        ]
    
    def load_transformer_models(self):
        """Load transformer models for enhanced NLP capabilities."""
        try:
            # Load sentence transformer for semantic similarity
            self.sentence_transformer = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Load BERT tokenizer and model for advanced analysis
            model_name = 'bert-base-uncased'
            self.transformer_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.transformer_model = AutoModel.from_pretrained(model_name)
            
            self.is_transformer_loaded = True
            self.logger.info("Transformer models loaded successfully")
        except Exception as e:
            self.logger.warning(f"Failed to load transformer models: {str(e)}")
            self.is_transformer_loaded = False
    
    def preprocess_text(self, text: str) -> str:
        """Advanced text preprocessing with lemmatization."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and lemmatize
        processed_tokens = [
            self.lemmatizer.lemmatize(token) 
            for token in tokens 
            if token not in self.stop_words and len(token) > 2
        ]
        
        return ' '.join(processed_tokens)
    
    def extract_concepts(self, text: str) -> List[str]:
        """Extract key concepts from question text."""
        # Simple concept extraction (can be enhanced with NER)
        words = text.split()
        # Filter for potentially important terms (nouns, technical terms)
        concepts = [word for word in words if len(word) > 3 and word.isalpha()]
        return concepts[:10]  # Limit to top 10 concepts
    
    def calculate_semantic_similarity(self, questions: List[str]) -> np.ndarray:
        """Calculate semantic similarity between questions using transformers."""
        if not self.is_transformer_loaded or self.sentence_transformer is None:
            # Fallback to TF-IDF similarity
            tfidf_matrix = self.vectorizer.fit_transform(questions)
            return cosine_similarity(tfidf_matrix)
        
        try:
            # Get sentence embeddings
            embeddings = self.sentence_transformer.encode(questions)
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(embeddings)
            return similarity_matrix
        except Exception as e:
            self.logger.warning(f"Semantic similarity calculation failed: {str(e)}")
            # Fallback to TF-IDF
            tfidf_matrix = self.vectorizer.fit_transform(questions)
            return cosine_similarity(tfidf_matrix)
    
    def preprocess_data(self, data: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[Dict]]:
        """Preprocess question data for analysis."""
        if not data:
            raise ValueError("No data provided for preprocessing")
        
        # Preprocess questions
        processed_questions = []
        for item in data:
            processed_text = self.preprocess_text(item.get('text', ''))
            if processed_text:
                processed_questions.append({
                    **item,
                    'processed_text': processed_text,
                    'concepts': self.extract_concepts(processed_text)
                })
        
        if not processed_questions:
            raise ValueError("No valid questions after preprocessing")
        
        # Create TF-IDF features
        question_texts = [q['processed_text'] for q in processed_questions]
        tfidf_features = self.vectorizer.fit_transform(question_texts)
        
        return tfidf_features.toarray(), processed_questions
    
    def train(self, X: np.ndarray, processed_questions: List[Dict], **kwargs) -> Dict[str, float]:
        """Train the enhanced question analyzer."""
        # Perform topic modeling and clustering
        try:
            # K-means clustering to identify question types
            n_clusters = min(10, len(processed_questions) // 3)
            if n_clusters > 1:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                clusters = kmeans.fit_predict(X)
            else:
                clusters = np.zeros(len(processed_questions))
            
            # Calculate topic importance scores
            topic_scores = self._calculate_topic_importance(processed_questions, X)
            
            # Calculate frequency-based scores
            frequency_scores = self._calculate_frequency_scores(processed_questions)
            
            # Combine all features
            combined_features = self._combine_features(
                X, clusters, topic_scores, frequency_scores, processed_questions
            )
            
            # Store training results
            self.training_data = {
                'clusters': clusters,
                'topic_scores': topic_scores,
                'frequency_scores': frequency_scores,
                'combined_features': combined_features,
                'processed_questions': processed_questions
            }
            
            # Calculate training metrics
            metrics = {
                'training_samples': len(processed_questions),
                'feature_dimensions': X.shape[1],
                'clusters_created': len(np.unique(clusters)),
                'avg_topic_score': float(np.mean(topic_scores)),
                'avg_frequency_score': float(np.mean(frequency_scores))
            }
            
            # Update model metadata
            self.is_trained = True
            self.training_date = datetime.utcnow()
            self.metrics = metrics
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Training failed: {str(e)}")
            raise
    
    def _calculate_topic_importance(self, questions: List[Dict], tfidf_features: np.ndarray) -> np.ndarray:
        """Calculate topic importance scores based on TF-IDF and question metadata."""
        scores = []
        
        for i, question in enumerate(questions):
            # Base TF-IDF importance
            tfidf_score = np.mean(tfidf_features[i]) if len(tfidf_features[i]) > 0 else 0
            
            # Topic frequency bonus
            topic = question.get('topic', '').lower()
            topic_bonus = 0.1 if any(important in topic for important in 
                                   ['important', 'key', 'fundamental', 'core']) else 0
            
            # Marks weight bonus
            marks = question.get('marks', 1)
            marks_bonus = marks / 10.0  # Normalize to 0-1
            
            # Concept density bonus
            concepts = question.get('concepts', [])
            concept_bonus = len(concepts) / 20.0  # Normalize
            
            # Combine scores
            total_score = (tfidf_score * 0.4 + 
                          topic_bonus * 0.2 + 
                          marks_bonus * 0.2 + 
                          concept_bonus * 0.2)
            
            scores.append(total_score)
        
        return np.array(scores)
    
    def _calculate_frequency_scores(self, questions: List[Dict]) -> np.ndarray:
        """Calculate frequency-based importance scores."""
        # Extract all concepts
        all_concepts = []
        for question in questions:
            all_concepts.extend(question.get('concepts', []))
        
        # Calculate concept frequencies
        concept_freq = Counter(all_concepts)
        max_freq = max(concept_freq.values()) if concept_freq else 1
        
        scores = []
        for question in questions:
            concepts = question.get('concepts', [])
            if not concepts:
                scores.append(0.1)  # Minimum score
                continue
            
            # Calculate average frequency score for concepts in this question
            freq_scores = [concept_freq[concept] / max_freq for concept in concepts]
            avg_freq_score = np.mean(freq_scores)
            
            # Bonus for questions with multiple high-frequency concepts
            diversity_bonus = len([s for s in freq_scores if s > 0.5]) / len(concepts)
            
            final_score = avg_freq_score * 0.7 + diversity_bonus * 0.3
            scores.append(final_score)
        
        return np.array(scores)
    
    def _combine_features(self, tfidf_features: np.ndarray, clusters: np.ndarray,
                         topic_scores: np.ndarray, frequency_scores: np.ndarray,
                         questions: List[Dict]) -> np.ndarray:
        """Combine all features into a single feature matrix."""
        # Normalize all scores to 0-1 range
        normalized_topic = (topic_scores - np.min(topic_scores)) / (np.max(topic_scores) - np.min(topic_scores) + 1e-8)
        normalized_frequency = (frequency_scores - np.min(frequency_scores)) / (np.max(frequency_scores) - np.min(frequency_scores) + 1e-8)
        
        # Create combined feature matrix
        combined = np.column_stack([
            tfidf_features,
            normalized_topic.reshape(-1, 1),
            normalized_frequency.reshape(-1, 1),
            clusters.reshape(-1, 1)
        ])
        
        return combined
    
    def predict(self, X: np.ndarray = None) -> List[Dict[str, Any]]:
        """Analyze questions and predict importance scores."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        if X is None:
            # Use training data for prediction
            processed_questions = self.training_data['processed_questions']
        else:
            # Process new data (simplified - would need full preprocessing pipeline)
            raise NotImplementedError("Prediction on new data requires full preprocessing pipeline")
        
        # Calculate final importance scores
        importance_scores = self._calculate_final_scores(processed_questions)
        
        # Generate predictions
        predictions = []
        for i, (question, score) in enumerate(zip(processed_questions, importance_scores)):
            predictions.append({
                'question_id': question.get('id', f'q_{i}'),
                'question_text': question.get('text', ''),
                'importance_score': float(score),
                'confidence': float(self._calculate_confidence(score)),
                'category': self._categorize_importance(score),
                'key_concepts': question.get('concepts', [])[:5],
                'recommended_action': self._generate_recommendation(score),
                'similar_questions': self._find_similar_questions(i, processed_questions)
            })
        
        # Sort by importance score
        predictions.sort(key=lambda x: x['importance_score'], reverse=True)
        
        return predictions
    
    def _calculate_final_scores(self, questions: List[Dict]) -> np.ndarray:
        """Calculate final importance scores combining all factors."""
        scores = []
        
        for question in questions:
            # Weighted combination of factors
            topic_importance = question.get('topic_importance', 0.5)
            frequency_score = question.get('frequency_score', 0.3)
            marks = question.get('marks', 1)
            difficulty = question.get('difficulty', 3)
            
            # Calculate weighted score
            final_score = (
                topic_importance * 0.35 +
                frequency_score * 0.30 +
                (marks / 10) * 0.20 +
                (6 - difficulty) / 5 * 0.15  # Inverse difficulty (harder = more important)
            )
            
            scores.append(final_score)
        
        return np.array(scores)
    
    def _calculate_confidence(self, score: float) -> float:
        """Calculate confidence level for the prediction."""
        # Higher confidence for extreme scores (very high or very low)
        if score > 0.8 or score < 0.2:
            return min(0.95, 0.7 + abs(score - 0.5) * 0.5)
        else:
            return 0.6 + (0.8 - abs(score - 0.5)) * 0.4
    
    def _categorize_importance(self, score: float) -> str:
        """Categorize importance level."""
        if score >= 0.8:
            return "Very High"
        elif score >= 0.6:
            return "High"
        elif score >= 0.4:
            return "Medium"
        elif score >= 0.2:
            return "Low"
        else:
            return "Very Low"
    
    def _generate_recommendation(self, score: float) -> str:
        """Generate study recommendation based on importance score."""
        if score >= 0.8:
            return "High priority - Master this topic thoroughly"
        elif score >= 0.6:
            return "Important - Focus on understanding key concepts"
        elif score >= 0.4:
            return "Review basics and practice moderately"
        else:
            return "Low priority - Brief review if time permits"
    
    def _find_similar_questions(self, question_index: int, questions: List[Dict]) -> List[str]:
        """Find similar questions for practice grouping."""
        if len(questions) < 2:
            return []
        
        # Get question texts
        question_texts = [q['processed_text'] for q in questions]
        
        # Calculate similarity matrix
        similarity_matrix = self.calculate_semantic_similarity(question_texts)
        
        # Find most similar questions (excluding self)
        similarities = similarity_matrix[question_index]
        similar_indices = np.argsort(similarities)[::-1][1:4]  # Top 3 similar (excluding self)
        
        return [questions[i].get('id', f'q_{i}') for i in similar_indices]
    
    def analyze_question_patterns(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns and trends in questions."""
        if not questions:
            return {}
        
        # Extract patterns
        patterns = {
            'total_questions': len(questions),
            'average_marks': np.mean([q.get('marks', 0) for q in questions]),
            'difficulty_distribution': self._analyze_difficulty(questions),
            'topic_distribution': self._analyze_topics(questions),
            'common_concepts': self._find_common_concepts(questions),
            'question_types': self._analyze_question_types(questions)
        }
        
        return patterns
    
    def _analyze_difficulty(self, questions: List[Dict]) -> Dict[str, int]:
        """Analyze difficulty distribution."""
        difficulties = [q.get('difficulty', 3) for q in questions]
        difficulty_counts = Counter(difficulties)
        return dict(difficulty_counts)
    
    def _analyze_topics(self, questions: List[Dict]) -> Dict[str, int]:
        """Analyze topic distribution."""
        topics = [q.get('topic', 'Unknown') for q in questions]
        topic_counts = Counter(topics)
        return dict(topic_counts)
    
    def _find_common_concepts(self, questions: List[Dict]) -> List[Dict[str, Any]]:
        """Find most common concepts across questions."""
        all_concepts = []
        for question in questions:
            all_concepts.extend(question.get('concepts', []))
        
        concept_freq = Counter(all_concepts)
        common_concepts = [
            {'concept': concept, 'frequency': freq}
            for concept, freq in concept_freq.most_common(10)
        ]
        
        return common_concepts
    
    def _analyze_question_types(self, questions: List[Dict]) -> Dict[str, int]:
        """Analyze question type distribution."""
        types = [q.get('type', 'Unknown') for q in questions]
        type_counts = Counter(types)
        return dict(type_counts)
    
    def generate_study_guide(self, predictions: List[Dict[str, Any]], 
                           time_limit: int = 180) -> Dict[str, Any]:
        """Generate a personalized study guide based on question importance."""
        # Sort by importance
        important_questions = sorted(predictions, key=lambda x: x['importance_score'], reverse=True)
        
        study_guide = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': [],
            'time_allocation': {},
            'total_estimated_time': 0
        }
        
        time_remaining = time_limit
        
        for question in important_questions:
            importance = question['importance_score']
            estimated_time = question.get('estimated_time', 30)  # Default 30 minutes
            
            if time_remaining >= estimated_time:
                if importance >= 0.7:
                    study_guide['high_priority'].append(question)
                elif importance >= 0.4:
                    study_guide['medium_priority'].append(question)
                else:
                    study_guide['low_priority'].append(question)
                
                time_remaining -= estimated_time
                study_guide['total_estimated_time'] += estimated_time
        
        # Calculate time allocation percentages
        total_time = study_guide['total_estimated_time']
        if total_time > 0:
            study_guide['time_allocation'] = {
                'high_priority': len(study_guide['high_priority']) * 100 / len(predictions),
                'medium_priority': len(study_guide['medium_priority']) * 100 / len(predictions),
                'low_priority': len(study_guide['low_priority']) * 100 / len(predictions)
            }
        
        return study_guide


# Lightweight version for deployment without transformers
class LightweightQuestionAnalyzer(EnhancedQuestionAnalyzer):
    """Lightweight version that doesn't require transformer models."""
    
    def __init__(self, version: str = "2.0.0"):
        super().__init__(version)
        self.model_name = "lightweight_question_analyzer"
        # Skip transformer loading
        self.is_transformer_loaded = False
    
    def calculate_semantic_similarity(self, questions: List[str]) -> np.ndarray:
        """Use TF-IDF similarity instead of transformers."""
        tfidf_matrix = self.vectorizer.fit_transform(questions)
        return cosine_similarity(tfidf_matrix)