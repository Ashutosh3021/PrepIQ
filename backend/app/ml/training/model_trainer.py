from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import joblib
import json
import os
from pathlib import Path
import mlflow
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import make_scorer

from ..core.base_model import BaseModel
from ..core.config import settings
from ...core.logging import get_structured_logger
from .data_pipeline import DataPipeline


class ModelTrainer:
    """Comprehensive model training and management system."""
    
    def __init__(self):
        self.logger = get_structured_logger("ml.model_trainer")
        self.data_pipeline = DataPipeline()
        self.models_dir = Path(settings.ML_MODEL_PATH)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.training_history = []
        
        # Initialize MLflow if available
        try:
            mlflow.set_tracking_uri("file:./mlruns")
            self.mlflow_enabled = True
        except:
            self.mlflow_enabled = False
            self.logger.warning("MLflow not available, training metrics will not be tracked")
    
    def train_model(self, model: BaseModel, data_config: Dict[str, Any], 
                   training_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Train a model with comprehensive configuration."""
        if training_config is None:
            training_config = self._get_default_training_config()
        
        training_start = datetime.now(timezone.utc)
        
        try:
            # Load and preprocess data
            self.logger.info(f"Loading data for {model.model_name}")
            raw_data = self.data_pipeline.load_data(
                data_config['source'], 
                data_config.get('type', 'csv')
            )
            
            # Clean data
            cleaned_data = self.data_pipeline.clean_data(
                raw_data, 
                data_config.get('cleaning_rules')
            )
            
            # Feature engineering
            processed_data = self.data_pipeline.feature_engineering(
                cleaned_data,
                data_config.get('feature_config')
            )
            
            # Save processed data
            processed_filename = f"{model.model_name}_processed_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.data_pipeline.save_processed_data(processed_data, processed_filename)
            
            # Prepare features and target
            X, y = self._prepare_features_target(processed_data, data_config)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, 
                test_size=training_config.get('test_size', 0.2),
                random_state=training_config.get('random_state', 42),
                stratify=y if len(np.unique(y)) > 1 and len(y) > 100 else None
            )
            
            # Start MLflow run if enabled
            if self.mlflow_enabled:
                mlflow.start_run(run_name=f"{model.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                mlflow.log_params(training_config.get('hyperparameters', {}))
                mlflow.log_param("model_name", model.model_name)
                mlflow.log_param("training_start", training_start.isoformat())
            
            # Train model
            self.logger.info(f"Training {model.model_name}")
            metrics = model.train(X_train, y_train, **training_config.get('training_params', {}))
            
            # Evaluate model
            test_metrics = model.evaluate(X_test, y_test)
            
            # Cross-validation
            if training_config.get('cross_validation', True):
                cv_scores = self._perform_cross_validation(model, X, y, training_config)
                metrics['cv_scores'] = cv_scores
                metrics['cv_mean'] = float(np.mean(cv_scores))
                metrics['cv_std'] = float(np.std(cv_scores))
            
            # Hyperparameter tuning if enabled
            if training_config.get('hyperparameter_tuning', False):
                best_params, best_score = self._tune_hyperparameters(
                    model, X_train, y_train, training_config
                )
                metrics['best_hyperparameters'] = best_params
                metrics['best_cv_score'] = best_score
            
            # Save model
            model_version = training_config.get('version', '1.0.0')
            model_path = model.save_model()
            
            # Log results
            training_end = datetime.now(timezone.utc)
            training_duration = (training_end - training_start).total_seconds()
            
            training_result = {
                'model_name': model.model_name,
                'version': model_version,
                'training_start': training_start.isoformat(),
                'training_end': training_end.isoformat(),
                'training_duration_seconds': training_duration,
                'training_metrics': metrics,
                'test_metrics': test_metrics,
                'model_path': model_path,
                'data_config': data_config,
                'training_config': training_config,
                'sample_size': len(X),
                'feature_count': X.shape[1] if len(X.shape) > 1 else 1
            }
            
            # Log to MLflow if enabled
            if self.mlflow_enabled:
                mlflow.log_metrics(metrics)
                mlflow.log_metrics(test_metrics)
                mlflow.log_artifact(model_path)
                mlflow.log_artifact(str(self.data_pipeline.data_dir / processed_filename))
                mlflow.end_run()
            
            # Save training history
            self.training_history.append(training_result)
            self._save_training_history()
            
            self.logger.info(f"Model training completed for {model.model_name}", 
                           duration=f"{training_duration:.2f}s")
            
            return training_result
            
        except Exception as e:
            self.logger.error(f"Model training failed for {model.model_name}", error=str(e))
            if self.mlflow_enabled:
                mlflow.end_run()
            raise
    
    def _get_default_training_config(self) -> Dict[str, Any]:
        """Get default training configuration."""
        return {
            'test_size': 0.2,
            'random_state': 42,
            'cross_validation': True,
            'cv_folds': 5,
            'hyperparameter_tuning': False,
            'hyperparameters': {},
            'training_params': {
                'epochs': 100,
                'batch_size': 32
            }
        }
    
    def _prepare_features_target(self, df: pd.DataFrame, data_config: Dict[str, Any]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and target arrays from dataframe."""
        target_column = data_config.get('target_column')
        feature_columns = data_config.get('feature_columns')
        
        if target_column and target_column in df.columns:
            y = df[target_column].values
            if feature_columns:
                X = df[feature_columns].values
            else:
                # Use all columns except target
                feature_columns = [col for col in df.columns if col != target_column]
                X = df[feature_columns].values
        else:
            # For unsupervised learning or when no target specified
            X = df.values
            y = None
        
        return X, y
    
    def _perform_cross_validation(self, model: BaseModel, X: np.ndarray, y: np.ndarray, 
                                config: Dict[str, Any]) -> np.ndarray:
        """Perform cross-validation."""
        try:
            cv_folds = config.get('cv_folds', 5)
            cv_scores = cross_val_score(model.model, X, y, cv=cv_folds, 
                                      scoring='accuracy' if hasattr(model, 'predict') else 'neg_mean_squared_error')
            return cv_scores
        except Exception as e:
            self.logger.warning(f"Cross-validation failed: {str(e)}")
            return np.array([0.0])
    
    def _tune_hyperparameters(self, model: BaseModel, X: np.ndarray, y: np.ndarray, 
                            config: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """Perform hyperparameter tuning."""
        try:
            param_grid = config.get('param_grid', {})
            if not param_grid:
                return {}, 0.0
            
            grid_search = GridSearchCV(
                model.model,
                param_grid,
                cv=config.get('cv_folds', 3),
                scoring='accuracy' if hasattr(model, 'predict') else 'neg_mean_squared_error',
                n_jobs=-1
            )
            
            grid_search.fit(X, y)
            
            return grid_search.best_params_, grid_search.best_score_
            
        except Exception as e:
            self.logger.warning(f"Hyperparameter tuning failed: {str(e)}")
            return {}, 0.0
    
    def batch_train_models(self, training_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Train multiple models in batch."""
        results = []
        
        for config in training_configs:
            try:
                model_class = config['model_class']
                model = model_class(version=config.get('version', '1.0.0'))
                data_config = config['data_config']
                training_config = config.get('training_config', {})
                
                result = self.train_model(model, data_config, training_config)
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Batch training failed for config: {config}", error=str(e))
                results.append({
                    'error': str(e),
                    'config': config
                })
        
        return results
    
    def retrain_model(self, model_name: str, version: str = None, 
                     force: bool = False) -> Optional[Dict[str, Any]]:
        """Retrain an existing model."""
        # Find latest training configuration for this model
        model_history = [h for h in self.training_history 
                        if h['model_name'] == model_name]
        
        if not model_history:
            self.logger.warning(f"No training history found for model {model_name}")
            return None
        
        # Get latest training config
        latest_training = sorted(model_history, 
                               key=lambda x: x['training_start'])[-1]
        
        # Check if retraining is needed
        if not force:
            last_training = datetime.fromisoformat(latest_training['training_end'])
            if datetime.now(timezone.utc) - last_training < timedelta(days=7):
                self.logger.info(f"Model {model_name} trained recently, skipping retraining")
                return latest_training
        
        # Retrain model
        try:
            # Recreate model instance
            # This assumes model classes can be imported - adjust as needed
            model_class = self._get_model_class(model_name)
            model = model_class(version=version or latest_training['version'])
            
            # Use same configuration
            result = self.train_model(
                model, 
                latest_training['data_config'],
                latest_training['training_config']
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Retraining failed for {model_name}", error=str(e))
            return None
    
    def _get_model_class(self, model_name: str):
        """Get model class by name."""
        # This is a simplified implementation
        # In practice, you'd have a registry or import system
        model_mapping = {
            'progress_forecaster': 'ProgressForecaster',
            'topic_recommender': 'TopicRecommender',
            'focus_area_identifier': 'FocusAreaIdentifier',
            'question_importance': 'EnhancedQuestionAnalyzer'
        }
        
        # Import and return the class
        # This is simplified - you'd need proper import logic
        raise NotImplementedError("Model class resolution not fully implemented")
    
    def get_model_performance_report(self, model_name: str = None) -> Dict[str, Any]:
        """Generate performance report for models."""
        if model_name:
            history = [h for h in self.training_history if h['model_name'] == model_name]
        else:
            history = self.training_history
        
        if not history:
            return {}
        
        # Group by model
        model_performance = {}
        for record in history:
            model_key = f"{record['model_name']}_v{record['version']}"
            if model_key not in model_performance:
                model_performance[model_key] = []
            model_performance[model_key].append(record)
        
        # Generate summary statistics
        report = {
            'total_models_trained': len(history),
            'models_by_type': {},
            'performance_summary': {},
            'recent_training': sorted(history, key=lambda x: x['training_end'])[-5:] if len(history) >= 5 else history
        }
        
        # Performance by model type
        for model_key, records in model_performance.items():
            model_name = records[0]['model_name']
            if model_name not in report['models_by_type']:
                report['models_by_type'][model_name] = {
                    'versions': [],
                    'latest_performance': None,
                    'average_training_time': 0
                }
            
            # Add version info
            versions = [r['version'] for r in records]
            report['models_by_type'][model_name]['versions'].extend(versions)
            
            # Latest performance
            latest_record = sorted(records, key=lambda x: x['training_end'])[-1]
            report['models_by_type'][model_name]['latest_performance'] = {
                'metrics': latest_record.get('test_metrics', {}),
                'training_date': latest_record['training_end']
            }
            
            # Average training time
            avg_time = np.mean([r['training_duration_seconds'] for r in records])
            report['models_by_type'][model_name]['average_training_time'] = avg_time
        
        return report
    
    def _save_training_history(self):
        """Save training history to file."""
        history_file = self.models_dir / "training_history.json"
        try:
            with open(history_file, 'w') as f:
                json.dump(self.training_history, f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"Failed to save training history: {str(e)}")
    
    def load_training_history(self):
        """Load training history from file."""
        history_file = self.models_dir / "training_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    self.training_history = json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load training history: {str(e)}")