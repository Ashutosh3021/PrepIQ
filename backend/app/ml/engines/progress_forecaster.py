from typing import Dict, List, Any, Optional, Union
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import tensorflow as tf

from .core.base_model import TimeSeriesModel
from .core.config import settings


class ProgressForecaster(TimeSeriesModel):
    """LSTM-based model for forecasting user progress over time."""
    
    def __init__(self, version: str = "1.0.0"):
        super().__init__("progress_forecaster", version)
        self.sequence_length = 30  # Days of historical data
        self.forecast_horizon = 30  # Forecast next 30 days
        self.scaler = StandardScaler()
        self.feature_columns = [
            'completion_percentage', 'study_hours', 'topics_covered', 
            'practice_tests_taken', 'average_score', 'streak_days'
        ]
    
    def preprocess_data(self, data: Union[pd.DataFrame, List[Dict]]) -> np.ndarray:
        """Preprocess input data for the progress forecaster."""
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()
        
        # Ensure required columns exist
        required_columns = set(self.feature_columns + ['date'])
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Convert date column to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Select feature columns
        features = df[self.feature_columns].values
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        return scaled_features
    
    def create_lstm_model(self, input_shape: tuple) -> Sequential:
        """Create LSTM model architecture."""
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(64, return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(len(self.feature_columns))  # Output all features
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs) -> Dict[str, float]:
        """Train the LSTM progress forecaster."""
        # Reshape data for LSTM (samples, timesteps, features)
        X_lstm = X.reshape((X.shape[0], self.sequence_length, len(self.feature_columns)))
        
        # Create sequences for training
        X_seq, y_seq = self.create_sequences(X_lstm)
        
        # Split data
        split_idx = int(0.8 * len(X_seq))
        X_train, X_val = X_seq[:split_idx], X_seq[split_idx:]
        y_train, y_val = y_seq[:split_idx], y_seq[split_idx:]
        
        # Create and train model
        self.model = self.create_lstm_model((self.sequence_length, len(self.feature_columns)))
        
        # Training parameters
        epochs = kwargs.get('epochs', 100)
        batch_size = kwargs.get('batch_size', 32)
        validation_split = kwargs.get('validation_split', 0.2)
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_val, y_val),
            verbose=0
        )
        
        # Evaluate model
        metrics = self.evaluate(X_val, y_val)
        
        # Update model metadata
        self.is_trained = True
        self.training_date = datetime.utcnow()
        self.metrics = metrics
        
        return metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions for future progress."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Reshape for LSTM
        if len(X.shape) == 2:
            X = X.reshape((1, self.sequence_length, len(self.feature_columns)))
        
        # Make prediction
        prediction = self.model.predict(X, verbose=0)
        
        # Inverse transform to get original scale
        prediction_original = self.scaler.inverse_transform(prediction)
        
        return prediction_original
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance."""
        if not self.is_trained:
            raise ValueError("Model must be trained before evaluation")
        
        # Make predictions
        y_pred = self.model.predict(X, verbose=0)
        
        # Calculate metrics
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        
        return {
            'mse': float(mse),
            'mae': float(mae),
            'rmse': float(np.sqrt(mse)),
            'r2_score': float(r2)
        }
    
    def forecast_progress(self, historical_data: pd.DataFrame, 
                         forecast_days: int = 30) -> List[Dict[str, Any]]:
        """Generate progress forecast for specified number of days."""
        if not self.is_trained:
            raise ValueError("Model must be trained before forecasting")
        
        # Preprocess historical data
        processed_data = self.preprocess_data(historical_data)
        
        # Get the most recent sequence
        if len(processed_data) < self.sequence_length:
            raise ValueError(f"Need at least {self.sequence_length} days of data for forecasting")
        
        recent_sequence = processed_data[-self.sequence_length:]
        
        # Generate forecasts
        forecasts = []
        current_sequence = recent_sequence.copy()
        
        for day in range(forecast_days):
            # Make prediction
            prediction = self.predict(current_sequence.reshape(1, self.sequence_length, -1))
            
            # Add to forecasts
            forecast_date = datetime.utcnow() + timedelta(days=day + 1)
            forecast_data = {
                'date': forecast_date.isoformat(),
                'completion_percentage': float(prediction[0][0]),
                'study_hours': float(prediction[0][1]),
                'topics_covered': int(prediction[0][2]),
                'practice_tests_taken': int(prediction[0][3]),
                'average_score': float(prediction[0][4]),
                'streak_days': int(prediction[0][5]),
                'confidence': max(0.5, 1.0 - (day * 0.02))  # Decreasing confidence over time
            }
            forecasts.append(forecast_data)
            
            # Update sequence for next prediction
            current_sequence = np.vstack([current_sequence[1:], prediction[0]])
        
        return forecasts
    
    def generate_progress_insights(self, forecasts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights from progress forecasts."""
        if not forecasts:
            return {}
        
        # Calculate trends
        completion_trend = forecasts[-1]['completion_percentage'] - forecasts[0]['completion_percentage']
        study_hours_trend = forecasts[-1]['study_hours'] - forecasts[0]['study_hours']
        
        # Identify key insights
        insights = {
            'overall_progress_trend': 'improving' if completion_trend > 0 else 'declining',
            'completion_change': completion_trend,
            'study_hours_change': study_hours_trend,
            'predicted_completion_30_days': forecasts[-1]['completion_percentage'],
            'recommended_actions': self._generate_recommendations(forecasts),
            'risk_level': self._assess_risk_level(forecasts)
        }
        
        return insights
    
    def _generate_recommendations(self, forecasts: List[Dict[str, Any]]) -> List[str]:
        """Generate personalized recommendations based on forecasts."""
        recommendations = []
        final_completion = forecasts[-1]['completion_percentage']
        
        if final_completion < 60:
            recommendations.append("Increase daily study hours by 1-2 hours")
            recommendations.append("Focus on completing at least 2-3 topics per week")
            recommendations.append("Take more practice tests to improve accuracy")
        elif final_completion < 80:
            recommendations.append("Maintain current study schedule")
            recommendations.append("Focus on weak areas identified in practice tests")
        else:
            recommendations.append("Excellent progress! Consider helping peers or exploring advanced topics")
        
        # Add streak recommendations
        if forecasts[-1]['streak_days'] < 7:
            recommendations.append("Try to maintain a daily study streak for better consistency")
        
        return recommendations
    
    def _assess_risk_level(self, forecasts: List[Dict[str, Any]]) -> str:
        """Assess the risk level of the progress trajectory."""
        final_completion = forecasts[-1]['completion_percentage']
        
        if final_completion < 50:
            return "high"
        elif final_completion < 70:
            return "medium"
        else:
            return "low"


