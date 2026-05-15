"""
نافذة عرض الألوان المستخدمة في الريتشتات
"""
import tkinter as tk
import sqlite3
import os
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional
from datetime import datetime
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
    show_on_top,
)





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

        # [OK] أنواع الصبغة من CONFIG (متطابقة مع Add color)
        self.dye_types = DYE_TYPES

        self.window = tk.Toplevel(parent)
        show_on_top(self.window, parent)
        self.window.title(f"Modify Color: {color_code}")

        # توسيط النافذة في منتصف الشاشة
        width, height = 500, 550
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")

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
                        id=row[0],
                        code=row[1],
                        name=row[2],
                        dye_type=row[3],
                        supplier=row[4],
                        price_kg=row[5],
                        resa_percent=row[6],
                        current_lotto=row[9],
                        created_at=row[7],
                        updated_at=row[8]
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
                    'lotto': getattr(color, 'current_lotto', ''),
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

        # [OK] إطار الحقول - مضغوط
        fields_frame = ttk.LabelFrame(main_frame, text="Color Details", padding=10)
        fields_frame.pack(fill=tk.X, pady=(0, 10))

        # [OK] استخدام grid مع مسافات صغيرة
        row = 0

        # كود اللون
        ttk.Label(fields_frame, text="Code:",
                  font=('Arial', 9)).grid(
            row=row, column=0, sticky="e", padx=5, pady=3)  # <- مسافات صغيرة
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

        # المورد
        ttk.Label(fields_frame, text="Supplier:",
                  font=('Arial', 9)).grid(
            row=row, column=0, sticky="e", padx=5, pady=3)
        self.supplier_var = tk.StringVar(value=self.color_data.get('supplier', ''))
        self.supplier_entry = ttk.Entry(fields_frame, textvariable=self.supplier_var,
                                        width=30, font=('Arial', 9))
        self.supplier_entry.grid(row=row, column=1, padx=5, pady=3, sticky="w")
        row += 1

        # Lotto
        ttk.Label(fields_frame, text="Current Lotto:",
                  font=('Arial', 9)).grid(
            row=row, column=0, sticky="e", padx=5, pady=3)
        self.lotto_var = tk.StringVar(value=self.color_data.get('lotto', ''))
        self.lotto_entry = ttk.Entry(fields_frame, textvariable=self.lotto_var,
                                        width=30, font=('Arial', 9))
        self.lotto_entry.grid(row=row, column=1, padx=5, pady=3, sticky="w")
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

        # [OK] معلومات إضافية مضغوطة
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

        # [OK] [OK] [OK] أزرار التحكم - في نفس السطر مضغوطة
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 10))

        # [OK] زر الحفظ - واضح لكن مضغوط
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

        # [OK] زر الحذف
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

        # [OK] زر الإلغاء
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

        # [OK] ربط أحداث لوحة المفاتيح
        self.window.bind('<Return>', lambda e: self.save_changes())
        self.window.bind('<Control-s>', lambda e: self.save_changes())
        self.window.bind('<Escape>', lambda e: self.window.destroy())

        # [OK] Focus على أول حقل
        self.code_entry.focus_set()

    def save_changes(self):
        """حفظ التغييرات - مع رسائل واضحة"""
        if not self.session.has_permission("can_edit"):
            messagebox.showwarning(
                "Permission Denied",
                "You do not have permission to edit colors.",
                parent=self.window,
            )
            return
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
                'resa_percent': resa_percent,
                'lotto': self.lotto_var.get().strip()
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

                # [OK] استدعاء دالة الرد للتحديث
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
                current_lotto=color_data['lotto'],
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
        show_on_top(dialog, self.window)

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
        show_on_top(self.window, parent)
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
        self._all_color_usage: Dict[str, Dict[str, Any]] = {}

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

        # إضافة نمط الزر الأحمر (Danger)
        style.configure('Danger.Sub.TButton',
                        font=('Arial', 10, 'bold'),
                        padding=6,
                        background='#dc3545',
                        foreground='white')
        style.map('Danger.Sub.TButton',
                  background=[('active', '#c82333')])

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
            columns=("code", "name", "dye_type", "lotto", "resa", "recipes_count", "total_percentage"),
            show="headings",
            height=12
        )

        self.colors_tree.heading("code", text="Color Code",
                                 command=lambda: self.sort_treeview(self.colors_tree, "code", False))
        self.colors_tree.heading("name", text="Color Name",
                                 command=lambda: self.sort_treeview(self.colors_tree, "name", False))
        self.colors_tree.heading("dye_type", text="Type",
                                 command=lambda: self.sort_treeview(self.colors_tree, "dye_type", False))
        self.colors_tree.heading("lotto", text="Lotto",
                                 command=lambda: self.sort_treeview(self.colors_tree, "lotto", False))
        self.colors_tree.heading("resa", text="RESA %",
                                 command=lambda: self.sort_treeview(self.colors_tree, "resa", False))
        self.colors_tree.heading("recipes_count", text="Recipes",
                                 command=lambda: self.sort_treeview(self.colors_tree, "recipes_count", False))
        self.colors_tree.heading("total_percentage", text="Total %",
                                 command=lambda: self.sort_treeview(self.colors_tree, "total_percentage", False))

        self.colors_tree.column("code",            width=95,  anchor="center")
        self.colors_tree.column("name",            width=140, anchor="center")
        self.colors_tree.column("dye_type",        width=90,  anchor="center")
        self.colors_tree.column("lotto",           width=90,  anchor="center")
        self.colors_tree.column("resa",            width=80,  anchor="center")
        self.colors_tree.column("recipes_count",   width=90,  anchor="center")
        self.colors_tree.column("total_percentage",width=80,  anchor="center")

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
            columns=("recipe_code", "recipe_name", "percentage"),
            show="headings",
            height=12
        )

        self.recipes_tree.heading("recipe_code", text="Recipe Code",
                                  command=lambda: self.sort_treeview(self.recipes_tree, "recipe_code", True))
        self.recipes_tree.heading("recipe_name", text="Recipe Name",
                                  command=lambda: self.sort_treeview(self.recipes_tree, "recipe_name", True))
        self.recipes_tree.heading("percentage", text="Color %",
                                  command=lambda: self.sort_treeview(self.recipes_tree, "percentage", True))

        self.recipes_tree.column("recipe_code", width=150, anchor="center")
        self.recipes_tree.column("recipe_name", width=200, anchor="center")
        self.recipes_tree.column("percentage", width=100, anchor="center")

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
        self.delete_used_color_btn = ttk.Button(
            control_frame,
            text="Delete Used Color",
            command=self.delete_selected_color_with_recipes,
            style='Danger.Sub.TButton'
        )
        self.delete_used_color_btn.pack(side=tk.LEFT, padx=5)
        if self.session.get_current_role() != "admin":
            self.delete_used_color_btn.state(["disabled"])
        ttk.Button(control_frame, text="Show Recipe",
                   command=self.show_recipe_details, style='Sub.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🗂  Manage Lotto",
                   command=self.manage_lotto, style='Sub.TButton').pack(side=tk.LEFT, padx=5)
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
                self.populate_colors_tree(self._all_color_usage)
                return

            # تصفية الألوان المستخدمة حسب البحث
            filtered_usage = {}

            for color_code, usage_info in self._all_color_usage.items():
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
            self.populate_colors_tree(filtered_usage)

            # تحديث شريط الحالة
            self.status_label.config(text=f"Found {len(filtered_usage)} color(s)")

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}", parent=self.window)

    def reset_search(self):
        """إعادة تعيين البحث"""
        self.search_code_var.set("")
        self.search_name_var.set("")
        self.populate_colors_tree(self._all_color_usage)
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
                data.sort(key=lambda x: int(x[5]) if x[5] else 0, reverse=reverse)
            elif column == "resa":
                data.sort(key=lambda x: float(str(x[4]).replace('%', '').strip()) if x[4] else 0.0, reverse=reverse)
            elif column == "total_percentage":
                # فرز النسبة المئوية كرقم
                data.sort(key=lambda x: float(x[6].replace('%', '')) if x[6] else 0.0, reverse=reverse)
            elif column == "percentage":
                # فرز النسبة المئوية للريتشتات كرقم
                data.sort(key=lambda x: float(x[2].replace('%', '')) if x[2] else 0.0, reverse=reverse)
            else:
                # فرز النص (الكود، الاسم، النوع)
                column_index = {
                    "code": 0, "name": 1, "dye_type": 2, "lotto": 3,
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
            self._all_color_usage = self.db.get_colors_in_use() or {}
            self.color_usage = self._all_color_usage
            self.perform_search()

            if not self._all_color_usage:
                self.status_label.config(text="No colors in use")
            else:
                self.status_label.config(text=f"Loaded {len(self._all_color_usage)} color(s) in use")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}", parent=self.window)
            self.status_label.config(text="Error loading data")

    def populate_colors_tree(self, usage_map: Optional[Dict[str, Dict[str, Any]]] = None):
        """ملء شجرة الألوان"""
        # مسح الشجرة
        for item in self.colors_tree.get_children():
            self.colors_tree.delete(item)

        if usage_map is None:
            usage_map = self._all_color_usage
        self.color_usage = usage_map

        if not usage_map:
            zebra_insert(self.colors_tree, ("No colors in use", "", "", "", "", "", ""))
            return

        colors_list = []
        for color_code, usage_info in usage_map.items():
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
                    'lotto': color_info.get('current_lotto', '') or '—',
                    'resa': float(color_info.get('resa_percent', 100.0) or 100.0),
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
        elif self.sort_column_colors == "resa":
            colors_list.sort(key=lambda x: x['resa'], reverse=self.sort_reverse_colors)
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
                color['lotto'],
                f"{color['resa']:.1f}%",
                color['recipes_count'],
                f"{color['total_percentage']:.2f}%"
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
                else:  # recipe_code
                    recipes_list.sort(key=lambda x: x['recipe_code'], reverse=self.sort_reverse_recipes)

                # إضافة البيانات للشجرة
                for recipe in recipes_list:
                    zebra_insert(
                        self.recipes_tree,
                        (
                            recipe['recipe_code'],
                            recipe['recipe_name'],
                            f"{recipe['percentage']:.2f}%"
                        ),
                        iid=str(recipe['recipe_id'])
                    )
            else:
                zebra_insert(self.recipes_tree, ("No recipes found", "", ""))

    def modify_color(self):
        """تعديل اللون المحدد"""
        if not self.session.has_permission("can_edit"):
            messagebox.showwarning(
                "Permission Denied",
                "You do not have permission to modify colors here.",
                parent=self.window,
            )
            return
        selected = self.colors_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a color to modify", parent=self.window)
            return

        try:
            color_code_display = self.colors_tree.item(selected[0])["values"][0]
            color_code = clean_color_code(color_code_display)


            # [OK] استخدم SimpleColorsWindow مباشرة مع دالة callback للتحديث
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

        recipe_id = selected[0]
        try:
            recipe_id = int(recipe_id)
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Unable to determine the recipe ID for the selected row.", parent=self.window)
            return

        try:
            from ui.saved_recipes_window import SavedRecipesWindow
            SavedRecipesWindow(
                self.window,
                self.db,
                recipe_id,
                on_data_changed=self._on_color_changed,
                dark_mode=self.dark_mode
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open recipe window: {str(e)}", parent=self.window)

    def on_recipe_double_click(self, event):
        """عند النقر المزدوج على الريتشت"""
        self.show_recipe_details()

    def delete_selected_color_with_recipes(self):
        """Admin-only: delete selected color after deleting all recipes that use it."""
        if self.session.get_current_role() != "admin":
            messagebox.showwarning(
                "Permission Denied",
                "Only admin can delete a used color with its recipes.",
                parent=self.window
            )
            return

        code = self._get_selected_color_code()
        if not code:
            messagebox.showwarning("No Selection", "Please select a color first.", parent=self.window)
            return

        normalized_code = clean_color_code(code)
        color_obj = self.db.get_color_by_code(normalized_code)
        if not color_obj:
            messagebox.showerror("Error", f"Color {normalized_code} not found.", parent=self.window)
            return

        recipes_using_color = self.db.get_recipes_using_color(normalized_code)
        recipe_ids = [recipe.id for recipe in recipes_using_color]

        if recipe_ids:
            preview_lines = [f"- {r.recipe_code}: {r.name}" for r in recipes_using_color[:8]]
            if len(recipes_using_color) > 8:
                preview_lines.append(f"... and {len(recipes_using_color) - 8} more")
            recipes_preview = "\n".join(preview_lines)
            msg = (
                f"This will delete color '{normalized_code}' and {len(recipe_ids)} recipe(s) using it.\n\n"
                f"Recipes:\n{recipes_preview}\n\n"
                "This action cannot be undone.\n\nContinue?"
            )
        else:
            msg = (
                f"Color '{normalized_code}' is not used in any recipe.\n\n"
                "Delete this color?\n\nThis action cannot be undone."
            )

        confirm = messagebox.askyesno("Confirm Delete", msg, parent=self.window)
        if not confirm:
            return

        try:
            if recipe_ids:
                success = self.db.delete_color_and_associated_recipes(color_obj.id, recipe_ids)
            else:
                success = self.db.delete_color(color_obj.id)

            if not success:
                messagebox.showerror("Error", "Delete operation failed.", parent=self.window)
                return

            if recipe_ids:
                messagebox.showinfo(
                    "Deleted",
                    f"Deleted color '{normalized_code}' and {len(recipe_ids)} recipe(s).",
                    parent=self.window
                )
            else:
                messagebox.showinfo("Deleted", f"Deleted color '{normalized_code}'.", parent=self.window)

            self.refresh_window()
            if callable(self.on_data_changed):
                self.on_data_changed()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete color and recipes: {e}", parent=self.window)

    def _get_selected_color_code(self) -> Optional[str]:
        sel = self.colors_tree.selection()
        if not sel:
            return None
        return str(self.colors_tree.item(sel[0])["values"][0])

    def manage_lotto(self):
        """Open Lotto management dialog for selected color."""
        code = self._get_selected_color_code()
        if not code:
            messagebox.showwarning("No Selection", "Please select a color first.", parent=self.window)
            return
        color_id = self.db.get_color_id_by_code(code)
        if not color_id:
            messagebox.showerror("Error", f"Color {code} not found in database.", parent=self.window)
            return
        LottoManagerDialog(
            self.window,
            self.db,
            color_id=color_id,
            color_code=code,
            session=self.session,
            dark_mode=self.dark_mode,
        )
        self.refresh_window()

    def report_lotto_pdf(self):
        """Export full color report: info + all changes history."""
        code = self._get_selected_color_code()
        if not code:
            messagebox.showwarning("No Selection", "Please select a color first.", parent=self.window)
            return
        color_id = self.db.get_color_id_by_code(code)
        if not color_id:
            messagebox.showerror("Error", f"Color {code} not found.", parent=self.window)
            return

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors as rl_colors
            from reportlab.lib.units import cm
            from datetime import datetime
            from app.utils import get_desktop_exports_dir

            folder = get_desktop_exports_dir()
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            path_pdf = os.path.join(folder, f"ColorReport_{code}_{ts}.pdf")

            doc    = SimpleDocTemplate(path_pdf, pagesize=A4,
                                       leftMargin=2*cm, rightMargin=2*cm,
                                       topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            elems  = []

            # Title
            elems.append(Paragraph(f"Color Report — {code}", styles["Title"]))
            elems.append(Paragraph(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                styles["Normal"]))
            elems.append(Spacer(1, 0.4*cm))

            # Current color info
            color_obj = self.db.get_color_by_code(code)
            if color_obj:
                info_data = [
                    ["Field", "Value"],
                    ["Code",          getattr(color_obj, "code", "—")],
                    ["Name",          getattr(color_obj, "name", "—")],
                    ["Dye Type",      getattr(color_obj, "dye_type", "—")],
                    ["Supplier",      getattr(color_obj, "supplier", "—") or "—"],
                    ["Price/kg (€)",  str(getattr(color_obj, "price_kg", "—"))],
                    ["Resa %",        str(getattr(color_obj, "resa_percent", "—"))],
                    ["Current Lotto", getattr(color_obj, "current_lotto", "—") or "—"],
                    ["Created At",    getattr(color_obj, "created_at", "—")],
                    ["Updated At",    getattr(color_obj, "updated_at", "—")],
                ]
                t = Table(info_data, colWidths=[5*cm, 12*cm])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), rl_colors.HexColor("#1565C0")),
                    ("TEXTCOLOR",  (0,0), (-1,0), rl_colors.white),
                    ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",   (0,0), (-1,-1), 9),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1),
                     [rl_colors.HexColor("#EEF2FF"), rl_colors.white]),
                    ("GRID",  (0,0), (-1,-1), 0.5, rl_colors.grey),
                    ("ALIGN", (0,0), (-1,-1), "LEFT"),
                    ("LEFTPADDING",   (0,0), (-1,-1), 6),
                    ("TOPPADDING",    (0,0), (-1,-1), 4),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ]))
                elems.append(t)
                elems.append(Spacer(1, 0.5*cm))

            # Change History
            history = []
            if hasattr(self.db, "get_color_history"):
                history = self.db.get_color_history(color_id)

            elems.append(HRFlowable(width="100%", thickness=1,
                                    color=rl_colors.HexColor("#1565C0")))
            elems.append(Spacer(1, 0.2*cm))
            elems.append(Paragraph("<b>Change History</b>", styles["Heading2"]))
            elems.append(Spacer(1, 0.2*cm))

            if history:
                hist_data = [["#", "Field", "Old Value", "New Value", "Changed At", "Changed By"]]
                for i, h in enumerate(history, 1):
                    hist_data.append([
                        str(i),
                        h.get("field","—"),
                        h.get("old","—") or "—",
                        h.get("new","—") or "—",
                        h.get("at","—") or "—",
                        h.get("by","—") or "—",
                    ])
                ht = Table(hist_data,
                           colWidths=[0.8*cm, 3.2*cm, 3.5*cm, 3.5*cm, 4.2*cm, 2*cm])
                ht.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), rl_colors.HexColor("#37474F")),
                    ("TEXTCOLOR",  (0,0), (-1,0), rl_colors.white),
                    ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",   (0,0), (-1,-1), 8),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1),
                     [rl_colors.HexColor("#F5F5F5"), rl_colors.white]),
                    ("GRID",  (0,0), (-1,-1), 0.4, rl_colors.grey),
                    ("ALIGN", (0,0), (-1,-1), "LEFT"),
                    ("LEFTPADDING",   (0,0), (-1,-1), 4),
                    ("TOPPADDING",    (0,0), (-1,-1), 3),
                    ("BOTTOMPADDING", (0,0), (-1,-1), 3),
                ]))
                elems.append(ht)
            else:
                elems.append(Paragraph("No change history recorded yet.", styles["Normal"]))

            doc.build(elems)
            messagebox.showinfo("PDF Exported",
                                f"Color report saved to:\n{path_pdf}", parent=self.window)

        except ImportError:
            messagebox.showerror("Error", "reportlab is required for PDF export.", parent=self.window)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to generate report:\n{exc}", parent=self.window)


        """Export a PDF report for the selected color's lottos and history."""
        code = self._get_selected_color_code()
        if not code:
            messagebox.showwarning("No Selection", "Please select a color first.", parent=self.window)
            return
        color_id = self.db.get_color_id_by_code(code)
        if not color_id:
            messagebox.showerror("Error", f"Color {code} not found.", parent=self.window)
            return
        lottos = self.db.get_lottos_for_color(color_id)
        if not lottos:
            messagebox.showinfo("No Lottos", f"No lotto records found for {code}.", parent=self.window)
            return
        # Build PDF
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors as rl_colors
            from reportlab.lib.units import cm
            from datetime import datetime
            from app.utils import get_desktop_exports_dir

            folder = get_desktop_exports_dir()
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            path_pdf = os.path.join(folder, f"LottoReport_{code}_{ts}.pdf")

            doc    = SimpleDocTemplate(path_pdf, pagesize=A4,
                                       leftMargin=2*cm, rightMargin=2*cm,
                                       topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            elems  = []

            elems.append(Paragraph(f"Lotto Report — Color: {code}", styles["Title"]))
            elems.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
            elems.append(Spacer(1, 0.4*cm))

            # Summary table with all lottos
            if len(lottos) > 1:
                elems.append(Paragraph("<b>Lottos Summary</b>", styles["Heading2"]))
                elems.append(Spacer(1, 0.2*cm))
                summary_data = [["#", "Lotto No", "Quantity (kg)", "RESA %"]]
                for i, lotto in enumerate(lottos, 1):
                    resa = lotto.get("resa_percent", 100.0)
                    summary_data.append([
                        str(i),
                        lotto["lotto_no"],
                        f"{lotto['quantity_kg']:.2f}",
                        f"{resa:.1f}%"
                    ])
                st = Table(summary_data, colWidths=[1*cm, 4*cm, 4*cm, 4*cm])
                st.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), rl_colors.HexColor("#1565C0")),
                    ("TEXTCOLOR",  (0,0), (-1,0), rl_colors.white),
                    ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",   (0,0), (-1,-1), 9),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1),
                     [rl_colors.HexColor("#EEF2FF"), rl_colors.white]),
                    ("GRID", (0,0), (-1,-1), 0.5, rl_colors.grey),
                    ("ALIGN", (0,0), (-1,-1), "CENTER"),
                    ("LEFTPADDING", (0,0), (-1,-1), 4),
                ]))
                elems.append(st)
                elems.append(Spacer(1, 0.5*cm))

            for lotto in lottos:
                lid    = lotto["id"]
                ln     = lotto["lotto_no"]
                resa   = lotto.get("resa_percent", 100.0)
                elems.append(Paragraph(f"<b>Lotto No: {ln}</b>", styles["Heading2"]))
                info_data = [
                    ["Field", "Value"],
                    ["Lotto No",    ln],
                    ["Quantity kg", str(lotto["quantity_kg"])],
                    ["RESA %",      f"{resa:.1f}%"],
                    ["Supplier",    lotto["supplier"] or "—"],
                    ["Notes",       lotto["notes"] or "—"],
                    ["Created at",  lotto["created_at"] or "—"],
                    ["Created by",  lotto["created_by"] or "—"],
                ]
                t = Table(info_data, colWidths=[5*cm, 12*cm])
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), rl_colors.HexColor("#1565C0")),
                    ("TEXTCOLOR",  (0,0), (-1,0), rl_colors.white),
                    ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                    ("FONTSIZE",   (0,0), (-1,-1), 9),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1),
                     [rl_colors.HexColor("#EEF2FF"), rl_colors.white]),
                    ("GRID", (0,0), (-1,-1), 0.5, rl_colors.grey),
                    ("ALIGN", (0,0), (-1,-1), "LEFT"),
                    ("LEFTPADDING", (0,0), (-1,-1), 6),
                ]))
                elems.append(t)
                elems.append(Spacer(1, 0.3*cm))

                # History
                history = self.db.get_lotto_history(lid)
                if history:
                    elems.append(Paragraph("Change History:", styles["Heading3"]))
                    hist_data = [["#", "Field", "Old Value", "New Value", "Changed At", "Changed By"]]
                    for i, h in enumerate(history, 1):
                        hist_data.append([
                            str(i), h["field"], h["old"] or "—",
                            h["new"] or "—", h["at"] or "—", h["by"] or "—"
                        ])
                    ht = Table(hist_data, colWidths=[1*cm, 3*cm, 3*cm, 3*cm, 4.5*cm, 2.5*cm])
                    ht.setStyle(TableStyle([
                        ("BACKGROUND", (0,0), (-1,0), rl_colors.HexColor("#37474F")),
                        ("TEXTCOLOR",  (0,0), (-1,0), rl_colors.white),
                        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                        ("FONTSIZE",   (0,0), (-1,-1), 8),
                        ("ROWBACKGROUNDS", (0,1), (-1,-1),
                         [rl_colors.HexColor("#F5F5F5"), rl_colors.white]),
                        ("GRID", (0,0), (-1,-1), 0.4, rl_colors.grey),
                        ("ALIGN", (0,0), (-1,-1), "LEFT"),
                        ("LEFTPADDING", (0,0), (-1,-1), 4),
                    ]))
                    elems.append(ht)
                elems.append(Spacer(1, 0.6*cm))

            doc.build(elems)
            messagebox.showinfo("PDF Exported", f"Report saved to:\n{path_pdf}", parent=self.window)
        except ImportError:
            messagebox.showerror("Error", "reportlab is required for PDF export.", parent=self.window)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to generate report:\n{exc}", parent=self.window)

    def refresh_window(self):
        """تحديث النافذة"""
        self.load_data()


