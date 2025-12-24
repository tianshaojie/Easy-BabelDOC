from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Dict, List, Optional
import uuid
import asyncio
import json
from datetime import datetime

from models.schemas import TranslationRequest

router = APIRouter(prefix="/api", tags=["translation"])

active_translations: Dict[str, Dict] = {}
connected_clients: Dict[str, WebSocket] = {}

@router.post("/translate")
async def start_translation(request: TranslationRequest, authorization: Optional[str] = Header(None)):
    """开始翻译任务"""
    from config.settings import UPLOADS_DIR, OUTPUTS_DIR, GLOSSARIES_DIR, SENSITIVE_CONFIG_KEYS
    from utils.history import add_to_history
    from api.auth import get_user_id_from_token
    
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="未提供有效的认证令牌")
    
    try:
        from babeldoc.format.pdf.translation_config import TranslationConfig
        from babeldoc.translator.translator import OpenAITranslator
        from babeldoc.docvision.doclayout import DocLayoutModel
        from babeldoc.glossary import Glossary
    except ImportError:
        raise HTTPException(status_code=500, detail="BabelDOC未安装")
    
    task_id = str(uuid.uuid4())
    
    file_path = UPLOADS_DIR / f"{request.file_id}.pdf"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        translator = OpenAITranslator(
            lang_in=request.lang_in,
            lang_out=request.lang_out,
            model=request.model,
            api_key=request.api_key,
            base_url=request.base_url
        )
        
        doc_layout_model = DocLayoutModel.load_onnx()
        
        glossaries = []
        for glossary_id in request.glossary_ids:
            glossary_path = GLOSSARIES_DIR / f"{glossary_id}.csv"
            if glossary_path.exists():
                glossary = Glossary.from_csv(glossary_path, request.lang_out)
                glossaries.append(glossary)
        
        config = TranslationConfig(
            translator=translator,
            input_file=str(file_path),
            lang_in=request.lang_in,
            lang_out=request.lang_out,
            doc_layout_model=doc_layout_model,
            pages=request.pages,
            output_dir=str(OUTPUTS_DIR / task_id),
            debug=request.debug,
            no_dual=request.no_dual,
            no_mono=request.no_mono,
            qps=request.qps,
            glossaries=glossaries
        )
        
        request_config = request.model_dump(exclude=SENSITIVE_CONFIG_KEYS)
        
        task_data = {
            "task_id": task_id,
            "user_id": user_id,
            "status": "running",
            "filename": f"{request.file_id}.pdf",
            "source_lang": request.lang_in,
            "target_lang": request.lang_out,
            "model": request.model,
            "start_time": datetime.now().isoformat(),
            "progress": 0,
            "stage": "初始化",
            "config": request_config
        }
        
        active_translations[task_id] = task_data
        add_to_history(task_data)
        
        asyncio.create_task(run_translation(task_id, config))
        
        return {"task_id": task_id, "status": "started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译启动失败: {str(e)}")

