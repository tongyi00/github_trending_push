# GitHub Trending Push 🚀

[🇺🇸 English](README.md) | [🇨🇳 简体中文](README_CN.md)

一个自动抓取 GitHub Trending 热门项目、利用 AI 生成中文摘要并通过邮件定时推送的 Python 工具。

## ✨ 功能特点

- **多维度抓取**：支持每日 (Daily)、每周 (Weekly)、每月 (Monthly) 的热门项目抓取。
- **AI 智能摘要**：
  - 集成多种 AI 模型（DeepSeek, NVIDIA, GLM, Moonshot/Kimi）。
  - 自动生成精简的中文摘要（亮点、核心功能、适用人群）。
  - 支持多模型自动降级（Fallback），确保服务高可用。
- **精美邮件推送**：
  - 使用响应式 HTML 邮件模板。
  - 清晰展示项目名称、Stars 增长、编程语言及 AI 摘要。
- **智能去重**：
  - 自动记录历史推送项目，防止重复推荐。
- **健壮性设计**：
  - 网络请求自动重试机制。
  - 完善的日志记录 (Loguru)。
  - 守护进程模式，支持长期运行。

## 🛠️ 环境要求

- Python 3.10+ (推荐 Python 3.14)
- 依赖库：见 `requirements.txt`

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置文件

复制示例配置文件并修改：

```bash
cp config/config.example.yaml config/config.yaml
```

编辑 `config/config.yaml`，填入以下关键信息：
- **GitHub Token** (可选，建议配置以提高 API 限额)
- **AI 模型 API Key** (支持 DeepSeek, NVIDIA 等，至少配置一个)
- **邮箱 SMTP 设置** (用于发送邮件，推荐使用应用专用密码)

### 3. 验证配置

运行以下命令检查配置是否正确：

```bash
python main.py --validate
```

### 4. 测试运行

执行一次每日抓取任务进行测试：

```bash
python main.py --test
```

## 📖 使用指南

### 命令行参数

```bash
python main.py [OPTIONS]

选项:
  --validate       验证配置文件格式
  --test           测试运行（执行一次每日任务）
  --daily          执行一次每日任务
  --weekly         执行一次每周任务
  --monthly        执行一次每月任务
  --daemon, -d     启动守护进程（后台定时运行）
  --config PATH    指定配置文件路径 (默认: config/config.yaml)
```

### 定时任务策略

- **每日推送**: 每天 08:00 (北京时间)
- **每周推送**: 每周日 22:00
- **每月推送**: 每月最后一天 22:00

*注：时间可在 `config.yaml` 中自定义修改。*

## 📂 项目结构

```
github_trending_push/
├── config/
│   ├── config.yaml          # 配置文件
│   └── config.example.yaml  # 配置模板
├── src/
│   ├── ai_summarizer.py     # AI 摘要生成模块
│   ├── config_validator.py  # 配置验证模块
│   ├── logging_config.py    # 日志配置模块
│   ├── mailer.py            # 邮件发送模块
│   ├── scheduler.py         # 定时任务调度器
│   └── scraper_treding.py   # GitHub 爬虫模块
├── templates/
│   └── email_template.html  # 邮件 HTML 模板
├── data/
│   └── trending.json        # 历史数据（用于去重）
├── logs/                    # 运行日志
├── main.py                  # 程序主入口
└── requirements.txt         # 项目依赖
```

## 📝 开发说明

- **日志**：默认保存在 `logs/trending.log`，会自动轮转（10MB/文件，保留 7 天）。
- **数据**：抓取的原始数据会以 JSON 格式保存在 `data/trending.json` 中。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License
