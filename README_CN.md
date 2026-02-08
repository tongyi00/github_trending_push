# GitHub Trending Push 🚀

[🇺🇸 English](README.md) | [🇨🇳 简体中文](README_CN.md)

自动抓取 GitHub Trending 热门项目，利用 AI 生成智能摘要，并通过邮件和 RESTful API 推送。

## ✨ 功能特点

- **多维度抓取**：支持每日、每周、每月热门项目抓取
- **AI 智能摘要**：集成多种 AI 模型（DeepSeek、NVIDIA、GLM、Kimi），支持自动降级
- **RESTful API**：FastAPI 后端，15+ 个端点，自带 Swagger UI
- **Vue 3 仪表盘**：现代化响应式前端，实时数据可视化
- **邮件推送**：精美的 HTML 邮件模板，响应式设计
- **定时任务**：自动执行每日/每周/每月推送
- **健康监控**：5 个子系统健康检查（数据库、AI、邮件、GitHub API、系统）

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置文件

```bash
cp config/config.example.yaml config/config.yaml
```

编辑 `config/config.yaml`，填入：
- **AI 模型 API Key**（至少配置一个：DeepSeek/NVIDIA/GLM/Kimi）
- **邮箱 SMTP 设置**（发件人、密码、收件人列表）
- **GitHub Token**（可选，提高 API 限额）

### 3. 启动服务

```bash
python start_api.py
```

- 后端 API：http://localhost:8000
- Swagger 文档：http://localhost:8000/api/docs

## 🎨 前端设置（可选）

```bash
cd frontend
npm install
npm run dev
```

前端将在 http://localhost:5173 可用

## 📖 API 端点

**趋势数据**
- `GET /api/trending/{time_range}` - 获取趋势项目（daily/weekly/monthly）

**统计分析**
- `GET /api/stats/overview` - 统计概览
- `GET /api/stats/languages` - 编程语言分布
- `GET /api/stats/history` - 历史统计数据
- `GET /api/stats/comparison` - 周对比数据

**AI 分析**
- `GET /api/analysis/{owner}/{repo}` - 详细 AI 分析报告
- `GET /api/analysis/{owner}/{repo}/stream` - 流式 AI 分析（SSE）

**设置管理**
- `GET /api/settings` - 获取所有设置
- `PUT /api/settings` - 更新设置
- `PUT /api/scheduler` - 控制调度器（启动/停止）

**任务管理**
- `POST /api/tasks/run` - 手动触发任务
- `GET /api/tasks/status/{task_id}` - 查询任务状态

**系统监控**
- `GET /api/health` - 健康检查（5个子系统）

## 📂 项目结构

```
github_trending_push/
├── config/                 # 配置文件
├── src/
│   ├── core/              # 数据库模型和服务
│   ├── collectors/        # GitHub 爬虫
│   ├── analyzers/         # AI 分析和分类
│   ├── outputs/           # 报告生成和邮件
│   ├── infrastructure/    # 日志、调度、监控
│   └── web/               # FastAPI 路由和模型
├── frontend/              # Vue 3 仪表盘
├── templates/             # HTML 模板
├── scripts/               # 工具脚本
└── start_api.py           # 主入口
```

## 🛠️ 技术栈

**后端**：FastAPI、SQLAlchemy、Loguru、BeautifulSoup4、httpx

**前端**：Vue 3、Vite、Element Plus、ECharts、Pinia

**AI 模型**：DeepSeek、NVIDIA、GLM、Kimi (Moonshot)

## 🚨 故障排查

**邮件发送失败**
- 使用 SMTP 应用专用密码，而非账户密码
- Gmail：https://myaccount.google.com/apppasswords

**数据库锁定错误**
- 确保只有一个实例在运行

**AI API 配额超限**
- 检查 API 密钥有效性
- 在配置中启用多模型降级

## 📄 许可证

MIT License

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**
