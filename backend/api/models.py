from fastapi import APIRouter, HTTPException, Header, Depends
from typing import List, Optional
from models.schemas import ModelCreate, ModelUpdate, ModelInfo
from db.database import Database
from config.settings import DB_FILE
from db import User

router = APIRouter(prefix="/api", tags=["models"])
db = Database(DB_FILE)

async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """获取当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供用户ID")
    
    user_id = authorization.replace("Bearer ", "")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的用户ID")
    
    user_model = User(db)
    user = user_model.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return {
        "user_id": user['user_id'],
        "username": user['username'],
        "is_guest": bool(user['is_guest']),
        "role": user.get('role', 'user')
    }

@router.get("/models/default", response_model=ModelInfo)
async def get_default_model(current_user: dict = Depends(get_current_user)):
    """获取默认模型配置
    
    优先级:
    1. 用户自定义模型中的默认模型
    2. 系统内置模型中的默认模型
    3. 用户的第一个可用模型
    """
    user_id = current_user["user_id"]
    user_role = current_user.get("role", "user")
    
    # 1. 优先查找用户自定义的默认模型
    row = db.fetchone(
        "SELECT * FROM models WHERE user_id = ? AND is_system = 0 AND is_default = 1 ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    
    # 2. 如果没有用户自定义的默认模型,且不是游客,查找系统内置的默认模型
    if not row and user_role != "guest":
        row = db.fetchone(
            "SELECT * FROM models WHERE is_system = 1 AND is_default = 1 ORDER BY created_at DESC LIMIT 1"
        )
    
    # 3. 如果还没有,返回用户的第一个可用模型
    if not row:
        if user_role == "guest":
            row = db.fetchone(
                "SELECT * FROM models WHERE user_id = ? AND is_system = 0 ORDER BY created_at DESC LIMIT 1",
                (user_id,)
            )
        else:
            row = db.fetchone(
                "SELECT * FROM models WHERE user_id = ? OR is_system = 1 ORDER BY is_system DESC, created_at DESC LIMIT 1",
                (user_id,)
            )
    
    if not row:
        raise HTTPException(status_code=404, detail="没有可用的模型配置")
    
    return ModelInfo(
        id=row["id"],
        user_id=row["user_id"],
        base_url=row["base_url"],
        api_key=row["api_key"],
        model=row["model"],
        is_default=bool(row["is_default"]),
        is_system=bool(row["is_system"]) if "is_system" in row.keys() else False,
        created_at=row["created_at"]
    )

@router.get("/models", response_model=List[ModelInfo])
async def get_models(current_user: dict = Depends(get_current_user)):
    """获取当前用户的所有模型配置"""
    user_id = current_user["user_id"]
    user_role = current_user.get("role", "user")
    
    if user_role == "guest":
        rows = db.fetchall(
            "SELECT * FROM models WHERE user_id = ? AND is_system = 0 ORDER BY is_default DESC, created_at DESC",
            (user_id,)
        )
    else:
        rows = db.fetchall(
            "SELECT * FROM models WHERE user_id = ? OR is_system = 1 ORDER BY is_system DESC, is_default DESC, created_at DESC",
            (user_id,)
        )
    
    return [
        ModelInfo(
            id=row["id"],
            user_id=row["user_id"],
            base_url=row["base_url"],
            api_key=row["api_key"],
            model=row["model"],
            is_default=bool(row["is_default"]),
            is_system=bool(row["is_system"]) if "is_system" in row.keys() else False,
            created_at=row["created_at"]
        )
        for row in rows
    ]

@router.post("/models", response_model=ModelInfo)
async def create_model(model_data: ModelCreate, current_user: dict = Depends(get_current_user)):
    """创建新的模型配置
    
    admin角色添加的模型自动标记为系统内置模型
    """
    user_id = current_user["user_id"]
    user_role = current_user.get("role", "user")
    
    # admin角色添加的模型自动标记为系统内置模型
    is_system = True if user_role == "admin" else False
    
    if model_data.is_default:
        # 只清除用户自己的模型的默认标记,不影响系统内置模型
        db.execute(
            "UPDATE models SET is_default = 0 WHERE user_id = ? AND is_system = 0",
            (user_id,)
        )
    
    cursor = db.execute(
        """
        INSERT INTO models (user_id, base_url, api_key, model, is_default, is_system)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, model_data.base_url, model_data.api_key, model_data.model, int(model_data.is_default), int(is_system))
    )
    
    model_id = cursor.lastrowid
    
    row = db.fetchone("SELECT * FROM models WHERE id = ?", (model_id,))
    
    return ModelInfo(
        id=row["id"],
        user_id=row["user_id"],
        base_url=row["base_url"],
        api_key=row["api_key"],
        model=row["model"],
        is_default=bool(row["is_default"]),
        is_system=bool(row["is_system"]) if "is_system" in row.keys() else False,
        created_at=row["created_at"]
    )

