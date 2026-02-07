# 设计方案：将 main.py 功能集成到 start_api.py

**日期**: 2026-02-08
**状态**: 已确认，待实现

## 概述

将 `main.py` 的定时任务功能集成到 `start_api.py`，实现单一进程同时运行 API 服务和后台定时任务，并通过前端提供完整的任务管理控制。

## 设计决策

| 决策点 | 选择 |
|--------|------|
| 启动方式 | 单一进程模式 - 一个进程管理 API 和定时任务 |
| 前端交互 | 完整控制 - 查看、手动触发、启停调度器、修改调度时间 |
| 配置持久化 | 数据库优先 - SQLite 存储配置，覆盖 config.yaml 默认值 |
| 执行历史 | 基础记录 - 执行时间、任务类型、成功/失败状态 |
| 界面位置 | 集成到 Settings.vue |

## 后端架构

### 新增数据库表

```sql
-- 调度配置表（覆盖 config.yaml 默认值）
CREATE TABLE scheduler_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL UNIQUE,  -- daily/weekly/monthly
    enabled INTEGER NOT NULL DEFAULT 1,
    cron_expression TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 任务执行历史表
CREATE TABLE task_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    status TEXT NOT NULL,  -- running/success/failed
    error_message TEXT
);
```

### 新增 API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/scheduler/status` | GET | 获取调度器状态和下次执行时间 |
| `/api/scheduler/config` | GET | 读取调度配置 |
| `/api/scheduler/config` | PUT | 修改调度配置 |
| `/api/scheduler/start` | POST | 启动调度器 |
| `/api/scheduler/stop` | POST | 停止调度器 |
| `/api/tasks/run` | POST | 手动触发任务（参数：task_type） |
| `/api/tasks/history` | GET | 获取执行历史 |

### 核心代码变更

#### TrendingPush 类迁移

将 `main.py` 中的 `TrendingPush` 类移至 `src/core/trending_push.py`：

```python
# src/core/trending_push.py
class TrendingPush:
    def __init__(self, config_path: str = "config/config.yaml"):
        # 保持原有初始化逻辑

    def run_task(self, time_range: str) -> TaskResult:
        # 返回结构化结果，便于记录历史
```

#### 调度器增强

`src/infrastructure/scheduler.py` 新增方法：

```python
class TrendingScheduler:
    def __init__(self, config, db_manager):
        self.db_manager = db_manager

    def get_config_from_db(self) -> dict
    def update_config(self, task_type: str, config: dict)
    def get_next_run_times(self) -> dict
    def is_running(self) -> bool
```

#### start_api.py 改造

```python
@app.on_event("startup")
async def startup():
    app.state.trending_push = TrendingPush()
    app.state.scheduler = TrendingScheduler(...)
    app.state.scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    app.state.scheduler.stop()
```

## 前端变更

### Settings.vue 新增区块

```
┌─────────────────────────────────────────────────┐
│ 调度任务                                         │
├─────────────────────────────────────────────────┤
│ 调度器状态: ● 运行中    [停止] [启动]            │
├─────────────────────────────────────────────────┤
│ 每日任务   ☑ 启用   时间: [08:00]  下次: 明天08:00 │
│ 每周任务   ☑ 启用   时间: [周日 22:00]           │
│ 每月任务   ☐ 禁用   时间: [每月最后一天 22:00]    │
├─────────────────────────────────────────────────┤
│ 手动执行   [Daily ▼] [立即执行]                  │
├─────────────────────────────────────────────────┤
│ 最近执行                                         │
│ • 2026-02-08 08:00  daily   ✓ 成功              │
│ • 2026-02-07 08:00  daily   ✓ 成功              │
│ • 2026-02-02 22:00  weekly  ✗ 失败 (网络超时)    │
└─────────────────────────────────────────────────┘
```

### 新增 API 模块

```typescript
// src/api/scheduler.ts
export function getSchedulerStatus(): Promise<SchedulerStatus>
export function updateSchedulerConfig(config: SchedulerConfig): Promise<void>
export function startScheduler(): Promise<void>
export function stopScheduler(): Promise<void>
export function runTask(type: TaskType): Promise<TaskResult>
export function getTaskHistory(limit?: number): Promise<TaskHistory[]>
```

## 实现清单

### 后端

| 文件 | 操作 |
|------|------|
| `src/core/trending_push.py` | 新建，从 main.py 迁移 TrendingPush 类 |
| `src/core/models.py` | 新增 SchedulerConfig、TaskHistory 模型 |
| `src/infrastructure/scheduler.py` | 改造，增加数据库配置读写 |
| `src/web/api.py` | 新增 6 个调度相关端点 |
| `src/web/schemas.py` | 新增请求/响应模型 |
| `start_api.py` | 改造，集成调度器生命周期管理 |
| `main.py` | 删除（功能已迁移） |

### 前端

| 文件 | 操作 |
|------|------|
| `src/api/scheduler.ts` | 新建，调度器 API 调用 |
| `src/views/Settings.vue` | 改造，新增调度任务区块 |

### 数据库

- 新增 `scheduler_config` 表
- 新增 `task_history` 表
