# PrepIQ Enhanced Backend with ML Integration

## Overview

This is the enhanced backend for PrepIQ, a comprehensive educational platform for BTech students. The backend includes advanced machine learning capabilities for personalized learning recommendations, progress prediction, and intelligent content analysis.

## Key Features

### 🔧 Enhanced Architecture
- **Modular Design**: Clean separation of concerns with well-organized directories
- **Production-Ready**: Professional configuration with proper error handling and logging
- **Scalable**: Designed to handle growth with proper database indexing and caching
- **Secure**: Industry-standard security practices with JWT authentication and role-based access control

### 🤖 Machine Learning Models
1. **Progress Forecaster**: LSTM-based time series model for predicting learning progress
2. **Topic Recommender**: Hybrid system combining collaborative and content-based filtering
3. **Focus Area Identifier**: Classification model to identify weak areas needing attention
4. **Question Importance Predictor**: Enhanced NLP system with TF-IDF and transformer-based analysis

### 📊 API Endpoints
- **User Management**: Authentication, profiles, settings
- **ML Predictions**: Progress forecasts, recommendations, focus areas
- **Content Management**: Subjects, topics, questions, tests
- **Analytics**: User progress tracking, performance metrics

## Directory Structure

```
backend/
├── app/
│   ├── api/                    # REST API endpoints
│   │   └── v1/
│   │       ├── routes/         # API route handlers
│   │       ├── middleware/     # Custom middleware
│   │       └── dependencies/   # Dependency injection
│   ├── core/                   # Core configuration
│   │   ├── config.py          # Application settings
│   │   ├── logging.py         # Logging configuration
│   │   ├── exceptions.py      # Custom exceptions
│   │   └── security.py        # Authentication and security
│   ├── database/               # Database management
│   ├── ml/                     # Machine Learning components
│   │   ├── engines/           # ML model implementations
│   │   ├── core/              # ML base classes
│   │   └── training/          # Model training pipeline
│   ├── models/                # Database models
│   ├── schemas/               # Pydantic schemas
│   ├── services/              # Business logic
│   └── utils/                 # Utility functions
├── ml_models/                 # Trained model storage
├── data/                      # Training data
├── tests/                     # Test suite
├── requirements.txt           # Python dependencies
└── main.py                   # Application entry point
```

## Quick Start

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with the following variables:

```env
# Application settings
APP_NAME=PrepIQ Backend
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/prepiq
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Security
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=11520

# ML Settings
ML_MODEL_PATH=./ml_models
ML_TRAINING_DATA_PATH=./data

# Google AI
GOOGLE_API_KEY=your_google_api_key

# Logging
LOG_LEVEL=INFO
LOG_FILE=app.log
```

### 3. Run the Application

```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
python main.py
```

The API documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Machine Learning Models

### Progress Forecaster (LSTM)
Predicts user progress over time based on historical learning data.

```python
# Example usage
from app.ml.engines.progress_forecaster import ProgressForecaster

forecaster = ProgressForecaster()
# Train with user progress data
metrics = forecaster.train(X_train, y_train)
# Generate forecasts
forecasts = forecaster.forecast_progress(historical_data, days=30)
```

### Topic Recommender (Hybrid)
Recommends learning topics based on user preferences and behavior patterns.

```python
# Example usage
from app.ml.engines.topic_recommender import TopicRecommender

recommender = TopicRecommender()
recommender.train(user_topic_matrix, topic_features)
recommendations = recommender.recommend(user_id, n_recommendations=10)
```

### Focus Area Identifier (Classification)
Identifies weak areas in user knowledge for targeted improvement.

```python
# Example usage
from app.ml.engines.focus_area_identifier import FocusAreaIdentifier

identifier = FocusAreaIdentifier()
identifier.train(X_train, y_train)
focus_areas = identifier.identify_focus_areas(user_data, user_id)
```

### Question Importance Predictor (Enhanced NLP)
Analyzes question importance using hybrid TF-IDF and transformer approach.

```python
# Example usage
from app.ml.engines.question_importance import EnhancedQuestionAnalyzer

analyzer = EnhancedQuestionAnalyzer()
analyzer.train(tfidf_features, processed_questions)
predictions = analyzer.predict()
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/profile` - Get user profile
- `PUT /api/v1/auth/profile` - Update user profile

### ML Predictions
- `POST /api/v1/ml/predict/progress` - Predict user progress
- `POST /api/v1/ml/recommend/topics` - Get topic recommendations
- `POST /api/v1/ml/identify/focus-areas` - Identify focus areas
- `POST /api/v1/ml/analyze/questions` - Analyze question importance
- `GET /api/v1/ml/status` - Get ML model status

### User Data
- `GET /api/v1/users/{user_id}/dashboard` - User dashboard data
- `GET /api/v1/users/{user_id}/progress` - User progress data
- `GET /api/v1/users/{user_id}/analytics` - User analytics

## Database Schema

The enhanced backend includes the following key tables:

### User-Related
- `users` - User account information
- `user_progress` - Track study progress over time
- `user_preferences` - User learning preferences
- `model_predictions` - Store ML predictions for analysis

### Content-Related
- `subjects` - Academic subjects
- `topics` - Topics within subjects
- `questions` - Learning questions and problems
- `question_ratings` - User feedback on questions

### Interaction-Related
- `study_sessions` - Track user study activity
- `test_results` - Record test performance
- `topic_performance` - Store topic-wise performance data

## Deployment

### Docker Deployment

```dockerfile
# Build the image
docker build -t prepiq-backend .

# Run the container
docker run -p 8000:8000 prepiq-backend
```

### Environment-specific Configurations

Adjust configuration variables in `.env` for different environments:
- Development: `DEBUG=True`, local database
- Staging: `DEBUG=False`, staging database
- Production: `DEBUG=False`, production database, proper security settings

## Monitoring and Maintenance

### Health Checks
- `GET /health` - Basic application health
- `GET /ml/status` - ML model status and performance

### Logging
Structured logging with different levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General operational information
- `WARNING`: Warning conditions
- `ERROR`: Error conditions

### Model Retraining
Models can be automatically retrained based on:
- Performance degradation thresholds
- New data availability
- Scheduled intervals

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is proprietary software for PrepIQ educational platform.

## Support

For support, please contact the development team or check the documentation.