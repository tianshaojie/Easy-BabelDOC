import json
import copy
from pathlib import Path
from typing import List, Dict, Any, Optional

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
    """从文件加载翻译历史"""
    from config.settings import HISTORY_FILE
    
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            return []
        sanitized_history = []
        modified = False
        for item in history:
            sanitized = remove_sensitive_config(item)
            if sanitized != item:
                modified = True
            sanitized_history.append(sanitized)
        if modified:
            save_history(sanitized_history)
        return sanitized_history
    return []

def save_history(history):
    """保存历史记录到文件"""
    from config.settings import HISTORY_FILE
    
    try:
        clean_history = convert_paths_to_strings(history)
        print(f"准备保存历史记录，共 {len(clean_history)} 条")
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(clean_history, f, ensure_ascii=False, indent=2)
        print("历史记录保存成功")
    except Exception as e:
        print(f"保存历史记录失败: {e}")
        import traceback
        traceback.print_exc()

def add_to_history(task_data: Dict):
    """添加任务到历史记录"""
    sanitized_task = remove_sensitive_config(task_data)
    history = load_history()
    for i, item in enumerate(history):
        if item.get('task_id') == sanitized_task.get('task_id'):
            history[i] = sanitized_task
            save_history(history)
            return
    history.append(sanitized_task)
    save_history(history)

def get_task(task_id: str, active_translations: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """从内存或历史记录获取任务信息"""
    if task_id in active_translations:
        return active_translations[task_id]
    
    history = load_history()
    for task in history:
        if task.get("task_id") == task_id:
            return task
    return None
