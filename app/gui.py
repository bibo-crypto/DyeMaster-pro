"""
الواجهة الرئيسية
"""
import tkinter as tk
from tkinter import ttk, messagebox
import shutil
import sqlite3

from app.config import *
from app.database import DatabaseManager
from app.utils import *
from app.models import Color
from app.updater import AppUpdater
import logging


class ColorChemSystemGUI:
    """الواجهة الرئيسية للتطبيق"""

    def __init__(self, root):
        self.root = root
        self.root.title("Color and Chemicals Management System")
        
        # تعيين أيقونة البرنامج
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass
            
        self.root.after(1, lambda: self.root.state('zoomed'))

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

        # تحسين المظهر العام
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()

        # إنشاء الواجهة
        self.setup_ui()

        # تحميل البيانات
        self.load_data()

        # ربط حدث إغلاق البرنامج بدالة النسخ الاحتياطي التلقائي
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def import_data(self):
        """استيراد البيانات"""
        messagebox.showinfo("قيد التطوير", "خاصية الاستيراد قيد التطوير حالياً")

    def create_menu_bar(self):
        """إنشاء شريط القوائم"""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # قائمة File
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")

        # ربط الاختصارات
        self.root.bind('<Control-q>', lambda e: self.root.quit())

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
        tools_menu.add_command(label="🔄 Check for Updates", command=self.check_updates)
        tools_menu.add_separator()
        tools_menu.add_command(label="🧪 Run System Tests", command=self.run_system_tests)

        # قائمة Help
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_dialog)

    def show_add_color_form(self):
        """عرض نموذج إضافة لون"""
        # مسح الحقول والبدء بإضافة جديدة
        self.clear_fields()
        messagebox.showinfo("إضافة لون", "املأ الحقول في أسفل النافذة ثم انقر على 'Add Color'")

    def show_add_recipe_form(self):
        """عرض نموذج إضافة وصفة"""
        self.open_recipe_creator()

    def show_colors_page(self):
        """عرض صفحة الألوان"""
        # نحن بالفعل في صفحة الألوان
        pass

    def show_recipes_page(self):
        """عرض صفحة الريتشتات"""
        self.open_saved_recipes()

    def show_colors_in_use_page(self):
        """عرض صفحة الألوان المستخدمة"""
        self.open_colors_in_use()

    
    def show_settings_page(self):
        """عرض صفحة الإعدادات"""
        messagebox.showinfo("الإعدادات", "الإعدادات قيد التطوير")

    def check_updates(self):
        """التحقق من التحديثات"""
        is_update, version, notes, url = self.updater.check_for_updates()
        if is_update:
            if messagebox.askyesno("Update Available", f"New version {version} is available.\n\nNotes:\n{notes}\n\nDo you want to download it?"):
                self.updater.download_and_install(url)
        else:
            messagebox.showinfo("Update", "You are using the latest version.")

    def show_about_dialog(self):
        """عرض نافذة حول"""
        about_text = """
        Color and Chemicals Management System
        
        Version: 1.0.0
        Developer: Bibo Marcos
        
        نظام إدارة الألوان والكيماويات
        خاص بمصانع الصباغة والنسيج
        
        © 2024 جميع الحقوق محفوظة
        """
        messagebox.showinfo("About", about_text)

    def toggle_dark_mode(self):
        """Toggle between dark and light mode."""
        self.dark_mode = not self.dark_mode
        self.configure_styles()
        
        if self.dark_mode:
            self.dark_mode_button.config(text="☀️")
        else:
            self.dark_mode_button.config(text="🌙")

    def configure_styles(self):
        """تكوين أنماط الواجهة"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

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
        # إنشاء القوائم
        self.create_menu_bar()

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

    def setup_toolbar(self):
        """إعداد شريط الأدوات"""
        toolbar_frame = ttk.LabelFrame(self.main_frame, text="Tools", padding=10)
        toolbar_frame.pack(fill=tk.X, pady=5)


        # الأزرار الأصلية
        ttk.Button(toolbar_frame, text="🔄 Refresh List", command=self.load_data, style="App.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="➕ Create Recipe", command=self.open_recipe_creator, style="App.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="📋 Ricette", command=self.open_saved_recipes, style="App.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="🎨 Colors in Use", command=self.open_colors_in_use, style="App.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="🗑️ Clear Fields", command=self.clear_fields, style="App.TButton").pack(side=tk.LEFT, padx=5)

        # زر Backup
        ttk.Button(toolbar_frame, text="💾 Backup DB",
                   command=self.backup_database, style="App.TButton").pack(side=tk.LEFT, padx=5)

        # زر Statistics

        ttk.Button(toolbar_frame, text="📄 Import PDF",
                   command=self.open_pdf_import, width=12, style='Import.TButton').pack(side=tk.LEFT, padx=5)

        self.dark_mode_button = ttk.Button(toolbar_frame, text="🌙", command=self.toggle_dark_mode, width=4)
        self.dark_mode_button.pack(side=tk.RIGHT, padx=5)


    def open_pdf_import(self):
        """فتح نافذة استيراد PDF"""
        try:
            from ui.pdf_import_window import PDFImportWindow
            PDFImportWindow(self.root, self.db)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open PDF import: {str(e)}")

    
    def setup_search_frame(self):
        """إعداد إطار البحث"""
        search_frame = ttk.LabelFrame(self.main_frame, text="Search & Filter", padding=10)
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

        ttk.Button(search_frame, text="Search", command=self.search_colors, style="App.TButton").grid(row=0, column=6, padx=5)
        ttk.Button(search_frame, text="Clear", command=self.clear_search, style="App.TButton").grid(row=0, column=7, padx=5)

    def setup_input_frame(self):
        """إعداد إطار إدخال البيانات"""
        input_frame = ttk.LabelFrame(self.main_frame, text="Color Data", padding=10)
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

        ttk.Button(control_frame, text="Add Color", command=self.add_color, style="App.TButton").grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Modify Color", command=self.modify_color, style="App.TButton").grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Delete Color", command=self.delete_color, style="App.TButton").grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Clear Fields", command=self.clear_fields, style="App.TButton").grid(row=0, column=3, padx=5)

    def setup_table(self):
        """إعداد الجدول"""
        table_frame = ttk.LabelFrame(self.main_frame, text="Colors List", padding=10)
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
        self.status_bar = ttk.Label(self.root, text="Ready - Color and Chemicals Management System",
                                    relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

    # دوال التحقق
    def validate_code_input(self, action, value):
        """التحقق من صحة إدخال الكود"""
        if action == '1':
            if value == '':
                return True
            return value.isdigit() and len(value) <= 5
        return True

    def load_data(self):
        """تحميل البيانات"""
        try:
            # مسح الجدول
            for row in self.colors_table.get_children():
                self.colors_table.delete(row)

            # تحميل الألوان
            colors = self.db.get_all_colors()  # <-- هنا المشكلة!

            # إضافة البيانات للجدول
            for color in colors:
                self.colors_table.insert("", tk.END, values=(
                    color.code,
                    color.name,
                    color.dye_type,
                    color.supplier,
                    format_currency(color.price_kg),
                    format_percentage(color.resa_percent),
                    color.created_at.split()[0] if color.created_at else "",
                    color.updated_at.split()[0] if color.updated_at else ""
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
                self.colors_table.insert("", tk.END, values=(
                    color.code,
                    color.name,
                    color.dye_type,
                    color.supplier,
                    format_currency(color.price_kg),
                    format_percentage(color.resa_percent),
                    color.created_at.split()[0],
                    color.updated_at.split()[0] if color.updated_at else color.created_at.split()[0]
                ))

            self.status_bar.config(text=f"Found {len(filtered_colors)} colors")

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")

    def treeview_sort_column(self, tv, col):
        """دالة لترتيب Treeview حسب العمود مع عكس الترتيب عند النقر مرة أخرى"""
        # الحصول على كل العناصر
        items = [(tv.set(k, col), k) for k in tv.get_children('')]

        # محاولة ترتيب الأرقام
        try:
            items.sort(key=lambda t: float(t[0].replace('€', '').replace('%', '').strip())
            if t[0].replace('€', '').replace('%', '').replace('.', '', 1).isdigit()
            else t[0], reverse=self.sort_ascending)
        except:
            # إذا فشل، ترتيب نصي
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

        color_code = self.colors_table.item(selected_item[0], "values")[0]

        try:
            # Use the database manager to check for usage
            recipes_using_color = self.db.get_recipes_using_color(color_code)

            if recipes_using_color:
                # If the color is in use, prevent deletion and show the required error message.
                error_message = (
                    f"Forbidden: Color '{color_code}' cannot be deleted.\n\n"
                    f"It is currently used in {len(recipes_using_color)} recipe(s). "
                    "Please see 'Colors in Use' for details."
                )
                messagebox.showerror("Deletion Forbidden", error_message)
                return

            # If not in use, proceed with deletion confirmation.
            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete the color '{color_code}'?\n\n"
                "This action is irreversible."
            )

            if not confirm:
                return

            # Get the full color object to get the ID for deletion
            color_to_delete = self.db.get_color_by_code(color_code)
            if not color_to_delete:
                messagebox.showerror("Error", f"Color '{color_code}' could not be found in the database.")
                self.load_data() # Refresh list in case it was deleted by another process
                return

            # Use the correct database manager method to delete by ID
            success = self.db.delete_color(color_to_delete.id)

            if success:
                messagebox.showinfo("Success", f"Color '{color_code}' has been deleted successfully.")
                self.load_data()  # Refresh the color list
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
                    self.open_colors_in_use()
                return
        except Exception as e:
            print(f"Error checking color usage: {e}")
            pass

        # إذا كان اللون غير مستخدم، تعديله مباشرة في نفس النافذة
        self.modify_color_directly(old_code)

    def modify_color_directly(self, old_code):
        """تعديل لون غير مستخدم مباشرة"""
        try:
            # الحصول على البيانات من الحقول
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
        self.on_table_select(event)

    def open_recipe_creator(self):
        """فتح نافذة إنشاء وصفة"""
        from ui.recipe_creator_window import RecipeCreatorWindow
        RecipeCreatorWindow(self.root, self.db)

    def open_saved_recipes(self):
        """فتح نافذة الريتشتات المحفوظة"""
        try:
            from ui.saved_recipes_window import SavedRecipesWindow
            SavedRecipesWindow(self.root, self.db)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Saved Recipes window: {str(e)}")

    def open_colors_in_use(self):
        """فتح نافذة الألوان المستخدمة"""
        from ui.colors_in_use_window import ColorsInUseWindow
        ColorsInUseWindow(self.root, self.db)

    def backup_database(self):
        """إنشاء نسخة احتياطية من قاعدة البيانات"""
        try:
            from tkinter import filedialog
            from datetime import datetime

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

                messagebox.showinfo("✅ تم النسخ الاحتياطي",
                                    f"تم إنشاء النسخة الاحتياطية بنجاح!\n\n"
                                    f"الملف: {backup_file}\n"
                                    f"معلومات: {info_file}")
            else:
                messagebox.showerror("خطأ", "لم يتم العثور على ملف قاعدة البيانات")

        except Exception as e:
            messagebox.showerror("خطأ", f"فشل النسخ الاحتياطي: {str(e)}")

    def run_system_tests(self):
        """تشغيل اختبارات النظام"""
        try:
            from app.tester import run_tests_from_gui
            run_tests_from_gui(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tests: {str(e)}")

    def on_closing(self):
        """معالج حدث إغلاق البرنامج - عمل نسخة احتياطية تلقائية"""
        try:
            # محاولة إنشاء نسخة احتياطية تلقائية
            backup_path = self.db.backup_database()
            print(f"[+] Auto backup created: {backup_path}")
        except Exception as e:
            print(f"[-] Auto backup failed: {str(e)}")
            # لا نمنع الإغلاق حتى إذا فشل الـ backup
        
        # إغلاق البرنامج بشكل طبيعي
        self.root.destroy()

    def run(self):
        """تشغيل التطبيق"""
        self.root.mainloop()