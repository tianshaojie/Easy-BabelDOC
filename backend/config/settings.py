import os
import platform
import sys
from pathlib import Path

def resolve_backend_root() -> Path:
    """Return the directory containing this backend module."""
    return Path(__file__).resolve().parent.parent

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

SENSITIVE_CONFIG_KEYS = {"api_key"}
