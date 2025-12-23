#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Easy-BabelDOC - 基于BabelDOC API的Web翻译应用
Copyright (C) 2024 lijiapeng365

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

Based on BabelDOC: https://github.com/funstory-ai/BabelDOC
Source code: https://github.com/lijiapeng365/Easy-BabelDOC
"""

import argparse
import errno
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import json
import uuid
import asyncio
import copy
import platform
import socket
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import aiofiles
from datetime import datetime

# 导入BabelDOC相关模块
try:
    import babeldoc.format.pdf.high_level as high_level
    from babeldoc.format.pdf.translation_config import TranslationConfig
    from babeldoc.translator.translator import OpenAITranslator
    from babeldoc.docvision.doclayout import DocLayoutModel
    from babeldoc.glossary import Glossary
except ImportError:
    print("Warning: BabelDOC not installed. Some features will not work.")
    # 创建模拟类用于开发
    class MockTranslationConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class MockTranslator:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class MockDocLayoutModel:
        @staticmethod
        def load_onnx():
            return MockDocLayoutModel()
    
    class MockGlossary:
        @staticmethod
        def from_csv(file_path, target_lang):
            return MockGlossary()
    
    TranslationConfig = MockTranslationConfig
    OpenAITranslator = MockTranslator
    DocLayoutModel = MockDocLayoutModel
    Glossary = MockGlossary
    
    class MockHighLevel:
        @staticmethod
        def init():
            pass
        
        @staticmethod
        def translate(config):
            return {"mono_pdf_path": "mock.pdf", "dual_pdf_path": "mock_dual.pdf"}
        
        @staticmethod
        async def async_translate(config):
            for i in range(101):
                yield {
                    "type": "progress_update",
                    "overall_progress": i,
                    "stage": "翻译中",
                    "message": f"进度 {i}%"
                }
                await asyncio.sleep(0.1)
            yield {
                "type": "finish",
                "translate_result": {
                    "mono_pdf_path": "mock.pdf",
                    "dual_pdf_path": "mock_dual.pdf",
                    "total_seconds": 10.5,
                    "peak_memory_usage": 256
                }
            }
    
    high_level = MockHighLevel()

app = FastAPI(title="BabelDOC API", version="1.0.0")

logger = logging.getLogger("easy_babeldoc")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

def get_env_int(name: str, default: int) -> int:
    """Return integer environment variable value with fallback."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning(
            "Environment variable %s=%r is not a valid integer; falling back to %s",
            name,
            value,
            default,
        )
        return default

def resolve_backend_root() -> Path:
    """Return the directory containing this backend module."""
    return Path(__file__).resolve().parent

def resolve_static_dir() -> Path:
    """Locate the compiled frontend assets directory."""
    candidates = []

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "static" / "dist")

    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(exe_dir / "static" / "dist")

    backend_root = resolve_backend_root()
    candidates.append(backend_root / "static" / "dist")
    candidates.append(Path.cwd() / "backend" / "static" / "dist")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return backend_root / "static" / "dist"

def determine_data_dir() -> Path:
    """Determine a writable directory for runtime data."""
    env_dir = os.environ.get("EASY_BABELDOC_DATA_DIR")
    if env_dir:
        return Path(env_dir).expanduser()

    system_name = platform.system().lower()
    if system_name == "windows":
        base_dir = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
        if base_dir:
            return Path(base_dir) / "Easy-BabelDOC"

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data"

    return Path.home() / ".easy-babeldoc"

def determine_host(cli_host: Optional[str] = None) -> str:
    """Determine which host the server should bind to."""
    if cli_host:
        return cli_host
    env_host = os.environ.get("EASY_BABELDOC_HOST")
    if env_host:
        return env_host
    return "0.0.0.0"

def determine_port(cli_port: Optional[int] = None) -> int:
    """Determine the preferred port for the server."""
    if cli_port is not None:
        return cli_port
    return get_env_int("EASY_BABELDOC_PORT", 58273)

