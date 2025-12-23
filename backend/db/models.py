"""数据库模型"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from .database import Database


class TranslationHistory:
    """翻译历史记录模型"""
    
    def __init__(self, db: Database):
        """初始化
        
        Args:
            db: 数据库实例
        """
        self.db = db
    
    def create(self, task_data: Dict[str, Any]) -> bool:
        """创建翻译记录
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            是否创建成功
        """
        try:
            config_json = json.dumps(task_data.get('config', {}), ensure_ascii=False)
            result_json = json.dumps(task_data.get('result', {}), ensure_ascii=False) if task_data.get('result') else None
            
            self.db.execute("""
                INSERT INTO translation_history 
                (task_id, status, filename, source_lang, target_lang, model, 
                 start_time, end_time, progress, stage, message, error, config, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data['task_id'],
                task_data['status'],
                task_data['filename'],
                task_data['source_lang'],
                task_data['target_lang'],
                task_data['model'],
                task_data['start_time'],
                task_data.get('end_time'),
                task_data.get('progress', 0),
                task_data.get('stage'),
                task_data.get('message'),
                task_data.get('error'),
                config_json,
                result_json
            ))
            return True
        except Exception as e:
            print(f"创建翻译记录失败: {e}")
            return False
    
    def update(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """更新翻译记录
        
        Args:
            task_id: 任务ID
            updates: 要更新的字段字典
            
        Returns:
            是否更新成功
        """
        try:
            set_clauses = []
            params = []
            
            for key, value in updates.items():
                if key in ['config', 'result'] and isinstance(value, dict):
                    value = json.dumps(value, ensure_ascii=False)
                set_clauses.append(f"{key} = ?")
                params.append(value)
            
            set_clauses.append("updated_at = CURRENT_TIMESTAMP")
            params.append(task_id)
            
            query = f"""
                UPDATE translation_history 
                SET {', '.join(set_clauses)}
                WHERE task_id = ?
            """
            
            self.db.execute(query, tuple(params))
            return True
        except Exception as e:
            print(f"更新翻译记录失败: {e}")
            return False
    
    def get_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取翻译记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务数据字典或None
        """
        row = self.db.fetchone(
            "SELECT * FROM translation_history WHERE task_id = ?",
            (task_id,)
        )
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """获取所有翻译记录
        
        Args:
            limit: 限制返回数量
            offset: 偏移量
            
        Returns:
            任务数据列表
        """
        query = "SELECT * FROM translation_history ORDER BY created_at DESC"
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        rows = self.db.fetchall(query)
        return [self._row_to_dict(row) for row in rows]
    
    def delete(self, task_id: str) -> bool:
        """删除翻译记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        try:
            self.db.execute(
                "DELETE FROM translation_history WHERE task_id = ?",
                (task_id,)
            )
            return True
        except Exception as e:
            print(f"删除翻译记录失败: {e}")
            return False
    
    def upsert(self, task_data: Dict[str, Any]) -> bool:
        """插入或更新翻译记录
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            是否操作成功
        """
        existing = self.get_by_id(task_data['task_id'])
        
        if existing:
            updates = {k: v for k, v in task_data.items() if k != 'task_id'}
            return self.update(task_data['task_id'], updates)
        else:
            return self.create(task_data)
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """将数据库行转换为字典
        
        Args:
            row: 数据库行对象
            
        Returns:
            字典格式的数据
        """
        data = dict(row)
        
        if data.get('config'):
            try:
                data['config'] = json.loads(data['config'])
            except:
                data['config'] = {}
        
        if data.get('result'):
            try:
                data['result'] = json.loads(data['result'])
            except:
                data['result'] = None
        
        data.pop('created_at', None)
        data.pop('updated_at', None)
        
        return data
