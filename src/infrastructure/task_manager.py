#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
后台任务管理器
"""

import uuid
import threading
from datetime import datetime
from typing import Optional, Dict


class BackgroundTaskManager:
    """后台任务管理器（线程安全）"""
    def __init__(self):
        self.tasks: Dict[str, dict] = {}
        self.ttl_seconds = 3600
        self._lock = threading.Lock()

    def cleanup_expired(self):
        """清理过期任务"""
        now = datetime.now()
        expired_keys = []
        with self._lock:
            for task_id, task_info in self.tasks.items():
                finished_at = task_info.get("finished_at")
                if finished_at and task_info["status"] in ("success", "failed"):
                    try:
                        finish_time = datetime.fromisoformat(finished_at)
                        if (now - finish_time).total_seconds() > self.ttl_seconds:
                            expired_keys.append(task_id)
                    except (ValueError, TypeError):
                        pass
            for key in expired_keys:
                del self.tasks[key]

    def create_task(self, task_type: str) -> str:
        """创建新任务"""
        self.cleanup_expired()
        task_id = str(uuid.uuid4())
        with self._lock:
            self.tasks[task_id] = {
                "task_type": task_type,
                "status": "pending",
                "started_at": None,
                "finished_at": None,
                "repos_found": 0,
                "repos_after_filter": 0,
                "email_sent": False,
                "error_message": None
            }
        return task_id

    def update_task(self, task_id: str, **kwargs):
        """更新任务状态"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id].update(kwargs)

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取任务信息"""
        with self._lock:
            task = self.tasks.get(task_id)
            return task.copy() if task else None
