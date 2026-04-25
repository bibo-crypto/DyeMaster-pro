"""
نافذة عرض الألوان المستخدمة في الريتشتات
"""
import tkinter as tk
import sqlite3
from tkinter import ttk, messagebox
from typing import Dict, Any
from app.models import Color
from app.session import SessionManager
from color_helper import fix_color_code

from app.utils import clean_color_code, parse_percentage_input, parse_number_input, normalize_dye_type_label
from app.config import DYE_TYPES
from ui.theme_tokens import (
    setup_tree_tags,
    zebra_insert,
    get_theme_tokens,
    apply_excel_treeview_style,
)


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


# ============================================
# نافذة تعديل الألوان المبسطة
# ============================================
class SimpleColorsWindow:
    """نافذة مبسطة لتعديل الألوان"""

    def __init__(self, parent, db, color_code, callback=None, dark_mode: bool = False):
        self.parent = parent
        self.db = db
        self.session = SessionManager.get_session()
        self.original_color_code = fix_color_code(color_code)
        self.callback = callback
        self.dark_mode = dark_mode

        # ✅ أنواع الصبغة من CONFIG (متطابقة مع Add color)
        self.dye_types = DYE_TYPES

        self.window = tk.Toplevel(parent)
        _show_on_top(self.window, parent)
        self.window.title(f"Modify Color: {color_code}")

        # ✅ حجم أصغر وأكثر كفاءة
        self.window.geometry("500x550")
        self.window.minsize(480, 500)

        # مركز النافذة
        # Keep this as a normal top-level window (with full title-bar controls).

        # تحميل بيانات اللون
        self.color_data = self.load_color_data()

        # إنشاء الواجهة
        self.setup_ui()

    def load_color_data(self):
        """تحميل بيانات اللون"""
        try:
            # محاولة الحصول على بيانات اللون من قاعدة البيانات
            if hasattr(self.db, 'get_color_by_code'):
                color = self.db.get_color_by_code(self.original_color_code)
            else:
                # طريقة بديلة
                conn = sqlite3.connect(self.db.db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM colors WHERE code = ?", (self.original_color_code,))
                row = cursor.fetchone()
                conn.close()

                if row:
                    color = Color(
                        code=row[0],
                        name=row[1],
                        dye_type=row[2],
                        supplier=row[3],
                        price_kg=row[4],
                        resa_percent=row[5],
                        created_at=row[6],
                        updated_at=row[7]
                    )
                else:
                    color = None

            if color:
                return {
                    'code': getattr(color, 'code', self.original_color_code),
                    'name': getattr(color, 'name', ''),
                    'dye_type': getattr(color, 'dye_type', ''),
                    'supplier': getattr(color, 'supplier', ''),
                    'price_kg': getattr(color, 'price_kg', 0),
                    'resa_percent': getattr(color, 'resa_percent', 100),
                    'created_at': getattr(color, 'created_at', ''),
                    'updated_at': getattr(color, 'updated_at', '')
                }
        except Exception as e:
            print(f"Error loading color data: {e}")

        # بيانات افتراضية إذا فشل التحميل
        return {
            'code': self.original_color_code,
            'name': '',
            'dye_type': '',
            'supplier': '',
            'price_kg': 0,
            'resa_percent': 100,
            'created_at': '',
            'updated_at': ''
        }

    def validate_code_input(self, action, value):
        """التحقق من صحة إدخال الكود"""
        # Always allow delete/backspace operations.
        if action == '0':
            return True
        if value == '':
            return True
        return value.isdigit() and len(value) <= 5

    def setup_ui(self):
        """إعداد واجهة المستخدم - تخطيط مضغوط"""
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # العنوان
        title_label = ttk.Label(
            main_frame,
            text=f"Modify Color: {self.color_data.get('code', '')}",
            font=('Arial', 12, 'bold'),
            foreground='#2c3e50'
        )
        title_label.pack(pady=(0, 15))

        # ✅ إطار الحقول - مضغوط
        fields_frame = ttk.LabelFrame(main_frame, text="Color Details", padding=10)
        fields_frame.pack(fill=tk.X, pady=(0, 10))

        # ✅ استخدام grid مع مسافات صغيرة
        row = 0

        # كود اللون
        ttk.Label(fields_frame, text="Code:",
                  font=('Arial', 9)).grid(
            row=row, column=0, sticky="e", padx=5, pady=3)  # ⬅️ مسافات صغيرة
        self.code_var = tk.StringVar(value=self.color_data.get('code', ''))
        self.code_entry = ttk.Entry(fields_frame, textvariable=self.code_var,
                                    width=30, font=('Arial', 9))
        self.code_entry.configure(
            validate='key',
            validatecommand=(self.window.register(self.validate_code_input), '%d', '%P')
        )
        self.code_entry.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        row += 1

        # اسم اللون
        ttk.Label(fields_frame, text="Name:",
                  font=('Arial', 9)).grid(
            row=row, column=0, sticky="e", padx=5, pady=3)
        self.name_var = tk.StringVar(value=self.color_data.get('name', ''))
        self.name_entry = ttk.Entry(fields_frame, textvariable=self.name_var,
                                    width=30, font=('Arial', 9))
        self.name_entry.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        row += 1

        # نوع الصبغة
        ttk.Label(fields_frame, text="Type:",
                  font=('Arial', 9)).grid(
            row=row, column=0, sticky="e", padx=5, pady=3)

        self.type_var = tk.StringVar(value=self.color_data.get('dye_type', ''))
        type_combo = ttk.Combobox(
            fields_frame,
            textvariable=self.type_var,
            values=self.dye_types,
            state='readonly',
            width=28,
            font=('Arial', 9)
        )
        type_combo.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        row += 1

        # المورد
        ttk.Label(fields_frame, text="Supplier:",
                  font=('Arial', 9)).grid(
            row=row, column=0, sticky="e", padx=5, pady=3)
        self.supplier_var = tk.StringVar(value=self.color_data.get('supplier', ''))
        self.supplier_entry = ttk.Entry(fields_frame, textvariable=self.supplier_var,
                                        width=30, font=('Arial', 9))
        self.supplier_entry.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        row += 1

        # السعر
        ttk.Label(fields_frame, text="Price (€/kg):",
                  font=('Arial', 9)).grid(
            row=row, column=0, sticky="e", padx=5, pady=3)
        self.price_var = tk.StringVar(value=str(self.color_data.get('price_kg', 0)))
        self.price_entry = ttk.Entry(fields_frame, textvariable=self.price_var,
                                     width=30, font=('Arial', 9))
        self.price_entry.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        row += 1

        # نسبة الصباغة
        ttk.Label(fields_frame, text="Resa %:",
                  font=('Arial', 9)).grid(
            row=row, column=0, sticky="e", padx=5, pady=3)
        self.resa_var = tk.StringVar(value=str(self.color_data.get('resa_percent', 100)))
        self.resa_entry = ttk.Entry(fields_frame, textvariable=self.resa_var,
                                    width=30, font=('Arial', 9))
        self.resa_entry.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        row += 1

        # ✅ معلومات إضافية مضغوطة
        info_frame = ttk.LabelFrame(main_frame, text="Additional Info", padding=8)
        info_frame.pack(fill=tk.X, pady=(10, 15))

        info_text = ""
        if self.color_data.get('created_at'):
            info_text += f"Created: {self.color_data['created_at']}\n"
        if self.color_data.get('updated_at'):
            info_text += f"Updated: {self.color_data['updated_at']}"

        if info_text:
            info_label = ttk.Label(info_frame, text=info_text,
                                   font=('Arial', 8), justify="left")
            info_label.pack(anchor="w")

        # ✅ ✅ ✅ أزرار التحكم - في نفس السطر مضغوطة
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 10))

        # ✅ زر الحفظ - واضح لكن مضغوط
        save_button = tk.Button(
            button_frame,
            text="Save",
            command=self.save_changes,
            font=('Arial', 10, 'bold'),
            bg='#28a745',
            fg='white',
            padx=15,
            pady=6,
            bd=0,
            cursor="hand2"
        )
        save_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # ✅ زر الحذف
        delete_button = tk.Button(
            button_frame,
            text="Delete",
            command=self.delete_color,
            font=('Arial', 10),
            bg='#dc3545',
            fg='white',
            padx=15,
            pady=6,
            bd=0,
            cursor="hand2"
        )
        delete_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        if not self.session.has_permission("can_delete"):
            delete_button.configure(state=tk.DISABLED)

        # ✅ زر الإلغاء
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            font=('Arial', 10),
            bg='#6c757d',
            fg='white',
            padx=15,
            pady=6,
            bd=0,
            cursor="hand2"
        )
        cancel_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # ✅ ربط أحداث لوحة المفاتيح
        self.window.bind('<Return>', lambda e: self.save_changes())
        self.window.bind('<Control-s>', lambda e: self.save_changes())
        self.window.bind('<Escape>', lambda e: self.window.destroy())

        # ✅ Focus على أول حقل
        self.code_entry.focus_set()

    def save_changes(self):
        """حفظ التغييرات - مع رسائل واضحة"""
        try:
            # جمع البيانات
            new_code = self.code_var.get().strip().upper()
            if not new_code:
                messagebox.showwarning("Warning", "Color code is required!", parent=self.window)
                self.code_entry.focus_set()
                return

            resa_input = self.resa_var.get().strip() or "100"
            try:
                resa_percent = parse_percentage_input(resa_input)
            except ValueError:
                messagebox.showwarning(
                    "Invalid RESA",
                    "RESA must use English digits only (0-9).\n"
                    "Allowed format: 85 or 85.5",
                    parent=self.window
                )
                self.resa_entry.focus_set()
                return

            color_data = {
                'code': new_code,
                'name': self.name_var.get().strip(),
                'dye_type': normalize_dye_type_label(self.type_var.get().strip()),
                'supplier': self.supplier_var.get().strip(),
                'price_kg': self.price_var.get().strip(),
                'resa_percent': resa_percent
            }

            # التحقق من البيانات
            if not color_data['name']:
                messagebox.showwarning("Warning", "Color name is required!", parent=self.window)
                self.name_entry.focus_set()
                return

            if len(new_code) != 5:
                messagebox.showwarning("Warning", "Color code must be exactly 5 digits!", parent=self.window)
                self.code_entry.focus_set()
                return

            # التحقق من القيم العددية
            try:
                price_val = parse_number_input(color_data['price_kg'], default=0.0)
                resa_val = parse_number_input(color_data['resa_percent'], default=100.0)
            except ValueError:
                messagebox.showerror("Error",
                                     "Please enter valid numeric value for price.\n\n"
                                     "Example:\n"
                                     "- Price: 12.50", parent=self.window)
                return

            # التحقق مما إذا تم تغيير الكود
            if new_code != self.original_color_code:
                # التحقق من عدم وجود كود مكرر
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT code FROM colors WHERE code = ?", (new_code,))
                existing = cursor.fetchone()
                conn.close()

                if existing:
                    messagebox.showerror("Error",
                                         f"Color code '{new_code}' already exists!\n"
                                         f"Please use a different code.", parent=self.window)
                    self.code_entry.focus_set()
                    return

            # حفظ التغييرات في قاعدة البيانات
            success = self.save_to_database(new_code, color_data, price_val, resa_val)

            if success:
                resa_display = str(int(resa_val)) if float(resa_val).is_integer() else str(resa_val)
                messagebox.showinfo("Success",
                                    f"Color '{new_code}' saved successfully!\n\n"
                                    f"- Name: {color_data['name']}\n"
                                    f"- Type: {color_data['dye_type']}\n"
                                    f"- Price: €{price_val:.2f}/kg\n"
                                    f"- Resa: {resa_display}%", parent=self.window)

                # ✅ استدعاء دالة الرد للتحديث
                if self.callback:
                    try:
                        self.callback()  # هذا سينادي refresh_window في النافذة الرئيسية
                    except Exception as cb_error:
                        print(f"Callback error: {cb_error}")

                self.window.destroy()
            else:
                messagebox.showerror("Error",
                                     "Failed to save color in database.\n"
                                     "Please check the database connection.", parent=self.window)

        except Exception as e:
            messagebox.showerror("Error",
                                 f"Failed to save changes:\n{str(e)}", parent=self.window)

    def save_to_database(self, new_code, color_data, price_val, resa_val):
        """Save color through DatabaseManager to ensure cache invalidation."""
        try:
            from app.models import Color
            from app.utils import get_current_timestamp

            existing = self.db.get_color_by_code(self.original_color_code)
            if not existing:
                return False

            if new_code != self.original_color_code:
                duplicate = self.db.get_color_by_code(new_code)
                if duplicate:
                    return False

            updated_color = Color(
                id=existing.id,
                code=new_code,
                name=color_data['name'],
                dye_type=color_data['dye_type'],
                supplier=color_data['supplier'],
                price_kg=price_val,
                resa_percent=resa_val,
                created_at=existing.created_at,
                updated_at=get_current_timestamp()
            )
            return self.db.update_color(updated_color)
        except Exception as e:
            print(f"Database error: {e}")
            return False

    def delete_color(self):
        """
        Prevents deletion of a color if it is in use and shows a warning.
        """
        if not self.session.has_permission("can_delete"):
            messagebox.showwarning("Permission Denied", "You do not have permission to delete colors.", parent=self.window)
            return
        try:
            # Check if the color is used in any recipes.
            recipes_using_color = self.db.get_recipes_using_color(self.original_color_code)
            
            if recipes_using_color:
                # If the color is in use, prevent deletion and show an error message.
                error_message = (
                    f"Forbidden: Color '{self.original_color_code}' cannot be deleted.\n\n"
                    f"It is currently used in {len(recipes_using_color)} recipes. "
                    "Please review the 'Active Colors' window to manage these recipes first."
                )
                messagebox.showerror("Deletion Forbidden", error_message, parent=self.window)
                return

            # This part will likely not be reached if opened from ActiveColorsWindow,
            # but is kept for logical completeness in case this window is used elsewhere.
            confirm = messagebox.askyesno(
                "Confirm Delete",
                f"Are you sure you want to delete color '{self.original_color_code}'?\n\n"
                "This action cannot be undone!",
                parent=self.window
            )

            if not confirm:
                return

            # To correctly delete, we need the color's ID
            color_to_delete = self.db.get_color_by_code(self.original_color_code)
            if not color_to_delete:
                messagebox.showwarning("Warning", "Color not found.", parent=self.window)
                return

            # Call the corrected delete method with the ID
            success = self.db.delete_color(color_to_delete.id)

            if success:
                messagebox.showinfo("Success", f"Color {self.original_color_code} deleted successfully", parent=self.window)
                if self.callback:
                    self.callback()
                self.window.destroy()
            else:
                messagebox.showerror("Error", "Failed to delete color from the database.", parent=self.window)

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during deletion: {str(e)}", parent=self.window)

    def _handle_color_in_use(self, recipes_using_color):
        """معالجة حذف لون مستخدم في وصفات"""
        num_recipes = len(recipes_using_color)

        # إنشاء رسالة مفصلة تظهر الوصفات التي تستخدم هذا اللون
        recipe_list = "\n".join([f"- {recipe.recipe_code}: {recipe.name}" for recipe in recipes_using_color[:5]])
        if num_recipes > 5:
            recipe_list += f"\n... and {num_recipes - 5} more recipes"

        message = (
            f"Color '{self.original_color_code}' is used in {num_recipes} recipe(s).\n\n"
            f"Recipes using this color:\n{recipe_list}\n\n"
            "Choose how to proceed:"
        )

        # إنشاء حوار مخصص مع خيارات
        result = self._show_deletion_options_dialog(message, num_recipes)

        if result == "cancel":
            return
        elif result == "delete_recipes":
            # حذف جميع الوصفات التي تستخدم هذا اللون، ثم حذف اللون
            self._delete_recipes_and_color(recipes_using_color)
        elif result == "manage_manually":
            # فتح ActiveColorsWindow للإدارة اليدوية
            self._open_colors_in_use_window()

    def _show_deletion_options_dialog(self, message, num_recipes):
        """عرض حوار مخصص مع خيارات الحذف"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Color Deletion Options")
        dialog.geometry("500x300")
        _show_on_top(dialog, self.window)

        # توسيط الحوار
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        ttk.Label(dialog, text=message, wraplength=450, justify="left").pack(pady=20, padx=20)

        result = {"choice": None}

        def set_choice(choice):
            result["choice"] = choice
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)

        # خيار 1: الإلغاء
        ttk.Button(button_frame, text="Cancel",
                  command=lambda: set_choice("cancel")).pack(side=tk.LEFT, padx=5)

        # خيار 2: حذف الوصفات واللون (إذا لم يكن عدد الوصفات كبيراً جداً)
        if num_recipes <= 10:  # حد أمان
            ttk.Button(button_frame, text="Delete All Recipes & Color",
                      command=lambda: set_choice("delete_recipes")).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Label(button_frame, text="(Too many recipes to auto-delete)",
                     foreground="red").pack(side=tk.LEFT, padx=5)

        # خيار 3: الإدارة اليدوية
        ttk.Button(button_frame, text="Manage Manually",
                  command=lambda: set_choice("manage_manually")).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()
        return result["choice"]

    def _delete_recipes_and_color(self, recipes_using_color):
        """حذف جميع الوصفات التي تستخدم اللون، ثم حذف اللون نفسه"""
        try:
            # تأكيد الإجراء المدمر
            recipe_codes = [recipe.recipe_code for recipe in recipes_using_color]
            recipe_list = "\n".join([f"- {code}" for code in recipe_codes])

            confirm_msg = (
                f"WARNING: This will permanently delete {len(recipes_using_color)} recipe(s) and the color!\n\n"
                f"Recipes to be deleted:\n{recipe_list}\n\n"
                f"Color to be deleted: {self.original_color_code}\n\n"
                "This action CANNOT be undone!\n\n"
                "Are you absolutely sure?"
            )

            if not messagebox.askyesno("Confirm Mass Deletion", confirm_msg, parent=self.window):
                return

            # الحصول على ID اللون
            color = self.db.get_color_by_code(self.original_color_code)
            if not color:
                messagebox.showerror("Error", "Color not found.", parent=self.window)
                return

            # حذف الوصفات واللون باستخدام دالة قاعدة البيانات
            recipe_ids = [recipe.id for recipe in recipes_using_color]
            success = self.db.delete_color_and_associated_recipes(color.id, recipe_ids)

            if success:
                messagebox.showinfo("Success",
                                   f"Successfully deleted {len(recipes_using_color)} recipe(s) and color '{self.original_color_code}'.",
                                   parent=self.window)
                if self.callback:
                    self.callback()
                self.window.destroy()
            else:
                messagebox.showerror("Error", "Failed to delete recipes and color.", parent=self.window)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete recipes and color: {str(e)}", parent=self.window)

    def _open_colors_in_use_window(self):
        """فتح ActiveColorsWindow للإدارة اليدوية"""
        try:
            ActiveColorsWindow(self.window, self.db, initial_search_code=self.original_color_code)
        except ImportError:
            messagebox.showerror("Error", "Could not import the 'Active Colors' window component.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open 'Active Colors' window: {str(e)}", parent=self.window)

    def _confirm_and_delete_color(self):
        """تأكيد وحذف لون غير مستخدم"""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete color '{self.original_color_code}'?\n\n"
            "This action cannot be undone!",
            parent=self.window
        )

        if not confirm:
            return

        color_to_delete = self.db.get_color_by_code(self.original_color_code)
        if not color_to_delete:
            messagebox.showwarning("Warning", "Color not found.", parent=self.window)
            return

        success = self.db.delete_color(color_to_delete.id)

        if success:
            messagebox.showinfo("Success", f"Color '{self.original_color_code}' deleted successfully.", parent=self.window)
            if self.callback:
                self.callback()
            self.window.destroy()
        else:
            messagebox.showwarning("Warning", "Color could not be deleted. It might have already been removed.", parent=self.window)


# ============================================
# النافذة الرئيسية
# ============================================
class ActiveColorsWindow:
    """نافذة الألوان النشطة"""

    def __init__(self, parent, db, initial_search_code: str = None, on_data_changed=None, dark_mode: bool = False):
        self.parent = parent
        self.db = db
        self.session = SessionManager.get_session()
        self.on_data_changed = on_data_changed
        self.dark_mode = dark_mode

        self.window = tk.Toplevel(parent)
        _show_on_top(self.window, parent)
        self.window.title("Active Colors")
        
        # ضبط أبعاد النافذة لتكون متجاوبة
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.86)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # السماح بالتكبير والتصغير وإظهار أزرار التحكم
        self.window.resizable(True, True)
        self.window.minsize(980, 700)

        # Keep this as a normal top-level window (with full title-bar controls).

        # متغيرات
        self.color_usage: Dict[str, Dict[str, Any]] = {}

        # متغيرات الترتيب
        self.sort_column_colors = "code"
        self.sort_reverse_colors = False
        self.sort_column_recipes = "recipe_code"
        self.sort_reverse_recipes = False

        # تهيئة الأنماط
        self.configure_styles()

        # إنشاء الواجهة
        self.setup_ui()

        # تحميل البيانات
        self.load_data()

        # If an initial color code is provided, search and select this exact color.
        if initial_search_code:
            normalized_code = clean_color_code(initial_search_code)
            self.search_code_var.set(normalized_code)
            self.perform_search()
            self._select_color_in_tree(normalized_code)

    def configure_styles(self):
        """تكوين أنماط الواجهة"""
        style = ttk.Style(self.window)
        palette = get_theme_tokens(self.dark_mode)
        apply_excel_treeview_style(style, palette, self.dark_mode)
        style.configure('Sub.TButton',
                        font=('Arial', 10, 'bold'),
                        padding=6,
                        background='#3498DB',
                        foreground='white')
        style.map('Sub.TButton',
                  background=[('active', '#2980B9')])

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # الإطار الرئيسي
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # إطار البحث والتصفية
        search_frame = ttk.LabelFrame(self.main_frame, text="Color Filters", padding=10)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        # البحث بالكود
        ttk.Label(search_frame, text="Color Code:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.search_code_var = tk.StringVar()
        self.search_code_entry = ttk.Entry(search_frame, textvariable=self.search_code_var, width=15)
        self.search_code_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.search_code_entry.bind('<KeyRelease>', lambda e: self.perform_search())

        # البحث بالاسم
        ttk.Label(search_frame, text="Color Name:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.search_name_var = tk.StringVar()
        self.search_name_entry = ttk.Entry(search_frame, textvariable=self.search_name_var, width=20)
        self.search_name_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.search_name_entry.bind('<KeyRelease>', lambda e: self.perform_search())

        ttk.Button(search_frame, text="Clear",
                   command=self.reset_search, width=10, style='Sub.TButton').grid(row=0, column=5, padx=5, pady=5)

        # إطار قائمة الألوان المستخدمة
        list_frame = ttk.LabelFrame(self.main_frame, text="Active Colors", padding=10)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # شجرة الألوان المستخدمة مع دعم الترتيب
        self.colors_tree = ttk.Treeview(
            list_frame,
            columns=("code", "name", "dye_type", "recipes_count", "total_percentage", "status"),
            show="headings",
            height=12
        )

        # تعريف عناوين الأعمدة مع دعم الترتيب
        self.colors_tree.heading("code", text="Color Code",
                                 command=lambda: self.sort_treeview(self.colors_tree, "code", False))
        self.colors_tree.heading("name", text="Color Name",
                                 command=lambda: self.sort_treeview(self.colors_tree, "name", False))
        self.colors_tree.heading("dye_type", text="Type",
                                 command=lambda: self.sort_treeview(self.colors_tree, "dye_type", False))
        self.colors_tree.heading("recipes_count", text="Recipes Count",
                                 command=lambda: self.sort_treeview(self.colors_tree, "recipes_count", False))
        self.colors_tree.heading("total_percentage", text="Total %",
                                 command=lambda: self.sort_treeview(self.colors_tree, "total_percentage", False))
        self.colors_tree.heading("status", text="Status",
                                 command=lambda: self.sort_treeview(self.colors_tree, "status", False))

        self.colors_tree.column("code", width=100, anchor="center")
        self.colors_tree.column("name", width=150, anchor="center")
        self.colors_tree.column("dye_type", width=100, anchor="center")
        self.colors_tree.column("recipes_count", width=100, anchor="center")
        self.colors_tree.column("total_percentage", width=100, anchor="center")
        self.colors_tree.column("status", width=100, anchor="center")

        # إطار تفاصيل الريتشتات
        details_frame = ttk.LabelFrame(
            self.main_frame,
            text="Recipes Using This Color",
            padding=10
        )
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # شجرة الريتشتات مع دعم الترتيب
        self.recipes_tree = ttk.Treeview(
            details_frame,
            columns=("recipe_code", "recipe_name", "percentage", "recipe_id"),
            show="headings",
            height=12
        )

        self.recipes_tree.heading("recipe_code", text="Recipe Code",
                                  command=lambda: self.sort_treeview(self.recipes_tree, "recipe_code", True))
        self.recipes_tree.heading("recipe_name", text="Recipe Name",
                                  command=lambda: self.sort_treeview(self.recipes_tree, "recipe_name", True))
        self.recipes_tree.heading("percentage", text="Color %",
                                  command=lambda: self.sort_treeview(self.recipes_tree, "percentage", True))
        self.recipes_tree.heading("recipe_id", text="Recipe ID",
                                  command=lambda: self.sort_treeview(self.recipes_tree, "recipe_id", True))

        self.recipes_tree.column("recipe_code", width=150, anchor="center")
        self.recipes_tree.column("recipe_name", width=200, anchor="center")
        self.recipes_tree.column("percentage", width=100, anchor="center")
        self.recipes_tree.column("recipe_id", width=80, anchor="center", stretch=False)

        # أشرطة التمرير
        scrollbar_colors = ttk.Scrollbar(list_frame, orient="vertical", command=self.colors_tree.yview)
        self.colors_tree.configure(yscrollcommand=scrollbar_colors.set)
        scrollbar_colors.pack(side=tk.RIGHT, fill=tk.Y)
        self.colors_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        setup_tree_tags(self.colors_tree, self.dark_mode)

        scrollbar_recipes = ttk.Scrollbar(details_frame, orient="vertical", command=self.recipes_tree.yview)
        self.recipes_tree.configure(yscrollcommand=scrollbar_recipes.set)
        scrollbar_recipes.pack(side=tk.RIGHT, fill=tk.Y)
        self.recipes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        setup_tree_tags(self.recipes_tree, self.dark_mode)

        # أزرار التحكم
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=6)

        self.modify_color_btn = ttk.Button(
            control_frame,
            text="Modify Color",
            command=self.modify_color,
            style='Sub.TButton'
        )
        self.modify_color_btn.pack(side=tk.LEFT, padx=5)
        if self.session.get_current_role() == "viewer":
            self.modify_color_btn.state(["disabled"])
        ttk.Button(control_frame, text="Show Recipe",
                   command=self.show_recipe_details, style='Sub.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Refresh",
                   command=self.refresh_window, style='Sub.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Close",
                   command=self.window.destroy, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        # شريط الحالة
        self.status_label = ttk.Label(self.window, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

        # ربط الأحداث
        self.colors_tree.bind("<<TreeviewSelect>>", self.show_color_recipes)
        self.recipes_tree.bind("<Double-1>", self.on_recipe_double_click)

    def perform_search(self):
        """تنفيذ البحث عن الألوان"""
        try:
            search_code = self.search_code_var.get().strip()
            search_name = self.search_name_var.get().strip()

            if not search_code and not search_name:
                # إذا كان البحث فارغاً، عرض جميع الألوان المستخدمة
                self.load_data()
                return

            # تصفية الألوان المستخدمة حسب البحث
            filtered_usage = {}

            for color_code, usage_info in self.color_usage.items():
                color_info = usage_info.get('color_info')
                if not color_info:
                    continue

                # البحث بالكود
                code_match = search_code.upper() in color_code.upper() if search_code else True

                # البحث بالاسم
                name_match = search_name.lower() in color_info['name'].lower() if search_name else True

                if code_match and name_match:
                    filtered_usage[color_code] = usage_info

            # عرض النتائج
            self.color_usage = filtered_usage
            self.populate_colors_tree()

            # تحديث شريط الحالة
            self.status_label.config(text=f"Found {len(filtered_usage)} color(s)")

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}", parent=self.window)

    def reset_search(self):
        """إعادة تعيين البحث"""
        self.search_code_var.set("")
        self.search_name_var.set("")
        self.load_data()
        self.search_code_entry.focus()

    def _select_color_in_tree(self, color_code: str):
        """Select a specific color row by exact code and show its recipes."""
        target_code = clean_color_code(color_code)
        if not target_code:
            return

        for item_id in self.colors_tree.get_children():
            values = self.colors_tree.item(item_id, "values")
            if not values:
                continue
            row_code = clean_color_code(values[0])
            if row_code == target_code:
                self.colors_tree.selection_set(item_id)
                self.colors_tree.focus(item_id)
                self.colors_tree.see(item_id)
                self.show_color_recipes()
                return

    def sort_treeview(self, treeview, column, is_recipes_tree=False):
        """
        ترتيب Treeview حسب العمود

        Args:
            treeview: كائن Treeview
            column: اسم العمود للترتيب
            is_recipes_tree: True إذا كانت شجرة الريتشتات
        """
        # تحديث حالة الترتيب
        if is_recipes_tree:
            if column == self.sort_column_recipes:
                self.sort_reverse_recipes = not self.sort_reverse_recipes
            else:
                self.sort_column_recipes = column
                self.sort_reverse_recipes = False
            reverse = self.sort_reverse_recipes
        else:
            if column == self.sort_column_colors:
                self.sort_reverse_colors = not self.sort_reverse_colors
            else:
                self.sort_column_colors = column
                self.sort_reverse_colors = False
            reverse = self.sort_reverse_colors

        # الحصول على البيانات من الشجرة
        data = []
        for item in treeview.get_children():
            values = treeview.item(item, 'values')
            data.append(values)

        # فرز البيانات حسب نوع العمود
        try:
            if column == "recipes_count":
                # فرز عدد الوصفات كرقم
                data.sort(key=lambda x: int(x[3]) if x[3] else 0, reverse=reverse)
            elif column == "total_percentage":
                # فرز النسبة المئوية كرقم
                data.sort(key=lambda x: float(x[4].replace('%', '')) if x[4] else 0.0, reverse=reverse)
            elif column == "percentage":
                # فرز النسبة المئوية للريتشتات كرقم
                data.sort(key=lambda x: float(x[2].replace('%', '')) if x[2] else 0.0, reverse=reverse)
            elif column == "recipe_id":
                # فرز ID كرقم
                data.sort(key=lambda x: int(x[3]) if x[3] else 0, reverse=reverse)
            elif column == "status":
                # فرز الحالة نصياً
                data.sort(key=lambda x: x[5] if len(x) > 5 else "", reverse=reverse)
            else:
                # فرز النص (الكود، الاسم، النوع)
                column_index = {
                    "code": 0, "name": 1, "dye_type": 2,
                    "recipe_code": 0, "recipe_name": 1
                }.get(column, 0)

                if column_index < len(data[0]) if data else 0:
                    data.sort(key=lambda x: x[column_index], reverse=reverse)
                else:
                    data.sort(key=lambda x: str(x), reverse=reverse)
        except (ValueError, IndexError) as e:
            print(f"Sort error: {str(e)}")
            return

        # تحديث الشجرة
        for item in treeview.get_children():
            treeview.delete(item)

        for values in data:
            zebra_insert(treeview, values)

        # تحديث عنوان العمود للإشارة للاتجاه
        direction = "(desc)" if reverse else "(asc)"

        # إزالة أي أسهم سابقة وإضافة السهم الجديد
        current_text = treeview.heading(column)["text"]
        clean_text = current_text.replace(" (desc)", "").replace(" (asc)", "").replace("(desc)", "").replace("(asc)", "")
        treeview.heading(column, text=f"{clean_text} {direction}")

    def load_data(self):
        """تحميل البيانات"""
        try:
            # استخدام الدالة من DatabaseManager
            self.color_usage = self.db.get_colors_in_use()

            self.populate_colors_tree()

            if not self.color_usage:
                self.status_label.config(text="No colors in use")
            else:
                self.status_label.config(text=f"Loaded {len(self.color_usage)} color(s) in use")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}", parent=self.window)
            self.status_label.config(text="Error loading data")

    def populate_colors_tree(self):
        """ملء شجرة الألوان"""
        # مسح الشجرة
        for item in self.colors_tree.get_children():
            self.colors_tree.delete(item)

        if not self.color_usage:
            zebra_insert(self.colors_tree, ("No colors in use", "", "", "", "", "No usage"))
            return

        colors_list = []
        for color_code, usage_info in self.color_usage.items():
            if usage_info.get('color_info'):
                color_info = usage_info['color_info']

                # تحديد حالة اللون
                status = "Active"
                if usage_info['total_recipes'] > 5:
                    status = "Heavily Used"
                elif usage_info['total_recipes'] == 0:
                    status = "Not Used"

                colors_list.append({
                    'code': color_code.upper(),
                    'name': color_info['name'],
                    'dye_type': color_info['dye_type'],
                    'recipes_count': usage_info['total_recipes'],
                    'total_percentage': usage_info['total_percentage'],
                    'status': status
                })

        # فرز القائمة حسب العمود الحالي
        if self.sort_column_colors == "recipes_count":
            colors_list.sort(key=lambda x: x['recipes_count'], reverse=self.sort_reverse_colors)
        elif self.sort_column_colors == "total_percentage":
            colors_list.sort(key=lambda x: x['total_percentage'], reverse=self.sort_reverse_colors)
        elif self.sort_column_colors == "status":
            colors_list.sort(key=lambda x: x['status'], reverse=self.sort_reverse_colors)
        elif self.sort_column_colors == "name":
            colors_list.sort(key=lambda x: x['name'].lower(), reverse=self.sort_reverse_colors)
        elif self.sort_column_colors == "dye_type":
            colors_list.sort(key=lambda x: x['dye_type'], reverse=self.sort_reverse_colors)
        else:  # code
            colors_list.sort(key=lambda x: x['code'], reverse=self.sort_reverse_colors)

        # إضافة البيانات للشجرة
        for color in colors_list:
            zebra_insert(self.colors_tree, (
                color['code'],
                color['name'],
                color['dye_type'],
                color['recipes_count'],
                f"{color['total_percentage']:.2f}%",
                color['status']
            ))

    def show_color_recipes(self, event=None):
        """عرض الريتشتات التي يستخدم فيها اللون المحدد"""
        # مسح شجرة الريتشتات
        for item in self.recipes_tree.get_children():
            self.recipes_tree.delete(item)

        selected = self.colors_tree.selection()
        if not selected:
            return

        color_code_display = self.colors_tree.item(selected[0])["values"][0]
        color_code = clean_color_code(color_code_display)

        if color_code in self.color_usage:
            usage_info = self.color_usage[color_code]

            if usage_info['recipes']:
                recipes_list = []
                for recipe in usage_info['recipes']:
                    recipes_list.append({
                        'recipe_code': recipe['recipe_code'] if recipe['recipe_code'] else "No Code",
                        'recipe_name': recipe['recipe_name'],
                        'percentage': recipe['percentage'],
                        'recipe_id': recipe['recipe_id']
                    })

                # فرز القائمة حسب العمود الحالي
                if self.sort_column_recipes == "percentage":
                    recipes_list.sort(key=lambda x: x['percentage'], reverse=self.sort_reverse_recipes)
                elif self.sort_column_recipes == "recipe_name":
                    recipes_list.sort(key=lambda x: x['recipe_name'].lower(), reverse=self.sort_reverse_recipes)
                elif self.sort_column_recipes == "recipe_id":
                    recipes_list.sort(key=lambda x: x['recipe_id'], reverse=self.sort_reverse_recipes)
                else:  # recipe_code
                    recipes_list.sort(key=lambda x: x['recipe_code'], reverse=self.sort_reverse_recipes)

                # إضافة البيانات للشجرة
                for recipe in recipes_list:
                    zebra_insert(self.recipes_tree, (
                        recipe['recipe_code'],
                        recipe['recipe_name'],
                        f"{recipe['percentage']:.2f}%",
                        recipe['recipe_id']
                    ))
            else:
                zebra_insert(self.recipes_tree, ("No recipes found", "", "", ""))

    def modify_color(self):
        """تعديل اللون المحدد"""
        if self.session.get_current_role() == "viewer":
            messagebox.showwarning("Permission Denied", "You do not have permission to modify colors here.", parent=self.window)
            return
        selected = self.colors_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a color to modify", parent=self.window)
            return

        try:
            color_code_display = self.colors_tree.item(selected[0])["values"][0]
            color_code = clean_color_code(color_code_display)


            # ✅ استخدم SimpleColorsWindow مباشرة مع دالة callback للتحديث
            SimpleColorsWindow(
                self.window,
                self.db,
                color_code,
                callback=self._on_color_changed,
                dark_mode=self.dark_mode
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open color window: {str(e)}", parent=self.window)

    def _on_color_changed(self):
        """Handle color change and notify parent window."""
        try:
            # إعادة تحميل البيانات
            self.load_data()

            # مسح شجرة الريتشتات أيضاً
            for item in self.recipes_tree.get_children():
                self.recipes_tree.delete(item)

            self.status_label.config(text="Data refreshed successfully")
            if callable(self.on_data_changed):
                self.on_data_changed()

        except Exception as e:
            self.status_label.config(text="Error refreshing data")

    def show_recipe_details(self):
        """عرض تفاصيل الريتشت المحددة"""
        selected = self.recipes_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a recipe to view", parent=self.window)
            return

        recipe_id = self.recipes_tree.item(selected[0])["values"][3]

        # فتح نافذة تفاصيل الريتشت
        try:
            from ui.saved_recipes_window import SavedRecipesWindow
            SavedRecipesWindow(
                self.window,
                self.db,
                recipe_id,
                on_data_changed=self._on_color_changed
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open recipe window: {str(e)}", parent=self.window)

    def on_recipe_double_click(self, event):
        """عند النقر المزدوج على الريتشت"""
        self.show_recipe_details()

    def refresh_window(self):
        """تحديث النافذة"""
        self.load_data()


# Backward-compatible alias for older imports.
ColorsInUseWindow = ActiveColorsWindow

