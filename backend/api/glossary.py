from fastapi import APIRouter, File, UploadFile, HTTPException
import aiofiles
import uuid
import json
from datetime import datetime

router = APIRouter(prefix="/api", tags=["glossary"])

@router.post("/glossary/upload")
async def upload_glossary(file: UploadFile = File(...), target_lang: str = "zh"):
    """上传术语表文件"""
    from config.settings import GLOSSARIES_DIR
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")
    
    glossary_id = str(uuid.uuid4())
    file_path = GLOSSARIES_DIR / f"{glossary_id}.csv"
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    try:
        content_str = content.decode('utf-8')
        entry_count = len(content_str.strip().split('\n')) - 1
    except:
        entry_count = 0
    
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

@router.get("/glossaries")
async def list_glossaries():
    """获取术语表列表"""
    from config.settings import GLOSSARIES_DIR
    
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

@router.delete("/glossary/{glossary_id}")
async def delete_glossary(glossary_id: str):
    """删除术语表"""
    from config.settings import GLOSSARIES_DIR
    
    csv_path = GLOSSARIES_DIR / f"{glossary_id}.csv"
    json_path = GLOSSARIES_DIR / f"{glossary_id}.json"
    
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="术语表不存在")
    
    csv_path.unlink()
    if json_path.exists():
        json_path.unlink()
    
    return {"message": "术语表已删除"}
