from fastapi import APIRouter

def register_routes(app):
    """注册所有API路由到FastAPI应用"""
    from . import health, upload, translation, glossary, files, auth, models
    
    # 默认使用 /t 前缀，与 vite.config.ts 中的 base 保持一致
    import os
    global_prefix = os.getenv("EASY_BABELDOC_PREFIX", "/t").rstrip("/")
    
    app.include_router(health.router, prefix=global_prefix)
    app.include_router(upload.router, prefix=global_prefix)
    app.include_router(translation.router, prefix=global_prefix)
    app.include_router(glossary.router, prefix=global_prefix)
    app.include_router(files.router, prefix=global_prefix)
    app.include_router(auth.router, prefix=global_prefix)
    app.include_router(models.router, prefix=global_prefix)