def determine_port_search_limit(cli_limit: Optional[int] = None) -> int:
    """Determine how many additional ports we should probe when encountering conflicts."""
    if cli_limit is not None:
        return max(cli_limit, 0)
    return max(get_env_int("EASY_BABELDOC_PORT_SEARCH_LIMIT", 10), 0)

def can_bind_port(host: str, port: int) -> bool:
    """Check whether the given host/port is currently available for binding."""
    try:
        addr_infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        logger.error("Invalid host %s: %s", host, exc)
        raise SystemExit(1)

    bindable = False
    for family, socktype, proto, _, sockaddr in addr_infos:
        try:
            with socket.socket(family, socktype, proto) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(sockaddr)
                bindable = True
        except OSError as exc:
            if exc.errno == errno.EADDRINUSE:
                return False
            if exc.errno in (errno.EADDRNOTAVAIL, errno.EAFNOSUPPORT):
                continue
            raise

    return bindable

FRONTEND_STATIC_DIR = resolve_static_dir()
FRONTEND_INDEX_FILE = FRONTEND_STATIC_DIR / "index.html"

DATA_DIR = determine_data_dir()
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
GLOSSARIES_DIR = DATA_DIR / "glossaries"
HISTORY_FILE = DATA_DIR / "translation_history.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
for dir_path in [UPLOADS_DIR, OUTPUTS_DIR, GLOSSARIES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

logger.info("Using data directory: %s", DATA_DIR)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Health check endpoint for the packaged application."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "frontend_ready": FRONTEND_STATIC_DIR.exists(),
        "data_dir": str(DATA_DIR),
    }

@app.exception_handler(404)
async def spa_fallback(request: Request, exc: HTTPException):
    """Serve the React SPA for unknown non-API routes."""
    path = request.url.path
    if (
        request.method == "GET"
        and FRONTEND_STATIC_DIR.exists()
        and FRONTEND_INDEX_FILE.exists()
        and not path.startswith(("/api", "/docs", "/redoc", "/openapi"))
        and "." not in Path(path).name
    ):
        return FileResponse(FRONTEND_INDEX_FILE)

    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)

# 数据模型
class TranslationRequest(BaseModel):
    file_id: str
    lang_in: str
    lang_out: str
    model: str = "gpt-4o-mini"
    api_key: str
    base_url: Optional[str] = None
    pages: Optional[str] = None
    qps: Optional[int] = 1
    no_dual: bool = False
    no_mono: bool = False
    debug: bool = False
    glossary_ids: List[str] = []

class TranslatorConfig(BaseModel):
    api_key: str
    model: str = "gpt-4o-mini"
    base_url: Optional[str] = None
    qps: int = 1

class GlossaryInfo(BaseModel):
    id: str
    name: str
    target_lang: str
    created_at: str
    entry_count: int

# 全局变量
active_translations: Dict[str, Dict] = {}
connected_clients: Dict[str, WebSocket] = {}

# 历史记录文件路径
SENSITIVE_CONFIG_KEYS = {"api_key"}

# 加载历史记录
def load_history() -> List[Dict]:
    """从文件加载翻译历史"""
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

# 保存历史记录
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

def save_history(history):
    """保存历史记录到文件"""
    try:
        # 在保存前转换所有Path对象为字符串
        clean_history = convert_paths_to_strings(history)
        print(f"准备保存历史记录，共 {len(clean_history)} 条")
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(clean_history, f, ensure_ascii=False, indent=2)
        print("历史记录保存成功")
    except Exception as e:
        print(f"保存历史记录失败: {e}")
        import traceback
        traceback.print_exc()

