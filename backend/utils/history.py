import json
import copy
from pathlib import Path
from typing import List, Dict, Any, Optional
from db import Database, TranslationHistory

def convert_paths_to_strings(obj):
    """递归地将所有Path对象转换为字符串"""
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_paths_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_paths_to_strings(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_paths_to_strings(item) for item in obj)
    elif isinstance(obj, set):
        return {convert_paths_to_strings(item) for item in obj}
    else:
        return obj

_db_instance = None
_history_model = None

def get_db():
    """获取数据库实例（单例模式）"""
    global _db_instance, _history_model
    if _db_instance is None:
        from config.settings import DB_FILE
        _db_instance = Database(DB_FILE)
        _history_model = TranslationHistory(_db_instance)
    return _history_model

def remove_sensitive_config(task: Dict[str, Any]) -> Dict[str, Any]:
    """返回移除敏感配置后的任务副本"""
    from config.settings import SENSITIVE_CONFIG_KEYS
    
    sanitized = copy.deepcopy(task)
    config = sanitized.get("config")
    if isinstance(config, dict):
        for key in SENSITIVE_CONFIG_KEYS:
            if key in config:
                config.pop(key, None)
    return sanitized

def load_history() -> List[Dict]:
    """从数据库加载翻译历史"""
    try:
        history_model = get_db()
        history = history_model.get_all()
        return [remove_sensitive_config(item) for item in history]
    except Exception as e:
        print(f"加载历史记录失败: {e}")
        return []

def save_history(history):
    """保存历史记录到数据库（批量）"""
    try:
        history_model = get_db()
        for item in history:
            clean_item = convert_paths_to_strings(item)
            history_model.upsert(clean_item)
        print(f"历史记录保存成功，共 {len(history)} 条")
    except Exception as e:
        print(f"保存历史记录失败: {e}")
        import traceback
        traceback.print_exc()

def add_to_history(task_data: Dict):
    """添加或更新任务到历史记录"""
    try:
        sanitized_task = remove_sensitive_config(task_data)
        clean_task = convert_paths_to_strings(sanitized_task)
        history_model = get_db()
        history_model.upsert(clean_task)
    except Exception as e:
        print(f"添加历史记录失败: {e}")
        import traceback
        traceback.print_exc()

def get_task(task_id: str, active_translations: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """从内存或数据库获取任务信息"""
    if task_id in active_translations:
        return active_translations[task_id]
    
    try:
        history_model = get_db()
        task = history_model.get_by_id(task_id)
        if task:
            return remove_sensitive_config(task)
    except Exception as e:
        print(f"获取任务失败: {e}")
    
    return None

def delete_task(task_id: str) -> bool:
    """从数据库删除任务记录"""
    try:
        history_model = get_db()
        return history_model.delete(task_id)
    except Exception as e:
        print(f"删除任务失败: {e}")
        return False
