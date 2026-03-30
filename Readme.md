# PrepIQ

AI-Powered Exam Preparation Platform that predicts exam questions using ML analysis.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python, SQLAlchemy |
| Database | PostgreSQL (Supabase) |
| Auth | Supabase Auth, JWT |
| AI/ML | Google Gemini, Bytez API, Lightweight ML |

---

## Features

- **Question Prediction** - AI analyzes past papers to predict likely exam questions
- **Smart Mock Tests** - Generate practice tests from uploaded materials  
- **AI Tutor** - Socratic teaching method chatbot
- **Analytics Dashboard** - Visualize patterns and trends
- **Subject Management** - Organize subjects and papers

---

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure env vars
uvicorn app.main:app --reload

# Frontend  
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

---

## Project Structure

```
PrepIQ/
├── backend/
│   ├── app/
│   │   ├── routers/       # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── subjects.py
│   │   │   ├── predictions.py
│   │   │   ├── tests.py
│   │   │   ├── upload.py
│   │   │   ├── chat.py
│   │   │   ├── analysis.py
│   │   │   └── wizard.py
│   │   ├── services/      # Business logic
│   │   ├── core/          # Config & security
│   │   ├── models.py      # Database models
│   │   ├── schemas.py     # Pydantic schemas
│   │   └── main.py        # FastAPI app
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx           # Landing page
│   │   ├── login/
│   │   ├── signup/
│   │   ├── wizard/
│   │   ├── auth/callback/
│   │   └── protected/         # Protected routes
│   │       ├── layout.tsx
│   │       ├── dashboard/
│   │       ├── subjects/
│   │       ├── predictions/
│   │       ├── tests/
│   │       ├── chat/
│   │       ├── upload/
│   │       └── profile/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── lib/           # API client, utilities
│   │   └── hooks/         # Custom hooks
│   └── public/
│
├── .env                   # Environment config
├── .env.example          # Environment template
└── bugs.md              # Known issues
```

---

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://...
SUPABASE_URL=https://...
SUPABASE_SERVICE_KEY=...
JWT_SECRET=...
GEMINI_API_KEY=...
BYTEZ_API_KEY=...
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /auth/signup` | User registration |
| `POST /auth/login` | User login |
| `GET /subjects` | List subjects |
| `POST /subjects` | Create subject |
| `POST /upload/` | Upload question paper |
| `GET /predictions/{id}/latest` | Get predictions |
| `POST /tests/generate` | Generate mock test |
| `POST /chat/tutor` | AI tutor chat |
| `GET /wizard/status` | Setup wizard status |

---

## Deployment

- **Frontend**: Vercel (push to main)
- **Backend**: Render / Railway
- **Database**: Supabase PostgreSQL

---

## License

MIT
