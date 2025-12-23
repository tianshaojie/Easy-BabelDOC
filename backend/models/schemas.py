from pydantic import BaseModel
from typing import List, Optional

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

class CleanupRequest(BaseModel):
    delete_orphan_files: bool = False
    delete_orphan_records: bool = False