def remove_sensitive_config(task: Dict[str, Any]) -> Dict[str, Any]:
    """返回移除敏感配置后的任务副本"""
    sanitized = copy.deepcopy(task)
    config = sanitized.get("config")
    if isinstance(config, dict):
        for key in SENSITIVE_CONFIG_KEYS:
            if key in config:
                config.pop(key, None)
    return sanitized

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """从内存或历史记录获取任务信息"""
    if task_id in active_translations:
        return active_translations[task_id]
    
    history = load_history()
    for task in history:
        if task.get("task_id") == task_id:
            return task
    return None

# 添加历史记录
def add_to_history(task_data: Dict):
    """添加任务到历史记录"""
    sanitized_task = remove_sensitive_config(task_data)
    history = load_history()
    # 检查是否已存在
    for i, item in enumerate(history):
        if item.get('task_id') == sanitized_task.get('task_id'):
            history[i] = sanitized_task
            save_history(history)
            return
    # 新增记录
    history.append(sanitized_task)
    save_history(history)

# 初始化BabelDOC
try:
    high_level.init()
except:
    print("BabelDOC initialization skipped (development mode)")

@app.get("/api")
async def api_root():
    return {"message": "BabelDOC API Server", "version": "1.0.0"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传PDF文件"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    file_id = str(uuid.uuid4())
    file_path = UPLOADS_DIR / f"{file_id}.pdf"
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # 获取文件信息
    file_size = len(content)
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "size": file_size,
        "upload_time": datetime.now().isoformat()
    }

