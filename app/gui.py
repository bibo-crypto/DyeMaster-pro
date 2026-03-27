"""
الواجهة الرئيسية
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime
import shutil
import sqlite3

from app.config import DYE_TYPES
from app.database import DatabaseManager
from app.utils import format_currency, format_percentage, clean_color_code, get_current_timestamp
from app.models import Color
from app.updater import AppUpdater
from app.tester import run_tests_from_gui
import logging


class ColorChemSystemGUI:
    """الواجهة الرئيسية للتطبيق"""
    
    def __init__(self, root):
        """تهيئة الواجهة"""
        self.root = root
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # إضافة رقم الإصدار لعنوان النافذة
        from app.config import APP_VERSION
        self.root.title(f"Color and Chemicals Management System - v{APP_VERSION}")
        
        # تعيين أيقونة البرنامج
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass
            
        self.root.after(1, lambda: self.root.state('zoomed'))
        
        # Disable silent auto-update checks on startup to avoid background relaunch behavior.
        # Users can still check updates manually from the menu.
        # Silent auto-update check disabled - only enable via "Test Update" button
        # self.root.after(1000, self.check_for_updates_silent)

        # ✅ إصلاح: استخدام قيمة افتراضية إذا MAIN_WINDOW_SIZE غير معرف
        try:
            # جلب الإعداد من config إذا كان موجوداً
            from app.config import MAIN_WINDOW_SIZE
            self.root.geometry(MAIN_WINDOW_SIZE)
        except (ImportError, AttributeError):
            # قيمة افتراضية في حالة الخطأ
            self.root.geometry("1200x700")

        self.root.configure(bg="#e8e8e8")

        # إدارة قاعدة البيانات
        self.db = DatabaseManager()
        
        # نظام التحديث
        self.updater = AppUpdater(current_version=APP_VERSION)

        # إعدادات الواجهة
        self.dark_mode = False
        self.sort_column = "code"
        self.sort_ascending = True
        self._child_windows = {}

        # تحسين المظهر العام
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        # إنشاء الواجهة
        self.setup_ui()

        # تحميل البيانات
        self.load_data()

        # نسخ احتياطي يومي عند التشغيل (مرة واحدة فقط يومياً)
        try:
            daily_path = self.db.backup_database(once_per_day=True)
            if daily_path:
                print(f"[+] Daily startup backup created: {daily_path}")
            else:
                print("[=] Daily startup backup skipped (already created today).")
        except Exception as e:
            print(f"[-] Daily startup backup failed: {str(e)}")

        # ربط حدث إغلاق البرنامج بدالة النسخ الاحتياطي التلقائي
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def import_data(self):
        """استيراد البيانات"""
        try:
            from app.config import BACKUP_DIR

            backup_file = filedialog.askopenfilename(
                title="Select Backup File",
                initialdir=BACKUP_DIR if os.path.isdir(BACKUP_DIR) else os.path.expanduser("~"),
                filetypes=[("Database files", "*.db"), ("All files", "*.*")]
            )
            if not backup_file:
                return

            if not os.path.isfile(backup_file):
                messagebox.showerror("Import Error", "Selected backup file does not exist.")
                return

            confirm = messagebox.askyesno(
                "Confirm Import",
                "This will replace current application data with the selected backup.\n"
                "A safety backup of current data will be created first.\n\n"
                "Do you want to continue?"
            )
            if not confirm:
                return

            # Safety backup before restore.
            safety_backup_path = self.db.backup_database()

            db_file = self.db.db_file
            os.makedirs(os.path.dirname(db_file), exist_ok=True)
            shutil.copy2(backup_file, db_file)

            # Quick validation that restored file is a readable sqlite DB.
            conn = sqlite3.connect(db_file)
            conn.execute("SELECT name FROM sqlite_master LIMIT 1")
            conn.close()

            self.load_data()
            messagebox.showinfo(
                "Import Completed",
                "Backup imported successfully.\n\n"
                f"Restored from: {backup_file}\n"
                f"Safety backup created at: {safety_backup_path}"
            )
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import backup: {str(e)}")

    def create_menu_bar(self):
        """إنشاء شريط القوائم"""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # قائمة File
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Ctrl+Q")

        # ربط الاختصارات
        self.root.bind('<Control-q>', lambda e: self.on_closing())

        # قائمة Edit
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add Color", command=self.show_add_color_form)
        edit_menu.add_command(label="Add Recipe", command=self.show_add_recipe_form)

        # قائمة View
        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Colors", command=self.show_colors_page)
        view_menu.add_command(label="Recipes", command=self.show_recipes_page)
        view_menu.add_command(label="Colors in Use", command=self.show_colors_in_use_page)

        # قائمة Tools
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Backup Database", command=self.backup_database)
        tools_menu.add_command(label="Import Data", command=self.import_data)
        tools_menu.add_command(label="Check for Updates", command=self.check_updates)
        tools_menu.add_command(label="Test Update", command=self.test_update)
        tools_menu.add_separator()
        tools_menu.add_command(label="Run System Tests", command=self.run_system_tests)

        # قائمة Help
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_dialog)

    def show_add_color_form(self):
        """عرض نموذج إضافة لون"""
        self.clear_fields()
        messagebox.showinfo("Add Color", "Use the form below to add a new color")

    def show_add_recipe_form(self):
        """عرض نموذج إضافة وصفة"""
        self.open_recipe_creator()

    def show_colors_page(self):
        """عرض صفحة الألوان"""
        pass

    def show_recipes_page(self):
        """عرض صفحة الريتشتات"""
        pass

    def show_colors_in_use_page(self):
        """عرض صفحة الألوان المستخدمة"""
        self.open_colors_in_use()

    def check_updates(self):
        """التحقق من التحديثات"""
        try:
            is_update, version, notes, download_info = self.updater.check_for_updates()
            if is_update:
                if messagebox.askyesno(
                    "Update Available",
                    f"New version {version} is available.\n\nNotes:\n{notes}\n\nInstall now?"
                ):
                    # Backup database before update starts
                    backup_path = None
                    try:
                        backup_path = self.db.backup_database()
                    except Exception as e:
                        messagebox.showwarning("Backup Failed", f"Failed to create database backup before update: {e}")

                    success = self.updater.download_and_install(download_info, version, db_backup_path=backup_path)
                    if success:
                        messagebox.showinfo(
                            "Update",
                            "Update downloaded. The app will close now and restart with the new version."
                        )
                        self.root.after(200, self.root.destroy)
            else:
                messagebox.showinfo("Update", "You are using the latest version.")
        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to check for updates: {str(e)}")

    def test_update(self):
        """Force test update flow using latest release payload."""
        if not messagebox.askyesno(
            "Test Update",
            "This will force-download the latest release and restart the app.\n\nContinue?"
        ):
            return

        is_available, version, notes, download_info = self.updater.get_latest_release()
        if not is_available:
            messagebox.showerror("Test Update", "Could not fetch latest release info from GitHub.")
            return

        if messagebox.askyesno(
            "Test Update Ready",
            f"Latest release: v{version}\n\nNotes:\n{notes}\n\nInstall now?"
        ):
            backup_path = None
            try:
                backup_path = self.db.backup_database()
            except Exception as e:
                messagebox.showwarning("Backup Failed", f"Failed to create database backup before update: {e}")

            success = self.updater.download_and_install(download_info, version, db_backup_path=backup_path)
            if success:
                messagebox.showinfo(
                    "Test Update",
                    "Update downloaded. The app will close now and relaunch the new version."
                )
                self.root.after(200, self.root.destroy)

    def check_for_updates_silent(self):
        """التحقق من وجود تحديثات تلقائياً عند بدء التشغيل"""
        try:
            print("Checking for updates...")
            is_update, version, notes, download_info = self.updater.check_for_updates()
            print(f"Update available: {is_update}, version: {version}")
            if is_update:
                print("Update found, showing dialog...")
                if messagebox.askyesno("Update Available", f"A new update is available: v{version}\n\nWould you like to download and install it automatically?"):
                    print("User accepted update, downloading...")
                    success = self.updater.download_and_install(download_info, version)
                    print(f"Update success: {success}")
                    if success:
                        self.root.after(200, self.root.destroy)
        except Exception as e:
            print(f"Silent update check failed: {e}")

    def show_about_dialog(self):
        """عرض نافذة حول"""
        from app.config import APP_VERSION
        about_text = f"""Color and Chemicals Management System

