"""SQLite 数据库管理"""
import sqlite3
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger("easy_babeldoc.db")


class Database:
    """SQLite 数据库管理类"""
    
    def __init__(self, db_path: Path):
        """初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """确保数据库文件和表结构存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS translation_history (
                    task_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    source_lang TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    model TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    progress INTEGER DEFAULT 0,
                    stage TEXT,
                    message TEXT,
                    error TEXT,
                    config TEXT,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON translation_history(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON translation_history(created_at DESC)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute(self, query: str, params: tuple = ()):
        """执行SQL语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            cursor对象
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
    
    def fetchall(self, query: str, params: tuple = ()):
        """查询所有结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            结果列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def fetchone(self, query: str, params: tuple = ()):
        """查询单条结果
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            单条结果或None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
