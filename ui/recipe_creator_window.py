"""
نافذة إنشاء وصفة جديدة
"""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict

from app.database import DatabaseManager
from app.session import SessionManager
from app.calculator import ChemicalCalculator, CostCalculator
from app.utils import clean_recipe_code, validate_recipe_code_input, get_current_timestamp
from app.models import Recipe
from app.config import DYE_TYPES
from app.lab_settings import load_lab_settings, save_lab_settings
from ui.theme_tokens import configure_sub_button_style, setup_tree_tags, zebra_insert, get_theme_tokens, apply_excel_treeview_style, show_on_top





class RecipeCreatorWindow:
    """نافذة إنشاء وصفة جديدة"""

    def __init__(self, parent, db: DatabaseManager, dark_mode: bool = False):
        self.parent = parent
        self.db = db
        self.session = SessionManager.get_session()
        self.dark_mode = dark_mode
        self.indanthren_colors = []  # تخزين ألوان Indanthren
        self.reattivi_colors = []  # تخزين ألوان Reattivi (Caldi + Freddi + Other)

        self.window = tk.Toplevel(parent)
        show_on_top(self.window, parent)
        self.window.title("Create New Recipe")
        
        # ضبط أبعاد النافذة لتكون متجاوبة مع حد أدنى معقول
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        # Ensure minimum screen dimensions
        screen_width = max(screen_width, 1024)
        screen_height = max(screen_height, 768)
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.88)
        # Apply bounds
        width = max(980, width)
        height = max(780, height)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.configure(bg=get_theme_tokens(self.dark_mode)["bg"])
        
        # السماح بالتكبير والتصغير وإظهار أزرار التحكم
        self.window.resizable(True, True)
        self.window.minsize(980, 780)

        # Keep it as a normal top-level window so Windows title-bar controls
        # (Close / Restore / Minimize) remain fully available.

        # متغيرات
        self.selected_colors: List[Dict] = []
        self._tree_sort_state = {}
        self.recipe_code_var = tk.StringVar()
        self.recipe_name_var = tk.StringVar()
        current_lab = load_lab_settings()
        self.lab_peso_var = tk.StringVar(value=f"{current_lab['sample_g']:.2f}")
        self.lab_volume_var = tk.StringVar(value=f"{current_lab['volume_ml']:.2f}")
        self.lab_rapporto_var = tk.StringVar(value="")

        # متغيرات البحث لكل تبويب
        self.search_code_var_ind = tk.StringVar()
        self.search_name_var_ind = tk.StringVar()
        self.search_code_var_rea = tk.StringVar()
        self.search_name_var_rea = tk.StringVar()

        # تهيئة الأنماط
        self.configure_styles()

        # إنشاء الواجهة
        self.setup_ui()
        self._lab_settings_bind_id = self.parent.bind(
            "<<LabSettingsChanged>>",
            self._on_lab_settings_changed,
            add="+",
        )
        self.window.bind("<Destroy>", self._on_window_destroy, add="+")

        # تحميل الألوان المتاحة
        self.load_available_colors()

    def _on_window_destroy(self, event=None):
        """Cleanup global bindings when this window is closed."""
        if event is not None and getattr(event, "widget", None) is not self.window:
            return
        try:
            if getattr(self, "_lab_settings_bind_id", None):
                self.parent.unbind("<<LabSettingsChanged>>", self._lab_settings_bind_id)
                self._lab_settings_bind_id = None
        except Exception:
            pass

    def configure_styles(self):
        """تكوين أنماط الواجهة"""
        style = ttk.Style(self.window)
        palette = get_theme_tokens(self.dark_mode)
        apply_excel_treeview_style(style, palette, self.dark_mode)
        configure_sub_button_style(style, 'Sub.TButton', palette)

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # إطار معلومات الوصفة
        info_frame = ttk.LabelFrame(self.window, text="Recipe Information", padding=2)
        info_frame.pack(fill=tk.X, padx=10, pady=0)

        # كود الوصفة
        ttk.Label(info_frame, text="Recipe Code* (6 digits):").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.code_entry = ttk.Entry(info_frame, textvariable=self.recipe_code_var, width=18)
        self.code_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.code_entry.focus()

        # التحقق من صحة الإدخال
        self.code_entry.configure(
            validate='key',
            validatecommand=(self.window.register(self.validate_recipe_code_input), '%P')
        )

        # اسم الوصفة
        ttk.Label(info_frame, text="Recipe Name*:").grid(row=0, column=2, padx=5, pady=2, sticky="e")
        name_entry = ttk.Entry(info_frame, textvariable=self.recipe_name_var, width=35)
        name_entry.grid(row=0, column=3, padx=5, pady=2, sticky="w")

        ttk.Separator(info_frame, orient=tk.VERTICAL).grid(row=0, column=4, sticky="ns", padx=12)
        ttk.Label(info_frame, text="Peso (g):").grid(row=0, column=5, padx=(4, 2), pady=2, sticky="e")
        self.lab_peso_entry = ttk.Entry(info_frame, textvariable=self.lab_peso_var, width=8)
        self.lab_peso_entry.grid(row=0, column=6, padx=2, pady=2, sticky="w")

        ttk.Label(info_frame, text="Volume (ml):").grid(row=0, column=7, padx=(8, 2), pady=2, sticky="e")
        self.lab_volume_entry = ttk.Entry(info_frame, textvariable=self.lab_volume_var, width=8)
        self.lab_volume_entry.grid(row=0, column=8, padx=2, pady=2, sticky="w")

        ttk.Label(info_frame, text="Rapporto Bagno:").grid(row=0, column=9, padx=(8, 2), pady=2, sticky="e")
        lab_rapporto_entry = ttk.Entry(info_frame, textvariable=self.lab_rapporto_var, width=10, state="readonly")
        lab_rapporto_entry.grid(row=0, column=10, padx=2, pady=2, sticky="w")

        self.lab_save_btn = ttk.Button(
            info_frame,
            text="Save Changes",
            command=self._save_lab_settings_changes,
            width=12,
            style='Sub.TButton'
        )
        self.lab_save_btn.grid(row=0, column=11, padx=(10, 2), pady=2, sticky="w")

        self.lab_peso_entry.bind("<KeyRelease>", lambda _e: self._update_lab_rapporto())
        self.lab_volume_entry.bind("<KeyRelease>", lambda _e: self._update_lab_rapporto())
        self._update_lab_rapporto()
        if not self.session.has_permission("can_edit_lab_settings"):
            self.lab_peso_entry.configure(state="readonly")
            self.lab_volume_entry.configure(state="readonly")
            self.lab_save_btn.state(["disabled"])

        # ── أزرار التحكم — تُحزم قبل الـ notebook عشان تبقى دايمًا ظاهرة ──
        button_frame = ttk.LabelFrame(self.window, text="Actions", padding=8)
        button_frame.pack(fill=tk.X, padx=10, pady=(4, 6), side=tk.BOTTOM)

        button_row = ttk.Frame(button_frame)
        button_row.pack(fill=tk.X, pady=4)

        ttk.Button(button_row, text="💾  Save Recipe Only",
                   command=self.save_recipe_only,
                   width=22, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(button_row, text="📄  Save & Export PDF",
                   command=self.save_and_export,
                   width=22, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(button_row, text="🧪  Show Chemicals",
                   command=self.show_chemicals_details,
                   width=22, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(button_row, text="✖  Close Window",
                   command=self.window.destroy,
                   width=18, style='Sub.TButton').pack(side=tk.RIGHT, padx=5)

        # ======== التعديل الأساسي: تبويبات الألوان ========
        # إنشاء Notebook للتبويبات
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)

        # ====== تبويب INDANTHREN ======
        indanthren_frame = ttk.Frame(notebook, padding=5)
        notebook.add(indanthren_frame, text="INDANTHREN")

        # إطار البحث في تبويب Indanthren
        search_frame_ind = ttk.LabelFrame(indanthren_frame, text="INDANTHREN Filters", padding=3)
        search_frame_ind.pack(fill=tk.X, pady=(0, 2))

        ttk.Label(search_frame_ind, text="Code:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.search_code_entry_ind = ttk.Entry(search_frame_ind, textvariable=self.search_code_var_ind, width=15)
        self.search_code_entry_ind.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.search_code_entry_ind.bind('<KeyRelease>', lambda e: self.perform_search_ind())

        ttk.Label(search_frame_ind, text="Name:").grid(row=0, column=2, padx=5, pady=3, sticky="e")
        self.search_name_entry_ind = ttk.Entry(search_frame_ind, textvariable=self.search_name_var_ind, width=25)
        self.search_name_entry_ind.grid(row=0, column=3, padx=5, pady=3, sticky="w")
        self.search_name_entry_ind.bind('<KeyRelease>', lambda e: self.perform_search_ind())

        ttk.Button(search_frame_ind, text="Clear",
                   command=self.reset_search_ind, width=10, style='Sub.TButton').grid(row=0, column=4, padx=5, pady=3)

        # شجرة ألوان Indanthren
        self.indanthren_tree = ttk.Treeview(
            indanthren_frame,
            columns=("code", "name", "dye_type", "supplier", "price", "resa", "created"),
            show="headings",
            height=6
        )

        self.indanthren_tree.heading("code", text="Color Code")
        self.indanthren_tree.heading("name", text="Color Name")
        self.indanthren_tree.heading("dye_type", text="Type")
        self.indanthren_tree.heading("supplier", text="Supplier")
        self.indanthren_tree.heading("price", text="Price/kg")
        self.indanthren_tree.heading("resa", text="RESA %")
        self.indanthren_tree.heading("created", text="Create Date")

        self.indanthren_tree.column("code", width=90, anchor="center")
        self.indanthren_tree.column("name", width=150, anchor="center")
        self.indanthren_tree.column("dye_type", width=90, anchor="center")
        self.indanthren_tree.column("supplier", width=110, anchor="center")
        self.indanthren_tree.column("price", width=75, anchor="center")
        self.indanthren_tree.column("resa", width=70, anchor="center")
        self.indanthren_tree.column("created", width=95, anchor="center")

        scrollbar_ind = ttk.Scrollbar(indanthren_frame, orient="vertical", command=self.indanthren_tree.yview)
        self.indanthren_tree.configure(yscrollcommand=scrollbar_ind.set)
        scrollbar_ind.pack(side=tk.RIGHT, fill=tk.Y)
        self.indanthren_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.indanthren_tree.bind("<Double-1>", lambda e: self.on_color_double_click("indanthren"))
        self._setup_treeview_sorting(self.indanthren_tree)
        setup_tree_tags(self.indanthren_tree, self.dark_mode)

        # ====== تبويب REATTIVI ======
        reattivi_frame = ttk.Frame(notebook, padding=5)
        notebook.add(reattivi_frame, text="REATTIVI")

        # إطار البحث في تبويب Reattivi
        search_frame_rea = ttk.LabelFrame(reattivi_frame, text="REATTIVI Filters", padding=3)
        search_frame_rea.pack(fill=tk.X, pady=(0, 2))

        ttk.Label(search_frame_rea, text="Code:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.search_code_entry_rea = ttk.Entry(search_frame_rea, textvariable=self.search_code_var_rea, width=15)
        self.search_code_entry_rea.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.search_code_entry_rea.bind('<KeyRelease>', lambda e: self.perform_search_rea())

        ttk.Label(search_frame_rea, text="Name:").grid(row=0, column=2, padx=5, pady=3, sticky="e")
        self.search_name_entry_rea = ttk.Entry(search_frame_rea, textvariable=self.search_name_var_rea, width=25)
        self.search_name_entry_rea.grid(row=0, column=3, padx=5, pady=3, sticky="w")
        self.search_name_entry_rea.bind('<KeyRelease>', lambda e: self.perform_search_rea())

        ttk.Button(search_frame_rea, text="Clear",
                   command=self.reset_search_rea, width=10, style='Sub.TButton').grid(row=0, column=4, padx=5, pady=3)

        # شجرة ألوان Reattivi
        self.reattivi_tree = ttk.Treeview(
            reattivi_frame,
            columns=("code", "name", "dye_type", "supplier", "price", "resa", "created"),
            show="headings",
            height=6
        )

        self.reattivi_tree.heading("code", text="Color Code")
        self.reattivi_tree.heading("name", text="Color Name")
        self.reattivi_tree.heading("dye_type", text="Type")
        self.reattivi_tree.heading("supplier", text="Supplier")
        self.reattivi_tree.heading("price", text="Price/kg")
        self.reattivi_tree.heading("resa", text="RESA %")
        self.reattivi_tree.heading("created", text="Create Date")

        self.reattivi_tree.column("code", width=90, anchor="center")
        self.reattivi_tree.column("name", width=150, anchor="center")
        self.reattivi_tree.column("dye_type", width=90, anchor="center")
        self.reattivi_tree.column("supplier", width=110, anchor="center")
        self.reattivi_tree.column("price", width=75, anchor="center")
        self.reattivi_tree.column("resa", width=70, anchor="center")
        self.reattivi_tree.column("created", width=95, anchor="center")

        scrollbar_rea = ttk.Scrollbar(reattivi_frame, orient="vertical", command=self.reattivi_tree.yview)
        self.reattivi_tree.configure(yscrollcommand=scrollbar_rea.set)
        scrollbar_rea.pack(side=tk.RIGHT, fill=tk.Y)
        self.reattivi_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.reattivi_tree.bind("<Double-1>", lambda e: self.on_color_double_click("reattivi"))
        self._setup_treeview_sorting(self.reattivi_tree)
        setup_tree_tags(self.reattivi_tree, self.dark_mode)

        # ======== باقي الواجهة كما هي ========
        # إطار التحكم في الإضافة
        control_frame = ttk.LabelFrame(self.window, text="Controls", padding=6)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=1, anchor="n")

        # حقل النسبة المئوية
        ttk.Label(control_frame, text="Percentage (%):").pack(pady=(0, 1))
        self.percentage_entry = ttk.Entry(control_frame, width=8)
        self.percentage_entry.pack(pady=(0, 2))
        self.percentage_entry.bind('<Return>', lambda e: self.add_selected_color())

        # زر الإضافة
        ttk.Button(control_frame, text="Add Color", command=self.add_selected_color, width=12, style='Sub.TButton').pack(pady=(1, 2))

        # زر الحذف
        ttk.Button(control_frame, text="Remove Selected", command=self.remove_selected_color, width=16, style='Sub.TButton').pack(pady=1)

        # نقل زر المسح الكامل إلى عمود التحكم أسفل Remove Selected
        ttk.Button(control_frame, text="Clear All Colors",
                   command=self.clear_all_colors,
                   width=18, style='Sub.TButton').pack(pady=(1, 0))

        # إطار الألوان المضافة
        selected_frame = ttk.LabelFrame(self.window, text="Added Colors", padding=8)
        selected_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=3)

        # شجرة الألوان المضافة
        self.selected_tree = ttk.Treeview(
            selected_frame,
            columns=("code", "name", "dye_type", "percentage", "cost"),
            show="headings",
            height=7
        )

        self.selected_tree.heading("code", text="Color Code")
        self.selected_tree.heading("name", text="Color Name")
        self.selected_tree.heading("dye_type", text="Type")
        self.selected_tree.heading("percentage", text="%")
        self.selected_tree.heading("cost", text="Cost (€)")

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
        self._setup_treeview_sorting(self.selected_tree)
        setup_tree_tags(self.selected_tree, self.dark_mode)

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
        chemicals_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=3)

        chemicals_scrollbar = ttk.Scrollbar(chemicals_frame, orient="vertical")
        self.chemicals_text = tk.Text(
            chemicals_frame,
            height=14,
            wrap=tk.WORD,
            font=('Arial', 10),
            yscrollcommand=chemicals_scrollbar.set
        )
        chemicals_scrollbar.config(command=self.chemicals_text.yview)
        chemicals_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chemicals_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=2)
        self.chemicals_text.insert(tk.END, "No chemicals calculated yet. Add colors to the recipe.")
        self.chemicals_text.config(state='disabled')

    def validate_recipe_code_input(self, value):
        """التحقق من صحة إدخال كود الوصفة"""
        if value == '':
            return True
        return value.isdigit() and len(value) <= 6

    def _setup_treeview_sorting(self, tree: ttk.Treeview):
        """Enable click-to-sort on all tree columns (toggle asc/desc)."""
        for column in tree["columns"]:
            heading_text = tree.heading(column, "text")
            tree.heading(
                column,
                text=heading_text,
                command=lambda c=column, t=tree: self._on_tree_heading_click(t, c),
            )

    def _to_sort_value(self, raw_value):
        text = str(raw_value).strip()
        normalized = text.replace("€", "").replace("%", "").replace(",", "")
        try:
            return (0, float(normalized))
        except (TypeError, ValueError):
            return (1, text.lower())

    def _on_tree_heading_click(self, tree: ttk.Treeview, column: str):
        key = (str(tree), column)
        reverse = self._tree_sort_state.get(key, False)

        rows = [(tree.set(item_id, column), item_id) for item_id in tree.get_children("")]
        rows.sort(key=lambda row: self._to_sort_value(row[0]), reverse=reverse)

        for index, (_, item_id) in enumerate(rows):
            tree.move(item_id, "", index)

        self._tree_sort_state[key] = not reverse

    def _get_lab_params(self) -> Dict[str, float]:
        sample_g = self._safe_positive_float(self.lab_peso_var.get(), 10.0)
        volume_ml = self._safe_positive_float(self.lab_volume_var.get(), 150.0)
        return {"sample_g": sample_g, "volume_ml": volume_ml}

    def _safe_positive_float(self, raw_value: str, fallback: float) -> float:
        try:
            value = float(str(raw_value).strip())
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass
        return fallback

    def _update_lab_rapporto(self):
        sample_g = self._safe_positive_float(self.lab_peso_var.get(), 10.0)
        volume_ml = self._safe_positive_float(self.lab_volume_var.get(), 150.0)
        ratio = volume_ml / sample_g if sample_g else 0.0
        rounded = round(ratio)
        if abs(ratio - rounded) < 1e-9:
            rapporto_text = f"1:{int(rounded)}"
        else:
            rapporto_text = f"1:{ratio:.2f}"
        self.lab_rapporto_var.set(rapporto_text)

    def _save_lab_settings_changes(self):
        if not self.session.has_permission("can_edit_lab_settings"):
            messagebox.showwarning("Permission Denied", "You do not have permission to edit lab settings.", parent=self.window)
            return
        params = self._get_lab_params()
        saved = save_lab_settings(params["sample_g"], params["volume_ml"])
        self.lab_peso_var.set(f"{saved['sample_g']:.2f}")
        self.lab_volume_var.set(f"{saved['volume_ml']:.2f}")
        self._update_lab_rapporto()
        self.parent.event_generate("<<LabSettingsChanged>>", when="tail")
        messagebox.showinfo("Saved", "Lab parameters saved for the whole program.", parent=self.window)

    def _on_lab_settings_changed(self, _event=None):
        try:
            latest = load_lab_settings()
            self.lab_peso_var.set(f"{latest['sample_g']:.2f}")
            self.lab_volume_var.set(f"{latest['volume_ml']:.2f}")
            self._update_lab_rapporto()
        except Exception:
            pass

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
                    "supplier": getattr(color, 'supplier', ''),
                    "price_kg": float(getattr(color, 'price_kg', 0)),
                    "resa_percent": float(getattr(color, 'resa_percent', 100) or 100),
                    "created_at": str(getattr(color, 'created_at', '') or '')
                }
            elif isinstance(color, dict):
                # قاموس
                return {
                    "code": color.get('code', ''),
                    "name": color.get('name', ''),
                    "dye_type": color.get('dye_type', ''),
                    "supplier": color.get('supplier', ''),
                    "price_kg": float(color.get('price_kg', 0)),
                    "resa_percent": float(color.get('resa_percent', 100) or 100),
                    "created_at": str(color.get('created_at', '') or '')
                }
            else:
                # tuple/list
                return {
                    "code": str(color[0]) if len(color) > 0 else '',
                    "name": str(color[1]) if len(color) > 1 else '',
                    "dye_type": str(color[2]) if len(color) > 2 else '',
                    "supplier": str(color[4]) if len(color) > 4 else '',
                    "price_kg": float(color[5]) if len(color) > 5 else 0.0,
                    "resa_percent": float(color[6]) if len(color) > 6 and color[6] not in (None, '') else 100.0,
                    "created_at": str(color[7]) if len(color) > 7 else ''
                }
        except Exception:
            return None

    def _normalize_resa_percent(self, resa_percent) -> float:
        try:
            value = float(resa_percent)
        except (TypeError, ValueError):
            return 100.0
        return value if value > 0 else 100.0

    def _find_color_resa_percent(self, color_code: str) -> float:
        code = str(color_code).strip()
        for color in self.indanthren_colors:
            if str(color.get("code", "")).strip() == code:
                return self._normalize_resa_percent(color.get("resa_percent", 100))
        for color in self.reattivi_colors:
            if str(color.get("code", "")).strip() == code:
                return self._normalize_resa_percent(color.get("resa_percent", 100))
        return 100.0

    def display_colors(self, tree, colors):
        """عرض الألوان في شجرة محددة"""
        for item in tree.get_children():
            tree.delete(item)

        for color in colors:
            created = str(color.get("created_at", "") or "")
            created_date = created.split()[0] if created else ""
            zebra_insert(tree, (
                color["code"],
                color["name"],
                color["dye_type"],
                color.get("supplier", ""),
                f"€{color['price_kg']:.2f}",
                f"{float(color.get('resa_percent', 100) or 100):.2f}%",
                created_date
            ))

    def perform_search_ind(self):
        """بحث في تبويب Indanthren"""
        if not self.indanthren_colors:
            self.display_colors(self.indanthren_tree, [])
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

        self.display_colors(self.indanthren_tree, filtered)

    def perform_search_rea(self):
        """بحث في تبويب Reattivi"""
        if not self.reattivi_colors:
            self.display_colors(self.reattivi_tree, [])
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

        self.display_colors(self.reattivi_tree, filtered)

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
        show_on_top(input_win, self.window)
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

                self.add_color_to_recipe(color_data, percentage)  # [OK] ستستدعي update_chemicals تلقائياً
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
        self.add_color_to_recipe(color_data, percentage)  # [OK] ستستدعي update_chemicals تلقائياً

        self.percentage_entry.delete(0, tk.END)

    def add_color_to_recipe(self, color_data, percentage):
        """إضافة لون إلى الوصفة"""
        # التحقق من التوافق بين أنواع الصباغة
        new_color_code = str(color_data[0]).strip()

        # Prevent adding the same color twice to one recipe.
        for existing_color in self.selected_colors:
            if str(existing_color.get("code", "")).strip() == new_color_code:
                messagebox.showwarning(
                    "Duplicate Color",
                    f"Color '{new_color_code}' is already added to this recipe.",
                    parent=self.window
                )
                return

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
        
        price_text = color_data[4].replace('€', '').strip()
        try:
            price = float(price_text)
        except Exception:
            price = 0.0

        self.selected_colors.append({
            "code": new_color_code,
            "name": color_data[1],
            "dye_type": color_data[2],
            "price_kg": price,
            "percentage": percentage,
            "resa_percent": self._find_color_resa_percent(new_color_code)
        })

        self._refresh_recipe_calculations()

    def update_selected_tree(self):
        """تحديث شجرة الألوان المضافة"""
        for item in self.selected_tree.get_children():
            self.selected_tree.delete(item)

        for color in self.selected_colors:
            color_cost = (color["percentage"] / 100) * color.get("price_kg", 0)
            zebra_insert(self.selected_tree, (
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

        self._refresh_recipe_calculations()

    def clear_all_colors(self):
        """مسح جميع الألوان"""
        if not self.selected_colors:
            return

        confirm = messagebox.askyesno("Confirm", "Are you sure you want to remove all colors from the recipe?", parent=self.window)
        if confirm:
            self.selected_colors.clear()
            self._refresh_recipe_calculations()

    def _refresh_recipe_calculations(self):
        """Refresh selected tree and all dependent calculations instantly."""
        self.update_selected_tree()
        self.update_quick_info()
        self.update_chemicals()

    def update_quick_info(self):
        """تحديث المعلومات السريعة"""
        colors_count = len(self.selected_colors)
        total_percentage = sum(color["percentage"] for color in self.selected_colors)
        total_cost = CostCalculator.calculate_recipe_cost(self.selected_colors)

        self.colors_count_label.config(text=str(colors_count))
        self.percentage_label.config(text=f"{total_percentage:.2f}%")
        self.cost_label.config(text=f"€{total_cost:.2f}")
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

            # Generate the chemical report details
            chemicals_text = f"Chemicals for {total_percentage:.2f}% ({dominant_type}):\n"
            chemicals_text += "=" * 50 + "\n\n"

            for i, chemical in enumerate(chemicals, 1):
                chemicals_text += f"{i}. [{chemical.code}] {chemical.name}: {chemical.quantity} {chemical.unit}\n"

            chemicals_text += "\n" + "=" * 50
            chemicals_text += "\nNote: Quantities are per liter of dye bath"

            self.chemicals_text.insert(tk.END, chemicals_text)
            self.chemicals_text.config(state='disabled')

        except Exception as e:
            self.chemicals_text.config(state='normal')
            self.chemicals_text.delete(1.0, tk.END)
            error_text = f"Error calculating chemicals!\n\n"
            error_text += f"Error: {str(e)}\n"
            error_text += f"Total Percentage: {total_percentage:.2f}%\n"
            error_text += f"Dominant Type: {dominant_type}\n\n"
            error_text += "Please check the calculator module."
            self.chemicals_text.insert(tk.END, error_text)
            self.chemicals_text.config(state='disabled')
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

            messagebox.showinfo("Success", f"Recipe saved successfully!\nRecipe ID: {recipe_id}", parent=self.window)
            self.window.destroy()

            if hasattr(self.parent, 'load_data'):
                self.parent.load_data()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save recipe: {str(e)}", parent=self.window)

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
            recipe_details.lab_params = self._get_lab_params()

            from app.pdf_exporter import PDFExporter
            pdf_path = PDFExporter.export_recipe_to_pdf(recipe_details, parent_window=self.window)

            if pdf_path:
                messagebox.showinfo("Success",
                                    f"Recipe saved and exported successfully!\n"
                                    f"Recipe ID: {recipe_id}\n"
                                    f"PDF saved to: {pdf_path}", parent=self.window)
            else:
                messagebox.showinfo("Success", f"Recipe saved successfully! (ID: {recipe_id})", parent=self.window)

            self.window.destroy()

            if hasattr(self.parent, 'load_data'):
                self.parent.load_data()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save recipe: {str(e)}", parent=self.window)

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
        show_on_top(chem_win, self.window)
        chem_win.title("Chemical Requirements Details")
        chem_win.geometry("500x400")
        chem_win.configure(bg=get_theme_tokens(self.dark_mode)["bg"])
        chem_win.grab_set()

        ttk.Label(chem_win, text="Detailed Chemical Requirements",
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
        - These quantities are per liter of dye bath
        - Adjust based on fabric weight and liquor ratio
        - Always conduct lab tests before full production
        - Store chemicals in cool, dry places
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

