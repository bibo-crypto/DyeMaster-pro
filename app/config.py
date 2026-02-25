"""
إعدادات التطبيق
"""
import os
import sys
from pathlib import Path

# إصدار التطبيق
def _resolve_version_file_path():
    """Return version.txt path near executable (frozen) or project root (dev)."""
    if getattr(sys, "frozen", False):
        # First check _MEIPASS (bundled files location)
        if hasattr(sys, "_MEIPASS"):
            meipass_path = os.path.join(sys._MEIPASS, "version.txt")
            if os.path.exists(meipass_path):
                return meipass_path
        # Fallback to directory next to executable
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "version.txt")


def _resolve_app_version(default="1.0.0"):
    """Read app version from version.txt if present, fallback to default."""
    version_file = _resolve_version_file_path()
    try:
        if os.path.exists(version_file):
            with open(version_file, "r", encoding="utf-8") as f:
                version = f.read().strip()
                if version:
                    return version
    except Exception:
        pass
    return default


APP_VERSION = _resolve_app_version()

# المسارات الأساسية
# Use LOCALAPPDATA on Windows to avoid permission issues on home-root folders.
_base_data_dir = os.environ.get("LOCALAPPDATA", str(Path.home()))
USER_DATA_DIR = os.path.join(_base_data_dir, "ColorChemSystem")
DATA_DIR = os.path.join(USER_DATA_DIR, "data")
EXPORT_DIR = os.path.join(USER_DATA_DIR, "exports")
BACKUP_DIR = os.path.join(USER_DATA_DIR, "backups")
LOG_DIR = os.path.join(USER_DATA_DIR, "logs")

# مسار قاعدة البيانات
DATABASE_FILE = os.path.join(DATA_DIR, "colorchemsystem.db")

# أنواع الصباغة
DYE_TYPES = [
    "Indanthren IN",
    "Indanthren IN SP",
    "Indanthren IW",
    "Indanthren RS",
    "Indanthren Black",
    "Indanthren Rosa R",
    "Indanthren RRN",
    "Reattivi Caldi",
    "Reattivi Freddi",
    "Reattivi Oltri",
]

# إعدادات PDF
PDF_SETTINGS = {
    "page_size": "A4",
    "margin": 20,
    "title_font_size": 16,
    "subtitle_font_size": 12,
    "text_font_size": 10,
    "logo_path": None
}

# إعدادات الواجهة
GUI_SETTINGS = {
    "window_title": "ColorChem System",
    "window_size": "1200x700",  # الحجم الذي تريده
    "theme": "clam",
    "font_family": "Arial",
    "font_size": 10
}

# Chemical codes mapping
CHEMICAL_CODES = {
    '31180': 'IDROSOLFITO',
    '31160': 'GLUCOSIO',
    '31310': 'SODA CAUSTICA',
    '31330': 'SODIO CARBONATO',
    '31360': 'SOLFATO SODICO'
}