@app.post("/api/translate")
async def start_translation(request: TranslationRequest):
    """开始翻译任务"""
    task_id = str(uuid.uuid4())
    
    # 验证文件存在
    file_path = UPLOADS_DIR / f"{request.file_id}.pdf"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 创建翻译配置
    try:
        translator = OpenAITranslator(
            lang_in=request.lang_in,
            lang_out=request.lang_out,
            model=request.model,
            api_key=request.api_key,
            base_url=request.base_url
        )
        
        doc_layout_model = DocLayoutModel.load_onnx()
        
        # 加载术语表
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
        
        # 记录翻译任务
        task_data = {
            "task_id": task_id,
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
        
        # 启动异步翻译任务
        asyncio.create_task(run_translation(task_id, config))
        
        return {"task_id": task_id, "status": "started"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译启动失败: {str(e)}")

async def run_translation(task_id: str, config):
    """运行翻译任务"""
    try:
        async for event in high_level.async_translate(config):
            # 更新任务状态
            if task_id in active_translations:
                if event["type"] == "progress_update":
                    active_translations[task_id].update({
                        "progress": event.get("overall_progress", 0),
                        "stage": event.get("stage", "处理中"),
                        "message": event.get("message", "")
                    })
                    # 更新历史记录
                    add_to_history(active_translations[task_id])
                elif event["type"] == "finish":
                    result = event["translate_result"]
                    # 处理TranslateResult对象，使用属性访问而不是字典方法
                    # 确保路径转换为字符串以避免JSON序列化错误
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
                    # 更新历史记录
                    add_to_history(active_translations[task_id])
                elif event["type"] == "error":
                    active_translations[task_id].update({
                        "status": "error",
                        "error": event.get("error", "未知错误"),
                        "end_time": datetime.now().isoformat()
                    })
                    # 更新历史记录
                    add_to_history(active_translations[task_id])
                
                # 通知WebSocket客户端
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
            # 更新历史记录
            add_to_history(active_translations[task_id])

@app.get("/api/translation/{task_id}/status")
async def get_translation_status(task_id: str):
    """获取翻译任务状态"""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return task

@app.websocket("/api/translation/{task_id}/ws")
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

@app.get("/api/translation/{task_id}/download/{file_type}")
async def download_result(task_id: str, file_type: str):
    """下载翻译结果文件"""
    task = get_task(task_id)
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

@app.post("/api/glossary/upload")
async def upload_glossary(file: UploadFile = File(...), target_lang: str = "zh"):
    """上传术语表文件"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")
    
    glossary_id = str(uuid.uuid4())
    file_path = GLOSSARIES_DIR / f"{glossary_id}.csv"
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # 计算条目数量
    try:
        content_str = content.decode('utf-8')
        entry_count = len(content_str.strip().split('\n')) - 1  # 减去标题行
    except:
        entry_count = 0
    
    # 保存术语表信息
    glossary_info = {
        "id": glossary_id,
        "name": file.filename,
        "target_lang": target_lang,
        "created_at": datetime.now().isoformat(),
        "entry_count": entry_count
    }
    
    info_path = GLOSSARIES_DIR / f"{glossary_id}.json"
    async with aiofiles.open(info_path, 'w', encoding='utf-8') as f:
        await f.write(json.dumps(glossary_info, ensure_ascii=False, indent=2))
    
    return glossary_info

@app.get("/api/glossaries")
async def list_glossaries():
    """获取术语表列表"""
    glossaries = []
    
    for info_file in GLOSSARIES_DIR.glob("*.json"):
        try:
            async with aiofiles.open(info_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                glossary_info = json.loads(content)
                glossaries.append(glossary_info)
        except:
            continue
    
    return sorted(glossaries, key=lambda x: x["created_at"], reverse=True)

@app.delete("/api/glossary/{glossary_id}")
async def delete_glossary(glossary_id: str):
    """删除术语表"""
    csv_path = GLOSSARIES_DIR / f"{glossary_id}.csv"
    json_path = GLOSSARIES_DIR / f"{glossary_id}.json"
    
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="术语表不存在")
    
    csv_path.unlink()
    if json_path.exists():
        json_path.unlink()
    
    return {"message": "术语表已删除"}

@app.get("/api/translations")
async def list_translations():
    """获取翻译历史"""
    history = load_history()
    
    # 检查每个任务的文件状态
    for task in history:
        task_id = task.get('task_id')
        result = task.get('result', {})
        
        # 检查文件是否存在
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
    
    # 按时间倒序排列
    return sorted(history, key=lambda x: x.get('start_time', ''), reverse=True)

@app.delete("/api/translation/{task_id}")
async def delete_translation(task_id: str):
    """删除翻译记录"""
    history = load_history()
    original_length = len(history)
    
    # 过滤掉指定的任务
    history = [item for item in history if item.get('task_id') != task_id]
    
    if len(history) == original_length:
        raise HTTPException(status_code=404, detail="翻译记录不存在")
    
    save_history(history)
    
    # 同时从内存中删除
    if task_id in active_translations:
        del active_translations[task_id]
    
    return {"message": "翻译记录已删除"}

@app.delete("/api/translations")
async def delete_multiple_translations(task_ids: List[str]):
    """批量删除翻译记录"""
    history = load_history()
    original_length = len(history)
    
    # 过滤掉指定的任务
    history = [item for item in history if item.get('task_id') not in task_ids]
    
    deleted_count = original_length - len(history)
    
    if deleted_count == 0:
        raise HTTPException(status_code=404, detail="没有找到要删除的翻译记录")
    
    save_history(history)
    
    # 同时从内存中删除
    for task_id in task_ids:
        if task_id in active_translations:
            del active_translations[task_id]
    
    return {"message": f"已删除 {deleted_count} 条翻译记录"}

class CleanupRequest(BaseModel):
    delete_orphan_files: bool = False
    delete_orphan_records: bool = False

@app.post("/api/files/cleanup")
async def cleanup_files(request: CleanupRequest):
    """清理孤儿文件和记录"""
    print(f"\n=== 开始文件清理 ===")
    print(f"delete_orphan_files: {request.delete_orphan_files}")
    print(f"delete_orphan_records: {request.delete_orphan_records}")
    
    history = load_history()
    print(f"历史记录数量: {len(history)}")
    
    cleanup_result = {
        "orphan_files": [],
        "orphan_records": [],
        "deleted_files": 0,
        "deleted_records": 0,
        "errors": [],
        "warnings": []
    }
    
    # 获取所有历史记录中的文件路径
    history_files = set()
    for task in history:
        result = task.get('result', {})
        if result:
            mono_path = result.get('mono_pdf_path')
            dual_path = result.get('dual_pdf_path')
            if mono_path:
                history_files.add(Path(str(mono_path)))
            if dual_path:
                history_files.add(Path(str(dual_path)))
    
    print(f"历史记录中的文件数量: {len(history_files)}")
    for f in history_files:
        print(f"  历史文件: {f}")
    
    # 扫描outputs目录中的所有文件
    existing_files = set()
    print(f"OUTPUTS_DIR: {OUTPUTS_DIR}")
    print(f"OUTPUTS_DIR存在: {OUTPUTS_DIR.exists()}")
    
    if OUTPUTS_DIR.exists():
        for file_path in OUTPUTS_DIR.rglob("*.pdf"):
            existing_files.add(file_path)
            print(f"  发现文件: {file_path}")
    
    print(f"实际存在的文件数量: {len(existing_files)}")
    
    # 找出孤儿文件（存在于文件系统但不在历史记录中）
    orphan_files = existing_files - history_files
    cleanup_result["orphan_files"] = [str(f) for f in orphan_files]
    
    print(f"孤儿文件数量: {len(orphan_files)}")
    for f in orphan_files:
        print(f"  孤儿文件: {f}")
    
    # 找出孤儿记录（历史记录中存在但文件不存在）
    orphan_records = []
    for task in history:
        if task.get('status') == 'completed':
            result = task.get('result', {})
            if result:
                mono_path = result.get('mono_pdf_path')
                dual_path = result.get('dual_pdf_path')
                
                mono_missing = mono_path and not Path(mono_path).exists()
                dual_missing = dual_path and not Path(dual_path).exists()
                
                if mono_missing or dual_missing:
                    orphan_records.append({
                        'task_id': task.get('task_id'),
                        'filename': task.get('filename'),
                        'mono_missing': mono_missing,
                        'dual_missing': dual_missing
                    })
    
    cleanup_result["orphan_records"] = orphan_records
    print(f"孤儿记录数量: {len(orphan_records)}")
    
    # 执行清理操作
    if request.delete_orphan_files:
        print(f"\n开始删除 {len(orphan_files)} 个孤儿文件...")
        for file_path in orphan_files:
            try:
                print(f"正在删除文件: {file_path}")
                print(f"文件存在: {file_path.exists()}")
                print(f"文件大小: {file_path.stat().st_size if file_path.exists() else 'N/A'}")
                
                file_path.unlink()
                cleanup_result["deleted_files"] += 1
                print(f"✓ 成功删除: {file_path}")
            except PermissionError as e:
                error_msg = f"文件被占用无法删除: {file_path.name}"
                print(f"✗ {error_msg}: {e}")
                cleanup_result["errors"].append({
                    "type": "permission_error",
                    "file": str(file_path),
                    "message": error_msg
                })
            except FileNotFoundError as e:
                warning_msg = f"文件已不存在: {file_path.name}"
                print(f"⚠ {warning_msg}: {e}")
                cleanup_result["warnings"].append({
                    "type": "file_not_found",
                    "file": str(file_path),
                    "message": warning_msg
                })
            except Exception as e:
                error_msg = f"删除文件时发生未知错误: {file_path.name}"
                print(f"✗ {error_msg}: {e}")
                cleanup_result["errors"].append({
                    "type": "unknown_error",
                    "file": str(file_path),
                    "message": error_msg,
                    "detail": str(e)
                })
                import traceback
                traceback.print_exc()
    
    if request.delete_orphan_records:
        print(f"\n开始删除 {len(orphan_records)} 个孤儿记录...")
        # 删除有缺失文件的记录
        task_ids_to_delete = [record['task_id'] for record in orphan_records]
        if task_ids_to_delete:
            updated_history = [task for task in history if task.get('task_id') not in task_ids_to_delete]
            save_history(updated_history)
            cleanup_result["deleted_records"] = len(task_ids_to_delete)
            print(f"✓ 成功删除 {len(task_ids_to_delete)} 个记录")
    
    print(f"\n=== 清理完成 ===")
    print(f"删除的文件数: {cleanup_result['deleted_files']}")
    print(f"删除的记录数: {cleanup_result['deleted_records']}")
    
    return cleanup_result

@app.get("/api/files/stats")
async def get_file_stats():
    """获取文件存储统计信息"""
    stats = {
        "total_files": 0,
        "total_size": 0,
        "by_status": {
            "completed": {"count": 0, "size": 0},
            "running": {"count": 0, "size": 0},
            "error": {"count": 0, "size": 0}
        }
    }
    
    history = load_history()
    
    for task in history:
        status = task.get('status', 'unknown')
        if status not in stats["by_status"]:
            stats["by_status"][status] = {"count": 0, "size": 0}
        
        stats["by_status"][status]["count"] += 1
        
        if status == 'completed':
            result = task.get('result', {})
            if result:
                mono_path = result.get('mono_pdf_path')
                dual_path = result.get('dual_pdf_path')
                
                for path in [mono_path, dual_path]:
                    if path and Path(path).exists():
                        file_size = Path(path).stat().st_size
                        stats["total_size"] += file_size
                        stats["by_status"][status]["size"] += file_size
                        stats["total_files"] += 1
    
    return stats

def run_server(host: str, preferred_port: int, port_search_limit: int = 10) -> None:
    """Start uvicorn with automatic fallback when the preferred port is occupied."""
    import uvicorn
    attempted_ports: List[int] = []
    for offset in range(port_search_limit + 1):
        port = preferred_port + offset
        attempted_ports.append(port)
        if not can_bind_port(host, port):
            logger.warning("Port %s is in use. Trying next port...", port)
            continue
        try:
            logger.info("Starting Easy-BabelDOC server on %s:%s", host, port)
            uvicorn.run(app, host=host, port=port)
            return
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise
            logger.warning("Port %s is in use. Trying next port...", port)
            continue

    min_port = attempted_ports[0]
    max_port = attempted_ports[-1]
    logger.error(
        "Unable to find an open port in range %s-%s. "
        "Set EASY_BABELDOC_PORT or use --port to pick a different starting port.",
        min_port,
        max_port,
    )
    raise SystemExit(1)

if FRONTEND_STATIC_DIR.exists():
    logger.info("Serving frontend assets from %s", FRONTEND_STATIC_DIR)
    app.mount("/", StaticFiles(directory=str(FRONTEND_STATIC_DIR), html=True), name="frontend")
else:
    logger.warning(
        "Frontend build not found at %s. Only API routes will be available.",
        FRONTEND_STATIC_DIR,
    )

    @app.get("/", include_in_schema=False)
    async def root_placeholder():
        return {
            "message": "BabelDOC API Server",
            "version": "1.0.0",
            "frontend_ready": False,
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Easy-BabelDOC backend server.")
    parser.add_argument("--host", help="Host/IP to bind (default: EASY_BABELDOC_HOST or 0.0.0.0)")
    parser.add_argument(
        "--port",
        type=int,
        help="Preferred port (default: EASY_BABELDOC_PORT or 8000)",
    )
    parser.add_argument(
        "--port-search-limit",
        type=int,
        help="How many additional ports to probe when the preferred port is occupied "
        "(default: EASY_BABELDOC_PORT_SEARCH_LIMIT or 10).",
    )
    cli_args = parser.parse_args()

    host = determine_host(cli_args.host)
    port = determine_port(cli_args.port)
    port_search_limit = determine_port_search_limit(cli_args.port_search_limit)

    logger.info(
        "Starting Easy-BabelDOC with host=%s port=%s (search limit: %s)",
        host,
        port,
        port_search_limit,
    )

    run_server(host, port, port_search_limit)
