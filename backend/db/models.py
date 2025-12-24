"""数据库模型"""
import json
import hashlib
import uuid
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
                (task_id, user_id, status, filename, source_lang, target_lang, model, 
                 start_time, end_time, progress, stage, message, error, config, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data['task_id'],
                task_data.get('user_id'),
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
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取所有翻译记录
        
        Args:
            limit: 限制返回数量
            offset: 偏移量
            user_id: 用户ID（可选，用于过滤）
            
        Returns:
            任务数据列表
        """
        if user_id:
            query = "SELECT * FROM translation_history WHERE user_id = ? ORDER BY created_at DESC"
            params = (user_id,)
        else:
            query = "SELECT * FROM translation_history ORDER BY created_at DESC"
            params = ()
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        rows = self.db.fetchall(query, params)
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


class User:
    """用户模型"""
    
    def __init__(self, db: Database):
        """初始化
        
        Args:
            db: 数据库实例
        """
        self.db = db
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密码哈希
        
        Args:
            password: 明文密码
            
        Returns:
            密码哈希值
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create(self, username: str, password: str, email: Optional[str] = None, is_guest: bool = False) -> Optional[str]:
        """创建用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱（可选）
            is_guest: 是否为游客
            
        Returns:
            用户ID或None（如果创建失败）
        """
        try:
            user_id = str(uuid.uuid4())
            password_hash = self.hash_password(password)
            
            self.db.execute("""
                INSERT INTO users (user_id, username, password_hash, email, is_guest)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, password_hash, email, 1 if is_guest else 0))
            
            return user_id
        except Exception as e:
            print(f"创建用户失败: {e}")
            return None
    
    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户数据字典或None
        """
        row = self.db.fetchone(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        
        if row:
            return dict(row)
        return None
    
    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据用户ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户数据字典或None
        """
        row = self.db.fetchone(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
        
        if row:
            return dict(row)
        return None
    
    def verify_password(self, username: str, password: str) -> Optional[str]:
        """验证密码
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            用户ID（验证成功）或None（验证失败）
        """
        user = self.get_by_username(username)
        if not user:
            return None
        
        password_hash = self.hash_password(password)
        if user['password_hash'] == password_hash:
            self.update_last_login(user['user_id'])
            return user['user_id']
        
        return None
    
    def update_last_login(self, user_id: str) -> bool:
        """更新最后登录时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否更新成功
        """
        try:
            self.db.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
            return True
        except Exception as e:
            print(f"更新登录时间失败: {e}")
            return False