Version: {APP_VERSION}
Developer: Bibo Marcos

نظام إدارة الألوان والكيميائيات
خاصة بمصنع الصباغة والنسيج

© 2024 شركة الحقائق محفوظة
"""
        messagebox.showinfo("About", about_text)

    def toggle_dark_mode(self):
        """Toggle between dark and light mode."""
        self.dark_mode = not self.dark_mode
        self.configure_styles()
        
        if self.dark_mode:
            self.dark_mode_button.config(text="☀ Light")
        else:
            self.dark_mode_button.config(text="🌙 Dark")

    def configure_styles(self):
        """تكوين أنماط الواجهة"""

        # --- Color Palette ---
        if self.dark_mode:
            # Dark Mode Colors
            self.bg_color = "#333333"
            self.fg_color = "#FFFFFF"
            self.frame_bg = "#444444"
            self.entry_bg = "#555555"
            self.button_bg = "#00529B"
            self.button_fg = "#FFFFFF"
            self.button_active_bg = "#0077CC"
            self.accent_button_bg = "#0077CC"
            self.accent_button_active_bg = "#00529B"
            self.header_bg = "#555555"
            self.tree_bg = "#3A3A3A"
            self.tree_fg = "#FFFFFF"
            self.tree_selected_bg = "#00529B"
        else:
            # Light Mode Colors
            self.bg_color = "#e8e8e8"
            self.fg_color = "#000000"
            self.frame_bg = "#e8e8e8"
            self.entry_bg = "#FFFFFF"
            self.button_bg = "#0078D7"
            self.button_fg = "#FFFFFF"
            self.button_active_bg = "#005A9E"
            self.accent_button_bg = "#2E86C1"
            self.accent_button_active_bg = "#1B4F72"
            self.header_bg = "#F0F0F0"
            self.tree_bg = "#FFFFFF"
            self.tree_fg = "#000000"
            self.tree_selected_bg = "#0078D7"

        # Update root background
        self.root.configure(bg=self.bg_color)
        
        # --- Base Styles ---
        self.style.configure('TFrame', background=self.frame_bg)
        self.style.configure('TLabel', background=self.frame_bg, foreground=self.fg_color, font=('Arial', 10))
        self.style.configure('TLabelframe', background=self.frame_bg)
        self.style.configure('TLabelframe.Label', background=self.frame_bg, foreground=self.fg_color, font=('Arial', 10, 'bold'))

        # --- Entry and Combobox ---
        self.style.configure('TEntry', fieldbackground=self.entry_bg, foreground=self.fg_color, insertcolor=self.fg_color)
        self.style.map('TCombobox',
                       fieldbackground=[('readonly', self.entry_bg)],
                       selectbackground=[('readonly', self.entry_bg)],
                       selectforeground=[('readonly', self.fg_color)],
                       background=[('readonly', self.entry_bg)])
        self.style.configure('TCombobox', foreground=self.fg_color)


        # --- General App Button Style ---
        self.style.configure('App.TButton',
                             font=('Arial', 10),
                             padding=5,
                             background=self.button_bg,
                             foreground=self.button_fg)
        self.style.map('App.TButton',
                       background=[('active', self.button_active_bg), ('disabled', self.frame_bg)])

        # --- Treeview Style ---
        self.style.configure('Treeview',
                             background=self.tree_bg,
                             foreground=self.tree_fg,
                             fieldbackground=self.tree_bg,
                             font=('Arial', 10),
                             rowheight=25)
        self.style.map('Treeview',
                       background=[('selected', self.tree_selected_bg)],
                       foreground=[('selected', self.button_fg)])
        self.style.configure('Treeview.Heading', font=('Arial', 10, 'bold'), background=self.header_bg, foreground=self.fg_color)
        self.style.map('Treeview.Heading',
                       background=[('active', self.button_active_bg)])


        # --- Special Buttons (keeping user's preference) ---

        # نمط زر Import مميز (أخضر) - Unchanged
        self.style.configure('Import.TButton',
                             font=('Arial', 10, 'bold'),
                             foreground='white',
                             background='#27AE60',
                             padding=6)
        self.style.map('Import.TButton',
                       background=[('active', '#1E8449')])
        
        # نمط زر Test
        self.style.configure('Test.TButton',
                             font=('Arial', 10, 'bold'),
                             foreground='white',
                             background='#FF5722',
                             padding=6)
        self.style.map('Test.TButton',
                       background=[('active', '#D84315')])

        # Data buttons (Backup/Import)
        self.style.configure('Data.TButton',
                             font=('Arial', 10, 'bold'),
                             foreground='white',
                             background='#2F7D8C',
                             padding=6)
        self.style.map('Data.TButton',
                       background=[('active', '#266773')])

        # نمط زر Accent - I'll keep it but it's not used
        self.style.configure('Accent.TButton',
                             font=('Arial', 10, 'bold'),
                             foreground='white',
                             background=self.accent_button_bg,
                             padding=6)
        self.style.map('Accent.TButton',
                       background=[('active', self.accent_button_active_bg)])

    def setup_ui(self):
        """إعداد واجهة المستخدم"""

        # إطار رئيسي
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # شريط الأدوات
        self.setup_toolbar()

        # إطار البحث
        self.setup_search_frame()

        # إطار الإدخال
        self.setup_input_frame()

        # الجدول
        self.setup_table()

        # شريط الحالة
        self.setup_status_bar()
        
        # إنشاء شريط القوائم
        self.create_menu_bar()

    def setup_toolbar(self):
        """إعداد شريط الأدوات"""
        toolbar_frame = ttk.Frame(self.main_frame)
        toolbar_frame.pack(fill=tk.X, pady=5)

        # الإطار الأول: أزرار التطبيق الرئيسية
        frame1 = ttk.Frame(toolbar_frame, relief="groove", borderwidth=1)
        frame1.pack(side=tk.LEFT, padx=5, pady=2)

        ttk.Button(frame1, text="✚ Create Recipe", command=self.open_recipe_creator, style="App.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(frame1, text="📚 Ricette", command=self.open_saved_recipes, style="App.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(frame1, text="🎨 Colors in Use", command=self.open_colors_in_use, style="App.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(frame1, text="📄 Import PDF", command=self.open_pdf_import, style='Import.TButton').pack(side=tk.LEFT, padx=5)

        # الإطار الثاني: أزرار البيانات والتحديث (على اليسار مع مسافة)
        frame2 = ttk.Frame(toolbar_frame, relief="groove", borderwidth=1)
        frame2.pack(side=tk.LEFT, padx=(20, 5), pady=2)

        ttk.Button(frame2, text="⬇ Import Data", command=self.import_data, style="Data.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(frame2, text="🗄 Backup DB", command=self.backup_database, style="Data.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(frame2, text="⬆ CHECK UPDATE", command=self.test_update, style="Test.TButton").pack(side=tk.LEFT, padx=5)

        self.dark_mode_button = ttk.Button(toolbar_frame, text="🌙 Dark", command=self.toggle_dark_mode, width=10)
        self.dark_mode_button.pack(side=tk.RIGHT, padx=(0, 5))


    def open_pdf_import(self):
        """فتح نافذة استيراد PDF"""
        try:
            from ui.pdf_import_window import PDFImportWindow
            self._open_single_child_window(
                "pdf_import",
                lambda: PDFImportWindow(self.root, self.db)
            )
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open PDF import: {str(e)}")

    def _get_active_child_window(self):
        """Return currently alive child window object if any."""
        stale_keys = []
        for child_key, child_obj in self._child_windows.items():
            child_window = getattr(child_obj, "window", None)
            try:
                if child_window and child_window.winfo_exists():
                    return child_window
            except Exception:
                pass
            stale_keys.append(child_key)
        for stale_key in stale_keys:
            self._child_windows.pop(stale_key, None)
        return None

    def _release_stale_grab(self):
        """Release invalid Tk grab state that can freeze the UI."""
        try:
            grab_widget = self.root.grab_current()
            if grab_widget is None:
                return
            try:
                if grab_widget.winfo_exists():
                    return
            except Exception:
                pass
            self.root.grab_release()
        except Exception:
            pass

    def _bring_child_to_front(self, child_window):
        """Safely show/focus a child window without forcing unstable focus transitions."""
        try:
            if not child_window or not child_window.winfo_exists():
                return
            child_window.deiconify()
            child_window.lift()
            # focus_set is less aggressive than focus_force and avoids some
            # first-open flicker/close behavior on Windows.
            child_window.focus_set()
        except Exception:
            pass

    def _ensure_modal_grab(self, child_window):
        """Ensure the child keeps modal grab over the main window."""
        try:
            if not child_window or not child_window.winfo_exists():
                return
            current_grab = self.root.grab_current()
            if current_grab is None:
                child_window.grab_set()
                return
            if current_grab is child_window:
                return
            current_path = str(current_grab)
            child_path = str(child_window)
            if current_path.startswith(f"{child_path}."):
                return
        except Exception:
            pass

    def _open_single_child_window(self, key: str, factory):
        """Open one modal child window per key and reuse existing instance."""
        self._release_stale_grab()

        existing = self._child_windows.get(key)
        if existing is not None:
            existing_window = getattr(existing, "window", None)
            try:
                if existing_window and existing_window.winfo_exists():
                    self._bring_child_to_front(existing_window)
                    self._ensure_modal_grab(existing_window)
                    return existing
            except Exception:
                pass
            self._child_windows.pop(key, None)

        active_window = self._get_active_child_window()
        if active_window is not None:
            try:
                self._bring_child_to_front(active_window)
                self._ensure_modal_grab(active_window)
            except Exception:
                pass
            return None

        instance = factory()
        child_window = getattr(instance, "window", None)
        if not child_window:
            return instance

        self._child_windows[key] = instance

        def _cleanup_child(_event=None):
            # Ignore destroy events coming from child widgets; we only care
            # when the toplevel window itself is being destroyed.
            if _event is not None and getattr(_event, "widget", None) is not child_window:
                return
            try:
                if self.root.grab_current() is child_window:
                    child_window.grab_release()
            except Exception:
                pass
            if self._child_windows.get(key) is instance:
                self._child_windows.pop(key, None)

        def _on_child_close():
            try:
                child_window.destroy()
            except Exception:
                _cleanup_child()

        try:
            # Keep child windows as normal top-level windows so the OS title-bar
            # controls (Close / Minimize / Maximize) remain available.
            # Avoid using transient() here because on some Windows setups it can
            # remove or disable the standard window controls.
            child_window.protocol("WM_DELETE_WINDOW", _on_child_close)
            child_window.bind("<Destroy>", _cleanup_child, add="+")
            self._bring_child_to_front(child_window)
            self._ensure_modal_grab(child_window)
            # Re-assert visibility shortly after creation to avoid first-open
            # withdrawn state on some Windows setups.
            child_window.after(80, lambda: self._bring_child_to_front(child_window))
            child_window.after(220, lambda: self._bring_child_to_front(child_window))
            child_window.after(80, lambda: self._ensure_modal_grab(child_window))
            child_window.after(220, lambda: self._ensure_modal_grab(child_window))
        except Exception:
            _cleanup_child()

        return instance

    
    def setup_search_frame(self):
        """إعداد إطار البحث"""
        search_frame = ttk.LabelFrame(self.main_frame, text="Search", padding="5")
        search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_colors())

        ttk.Label(search_frame, text="Dye Type:").grid(row=0, column=2, padx=5)
        self.search_type_combo = ttk.Combobox(search_frame, values=DYE_TYPES, state="readonly", width=20)
        self.search_type_combo.grid(row=0, column=3, padx=5)

        ttk.Label(search_frame, text="Supplier:").grid(row=0, column=4, padx=5)
        self.search_supplier_entry = ttk.Entry(search_frame, width=20)
        self.search_supplier_entry.grid(row=0, column=5, padx=5)
        self.search_supplier_entry.bind('<Return>', lambda e: self.search_colors())

        ttk.Button(search_frame, text="🔍 Search", command=self.search_colors, style="App.TButton").grid(row=0, column=6, padx=5)
        ttk.Button(search_frame, text="🧽 Clear", command=self.clear_search, style="App.TButton").grid(row=0, column=7, padx=5)

    def setup_input_frame(self):
        """إعداد إطار إدخال البيانات"""
        input_frame = ttk.LabelFrame(self.main_frame, text="Color Details", padding="5")
        input_frame.pack(fill=tk.X, pady=5)

        # الصف الأول
        row1 = ttk.Frame(input_frame)
        row1.pack(fill=tk.X, pady=5)

        ttk.Label(row1, text="Color Code*:").grid(row=0, column=0, padx=5, sticky="e")
        self.code_entry = ttk.Entry(row1, width=20)
        self.code_entry.grid(row=0, column=1, padx=5, sticky="w")
        self.code_entry.configure(
            validate='key',
            validatecommand=(self.root.register(self.validate_code_input), '%d', '%P')
        )

        ttk.Label(row1, text="Color Name*:").grid(row=0, column=2, padx=5, sticky="e")
        self.name_entry = ttk.Entry(row1, width=30)
        self.name_entry.grid(row=0, column=3, padx=5, sticky="w")

        ttk.Label(row1, text="Dye Type*:").grid(row=0, column=4, padx=5, sticky="e")
        self.type_combo = ttk.Combobox(row1, values=DYE_TYPES, state="readonly", width=20)
        self.type_combo.grid(row=0, column=5, padx=5, sticky="w")

        # الصف الثاني
        row2 = ttk.Frame(input_frame)
        row2.pack(fill=tk.X, pady=5)

        ttk.Label(row2, text="Supplier:").grid(row=0, column=0, padx=5, sticky="e")
        self.supplier_entry = ttk.Entry(row2, width=20)
        self.supplier_entry.grid(row=0, column=1, padx=5, sticky="w")

        ttk.Label(row2, text="Price (kg):").grid(row=0, column=2, padx=5, sticky="e")
        self.price_entry = ttk.Entry(row2, width=10)
        self.price_entry.grid(row=0, column=3, padx=5, sticky="w")

        ttk.Label(row2, text="RESA %:").grid(row=0, column=4, padx=5, sticky="e")
        self.resa_entry = ttk.Entry(row2, width=10)
        self.resa_entry.grid(row=0, column=5, padx=5, sticky="w")

        # أزرار التحكم
        control_frame = ttk.Frame(input_frame)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Button(control_frame, text="➕ Add Color", command=self.add_color, style="App.TButton").grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="✏ Modify Color", command=self.modify_color, style="App.TButton").grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="🗑 Delete Color", command=self.delete_color, style="App.TButton").grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="🧹 Clear Fields", command=self.clear_fields, style="App.TButton").grid(row=0, column=3, padx=5)

    def setup_table(self):
        """إعداد الجدول"""
        table_frame = ttk.Frame(self.main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = [
            ("code", "Color Code", 100),
            ("name", "Color Name", 150),
            ("dye_type", "Type", 100),
            ("supplier", "Supplier", 120),
            ("price_kg", "Price (kg)", 100),
            ("resa_percent", "RESA %", 80),
            ("created_at", "Created", 120),
            ("updated_at", "Updated", 120),
            ("status", "Status", 80),
            ]
        

        self.colors_table = ttk.Treeview(
            table_frame,
            columns=[col[0] for col in columns],
            show="headings",
            height=15
        )

        for col_id, col_text, col_width in columns:
            self.colors_table.heading(
                col_id,
                text=col_text,
                command=lambda c=col_id: self.treeview_sort_column(self.colors_table, c)
            )
            self.colors_table.column(col_id, width=col_width, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.colors_table.yview)
        self.colors_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.colors_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.colors_table.bind("<<TreeviewSelect>>", self.on_table_select)
        self.colors_table.bind("<Double-1>", self.on_double_click)

    def setup_status_bar(self):
        """إعداد شريط الحالة"""
        self.status_bar = tk.Label(
            self.root, 
            text="Ready", 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

    # دوال التحقق
    def validate_code_input(self, action, value):
        """التحقق من صحة إدخال الكود"""
        # Always allow delete/backspace operations.
        if action == '0':
            return True
        # Insert/replace: code must be digits only and max 5 chars.
        if value == "":
            return True
        return value.isdigit() and len(value) <= 5

    def load_data(self):
        """تحميل البيانات"""
        try:
            for row in self.colors_table.get_children():
                self.colors_table.delete(row)

            # تحميل الألوان
            colors = self.db.get_all_colors()

            # إضافة البيانات للجدول
            for color in colors:
                recipes_using = self.db.get_recipes_using_color(color.code)
                status = "Active" if recipes_using else ""
                self.colors_table.insert("", tk.END, values=(
                    color.code,
                    color.name,
                    color.dye_type,
                    color.supplier,
                    format_currency(color.price_kg),
                    format_percentage(color.resa_percent),
                    color.created_at.split()[0] if color.created_at else "",
                    color.updated_at.split()[0] if color.updated_at else "",
                    status
                ))

            self.status_bar.config(text=f"Loaded {len(colors)} colors")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")

    def search_colors(self):
        """بحث في الألوان"""
        try:
            search_term = self.search_entry.get().strip()
            dye_type = self.search_type_combo.get()
            supplier = self.search_supplier_entry.get().strip()

            colors = self.db.get_all_colors()

            # تطبيق الفلاتر
            filtered_colors = []
            for color in colors:
                # فلترة حسب مصطلح البحث
                if search_term:
                    search_lower = search_term.lower()
                    if (search_lower not in str(color.code).lower() and
                        search_lower not in str(color.name).lower() and
                        search_lower not in str(color.dye_type).lower() and
                        search_lower not in str(color.supplier).lower()):
                        continue

                # فلترة حسب نوع الصباغة
                if dye_type and color.dye_type != dye_type:
                    continue

                # فلترة حسب المورد
                if supplier and supplier.lower() not in str(color.supplier).lower():
                    continue

                filtered_colors.append(color)

            # مسح الجدول
            for row in self.colors_table.get_children():
                self.colors_table.delete(row)

            # إضافة النتائج
            for color in filtered_colors:
                recipes_using = self.db.get_recipes_using_color(color.code)
                status = "Active" if recipes_using else ""
                self.colors_table.insert("", tk.END, values=(
                    color.code,
                    color.name,
                    color.dye_type,
                    color.supplier,
                    format_currency(color.price_kg),
                    format_percentage(color.resa_percent),
                    color.created_at.split()[0],
                    color.updated_at.split()[0] if color.updated_at else color.created_at.split()[0],
                    status
                ))

            self.status_bar.config(text=f"Found {len(filtered_colors)} colors")

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def treeview_sort_column(self, tv, col):
        """دالة لترتيب Treeview حسب العمود مع عكس الترتيب عند النقر مرة أخرى"""
        try:
            items = [(tv.set(k, col), k) for k in tv.get_children('')]
            items.sort(key=lambda t: t[0], reverse=self.sort_ascending)
        except:
            # إذا فشل، ترتيب نصي
            items = [(tv.set(k, col), k) for k in tv.get_children('')]
            items.sort(key=lambda t: t[0], reverse=self.sort_ascending)

        # إعادة ترتيب العناصر
        for index, (val, k) in enumerate(items):
            tv.move(k, '', index)

        # عكس الترتيب في المرة القادمة
        self.sort_ascending = not self.sort_ascending

        # تحديث عنوان العمود
        direction = "↑" if self.sort_ascending else "↓"
        current_heading = tv.heading(col)["text"]
        # إزالة أي أسهم سابقة
        if "↑" in current_heading or "↓" in current_heading:
            current_heading = current_heading[:-2]
        tv.heading(col, text=f"{current_heading} {direction}")

    def add_color(self):
        """إضافة لون جديد"""
        try:
            code = self.code_entry.get().strip()
            name = self.name_entry.get().strip()
            dye_type = self.type_combo.get()
            supplier = self.supplier_entry.get().strip()

            # التحقق من الحقول المطلوبة
            if not code or not name or not dye_type:
                messagebox.showwarning("Warning", "Please fill all required fields (*)")
                return

            # تنظيف الكود
            cleaned_code = clean_color_code(code)
            if not cleaned_code.isdigit() or len(cleaned_code) != 5:
                messagebox.showwarning("Warning", "Color code must be exactly 5 digits")
                return

            # الحصول على السعر والنسبة
            try:
                price_kg = float(self.price_entry.get() or 0)
                resa_percent = float(self.resa_entry.get() or 0)
            except ValueError:
                messagebox.showwarning("Error", "Price and RESA must be numbers")
                return

            # التحقق من أن الكود غير موجود مسبقاً
            colors = self.db.get_all_colors()
            for color in colors:
                if color.code == cleaned_code:
                    messagebox.showerror("Error", f"Color code '{cleaned_code}' already exists!")
                    return

            # الاتصال المباشر بقاعدة البيانات
            try:
                conn = self.db.get_connection()
                cursor = conn.cursor()

                # استخدام datetime('now') مباشرة
                cursor.execute('''
                               INSERT INTO colors (code, name, dye_type, supplier, price_kg, resa_percent, created_at,
                                                   updated_at)
                               VALUES (?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                               ''', (cleaned_code, name, dye_type, supplier, price_kg, resa_percent))

                color_id = cursor.lastrowid
                conn.commit()
                conn.close()

                self.load_data()
                self.clear_fields()

                if code != cleaned_code:
                    messagebox.showinfo("Success",
                                        f"Color added successfully! ID: {color_id}\nCode '{code}' was saved as '{cleaned_code}'")
                else:
                    messagebox.showinfo("Success", f"Color added successfully! ID: {color_id}")

            except sqlite3.IntegrityError as e:
                messagebox.showerror("Error", f"Color code '{cleaned_code}' already exists in database")
            except Exception as db_error:
                messagebox.showerror("Error", f"Database error: {str(db_error)}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add color: {str(e)}")

    def delete_color(self):
        """
        Prevents deletion of a selected color if it is in use.
        """
        selected_item = self.colors_table.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a color to delete.")
            return

        raw_color_code = self.colors_table.item(selected_item[0], "values")[0]
        color_code = clean_color_code(raw_color_code)

        try:
            # Resolve the actual row first to avoid stale Treeview selections.
            color_to_delete = self.db.get_color_by_code(color_code)
            if not color_to_delete:
                self.colors_table.delete(selected_item[0])
                self.status_bar.config(text=f"Color '{raw_color_code}' was already removed")
                return

            # Use the database manager to check for usage
            recipes_using_color = self.db.get_recipes_using_color(color_to_delete.code)

            if recipes_using_color:
                # If the color is in use, prevent deletion and show the required error message.
                error_message = (
                    f"Forbidden: Color '{color_to_delete.code}' cannot be deleted.\n\n"
                    f"It is currently used in {len(recipes_using_color)} recipe(s). "
                    "Please see 'Colors in Use' for details."
                )
                messagebox.showerror("Deletion Forbidden", error_message)
                return

            # If not in use, proceed with deletion confirmation.
            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete the color '{color_to_delete.code}'?\n\n"
                "This action is irreversible."
            )

            if not confirm:
                return

            # Use the correct database manager method to delete by ID
            success = self.db.delete_color(color_to_delete.id)

            if success:
                self.colors_table.delete(selected_item[0])
                messagebox.showinfo("Success", f"Color '{color_to_delete.code}' has been deleted successfully.")
                self.load_data()  # Refresh full data and status values
                self.clear_fields()
            else:
                messagebox.showerror("Error", "An error occurred while deleting the color.")

        except Exception as e:
            messagebox.showerror("Application Error", f"A critical error occurred: {str(e)}")

    def modify_color(self):
        """تعديل لون"""
        selected = self.colors_table.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a color to modify")
            return

        old_code = self.colors_table.item(selected[0], "values")[0]

        # التحقق مما إذا كان اللون مستخدماً
        try:
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()

            # أولاً: إيجاد الـ ID الخاص باللون
            cursor.execute("SELECT id FROM colors WHERE code = ?", (old_code,))
            result = cursor.fetchone()

            if not result:
                conn.close()
                messagebox.showerror("Error", f"Color '{old_code}' not found in database")
                return

            color_id = result[0]

            # ثانياً: التحقق من استخدام اللون
            cursor.execute("SELECT COUNT(*) FROM recipe_colors WHERE color_id = ?", (color_id,))
            count = cursor.fetchone()[0]
            conn.close()

            if count > 0:
                # إذا كان مستخدماً، إرسال المستخدم إلى Colors in Use
                response = messagebox.askyesno(
                    "Color Used in Recipes",
                    f"Color '{old_code}' is used in {count} recipe(s).\n\n"
                    "You can only modify this color from the 'Colors in Use' window.\n"
                    "Do you want to open 'Colors in Use' to modify this color?"
                )

                if response:
                    self.open_colors_in_use(initial_search_code=old_code)
                return
        except Exception as e:
            print(f"Error checking color usage: {e}")
            pass

        # إذا كان اللون غير مستخدم، تعديله مباشرة في نفس النافذة
        self.modify_color_directly(old_code)

    def modify_color_directly(self, old_code):
        """تعديل لون غير مستخدم مباشرة"""
        try:
            new_code = self.code_entry.get().strip()
            name = self.name_entry.get().strip()
            dye_type = self.type_combo.get()
            supplier = self.supplier_entry.get().strip()

            # التحقق من الحقول المطلوبة
            if not new_code or not name or not dye_type:
                messagebox.showwarning("Warning", "Please fill all required fields (*)")
                return

            # تنظيف الكود الجديد
            cleaned_new_code = clean_color_code(new_code)
            if not cleaned_new_code.isdigit() or len(cleaned_new_code) != 5:
                messagebox.showwarning("Warning", "Color code must be exactly 5 digits")
                return

            # الحصول على السعر والنسبة
            try:
                price_kg = float(self.price_entry.get() or 0)
                resa_percent = float(self.resa_entry.get() or 0)
            except ValueError:
                messagebox.showwarning("Error", "Price and RESA must be numbers")
                return

            # التحقق من أن الكود الجديد فريد (إذا تغير)
            if cleaned_new_code != old_code:
                colors = self.db.get_all_colors()
                for color in colors:
                    if color.code == cleaned_new_code:
                        messagebox.showerror("Error", f"Color code '{cleaned_new_code}' already exists!")
                        return

            # الحصول على اللون القديم لتحديثه
            old_color = self.db.get_color_by_code(old_code)
            if not old_color:
                messagebox.showerror("Error", f"Color '{old_code}' not found!")
                return

            # تحديث بيانات اللون
            updated_color = Color(
                id=old_color.id,
                code=cleaned_new_code,
                name=name,
                dye_type=dye_type,
                supplier=supplier,
                price_kg=price_kg,
                resa_percent=resa_percent,
                created_at=old_color.created_at,
                updated_at=get_current_timestamp()
            )

            # استخدام دالة update_color من DatabaseManager
            success = self.db.update_color(updated_color)

            if success:
                # تحديث الواجهة
                self.load_data()

                # تحديث الحقول إذا تغير الكود
                if cleaned_new_code != old_code:
                    self.code_entry.delete(0, tk.END)
                    self.code_entry.insert(0, cleaned_new_code)

                messagebox.showinfo("Success", "Color updated successfully!")
            else:
                messagebox.showerror("Error", "Failed to update color!")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to update color: {str(e)}")

    def clear_search(self):
        """مسح البحث"""
        self.search_entry.delete(0, tk.END)
        self.search_type_combo.set('')
        self.search_supplier_entry.delete(0, tk.END)
        self.load_data()

    def clear_fields(self):
        """مسح الحقول"""
        self.code_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.type_combo.set('')
        self.supplier_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.resa_entry.delete(0, tk.END)

        for item in self.colors_table.selection():
            self.colors_table.selection_remove(item)

    def on_table_select(self, event):
        """عند تحديد عنصر من الجدول"""
        selected = self.colors_table.selection()
        if selected:
            values = self.colors_table.item(selected[0], "values")

            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, values[0])

            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, values[1])

            self.type_combo.set(values[2])

            self.supplier_entry.delete(0, tk.END)
            self.supplier_entry.insert(0, values[3])

            # إزالة € من السعر
            price_str = values[4].replace('€', '').strip()
            self.price_entry.delete(0, tk.END)
            self.price_entry.insert(0, price_str)

            # إزالة % من النسبة
            resa_str = values[5].replace('%', '').strip()
            self.resa_entry.delete(0, tk.END)
            self.resa_entry.insert(0, resa_str)

    def on_double_click(self, event):
        """عند النقر المزدوج على الجدول"""
        # يمكن إضافة功能 هنا للتعامل مع النقر المزدوج
        pass

    def open_recipe_creator(self):
        """فتح نافذة إنشاء وصفة"""
        try:
            from ui.recipe_creator_window import RecipeCreatorWindow
            self._open_single_child_window(
                "recipe_creator",
                lambda: RecipeCreatorWindow(self.root, self.db)
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Recipe Creator: {str(e)}")

    def open_saved_recipes(self):
        """فتح نافذة الريتشتات المحفوظة"""
        try:
            from ui.saved_recipes_window import SavedRecipesWindow
            self._open_single_child_window(
                "saved_recipes",
                lambda: SavedRecipesWindow(self.root, self.db, on_data_changed=self.load_data)
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Saved Recipes window: {str(e)}")

    def open_colors_in_use(self, initial_search_code: str = None):
        """فتح نافذة الألوان المستخدمة"""
        try:
            from ui.colors_in_use_window import ColorsInUseWindow
            window_obj = self._open_single_child_window(
                "colors_in_use",
                lambda: ColorsInUseWindow(
                    self.root,
                    self.db,
                    initial_search_code=initial_search_code,
                    on_data_changed=self.load_data
                )
            )
            # If already open, keep behavior of pre-selecting requested color.
            if initial_search_code and window_obj:
                try:
                    normalized_code = clean_color_code(initial_search_code)
                    window_obj.search_code_var.set(normalized_code)
                    window_obj.perform_search()
                    if hasattr(window_obj, "_select_color_in_tree"):
                        window_obj._select_color_in_tree(normalized_code)
                except Exception:
                    pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Colors in Use window: {str(e)}")

    def backup_database(self):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            from app.config import BACKUP_DIR

            # اختيار مجلد الحفظ
            folder = filedialog.askdirectory(title="Select Backup Folder")

            if not folder:
                return

            # اسم الملف
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            db_file = self.db.db_file

            if os.path.exists(db_file):
                backup_file = os.path.join(folder, f"ColorChem_Backup_{timestamp}.db")

                # نسخ ملف قاعدة البيانات
                shutil.copy2(db_file, backup_file)

                # إنشاء ملف معلومات
                info_file = os.path.join(folder, f"Backup_Info_{timestamp}.txt")
                with open(info_file, 'w', encoding='utf-8') as f:
                    f.write(f"ColorChem System Backup\n")
                    f.write(f"=" * 40 + "\n")
                    f.write(f"Backup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Original: {db_file}\n")
                    f.write(f"Backup: {backup_file}\n")
                    f.write(f"\nStatistics:\n")

                    # إضافة إحصائيات
                    colors = self.db.get_all_colors()
                    recipes = self.db.get_all_recipes()

                    f.write(f"- Colors: {len(colors)}\n")
                    f.write(f"- Recipes: {len(recipes)}\n")

                messagebox.showinfo("Backup Complete",
                                    f"Backup created successfully!\n\n"
                                    f"File: {backup_file}\n"
                                    f"Info: {info_file}")
            else:
                messagebox.showerror("Error", "Could not find database file")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {str(e)}")

    def run_system_tests(self):
        """تشغيل اختبارات النظام"""
        try:
            run_tests_from_gui(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tests: {str(e)}")

    def on_closing(self):
        """معالج حدث إغلاق البرنامج - عمل نسخة احتياطية تلقائية"""
        try:
            # نسخة يومية إذا لم توجد بعد اليوم
            daily_path = self.db.backup_database(once_per_day=True)
            if daily_path:
                print(f"[+] Daily auto backup created: {daily_path}")
            else:
                print("[=] Daily auto backup skipped (already created today).")

            # نسخة متجددة دائماً عند الإغلاق
            latest_path = self.db.backup_database(always_latest=True)
            if latest_path:
                print(f"[+] Latest backup created/updated: {latest_path}")

        except Exception as e:
            print(f"[-] Auto backup failed: {str(e)}")
            # لا نمنع الإغلاق حتى إذا فشل الـ backup
        
        # إغلاق البرنامج بشكل طبيعي
        try:
            for child_obj in list(self._child_windows.values()):
                child_window = getattr(child_obj, "window", None)
                if child_window and child_window.winfo_exists():
                    try:
                        if self.root.grab_current() is child_window:
                            child_window.grab_release()
                    except Exception:
                        pass
                    child_window.destroy()
            self._child_windows.clear()
            try:
                if self.root.grab_current() is not None:
                    self.root.grab_release()
            except Exception:
                pass
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        """تشغيل التطبيق"""
        self.root.mainloop()