@router.put("/models/{model_id}", response_model=ModelInfo)
async def update_model(model_id: int, model_data: ModelUpdate, current_user: dict = Depends(get_current_user)):
    """更新模型配置"""
    user_id = current_user["user_id"]
    
    existing = db.fetchone(
        "SELECT * FROM models WHERE id = ? AND user_id = ?",
        (model_id, user_id)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    if model_data.is_default:
        # 只清除用户自己的模型的默认标记,不影响系统内置模型
        db.execute(
            "UPDATE models SET is_default = 0 WHERE user_id = ? AND is_system = 0",
            (user_id,)
        )
    
    update_fields = []
    params = []
    
    if model_data.base_url is not None:
        update_fields.append("base_url = ?")
        params.append(model_data.base_url)
    
    if model_data.api_key is not None:
        update_fields.append("api_key = ?")
        params.append(model_data.api_key)
    
    if model_data.model is not None:
        update_fields.append("model = ?")
        params.append(model_data.model)
    
    if model_data.is_default is not None:
        update_fields.append("is_default = ?")
        params.append(int(model_data.is_default))
    
    if model_data.is_system is not None and current_user.get("role") == "admin":
        update_fields.append("is_system = ?")
        params.append(int(model_data.is_system))
    
    if update_fields:
        params.extend([model_id, user_id])
        db.execute(
            f"UPDATE models SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?",
            tuple(params)
        )
    
    row = db.fetchone("SELECT * FROM models WHERE id = ?", (model_id,))
    
    return ModelInfo(
        id=row["id"],
        user_id=row["user_id"],
        base_url=row["base_url"],
        api_key=row["api_key"],
        model=row["model"],
        is_default=bool(row["is_default"]),
        is_system=bool(row["is_system"]) if "is_system" in row.keys() else False,
        created_at=row["created_at"]
    )

@router.delete("/models/{model_id}")
async def delete_model(model_id: int, current_user: dict = Depends(get_current_user)):
    """删除模型配置
    
    admin角色可以删除系统内置模型,普通用户不能删除
    """
    user_id = current_user["user_id"]
    user_role = current_user.get("role", "user")
    
    existing = db.fetchone(
        "SELECT * FROM models WHERE id = ? AND user_id = ?",
        (model_id, user_id)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    # 检查是否为系统内置模型
    is_system = bool(existing["is_system"]) if "is_system" in existing.keys() else False
    
    # 只有admin可以删除系统内置模型,普通用户不能删除
    if is_system and user_role != "admin":
        raise HTTPException(status_code=403, detail="系统内置模型不能删除")
    
    db.execute("DELETE FROM models WHERE id = ? AND user_id = ?", (model_id, user_id))
    
    return {"message": "模型配置已删除"}

@router.put("/models/{model_id}/set-default")
async def set_default_model(model_id: int, current_user: dict = Depends(get_current_user)):
    """设置默认模型"""
    user_id = current_user["user_id"]
    
    existing = db.fetchone(
        "SELECT * FROM models WHERE id = ? AND user_id = ?",
        (model_id, user_id)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    # 只清除用户自己的模型的默认标记,不影响系统内置模型
    db.execute(
        "UPDATE models SET is_default = 0 WHERE user_id = ? AND is_system = 0",
        (user_id,)
    )
    
    db.execute(
        "UPDATE models SET is_default = 1 WHERE id = ? AND user_id = ?",
        (model_id, user_id)
    )
    
    return {"message": "默认模型已设置"}
