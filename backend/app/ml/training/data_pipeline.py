from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import logging
from pathlib import Path

from ..core.base_model import BaseModel
from ..core.config import settings
from ...core.logging import get_structured_logger


class DataPipeline:
    """Data pipeline for preprocessing and preparing training data."""
    
    def __init__(self):
        self.logger = get_structured_logger("ml.data_pipeline")
        self.data_dir = Path(settings.ML_TRAINING_DATA_PATH)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_data(self, data_source: str, data_type: str = "csv") -> pd.DataFrame:
        """Load data from various sources."""
        try:
            if data_source.startswith("db://"):
                # Load from database
                return self._load_from_database(data_source)
            elif data_source.startswith("api://"):
                # Load from API
                return self._load_from_api(data_source)
            else:
                # Load from file
                file_path = self.data_dir / data_source
                if data_type == "csv":
                    return pd.read_csv(file_path)
                elif data_type == "json":
                    return pd.read_json(file_path)
                elif data_type == "parquet":
                    return pd.read_parquet(file_path)
                else:
                    raise ValueError(f"Unsupported data type: {data_type}")
        
        except Exception as e:
            self.logger.error(f"Failed to load data from {data_source}", error=str(e))
            raise
    
    def _load_from_database(self, db_url: str) -> pd.DataFrame:
        """Load data from database."""
        # Implementation depends on your database setup
        # This is a placeholder
        raise NotImplementedError("Database loading not implemented")
    
    def _load_from_api(self, api_url: str) -> pd.DataFrame:
        """Load data from API."""
        # Implementation depends on your API structure
        # This is a placeholder
        raise NotImplementedError("API loading not implemented")
    
    def clean_data(self, df: pd.DataFrame, cleaning_rules: Dict[str, Any] = None) -> pd.DataFrame:
        """Clean and preprocess data."""
        df_clean = df.copy()
        
        if cleaning_rules is None:
            cleaning_rules = self._get_default_cleaning_rules()
        
        # Handle missing values
        for column, strategy in cleaning_rules.get('missing_values', {}).items():
            if column in df_clean.columns:
                if strategy == 'drop':
                    df_clean = df_clean.dropna(subset=[column])
                elif strategy == 'mean':
                    df_clean[column] = df_clean[column].fillna(df_clean[column].mean())
                elif strategy == 'median':
                    df_clean[column] = df_clean[column].fillna(df_clean[column].median())
                elif strategy == 'mode':
                    df_clean[column] = df_clean[column].fillna(df_clean[column].mode().iloc[0] if not df_clean[column].mode().empty else 0)
        
        # Handle outliers
        if 'outliers' in cleaning_rules:
            for column, method in cleaning_rules['outliers'].items():
                if column in df_clean.columns:
                    df_clean = self._handle_outliers(df_clean, column, method)
        
        # Data type conversions
        if 'data_types' in cleaning_rules:
            for column, dtype in cleaning_rules['data_types'].items():
                if column in df_clean.columns:
                    df_clean[column] = df_clean[column].astype(dtype)
        
        self.logger.info(f"Data cleaned: {len(df)} -> {len(df_clean)} records")
        return df_clean
    
    def _get_default_cleaning_rules(self) -> Dict[str, Any]:
        """Get default data cleaning rules."""
        return {
            'missing_values': {
                'accuracy_rate': 'mean',
                'study_hours': 'median',
                'completion_percentage': 'mean'
            },
            'outliers': {
                'accuracy_rate': 'iqr',
                'study_hours': 'iqr'
            },
            'data_types': {
                'accuracy_rate': 'float32',
                'study_hours': 'float32',
                'completion_percentage': 'float32'
            }
        }
    
    def _handle_outliers(self, df: pd.DataFrame, column: str, method: str) -> pd.DataFrame:
        """Handle outliers in a column."""
        if method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
        elif method == 'zscore':
            z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
            df = df[z_scores < 3]
        
        return df
    
    def feature_engineering(self, df: pd.DataFrame, 
                          feature_config: Dict[str, Any] = None) -> pd.DataFrame:
        """Create new features from existing data."""
        df_features = df.copy()
        
        if feature_config is None:
            feature_config = self._get_default_feature_config()
        
        # Temporal features
        if 'temporal' in feature_config:
            for feature_name, config in feature_config['temporal'].items():
                if config['source_column'] in df_features.columns:
                    df_features = self._create_temporal_features(
                        df_features, config['source_column'], feature_name, config.get('type', 'datetime')
                    )
        
        # Statistical features
        if 'statistical' in feature_config:
            for feature_name, config in feature_config['statistical'].items():
                df_features = self._create_statistical_features(
                    df_features, config['source_columns'], feature_name, config['operation']
                )
        
        # Categorical encoding
        if 'categorical' in feature_config:
            for column, method in feature_config['categorical'].items():
                if column in df_features.columns:
                    df_features = self._encode_categorical(df_features, column, method)
        
        self.logger.info(f"Feature engineering completed: {len(df.columns)} -> {len(df_features.columns)} features")
        return df_features
    
    def _get_default_feature_config(self) -> Dict[str, Any]:
        """Get default feature engineering configuration."""
        return {
            'temporal': {
                'study_day_of_week': {
                    'source_column': 'study_date',
                    'type': 'date'
                },
                'time_since_last_test': {
                    'source_column': 'last_test_date',
                    'type': 'timedelta'
                }
            },
            'statistical': {
                'avg_accuracy_last_7_days': {
                    'source_columns': ['accuracy_day1', 'accuracy_day2', 'accuracy_day3', 
                                     'accuracy_day4', 'accuracy_day5', 'accuracy_day6', 'accuracy_day7'],
                    'operation': 'mean'
                },
                'accuracy_trend': {
                    'source_columns': ['accuracy_current', 'accuracy_previous'],
                    'operation': 'trend'
                }
            },
            'categorical': {
                'subject': 'onehot',
                'difficulty_level': 'label'
            }
        }
    
    def _create_temporal_features(self, df: pd.DataFrame, source_column: str, 
                                feature_name: str, feature_type: str) -> pd.DataFrame:
        """Create temporal features."""
        if feature_type == 'datetime':
            df[f'{feature_name}_year'] = pd.to_datetime(df[source_column]).dt.year
            df[f'{feature_name}_month'] = pd.to_datetime(df[source_column]).dt.month
            df[f'{feature_name}_day'] = pd.to_datetime(df[source_column]).dt.day
            df[f'{feature_name}_weekday'] = pd.to_datetime(df[source_column]).dt.weekday
        elif feature_type == 'timedelta':
            df[feature_name] = (datetime.now() - pd.to_datetime(df[source_column])).dt.days
        
        return df
    
    def _create_statistical_features(self, df: pd.DataFrame, source_columns: List[str],
                                   feature_name: str, operation: str) -> pd.DataFrame:
        """Create statistical features."""
        if operation == 'mean':
            df[feature_name] = df[source_columns].mean(axis=1)
        elif operation == 'std':
            df[feature_name] = df[source_columns].std(axis=1)
        elif operation == 'trend':
            if len(source_columns) == 2:
                df[feature_name] = (df[source_columns[0]] - df[source_columns[1]]) / df[source_columns[1]].replace(0, 1)
        
        return df
    
    def _encode_categorical(self, df: pd.DataFrame, column: str, method: str) -> pd.DataFrame:
        """Encode categorical variables."""
        if method == 'onehot':
            dummies = pd.get_dummies(df[column], prefix=column)
            df = pd.concat([df, dummies], axis=1)
            df = df.drop(columns=[column])
        elif method == 'label':
            df[f'{column}_encoded'] = pd.Categorical(df[column]).codes
        
        return df
    
    def save_processed_data(self, df: pd.DataFrame, filename: str) -> str:
        """Save processed data to file."""
        output_path = self.data_dir / filename
        df.to_csv(output_path, index=False)
        self.logger.info(f"Processed data saved to {output_path}")
        return str(output_path)