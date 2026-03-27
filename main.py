"""
نقطة الدخول الرئيسية للتطبيق - نسخة مبسطة
"""
import os
import sys
import socket
import errno
from pathlib import Path

# في حالة تشغيل الملف مباشرة من زر Run في VSCode باستخدام مفسر خارجي (غير venv)،
# نحاول إعادة التشغيل مع المفسر الموجود في venv المحلي إذا كان موجود.
def _find_local_venv_python():
    candidates = [
        Path("venv/Scripts/python.exe"),
        Path(".venv/Scripts/python.exe"),
        Path("venv/bin/python"),
        Path(".venv/bin/python"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


def _is_venv_active():
    # Detect by standard Python virtualenv flags.
    if hasattr(sys, 'real_prefix') and sys.real_prefix != sys.base_prefix:
        return True
    if hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix:
        return True
    # Fallback for named directories.
    parts = Path(sys.executable).parts
    return any(name.lower() in ('venv', '.venv') for name in parts)


def _ensure_venv():
    # In frozen build, لا يعمل.
    if getattr(sys, 'frozen', False):
        return

    if _is_venv_active():
        print(f"Using active interpreter: {sys.executable}")
        return

    venv_python = _find_local_venv_python()
    if venv_python:
        venv_python = os.path.abspath(venv_python)
        current = os.path.abspath(sys.executable)
        if os.path.normcase(current) != os.path.normcase(venv_python):
            print(f"Switching Python interpreter from {current} to {venv_python}")
            try:
                os.execv(venv_python, [venv_python] + sys.argv)
            except Exception as e:
                print(f"Failed to exec venv Python: {e}")
    else:
        print("توجد بيئة افتراضية (venv) محلية غير موجودة؛ استخدم venv\\Scripts\\activate في VSCode")


_ensure_venv()

import tkinter as tk
from tkinter import messagebox

INSTANCE_PORT = 52476  # بورت ثابت لحماية التشغيل مرة واحدة


def acquire_single_instance():
    """يحاول حجز بورت محلي لتحديد إن كانت نسخة أخرى تعمل فعلاً."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # في ويندوز، استخدم SO_EXCLUSIVEADDRUSE لتجنب استغلال نفس البورت من عدة عمليات.
    if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        except OSError:
            pass

    try:
        sock.bind(("127.0.0.1", INSTANCE_PORT))
        sock.listen(1)
        print(f"[single-instance] lock acquired on 127.0.0.1:{INSTANCE_PORT}")
        return sock
    except OSError as e:
        sock.close()
        if e.errno in (errno.EADDRINUSE,):
            print(f"[single-instance] lock failed, port {INSTANCE_PORT} already in use")
            return None
        raise


def _restore_pending_database():
    """If an update has marked a DB backup, restore it now (after new version start)."""
    try:
        from app.config import BACKUP_DIR
        marker = os.path.join(BACKUP_DIR, "pending_update_restore.txt")
        if os.path.isfile(marker):
            with open(marker, "r", encoding="utf-8") as mf:
                backup_path = mf.read().strip()
            if backup_path and os.path.isfile(backup_path):
                from app.database import DatabaseManager
                db = DatabaseManager()
                db.restore_database(backup_path)
                print(f"[Updater] Restored database from backup: {backup_path}")
            else:
                print(f"[Updater] Pending backup path missing: {backup_path}")
            try:
                os.remove(marker)
            except Exception:
                pass
    except Exception as e:
        print(f"[Updater] Failed pending DB restore: {e}")


def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    _restore_pending_database()
    lock_socket = acquire_single_instance()
    if lock_socket is None:
        # إذا كانت نسخة أخرى بالفعل تعمل، نمنع فتح نسخة جديدة ونخرج فوراً بدون شاشة إضافية
        print("[single-instance] another instance already running; exiting")
        sys.exit(0)

    try:
        # إنشاء النافذة الرئيسية
        root = tk.Tk()
        from app.config import APP_VERSION
        root.title(f"ColorChem System v{APP_VERSION}")
        root.geometry("1200x700")

        # محاولة استيراد وتشغيل الواجهة
        try:
            from app.gui import ColorChemSystemGUI
            app = ColorChemSystemGUI(root)
            print("GUI created successfully")
            app.run()
        except Exception as e:
            # إذا فشل تحميل GUI، اعرض رسالة خطأ
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load GUI: {str(e)}")
            root.destroy()
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            messagebox.showerror("Fatal Error", f"Application error: {str(e)}")
        except Exception:
            print(f"Fatal Error: {e}")
        sys.exit(1)
    finally:
        # تحرير القفل عند انتهاء العملية
        try:
            lock_socket.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
