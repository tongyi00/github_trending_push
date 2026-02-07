# 调度器集成设计方案

**日期**: 2026-02-08
**目标**: 将 main.py 的定时任务功能集成到 start_api.py，实现单一进程运行 API 服务和后台调度

## 需求决策

| 决策点 | 选择 |
|--------|------|
| 启动方式 | 单一进程模式 - 一个进程同时运行 API 和定时任务 |
| 前端交互 | 完整控制 - 查看、手动触发、启停调度器、修改调度时间 |
| 配置持久化 | 数据库优先 - SQLite 存储配置，优先级高于 config.yaml |
| 执行历史 | 基础记录 - 时间、类型、状态、错误信息 |
| 界面位置 | Settings.vue - 在设置页面新增调度任务区块 |

## 数据库变更

### 新增表

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

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/scheduler/status` | GET | 获取调度器状态和下次执行时间 |
| `/api/scheduler/config` | GET | 获取所有调度配置 |
| `/api/scheduler/config/{task_type}` | PUT | 修改指定任务调度配置 |
| `/api/scheduler/start` | POST | 启动调度器 |
| `/api/scheduler/stop` | POST | 停止调度器 |
| `/api/tasks/run` | POST | 手动触发任务（body: {task_type}) |
| `/api/tasks/history` | GET | 获取执行历史（query: limit） |

## 文件变更

### 删除
- `main.py`

### 新增
- `src/core/trending_push.py` — 业务核心类（从 main.py 迁移）
- `src/web/routers/scheduler.py` — 调度器 API 路由
- `frontend/src/api/scheduler.ts` — 前端 API 调用

### 修改
- `start_api.py` — 添加启动/关闭事件，初始化调度器
- `src/infrastructure/scheduler.py` — 增强调度器，支持数据库配置
- `src/core/models.py` — 新增 SchedulerConfig、TaskHistory 模型
- `src/core/database.py` — 新增表初始化
- `src/web/api.py` — 注册新路由
- `frontend/src/views/Settings.vue` — 添加调度任务区块

## 代码结构

### TrendingPush 类

```python
# src/core/trending_push.py
@dataclass
class TaskResult:
    success: bool
    task_type: str
    started_at: datetime
    finished_at: datetime
    error_message: Optional[str] = None

class TrendingPush:
    def __init__(self, config_path: str = "config/config.yaml"):
        # 初始化各组件

    def run_task(self, time_range: str) -> TaskResult:
        # 执行任务，返回结构化结果
```

### 调度器增强

```python
# src/infrastructure/scheduler.py
class TrendingScheduler:
    def __init__(self, config, db_manager):
        self.db_manager = db_manager

    def get_config_from_db(self) -> list[SchedulerConfig]
    def update_config(self, task_type: str, enabled: bool, cron: str)
    def get_next_run_times(self) -> dict[str, datetime]
    def is_running(self) -> bool
    def start(self)
    def stop(self)
```

### 应用启动

```python
# start_api.py
@app.on_event("startup")
async def startup():
    app.state.trending_push = TrendingPush()
    app.state.scheduler = TrendingScheduler(config, db_manager)
    app.state.scheduler.start()

@app.on_event("shutdown")
async def shutdown():
    app.state.scheduler.stop()
```

## 前端变更

### Settings.vue 新增区块

1. **调度器状态卡片** - 运行状态、启动/停止按钮
2. **调度配置表格** - 任务类型、启用开关、调度时间、下次执行、操作按钮
3. **执行历史列表** - 最近 10 条记录

## 数据迁移

首次启动时，检测 scheduler_config 表是否为空：
- 若为空，从 config.yaml 读取调度配置写入数据库
- 后续启动优先使用数据库配置
