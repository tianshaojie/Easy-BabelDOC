from fastapi import APIRouter, File, UploadFile, HTTPException
import aiofiles
import uuid
from datetime import datetime

router = APIRouter(prefix="/api", tags=["upload"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传PDF文件"""
    from config.settings import UPLOADS_DIR
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    file_id = str(uuid.uuid4())
    file_path = UPLOADS_DIR / f"{file_id}.pdf"
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    file_size = len(content)
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "size": file_size,
        "upload_time": datetime.now().isoformat()
    }
