from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split, cross_val_score
from imblearn.over_sampling import SMOTE
# import xgboost as xgb

from ..core.base_model import ClassificationModel
from ..core.config import settings


class FocusAreaIdentifier(ClassificationModel):
    """Classification model to identify weak areas and focus topics for users."""
    
    def __init__(self, version: str = "1.0.0"):
        super().__init__("focus_area_identifier", version)
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        self.scaler = StandardScaler()
        self.feature_columns = [
            'accuracy_rate',           # 0-100 percentage
            'attempts_count',          # Number of attempts
            'average_time_taken',      # Average time per question (minutes)
            'confidence_level',        # Self-reported confidence 1-5
            'topic_difficulty',        # Topic difficulty 1-5
            'question_complexity',     # Average complexity of questions
            'time_since_last_practice', # Days since last practice
            'progress_trend',          # Trend in performance -1 to 1
            'error_patterns_score'     # Score indicating consistent error patterns
        ]
        self.target_column = 'needs_focus'  # Binary: 1 if needs focus, 0 otherwise
        self.classes_ = np.array([0, 1])
    
    def preprocess_data(self, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocess data for focus area identification."""
        # Validate required columns
        required_columns = set(self.feature_columns + [self.target_column])
        missing_columns = required_columns - set(data.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Extract features and target
        X = data[self.feature_columns].values
        y = data[self.target_column].values
        
        # Handle missing values
        X = pd.DataFrame(X, columns=self.feature_columns).fillna({
            'accuracy_rate': 50,
            'attempts_count': 1,
            'average_time_taken': 5.0,
            'confidence_level': 3,
            'topic_difficulty': 3,
            'question_complexity': 3,
            'time_since_last_practice': 30,
            'progress_trend': 0,
            'error_patterns_score': 0.5
        }).values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y
    
    def create_synthetic_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create additional synthetic features to improve model performance."""
        df = data.copy()
        
        # Performance consistency score (lower std = more consistent)
        df['performance_consistency'] = 1 - (df['accuracy_std'] / 100)  # Assuming accuracy_std column exists
        
        # Time pressure indicator (higher time taken relative to difficulty)
        df['time_pressure'] = df['average_time_taken'] / (df['topic_difficulty'] + 1)
        
        # Learning plateau indicator (low trend + high attempts)
        df['plateau_indicator'] = (df['progress_trend'] < 0.1) & (df['attempts_count'] > 10)
        df['plateau_indicator'] = df['plateau_indicator'].astype(int)
        
        # Knowledge gap indicator (high difficulty + low accuracy)
        df['knowledge_gap'] = (df['topic_difficulty'] >= 4) & (df['accuracy_rate'] <= 60)
        df['knowledge_gap'] = df['knowledge_gap'].astype(int)
        
        # Recent improvement score (negative trend * confidence adjustment)
        df['improvement_potential'] = np.where(
            df['progress_trend'] < 0,
            abs(df['progress_trend']) * (5 - df['confidence_level']) / 4,
            0
        )
        
        # Add these new features to feature columns
        self.feature_columns.extend([
            'performance_consistency',
            'time_pressure',
            'plateau_indicator',
            'knowledge_gap',
            'improvement_potential'
        ])
        
        return df
    
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs) -> Dict[str, float]:
        """Train the focus area identification model."""
        # Handle class imbalance
        smote = SMOTE(random_state=42)
        X_balanced, y_balanced = smote.fit_resample(X, y)
        
        # Split data for validation
        X_train, X_val, y_train, y_val = train_test_split(
            X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate model
        metrics = self.evaluate(X_val, y_val)
        
        # Cross-validation score
        cv_scores = cross_val_score(self.model, X_balanced, y_balanced, cv=5)
        metrics['cv_mean_accuracy'] = float(cv_scores.mean())
        metrics['cv_std_accuracy'] = float(cv_scores.std())
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))
            metrics['feature_importance'] = feature_importance
        
        # Update model metadata
        self.is_trained = True
        self.training_date = datetime.now(timezone.utc)
        self.metrics = metrics
        self.classes_ = np.unique(y_train)
        
        return metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict whether topics need focus."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        return self.model.predict(X)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Get prediction probabilities."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        return self.model.predict_proba(X)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance."""
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # Make predictions
        y_pred = self.predict(X)
        y_proba = self.predict_proba(X)
        
        # Calculate metrics
        accuracy = accuracy_score(y, y_pred)
        report = classification_report(y, y_pred, output_dict=True, zero_division=0)
        
        # Confusion matrix
        cm = confusion_matrix(y, y_pred)
        
        metrics = {
            'accuracy': float(accuracy),
            'precision_class_1': float(report['1']['precision']) if '1' in report else 0,
            'recall_class_1': float(report['1']['recall']) if '1' in report else 0,
            'f1_score_class_1': float(report['1']['f1-score']) if '1' in report else 0,
            'precision_class_0': float(report['0']['precision']) if '0' in report else 0,
            'recall_class_0': float(report['0']['recall']) if '0' in report else 0,
            'f1_score_class_0': float(report['0']['f1-score']) if '0' in report else 0,
            'confusion_matrix': cm.tolist()
        }
        
        return metrics
    
    def identify_focus_areas(self, user_performance_data: pd.DataFrame, 
                           user_id: str) -> List[Dict[str, Any]]:
        """Identify focus areas for a specific user."""
        if not self.is_trained:
            raise ValueError("Model must be trained before identifying focus areas")
        
        # Preprocess user data
        processed_data = self.create_synthetic_features(user_performance_data)
        X, _ = self.preprocess_data(processed_data)
        
        # Make predictions
        predictions = self.predict(X)
        probabilities = self.predict_proba(X)
        
        # Create focus area recommendations
        focus_areas = []
        for i, (prediction, proba) in enumerate(zip(predictions, probabilities)):
            if prediction == 1:  # Needs focus
                topic_data = user_performance_data.iloc[i]
                focus_areas.append({
                    'user_id': user_id,
                    'topic_id': topic_data.get('topic_id', 'unknown'),
                    'topic_name': topic_data.get('topic_name', 'Unknown Topic'),
                    'focus_probability': float(proba[1]),  # Probability of needing focus
                    'current_accuracy': float(topic_data.get('accuracy_rate', 0)),
                    'attempts_count': int(topic_data.get('attempts_count', 0)),
                    'priority_score': self._calculate_priority_score(topic_data, proba[1]),
                    'improvement_suggestions': self._generate_suggestions(topic_data),
                    'estimated_improvement_time': self._estimate_improvement_time(topic_data)
                })
        
        # Sort by priority score
        focus_areas.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return focus_areas
    
    def _calculate_priority_score(self, topic_data: pd.Series, focus_probability: float) -> float:
        """Calculate priority score for focus area."""
        # Weight factors
        accuracy_weight = 0.3      # Lower accuracy = higher priority
        attempts_weight = 0.2      # More attempts = higher priority
        difficulty_weight = 0.2    # Higher difficulty = higher priority
        probability_weight = 0.3   # Model confidence
        
        # Calculate components
        accuracy_component = (100 - topic_data.get('accuracy_rate', 50)) / 100
        attempts_component = min(topic_data.get('attempts_count', 1) / 20, 1)  # Cap at 20 attempts
        difficulty_component = topic_data.get('topic_difficulty', 3) / 5
        probability_component = focus_probability
        
        # Calculate weighted score
        priority_score = (
            accuracy_weight * accuracy_component +
            attempts_weight * attempts_component +
            difficulty_weight * difficulty_component +
            probability_weight * probability_component
        )
        
        return priority_score
    
    def _generate_suggestions(self, topic_data: pd.Series) -> List[str]:
        """Generate personalized improvement suggestions."""
        suggestions = []
        accuracy = topic_data.get('accuracy_rate', 50)
        difficulty = topic_data.get('topic_difficulty', 3)
        time_taken = topic_data.get('average_time_taken', 5)
        confidence = topic_data.get('confidence_level', 3)
        
        # Accuracy-based suggestions
        if accuracy < 40:
            suggestions.append("Review fundamental concepts before attempting practice questions")
            suggestions.append("Focus on understanding rather than memorization")
            suggestions.append("Seek help from peers or instructors for clarification")
        elif accuracy < 60:
            suggestions.append("Practice more questions on this topic")
            suggestions.append("Review incorrect answers to understand mistakes")
            suggestions.append("Create summary notes of key concepts")
        else:
            suggestions.append("Continue practicing to maintain proficiency")
            suggestions.append("Try more challenging questions to deepen understanding")
        
        # Time-based suggestions
        if time_taken > 10:  # More than 10 minutes average
            suggestions.append("Work on improving speed through timed practice")
            suggestions.append("Identify time-consuming steps in problem-solving")
        
        # Confidence-based suggestions
        if confidence < 3 and accuracy > 60:
            suggestions.append("Build confidence through consistent practice")
            suggestions.append("Track your progress to see improvement over time")
        elif confidence > 3 and accuracy < 50:
            suggestions.append("Focus on actual understanding rather than perceived confidence")
            suggestions.append("Practice with immediate feedback to calibrate confidence")
        
        # Difficulty-based suggestions
        if difficulty >= 4:
            suggestions.append("Break down complex topics into smaller, manageable parts")
            suggestions.append("Use multiple resources (videos, textbooks, practice) for difficult topics")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _estimate_improvement_time(self, topic_data: pd.Series) -> Dict[str, Any]:
        """Estimate time required for improvement."""
        accuracy = topic_data.get('accuracy_rate', 50)
        difficulty = topic_data.get('topic_difficulty', 3)
        current_attempts = topic_data.get('attempts_count', 1)
        
        # Base time estimation (hours)
        base_time = difficulty * 3  # 3 hours per difficulty level
        
        # Adjustment based on current performance
        if accuracy < 30:
            multiplier = 2.0  # Need significant more time
        elif accuracy < 50:
            multiplier = 1.5  # Need moderate more time
        elif accuracy < 70:
            multiplier = 1.2  # Need some more time
        else:
            multiplier = 1.0  # On track
        
        # Adjustment based on attempts (diminishing returns)
        attempt_factor = max(0.8, 1.0 - (current_attempts * 0.01))
        
        estimated_hours = base_time * multiplier * attempt_factor
        
        return {
            'total_hours': round(estimated_hours, 1),
            'daily_hours': round(estimated_hours / 14, 1),  # Assuming 2 weeks
            'sessions_needed': max(7, int(estimated_hours / 2))  # Assuming 2-hour sessions
        }


# Alternative XGBoost model for comparison
class XGBoostFocusIdentifier(FocusAreaIdentifier):
    """XGBoost-based focus area identifier for better performance."""
    
    def __init__(self, version: str = "1.0.0"):
        super().__init__(version)
        self.model_name = "xgboost_focus_identifier"
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )