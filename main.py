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
    base_dir = Path(__file__).resolve().parent
    candidates = [
        base_dir / "venv" / "Scripts" / "python.exe",
        base_dir / ".venv" / "Scripts" / "python.exe",
        base_dir / "venv" / "bin" / "python",
        base_dir / ".venv" / "bin" / "python",
    ]
    for p in candidates:
        if p.exists():
            return str(p.resolve())
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
    # In frozen build, do nothing.
    if getattr(sys, 'frozen', False):
        return

    preferred_python = _find_local_venv_python()
    current = os.path.abspath(sys.executable)

    if preferred_python:
        preferred_python = os.path.abspath(preferred_python)
        if os.path.normcase(current) != os.path.normcase(preferred_python):
            print(f"Switching Python interpreter from {current} to {preferred_python}")
            try:
                os.execv(preferred_python, [preferred_python] + sys.argv)
            except Exception as e:
                os.environ["DYEMASTER_VENV_FAILED"] = "1"
                print(f"Failed to exec preferred venv Python: {e}")

    if _is_venv_active():
        print(f"Using active interpreter: {sys.executable}")
        return

    if not preferred_python:
        print("Local virtual environment not found. Activate venv\\Scripts\\activate in VSCode.")


_ensure_venv()


def _configure_tk_env():
    """Best-effort Tcl/Tk path setup for environments with broken defaults."""
    if os.environ.get("TCL_LIBRARY") and os.environ.get("TK_LIBRARY"):
        return

    candidates = []

    # Project-local bundled Tcl/Tk (if present).
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tcl"))

    # Typical Python install location near current interpreter.
    candidates.append(os.path.join(os.path.dirname(sys.executable), "tcl"))

    # Known Windows locations used in this environment.
    local = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    if local:
        candidates.append(os.path.join(local, "Programs", "Python", "Python314", "tcl"))
    if appdata:
        candidates.append(os.path.join(appdata, "uv", "python", "cpython-3.14.3-windows-x86_64-none", "tcl"))


    for base in candidates:
        tcl_dir = os.path.join(base, "tcl8.6")
        tk_dir = os.path.join(base, "tk8.6")
        if os.path.isdir(tcl_dir) and os.path.isdir(tk_dir):
            os.environ.setdefault("TCL_LIBRARY", tcl_dir)
            os.environ.setdefault("TK_LIBRARY", tk_dir)
            return


_configure_tk_env()


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
            raise RuntimeError(f"Single-instance mutex initialization failed: {e}") from e

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
    """
    After a successful update, restore the pre-update database backup.
    The marker file is always removed, even if restore fails,
    so we never attempt a stale restore on subsequent launches.
    """
    try:
        from app.config import BACKUP_DIR
        marker = os.path.join(BACKUP_DIR, "pending_update_restore.txt")
        if not os.path.isfile(marker):
            return  # nothing to do

        backup_path = ""
        try:
            with open(marker, "r", encoding="utf-8") as mf:
                backup_path = mf.read().strip()
        except Exception as read_err:
            print(f"[Updater] Could not read restore marker: {read_err}")
        finally:
            # Always remove marker — prevents repeated restore attempts
            try:
                os.remove(marker)
            except Exception:
                pass

        if not backup_path:
            print("[Updater] Restore marker was empty — skipping.")
            return

        if not os.path.isfile(backup_path):
            print(f"[Updater] Backup file not found, skipping restore: {backup_path}")
            return

        from app.database import DatabaseManager
        db = DatabaseManager()
        db.restore_database(backup_path)
        print(f"[Updater] Database restored from: {backup_path}")

    except Exception as e:
        print(f"[Updater] Failed pending DB restore: {e}")


def main():
    """الدخول → Login Screen → GUI"""
    _trace_startup("main() started")
    lock_socket = acquire_single_instance()
    if lock_socket is None:
        print("[single-instance] another instance already running; exiting")
        _trace_startup("single-instance lock not acquired; exiting")
        sys.exit(0)
    _restore_pending_database()

    try:
        root = tk.Tk()
        _trace_startup("tk root created")
        
        # نظام Login الجديد
        from ui.login_window import LoginWindow

        login_success = [False]

        def on_login_success():
            login_success[0] = True

        LoginWindow(root, on_success_callback=on_login_success)
        root.mainloop()

        if login_success[0]:
            show_main_gui()
        
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
        _trace_startup("main() cleanup")
        try:
            if os.name == "nt":
                ctypes.windll.kernel32.CloseHandle(lock_socket)
            elif lock_socket:
                lock_socket.close()
        except Exception:
            pass

def show_main_gui():
    """عرض الـ GUI الرئيسي بعد Login الناجح"""
    from app.config import APP_VERSION

    root = tk.Tk()
    root.title(f"DyeMaster Pro v{APP_VERSION}")
    root.geometry("1200x700")
    
    try:
        from app.gui import DyeMasterProGUI
        app = DyeMasterProGUI(root)
        print("Login -> GUI loaded successfully")
        app.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Failed to load main GUI: {str(e)}")
        root.destroy()


if __name__ == "__main__":
    main()
