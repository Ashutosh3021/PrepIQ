from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import networkx as nx

from ..core.base_model import RecommendationModel
from ..core.config import settings


class TopicRecommender(RecommendationModel):
    """Hybrid recommendation system for educational topics combining collaborative and content-based filtering."""
    
    def __init__(self, version: str = "1.0.0"):
        super().__init__("topic_recommender", version)
        self.user_item_matrix = None
        self.topic_features = None
        self.user_features = None
        self.topic_similarity_matrix = None
        self.content_recommender = None
        self.collaborative_recommender = None
        self.feature_columns = [
            'difficulty_level', 'estimated_hours', 'popularity_score', 
            'success_rate', 'prerequisite_topics'
        ]
    
    def preprocess_data(self, data: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess user-topic interaction data and topic features."""
        # Extract user-topic interactions
        interactions = data.get('interactions', [])
        topics = data.get('topics', [])
        
        if not interactions or not topics:
            raise ValueError("Missing interactions or topics data")
        
        # Create user-item matrix
        interaction_df = pd.DataFrame(interactions)
        self.user_item_matrix = self._create_user_item_matrix(interaction_df)
        
        # Process topic features
        topic_df = pd.DataFrame(topics)
        self.topic_features = self._extract_topic_features(topic_df)
        
        # Scale features
        self.scaler = StandardScaler()
        scaled_features = self.scaler.fit_transform(self.topic_features)
        
        return self.user_item_matrix, scaled_features
    
    def _create_user_item_matrix(self, interaction_df: pd.DataFrame) -> np.ndarray:
        """Create user-item interaction matrix."""
        # Pivot to create user-topic matrix
        user_item_df = interaction_df.pivot_table(
            index='user_id',
            columns='topic_id',
            values='interaction_score',
            fill_value=0
        )
        
        return user_item_df.values
    
    def _extract_topic_features(self, topic_df: pd.DataFrame) -> np.ndarray:
        """Extract and process topic features."""
        features = []
        
        for _, topic in topic_df.iterrows():
            topic_features = []
            
            # Numerical features
            topic_features.append(topic.get('difficulty_level', 3))  # 1-5 scale
            topic_features.append(topic.get('estimated_hours', 2.0))
            
            # Popularity score (based on number of users who studied this topic)
            popularity = topic.get('popularity_score', 0.5)
            topic_features.append(popularity)
            
            # Success rate (average accuracy for this topic)
            success_rate = topic.get('success_rate', 0.7)
            topic_features.append(success_rate)
            
            # Prerequisite complexity (number of prerequisites)
            prereqs = topic.get('prerequisite_topics', [])
            topic_features.append(len(prereqs) if isinstance(prereqs, list) else 0)
            
            features.append(topic_features)
        
        return np.array(features)
    
    def train(self, X: np.ndarray, y: np.ndarray = None, **kwargs) -> Dict[str, float]:
        """Train the hybrid recommendation system."""
        # Train collaborative filtering component
        self.collaborative_recommender = self._train_collaborative_filtering()
        
        # Train content-based component
        self.content_recommender = self._train_content_based_filtering(X)
        
        # Create topic similarity matrix
        self.topic_similarity_matrix = cosine_similarity(X)
        
        # Update model metadata
        self.is_trained = True
        self.training_date = datetime.now(timezone.utc)
        self.metrics = {'training_complete': True}
        
        return self.metrics
    
    def _train_collaborative_filtering(self) -> NearestNeighbors:
        """Train collaborative filtering using user-item matrix."""
        # Use SVD for dimensionality reduction
        svd = TruncatedSVD(n_components=min(50, self.user_item_matrix.shape[1] - 1))
        user_factors = svd.fit_transform(self.user_item_matrix)
        
        # Create user similarity recommender
        recommender = NearestNeighbors(n_neighbors=10, metric='cosine')
        recommender.fit(user_factors)
        
        return recommender
    
    def _train_content_based_filtering(self, topic_features: np.ndarray) -> NearestNeighbors:
        """Train content-based filtering using topic features."""
        recommender = NearestNeighbors(n_neighbors=15, metric='cosine')
        recommender.fit(topic_features)
        return recommender
    
    def recommend(self, user_id: str, n_recommendations: int = 10, 
                 user_profile: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate topic recommendations for a user."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making recommendations")
        
        recommendations = []
        
        # Get collaborative filtering recommendations
        collab_recs = self._get_collaborative_recommendations(user_id, n_recommendations // 2)
        
        # Get content-based recommendations
        content_recs = self._get_content_based_recommendations(user_profile, n_recommendations // 2)
        
        # Combine recommendations with weighted scoring
        combined_recs = self._combine_recommendations(collab_recs, content_recs, user_profile)
        
        # Sort by score and limit to requested number
        recommendations = sorted(combined_recs, key=lambda x: x['score'], reverse=True)
        recommendations = recommendations[:n_recommendations]
        
        return recommendations
    
    def _get_collaborative_recommendations(self, user_id: str, n_recommendations: int) -> List[Dict[str, Any]]:
        """Get recommendations based on similar users."""
        # Find similar users (simplified - would need proper user indexing)
        user_index = hash(user_id) % len(self.user_item_matrix)
        user_vector = self.user_item_matrix[user_index: user_index + 1]
        
        # Get similar users
        distances, indices = self.collaborative_recommender.kneighbors(user_vector)
        
        # Aggregate topics from similar users
        topic_scores = {}
        for i, neighbor_idx in enumerate(indices[0]):
            if neighbor_idx != user_index:  # Skip the user themselves
                neighbor_topics = self.user_item_matrix[neighbor_idx]
                similarity = 1 - distances[0][i]  # Convert distance to similarity
                
                for topic_idx, score in enumerate(neighbor_topics):
                    if score > 0:  # User interacted with this topic
                        if topic_idx not in topic_scores:
                            topic_scores[topic_idx] = 0
                        topic_scores[topic_idx] += score * similarity
        
        # Convert to recommendation format
        recommendations = [
            {
                'topic_id': topic_idx,
                'score': score,
                'recommendation_type': 'collaborative'
            }
            for topic_idx, score in topic_scores.items()
        ]
        
        return sorted(recommendations, key=lambda x: x['score'], reverse=True)[:n_recommendations]
    
    def _get_content_based_recommendations(self, user_profile: Optional[Dict[str, Any]], 
                                         n_recommendations: int) -> List[Dict[str, Any]]:
        """Get recommendations based on user preferences and topic content."""
        if not user_profile:
            # Return popular topics if no profile
            topic_popularity = self.topic_features[:, 2]  # popularity score column
            top_indices = np.argsort(topic_popularity)[-n_recommendations:][::-1]
        else:
            # Create user preference vector
            preference_vector = self._create_user_preference_vector(user_profile)
            preference_vector = self.scaler.transform([preference_vector])
            
            # Find similar topics
            distances, indices = self.content_recommender.kneighbors(preference_vector)
            
            top_indices = indices[0][:n_recommendations]
        
        # Convert to recommendation format
        recommendations = [
            {
                'topic_id': topic_idx,
                'score': 1.0 / (1.0 + distances[0][i]) if 'distances' in locals() else 0.8,
                'recommendation_type': 'content_based'
            }
            for i, topic_idx in enumerate(top_indices)
        ]
        
        return recommendations
    
    def _create_user_preference_vector(self, user_profile: Dict[str, Any]) -> np.ndarray:
        """Create a preference vector based on user profile."""
        preference_vector = []
        
        # Preferred difficulty level (1-5)
        preferred_difficulty = user_profile.get('preferred_difficulty', 3)
        preference_vector.append(preferred_difficulty)
        
        # Preferred study time per topic (hours)
        preferred_hours = user_profile.get('preferred_study_time', 2.0)
        preference_vector.append(preferred_hours)
        
        # Popularity preference (0-1)
        popularity_preference = user_profile.get('popularity_preference', 0.5)
        preference_vector.append(popularity_preference)
        
        # Success rate preference (0-1)
        success_preference = user_profile.get('success_preference', 0.7)
        preference_vector.append(success_preference)
        
        # Prerequisite complexity preference
        complexity_preference = user_profile.get('complexity_preference', 1)
        preference_vector.append(complexity_preference)
        
        return np.array(preference_vector)
    
    def _combine_recommendations(self, collab_recs: List[Dict], content_recs: List[Dict], 
                               user_profile: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combine collaborative and content-based recommendations with weighting."""
        # Weight based on user profile confidence
        if user_profile and user_profile.get('profile_confidence', 0) > 0.7:
            collab_weight = 0.3
            content_weight = 0.7
        else:
            collab_weight = 0.6
            content_weight = 0.4
        
        # Combine recommendations
        combined_scores = {}
        
        # Add collaborative recommendations
        for rec in collab_recs:
            topic_id = rec['topic_id']
            combined_scores[topic_id] = combined_scores.get(topic_id, 0) + rec['score'] * collab_weight
            if 'recommendation_type' not in rec:
                rec['recommendation_type'] = 'collaborative'
        
        # Add content-based recommendations
        for rec in content_recs:
            topic_id = rec['topic_id']
            combined_scores[topic_id] = combined_scores.get(topic_id, 0) + rec['score'] * content_weight
            if 'recommendation_type' not in rec:
                rec['recommendation_type'] = 'content_based'
        
        # Convert to final format
        combined_recs = []
        for topic_id, score in combined_scores.items():
            combined_recs.append({
                'topic_id': topic_id,
                'score': score,
                'recommendation_type': 'hybrid'
            })
        
        return combined_recs
    
    def get_topic_details(self, topic_ids: List[int], 
                         topic_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get detailed information for recommended topics."""
        topic_details = []
        
        topic_lookup = {topic['id']: topic for topic in topic_data}
        
        for topic_id in topic_ids:
            if topic_id in topic_lookup:
                topic = topic_lookup[topic_id]
                topic_details.append({
                    'id': topic['id'],
                    'name': topic['name'],
                    'subject': topic.get('subject', 'Unknown'),
                    'difficulty_level': topic.get('difficulty_level', 3),
                    'estimated_hours': topic.get('estimated_hours', 0),
                    'description': topic.get('description', ''),
                    'prerequisites': topic.get('prerequisites', [])
                })
        
        return topic_details
    
    def generate_study_plan(self, recommendations: List[Dict[str, Any]], 
                          time_constraint: int = 180) -> List[Dict[str, Any]]:
        """Generate a personalized study plan based on recommendations."""
        study_plan = []
        total_time = 0
        
        for rec in recommendations:
            topic_details = rec.get('topic_details', {})
            estimated_hours = topic_details.get('estimated_hours', 2)
            
            if total_time + (estimated_hours * 60) <= time_constraint:
                study_plan.append({
                    'topic_id': rec['topic_id'],
                    'topic_name': topic_details.get('name', 'Unknown Topic'),
                    'estimated_hours': estimated_hours,
                    'priority': rec['score'],
                    'difficulty': topic_details.get('difficulty_level', 3),
                    'scheduled_days': max(1, int(estimated_hours))
                })
                total_time += estimated_hours * 60
        
        return study_plan