from fastapi import APIRouter

def register_routes(app):
    """注册所有API路由到FastAPI应用"""
    from . import health, upload, translation, glossary, files
    
    app.include_router(health.router)
    app.include_router(upload.router)
    app.include_router(translation.router)
    app.include_router(glossary.router)
    app.include_router(files.router)
