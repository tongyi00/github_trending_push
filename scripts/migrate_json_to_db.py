#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JSON 历史数据迁移到 SQLite 数据库
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from loguru import logger
from src.core.database import DatabaseManager
from src.core.data_repository import DataRepository


def migrate_json_to_db(json_path: str = "data/trending.json", db_path: str = "data/trending.db"):
    """迁移 JSON 数据到数据库"""
    json_file = Path(json_path)

    if not json_file.exists():
        logger.warning(f"JSON file {json_path} not found, skipping migration")
        return

    logger.info(f"Starting migration from {json_path} to {db_path}...")

    db_manager = DatabaseManager(db_path=db_path)
    db_manager.init_db()
    data_repo = DataRepository(db_manager)

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)

        total_migrated = 0

        for time_range, date_records in all_data.items():
            logger.info(f"Migrating {time_range} records...")

            for date_str, repos_dict in date_records.items():
                try:
                    record_date = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Invalid date format: {date_str}, skipping")
                    continue

                repos_list = []
                for repo_name, repo_data in repos_dict.items():
                    repos_list.append(repo_data)

                count = data_repo.save_trending_data(repos_list, time_range, record_date)
                total_migrated += count
                logger.info(f"Migrated {count} records for {date_str} ({time_range})")

        logger.success(f"Migration completed! Total {total_migrated} records migrated")

        stats = data_repo.get_repository_stats()
        logger.info(f"Database stats: {stats}")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        db_manager.close()


if __name__ == "__main__":
    migrate_json_to_db()
