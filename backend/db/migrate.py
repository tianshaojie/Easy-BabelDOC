#!/usr/bin/env python3
"""数据库迁移脚本"""
import sqlite3
import sys
from pathlib import Path

def migrate_database(db_path: Path):
    """迁移数据库，添加user_id列"""
    print(f"开始迁移数据库: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # 检查translation_history表是否存在user_id列
        cursor.execute("PRAGMA table_info(translation_history)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'user_id' not in columns:
            print("添加user_id列到translation_history表...")
            cursor.execute("""
                ALTER TABLE translation_history 
                ADD COLUMN user_id TEXT
            """)
            
            # 创建索引
            print("创建user_id索引...")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id 
                ON translation_history(user_id)
            """)
            
            conn.commit()
            print("✓ translation_history表迁移完成")
        else:
            print("✓ translation_history表已包含user_id列，无需迁移")
        
        # 检查users表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        
        if not cursor.fetchone():
            print("创建users表...")
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
            
            conn.commit()
            print("✓ users表创建完成")
        else:
            print("✓ users表已存在")
        
        print("\n数据库迁移成功完成！")
        return True
        
    except Exception as e:
        print(f"\n✗ 数据库迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # 获取数据库路径
    import os
    backend_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(backend_dir))
    
    from config.settings import DB_FILE
    
    if migrate_database(DB_FILE):
        sys.exit(0)
    else:
        sys.exit(1)
