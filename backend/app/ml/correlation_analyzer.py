import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
import json
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from scipy.stats import pearsonr, spearmanr
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class CorrelationAnalyzer:
    """
    Implements historical exam data analysis, creates correlation matrices between 
    syllabus topics and exam questions, adds temporal analysis for trend identification,
    and develops cross-subject correlation detection.
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Retain 95% variance
        self.temporal_window = 12  # Months for temporal analysis
        
    def prepare_data_for_correlation(self, questions: List[Dict[str, Any]], 
                                   syllabus_topics: Dict[str, float] = None) -> pd.DataFrame:
        """
        Prepare data for correlation analysis by extracting relevant features from questions
        and syllabus topics
        """
        if not questions:
            return pd.DataFrame()
        
        # Extract features from questions
        data = []
        for q in questions:
            row = {
                'question_id': q.get('id', ''),
                'text_length': len(q.get('text', '')),
                'marks': q.get('marks', 0),
                'unit': q.get('unit', 'Unknown'),
                'difficulty': q.get('difficulty', 'medium'),
                'question_type': q.get('question_type', 'unknown'),
                'year': q.get('year', datetime.now().year),
                'semester': q.get('semester', 1)
            }
            
            # Convert categorical variables to numeric
            difficulty_map = {'easy': 1, 'medium': 2, 'hard': 3}
            type_map = {'mcq': 1, 'short_answer': 2, 'long_answer': 3, 'numerical': 4, 'essay': 5, 'unknown': 0}
            
            row['difficulty_numeric'] = difficulty_map.get(row['difficulty'], 2)
            row['type_numeric'] = type_map.get(row['question_type'], 0)
            
            # Add syllabus topic relevance if available
            if syllabus_topics:
                topic_relevance = 0
                question_text = q.get('text', '').lower()
                for topic, importance in syllabus_topics.items():
                    if topic.lower() in question_text:
                        topic_relevance = max(topic_relevance, importance)
                row['syllabus_relevance'] = topic_relevance
            else:
                row['syllabus_relevance'] = 0
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Add derived features
        if not df.empty:
            df['marks_per_word'] = df['marks'] / (df['text_length'] + 1)
            df['year_month'] = pd.to_datetime(df[['year', 'semester']].assign(day=1))
        
        return df
    
    def calculate_correlation_matrix(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate correlation matrix between various features"""
        if df.empty:
            return {}
        
        # Select numeric columns for correlation analysis
        numeric_cols = ['text_length', 'marks', 'difficulty_numeric', 'type_numeric', 'syllabus_relevance', 'marks_per_word']
        numeric_df = df[numeric_cols].copy()
        
        # Fill NaN values
        numeric_df = numeric_df.fillna(0)
        
        # Calculate Pearson correlation
        pearson_corr = numeric_df.corr(method='pearson')
        
        # Calculate Spearman correlation (rank-based)
        spearman_corr = numeric_df.corr(method='spearman')
        
        # Calculate significance for correlations
        significance = {}
        for col1 in numeric_cols:
            for col2 in numeric_cols:
                if col1 != col2:
                    corr_val, p_val = pearsonr(numeric_df[col1], numeric_df[col2])
                    significance[f"{col1}_{col2}"] = {
                        'correlation': corr_val,
                        'p_value': p_val,
                        'significant': p_val < 0.05
                    }
        
        return {
            'pearson_correlation': pearson_corr.to_dict(),
            'spearman_correlation': spearman_corr.to_dict(),
            'significance': significance
        }
    
    def analyze_syllabus_question_correlation(self, questions: List[Dict[str, Any]], 
                                           syllabus_topics: Dict[str, float]) -> Dict[str, Any]:
        """Analyze correlation between syllabus topics and question patterns"""
        if not questions or not syllabus_topics:
            return {}
        
        # Create a matrix of topic-question relationships
        topic_question_matrix = []
        
        for q in questions:
            question_text = q.get('text', '').lower()
            row = {'question_id': q.get('id', ''), 'marks': q.get('marks', 0), 'difficulty': q.get('difficulty', 'medium')}
            
            # Calculate relevance to each syllabus topic
            for topic, importance in syllabus_topics.items():
                topic_relevance = 1 if topic.lower() in question_text else 0
                row[f'topic_{topic}_relevance'] = topic_relevance
                row[f'topic_{topic}_importance'] = importance
                row[f'topic_{topic}_weighted_relevance'] = topic_relevance * importance
            
            topic_question_matrix.append(row)
        
        df = pd.DataFrame(topic_question_matrix)
        
        if df.empty:
            return {}
        
        # Calculate correlations between topics and question features
        results = {}
        
        # Correlation between topic relevance and marks
        for topic in syllabus_topics.keys():
            topic_col = f'topic_{topic}_relevance'
            if topic_col in df.columns:
                # Calculate correlation between topic relevance and marks
                mask = df[topic_col].notna() & df['marks'].notna()
                if mask.sum() > 1:  # Need at least 2 values for correlation
                    corr, p_val = pearsonr(df.loc[mask, topic_col], df.loc[mask, 'marks'])
                    results[topic] = {
                        'relevance_to_marks_correlation': corr,
                        'relevance_to_marks_significance': p_val < 0.05,
                        'importance_score': syllabus_topics[topic],
                        'appears_in_questions': df[topic_col].sum(),
                        'avg_marks_for_topic': df[df[topic_col] == 1]['marks'].mean() if df[df[topic_col] == 1].shape[0] > 0 else 0
                    }
        
        return results
    
    def temporal_analysis(self, questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform temporal analysis for trend identification"""
        if not questions:
            return {}
        
        # Prepare temporal data
        temporal_data = []
        for q in questions:
            year = q.get('year', datetime.now().year)
            semester = q.get('semester', 1)
            month = q.get('month', 6)  # Default to June if not specified
            
            temporal_data.append({
                'year': year,
                'semester': semester,
                'month': month,
                'marks': q.get('marks', 0),
                'difficulty': q.get('difficulty', 'medium'),
                'unit': q.get('unit', 'Unknown'),
                'question_type': q.get('question_type', 'unknown')
            })
        
        df = pd.DataFrame(temporal_data)
        if df.empty:
            return {}
        
        # Convert to datetime for time series analysis
        df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        
        # Group by time periods and analyze trends
        monthly_trends = df.groupby(['year', 'month']).agg({
            'marks': ['mean', 'std', 'count'],
            'difficulty': lambda x: (x == 'hard').sum() / len(x) if len(x) > 0 else 0  # Hard question ratio
        }).round(2)
        
        # Unit popularity over time
        unit_popularity = df.groupby(['year', 'month', 'unit']).size().reset_index(name='question_count')
        
        # Question type trends
        type_trends = df.groupby(['year', 'month', 'question_type']).size().reset_index(name='count')
        
        # Identify trends
        trends = {
            'monthly_average_marks': monthly_trends[('marks', 'mean')].to_dict() if ('marks', 'mean') in monthly_trends.columns else {},
            'monthly_hard_question_ratio': monthly_trends[('difficulty', '<lambda>')] if ('difficulty', '<lambda>') in monthly_trends.columns else {},
            'unit_popularity': unit_popularity.to_dict('records'),
            'question_type_trends': type_trends.to_dict('records'),
            'total_questions_by_period': monthly_trends[('marks', 'count')].to_dict() if ('marks', 'count') in monthly_trends.columns else {}
        }
        
        # Detect increasing/decreasing trends
        if len(monthly_trends) > 1:
            marks_values = monthly_trends[('marks', 'mean')].dropna().values if ('marks', 'mean') in monthly_trends.columns else []
            if len(marks_values) > 1:
                # Simple linear regression to detect trend
                x = np.arange(len(marks_values))
                if len(x) == len(marks_values):
                    slope, _ = np.polyfit(x, marks_values, 1)
                    trends['marks_trend_direction'] = 'increasing' if slope > 0.1 else 'decreasing' if slope < -0.1 else 'stable'
                    trends['marks_trend_slope'] = slope
        
        return trends
    
    def cross_subject_correlation(self, subjects_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Analyze correlations between different subjects
        subjects_data: Dictionary where keys are subject names and values are lists of questions
        """
        if len(subjects_data) < 2:
            return {}
        
        correlation_results = {}
        
        # Extract features for each subject
        subject_features = {}
        for subject_name, questions in subjects_data.items():
            if questions:
                df = self.prepare_data_for_correlation(questions)
                if not df.empty:
                    # Calculate summary statistics for the subject
                    features = {
                        'avg_marks': df['marks'].mean() if 'marks' in df.columns else 0,
                        'std_marks': df['marks'].std() if 'marks' in df.columns else 0,
                        'avg_difficulty': df['difficulty_numeric'].mean() if 'difficulty_numeric' in df.columns else 0,
                        'total_questions': len(questions),
                        'avg_text_length': df['text_length'].mean() if 'text_length' in df.columns else 0,
                        'popular_units': df['unit'].value_counts().head(3).to_dict() if 'unit' in df.columns else {},
                        'question_types': df['question_type'].value_counts().to_dict() if 'question_type' in df.columns else {}
                    }
                    subject_features[subject_name] = features
        
        if len(subject_features) < 2:
            return {}
        
        # Calculate correlations between subjects
        subjects_list = list(subject_features.keys())
        for i, subj1 in enumerate(subjects_list):
            for j, subj2 in enumerate(subjects_list):
                if i < j:  # Avoid duplicate pairs
                    features1 = subject_features[subj1]
                    features2 = subject_features[subj2]
                    
                    # Calculate correlation between various features
                    correlations = {}
                    
                    # Marks correlation
                    if 'avg_marks' in features1 and 'avg_marks' in features2:
                        marks_corr = np.corrcoef([features1['avg_marks']], [features2['avg_marks']])[0, 0]
                        correlations['marks_correlation'] = marks_corr
                    
                    # Difficulty correlation
                    if 'avg_difficulty' in features1 and 'avg_difficulty' in features2:
                        difficulty_corr = np.corrcoef([features1['avg_difficulty']], [features2['avg_difficulty']])[0, 0]
                        correlations['difficulty_correlation'] = difficulty_corr
                    
                    # Question volume correlation (if we had time-series data)
                    # For now, we'll just note the relationship
                    correlations['volume_relationship'] = {
                        'subject1_total': features1.get('total_questions', 0),
                        'subject2_total': features2.get('total_questions', 0)
                    }
                    
                    correlation_results[f"{subj1}_vs_{subj2}"] = correlations
        
        # Overall cross-subject insights
        insights = {
            'total_subjects_analyzed': len(subject_features),
            'subject_characteristics': subject_features,
            'pairwise_correlations': correlation_results,
            'common_patterns': self._identify_common_patterns(subject_features)
        }
        
        return insights
    
    def _identify_common_patterns(self, subject_features: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Identify common patterns across subjects"""
        if not subject_features:
            return {}
        
        # Collect all features
        all_marks = [f['avg_marks'] for f in subject_features.values() if 'avg_marks' in f]
        all_difficulties = [f['avg_difficulty'] for f in subject_features.values() if 'avg_difficulty' in f]
        
        patterns = {
            'average_subject_complexity': np.mean(all_difficulties) if all_difficulties else 0,
            'average_mark_allocation': np.mean(all_marks) if all_marks else 0,
            'complexity_std': np.std(all_difficulties) if all_difficulties else 0,
            'mark_allocation_std': np.std(all_marks) if all_marks else 0
        }
        
        # Identify outliers
        if all_difficulties:
            mean_diff = np.mean(all_difficulties)
            std_diff = np.std(all_difficulties)
            patterns['high_complexity_subjects'] = [
                subj for subj, f in subject_features.items() 
                if 'avg_difficulty' in f and f['avg_difficulty'] > mean_diff + std_diff
            ]
            patterns['low_complexity_subjects'] = [
                subj for subj, f in subject_features.items() 
                if 'avg_difficulty' in f and f['avg_difficulty'] < mean_diff - std_diff
            ]
        
        return patterns
    
    def comprehensive_correlation_analysis(self, questions: List[Dict[str, Any]], 
                                        syllabus_topics: Dict[str, float] = None,
                                        subjects_data: Dict[str, List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive correlation analysis combining all methods
        """
        try:
            # Prepare data
            df = self.prepare_data_for_correlation(questions, syllabus_topics)
            
            # Feature correlation matrix
            feature_correlations = self.calculate_correlation_matrix(df)
            
            # Syllabus-question correlation
            syllabus_correlations = {}
            if syllabus_topics:
                syllabus_correlations = self.analyze_syllabus_question_correlation(questions, syllabus_topics)
            
            # Temporal analysis
            temporal_results = self.temporal_analysis(questions)
            
            # Cross-subject correlation (if multiple subjects provided)
            cross_subject_results = {}
            if subjects_data:
                cross_subject_results = self.cross_subject_correlation(subjects_data)
            
            # Compile comprehensive results
            comprehensive_results = {
                'feature_correlations': feature_correlations,
                'syllabus_correlations': syllabus_correlations,
                'temporal_analysis': temporal_results,
                'cross_subject_analysis': cross_subject_results,
                'analysis_timestamp': datetime.now().isoformat(),
                'total_questions_analyzed': len(questions),
                'summary_statistics': {
                    'avg_marks': df['marks'].mean() if 'marks' in df.columns and not df.empty else 0,
                    'avg_difficulty': df['difficulty_numeric'].mean() if 'difficulty_numeric' in df.columns and not df.empty else 0,
                    'total_unique_units': df['unit'].nunique() if 'unit' in df.columns and not df.empty else 0,
                    'most_common_difficulty': df['difficulty'].mode().iloc[0] if 'difficulty' in df.columns and not df.empty and not df['difficulty'].mode().empty else 'unknown'
                }
            }
            
            return comprehensive_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive correlation analysis: {e}")
            return {
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def predict_high_impact_topics(self, correlation_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Predict high-impact topics based on correlation analysis
        """
        high_impact_topics = []
        
        # Analyze syllabus correlations to identify high-impact topics
        syllabus_corr = correlation_results.get('syllabus_correlations', {})
        
        for topic, metrics in syllabus_corr.items():
            if isinstance(metrics, dict):
                # Calculate impact score based on multiple factors
                relevance_to_marks = abs(metrics.get('relevance_to_marks_correlation', 0))
                appears_count = metrics.get('appears_in_questions', 0)
                avg_marks = metrics.get('avg_marks_for_topic', 0)
                importance_score = metrics.get('importance_score', 0)
                
                # Calculate composite impact score
                impact_score = (
                    relevance_to_marks * 0.3 +
                    (appears_count / 10) * 0.2 +  # Normalize appearance count
                    (avg_marks / 10) * 0.3 +  # Normalize average marks
                    importance_score * 0.2  # Importance from syllabus
                )
                
                high_impact_topics.append({
                    'topic': topic,
                    'impact_score': round(impact_score, 3),
                    'relevance_to_marks': relevance_to_marks,
                    'appearance_frequency': appears_count,
                    'average_marks': avg_marks,
                    'syllabus_importance': importance_score,
                    'is_significant': metrics.get('relevance_to_marks_significance', False)
                })
        
        # Sort by impact score
        high_impact_topics.sort(key=lambda x: x['impact_score'], reverse=True)
        
        return high_impact_topics


# Example usage and testing
if __name__ == "__main__":
    analyzer = CorrelationAnalyzer()
    
    # Sample questions data
    sample_questions = [
        {
            "id": "q1",
            "text": "Explain object oriented programming concepts",
            "marks": 10,
            "unit": "Unit 2",
            "difficulty": "hard",
            "question_type": "long_answer",
            "year": 2023,
            "semester": 1,
            "month": 6
        },
        {
            "id": "q2",
            "text": "Describe binary search algorithm",
            "marks": 5,
            "unit": "Unit 3",
            "difficulty": "medium",
            "question_type": "short_answer",
            "year": 2023,
            "semester": 2,
            "month": 12
        },
        {
            "id": "q3",
            "text": "What is inheritance in OOP?",
            "marks": 7,
            "unit": "Unit 2",
            "difficulty": "medium",
            "question_type": "short_answer",
            "year": 2024,
            "semester": 1,
            "month": 6
        }
    ]
    
    # Sample syllabus topics with importance scores
    sample_syllabus_topics = {
        "Object Oriented Programming": 0.9,
        "Data Structures": 0.8,
        "Algorithms": 0.7,
        "Database Systems": 0.6
    }
    
    # Sample subjects data for cross-subject analysis
    sample_subjects_data = {
        "Computer Science": sample_questions,
        "Mathematics": [
            {
                "id": "math_q1",
                "text": "Solve the given differential equation",
                "marks": 8,
                "unit": "Calculus",
                "difficulty": "hard",
                "question_type": "numerical",
                "year": 2023,
                "semester": 1,
                "month": 6
            }
        ]
    }
    
    # Perform comprehensive analysis
    results = analyzer.comprehensive_correlation_analysis(
        questions=sample_questions,
        syllabus_topics=sample_syllabus_topics,
        subjects_data=sample_subjects_data
    )
    
    print("Correlation Analysis Results:")
    print(json.dumps(results, indent=2))
    
    # Predict high-impact topics
    high_impact = analyzer.predict_high_impact_topics(results)
    print("\nHigh Impact Topics:")
    print(json.dumps(high_impact, indent=2))