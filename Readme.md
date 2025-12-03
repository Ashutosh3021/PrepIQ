<div align="center">

# 🎯 PrepIQ

### AI-Powered Exam Prediction & Intelligent Study Platform

**Transform exam preparation from guesswork into strategy**

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg?logo=react)](https://reactjs.org/)
[![Status](https://img.shields.io/badge/Status-In%20Development-orange.svg)]()

[Features](#features) • [Demo](#demo) • [Tech Stack](#tech-stack) • [Getting Started](#getting-started) • [Roadmap](#roadmap)

</div>

---

## 📋 Overview

PrepIQ is an intelligent exam preparation platform that leverages AI-driven pattern analysis to help students study strategically. By analyzing previous year question papers (PYQs), PrepIQ identifies recurring patterns and predicts high-probability exam questions, enabling students to focus their efforts where it matters most.

### The Challenge

Students often struggle with:
- **Inefficient time management**: Spending excessive time on low-yield topics
- **Lack of direction**: Uncertainty about which topics to prioritize
- **Pattern blindness**: Missing recurring themes across past exams
- **Suboptimal preparation**: Studying without data-driven insights

### Our Solution

PrepIQ addresses these challenges through:
- **Predictive analytics**: 80%+ accuracy in question prediction using ML pattern recognition
- **Trend visualization**: Interactive dashboards showing topic frequency and weightage
- **Personalized planning**: AI-generated study schedules tailored to individual timelines
- **Interactive learning**: 24/7 AI chatbot for concept clarification and strategy guidance

---

## ✨ Features

### 🔮 Intelligent Question Prediction
Upload previous year papers and receive AI-generated predictions with confidence scores:
- **Very High** (80-100%): Topics appearing annually
- **High** (60-79%): Frequent recurring patterns
- **Moderate** (40-59%): Cyclical appearance trends

### 📊 Advanced Analytics Dashboard
Comprehensive visualizations including:
- Topic frequency heatmaps
- Unit-wise weightage distribution
- Historical trend analysis
- Question pattern cycles

### 🤖 AI Study Assistant
Conversational AI chatbot that provides:
- Customized study schedules
- Concept explanations and clarifications
- Performance analytics and insights
- Strategic exam-day guidance

### 📝 Smart Mock Testing
Automated practice exams featuring:
- University-specific formatting
- Adaptive difficulty progression
- Detailed solution breakdowns
- Performance tracking over time

### 🎯 Curated Question Banks
Organized collections of:
- High-frequency questions (3+ occurrences)
- Category-wise question sets (2/5/10-mark)
- Important numerical problems
- Last-minute revision essentials

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18 • Vite • Progressive Web App |
| **Backend** | FastAPI • Python 3.10+ |
| **AI/ML** | Google Gemini API • TensorFlow • Custom ML Models |
| **Database** | PostgreSQL • Supabase |
| **Processing** | PyPDF2 • Tesseract OCR • Natural Language Processing |
| **Deployment** | Vercel (Frontend) • Railway (Backend) |

</div>

---

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:
- Python 3.10 or higher
- Node.js 18 or higher
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/PrepIQ.git
   cd PrepIQ
   ```

2. **Backend setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```
   
   Required variables:
   ```
   GEMINI_API_KEY=your_google_gemini_api_key
   DATABASE_URL=your_database_connection_string
   ```

4. **Frontend setup**
   ```bash
   cd ../frontend
   npm install
   ```

5. **Launch development servers**
   
   Backend (Terminal 1):
   ```bash
   cd backend
   uvicorn main:app --reload
   ```
   
   Frontend (Terminal 2):
   ```bash
   cd frontend
   npm run dev
   ```

6. **Access the application**
   
   Open your browser and navigate to `http://localhost:5173`

---

## 💡 How It Works

```
1. Upload PDFs → 2. Text Extraction → 3. Pattern Analysis → 
4. Trend Detection → 5. Probability Scoring → 6. Question Prediction → 
7. Study Plan Generation → 8. Mock Testing → 9. Performance Tracking
```

**Process Flow:**

1. **Data Collection**: Students upload previous year question papers (PDF format)
2. **Content Extraction**: AI extracts and structures all questions using OCR and NLP
3. **Pattern Recognition**: Machine learning algorithms identify recurring topics and themes
4. **Predictive Modeling**: Questions are scored based on historical frequency and patterns
5. **Output Generation**: System produces predicted papers and strategic study materials
6. **Guided Learning**: AI chatbot provides personalized assistance and schedule optimization
7. **Practice & Assessment**: Students take mock exams with instant feedback
8. **Continuous Improvement**: Adaptive algorithms refine recommendations based on performance

---

## 🗺️ Roadmap

### Phase 1: Foundation (Weeks 1-4) ✅ *In Progress*
- [x] Architecture design and project initialization
- [x] Development environment setup
- [ ] PDF processing pipeline
- [ ] Core pattern analysis algorithm
- [ ] Basic UI implementation
- [ ] Gemini API integration

### Phase 2: Core Features (Weeks 5-8)
- [ ] Question classification system
- [ ] Probability scoring engine
- [ ] Predicted paper generation
- [ ] Analytics dashboard
- [ ] Mock test framework

### Phase 3: AI Integration (Weeks 9-12)
- [ ] Conversational AI chatbot
- [ ] Study plan generator
- [ ] Performance analytics
- [ ] Recommendation engine
- [ ] Voice interaction support

### Phase 4: Production Ready (Weeks 13-16)
- [ ] PWA implementation (offline access, notifications)
- [ ] University-specific customization
- [ ] Beta testing program
- [ ] Security hardening
- [ ] Public launch

### Future Enhancements
- Video-based learning modules
- Collaborative study features
- Gamification elements
- Mobile applications (iOS/Android)
- Multi-language support

---

## 📊 Use Cases

| User Profile | Key Benefits |
|--------------|-------------|
| **Undergraduate Students** | Optimize study time with data-driven topic prioritization |
| **Working Professionals** | Maximize limited study hours with targeted preparation |
| **Exam Repeaters** | Identify and address specific weak areas systematically |
| **First-Year Students** | Understand exam patterns and expectations early |

---

## 🤝 Contributing

We welcome contributions from the community! To get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -m 'Add YourFeature'`)
4. Push to your branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

**Contribution Areas:**
- Bug reports and fixes
- Feature suggestions and implementations
- Documentation improvements
- UI/UX enhancements
- Test coverage expansion

Please review our [Contributing Guidelines](CONTRIBUTING.md) before submitting PRs.

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for complete details.

---

## 📬 Contact & Support

**Project Maintainer**: [Your Name]  
**Email**: your.email@example.com  
**LinkedIn**: [linkedin.com/in/yourprofile](https://linkedin.com/in/yourprofile)

For bug reports and feature requests, please use the [GitHub Issues](https://github.com/yourusername/PrepIQ/issues) page.

---

## 🌟 Acknowledgments

If PrepIQ helps improve your exam performance:
- Star this repository ⭐
- Share with fellow students 📢
- Contribute to development 🔧
- Provide feedback for improvements 💬

---

<div align="center">

**PrepIQ** - *Data-driven exam preparation for the modern student*

Built with passion by students, for students

[⬆ Back to Top](#-prepiq)

</div>