# Backward-compatible alias for older imports.
ColorsInUseWindow = ActiveColorsWindow



# ─── Lotto Manager Dialog ──────────────────────────────────────────────────────

class LottoManagerDialog:
    """Dialog to manage lottos for all colors - like Active Colors window."""

    def __init__(self, parent, db, color_id: int = None, color_code: str = None, session=None, dark_mode: bool = False):
        self.parent   = parent
        self.db       = db
        self.session  = session
        self.username = getattr(session, "get_current_user", lambda: "")() if session else ""
        self.dark_mode = dark_mode

        self.win = tk.Toplevel(parent)
        self.win.title("Manage Lottos - All Colors")
        self.win.grab_set()
        
        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        w, h   = min(int(sw * 0.95), 1400), min(int(sh * 0.9), 700)
        self.win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.win.resizable(True, True)
        self.win.minsize(1100, 550)
        self._left_rows = []
        self._left_sort_column = "code"
        self._left_sort_reverse = False
        self.search_code_var = tk.StringVar()
        self.search_name_var = tk.StringVar()

        # Store all colors with their lottos
        self.colors_lottos = {}
        
        self._build()
        self._load_colors()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        """Build the UI with left tree (colors) and right tree (history)."""
        main = ttk.Frame(self.win)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # ── Left: Colors with current lottos ───────────────────────────
        left_lf = ttk.LabelFrame(main, text="Colors & Current Lottos", padding=8)
        left_lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        search_frame = ttk.Frame(left_lf)
        search_frame.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(search_frame, text="Code:").pack(side=tk.LEFT, padx=(0, 4))
        code_entry = ttk.Entry(search_frame, textvariable=self.search_code_var, width=14)
        code_entry.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(search_frame, text="Name:").pack(side=tk.LEFT, padx=(0, 4))
        name_entry = ttk.Entry(search_frame, textvariable=self.search_name_var, width=18)
        name_entry.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(search_frame, text="Clear", width=8, command=self._clear_left_search).pack(side=tk.LEFT)
        code_entry.bind("<KeyRelease>", lambda _e: self._apply_left_filters_and_sort())
        name_entry.bind("<KeyRelease>", lambda _e: self._apply_left_filters_and_sort())

        self.colors_tree = ttk.Treeview(
            left_lf,
            columns=("code", "name", "dye_type", "lotto", "resa", "updated_at"),
            show="headings",
        )
        for col, text, w in [
            ("code",       "Code",      80),
            ("name",       "Name",     140),
            ("dye_type",   "Type",      80),
            ("lotto",      "Lotto",     90),
            ("resa",       "RESA %",    70),
            ("updated_at", "Updated",  130),
        ]:
            self.colors_tree.heading(col, text=text, command=lambda c=col: self._sort_left_tree(c))
            self.colors_tree.column(col, width=w, anchor="center")
        
        self.colors_tree.column("code",       width=80,  anchor="center")
        self.colors_tree.column("name",      width=140, anchor="w")
        self.colors_tree.column("dye_type",   width=80,  anchor="center")
        self.colors_tree.column("lotto",      width=90, anchor="center")
        self.colors_tree.column("resa",      width=70,  anchor="center")
        self.colors_tree.column("updated_at",width=130, anchor="center")

        sb1 = ttk.Scrollbar(left_lf, orient="vertical", command=self.colors_tree.yview)
        self.colors_tree.configure(yscrollcommand=sb1.set)
        sb1.pack(side=tk.RIGHT, fill=tk.Y)
        self.colors_tree.pack(fill=tk.BOTH, expand=True)
        setup_tree_tags(self.colors_tree, self.dark_mode)
        self.colors_tree.bind("<<TreeviewSelect>>", self._on_color_select)

        # ── Right: Lotto History ─────────────────────────────────────────
        right_lf = ttk.LabelFrame(main, text="Lotto Changes History", padding=8)
        right_lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8,0))

        self.history_tree = ttk.Treeview(
            right_lf,
            columns=("code", "name", "supplier", "dye_type", "lotto", "resa", "updated_at"),
            show="headings",
        )
        for col, text, w in [
            ("code",       "Code",       80),
            ("name",       "Name",      130),
            ("supplier",   "Supplier",  120),
            ("dye_type",   "Type",       80),
            ("lotto",      "Lotto",     100),
            ("resa",       "RESA %",     70),
            ("updated_at", "Updated At", 140),
        ]:
            self.history_tree.heading(col, text=text)
            self.history_tree.column(col, width=w, anchor="center")
        self.history_tree.column("name", anchor="w")

        sb2 = ttk.Scrollbar(right_lf, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=sb2.set)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_tree.pack(fill=tk.BOTH, expand=True)
        setup_tree_tags(self.history_tree, self.dark_mode)

        # ── Bottom: Buttons ─────────────────────────────────────────────
        btn_frame = ttk.Frame(self.win)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0,8))

        style = ttk.Style(self.win)
        style.configure(
            "Danger.Sub.TButton",
            font=("Arial", 10, "bold"),
            padding=6,
            background="#C62828",
            foreground="white",
        )
        style.map(
            "Danger.Sub.TButton",
            background=[("active", "#B71C1C"), ("disabled", "#A0A0A0")],
            foreground=[("disabled", "#F0F0F0")],
        )

        self.reset_btn = ttk.Button(
            btn_frame,
            text="Reset Lotto",
            command=self._reset_lotto_history,
            width=14,
            style="Danger.Sub.TButton",
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        if not self.session or self.session.get_current_role() != "admin":
            self.reset_btn.state(["disabled"])

        ttk.Button(btn_frame, text="📄 Export Report",
                   command=self._export_report, width=16).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="✖ Close",
                   command=self._on_close, width=12).pack(side=tk.RIGHT, padx=5)

        # Status label
        self.status_lbl = ttk.Label(self.win, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_lbl.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

    def _load_colors(self):
        """Load all colors with their current lottos."""
        selected_id = self.colors_tree.selection()[0] if self.colors_tree.selection() else None
        self._left_rows = []
        self.colors_lottos = {}
        
        try:
            color_usage = self.db.get_colors_in_use() or {}
            for color_code, usage_info in color_usage.items():
                color_info = usage_info.get("color_info") or {}
                code = str(color_code).upper()
                color_obj = self.db.get_color_by_code(code)
                if not color_obj:
                    continue
                status = "Active"
                if usage_info.get("total_recipes", 0) > 5:
                    status = "Heavily Used"
                elif usage_info.get("total_recipes", 0) == 0:
                    status = "Not Used"

                row_values = (
                    code,
                    color_info.get("name", ""),
                    color_info.get("dye_type", ""),
                    color_info.get("current_lotto", "") or "—",
                    f"{float(color_info.get('resa_percent', 100.0) or 100.0):.1f}%",
                    self._format_dt(getattr(color_obj, "updated_at", "") or ""),
                )
                self._left_rows.append((code, row_values))
                self.colors_lottos[code] = {
                    "color_id": color_obj.id,
                    "color_obj": color_obj,
                }
            
            self._apply_left_filters_and_sort(selected_id)
            self.status_lbl.config(text=f"Loaded {len(self.colors_lottos)} color(s)")
            
        except Exception as e:
            print(f"Error loading colors: {e}")
            self.status_lbl.config(text=f"Error: {str(e)}")

    def _on_color_select(self, event=None):
        """When a color/lotto is selected, show its history."""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        sel = self.colors_tree.selection()
        if not sel:
            return
        
        item_id = sel[0]
        
        # Check if it's a color-only or color|lotto
        if "|" in item_id:
            code, lotto_no = item_id.split("|", 1)
        else:
            code = item_id
            lotto_no = None
        
        # Find color_id
        color_obj = self.db.get_color_by_code(code)
        if not color_obj:
            return
        
        color_id = color_obj.id
        
        try:
            for values in self._build_color_change_rows(color_obj):
                zebra_insert(self.history_tree, values)
            
            self.status_lbl.config(text=f"Showing history for {code}")
            
        except Exception as e:
            print(f"Error loading history: {e}")

    def _build_color_change_rows(self, color_obj):
        """Build timeline rows from color_history with one row per change batch."""
        history = self.db.get_color_history(color_obj.id) or []
        code = getattr(color_obj, "code", "") or ""
        name = getattr(color_obj, "name", "") or ""
        supplier = getattr(color_obj, "supplier", "") or ""
        dye_type = getattr(color_obj, "dye_type", "") or ""
        lotto_no = str(getattr(color_obj, "current_lotto", "") or "")
        resa = float(getattr(color_obj, "resa_percent", 100.0) or 100.0)
        current = {
            "name": name,
            "supplier": supplier,
            "dye_type": dye_type,
            "lotto_no": lotto_no,
            "resa_percent": resa,
        }

        rows = []
        tracked_fields = {"name", "supplier", "dye_type", "lotto", "resa_percent"}
        def _apply_change(state: dict, field: str, value):
            if field == "name":
                state["name"] = str(value or "")
            elif field == "supplier":
                state["supplier"] = str(value or "")
            elif field == "dye_type":
                state["dye_type"] = str(value or "")
            elif field == "lotto":
                state["lotto_no"] = str(value or "")
            elif field == "resa_percent":
                try:
                    state["resa_percent"] = float(value)
                except (TypeError, ValueError):
                    pass

        # Keep only fields that affect the Manage Lotto history view.
        events = []
        for h in history:
            field = (h.get("field") or "").strip()
            if field in tracked_fields:
                events.append(h)

        if not events:
            rows.append((
                code,
                (current["name"] or "—"),
                (current["supplier"] or "—"),
                (current["dye_type"] or "—"),
                (current["lotto_no"] or "—"),
                f"{float(current['resa_percent']):.1f}%",
                self._format_dt(getattr(color_obj, "updated_at", "") or ""),
            ))
            return rows

        # Reconstruct the earliest known state by walking backward from current values.
        base_state = dict(current)
        for h in reversed(events):
            field = (h.get("field") or "").strip()
            _apply_change(base_state, field, h.get("old"))

        # Show baseline ("before first change"), then one row per change batch.
        first_changed_at = events[0].get("at", "") or ""
        rows.append((
            code,
            base_state["name"] or "—",
            base_state["supplier"] or "—",
            base_state["dye_type"] or "—",
            base_state["lotto_no"] or "—",
            f"{float(base_state['resa_percent']):.1f}%",
            self._format_dt(first_changed_at),
        ))

        # Replay history forward and emit one row per change batch (same timestamp => one row).
        state = dict(base_state)
        current_batch_at = None

        def _append_state_row(batch_at: str):
            rows.append((
                code,
                state["name"] or "—",
                state["supplier"] or "—",
                state["dye_type"] or "—",
                state["lotto_no"] or "—",
                f"{float(state['resa_percent']):.1f}%",
                self._format_dt(batch_at or ""),
            ))

        for h in events:
            changed_at_raw = h.get("at", "") or ""
            field = (h.get("field") or "").strip()
            if current_batch_at is None:
                current_batch_at = changed_at_raw
            elif changed_at_raw != current_batch_at:
                _append_state_row(current_batch_at)
                current_batch_at = changed_at_raw
            _apply_change(state, field, h.get("new"))

        if current_batch_at is not None:
            _append_state_row(current_batch_at)

        return rows

    def _format_dt(self, value: str) -> str:
        if not value:
            return ""
        raw = str(value).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(raw[:19], fmt).strftime("%d/%m/%y %I:%M %p")
            except ValueError:
                continue
        return raw

    def _reset_lotto_history(self):
        sel = self.colors_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a color first.", parent=self.win)
            return
        code = str(self.colors_tree.item(sel[0])["values"][0]).strip()
        color_obj = self.db.get_color_by_code(code)
        if not color_obj:
            return
        if not messagebox.askyesno("Confirm Reset", f"Reset lotto history for color '{code}'?", parent=self.win):
            return
        deleted = self.db.reset_lotto_history_for_color(color_obj.id)
        self.status_lbl.config(text=f"History reset for {code} ({deleted} row(s) deleted)")
        self._refresh(keep_selection=True)

    def _add_lotto(self):
        """Add new lotto for selected color."""
        sel = self.colors_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a color first.", parent=self.win)
            return
        
        item_id = sel[0]
        if "|" in item_id:
            code = item_id.split("|")[0]
        else:
            code = item_id
        
        color_obj = self.db.get_color_by_code(code)
        if not color_obj:
            return
        
        # Open simple dialog to add lotto
        self._show_lotto_form(color_obj.id, code, None)

    def _edit_lotto(self):
        """Edit selected lotto."""
        sel = self.colors_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a lotto to edit.", parent=self.win)
            return
        
        item_id = sel[0]
        if "|" not in item_id:
            messagebox.showwarning("No Selection", "Please select a specific lotto (not just color).", parent=self.win)
            return
        
        code, lotto_no = item_id.split("|", 1)
        
        color_obj = self.db.get_color_by_code(code)
        if not color_obj:
            return
        
        lottos = self.db.get_lottos_for_color(color_obj.id)
        for lotto in lottos:
            if lotto.get('lotto_no') == lotto_no:
                self._show_lotto_form(color_obj.id, code, lotto)
                return

    def _show_lotto_form(self, color_id, color_code, lotto_data=None):
        """Show form to add/edit lotto."""
        dialog = tk.Toplevel(self.win)
        dialog.title("Add Lotto" if not lotto_data else "Edit Lotto")
        dialog.geometry("400x350")
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.win.winfo_x() + (self.win.winfo_width() // 2) - 200
        y = self.win.winfo_y() + (self.win.winfo_height() // 2) - 175
        dialog.geometry(f"+{x}+{y}")
        
        form = ttk.LabelFrame(dialog, text="Lotto Details", padding=15)
        form.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        vars = {}
        
        for row, (key, label, default) in enumerate([
            ("lotto_no",  "Lotto No *",  ""),
            ("qty",       "Quantity kg", "0"),
            ("resa",      "RESA %",      "100"),
            ("supplier",  "Supplier",    ""),
            ("notes",     "Notes",       ""),
        ]):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="e", padx=5, pady=5)
            vars[key] = tk.StringVar(value=default)
            ttk.Entry(form, textvariable=vars[key], width=25).grid(row=row, column=1, padx=5, pady=5)
        
        # Pre-fill if editing
        if lotto_data:
            vars["lotto_no"].set(lotto_data.get("lotto_no", ""))
            vars["qty"].set(str(lotto_data.get("quantity_kg", 0)))
            vars["resa"].set(str(lotto_data.get("resa_percent", 100)))
            vars["supplier"].set(lotto_data.get("supplier", ""))
            vars["notes"].set(lotto_data.get("notes", ""))
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        def save():
            ln = vars["lotto_no"].get().strip()
            if not ln:
                messagebox.showwarning("Required", "Lotto No is required.", parent=dialog)
                return
            
            try:
                qty = float(vars["qty"].get() or 0)
            except ValueError:
                qty = 0.0
            
            try:
                resa = float(vars["resa"].get() or 100)
            except ValueError:
                resa = 100.0
            
            if lotto_data:
                # Update existing
                lotto_id = lotto_data.get("id")
                self.db.update_lotto(lotto_id, "lotto_no", ln, self.username)
                self.db.update_lotto(lotto_id, "quantity_kg", str(qty), self.username)
                self.db.update_lotto(lotto_id, "resa_percent", str(resa), self.username)
                self.db.update_lotto(lotto_id, "supplier", vars["supplier"].get().strip(), self.username)
                self.db.update_lotto(lotto_id, "notes", vars["notes"].get().strip(), self.username)
            else:
                # Add new
                self.db.add_lotto(
                    color_id, ln, qty,
                    vars["supplier"].get().strip(),
                    vars["notes"].get().strip(),
                    self.username,
                    resa,
                )
            
            dialog.destroy()
            self._refresh()
        
        ttk.Button(btn_frame, text="Save", command=save, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def _delete_lotto(self):
        """Delete selected lotto."""
        sel = self.colors_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a lotto to delete.", parent=self.win)
            return
        
        item_id = sel[0]
        if "|" not in item_id:
            messagebox.showwarning("No Selection", "Please select a specific lotto (not just color).", parent=self.win)
            return
        
        code, lotto_no = item_id.split("|", 1)
        
        if not messagebox.askyesno("Confirm", f"Delete lotto '{lotto_no}' for color '{code}'?", parent=self.win):
            return
        
        color_obj = self.db.get_color_by_code(code)
        if not color_obj:
            return
        
        lottos = self.db.get_lottos_for_color(color_obj.id)
        for lotto in lottos:
            if lotto.get('lotto_no') == lotto_no:
                lotto_id = lotto.get('id')
                self.db.delete_lotto(lotto_id, self.username)
                self._refresh()
                return

    def _export_report(self):
        """Export PDF report for selected color with same Lotto Change History rows."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors as rl_colors
            from reportlab.lib.units import cm
            from datetime import datetime
            from app.utils import get_desktop_exports_dir

            folder = get_desktop_exports_dir()
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(folder, f"LottosReport_{ts}.pdf")

            doc    = SimpleDocTemplate(path, pagesize=A4,
                                       leftMargin=1.5*cm, rightMargin=1.5*cm,
                                       topMargin=1.5*cm, bottomMargin=1.5*cm)
            styles = getSampleStyleSheet()
            elems  = []

            elems.append(Paragraph("Lottos Management Report", styles["Title"]))
            elems.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
            elems.append(Spacer(1, 0.4*cm))

            sel = self.colors_tree.selection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select a color first.", parent=self.win)
                return
            code = str(self.colors_tree.item(sel[0])["values"][0]).strip()
            color_obj = self.db.get_color_by_code(code)
            if not color_obj:
                messagebox.showerror("Error", f"Color '{code}' not found.", parent=self.win)
                return

            history_rows = self._build_color_change_rows(color_obj)
            elems.append(Paragraph(f"<b>Color: {color_obj.code} - {color_obj.name}</b>", styles["Heading2"]))
            elems.append(Spacer(1, 0.2*cm))

            table_data = [["Code", "Name", "Type", "Lotto", "RESA %", "Updated At"]]
            for row in history_rows:
                table_data.append(list(row))

            t = Table(table_data, colWidths=[2*cm, 3.2*cm, 2*cm, 2.3*cm, 1.8*cm, 3*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), rl_colors.HexColor("#1565C0")),
                ("TEXTCOLOR",  (0,0), (-1,0), rl_colors.white),
                ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",   (0,0), (-1,-1), 8),
                ("ROWBACKGROUNDS", (0,1), (-1,-1),
                 [rl_colors.HexColor("#EEF2FF"), rl_colors.white]),
                ("GRID", (0,0), (-1,-1), 0.5, rl_colors.grey),
                ("ALIGN", (0,0), (-1,-1), "CENTER"),
                ("ALIGN", (1,1), (1,-1), "LEFT"),
                ("LEFTPADDING", (0,0), (-1,-1), 4),
            ]))
            elems.append(t)
            elems.append(Spacer(1, 0.4*cm))

            doc.build(elems)
            messagebox.showinfo("Exported", f"Report saved to:\n{path}", parent=self.win)
            
        except ImportError:
            messagebox.showerror("Error", "reportlab is required for PDF export.", parent=self.win)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to export:\n{exc}", parent=self.win)

    def _refresh(self, keep_selection: bool = True):
        """Refresh all data and keep current selection when possible."""
        selected = self.colors_tree.selection()[0] if (keep_selection and self.colors_tree.selection()) else None
        self._load_colors()
        if selected and self.colors_tree.exists(selected):
            self.colors_tree.selection_set(selected)
            self.colors_tree.focus(selected)
            self._on_color_select()
            return
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        self.status_lbl.config(text="Data refreshed")

    def _on_close(self):
        self.win.destroy()

    def _clear_left_search(self):
        self.search_code_var.set("")
        self.search_name_var.set("")
        self._apply_left_filters_and_sort()

    def _sort_left_tree(self, column: str):
        if self._left_sort_column == column:
            self._left_sort_reverse = not self._left_sort_reverse
        else:
            self._left_sort_column = column
            self._left_sort_reverse = False
        self._apply_left_filters_and_sort()

    def _apply_left_filters_and_sort(self, keep_selection_iid: str = None):
        code_q = self.search_code_var.get().strip().lower()
        name_q = self.search_name_var.get().strip().lower()

        filtered = []
        for iid, vals in self._left_rows:
            code_v = str(vals[0]).lower()
            name_v = str(vals[1]).lower()
            if code_q and code_q not in code_v:
                continue
            if name_q and name_q not in name_v:
                continue
            filtered.append((iid, vals))

        col_idx = {
            "code": 0, "name": 1, "dye_type": 2, "lotto": 3, "resa": 4, "updated_at": 5
        }[self._left_sort_column]

        def _sort_key(item):
            value = item[1][col_idx]
            if self._left_sort_column == "resa":
                try:
                    return float(str(value).replace("%", "").strip())
                except ValueError:
                    return -1.0
            return str(value).lower()

        filtered.sort(key=_sort_key, reverse=self._left_sort_reverse)

        for item in self.colors_tree.get_children():
            self.colors_tree.delete(item)
        for iid, vals in filtered:
            zebra_insert(self.colors_tree, vals, iid=iid)

        if keep_selection_iid and self.colors_tree.exists(keep_selection_iid):
            self.colors_tree.selection_set(keep_selection_iid)
            self.colors_tree.focus(keep_selection_iid)

    def _load(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for lt in self.db.get_lottos_for_color(self.color_id):
            resa = lt.get("resa_percent", 100.0)
            self.tree.insert("", "end", iid=str(lt["id"]), values=(
                lt["lotto_no"], lt["quantity_kg"], f"{resa:.1f}%",
                lt["supplier"] or "", lt["notes"] or "", 
                lt["created_at"] or "", lt["created_by"] or "",
            ))

    def _on_select(self, _e=None):
        sel = self.tree.selection()
        if not sel:
            return
        self._selected_id = int(sel[0])
        vals = self.tree.item(sel[0])["values"]
        self.vars["lotto_no"].set(vals[0])
        self.vars["qty"].set(vals[1])
        self.vars["resa"].set(vals[2].replace("%", ""))
        self.vars["supplier"].set(vals[3])
        self.vars["notes"].set(vals[4])
        # load history
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)
        for h in self.db.get_lotto_history(self._selected_id):
            self.hist_tree.insert("", "end", values=(
                h["field"], h["old"] or "—", h["new"] or "—",
                h["at"] or "—", h["by"] or "—",
            ))

    def _add(self):
        ln = self.vars["lotto_no"].get().strip()
        if not ln:
            messagebox.showwarning("Required", "Lotto No is required.", parent=self.win)
            return
        try:
            qty = float(self.vars["qty"].get() or 0)
        except ValueError:
            qty = 0.0
        try:
            resa = float(self.vars["resa"].get() or 100)
        except ValueError:
            resa = 100.0
        self.db.add_lotto(
            self.color_id, ln, qty,
            self.vars["supplier"].get().strip(),
            self.vars["notes"].get().strip(),
            self.username,
            resa,
        )
        self._load()
        self._clear_form()

    def _save_edit(self):
        if not self._selected_id:
            messagebox.showwarning("No Selection", "Select a lotto to edit.", parent=self.win)
            return
        for field, key in [("lotto_no","lotto_no"),("quantity_kg","qty"),
                            ("resa_percent","resa"),("supplier","supplier"),("notes","notes")]:
            val = self.vars[key].get().strip()
            self.db.update_lotto(self._selected_id, field, val, self.username)
        self._load()

    def _delete(self):
        if not self._selected_id:
            messagebox.showwarning("No Selection", "Select a lotto to delete.", parent=self.win)
            return
        if messagebox.askyesno("Confirm", "Delete this lotto?", parent=self.win):
            self.db.delete_lotto(self._selected_id, self.username)
            self._selected_id = None
            self._load()
            self._clear_form()

    def _clear_form(self):
        for v in self.vars.values():
            v.set("")
        self.vars["qty"].set("0")
        self.vars["resa"].set("100")
        self._selected_id = None
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)
