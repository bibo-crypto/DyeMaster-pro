"""
نافذة إنشاء وصفة جديدة
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import List, Dict

from app.database import DatabaseManager
from app.calculator import ChemicalCalculator, CostCalculator
from app.utils import clean_recipe_code, validate_recipe_code_input, get_current_timestamp
from app.models import Recipe
from app.config import DYE_TYPES


def _show_on_top(window, parent):
    """Ensure new windows open above their parent."""
    try:
        window.lift()
        window.focus_force()
        window.attributes("-topmost", True)
        window.after(250, lambda: window.attributes("-topmost", False))
    except Exception:
        pass


class RecipeCreatorWindow:
    """نافذة إنشاء وصفة جديدة"""

    def __init__(self, parent, db: DatabaseManager):
        self.parent = parent
        self.db = db
        self.indanthren_colors = []  # تخزين ألوان Indanthren
        self.reattivi_colors = []  # تخزين ألوان Reattivi (Caldi + Freddi + Other)

        self.window = tk.Toplevel(parent)
        _show_on_top(self.window, parent)
        self.window.title("Create New Recipe")
        
        # ضبط أبعاد النافذة لتكون متجاوبة
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.82)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.configure(bg="#f0f0f0")
        
        # السماح بالتكبير والتصغير وإظهار أزرار التحكم
        self.window.resizable(True, True)
        self.window.minsize(980, 620)

        # Keep it as a normal top-level window so Windows title-bar controls
        # (Close / Restore / Minimize) remain fully available.

        # متغيرات
        self.selected_colors: List[Dict] = []
        self.recipe_code_var = tk.StringVar()
        self.recipe_name_var = tk.StringVar()

        # متغيرات البحث لكل تبويب
        self.search_code_var_ind = tk.StringVar()
        self.search_name_var_ind = tk.StringVar()
        self.search_code_var_rea = tk.StringVar()
        self.search_name_var_rea = tk.StringVar()

        # تهيئة الأنماط
        self.configure_styles()

        # إنشاء الواجهة
        self.setup_ui()

        # تحميل الألوان المتاحة
        self.load_available_colors()

    def configure_styles(self):
        """تكوين أنماط الواجهة"""
        style = ttk.Style(self.window)
        style.configure('Sub.TButton',
                        font=('Arial', 10, 'bold'),
                        padding=6,
                        background='#3498DB',
                        foreground='white')
        style.map('Sub.TButton',
                  background=[('active', '#2980B9')])

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # إطار معلومات الوصفة
        info_frame = ttk.LabelFrame(self.window, text="Recipe Information", padding=8)
        info_frame.pack(fill=tk.X, padx=10, pady=3)

        # كود الوصفة
        ttk.Label(info_frame, text="Recipe Code* (6 digits):").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.code_entry = ttk.Entry(info_frame, textvariable=self.recipe_code_var, width=18)
        self.code_entry.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.code_entry.focus()

        # التحقق من صحة الإدخال
        self.code_entry.configure(
            validate='key',
            validatecommand=(self.window.register(self.validate_recipe_code_input), '%P')
        )

        # اسم الوصفة
        ttk.Label(info_frame, text="Recipe Name*:").grid(row=0, column=2, padx=5, pady=3, sticky="e")
        name_entry = ttk.Entry(info_frame, textvariable=self.recipe_name_var, width=35)
        name_entry.grid(row=0, column=3, padx=5, pady=3, sticky="w")

        # ======== التعديل الأساسي: تبويبات الألوان ========
        # إنشاء Notebook للتبويبات
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=3)

        # ====== تبويب INDANTHREN ======
        indanthren_frame = ttk.Frame(notebook, padding=5)
        notebook.add(indanthren_frame, text="INDANTHREN")

        # إطار البحث في تبويب Indanthren
        search_frame_ind = ttk.LabelFrame(indanthren_frame, text="Search INDANTHREN Colors", padding=8)
        search_frame_ind.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(search_frame_ind, text="Search by Code:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.search_code_entry_ind = ttk.Entry(search_frame_ind, textvariable=self.search_code_var_ind, width=15)
        self.search_code_entry_ind.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.search_code_entry_ind.bind('<Return>', lambda e: self.perform_search_ind())

        ttk.Label(search_frame_ind, text="Search by Name:").grid(row=0, column=2, padx=5, pady=3, sticky="e")
        self.search_name_entry_ind = ttk.Entry(search_frame_ind, textvariable=self.search_name_var_ind, width=25)
        self.search_name_entry_ind.grid(row=0, column=3, padx=5, pady=3, sticky="w")
        self.search_name_entry_ind.bind('<Return>', lambda e: self.perform_search_ind())

        ttk.Button(search_frame_ind, text="Search",
                   command=self.perform_search_ind, width=12, style='Sub.TButton').grid(row=0, column=4, padx=5, pady=3)
        ttk.Button(search_frame_ind, text="Reset",
                   command=self.reset_search_ind, width=10, style='Sub.TButton').grid(row=0, column=5, padx=5, pady=3)

        # شجرة ألوان Indanthren
        self.indanthren_tree = ttk.Treeview(
            indanthren_frame,
            columns=("code", "name", "dye_type", "price"),
            show="headings",
            height=10
        )

        self.indanthren_tree.heading("code", text="Color Code")
        self.indanthren_tree.heading("name", text="Color Name")
        self.indanthren_tree.heading("dye_type", text="Type")
        self.indanthren_tree.heading("price", text="Price/kg")

        self.indanthren_tree.column("code", width=90, anchor="center")
        self.indanthren_tree.column("name", width=180, anchor="center")
        self.indanthren_tree.column("dye_type", width=90, anchor="center")
        self.indanthren_tree.column("price", width=70, anchor="center")

        scrollbar_ind = ttk.Scrollbar(indanthren_frame, orient="vertical", command=self.indanthren_tree.yview)
        self.indanthren_tree.configure(yscrollcommand=scrollbar_ind.set)
        scrollbar_ind.pack(side=tk.RIGHT, fill=tk.Y)
        self.indanthren_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.indanthren_tree.bind("<Double-1>", lambda e: self.on_color_double_click("indanthren"))

        # ====== تبويب REATTIVI ======
        reattivi_frame = ttk.Frame(notebook, padding=5)
        notebook.add(reattivi_frame, text="REATTIVI")

        # إطار البحث في تبويب Reattivi
        search_frame_rea = ttk.LabelFrame(reattivi_frame, text="Search REATTIVI Colors", padding=8)
        search_frame_rea.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(search_frame_rea, text="Search by Code:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.search_code_entry_rea = ttk.Entry(search_frame_rea, textvariable=self.search_code_var_rea, width=15)
        self.search_code_entry_rea.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.search_code_entry_rea.bind('<Return>', lambda e: self.perform_search_rea())

        ttk.Label(search_frame_rea, text="Search by Name:").grid(row=0, column=2, padx=5, pady=3, sticky="e")
        self.search_name_entry_rea = ttk.Entry(search_frame_rea, textvariable=self.search_name_var_rea, width=25)
        self.search_name_entry_rea.grid(row=0, column=3, padx=5, pady=3, sticky="w")
        self.search_name_entry_rea.bind('<Return>', lambda e: self.perform_search_rea())

        ttk.Button(search_frame_rea, text="Search",
                   command=self.perform_search_rea, width=12, style='Sub.TButton').grid(row=0, column=4, padx=5, pady=3)
        ttk.Button(search_frame_rea, text="Reset",
                   command=self.reset_search_rea, width=10, style='Sub.TButton').grid(row=0, column=5, padx=5, pady=3)

        # شجرة ألوان Reattivi
        self.reattivi_tree = ttk.Treeview(
            reattivi_frame,
            columns=("code", "name", "dye_type", "price"),
            show="headings",
            height=10
        )

        self.reattivi_tree.heading("code", text="Color Code")
        self.reattivi_tree.heading("name", text="Color Name")
        self.reattivi_tree.heading("dye_type", text="Type")
        self.reattivi_tree.heading("price", text="Price/kg")

        self.reattivi_tree.column("code", width=90, anchor="center")
        self.reattivi_tree.column("name", width=180, anchor="center")
        self.reattivi_tree.column("dye_type", width=90, anchor="center")
        self.reattivi_tree.column("price", width=70, anchor="center")

        scrollbar_rea = ttk.Scrollbar(reattivi_frame, orient="vertical", command=self.reattivi_tree.yview)
        self.reattivi_tree.configure(yscrollcommand=scrollbar_rea.set)
        scrollbar_rea.pack(side=tk.RIGHT, fill=tk.Y)
        self.reattivi_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.reattivi_tree.bind("<Double-1>", lambda e: self.on_color_double_click("reattivi"))

        # ======== باقي الواجهة كما هي ========
        # إطار التحكم في الإضافة
        control_frame = ttk.LabelFrame(self.window, text="Controls", padding=8)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=3)

        # حقل النسبة المئوية
        ttk.Label(control_frame, text="Percentage (%):").pack(pady=3)
        self.percentage_entry = ttk.Entry(control_frame, width=8)
        self.percentage_entry.pack(pady=3)
        self.percentage_entry.bind('<Return>', lambda e: self.add_selected_color())

        # زر الإضافة
        ttk.Button(control_frame, text="Add Color", command=self.add_selected_color, width=12, style='Sub.TButton').pack(pady=5)

        # زر الحذف
        ttk.Button(control_frame, text="Remove Selected", command=self.remove_selected_color, width=12, style='Sub.TButton').pack(pady=3)

        # إطار الألوان المضافة
        selected_frame = ttk.LabelFrame(self.window, text="Added Colors", padding=8)
        selected_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=3)

        # شجرة الألوان المضافة
        self.selected_tree = ttk.Treeview(
            selected_frame,
            columns=("code", "name", "dye_type", "percentage", "cost"),
            show="headings",
            height=10
        )

        self.selected_tree.heading("code", text="Color Code")
        self.selected_tree.heading("name", text="Color Name")
        self.selected_tree.heading("dye_type", text="Type")
        self.selected_tree.heading("percentage", text="%")
        self.selected_tree.heading("cost", text="Cost €")

        self.selected_tree.column("code", width=90, anchor="center")
        self.selected_tree.column("name", width=180, anchor="center")
        self.selected_tree.column("dye_type", width=90, anchor="center")
        self.selected_tree.column("percentage", width=60, anchor="center")
        self.selected_tree.column("cost", width=70, anchor="center")

        # شريط التمرير
        scrollbar_selected = ttk.Scrollbar(selected_frame, orient="vertical", command=self.selected_tree.yview)
        self.selected_tree.configure(yscrollcommand=scrollbar_selected.set)
        scrollbar_selected.pack(side=tk.RIGHT, fill=tk.Y)
        self.selected_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # إطار معلومات سريعة
        quick_info_frame = ttk.LabelFrame(self.window, text="Quick Info", padding=8)
        quick_info_frame.pack(fill=tk.X, padx=10, pady=3)

        quick_row = ttk.Frame(quick_info_frame)
        quick_row.pack(fill=tk.X, pady=2)

        ttk.Label(quick_row, text="Colors:").pack(side=tk.LEFT, padx=5)
        self.colors_count_label = ttk.Label(quick_row, text="0", font=('Arial', 9, 'bold'), foreground="blue")
        self.colors_count_label.pack(side=tk.LEFT, padx=2)

        ttk.Label(quick_row, text="Total %:").pack(side=tk.LEFT, padx=10)
        self.percentage_label = ttk.Label(quick_row, text="0.00%", font=('Arial', 9, 'bold'), foreground="green")
        self.percentage_label.pack(side=tk.LEFT, padx=2)

        ttk.Label(quick_row, text="Cost:").pack(side=tk.LEFT, padx=10)
        self.cost_label = ttk.Label(quick_row, text="€0.00", font=('Arial', 9, 'bold'), foreground="red")
        self.cost_label.pack(side=tk.LEFT, padx=2)

        ttk.Label(quick_row, text="Type:").pack(side=tk.LEFT, padx=10)
        self.type_label = ttk.Label(quick_row, text="None", font=('Arial', 9, 'bold'), foreground="purple")
        self.type_label.pack(side=tk.LEFT, padx=2)

        # إطار الكيماويات
        chemicals_frame = ttk.LabelFrame(self.window, text="Required Chemicals", padding=8)
        chemicals_frame.pack(fill=tk.X, padx=10, pady=3)

        # ✅ زيادة الارتفاع من 2 إلى 6 لرؤية جميع الكيماويات
        self.chemicals_text = tk.Text(chemicals_frame, height=6, wrap=tk.WORD, font=('Arial', 10))
        self.chemicals_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)  # ✅ fill=tk.BOTH, expand=True
        self.chemicals_text.insert(tk.END, "No chemicals calculated yet. Add colors to the recipe.")
        self.chemicals_text.config(state='disabled')

        # أزرار التحكم
        button_frame = ttk.LabelFrame(self.window, text="Actions", padding=8)
        button_frame.pack(fill=tk.X, padx=10, pady=5, side=tk.BOTTOM)

        button_row = ttk.Frame(button_frame)
        button_row.pack(fill=tk.X, pady=5)

        ttk.Button(button_row, text="Save Recipe Only",
                   command=self.save_recipe_only,
                   width=20, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(button_row, text="Save & Export PDF",
                   command=self.save_and_export,
                   width=20, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(button_row, text="Show Chemicals",
                   command=self.show_chemicals_details,
                   width=20, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(button_row, text="Clear All Colors",
                   command=self.clear_all_colors,
                   width=18, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(button_row, text="Close Window",
                   command=self.window.destroy,
                   width=15, style='Sub.TButton').pack(side=tk.RIGHT, padx=5)

    def validate_recipe_code_input(self, value):
        """التحقق من صحة إدخال كود الوصفة"""
        if value == '':
            return True
        return value.isdigit() and len(value) <= 6

    def load_available_colors(self):
        """تحميل الألوان المتاحة"""
        try:
            colors = self.db.get_all_colors()

            # تفريغ القوائم
            self.indanthren_colors.clear()
            self.reattivi_colors.clear()

            for color in colors:
                # استخراج بيانات اللون
                color_data = self.extract_color_data(color)
                if not color_data:
                    continue

                dye_type_upper = color_data["dye_type"].upper()

                # توزيع حسب النوع
                if "INDANTHREN" in dye_type_upper:
                    self.indanthren_colors.append(color_data)
                else:
                    # كل ما عدا Indanthren => Reattivi
                    self.reattivi_colors.append(color_data)

            # عرض الألوان في التبويباتz
            self.display_colors(self.indanthren_tree, self.indanthren_colors)
            self.display_colors(self.reattivi_tree, self.reattivi_colors)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load colors: {str(e)}", parent=self.window)
            # بيانات تجريبية
            self.load_sample_data()

    def extract_color_data(self, color):
        """استخراج بيانات اللون"""
        try:
            if hasattr(color, '__dict__'):
                # كائن
                return {
                    "code": getattr(color, 'code', ''),
                    "name": getattr(color, 'name', ''),
                    "dye_type": getattr(color, 'dye_type', ''),
                    "price_kg": float(getattr(color, 'price_kg', 0))
                }
            elif isinstance(color, dict):
                # قاموس
                return {
                    "code": color.get('code', ''),
                    "name": color.get('name', ''),
                    "dye_type": color.get('dye_type', ''),
                    "price_kg": float(color.get('price_kg', 0))
                }
            else:
                # tuple/list
                return {
                    "code": str(color[0]) if len(color) > 0 else '',
                    "name": str(color[1]) if len(color) > 1 else '',
                    "dye_type": str(color[2]) if len(color) > 2 else '',
                    "price_kg": float(color[3]) if len(color) > 3 else 0.0
                }
        except:
            return None

    def display_colors(self, tree, colors):
        """عرض الألوان في شجرة محددة"""
        for item in tree.get_children():
            tree.delete(item)

        for color in colors:
            tree.insert("", tk.END, values=(
                color["code"],
                color["name"],
                color["dye_type"],
                f"€{color['price_kg']:.2f}"
            ))

    def perform_search_ind(self):
        """بحث في تبويب Indanthren"""
        if not self.indanthren_colors:
            messagebox.showinfo("Info", "No Indanthren colors available", parent=self.window)
            return

        code_search = self.search_code_var_ind.get().strip().upper()
        name_search = self.search_name_var_ind.get().strip().lower()

        if not code_search and not name_search:
            self.display_colors(self.indanthren_tree, self.indanthren_colors)
            return

        filtered = []
        for color in self.indanthren_colors:
            code_match = code_search in color["code"].upper() if code_search else True
            name_match = name_search in color["name"].lower() if name_search else True

            if code_match and name_match:
                filtered.append(color)

        if filtered:
            self.display_colors(self.indanthren_tree, filtered)
        else:
            messagebox.showinfo("Search Result", "No colors found matching your search criteria", parent=self.window)
            self.display_colors(self.indanthren_tree, [])

    def perform_search_rea(self):
        """بحث في تبويب Reattivi"""
        if not self.reattivi_colors:
            messagebox.showinfo("Info", "No Reattivi colors available", parent=self.window)
            return

        code_search = self.search_code_var_rea.get().strip().upper()
        name_search = self.search_name_var_rea.get().strip().lower()

        if not code_search and not name_search:
            self.display_colors(self.reattivi_tree, self.reattivi_colors)
            return

        filtered = []
        for color in self.reattivi_colors:
            code_match = code_search in color["code"].upper() if code_search else True
            name_match = name_search in color["name"].lower() if name_search else True

            if code_match and name_match:
                filtered.append(color)

        if filtered:
            self.display_colors(self.reattivi_tree, filtered)
        else:
            messagebox.showinfo("Search Result", "No colors found matching your search criteria", parent=self.window)
            self.display_colors(self.reattivi_tree, [])

    def reset_search_ind(self):
        """مسح بحث Indanthren"""
        self.search_code_var_ind.set("")
        self.search_name_var_ind.set("")
        self.display_colors(self.indanthren_tree, self.indanthren_colors)
        self.search_code_entry_ind.focus()

    def reset_search_rea(self):
        """مسح بحث Reattivi"""
        self.search_code_var_rea.set("")
        self.search_name_var_rea.set("")
        self.display_colors(self.reattivi_tree, self.reattivi_colors)
        self.search_code_entry_rea.focus()

    def on_color_double_click(self, tab_name):
        """عند النقر المزدوج على لون"""
        if tab_name == "indanthren":
            tree = self.indanthren_tree
            colors_list = self.indanthren_colors
        else:
            tree = self.reattivi_tree
            colors_list = self.reattivi_colors

        selected = tree.selection()
        if not selected:
            return

        color_data = tree.item(selected[0], "values")

        # نافذة الإدخال
        input_win = tk.Toplevel(self.window)
        _show_on_top(input_win, self.window)
        input_win.title(f"Add {color_data[0]}")
        input_win.geometry("300x150")
        input_win.grab_set()

        ttk.Label(input_win, text=f"Color: {color_data[0]} - {color_data[1]}",
                  font=('Arial', 10, 'bold')).pack(pady=10)

        ttk.Label(input_win, text="Enter Percentage (%):").pack()

        percentage_var = tk.StringVar()
        entry = ttk.Entry(input_win, textvariable=percentage_var, width=10)
        entry.pack(pady=5)
        entry.focus()

        def add_with_percentage():
            try:
                percentage = float(percentage_var.get())
                if percentage <= 0:
                    raise ValueError

                self.add_color_to_recipe(color_data, percentage)  # ✅ ستستدعي update_chemicals تلقائياً
                input_win.destroy()
                # لا حاجة لاستدعاء update_chemicals هنا

            except ValueError:
                messagebox.showwarning("Error", "Please enter a valid percentage greater than zero", parent=input_win)

        entry.bind('<Return>', lambda e: add_with_percentage())

        button_frame = ttk.Frame(input_win)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Add", command=add_with_percentage).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=input_win.destroy).pack(side=tk.LEFT, padx=5)

    def add_selected_color(self):
        """إضافة اللون المحدد"""
        active_tree = None

        if self.indanthren_tree.selection():
            active_tree = self.indanthren_tree
        elif self.reattivi_tree.selection():
            active_tree = self.reattivi_tree

        if not active_tree:
            messagebox.showwarning("Warning", "Please select a color from the list", parent=self.window)
            return

        try:
            percentage = float(self.percentage_entry.get())
            if percentage <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Error", "Please enter a valid percentage greater than zero", parent=self.window)
            return

        color_data = active_tree.item(active_tree.selection()[0], "values")
        self.add_color_to_recipe(color_data, percentage)  # ✅ ستستدعي update_chemicals تلقائياً

        self.percentage_entry.delete(0, tk.END)

    def add_color_to_recipe(self, color_data, percentage):
        """إضافة لون إلى الوصفة"""
        # التحقق من التوافق بين أنواع الصباغة
        new_dye_type = color_data[2]
        
        # فحص إذا كانت هناك ألوان مضافة بالفعل
        if self.selected_colors:
            # الحصول على نوع الصباغة الأول المضاف
            first_dye_type = self.selected_colors[0]["dye_type"]
            
            # التحقق من عدم خلط Indanthren مع Reattivi
            is_new_indanthren = "INDANTHREN" in new_dye_type.upper()
            is_first_indanthren = "INDANTHREN" in first_dye_type.upper()
            
            if is_new_indanthren != is_first_indanthren:
                messagebox.showerror(
                    "Incompatible Dye Types",
                    "Cannot mix INDANTHREN colors with REATTIVI colors in the same recipe.\n\n"
                    f"Current recipe uses: {first_dye_type}\n"
                    f"Trying to add: {new_dye_type}\n\n"
                    "Please create a separate recipe for different dye types.",
                    parent=self.window
                )
                return
        
        price_text = color_data[3].replace('€', '').strip()
        try:
            price = float(price_text)
        except:
            price = 0.0

        self.selected_colors.append({
            "code": color_data[0],
            "name": color_data[1],
            "dye_type": color_data[2],
            "price_kg": price,
            "percentage": percentage
        })

        self.update_selected_tree()
        # تحديث المعلومات والكيماويات تلقائياً
        self.update_quick_info()
        self.update_chemicals()  # ✅ هذا مهم جداً

    def update_selected_tree(self):
        """تحديث شجرة الألوان المضافة"""
        for item in self.selected_tree.get_children():
            self.selected_tree.delete(item)

        for color in self.selected_colors:
            color_cost = (color["percentage"] / 100) * color.get("price_kg", 0)
            self.selected_tree.insert("", tk.END, values=(
                color["code"],
                color["name"],
                color["dye_type"],
                f"{color['percentage']:.2f}",
                f"€{color_cost:.2f}"
            ), tags=(color["code"],))

    def remove_selected_color(self):
        """إزالة اللون المحدد من الوصفة"""
        selected = self.selected_tree.selection()
        if not selected:
            return

        item_values = self.selected_tree.item(selected[0], "values")
        if not item_values:
            return

        color_code = item_values[0]

        for i, color in enumerate(self.selected_colors):
            if color["code"] == color_code:
                self.selected_colors.pop(i)
                break

        self.update_selected_tree()
        self.update_quick_info()
        self.update_chemicals()  # ✅ تحديث الكيماويات تلقائياً بعد الحذف

    def clear_all_colors(self):
        """مسح جميع الألوان"""
        if not self.selected_colors:
            return

        confirm = messagebox.askyesno("Confirm", "Are you sure you want to remove all colors from the recipe?", parent=self.window)
        if confirm:
            self.selected_colors.clear()
            self.update_selected_tree()
            self.update_quick_info()
            self.update_chemicals()  # ✅ تحديث الكيماويات تلقائياً بعد المسح

    def update_quick_info(self):
        """تحديث المعلومات السريعة"""
        colors_count = len(self.selected_colors)
        total_percentage = sum(color["percentage"] for color in self.selected_colors)
        total_cost = CostCalculator.calculate_recipe_cost(self.selected_colors)

        self.colors_count_label.config(text=str(colors_count))
        self.percentage_label.config(text=f"{total_percentage:.2f}%")
        self.cost_label.config(text=f"€{total_cost:.2f}")
        self.update_chemicals()

        type_counts = {}
        for color in self.selected_colors:
            dye_type = color["dye_type"]
            type_counts[dye_type] = type_counts.get(dye_type, 0) + 1

        if type_counts:
            dominant_type = max(type_counts, key=type_counts.get)
            self.type_label.config(text=dominant_type)
        else:
            self.type_label.config(text="None")

    def update_chemicals(self):
        """تحديث عرض الكيماويات في frame required chemicals"""
        if not self.selected_colors:
            self.chemicals_text.config(state='normal')
            self.chemicals_text.delete(1.0, tk.END)
            self.chemicals_text.insert(tk.END, "No chemicals calculated yet. Add colors to the recipe.")
            self.chemicals_text.config(state='disabled')
            return

        total_percentage = sum(color["percentage"] for color in self.selected_colors)

        # تحديد نوع الصباغة المهيمن
        type_totals = {}
        for color in self.selected_colors:
            dye_type = color["dye_type"]
            type_totals[dye_type] = type_totals.get(dye_type, 0) + color["percentage"]

        if not type_totals:
            self.chemicals_text.config(state='normal')
            self.chemicals_text.delete(1.0, tk.END)
            self.chemicals_text.insert(tk.END, "No dye types found")
            self.chemicals_text.config(state='disabled')
            return

        dominant_type = max(type_totals, key=type_totals.get)

        try:
            # حساب الكيماويات
            chemicals = ChemicalCalculator.calculate_chemicals(total_percentage, dominant_type)

            self.chemicals_text.config(state='normal')
            self.chemicals_text.delete(1.0, tk.END)

            if not chemicals:
                self.chemicals_text.insert(tk.END, f"No chemicals calculated for {dominant_type} type")
                self.chemicals_text.config(state='disabled')
                return

            # بناء نص الكيماويات مع التفاصيل الكاملة
            chemicals_text = f"🧪 Chemicals for {total_percentage:.2f}% ({dominant_type}):\n"
            chemicals_text += "=" * 50 + "\n\n"

            for i, chemical in enumerate(chemicals, 1):
                chemicals_text += f"{i}. [{chemical.code}] {chemical.name}: {chemical.quantity} {chemical.unit}\n"

            chemicals_text += "\n" + "=" * 50
            chemicals_text += "\n📝 Note: Quantities are per liter of dye bath"

            self.chemicals_text.insert(tk.END, chemicals_text)
            self.chemicals_text.config(state='disabled')

        except Exception as e:
            self.chemicals_text.config(state='normal')
            self.chemicals_text.delete(1.0, tk.END)
            error_text = f"⚠️ Error calculating chemicals!\n\n"
            error_text += f"Error: {str(e)}\n"
            error_text += f"Total Percentage: {total_percentage:.2f}%\n"
            error_text += f"Dominant Type: {dominant_type}\n\n"
            error_text += "Please check the calculator module."
            self.chemicals_text.insert(tk.END, error_text)
            self.chemicals_text.config(state='disabled')

    def calculate_and_show_chemicals(self):
        """حساب وعرض الكيماويات مباشرة"""
        if not self.selected_colors:
            return

        total_percentage = sum(color["percentage"] for color in self.selected_colors)

        # تحديد نوع الصبغة الأكثر استخداماً
        type_counts = {}
        for color in self.selected_colors:
            dye_type = color["dye_type"]
            type_counts[dye_type] = type_counts.get(dye_type, 0) + 1

        if type_counts:
            # الحصول على النوع الأكثر تكراراً
            dominant_type = max(type_counts, key=type_counts.get)

            try:
                # حساب الكيماويات
                chemicals = ChemicalCalculator.calculate_chemicals(total_percentage, dominant_type)

                # تحديث عرض الكيماويات
                self.chemicals_text.config(state='normal')
                self.chemicals_text.delete(1.0, tk.END)

                chem_text = f"Chemicals for {total_percentage:.2f}% ({dominant_type}): "
                details = []
                for chem in chemicals:
                    details.append(f"[{chem.code}] {chem.name}: {chem.quantity} {chem.unit}")

                chem_text += " | ".join(details)
                self.chemicals_text.insert(tk.END, chem_text)
                self.chemicals_text.config(state='disabled')

            except Exception as e:
                self.chemicals_text.config(state='normal')
                self.chemicals_text.delete(1.0, tk.END)
                self.chemicals_text.insert(tk.END, f"Error calculating chemicals: {str(e)}")
                self.chemicals_text.config(state='disabled')
                self.update_chemicals()

    def validate_inputs(self):
        """التحقق من صحة المدخلات"""
        recipe_code = self.recipe_code_var.get().strip()
        if not recipe_code:
            messagebox.showwarning("Warning", "Please enter a recipe code", parent=self.window)
            self.code_entry.focus()
            return False

        cleaned_code = clean_recipe_code(recipe_code)
        is_valid, message = validate_recipe_code_input(cleaned_code)
        if not is_valid:
            messagebox.showwarning("Warning", message, parent=self.window)
            self.code_entry.focus()
            return False

        recipe_name = self.recipe_name_var.get().strip()
        if not recipe_name:
            messagebox.showwarning("Warning", "Please enter a recipe name", parent=self.window)
            return False

        if not self.selected_colors:
            messagebox.showwarning("Warning", "Recipe must contain at least one color", parent=self.window)
            return False

        return True

    def save_recipe_only(self):
        """حفظ الوصفة فقط"""
        if not self.validate_inputs():
            return

        try:
            recipe_code = clean_recipe_code(self.recipe_code_var.get().strip())
            recipe_name = self.recipe_name_var.get().strip()

            recipe = Recipe(
                id=0,
                recipe_code=recipe_code,
                name=recipe_name,
                created_at=get_current_timestamp()
            )

            # حساب الكيماويات
            total_percentage = sum(c.get('percentage', 0) for c in self.selected_colors)
            type_totals = {}
            for color in self.selected_colors:
                dye_type = color.get('dye_type', '')
                type_totals[dye_type] = type_totals.get(dye_type, 0) + color.get('percentage', 0)
            dominant_type = max(type_totals, key=type_totals.get) if type_totals else 'GENERAL'
            
            from app.calculator import ChemicalCalculator
            chemicals = ChemicalCalculator.calculate_chemicals(total_percentage, dominant_type)

            recipe_id = self.db.add_recipe(recipe, self.selected_colors, chemicals)

            messagebox.showinfo("✅ Success", f"Recipe saved successfully!\nRecipe ID: {recipe_id}", parent=self.window)
            self.window.destroy()

            if hasattr(self.parent, 'load_data'):
                self.parent.load_data()

        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to save recipe: {str(e)}", parent=self.window)

    def save_and_export(self):
        """حفظ الوصفة وتصديرها إلى PDF"""
        if not self.validate_inputs():
            return

        try:
            recipe_code = clean_recipe_code(self.recipe_code_var.get().strip())
            recipe_name = self.recipe_name_var.get().strip()

            recipe = Recipe(
                id=0,
                recipe_code=recipe_code,
                name=recipe_name,
                created_at=get_current_timestamp()
            )

            from app.calculator import ChemicalCalculator
            recipe_details = ChemicalCalculator.calculate_recipe_details(recipe_name, self.selected_colors)
            
            # حفظ الكيماويات مع الوصفة
            recipe_id = self.db.add_recipe(recipe, self.selected_colors, recipe_details.chemicals)
            recipe.id = recipe_id
            recipe_details.recipe = recipe

            from app.pdf_exporter import PDFExporter
            pdf_path = PDFExporter.export_recipe_to_pdf(recipe_details, parent_window=self.window)

            if pdf_path:
                messagebox.showinfo("✅ Success",
                                    f"Recipe saved and exported successfully!\n"
                                    f"Recipe ID: {recipe_id}\n"
                                    f"📄 PDF saved to: {pdf_path}", parent=self.window)
            else:
                messagebox.showinfo("✅ Success", f"Recipe saved successfully! (ID: {recipe_id})", parent=self.window)

            self.window.destroy()

            if hasattr(self.parent, 'load_data'):
                self.parent.load_data()

        except Exception as e:
            messagebox.showerror("❌ Error", f"Failed to save recipe: {str(e)}", parent=self.window)

    def show_chemicals_details(self):
        """عرض تفاصيل الكيماويات في نافذة منفصلة"""
        if not self.selected_colors:
            messagebox.showwarning("Warning", "No colors added to calculate chemicals", parent=self.window)
            return

        total_percentage = sum(color["percentage"] for color in self.selected_colors)

        type_totals = {dye_type: 0 for dye_type in DYE_TYPES}
        for color in self.selected_colors:
            if color["dye_type"] in type_totals:
                type_totals[color["dye_type"]] += color["percentage"]

        dominant_type = max(type_totals, key=type_totals.get)
        chemicals = ChemicalCalculator.calculate_chemicals(total_percentage, dominant_type)

        chem_win = tk.Toplevel(self.window)
        _show_on_top(chem_win, self.window)
        chem_win.title("Chemical Requirements Details")
        chem_win.geometry("500x400")
        chem_win.configure(bg="#f0f0f0")
        chem_win.grab_set()

        ttk.Label(chem_win, text="🧪 Detailed Chemical Requirements",
                  font=('Arial', 14, 'bold')).pack(pady=10)

        recipe_name = self.recipe_name_var.get() or "Unnamed Recipe"
        recipe_code = self.recipe_code_var.get() or "No Code"

        info_text = f"Recipe: {recipe_code} - {recipe_name}\n"
        info_text += f"Total Percentage: {total_percentage:.2f}%\n"
        info_text += f"Dominant Dye Type: {dominant_type}\n"

        ttk.Label(chem_win, text=info_text, font=('Arial', 10)).pack(pady=5)

        chem_frame = ttk.LabelFrame(chem_win, text="Required Chemicals per Liter", padding=15)
        chem_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for i, chemical in enumerate(chemicals, 1):
            chem_row = ttk.Frame(chem_frame)
            chem_row.pack(fill=tk.X, pady=5)

            ttk.Label(chem_row, text=f"{i}.", width=3, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
            ttk.Label(chem_row, text=chemical.name, width=20,
                      font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
            ttk.Label(chem_row, text=f"{chemical.quantity} {chemical.unit}",
                      font=('Arial', 10)).pack(side=tk.LEFT)

        info_frame = ttk.LabelFrame(chem_win, text="Usage Notes", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        notes = """
        • These quantities are per liter of dye bath
        • Adjust based on fabric weight and liquor ratio
        • Always conduct lab tests before full production
        • Store chemicals in cool, dry places
        """

        ttk.Label(info_frame, text=notes, justify=tk.LEFT).pack()

        ttk.Button(chem_win, text="Close", command=chem_win.destroy).pack(pady=10)

    def load_sample_data(self):
        """تحميل بيانات تجريبية"""
        # ألوان Indanthren
        indanthren_samples = [
            {"code": "IN-001", "name": "Indanthren Blue", "dye_type": "INDANTHREN", "price_kg": 45.50},
            {"code": "IN-002", "name": "Indanthren Red", "dye_type": "INDANTHREN", "price_kg": 52.30},
            {"code": "IN-003", "name": "Indanthren Green", "dye_type": "INDANTHREN", "price_kg": 48.75},
            {"code": "IN-004", "name": "Indanthren Yellow", "dye_type": "INDANTHREN", "price_kg": 55.20},
            {"code": "IN-005", "name": "Indanthren Black", "dye_type": "INDANTHREN", "price_kg": 40.90},
        ]

        # ألوان Reattivi
        reattivi_samples = [
            {"code": "RC-101", "name": "Reattivi Caldi Red", "dye_type": "REATTIVI CALDI", "price_kg": 38.50},
            {"code": "RC-102", "name": "Reattivi Caldi Blue", "dye_type": "REATTIVI CALDI", "price_kg": 42.30},
            {"code": "RF-201", "name": "Reattivi Freddi Yellow", "dye_type": "REATTIVI FREDDI", "price_kg": 35.75},
            {"code": "RF-202", "name": "Reattivi Freddi Green", "dye_type": "REATTIVI FREDDI", "price_kg": 39.20},
            {"code": "OT-301", "name": "Other Reactive Orange", "dye_type": "OTHER", "price_kg": 32.90},
            {"code": "OT-302", "name": "Other Direct Purple", "dye_type": "OTHER", "price_kg": 37.40},
        ]

        self.indanthren_colors = indanthren_samples
        self.reattivi_colors = reattivi_samples

        self.display_colors(self.indanthren_tree, indanthren_samples)
        self.display_colors(self.reattivi_tree, reattivi_samples)
