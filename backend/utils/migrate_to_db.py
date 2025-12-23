#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移工具：将 translation_history.json 迁移到 SQLite 数据库
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import HISTORY_FILE, DB_FILE
from db import Database, TranslationHistory


def migrate_json_to_db():
    """将 JSON 历史记录迁移到 SQLite 数据库"""
    
    if not HISTORY_FILE.exists():
        print(f"未找到历史文件: {HISTORY_FILE}")
        print("无需迁移")
        return
    
    print(f"开始迁移数据从 {HISTORY_FILE} 到 {DB_FILE}")
    
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        print(f"读取到 {len(history_data)} 条历史记录")
        
        db = Database(DB_FILE)
        history_model = TranslationHistory(db)
        
        success_count = 0
        error_count = 0
        
        for item in history_data:
            try:
                history_model.upsert(item)
                success_count += 1
            except Exception as e:
                print(f"迁移记录失败 {item.get('task_id', 'unknown')}: {e}")
                error_count += 1
        
        print(f"\n迁移完成:")
        print(f"  成功: {success_count} 条")
        print(f"  失败: {error_count} 条")
        
        backup_file = HISTORY_FILE.parent / f"{HISTORY_FILE.stem}.backup.json"
        HISTORY_FILE.rename(backup_file)
        print(f"\n原 JSON 文件已备份至: {backup_file}")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    migrate_json_to_db()
