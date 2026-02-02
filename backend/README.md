# PrepIQ Backend

This is the backend for the PrepIQ AI-powered study assistant, built with FastAPI.

## Features

- RESTful API built with FastAPI
- PDF parsing and analysis
- AI-powered exam predictions
- Personalized study plan generation
- AI chatbot functionality
- Database integration with PostgreSQL
- JWT-based authentication

## Tech Stack

- FastAPI
- Python 3.10+
- PostgreSQL
- SQLAlchemy
- Google Gemini API
- PyPDF2
- Tesseract OCR

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Google Gemini API key

### Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env to add your database URL, API keys, and other settings
   ```

4. Run the development server:
   ```bash
   python start_server.py
   ```

## Environment Variables

- `DATABASE_URL`: PostgreSQL database connection string
- `GEMINI_API_KEY`: Google Gemini API key
- `SECRET_KEY`: Secret key for JWT tokens
- `ALGORITHM`: Algorithm for JWT encoding (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30 minutes)
- `UPLOAD_DIR`: Directory for storing uploaded files (default: uploads/)
- `MAX_FILE_SIZE`: Maximum file upload size in bytes (default: 10485760)
- `ALLOWED_FILE_TYPES`: Comma-separated list of allowed file types (default: pdf,docx,txt)

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

## Project Structure

- `app/` - Main application code
  - `main.py` - FastAPI application entry point
  - `pdf_parser.py` - PDF parsing utilities
  - `prediction_engine.py` - AI prediction logic
  - `chatbot.py` - AI chatbot functionality
  - `database.py` - Database models and configuration
- `tests/` - Unit and integration tests
- `uploads/` - Storage for user-uploaded files (not in version control)

## Running Tests

```bash
pytest
```

## Dependencies

All Python dependencies are listed in `requirements.txt`. Key dependencies include:

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `sqlalchemy` - Database ORM
- `psycopg2-binary` - PostgreSQL adapter
- `google-generativeai` - Google AI SDK
- `PyPDF2` - PDF processing