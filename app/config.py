"""
Ø¥Ø¹Ø¯Ø§Ø¯Ø§Øª Ø§Ù„ØªØ·Ø¨ÙŠÙ‚
"""
import os
import sys
from pathlib import Path


# â”€â”€ Version resolution â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ #
def _resolve_version_file_path() -> str:
    """
    Find version.txt regardless of how the app is run:

      onedir frozen  : dist/DyeMasterPro/version.txt  (next to exe)
      onefile frozen : Temp/_MEIxxxxxx/version.txt        (bundled)
                       OR  dist/version.txt  (written by updater)
      dev / source   : project_root/version.txt
    """
    if getattr(sys, "frozen", False):
        # 1. Check next to the executable first (written by updater after update)
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidate = os.path.join(exe_dir, "version.txt")
        if os.path.exists(candidate):
            return candidate

        # 1.1 onedir fallback: some layouts place app data under _internal
        candidate = os.path.join(exe_dir, "_internal", "version.txt")
        if os.path.exists(candidate):
            return candidate

        # 2. Check inside _MEIPASS (bundled at build time â€“ onefile & onedir)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidate = os.path.join(meipass, "version.txt")
            if os.path.exists(candidate):
                return candidate

        # 3. Fallback: same directory as exe
        return os.path.join(exe_dir, "version.txt")

    # Dev / source mode
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "version.txt")


def _resolve_app_version(default: str = "1.0.0") -> str:
    path = _resolve_version_file_path()
    try:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                ver = fh.read().strip()
            if ver:
                return ver
    except Exception:
        pass
    return default


APP_VERSION = _resolve_app_version()

APP_DISPLAY_NAME = "DyeMaster Pro"
APP_ID = "DyeMasterPro"

# â”€â”€ Data directories â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ #
# Use LOCALAPPDATA so data survives app re-installs and avoids UAC issues.
_base_data_dir = os.environ.get("LOCALAPPDATA", str(Path.home()))
USER_DATA_DIR  = os.path.join(_base_data_dir, APP_ID)
DATA_DIR       = os.path.join(USER_DATA_DIR, "data")
EXPORT_DIR     = os.path.join(USER_DATA_DIR, "exports")
BACKUP_DIR     = os.path.join(USER_DATA_DIR, "backups")
LOG_DIR        = os.path.join(USER_DATA_DIR, "logs")
DATABASE_FILE  = os.path.join(DATA_DIR, "dyemasterpro.db")

# â”€â”€ Dye types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ #
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

# â”€â”€ PDF settings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ #
PDF_SETTINGS = {
    "page_size":        "A4",
    "margin":           20,
    "title_font_size":  16,
    "subtitle_font_size": 12,
    "text_font_size":   10,
    "logo_path":        None,
}

# Logging settings removed - reverted to original

# â”€â”€ GUI settings â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ #
GUI_SETTINGS = {
    "window_title": APP_DISPLAY_NAME,
    "window_size":  "1200x700",
    "theme":        "clam",
    "font_family":  "Arial",
    "font_size":    10,
}

