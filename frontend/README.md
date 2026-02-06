# GitHub Trending Push - Web Dashboard

## 简介

这是 GitHub Trending Push 项目的 Web Dashboard 前端界面，使用纯 HTML + CDN 方式实现。

## 技术栈

- **Vue 3** - 渐进式JavaScript框架（CDN引入）
- **Element Plus** - Vue 3组件库（CDN引入）
- **ECharts** - 数据可视化图表库（CDN引入）
- **Axios** - HTTP客户端（CDN引入）

## 快速开始

### 1. 启动后端API

```bash
cd ..
python start_api.py
```

后端API将运行在 `http://localhost:8000`

### 2. 访问前端

直接在浏览器中打开 `index.html` 文件即可：

```bash
# Windows
start index.html

# macOS
open index.html

# Linux
xdg-open index.html
```

或者使用任意HTTP服务器：

```bash
# Python 3
python -m http.server 5173

# Node.js
npx serve .
```

然后访问 `http://localhost:5173`

## 功能模块

### 📊 总览页

- 统计卡片（总项目数、总Stars、增长数）
- 语言分布饼图

### 📦 项目列表

- trending项目表格展示
- 按语言、时间范围筛选
- 排序功能

### 📈 趋势分析

- Top 10增长项目
- 关键词云图

### ⚙️ 设置中心

- 订阅配置
- 邮件设置

## API端点

前端调用以下后端API端点：

- `GET /api/stats/overview` - 获取统计概览
- `GET /api/trending/{time_range}` - 获取trending列表
- `GET /api/stats/languages` - 获取语言分布

## 部署说明

### 生产环境部署

1. 将 `index.html` 部署到任意静态文件服务器（Nginx、Apache等）
2. 确保后端API可访问
3. 根据需要修改 `index.html` 中的 `API_BASE_URL`

### CORS配置

如果前后端不在同一域名，需要在后端配置CORS：

```python
# 后端已配置CORS，支持跨域访问
```

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 许可证

MIT License
