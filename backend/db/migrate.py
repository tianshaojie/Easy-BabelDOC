#!/usr/bin/env python3
"""数据库迁移系统 - 版本化管理数据库结构变更"""
import sqlite3
import sys
from pathlib import Path
from typing import Callable, List
import logging

logger = logging.getLogger("easy_babeldoc.migrate")

class Migration:
    """单个迁移版本"""
    def __init__(self, version: int, description: str, upgrade: Callable):
        self.version = version
        self.description = description
        self.upgrade = upgrade

def migration_v1_add_user_support(cursor: sqlite3.Cursor):
    """版本1: 添加用户支持"""
    logger.info("执行迁移 v1: 添加用户支持")
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='users'
    """)
    
    if not cursor.fetchone():
        logger.info("创建users表...")
        cursor.execute("""
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                is_guest INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_username 
            ON users(username)
        """)
        logger.info("✓ users表创建完成")
    
    cursor.execute("PRAGMA table_info(translation_history)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'user_id' not in columns:
        logger.info("添加user_id列到translation_history表...")
        cursor.execute("""
            ALTER TABLE translation_history 
            ADD COLUMN user_id TEXT
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_id 
            ON translation_history(user_id)
        """)
        logger.info("✓ translation_history表迁移完成")

def migration_v2_add_models_table(cursor: sqlite3.Cursor):
    """版本2: 添加模型配置表"""
    logger.info("执行迁移 v2: 添加模型配置表")
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='models'
    """)
    
    if not cursor.fetchone():
        logger.info("创建models表...")
        cursor.execute("""
            CREATE TABLE models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                base_url TEXT NOT NULL,
                api_key TEXT NOT NULL,
                model TEXT NOT NULL,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_models_user_id 
            ON models(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_models_is_default 
            ON models(user_id, is_default)
        """)
        logger.info("✓ models表创建完成")

MIGRATIONS: List[Migration] = [
    Migration(1, "添加用户支持", migration_v1_add_user_support),
    Migration(2, "添加模型配置表", migration_v2_add_models_table),
]

def get_current_version(cursor: sqlite3.Cursor) -> int:
    """获取当前数据库版本"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='schema_version'
    """)
    
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        return 0
    
    cursor.execute("SELECT MAX(version) FROM schema_version")
    result = cursor.fetchone()
    return result[0] if result[0] is not None else 0

def set_version(cursor: sqlite3.Cursor, version: int, description: str):
    """设置数据库版本"""
    cursor.execute(
        "INSERT INTO schema_version (version, description) VALUES (?, ?)",
        (version, description)
    )

def run_migrations(db_path: Path) -> bool:
    """运行所有待执行的迁移"""
    logger.info(f"检查数据库迁移: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        current_version = get_current_version(cursor)
        logger.info(f"当前数据库版本: {current_version}")
        
        pending_migrations = [m for m in MIGRATIONS if m.version > current_version]
        
        if not pending_migrations:
            logger.info("数据库已是最新版本,无需迁移")
            return True
        
        logger.info(f"发现 {len(pending_migrations)} 个待执行的迁移")
        
        for migration in pending_migrations:
            logger.info(f"应用迁移 v{migration.version}: {migration.description}")
            migration.upgrade(cursor)
            set_version(cursor, migration.version, migration.description)
            conn.commit()
            logger.info(f"✓ 迁移 v{migration.version} 完成")
        
        logger.info("所有数据库迁移成功完成!")
        return True
        
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}", exc_info=True)
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    import os
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir))
    
    from config.settings import DB_FILE
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s:%(name)s:%(message)s'
    )
    
    if run_migrations(DB_FILE):
        sys.exit(0)
    else:
        sys.exit(1)
