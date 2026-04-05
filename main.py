"""
نقطة الدخول الرئيسية للتطبيق - نسخة مبسطة
"""
import os
import sys
import socket
import errno
from pathlib import Path
from datetime import datetime
if os.name == "nt":
    import ctypes

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


def _trace_startup(message: str) -> None:
    """Best-effort startup trace for installed builds diagnostics."""
    try:
        base = os.environ.get("LOCALAPPDATA", "")
        log_dir = os.path.join(base, "DyeMasterPro", "logs") if base else os.path.join(os.getcwd(), ".logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "startup_trace.log")
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception:
        pass

try:
    import tkinter as tk
    from tkinter import messagebox
except ModuleNotFoundError as e:
    print("FATAL: tkinter module not found. Please install or use a Python build with Tk support.")
    print("If you are using a virtual environment, activate it first and install dependencies:")
    print("  pip install -r requirements.txt")
    print("On Windows, install Python from python.org and enable tcl/tk option.")
    sys.exit(1)

INSTANCE_PORT = 52476  # fallback only (non-Windows)


def acquire_single_instance():
    """Acquire a single-instance lock handle."""
    if os.name == "nt":
        try:
            kernel32 = ctypes.windll.kernel32
            mutex_name = "Global\\DyeMasterPro_SingleInstance"
            handle = kernel32.CreateMutexW(None, False, mutex_name)
            if not handle:
                raise OSError("CreateMutexW failed")
            if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
                kernel32.CloseHandle(handle)
                print("[single-instance] lock failed (mutex already exists)")
                _trace_startup("single-instance mutex already exists")
                return None
            print("[single-instance] lock acquired via mutex")
            _trace_startup("single-instance mutex acquired")
            return handle
        except Exception as e:
            print(f"[single-instance] mutex lock error: {e}")
            _trace_startup(f"single-instance mutex error: {e}")
            return None

    # Non-Windows fallback uses localhost port.
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    _trace_startup("main() started")
    _restore_pending_database()
    lock_socket = acquire_single_instance()
    if lock_socket is None:
        # إذا كانت نسخة أخرى بالفعل تعمل، نمنع فتح نسخة جديدة ونخرج فوراً بدون شاشة إضافية
        print("[single-instance] another instance already running; exiting")
        _trace_startup("single-instance lock not acquired; exiting")
        sys.exit(0)

    try:
        # إنشاء النافذة الرئيسية
        root = tk.Tk()
        _trace_startup("tk root created")
        from app.config import APP_VERSION
        root.title(f"DyeMaster Pro v{APP_VERSION}")
        root.geometry("1200x700")

        from app.licensing import ensure_license_activated
        if not ensure_license_activated(root):
            _trace_startup("license activation cancelled/failed; exiting")
            root.destroy()
            sys.exit(0)
        _trace_startup("license activation OK")

        # محاولة استيراد وتشغيل الواجهة
        try:
            from app.gui import DyeMasterProGUI
            app = DyeMasterProGUI(root)
            print("GUI created successfully")
            _trace_startup("GUI created, entering mainloop")
            app.run()
            _trace_startup("mainloop exited")
        except Exception as e:
            # إذا فشل تحميل GUI، اعرض رسالة خطأ
            import traceback
            traceback.print_exc()
            _trace_startup(f"GUI exception: {e}")
            messagebox.showerror("Error", f"Failed to load GUI: {str(e)}")
            root.destroy()
    except Exception as e:
        import traceback
        traceback.print_exc()
        _trace_startup(f"fatal exception: {e}")
        try:
            messagebox.showerror("Fatal Error", f"Application error: {str(e)}")
        except Exception:
            print(f"Fatal Error: {e}")
        sys.exit(1)
    finally:
        # تحرير القفل عند انتهاء العملية
        _trace_startup("main() cleanup/finally")
        try:
            if os.name == "nt" and isinstance(lock_socket, int):
                ctypes.windll.kernel32.CloseHandle(lock_socket)
            else:
                lock_socket.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
