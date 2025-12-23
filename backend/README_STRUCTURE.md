# Backend 项目结构说明

## 目录结构

```
backend/
├── api/                    # API路由模块
│   ├── __init__.py        # 路由注册入口
│   ├── health.py          # 健康检查和基础API
│   ├── upload.py          # 文件上传
│   ├── translation.py     # 翻译任务管理
│   ├── glossary.py        # 术语表管理
│   └── files.py           # 文件管理和清理
│
├── config/                 # 配置模块
│   ├── __init__.py
│   └── settings.py        # 全局配置、路径、常量
│
├── models/                 # 数据模型
│   ├── __init__.py
│   └── schemas.py         # Pydantic数据模型定义
│
├── utils/                  # 工具函数
│   ├── __init__.py
│   ├── history.py         # 历史记录管理
│   └── network.py         # 网络工具（端口检测等）
│
├── main.py                # 主入口文件（157行）
├── main_old.py            # 重构前备份（1001行）
├── test_imports.py        # 模块导入测试
├── requirements.txt       # Python依赖
└── REFACTORING.md         # 重构文档
```

## 模块说明

### API模块 (`api/`)

所有HTTP端点按功能分组：

- **health.py**: 系统健康检查
- **upload.py**: PDF文件上传
- **translation.py**: 翻译任务的创建、查询、下载、删除
- **glossary.py**: 术语表的上传、查询、删除
- **files.py**: 文件清理和统计

### 配置模块 (`config/`)

- **settings.py**: 
  - 目录路径配置（DATA_DIR, UPLOADS_DIR, OUTPUTS_DIR等）
  - 前端静态文件路径
  - 敏感配置键定义

### 数据模型 (`models/`)

- **schemas.py**: 所有Pydantic模型
  - TranslationRequest: 翻译请求参数
  - TranslatorConfig: 翻译器配置
  - GlossaryInfo: 术语表信息
  - CleanupRequest: 清理请求参数

### 工具模块 (`utils/`)

- **history.py**: 翻译历史记录的增删改查
- **network.py**: 网络相关工具函数（端口检测、主机配置）

## 导入规范

所有模块使用绝对导入：

```python
# 正确 ✅
from config.settings import DATA_DIR
from utils.history import load_history
from models.schemas import TranslationRequest

# 错误 ❌
from ..config.settings import DATA_DIR
from .history import load_history
```

## 运行方式

```bash
# 激活conda环境
conda activate babeldoc

# 启动服务器
python main.py --port 58273

# 测试模块导入
python test_imports.py
```

## 添加新功能

### 添加新的API端点

1. 在 `api/` 目录下创建新文件或在现有文件中添加
2. 定义路由和处理函数
3. 在 `api/__init__.py` 中注册路由

示例：
```python
# api/new_feature.py
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["new_feature"])

@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "Hello"}

# api/__init__.py
def register_routes(app):
    from . import health, upload, translation, glossary, files, new_feature
    
    app.include_router(health.router)
    app.include_router(upload.router)
    app.include_router(translation.router)
    app.include_router(glossary.router)
    app.include_router(files.router)
    app.include_router(new_feature.router)  # 新增
```

### 添加新的数据模型

在 `models/schemas.py` 中添加：

```python
class NewModel(BaseModel):
    field1: str
    field2: int
```

### 添加新的工具函数

在 `utils/` 目录下创建新文件或在现有文件中添加：

```python
# utils/new_utils.py
def new_utility_function():
    pass
```

## 重构优势

1. **模块化**: 每个文件职责单一，易于理解和维护
2. **可测试**: 可以单独测试每个模块
3. **可扩展**: 添加新功能不会影响现有代码
4. **代码复用**: 工具函数和配置可以被多个模块共享
5. **团队协作**: 不同开发者可以同时修改不同模块

## 注意事项

1. 必须在 `backend/` 目录下运行，确保导入路径正确
2. 修改配置时只需修改 `config/settings.py`
3. 所有API端点保持向后兼容
4. 原始代码已备份为 `main_old.py`
