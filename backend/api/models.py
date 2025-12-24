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
        "is_guest": bool(user['is_guest'])
    }

@router.get("/models", response_model=List[ModelInfo])
async def get_models(current_user: dict = Depends(get_current_user)):
    """获取当前用户的所有模型配置"""
    user_id = current_user["user_id"]
    
    rows = db.fetchall(
        "SELECT * FROM models WHERE user_id = ? ORDER BY is_default DESC, created_at DESC",
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
            created_at=row["created_at"]
        )
        for row in rows
    ]

@router.post("/models", response_model=ModelInfo)
async def create_model(model_data: ModelCreate, current_user: dict = Depends(get_current_user)):
    """创建新的模型配置"""
    user_id = current_user["user_id"]
    
    if model_data.is_default:
        db.execute(
            "UPDATE models SET is_default = 0 WHERE user_id = ?",
            (user_id,)
        )
    
    cursor = db.execute(
        """
        INSERT INTO models (user_id, base_url, api_key, model, is_default)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, model_data.base_url, model_data.api_key, model_data.model, int(model_data.is_default))
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
        db.execute(
            "UPDATE models SET is_default = 0 WHERE user_id = ?",
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
        created_at=row["created_at"]
    )

@router.delete("/models/{model_id}")
async def delete_model(model_id: int, current_user: dict = Depends(get_current_user)):
    """删除模型配置"""
    user_id = current_user["user_id"]
    
    existing = db.fetchone(
        "SELECT * FROM models WHERE id = ? AND user_id = ?",
        (model_id, user_id)
    )
    
    if not existing:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
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
    
    db.execute(
        "UPDATE models SET is_default = 0 WHERE user_id = ?",
        (user_id,)
    )
    
    db.execute(
        "UPDATE models SET is_default = 1 WHERE id = ? AND user_id = ?",
        (model_id, user_id)
    )
    
    return {"message": "默认模型已设置"}
