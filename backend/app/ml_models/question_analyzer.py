import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import LatentDirichletAllocation
from typing import List, Dict, Any, Tuple
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class QuestionAnalyzer:
    """
    Machine Learning model for analyzing question patterns and predicting likely exam questions
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.lda_model = LatentDirichletAllocation(
            n_components=10,  # Number of topics to extract
            random_state=42,
            max_iter=10
        )
        self.kmeans_model = KMeans(
            n_clusters=5,
            random_state=42
        )
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis"""
        # Remove special characters and normalize
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
        text = text.strip().lower()
        return text
    
    def extract_questions_features(self, questions: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str]]:
        """Extract features from questions for ML analysis"""
        texts = []
        processed_questions = []
        
        for question in questions:
            text = self.preprocess_text(question.get('text', ''))
            if len(text) > 10:  # Only process substantial questions
                texts.append(text)
                processed_questions.append(question)
        
        if not texts:
            return np.array([]), []
        
        # Vectorize the text
        try:
            vectors = self.vectorizer.fit_transform(texts).toarray()
        except ValueError:
            # If no features found, return empty arrays
            return np.array([]), processed_questions
        
        return vectors, processed_questions
    
    def analyze_patterns(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in questions to identify topics and trends"""
        if not questions:
            return {
                "topics": [],
                "frequencies": {},
                "patterns": [],
                "trends": [],
                "predicted_questions": []
            }
        
        # Extract features
        vectors, processed_questions = self.extract_questions_features(questions)
        
        if vectors.size == 0:
            return {
                "topics": [],
                "frequencies": {},
                "patterns": [],
                "trends": [],
                "predicted_questions": []
            }
        
        # Perform topic modeling using LDA
        try:
            topics = self.lda_model.fit_transform(vectors)
        except Exception as e:
            logger.error(f"Error in LDA topic modeling: {str(e)}")
            topics = np.zeros((len(processed_questions), 10))
        
        # Perform clustering to identify question types
        try:
            clusters = self.kmeans_model.fit_predict(vectors)
        except Exception as e:
            logger.error(f"Error in KMeans clustering: {str(e)}")
            clusters = np.zeros(len(processed_questions))
        
        # Analyze frequencies of topics
        topic_frequencies = {}
        for i, topic_dist in enumerate(topics):
            dominant_topic = np.argmax(topic_dist)
            topic_frequencies[dominant_topic] = topic_frequencies.get(dominant_topic, 0) + 1
        
        # Identify question patterns based on clustering
        cluster_analysis = {}
        for i, cluster_id in enumerate(clusters):
            if cluster_id not in cluster_analysis:
                cluster_analysis[cluster_id] = {
                    "count": 0,
                    "questions": [],
                    "avg_length": 0
                }
            cluster_analysis[cluster_id]["count"] += 1
            cluster_analysis[cluster_id]["questions"].append(processed_questions[i])
            cluster_analysis[cluster_id]["avg_length"] += len(processed_questions[i].get("text", ""))
        
        # Calculate average lengths
        for cluster_id in cluster_analysis:
            count = cluster_analysis[cluster_id]["count"]
            if count > 0:
                cluster_analysis[cluster_id]["avg_length"] /= count
        
        # Generate predictions based on analysis
        predictions = self._generate_predictions(processed_questions, topic_frequencies, cluster_analysis)
        
        return {
            "topics": [
                {
                    "topic_id": topic_id,
                    "frequency": freq,
                    "percentage": round((freq / len(processed_questions)) * 100, 2) if processed_questions else 0
                }
                for topic_id, freq in topic_frequencies.items()
            ],
            "frequencies": topic_frequencies,
            "patterns": [
                {
                    "cluster_id": cluster_id,
                    "count": analysis["count"],
                    "avg_length": analysis["avg_length"],
                    "sample_questions": [q.get("text", "")[:100] for q in analysis["questions"][:3]]
                }
                for cluster_id, analysis in cluster_analysis.items()
            ],
            "trends": self._analyze_trends(processed_questions),
            "predicted_questions": predictions
        }
    
    def _analyze_trends(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze temporal and frequency trends in questions"""
        trends = []
        
        # Analyze by marks distribution
        marks_dist = {}
        for q in questions:
            marks = q.get('marks', 0)
            marks_dist[marks] = marks_dist.get(marks, 0) + 1
        
        # Analyze by unit distribution
        unit_dist = {}
        for q in questions:
            unit = q.get('unit', 'Unknown')
            unit_dist[unit] = unit_dist.get(unit, 0) + 1
        
        trends.append({
            "type": "marks_distribution",
            "data": marks_dist
        })
        
        trends.append({
            "type": "unit_distribution", 
            "data": unit_dist
        })
        
        # Identify most frequent units
        if unit_dist:
            most_frequent_unit = max(unit_dist, key=unit_dist.get)
            trends.append({
                "type": "most_frequent_unit",
                "unit": most_frequent_unit,
                "frequency": unit_dist[most_frequent_unit]
            })
        
        return trends
    
    def _generate_predictions(self, questions: List[Dict[str, Any]], topic_frequencies: Dict[int, int], cluster_analysis: Dict[int, Any]) -> List[Dict[str, Any]]:
        """Generate predicted questions based on analysis"""
        predictions = []
        
        if not questions:
            return predictions
        
        # Identify the most frequent topics and clusters
        if topic_frequencies:
            most_frequent_topic = max(topic_frequencies, key=topic_frequencies.get)
            topic_percentage = (topic_frequencies[most_frequent_topic] / len(questions)) * 100
            
            # Generate a prediction based on the most frequent topic
            predictions.append({
                "question_number": 1,
                "text": f"Predicted question based on Topic {most_frequent_topic} pattern analysis",
                "marks": self._estimate_common_marks(questions),
                "unit": self._estimate_common_unit(questions),
                "probability": "high" if topic_percentage > 30 else "moderate",
                "reasoning": f"Based on Topic {most_frequent_topic} being the most frequent ({topic_percentage:.1f}%)",
                "confidence_score": min(topic_percentage / 100, 1.0)
            })
        
        # Add more predictions based on cluster analysis
        if cluster_analysis:
            for cluster_id, analysis in list(cluster_analysis.items())[:2]:  # Take top 2 clusters
                if analysis["count"] > 1:  # Only consider clusters with multiple questions
                    predictions.append({
                        "question_number": len(predictions) + 1,
                        "text": f"Predicted question based on Cluster {cluster_id} pattern analysis",
                        "marks": self._estimate_common_marks(questions),
                        "unit": self._estimate_common_unit(questions),
                        "probability": "moderate" if analysis["count"] > 2 else "low",
                        "reasoning": f"Based on Cluster {cluster_id} pattern with {analysis['count']} similar questions",
                        "confidence_score": min(analysis["count"] / len(questions), 1.0)
                    })
        
        return predictions
    
    def _estimate_common_marks(self, questions: List[Dict[str, Any]]) -> int:
        """Estimate the most common marks value"""
        marks_list = [q.get('marks', 2) for q in questions if q.get('marks')]
        if marks_list:
            # Return the most common marks value
            from collections import Counter
            counter = Counter(marks_list)
            return counter.most_common(1)[0][0]
        return 5  # Default
    
    def _estimate_common_unit(self, questions: List[Dict[str, Any]]) -> str:
        """Estimate the most common unit"""
        unit_list = [q.get('unit', 'Unknown') for q in questions if q.get('unit') and q.get('unit') != 'Unknown']
        if unit_list:
            # Return the most common unit
            from collections import Counter
            counter = Counter(unit_list)
            return counter.most_common(1)[0][0]
        return "General"
    
    def predict_exam_questions(self, historical_questions: List[Dict[str, Any]], num_predictions: int = 5) -> List[Dict[str, Any]]:
        """Main method to predict exam questions based on historical data"""
        try:
            analysis = self.analyze_patterns(historical_questions)
            predictions = analysis.get("predicted_questions", [])
            
            # Ensure we have enough predictions
            while len(predictions) < num_predictions:
                # Generate additional predictions if needed
                additional_pred = {
                    "question_number": len(predictions) + 1,
                    "text": f"Additional predicted question based on pattern analysis",
                    "marks": self._estimate_common_marks(historical_questions),
                    "unit": self._estimate_common_unit(historical_questions),
                    "probability": "low",
                    "reasoning": "Generated based on overall pattern analysis",
                    "confidence_score": 0.5
                }
                predictions.append(additional_pred)
            
            # Limit to requested number
            return predictions[:num_predictions]
        
        except Exception as e:
            logger.error(f"Error in predicting exam questions: {str(e)}")
            # Return fallback predictions
            return [
                {
                    "question_number": i+1,
                    "text": f"Fallback predicted question {i+1}",
                    "marks": 5,
                    "unit": "General",
                    "probability": "low",
                    "reasoning": "Fallback prediction due to analysis error",
                    "confidence_score": 0.1
                }
                for i in range(num_predictions)
            ]