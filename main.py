"""
نقطة الدخول الرئيسية للتطبيق
"""
import tkinter as tk
from tkinter import messagebox
import os
import sys
import traceback
import logging
import ctypes
from app.config import LOG_DIR

def initialize_application():
    """تهيئة التطبيق وإنشاء المجلدات اللازمة"""
    try:
        from app.config import USER_DATA_DIR, DATA_DIR, EXPORT_DIR, BACKUP_DIR, LOG_DIR
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(EXPORT_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
        
        # التحقق من صلاحيات الكتابة
        test_file = os.path.join(DATA_DIR, "test_write.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        return True
    except Exception as e:
        # استخدام traceback لكتابة الخطأ في ملف لوج لاحقاً إذا لزم الأمر
        traceback.print_exc()
        messagebox.showerror(
            "Initialization Error",
            f"Could not initialize application directories.\n"
            f"Please check permissions for the path.\n\n"
            f"Error: {e}"
        )
        return False

def check_database_status():
    """فحص حالة قاعدة البيانات وإنشائها إذا لم تكن موجودة"""
    try:
        from app.database import DatabaseManager
        db = DatabaseManager()
        db.initialize_database() # يضمن إنشاء الجداول إذا لم تكن موجودة
        return True
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror(
            "Database Error",
            f"A critical error occurred while checking the database status.\n\n"
            f"Error: {e}"
        )
        return False

def setup_logging():
    """إعداد نظام السجلات"""
    log_file = os.path.join(LOG_DIR, "app.log")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    # منع تشغيل الواجهة أثناء تحليل PyInstaller
    try:
        import psutil
        parent = psutil.Process(os.getpid()).parent()
        if 'pyinstaller' in parent.name().lower():
            return
    except:
        pass

    setup_logging()
    logger = logging.getLogger(__name__)

    # منع تشغيل نسخ متعددة
    lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.lock")
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            # التحقق إذا كان العملية لا تزال تعمل
            try:
                import psutil
                if psutil.pid_exists(pid):
                    messagebox.showwarning("Application Already Running", "The application is already running.")
                    sys.exit(0)
                else:
                    # العملية انتهت، حذف الملف
                    os.remove(lock_file)
            except ImportError:
                # إذا لم يكن psutil مثبتاً، نفترض أن العملية لا تعمل
                os.remove(lock_file)
        except:
            os.remove(lock_file)

    # إنشاء ملف القفل
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
    except:
        pass

    try:
        # إضافة مسار المشروع إلى sys.path
        app_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(app_dir)
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)

        # تهيئة التطبيق
        if not initialize_application():
            logger.error("Failed to initialize application directories")
            sys.exit(1)

        # فحص قاعدة البيانات
        if not check_database_status():
            logger.error("Failed to check database status")
            sys.exit(1)

        # تحميل الواجهة الرسومية
        from app.gui import ColorChemSystemGUI

        # تشغيل الواجهة
        root = tk.Tk()

        app = ColorChemSystemGUI(root)

        # تكبير النافذة
        root.state('zoomed')

        app.run()

    except Exception as e:
        # معالجة أي خطأ فادح أثناء بدء التشغيل
        logger.critical(f"Fatal application error: {e}", exc_info=True)
        messagebox.showerror(
            "Fatal Application Error",
            f"A fatal error occurred and the application must close.\n"
            f"Please check the log files for more details.\n\n"
            f"Error: {e}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()