# Alternative simpler model for comparison
class SimpleProgressRegressor(TimeSeriesModel):
    """Simple regression-based progress predictor for comparison."""
    
    def __init__(self, version: str = "1.0.0"):
        super().__init__("simple_progress_regressor", version)
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.feature_columns = [
            'completion_percentage', 'study_hours', 'topics_covered', 
            'practice_tests_taken', 'average_score', 'streak_days', 'day_of_week'
        ]
    
    def preprocess_data(self, data: Union[pd.DataFrame, List[Dict]]) -> np.ndarray:
        """Preprocess data for simple regressor."""
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()
        
        # Add temporal features
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_of_year'] = df['date'].dt.dayofyear
        
        # Select features
        features = df[self.feature_columns].values
        return features
    
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs) -> Dict[str, float]:
        """Train the simple regressor."""
        self.model.fit(X, y)
        self.is_trained = True
        self.training_date = datetime.utcnow()
        
        # Evaluate
        metrics = self.evaluate(X, y)
        self.metrics = metrics
        
        return metrics
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        return self.model.predict(X)
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model."""
        y_pred = self.predict(X)
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        
        return {
            'mse': float(mse),
            'mae': float(mae),
            'rmse': float(np.sqrt(mse)),
            'r2_score': float(r2)
        }