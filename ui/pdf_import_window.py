"""
نافذة استيراد وصفات من PDF
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict
import os

from app.database import DatabaseManager
from app.session import SessionManager
from app.calculator import ChemicalCalculator, CostCalculator
from app.pdf_exporter import PDFExporter
from app.models import Recipe, Color
from app.utils import get_current_timestamp, parse_percentage_input, clean_recipe_code
from app.config import DYE_TYPES
from app.lab_settings import load_lab_settings, save_lab_settings
from ui.theme_tokens import setup_tree_tags, zebra_insert, get_theme_tokens, apply_excel_treeview_style, configure_sub_button_style


def _show_on_top(window, parent):
    """Make child windows modal and keep them above parent."""
    try:
        window.lift()
        window.focus_force()
        window.grab_set()
        window.attributes("-topmost", True)
        window.after(250, lambda: window.attributes("-topmost", False))
    except Exception:
        pass


class _AddMissingColorsWindow:
    def __init__(self, parent, db: DatabaseManager, missing_colors: List[Dict], on_success_callback, dark_mode: bool = False):
        self.parent = parent
        self.db = db
        self.missing_colors = missing_colors
        self.on_success_callback = on_success_callback
        self.dark_mode = dark_mode

        self.window = tk.Toplevel(parent)
        # Keep this dialog as a normal top-level window so OS title-bar
        # controls remain available.
        _show_on_top(self.window, parent)
        # Re-assert z-order after first paint to avoid being sent behind parent
        # on some Windows window-manager timing cases.
        self.window.after_idle(lambda: _show_on_top(self.window, parent))
        try:
            self.window.grab_set()
        except Exception:
            pass
        self.window.title("Register New Colors")
        self.window.geometry("900x600")
        self.window.minsize(900, 600)
        self.window.configure(bg=get_theme_tokens(self.dark_mode)["bg"])
        # Keep this as a normal top-level window (with full title-bar controls).

        self.color_entries = []

        self.configure_styles()
        self.setup_ui()

    def configure_styles(self):
        """تكوين أنماط الواجهة"""
        style = ttk.Style(self.window)
        palette = get_theme_tokens(self.dark_mode)
        apply_excel_treeview_style(style, palette, self.dark_mode)
        configure_sub_button_style(style, 'Sub.TButton', palette)
        style.configure('MissingTitle.TLabel', font=('Arial', 13, 'bold'))
        style.configure('MissingNote.TLabel', font=('Arial', 11))
        style.configure('MissingField.TLabel', font=('Arial', 11, 'bold'))
        style.configure('Missing.TEntry', font=('Arial', 11))
        style.configure('Missing.TCombobox', font=('Arial', 11))

    def setup_ui(self):
        main_frame = ttk.Frame(self.window, padding=18)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_frame,
            text="The following colors are not in the database.",
            style='MissingTitle.TLabel'
        ).pack(pady=(4, 8))
        ttk.Label(
            main_frame,
            text="Please provide a name, dye type, and RESA (%) for each new color.",
            style='MissingNote.TLabel'
        ).pack(pady=(0, 12))

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for i, color_info in enumerate(self.missing_colors):
            row_frame = ttk.Frame(scrollable_frame, padding=8)
            row_frame.pack(fill=tk.X, expand=True)
            row_frame.columnconfigure(1, weight=1)
            row_frame.columnconfigure(3, weight=1)

            ttk.Label(
                row_frame,
                text=f"Code: {color_info['code']}",
                style='MissingField.TLabel'
            ).grid(row=0, column=0, padx=8, sticky=tk.W)

            name_var = tk.StringVar(value=color_info.get('name', ''))
            name_entry = ttk.Entry(row_frame, textvariable=name_var, width=42, style='Missing.TEntry')
            name_entry.grid(row=0, column=1, padx=8, sticky=tk.EW)

            ttk.Label(row_frame, text="Dye Type:", style='MissingField.TLabel').grid(row=0, column=2, padx=8, sticky=tk.W)
            dye_type_var = tk.StringVar(value='GENERAL')
            dye_type_combo = ttk.Combobox(
                row_frame,
                textvariable=dye_type_var,
                values=DYE_TYPES,
                state='readonly',
                width=26,
                style='Missing.TCombobox'
            )
            dye_type_combo.grid(row=0, column=3, padx=8, sticky=tk.EW)

            ttk.Label(row_frame, text="Resa %:", style='MissingField.TLabel').grid(row=0, column=4, padx=8, sticky=tk.W)
            default_resa = color_info.get('resa_percent', 100)
            resa_var = tk.StringVar(value=str(default_resa))
            resa_entry = ttk.Entry(row_frame, textvariable=resa_var, width=10, style='Missing.TEntry')
            resa_entry.grid(row=0, column=5, padx=8, sticky=tk.W)

            self.color_entries.append({
                'code': color_info['code'],
                'name_var': name_var,
                'dye_type_var': dye_type_var,
                'resa_var': resa_var
            })

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        btn_frame = ttk.Frame(self.window, padding=14)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(btn_frame, text="Save New Colors", command=self.save_new_colors, style='Sub.TButton').pack(side=tk.LEFT, padx=8, ipadx=8, ipady=2)
        ttk.Button(btn_frame, text="Cancel", command=self.window.destroy, style='Sub.TButton').pack(side=tk.RIGHT, padx=8, ipadx=8, ipady=2)

    def save_new_colors(self):
        colors_to_add = []
        for entry in self.color_entries:
            code = entry['code']
            name = entry['name_var'].get().strip()
            dye_type = entry['dye_type_var'].get().strip()
            resa_raw = entry['resa_var'].get().strip()

            if not name:
                messagebox.showerror("Error", f"Please provide a name for color code {code}.", parent=self.window)
                return

            if not dye_type:
                messagebox.showerror("Error", f"Please select a dye type for color code {code}.", parent=self.window)
                return

            try:
                resa_percent = parse_percentage_input(resa_raw, default=100.0)
                if resa_percent <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", f"Please enter a valid RESA % for color code {code}.", parent=self.window)
                return

            if self.db.get_color_by_code(code):
                continue

            new_color = Color(
                code=code,
                name=name,
                dye_type=dye_type,
                supplier='',
                price_kg=0.0,
                resa_percent=resa_percent,
                created_at=get_current_timestamp(),
                updated_at=get_current_timestamp()
            )
            colors_to_add.append(new_color)

        if not colors_to_add:
            messagebox.showinfo("Info", "No new colors to add.", parent=self.window)
            self.window.destroy()
            return

        try:
            for color in colors_to_add:
                self.db.add_color(color)

            messagebox.showinfo("Success", f"{len(colors_to_add)} new colors have been registered.", parent=self.window)
            self.window.destroy()
            if self.on_success_callback:
                self.on_success_callback()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save new colors: {e}", parent=self.window)


class PDFImportWindow:
    """نافذة استيراد وصفات من PDF"""

    def __init__(self, parent, db: DatabaseManager, dark_mode: bool = False):
        self.parent = parent
        self.db = db
        self.session = SessionManager.get_session()
        self.dark_mode = dark_mode
        self.imported_data = None
        self.chemicals = []
        current_lab = load_lab_settings()
        self.lab_peso_var = tk.StringVar(value=f"{current_lab['sample_g']:.2f}")
        self.lab_volume_var = tk.StringVar(value=f"{current_lab['volume_ml']:.2f}")
        self.lab_rapporto_var = tk.StringVar(value="")

        self.window = tk.Toplevel(parent)
        # Keep as normal top-level window so OS title-bar controls remain available.
        _show_on_top(self.window, parent)
        self.window.title("Import Recipe from PDF")
        
        # ضبط أبعاد النافذة لتكون متجاوبة
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.86)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        _palette = get_theme_tokens(self.dark_mode)
        self.window.configure(bg=_palette["bg"])
        
        # السماح بالتكبير والتصغير وإظهار أزرار التحكم
        self.window.resizable(True, True)
        self.window.minsize(980, 700)

        self.configure_styles()
        self.setup_ui()
        self._lab_settings_bind_id = self.parent.bind(
            "<<LabSettingsChanged>>",
            self._on_lab_settings_changed,
            add="+",
        )
        self.window.bind("<Destroy>", self._on_window_destroy, add="+")

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
        title_frame = ttk.Frame(self.window, padding=10)
        title_frame.pack(fill=tk.X)

        ttk.Label(title_frame, text="📄 Import Recipe from PDF",
                  font=('Arial', 14, 'bold')).pack(anchor='w')
        ttk.Label(title_frame,
                  text="Upload a laboratory recipe PDF to import colors and calculate chemicals automatically",
                  font=('Arial', 10)).pack(anchor='w', pady=2)

        # زر رفع الملف
        upload_frame = ttk.LabelFrame(self.window, text="Upload PDF File", padding=15)
        upload_frame.pack(fill=tk.X, padx=10, pady=10)

        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(upload_frame, textvariable=self.file_path_var,
                               width=40, state='readonly', font=('Arial', 9))
        file_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

    
        ttk.Button(upload_frame, text="Upload & Parse",
                   command=self.browse_pdf, width=15, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        # إطار معلومات الوصفة (أكثر إحكاما)
        self.info_frame = ttk.LabelFrame(self.window, text="Recipe Information", padding=8)
        self.info_frame.pack(fill=tk.X, padx=10, pady=5)

        # استخدام Grid بدلاً من Pack لتنظيم أفضل
        info_grid = ttk.Frame(self.info_frame)
        info_grid.pack(fill=tk.X, padx=5, pady=2)

        # الصف الأول
        ttk.Label(info_grid, text="Recipe Name:",
                  font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=1, padx=2)
        self.recipe_name_var = tk.StringVar()
        ttk.Entry(info_grid, textvariable=self.recipe_name_var,
                  width=25, font=('Arial', 9)).grid(row=0, column=1, sticky=tk.W, pady=1, padx=5)

        ttk.Label(info_grid, text="Recipe Code:",
                  font=('Arial', 9, 'bold')).grid(row=0, column=2, sticky=tk.W, pady=1, padx=10)
        self.recipe_code_var = tk.StringVar()
        ttk.Entry(info_grid, textvariable=self.recipe_code_var,
                  width=15, font=('Arial', 9)).grid(row=0, column=3, sticky=tk.W, pady=1, padx=5)

        # الصف الثاني
        ttk.Label(info_grid, text="Dye Type:",
                  font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=1, padx=2)
        self.dye_type_var = tk.StringVar()
        ttk.Entry(info_grid, textvariable=self.dye_type_var,
                  width=20, font=('Arial', 9)).grid(row=1, column=1, sticky=tk.W, pady=1, padx=5)

        ttk.Label(info_grid, text="Total %:",
                  font=('Arial', 9, 'bold')).grid(row=1, column=2, sticky=tk.W, pady=1, padx=10)
        self.total_percent_var = tk.StringVar()
        ttk.Label(info_grid, textvariable=self.total_percent_var,
                  font=('Arial', 9, 'bold'), foreground="green").grid(row=1, column=3, sticky=tk.W, pady=1, padx=5)

        ttk.Label(info_grid, text="Peso (g):",
                  font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=1, padx=2)
        self.lab_peso_entry = ttk.Entry(info_grid, textvariable=self.lab_peso_var,
                                        width=12, font=('Arial', 9))
        self.lab_peso_entry.grid(row=2, column=1, sticky=tk.W, pady=1, padx=5)

        ttk.Label(info_grid, text="Volume (ml):",
                  font=('Arial', 9, 'bold')).grid(row=2, column=2, sticky=tk.W, pady=1, padx=10)
        self.lab_volume_entry = ttk.Entry(info_grid, textvariable=self.lab_volume_var,
                                          width=12, font=('Arial', 9))
        self.lab_volume_entry.grid(row=2, column=3, sticky=tk.W, pady=1, padx=5)

        ttk.Label(info_grid, text="Rapporto Bagno:",
                  font=('Arial', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=1, padx=2)
        ttk.Entry(info_grid, textvariable=self.lab_rapporto_var,
                  width=12, font=('Arial', 9), state='readonly').grid(row=3, column=1, sticky=tk.W, pady=1, padx=5)
        self.lab_save_btn = ttk.Button(
            info_grid,
            text="Save Changes",
            command=self._save_lab_settings_changes,
            width=14,
            style='Sub.TButton'
        )
        self.lab_save_btn.grid(row=2, column=4, rowspan=2, padx=10, pady=1, sticky=tk.W)

        self.lab_peso_entry.bind("<KeyRelease>", lambda _e: self._update_lab_rapporto())
        self.lab_volume_entry.bind("<KeyRelease>", lambda _e: self._update_lab_rapporto())
        self._update_lab_rapporto()
        if not self.session.has_permission("can_edit_lab_settings"):
            self.lab_peso_entry.configure(state="readonly")
            self.lab_volume_entry.configure(state="readonly")
            self.lab_save_btn.state(["disabled"])

        # إطار الألوان المستوردة (أصغر)
        colors_frame = ttk.LabelFrame(self.window, text=f"Imported Colors", padding=8)
        colors_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # شجرة الألوان - أصغر
        self.colors_tree = ttk.Treeview(
            colors_frame,
            columns=("code", "name", "dye_type", "percentage", "price", "status"),
            show="headings",
            height=3  # keep more space for footer buttons on smaller screens
        )

        # عناوين الأعمدة
        self.colors_tree.heading("code", text="Code", anchor="center")
        self.colors_tree.heading("name", text="Name", anchor="center")
        self.colors_tree.heading("dye_type", text="Type", anchor="center")
        self.colors_tree.heading("percentage", text="%", anchor="center")
        self.colors_tree.heading("price", text="Price €/kg", anchor="center")
        self.colors_tree.heading("status", text="Status", anchor="center")

        # أبعاد الأعمدة - أصغر
        self.colors_tree.column("code", width=70, anchor="center", minwidth=60)
        self.colors_tree.column("name", width=150, anchor="center", minwidth=120)
        self.colors_tree.column("dye_type", width=90, anchor="center", minwidth=80)
        self.colors_tree.column("percentage", width=70, anchor="center", minwidth=60)
        self.colors_tree.column("price", width=80, anchor="center", minwidth=70)
        self.colors_tree.column("status", width=80, anchor="center", minwidth=70)

        scrollbar_colors = ttk.Scrollbar(colors_frame, orient="vertical", command=self.colors_tree.yview)
        self.colors_tree.configure(yscrollcommand=scrollbar_colors.set)
        scrollbar_colors.pack(side=tk.RIGHT, fill=tk.Y)
        self.colors_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        setup_tree_tags(self.colors_tree, self.dark_mode)

        # إطار الكيماويات (أصغر)
        chemicals_frame = ttk.LabelFrame(self.window, text="Calculated Chemicals", padding=8)
        chemicals_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # شجرة الكيماويات - أصغر
        self.chemicals_tree = ttk.Treeview(
            chemicals_frame,
            columns=("code", "name", "quantity", "unit"),
            show="headings",
            height=2  # keep more space for footer buttons on smaller screens
        )

        self.chemicals_tree.heading("code", text="Code", anchor="center")
        self.chemicals_tree.heading("name", text="Chemical Name", anchor="center")
        self.chemicals_tree.heading("quantity", text="Quantity", anchor="center")
        self.chemicals_tree.heading("unit", text="Unit", anchor="center")

        self.chemicals_tree.column("code", width=80, anchor="center", minwidth=60)
        self.chemicals_tree.column("name", width=180, anchor="center", minwidth=150)
        self.chemicals_tree.column("quantity", width=80, anchor="center", minwidth=70)
        self.chemicals_tree.column("unit", width=60, anchor="center", minwidth=50)

        scrollbar_chem = ttk.Scrollbar(chemicals_frame, orient="vertical", command=self.chemicals_tree.yview)
        self.chemicals_tree.configure(yscrollcommand=scrollbar_chem.set)
        scrollbar_chem.pack(side=tk.RIGHT, fill=tk.Y)
        self.chemicals_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        setup_tree_tags(self.chemicals_tree, self.dark_mode)

        # أزرار التحكم (في الأسفل)
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=(2, 6), side=tk.BOTTOM)

        # صف الأزرار
        button_row = ttk.Frame(control_frame)
        button_row.pack(fill=tk.X, pady=1)

        # الأزرار بأحجام متساوية
        ttk.Button(button_row, text="Save Recipe",
                   command=self.save_recipe, width=16, style='Sub.TButton').pack(side=tk.LEFT, padx=2)

        ttk.Button(button_row, text="Export as PDF",
                   command=self.export_pdf, width=16, style='Sub.TButton').pack(side=tk.LEFT, padx=2)

        self.register_colors_button = ttk.Button(button_row, text="Register Colors",
                                                command=self.register_missing_colors, width=16, style='Sub.TButton')
        self.register_colors_button.pack(side=tk.LEFT, padx=2)
        self.register_colors_button.pack_forget()  # Initially hidden

        ttk.Button(button_row, text="Close",
                   command=self.window.destroy, width=16, style='Sub.TButton').pack(side=tk.RIGHT, padx=2)

    def _safe_positive_float(self, raw_value: str, fallback: float) -> float:
        try:
            value = float(str(raw_value).strip())
            if value > 0:
                return value
        except (TypeError, ValueError):
            pass
        return fallback

    def _filter_nonzero_chemicals(self, chemicals):
        """Return only chemicals with quantity > 0."""
        filtered = []
        for chemical in chemicals or []:
            try:
                qty = float(getattr(chemical, "quantity", 0) or 0)
            except (TypeError, ValueError):
                qty = 0.0
            if qty > 0:
                filtered.append(chemical)
        return filtered

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

    def _get_lab_params(self) -> Dict[str, float]:
        sample_g = self._safe_positive_float(self.lab_peso_var.get(), 10.0)
        volume_ml = self._safe_positive_float(self.lab_volume_var.get(), 150.0)
        return {"sample_g": sample_g, "volume_ml": volume_ml}

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

    def browse_pdf(self):
        """تصفح واختيار ملف PDF"""
        file_path = filedialog.askopenfilename(
            parent=self.window,
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
        )
        _show_on_top(self.window, self.parent)

        if file_path:
            self.file_path_var.set(file_path)
            self.parse_pdf()

    def parse_pdf(self):
        """تحليل ملف PDF"""
        file_path = self.file_path_var.get()

        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("Warning", "Please select a PDF file first", parent=self.window)
            return

        try:
            # قراءة ملف PDF
            import pdfplumber
            # استيراد الكلاس هنا لتجنب الخطأ إذا كانت المكتبة غير مثبتة عند فتح النافذة
            from ui.pdf_importer import PDFRecipeImporter

            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"

            print("=" * 50)
            print("Extracted Text from PDF:")
            print("=" * 50)
            print(text[:1000])  # طباعة أول 1000 حرف للتصحيح
            print("=" * 50)

            # استخراج البيانات من النص
            self.imported_data = PDFRecipeImporter.extract_recipe_from_text(text)

            # إذا لم نجد ألواناً، جرب الطريقة المباشرة
            if not self.imported_data['colors']:
                print("No colors found with text extraction, trying direct PDF extraction...")
                self.imported_data = PDFRecipeImporter.extract_recipe_from_pdf(file_path)

            if not self.imported_data['colors']:
                messagebox.showwarning("Warning",
                                       f"No colors found in PDF.\n\n"
                                       f"Extracted text preview:\n{text[:500]}...", parent=self.window)
                return

            print(f"Found {len(self.imported_data['colors'])} colors:")
            for color in self.imported_data['colors']:
                print(f"  {color['code']} - {color['name']} - {color['percentage']}%")

            # --- FIX: Pass fallback dye type for unknown colors ---
            recipe_dye_type = self.imported_data.get('dye_type', 'GENERAL')
            matched_colors = PDFRecipeImporter.match_colors_with_database(
                self.imported_data['colors'],
                self.db,
                fallback_dye_type=recipe_dye_type
            )

            # تحديث واجهة المستخدم
            self.update_ui(matched_colors)

            messagebox.showinfo("Success",
                                f"Successfully imported {len(matched_colors)} colors from PDF\n\n"
                                f"Recipe: {self.imported_data.get('recipe_name', 'Unknown')}\n"
                                f"Code: {self.imported_data.get('recipe_code', 'N/A')}\n"
                                f"Initial Dye Type: {self.imported_data.get('dye_type', 'Unknown')}", parent=self.window)

        except ImportError:
            messagebox.showerror("Error",
                                 "Please install pdfplumber:\n"
                                 "pip install pdfplumber\n\n"
                                 "Or: pip install -r requirements.txt", parent=self.window)
        except Exception as e:
            messagebox.showerror("Error",
                                 f"Failed to parse PDF:\n{str(e)}\n\n"
                                 f"Error type: {type(e).__name__}", parent=self.window)

    def update_ui(self, colors: List[Dict]):
        """تحديث واجهة المستخدم بالبيانات المستوردة"""
        # تحديث معلومات الوصفة
        calculated_total = sum(float(c.get('percentage', 0) or 0) for c in colors)
        if self.imported_data is None:
            self.imported_data = {}
        self.imported_data['total_percentage'] = calculated_total

        self.recipe_name_var.set(self.imported_data.get('recipe_name', 'Imported Recipe'))
        self.recipe_code_var.set(clean_recipe_code(self.imported_data.get('recipe_code', '')))
        # سيتم تحديث نوع الصبغة في recalculate_chemicals
        self.dye_type_var.set("Calculating...")
        self.total_percent_var.set(f"{calculated_total:.4f}%")

        # تحديث شجرة الألوان
        for item in self.colors_tree.get_children():
            self.colors_tree.delete(item)

        missing_colors = []  # لتخزين الألوان المفقودة

        for color in colors:
            # الحصول على السعر من قاعدة البيانات إذا كان اللون موجوداً
            price_text = "€0.00"
            if color['exists_in_db'] and color.get('db_color'):
                price_text = f"€{color['db_color'].price_kg:.2f}"
            elif color.get('price_kg', 0) > 0:
                price_text = f"€{color['price_kg']:.2f}"

            status = "✅ Found" if color['exists_in_db'] else "⚠️ Not in DB"

            # إذا كان اللون غير موجود، أضفه للقائمة
            if not color['exists_in_db']:
                missing_colors.append(f"{color['code']} - {color['name']}")

            zebra_insert(self.colors_tree, (
                color['code'],
                color['name'],
                color['dye_type'],
                f"{color['percentage']:.4f}%",
                price_text,
                status
            ))

        # إظهار زر تسجيل الألوان المفقودة
        if missing_colors:
            self.register_colors_button.pack(side=tk.LEFT, padx=2)  # Show the button
            self.missing_colors_list = [{"code": color['code'], "name": color['name']} for color in colors if not color['exists_in_db']]
        else:
            self.register_colors_button.pack_forget()  # Hide the button
            self.missing_colors_list = []

        # حساب الكيماويات
        self.recalculate_chemicals()

    def recalculate_chemicals(self):
        """إعادة حساب الكيماويات بناءً على النوع المهيمن"""
        if not self.imported_data:
            return

        try:
            # --- START FIX: Calculate Dominant Type for Display ---
            colors_from_tree = []
            for item in self.colors_tree.get_children():
                values = self.colors_tree.item(item, "values")
                if len(values) >= 4:
                    colors_from_tree.append({
                        "dye_type": values[2],
                        "percentage": float(values[3].replace('%', ''))
                    })

            if not colors_from_tree:
                self.chemicals = []
                self.dye_type_var.set("N/A")
                return

            type_totals = {}
            for color in colors_from_tree:
                dye_type = color.get('dye_type', 'GENERAL')
                type_totals[dye_type] = type_totals.get(dye_type, 0) + color.get('percentage', 0)
            
            dominant_type = max(type_totals, key=type_totals.get) if type_totals else 'GENERAL'
            # --- END FIX ---

            total_percent = sum(color.get('percentage', 0) for color in colors_from_tree)
            self.imported_data['total_percentage'] = total_percent
            self.total_percent_var.set(f"{total_percent:.4f}%")

            # استخدام النوع المهيمن للحساب
            raw_chemicals = ChemicalCalculator.calculate_chemicals(total_percent, dominant_type)
            self.chemicals = self._filter_nonzero_chemicals(raw_chemicals)

            # تحديث حقل نوع الصبغة لإظهار النوع المهيمن
            self.dye_type_var.set(dominant_type)

            # تحديث شجرة الكيماويات
            for item in self.chemicals_tree.get_children():
                self.chemicals_tree.delete(item)

            for chemical in self.chemicals:
                zebra_insert(self.chemicals_tree, (
                    chemical.code,
                    chemical.name,
                    chemical.quantity,
                    chemical.unit
                ))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate chemicals: {str(e)}", parent=self.window)

    def save_recipe(self):
        """حفظ الوصفة في قاعدة البيانات"""
        if not self.imported_data:
            messagebox.showwarning("Warning", "No recipe data to save", parent=self.window)
            return

        recipe_name = self.recipe_name_var.get().strip()
        if not recipe_name:
            messagebox.showwarning("Warning", "Please enter a recipe name", parent=self.window)
            return

        missing_colors_details = []
        colors_to_save = []
        for item in self.colors_tree.get_children():
            values = self.colors_tree.item(item, "values")
            if len(values) >= 6:
                code, name, dye_type, percentage_str, _, status = values
                if status == "⚠️ Not in DB":
                    missing_colors_details.append(f"{code} - {name}")

                try:
                    percentage = float(percentage_str.replace('%', ''))
                except ValueError:
                    percentage = 0.0
                
                db_color = self.db.get_color_by_code(code)
                price_kg = db_color.price_kg if db_color else 0.0

                colors_to_save.append({
                    "code": code, "name": name, "dye_type": dye_type,
                    "percentage": percentage, "price_kg": price_kg
                })

        if not colors_to_save:
            messagebox.showwarning("Warning", "No colors to save", parent=self.window)
            return

        if missing_colors_details:
            error_msg = "Cannot save the recipe. The following colors are not registered in the database:\n\n"
            for color_info in missing_colors_details:
                error_msg += f"• {color_info}\n"
            error_msg += "\nPlease use the 'Register Colors' button to add them first."
            messagebox.showerror("Unregistered Colors", error_msg, parent=self.window)
            return

        self._finalize_save(colors_to_save)

    def _on_colors_registered(self):
        """Callback function after new colors are registered."""
        messagebox.showinfo("Success", "Colors registered. Refreshing color status.", parent=self.window)

        # We just need to re-match and update the UI, not re-parse the whole PDF
        try:
            if not self.imported_data:
                # Should not happen, but as a safeguard
                self.parse_pdf()
                return

            # استيراد الكلاس هنا لتجنب الخطأ إذا كانت المكتبة غير مثبتة
            from ui.pdf_importer import PDFRecipeImporter

            recipe_dye_type = self.imported_data.get('dye_type', 'GENERAL')
            matched_colors = PDFRecipeImporter.match_colors_with_database(
                self.imported_data['colors'],
                self.db,
                fallback_dye_type=recipe_dye_type
            )

            # This will refresh the treeview and hide the "Register" button
            self.update_ui(matched_colors)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh color data after registration: {e}", parent=self.window)




    def _finalize_save(self, colors_to_save):
        """The actual logic to save the recipe to the database."""
        try:
            recipe_code = clean_recipe_code(self.recipe_code_var.get().strip())
            recipe_name = self.recipe_name_var.get().strip()

            recipe_obj = Recipe(
                id=0,
                recipe_code=recipe_code,
                name=recipe_name,
                created_at=get_current_timestamp()
            )

            total_percentage = sum(c.get('percentage', 0) for c in colors_to_save)
            
            type_totals = {}
            for color in colors_to_save:
                dye_type = color.get('dye_type', 'GENERAL')
                type_totals[dye_type] = type_totals.get(dye_type, 0) + color.get('percentage', 0)
            
            dominant_type = max(type_totals, key=type_totals.get) if type_totals else 'GENERAL'

            from app.calculator import ChemicalCalculator
            chemicals = ChemicalCalculator.calculate_chemicals(total_percentage, dominant_type)
            chemicals = self._filter_nonzero_chemicals(chemicals)

            recipe_id = self.db.add_recipe(recipe_obj, colors_to_save, chemicals)

            messagebox.showinfo("Success", f"Recipe saved successfully with ID: {recipe_id}", parent=self.window)
            self.window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save recipe: {e}", parent=self.window)


    def export_pdf(self):
        """تصدير الوصفة كملف PDF"""
        if not self.imported_data:
            messagebox.showwarning("Warning", "No recipe data to export", parent=self.window)
            return

        # --- FIX: Check for unregistered colors before exporting ---
        missing_colors = []
        for item in self.colors_tree.get_children():
            values = self.colors_tree.item(item, "values")
            if len(values) >= 6 and values[5] == "⚠️ Not in DB":
                code = values[0]
                name = values[1]
                missing_colors.append(f"{code} - {name}")
        
        if missing_colors:
            error_msg = "Cannot export to PDF. The following colors are not registered in the database:\n\n"
            for color_info in missing_colors:
                error_msg += f"• {color_info}\n"
            
            error_msg += "\nPlease register these colors first before exporting."
            
            messagebox.showerror("Unregistered Colors", error_msg, parent=self.window)
            return  # Stop the exporting process
        # --- END FIX ---

        try:
            # تحضير بيانات الألوان
            colors_data = []
            for item in self.colors_tree.get_children():
                values = self.colors_tree.item(item, "values")
                if len(values) >= 4:
                    code, name, dye_type, percentage = values[0], values[1], values[2], values[3]
                    percentage_val = float(percentage.replace('%', ''))

                    colors_data.append({
                        "code": code,
                        "name": name,
                        "dye_type": dye_type,
                        "percentage": percentage_val,
                        "price_kg": 0.0  # سعر مؤقت
                    })

            # حساب التكلفة
            total_cost = CostCalculator.calculate_recipe_cost(colors_data)

            # إنشاء RecipeDetails
            from app.models import RecipeDetails, Recipe
            from app.utils import get_current_timestamp

            recipe_obj = Recipe(
                id=0,
                recipe_code=clean_recipe_code(self.recipe_code_var.get()),
                name=self.recipe_name_var.get(),
                created_at=get_current_timestamp()
            )

            recipe_details = RecipeDetails(
                recipe=recipe_obj,
                colors=colors_data,
                chemicals=self._filter_nonzero_chemicals(self.chemicals),
                total_percentage=sum(c.get('percentage', 0) for c in colors_data),
                dominant_type=self.dye_type_var.get(),
                cost=total_cost
            )

            # تصدير إلى PDF
            recipe_details.lab_params = self._get_lab_params()
            pdf_path = PDFExporter.export_recipe_to_pdf(recipe_details, parent_window=self.window)

            if pdf_path:
                messagebox.showinfo("Success", f"Recipe exported to PDF:\n{pdf_path}", parent=self.window)
            else:
                messagebox.showinfo("Info", "PDF export cancelled", parent=self.window)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {str(e)}", parent=self.window)

    def register_missing_colors(self):
        """فتح نافذة تسجيل الألوان المفقودة"""
        if not hasattr(self, 'missing_colors_list') or not self.missing_colors_list:
            messagebox.showwarning("Warning", "No missing colors to register", parent=self.window)
            return

        # The self.missing_colors_list is already populated by update_ui,
        # so we can use it directly.
        _AddMissingColorsWindow(self.window, self.db, self.missing_colors_list, self._on_colors_registered, dark_mode=self.dark_mode)
