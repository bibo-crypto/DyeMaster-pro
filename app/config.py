"""
إعدادات التطبيق
"""
import os
from pathlib import Path

# إصدار التطبيق
APP_VERSION = "1.0.0"

# المسارات الأساسية
USER_DATA_DIR = os.path.join(str(Path.home()), ".colorchemsystem")
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
