# PrepIQ - AI-Powered Study Assistant

PrepIQ is an intelligent study assistant platform that helps students prepare for exams using AI technology. It features exam prediction, personalized study plans, and an AI chatbot to assist with learning.

## Project Structure

```
PrepIQ/
│
├── frontend/                    # All React PWA stuff
│   ├── src/
│   │   ├── app/                # Next.js app router pages
│   │   ├── components/         # React components
│   │   ├── hooks/              # React hooks
│   │   ├── lib/                # Utility functions and Supabase integration
│   │   ├── styles/             # Global styles
│   │   └── utils/
│   ├── public/
│   ├── package.json            # Frontend dependencies
│   └── public/
│
├── backend/                     # All FastAPI/Python stuff
│   ├── app/
│   │   ├── main.py
│   │   ├── pdf_parser.py
│   │   ├── prediction_engine.py
│   │   ├── chatbot.py
│   │   └── database.py
│   ├── tests/
│   ├── uploads/                # Store uploaded PDFs
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # API keys (gitignored)
│   ├── .env.example            # Template for environment variables
│   └── start_server.py         # Server startup script
│
├── .gitignore                  # Root level
├── README.md                   # Root level
├── LICENSE                     # Root level
└── .env.example                # Root level (template)
```

## Features

- **Exam Prediction**: AI-powered prediction of likely exam topics based on study materials
- **Personalized Study Plans**: Customized study schedules based on available time and current knowledge
- **AI Study Assistant**: Chatbot to answer questions and explain concepts
- **PDF Analysis**: Upload and analyze PDF study materials
- **Progress Tracking**: Monitor study progress and performance

## Tech Stack

### Frontend
- React.js
- Vite
- Tailwind CSS
- Radix UI
- Supabase (Authentication & Database)

### Backend
- FastAPI
- PostgreSQL
- Google Gemini API
- PyPDF2
- SQLAlchemy

## Setup Instructions

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd PrepIQ/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   pnpm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   # or
   pnpm run dev
   ```

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd PrepIQ/backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys and database URL
   ```

5. Start the server:
   ```bash
   python start_server.py
   ```

## Environment Variables

You'll need to set the following environment variables:

- `DATABASE_URL`: PostgreSQL database connection string
- `GEMINI_API_KEY`: Google Gemini API key
- `SECRET_KEY`: Secret key for JWT tokens

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.