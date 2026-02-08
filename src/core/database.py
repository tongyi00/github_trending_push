#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库连接和会话管理
"""

from pathlib import Path
from .models import Base, set_encryption_functions
from loguru import logger
from contextlib import contextmanager
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, db_path: str = "data/trending.db", echo: bool = False):
        self._init_encryption()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        db_url = f"sqlite:///{self.db_path}"

        self.engine = create_engine(
            db_url,
            echo=echo,
            connect_args={
                'check_same_thread': False,
                'timeout': 30
            },
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )

        # 启用 SQLite 外键约束
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        self.SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=self.engine))

        logger.info(f"Database initialized at {self.db_path}")

    def _init_encryption(self):
        """Initialize encryption functions (lazy import to avoid circular dependency)"""
        try:
            from ..infrastructure.security import encrypt_sensitive, decrypt_sensitive
            set_encryption_functions(encrypt_sensitive, decrypt_sensitive)
        except ImportError:
            logger.warning("Security module not available, encryption disabled")

    def init_db(self):
        """初始化数据库表"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")

    def drop_all(self):
        """删除所有表（谨慎使用）"""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")

    @contextmanager
    def get_session(self):
        """获取数据库会话（上下文管理器）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """关闭数据库连接"""
        self.SessionLocal.remove()
        self.engine.dispose()
        logger.info("Database connections closed")