async def run_translation(task_id: str, config):
    """运行翻译任务"""
    from utils.history import add_to_history
    
    try:
        import babeldoc.format.pdf.high_level as high_level
    except ImportError:
        return
    
    try:
        async for event in high_level.async_translate(config):
            if task_id in active_translations:
                if event["type"] == "progress_update":
                    active_translations[task_id].update({
                        "progress": event.get("overall_progress", 0),
                        "stage": event.get("stage", "处理中"),
                        "message": event.get("message", "")
                    })
                    add_to_history(active_translations[task_id])
                elif event["type"] == "finish":
                    result = event["translate_result"]
                    mono_path = getattr(result, "mono_pdf_path", None)
                    dual_path = getattr(result, "dual_pdf_path", None)
                    
                    active_translations[task_id].update({
                        "status": "completed",
                        "progress": 100,
                        "stage": "完成",
                        "result": {
                            "mono_pdf_path": str(mono_path) if mono_path else None,
                            "dual_pdf_path": str(dual_path) if dual_path else None,
                            "total_seconds": getattr(result, "total_seconds", 0),
                            "peak_memory_usage": getattr(result, "peak_memory_usage", 0)
                        },
                        "end_time": datetime.now().isoformat()
                    })
                    add_to_history(active_translations[task_id])
                elif event["type"] == "error":
                    active_translations[task_id].update({
                        "status": "error",
                        "error": event.get("error", "未知错误"),
                        "end_time": datetime.now().isoformat()
                    })
                    add_to_history(active_translations[task_id])
                
                if task_id in connected_clients:
                    try:
                        await connected_clients[task_id].send_text(json.dumps(event))
                    except:
                        pass
                        
    except Exception as e:
        if task_id in active_translations:
            active_translations[task_id].update({
                "status": "error",
                "error": str(e),
                "end_time": datetime.now().isoformat()
            })
            add_to_history(active_translations[task_id])

@router.get("/translation/{task_id}/status")
async def get_translation_status(task_id: str):
    """获取翻译任务状态"""
    from utils.history import get_task
    
    task = get_task(task_id, active_translations)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task

@router.websocket("/translation/{task_id}/ws")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket连接用于实时进度更新"""
    await websocket.accept()
    connected_clients[task_id] = websocket
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if task_id in connected_clients:
            del connected_clients[task_id]

@router.get("/translation/{task_id}/download/{file_type}")
async def download_result(task_id: str, file_type: str):
    """下载翻译结果文件"""
    from utils.history import get_task
    
    task = get_task(task_id, active_translations)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="翻译未完成")
    
    result = task.get("result", {})
    
    if file_type == "mono":
        file_path = result.get("mono_pdf_path")
    elif file_type == "dual":
        file_path = result.get("dual_pdf_path")
    else:
        raise HTTPException(status_code=400, detail="无效的文件类型")
    
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=file_path,
        filename=f"{task_id}_{file_type}.pdf",
        media_type="application/pdf"
    )

@router.get("/translations")
async def list_translations(authorization: Optional[str] = Header(None)):
    """获取翻译历史"""
    from utils.history import load_history
    from api.auth import get_user_id_from_token
    
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="未提供有效的认证令牌")
    
    history = load_history(user_id=user_id)
    
    for task in history:
        task_id = task.get('task_id')
        result = task.get('result', {})
        
        file_status = {
            'mono_exists': False,
            'dual_exists': False,
            'mono_size': 0,
            'dual_size': 0
        }
        
        if task.get('status') == 'completed' and result:
            mono_path = result.get('mono_pdf_path')
            dual_path = result.get('dual_pdf_path')
            
            if mono_path and Path(mono_path).exists():
                file_status['mono_exists'] = True
                file_status['mono_size'] = Path(mono_path).stat().st_size
            
            if dual_path and Path(dual_path).exists():
                file_status['dual_exists'] = True
                file_status['dual_size'] = Path(dual_path).stat().st_size
        
        task['file_status'] = file_status
    
    return sorted(history, key=lambda x: x.get('start_time', ''), reverse=True)

@router.delete("/translation/{task_id}")
async def delete_translation(task_id: str):
    """删除翻译记录"""
    from utils.history import delete_task
    
    success = delete_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="翻译记录不存在")
    
    if task_id in active_translations:
        del active_translations[task_id]
    
    return {"message": "翻译记录已删除"}

@router.delete("/translations")
async def delete_multiple_translations(task_ids: List[str]):
    """批量删除翻译记录"""
    from utils.history import delete_task
    
    deleted_count = 0
    for task_id in task_ids:
        if delete_task(task_id):
            deleted_count += 1
            if task_id in active_translations:
                del active_translations[task_id]
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="没有找到要删除的翻译记录")
    
    return {"message": f"已删除 {deleted_count} 条翻译记录"}
