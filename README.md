# GitHub Trending Push 🚀

[🇺🇸 English](README.md) | [🇨🇳 简体中文](README_CN.md)

Automatically scrape GitHub Trending repositories, generate AI-powered summaries, and deliver them via email and RESTful API.

## ✨ Features

- **Multi-dimension Scraping**: Daily, Weekly, Monthly trending repositories
- **AI-Powered Summaries**: Multiple AI models (DeepSeek, NVIDIA, GLM, Kimi) with automatic fallback
- **RESTful API**: FastAPI backend with 15+ endpoints and Swagger UI
- **Vue 3 Dashboard**: Modern responsive frontend with real-time data visualization
- **Email Push**: Beautiful HTML templates with responsive design
- **Scheduled Tasks**: Automatic daily/weekly/monthly execution
- **Health Monitoring**: 5 subsystems health check (Database, AI, Email, GitHub API, System)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configuration

```bash
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml` and fill in:
- **AI Model API Key** (at least one: DeepSeek/NVIDIA/GLM/Kimi)
- **Email SMTP Settings** (sender, password, recipients)
- **GitHub Token** (optional, for higher rate limits)

### 3. Start Server

```bash
python start_api.py
```

- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/api/docs

## 🎨 Frontend Setup (Optional)

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

## 📖 API Endpoints

**Trending**
- `GET /api/trending/{time_range}` - Get trending repositories (daily/weekly/monthly)

**Statistics**
- `GET /api/stats/overview` - Statistics overview
- `GET /api/stats/languages` - Language distribution
- `GET /api/stats/history` - Historical statistics
- `GET /api/stats/comparison` - Week-over-week comparison

**AI Analysis**
- `GET /api/analysis/{owner}/{repo}` - Detailed AI analysis report
- `GET /api/analysis/{owner}/{repo}/stream` - Streaming AI analysis (SSE)

**Settings**
- `GET /api/settings` - Get all settings
- `PUT /api/settings` - Update settings
- `PUT /api/scheduler` - Control scheduler (start/stop)

**Tasks**
- `POST /api/tasks/run` - Manually trigger task
- `GET /api/tasks/status/{task_id}` - Query task status

**System**
- `GET /api/health` - Health check (5 subsystems)

## 📂 Project Structure

```
github_trending_push/
├── config/                 # Configuration files
├── src/
│   ├── core/              # Database models and services
│   ├── collectors/        # GitHub scraping
│   ├── analyzers/         # AI analysis and classification
│   ├── outputs/           # Report generation and email
│   ├── infrastructure/    # Logging, scheduling, monitoring
│   └── web/               # FastAPI routes and schemas
├── frontend/              # Vue 3 dashboard
├── templates/             # HTML templates
├── scripts/               # Utility scripts
└── start_api.py           # Main entry point
```

## 🛠️ Tech Stack

**Backend**: FastAPI, SQLAlchemy, Loguru, BeautifulSoup4, httpx

**Frontend**: Vue 3, Vite, Element Plus, ECharts, Pinia

**AI Models**: DeepSeek, NVIDIA, GLM, Kimi (Moonshot)

## 🚨 Troubleshooting

**Email sending fails**
- Use SMTP app password, not account password
- Gmail: https://myaccount.google.com/apppasswords

**Database locked error**
- Ensure only one instance is running

**AI API quota exceeded**
- Check API key validity
- Configure multi-model fallback in config

## 📄 License

MIT License

---

**⭐ If you find this project helpful, please give it a star!**
