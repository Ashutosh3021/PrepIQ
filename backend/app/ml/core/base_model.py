from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import joblib
import os
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from ..core.config import settings
from ..core.logging import get_structured_logger


class BaseModel(ABC):
    """Base class for all ML models in PrepIQ."""
    
    def __init__(self, model_name: str, version: str = "1.0.0"):
        self.model_name = model_name
        self.version = version
        self.model: Optional[BaseEstimator] = None
        self.is_trained = False
        self.training_date: Optional[datetime] = None
        self.metrics: Dict[str, float] = {}
        self.logger = get_structured_logger(f"ml.{model_name}")
        
    @abstractmethod
    def preprocess_data(self, data: Union[pd.DataFrame, List[Dict]]) -> np.ndarray:
        """Preprocess input data for the model."""
        pass
    
    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray, **kwargs) -> Dict[str, float]:
        """Train the model and return metrics."""
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions using the trained model."""
        pass
    
    @abstractmethod
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance."""
        pass
    
    def save_model(self, path: Optional[str] = None) -> str:
        """Save the trained model to disk."""
        if not self.is_trained:
            raise ValueError("Model must be trained before saving")
            
        if path is None:
            path = os.path.join(settings.ML_MODEL_PATH, f"{self.model_name}_v{self.version}.joblib")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save model with metadata
        model_data = {
            'model': self.model,
            'model_name': self.model_name,
            'version': self.version,
            'training_date': self.training_date,
            'metrics': self.metrics,
            'is_trained': self.is_trained
        }
        
        joblib.dump(model_data, path)
        self.logger.info(f"Model saved successfully", path=path, version=self.version)
        return path
    
    def load_model(self, path: Optional[str] = None) -> bool:
        """Load a trained model from disk."""
        if path is None:
            path = os.path.join(settings.ML_MODEL_PATH, f"{self.model_name}_v{self.version}.joblib")
        
        if not os.path.exists(path):
            self.logger.warning(f"Model file not found", path=path)
            return False
        
        try:
            model_data = joblib.load(path)
            self.model = model_data['model']
            self.version = model_data.get('version', self.version)
            self.training_date = model_data.get('training_date')
            self.metrics = model_data.get('metrics', {})
            self.is_trained = model_data.get('is_trained', False)
            
            self.logger.info(f"Model loaded successfully", path=path, version=self.version)
            return True
        except Exception as e:
            self.logger.error(f"Failed to load model", path=path, error=str(e))
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and metadata."""
        return {
            'model_name': self.model_name,
            'version': self.version,
            'is_trained': self.is_trained,
            'training_date': self.training_date.isoformat() if self.training_date else None,
            'metrics': self.metrics,
            'model_type': self.__class__.__name__
        }


class TimeSeriesModel(BaseModel):
    """Base class for time series models."""
    
    def __init__(self, model_name: str, version: str = "1.0.0"):
        super().__init__(model_name, version)
        self.sequence_length = 30  # Default sequence length
        self.forecast_horizon = 30  # Default forecast horizon (days)
    
    def create_sequences(self, data: np.ndarray, sequence_length: int = None) -> tuple:
        """Create sequences for time series training."""
        if sequence_length is None:
            sequence_length = self.sequence_length
            
        X, y = [], []
        for i in range(len(data) - sequence_length):
            X.append(data[i:(i + sequence_length)])
            y.append(data[i + sequence_length])
        
        return np.array(X), np.array(y)
    
    def prepare_time_series_data(self, df: pd.DataFrame, target_column: str) -> tuple:
        """Prepare time series data for training."""
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Extract target values
        target_values = df[target_column].values
        
        # Create sequences
        X, y = self.create_sequences(target_values)
        
        return X, y


class ClassificationModel(BaseModel):
    """Base class for classification models."""
    
    def __init__(self, model_name: str, version: str = "1.0.0"):
        super().__init__(model_name, version)
        self.classes_: Optional[np.ndarray] = None
    
    def get_feature_importance(self) -> Optional[np.ndarray]:
        """Get feature importance if available."""
        if hasattr(self.model, 'feature_importances_'):
            return self.model.feature_importances_
        elif hasattr(self.model, 'coef_'):
            return np.abs(self.model.coef_[0])
        return None


class RecommendationModel(BaseModel):
    """Base class for recommendation models."""
    
    def __init__(self, model_name: str, version: str = "1.0.0"):
        super().__init__(model_name, version)
        self.user_features: Optional[np.ndarray] = None
        self.item_features: Optional[np.ndarray] = None
    
    @abstractmethod
    def recommend(self, user_id: str, n_recommendations: int = 10) -> List[Dict[str, Any]]:
        """Generate recommendations for a user."""
        pass