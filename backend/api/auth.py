from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import uuid

from models.schemas import LoginRequest, LoginResponse, UserInfo

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """用户登录"""
    from db import Database, User
    from config.settings import DB_FILE
    
    db = Database(DB_FILE)
    user_model = User(db)
    
    user_id = user_model.verify_password(request.username, request.password)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    user = user_model.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return LoginResponse(
        user_id=user['user_id'],
        username=user['username'],
        is_guest=bool(user['is_guest']),
        token=user['user_id']
    )

@router.post("/guest", response_model=LoginResponse)
async def create_guest():
    """创建游客账号"""
    from db import Database, User
    from config.settings import DB_FILE
    import logging
    
    logger = logging.getLogger("easy_babeldoc.auth")
    
    try:
        db = Database(DB_FILE)
        user_model = User(db)
        
        guest_id = str(uuid.uuid4())
        username = f"guest_{guest_id[:8]}"
        password = str(uuid.uuid4())
        
        logger.info(f"Creating guest user: {username}")
        
        user_id = user_model.create(username, password, is_guest=True)
        
        if not user_id:
            logger.error("Failed to create guest user in database")
            raise HTTPException(status_code=500, detail="创建游客账号失败")
        
        logger.info(f"Guest user created successfully: {user_id}")
        
        return LoginResponse(
            user_id=user_id,
            username=username,
            is_guest=True,
            token=user_id
        )
    except Exception as e:
        logger.error(f"Error creating guest user: {e}")
        raise HTTPException(status_code=500, detail=f"创建游客账号失败: {str(e)}")

@router.get("/me", response_model=UserInfo)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """获取当前用户信息"""
    from db import Database, User
    from config.settings import DB_FILE
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供用户ID")
    
    user_id = authorization.replace("Bearer ", "")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的用户ID")
    
    db = Database(DB_FILE)
    user_model = User(db)
    user = user_model.get_by_id(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UserInfo(
        user_id=user['user_id'],
        username=user['username'],
        email=user.get('email'),
        is_guest=bool(user['is_guest'])
    )

@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """用户登出"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供用户ID")
    
    return {"message": "登出成功"}

def get_user_id_from_token(user_id_header: Optional[str]) -> Optional[str]:
    """从请求头获取用户ID"""
    if not user_id_header:
        return None
    
    if user_id_header.startswith("Bearer "):
        user_id_header = user_id_header.replace("Bearer ", "")
    
    return user_id_header
