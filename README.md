# GitHub Trending Push 🚀

[🇺🇸 English](README.md) | [🇨🇳 简体中文](README_CN.md)

A Python tool that automatically scrapes GitHub Trending repositories, generates summaries using AI, and pushes them via email on a schedule.

## ✨ Features

- **Multi-dimension Scraping**: Supports scraping trending repositories Daily, Weekly, and Monthly.
- **AI-Powered Summaries**:
  - Integrates multiple AI models (DeepSeek, NVIDIA, GLM, Moonshot/Kimi).
  - Automatically generates concise summaries (Highlights, Core Features, Use Cases).
  - Supports multi-model automatic fallback for high availability.
- **Beautiful Email Push**:
  - Uses responsive HTML email templates.
  - Clearly displays project names, star growth, programming languages, and AI summaries.
- **Smart Deduplication**:
  - Automatically records history to prevent duplicate recommendations.
- **Robust Design**:
  - Automatic retry mechanism for network requests.
  - Comprehensive logging with Loguru.
  - Daemon mode support for long-running execution.

## 🛠️ Requirements

- Python 3.10+ (Python 3.14 recommended)
- Dependencies: See `requirements.txt`

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configuration

Copy the example configuration file and modify it:

```bash
cp config/config.example.yaml config/config.yaml
```

Edit `config/config.yaml` and fill in the key information:
- **GitHub Token** (Optional, recommended for higher API rate limits)
- **AI Model API Key** (Supports DeepSeek, NVIDIA, etc. At least one is required)
- **Email SMTP Settings** (For sending emails, App Password is recommended)

### 3. Verify Configuration

Run the following command to check if the configuration is correct:

```bash
python main.py --validate
```

### 4. Test Run

Execute a one-time daily scraping task for testing:

```bash
python main.py --test
```

## 📖 Usage Guide

### Command Line Arguments

```bash
python main.py [OPTIONS]

Options:
  --validate       Validate configuration format
  --test           Test run (execute one daily task)
  --daily          Execute one daily task
  --weekly         Execute one weekly task
  --monthly        Execute one monthly task
  --daemon, -d     Start daemon (run periodically in background)
  --config PATH    Specify configuration file path (default: config/config.yaml)
```

### Scheduling Strategy

- **Daily Push**: Every day at 08:00 (Asia/Shanghai)
- **Weekly Push**: Every Sunday at 22:00
- **Monthly Push**: The last day of every month at 22:00

*Note: Schedule times can be customized in `config.yaml`.*

## 📂 Project Structure

```
github_trending_push/
├── config/
│   ├── config.yaml          # Configuration file
│   └── config.example.yaml  # Configuration template
├── src/
│   ├── ai_summarizer.py     # AI summary generation module
│   ├── config_validator.py  # Configuration validation module
│   ├── logging_config.py    # Logging configuration module
│   ├── mailer.py            # Email sending module
│   ├── scheduler.py         # Task scheduler
│   └── scraper_treding.py   # GitHub scraper module
├── templates/
│   └── email_template.html  # Email HTML template
├── data/
│   └── trending.json        # Historical data (for deduplication)
├── logs/                    # Runtime logs
├── main.py                  # Main entry point
└── requirements.txt         # Project dependencies
```

## 📝 Development Notes

- **Logs**: Default saved in `logs/trending.log`, with automatic rotation (10MB/file, kept for 7 days).
- **Data**: Scraped raw data is saved in JSON format in `data/trending.json`.

## 🤝 Contribution

Issues and Pull Requests are welcome!

## 📄 License

MIT License
