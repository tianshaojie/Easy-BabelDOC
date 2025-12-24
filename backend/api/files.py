from fastapi import APIRouter, HTTPException, Header
from pathlib import Path
from typing import Optional

from models.schemas import CleanupRequest

router = APIRouter(prefix="/api", tags=["files"])

@router.post("/files/cleanup")
async def cleanup_files(request: CleanupRequest, authorization: Optional[str] = Header(None)):
    """清理孤儿文件和记录"""
    from utils.history import load_history, save_history
    from config.settings import OUTPUTS_DIR
    from api.auth import get_user_id_from_token
    
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="未提供有效的认证令牌")
    
    print(f"\n=== 开始文件清理 ===")
    print(f"delete_orphan_files: {request.delete_orphan_files}")
    print(f"delete_orphan_records: {request.delete_orphan_records}")
    
    history = load_history(user_id=user_id)
    print(f"历史记录数量: {len(history)}")
    
    cleanup_result = {
        "orphan_files": [],
        "orphan_records": [],
        "deleted_files": 0,
        "deleted_records": 0,
        "errors": [],
        "warnings": []
    }
    
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
    
    existing_files = set()
    print(f"OUTPUTS_DIR: {OUTPUTS_DIR}")
    print(f"OUTPUTS_DIR存在: {OUTPUTS_DIR.exists()}")
    
    if OUTPUTS_DIR.exists():
        for file_path in OUTPUTS_DIR.rglob("*.pdf"):
            existing_files.add(file_path)
            print(f"  发现文件: {file_path}")
    
    print(f"实际存在的文件数量: {len(existing_files)}")
    
    orphan_files = existing_files - history_files
    cleanup_result["orphan_files"] = [str(f) for f in orphan_files]
    
    print(f"孤儿文件数量: {len(orphan_files)}")
    for f in orphan_files:
        print(f"  孤儿文件: {f}")
    
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

@router.get("/files/stats")
async def get_file_stats(authorization: Optional[str] = Header(None)):
    """获取文件存储统计信息"""
    from utils.history import load_history
    from api.auth import get_user_id_from_token
    
    user_id = get_user_id_from_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="未提供有效的认证令牌")
    
    stats = {
        "total_files": 0,
        "total_size": 0,
        "by_status": {
            "completed": {"count": 0, "size": 0},
            "running": {"count": 0, "size": 0},
            "error": {"count": 0, "size": 0}
        }
    }
    
    history = load_history(user_id=user_id)
    
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
