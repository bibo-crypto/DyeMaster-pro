"""
نافذة إدارة الألوان - Colors Management Window
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from typing import Optional, Dict

from app.models import Color
from app.database import DatabaseManager
from app.session import SessionManager
from app.config import DYE_TYPES
from app.utils import parse_percentage_input, parse_number_input, normalize_dye_type_label
from ui.theme_tokens import get_theme_tokens, apply_excel_treeview_style, configure_sub_button_style


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


class ColorsWindow:
    """نافذة إدارة الألوان"""

    def __init__(self, parent, db: DatabaseManager, color_code: Optional[str] = None,
                 callback: Optional[callable] = None, initial_data: Optional[Dict] = None,
                 dark_mode: bool = False):
        """
        تهيئة نافذة الألوان

        Args:
            parent: النافذة الأم
            db: كائن قاعدة البيانات
            color_code: كود اللون للتعديل (إذا كان None -> إضافة جديد)
            callback: دالة للاستدعاء بعد الحفظ
            initial_data: بيانات أولية لتعبئة الحقول عند إضافة لون جديد
            dark_mode: وضع الألوان الداكنة
        """
        self.parent = parent
        self.db = db
        self.session = SessionManager.get_session()
        self.color_code = color_code
        self.callback = callback
        self.is_new_color = color_code is None
        self.dark_mode = dark_mode

        self.window = tk.Toplevel(parent)
        _show_on_top(self.window, parent)

        if self.is_new_color:
            self.window.title("Add New Color - إضافة لون جديد")
        else:
            self.window.title(f"Modify Color: {color_code} - تعديل اللون")

        # ضبط أبعاد النافذة لتكون متجاوبة
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = int(screen_width * 0.8)
        height = int(screen_height * 0.84)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.configure(bg=get_theme_tokens(self.dark_mode)["bg"])
        
        # السماح بالتكبير والتصغير وإظهار أزرار التحكم
        self.window.resizable(True, True)
        self.window.minsize(900, 640)

        # متغيرات الحقول
        self.code_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.dye_type_var = tk.StringVar()
        self.supplier_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.resa_var = tk.StringVar()

        # تهيئة الأنماط
        self.configure_styles()

        # إنشاء الواجهة
        self.setup_ui()

        # إذا كان تعديل لون موجود، تحميل بياناته
        if not self.is_new_color:
            self.load_color_data()
        
        # إذا كانت هناك بيانات أولية لإضافة لون جديد
        if self.is_new_color and initial_data:
            self.code_var.set(initial_data.get('code', ''))
            self.name_var.set(initial_data.get('name', ''))
            self.dye_type_var.set(initial_data.get('dye_type', ''))

    def configure_styles(self):
        """تكوين أنماط الواجهة"""
        style = ttk.Style(self.window)
        palette = get_theme_tokens(self.dark_mode)
        apply_excel_treeview_style(style, palette, self.dark_mode)
        configure_sub_button_style(style, 'Sub.TButton', palette)


    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # العنوان
        if self.is_new_color:
            title_text = "Add New Color"
        else:
            title_text = f"Modify Color: {self.color_code}"

        title_label = ttk.Label(
            main_frame,
            text=title_text,
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # إطار الحقول
        form_frame = ttk.LabelFrame(main_frame, text="Color Information", padding=15)
        form_frame.pack(fill=tk.X, pady=(0, 20))

        # كود اللون (فقط للإضافة الجديدة)
        if self.is_new_color:
            ttk.Label(form_frame, text="Color Code*:").grid(
                row=0, column=0, sticky="e", padx=5, pady=8
            )
            self.code_entry = ttk.Entry(form_frame, textvariable=self.code_var, width=30)
            self.code_entry.grid(row=0, column=1, padx=5, pady=8, sticky="w")
            self.code_entry.focus()
        else:
            # لعرض الكود في حالة التعديل
            ttk.Label(form_frame, text="Color Code:").grid(
                row=0, column=0, sticky="e", padx=5, pady=8
            )
            ttk.Label(form_frame, text=self.color_code, font=('Arial', 10, 'bold')).grid(
                row=0, column=1, padx=5, pady=8, sticky="w"
            )

        # اسم اللون
        ttk.Label(form_frame, text="Color Name*:").grid(
            row=1, column=0, sticky="e", padx=5, pady=8
        )
        self.name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=1, column=1, padx=5, pady=8, sticky="w")

        # نوع الصبغة
        ttk.Label(form_frame, text="Dye Type:").grid(
            row=2, column=0, sticky="e", padx=5, pady=8
        )

        # ✅ إصلاح: استخدام DYE_TYPES الثابتة
        self.dye_type_combo = ttk.Combobox(
            form_frame,
            textvariable=self.dye_type_var,
            values=DYE_TYPES,
            state='readonly',
            width=27
        )
        self.dye_type_combo.grid(row=2, column=1, padx=5, pady=8, sticky="w")

        # المورد
        ttk.Label(form_frame, text="Supplier:").grid(
            row=3, column=0, sticky="e", padx=5, pady=8
        )
        self.supplier_entry = ttk.Entry(form_frame, textvariable=self.supplier_var, width=30)
        self.supplier_entry.grid(row=3, column=1, padx=5, pady=8, sticky="w")

        # السعر
        ttk.Label(form_frame, text="Price/kg (€)*:").grid(
            row=4, column=0, sticky="e", padx=5, pady=8
        )
        self.price_entry = ttk.Entry(form_frame, textvariable=self.price_var, width=30)
        self.price_entry.grid(row=4, column=1, padx=5, pady=8, sticky="w")
        self.price_entry.insert(0, "0.00")

        # نسبة الصباغة
        ttk.Label(form_frame, text="Resa %:").grid(
            row=5, column=0, sticky="e", padx=5, pady=8
        )
        self.resa_entry = ttk.Entry(form_frame, textvariable=self.resa_var, width=30)
        self.resa_entry.grid(row=5, column=1, padx=5, pady=8, sticky="w")
        self.resa_entry.insert(0, "100")

        # معلومات إضافية (فقط للتعديل)
        if not self.is_new_color:
            info_frame = ttk.LabelFrame(main_frame, text="Additional Information", padding=10)
            info_frame.pack(fill=tk.X, pady=(0, 20))

            self.info_label = ttk.Label(info_frame, text="")
            self.info_label.pack(anchor="w")

        # أزرار التحكم
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=6)

        # زر الحفظ
        save_text = "💾 Save Color" if self.is_new_color else "💾 Update Color"
        ttk.Button(
            button_frame,
            text=save_text,
            command=self.save_color,
            width=15,
            style='Sub.TButton'
        ).pack(side=tk.LEFT, padx=5)

        # زر الحذف (فقط للتعديل)
        if not self.is_new_color:
            self.delete_color_button = ttk.Button(
                button_frame,
                text="Delete Color",
                command=self.delete_color,
                width=15,
                style='Sub.TButton'
            )
            self.delete_color_button.pack(side=tk.LEFT, padx=5)
            if not self.session.has_permission("can_delete"):
                self.delete_color_button.state(["disabled"])

        # زر الإلغاء
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            width=15,
            style='Sub.TButton'
        ).pack(side=tk.LEFT, padx=5)

        # زر المساعدة
        ttk.Button(
            button_frame,
            text="Help",
            command=self.show_help,
            width=15,
            style='Sub.TButton'
        ).pack(side=tk.LEFT, padx=5)

        # ربط حدث Enter
        self.window.bind('<Return>', lambda e: self.save_color())

    def load_color_data(self):
        """تحميل بيانات اللون من قاعدة البيانات"""
        try:
            if not self.color_code:
                return

            # محاولة الحصول على بيانات اللون
            color = None
            if hasattr(self.db, 'get_color_by_code'):
                color = self.db.get_color_by_code(self.color_code)
            else:
                # طريقة بديلة
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM colors WHERE code = ?", (self.color_code,))
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

            if color:
                # تعبئة الحقول
                self.name_var.set(getattr(color, 'name', ''))
                self.dye_type_var.set(getattr(color, 'dye_type', ''))
                self.supplier_var.set(getattr(color, 'supplier', ''))
                self.price_var.set(str(getattr(color, 'price_kg', 0)))
                resa_value = getattr(color, 'resa_percent', 100)
                try:
                    resa_float = float(resa_value)
                    resa_str = str(int(resa_float)) if resa_float.is_integer() else str(resa_float)
                except (TypeError, ValueError):
                    resa_str = "100"
                self.resa_var.set(resa_str)

                # تحديث معلومات إضافية
                if hasattr(self, 'info_label'):
                    info_text = f"Created: {getattr(color, 'created_at', 'N/A')}"
                    if getattr(color, 'updated_at', ''):
                        info_text += f" | Last Updated: {color.updated_at}"
                    self.info_label.config(text=info_text)
            else:
                messagebox.showwarning(
                    "Warning",
                    f"Color '{self.color_code}' not found in database.\n"
                    "You can add it as a new color.",
                    parent=self.window
                )
                self.is_new_color = True
                self.window.title("Add New Color")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load color data: {str(e)}", parent=self.window)

    def validate_input(self) -> tuple[bool, str]:
        """التحقق من صحة البيانات المدخلة"""
        try:
            # جمع البيانات
            if self.is_new_color:
                code = self.code_var.get().strip().upper()
                if not code:
                    return False, "Color code is required"
            else:
                code = self.color_code

            name = self.name_var.get().strip()
            if not name:
                return False, "Color name is required"

            # التحقق من السعر
            try:
                price = parse_number_input(self.price_var.get().strip() or "0", default=0.0)
                if price < 0:
                    return False, "Price cannot be negative"
            except ValueError:
                return False, "Invalid price value"

            # التحقق من نسبة الصباغة
            try:
                resa = parse_percentage_input(self.resa_var.get().strip() or "100")
                if resa < 0:
                    return False, "Resa percentage must be zero or positive"
            except ValueError:
                return False, "RESA must use English digits only (0-9), e.g. 85 or 85.5"

            return True, ""

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def save_color(self):
        """حفظ اللون"""
        try:
            # التحقق من البيانات
            is_valid, error_msg = self.validate_input()
            if not is_valid:
                messagebox.showwarning("Validation Error", error_msg, parent=self.window)
                return

            # جمع البيانات
            color_data = {
                'code': self.color_code if not self.is_new_color else self.code_var.get().strip().upper(),
                'name': self.name_var.get().strip(),
                'dye_type': normalize_dye_type_label(self.dye_type_var.get().strip()),
                'supplier': self.supplier_var.get().strip(),
                'price_kg': parse_number_input(self.price_var.get().strip() or "0", default=0.0),
                'resa_percent': parse_percentage_input(self.resa_var.get().strip() or "100")
            }

            # التحقق مما إذا كان اللون موجوداً بالفعل (لحالة الإضافة الجديدة)
            if self.is_new_color:
                try:
                    if hasattr(self.db, 'get_color_by_code'):
                        existing_color = self.db.get_color_by_code(color_data['code'])
                        if existing_color:
                            response = messagebox.askyesno(
                                "Color Exists",
                                f"Color '{color_data['code']}' already exists.\n"
                                "Do you want to update it instead?"
                            )
                            if response:
                                self.color_code = color_data['code']
                                self.is_new_color = False
                            else:
                                return
                except:
                    pass

            # إنشاء كائن Color
            color = Color(
                id=0 if self.is_new_color else getattr(self.db.get_color_by_code(color_data['code']), 'id', 0),
                code=color_data['code'],
                name=color_data['name'],
                dye_type=color_data['dye_type'],
                supplier=color_data['supplier'],
                price_kg=color_data['price_kg'],
                resa_percent=color_data['resa_percent']
            )

            if self.is_new_color:
                success = self.db.add_color(color) > 0
            else:
                success = self.db.update_color(color)

            if success:
                message = "Color added successfully!" if self.is_new_color else "Color updated successfully!"
                messagebox.showinfo("Success", message, parent=self.window)

                # استدعاء دالة الرد إذا كانت موجودة
                if self.callback:
                    self.callback()

                self.window.destroy()
            else:
                messagebox.showerror("Error", "Failed to save color to database", parent=self.window)

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                messagebox.showerror("Error", f"Color '{color_data['code']}' already exists!", parent=self.window)
            else:
                messagebox.showerror("Error", f"Database error: {str(e)}", parent=self.window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save color: {str(e)}", parent=self.window)

    def delete_color(self):
        """
        Handles color deletion with options for colors used in recipes.
        """
        if not self.session.has_permission("can_delete"):
            messagebox.showwarning("Permission Denied", "You do not have permission to delete colors.", parent=self.window)
            return
        if not self.color_code:
            return

        try:
            # Check if the color is used in any recipes
            recipes_using_color = self.db.get_recipes_using_color(self.color_code)

            if recipes_using_color:
                # Color is in use - offer user options
                self._handle_color_in_use(recipes_using_color)
                return

            # If the color is not in use, proceed with normal deletion
            self._confirm_and_delete_color()

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}", parent=self.window)

    def _handle_color_in_use(self, recipes_using_color):
        """Handle deletion of a color that's currently used in recipes."""
        num_recipes = len(recipes_using_color)

        # Create a detailed message showing which recipes use this color
        recipe_list = "\n".join([f"• {recipe.recipe_code}: {recipe.name}" for recipe in recipes_using_color[:5]])
        if num_recipes > 5:
            recipe_list += f"\n... and {num_recipes - 5} more recipes"

        message = (
            f"⚠️ Color '{self.color_code}' is used in {num_recipes} recipe(s).\n\n"
            f"Recipes using this color:\n{recipe_list}\n\n"
            "Choose how to proceed:"
        )

        # Create a custom dialog with options
        result = self._show_deletion_options_dialog(message, num_recipes)

        if result == "cancel":
            return
        elif result == "delete_recipes":
            # Delete all recipes using this color, then delete the color
            self._delete_recipes_and_color(recipes_using_color)
        elif result == "manage_manually":
            # Open ActiveColorsWindow for manual management
            self._open_colors_in_use_window()

    def _show_deletion_options_dialog(self, message, num_recipes):
        """Show a custom dialog with deletion options."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Color Deletion Options")
        dialog.geometry("500x300")
        _show_on_top(dialog, self.window)

        # Center the dialog
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

        # Option 1: Cancel
        ttk.Button(button_frame, text="Cancel",
                  command=lambda: set_choice("cancel")).pack(side=tk.LEFT, padx=5)

        # Option 2: Delete recipes and color (if not too many recipes)
        if num_recipes <= 10:  # Safety limit
            ttk.Button(button_frame, text="Delete All Recipes & Color",
                      command=lambda: set_choice("delete_recipes")).pack(side=tk.LEFT, padx=5)
        else:
            ttk.Label(button_frame, text="(Too many recipes to auto-delete)",
                     foreground="red").pack(side=tk.LEFT, padx=5)

        # Option 3: Manual management
        ttk.Button(button_frame, text="Manage Manually",
                  command=lambda: set_choice("manage_manually")).pack(side=tk.LEFT, padx=5)

        dialog.wait_window()
        return result["choice"]

    def _delete_recipes_and_color(self, recipes_using_color):
        """Delete all recipes using the color, then delete the color itself."""
        try:
            # Confirm the destructive action
            recipe_codes = [recipe.recipe_code for recipe in recipes_using_color]
            recipe_list = "\n".join([f"• {code}" for code in recipe_codes])

            confirm_msg = (
                f"⚠️ WARNING: This will permanently delete {len(recipes_using_color)} recipe(s) and the color!\n\n"
                f"Recipes to be deleted:\n{recipe_list}\n\n"
                f"Color to be deleted: {self.color_code}\n\n"
                "This action CANNOT be undone!\n\n"
                "Are you absolutely sure?"
            )

            if not messagebox.askyesno("⚠️ Confirm Mass Deletion", confirm_msg, parent=self.window):
                return

            # Get color ID
            color = self.db.get_color_by_code(self.color_code)
            if not color:
                messagebox.showerror("Error", "Color not found.", parent=self.window)
                return

            # Delete recipes and color using the database method
            recipe_ids = [recipe.id for recipe in recipes_using_color]
            success = self.db.delete_color_and_associated_recipes(color.id, recipe_ids)

            if success:
                messagebox.showinfo("Success",
                                   f"Successfully deleted {len(recipes_using_color)} recipe(s) and color '{self.color_code}'.",
                                   parent=self.window)
                if self.callback:
                    self.callback()
                self.window.destroy()
            else:
                messagebox.showerror("Error", "Failed to delete recipes and color.", parent=self.window)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete recipes and color: {str(e)}", parent=self.window)

    def _open_colors_in_use_window(self):
        """Open ActiveColorsWindow for manual management."""
        try:
            from ui.active_colors_window import ActiveColorsWindow
            ActiveColorsWindow(self.parent, self.db, initial_search_code=self.color_code)
        except ImportError:
            messagebox.showerror("Error", "Could not import the 'Active Colors' window component.", parent=self.window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open 'Active Colors' window: {str(e)}", parent=self.window)

    def _confirm_and_delete_color(self):
        """Confirm and delete a color that's not in use."""
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete color '{self.color_code}'?\n\n"
            "This action cannot be undone!",
            parent=self.window
        )

        if not confirm:
            return

        color_to_delete = self.db.get_color_by_code(self.color_code)
        if not color_to_delete:
            messagebox.showwarning("Warning", "Color not found.", parent=self.window)
            return

        success = self.db.delete_color(color_to_delete.id)

        if success:
            messagebox.showinfo("Success", f"Color '{self.color_code}' deleted successfully.", parent=self.window)
            if self.callback:
                self.callback()
            self.window.destroy()
        else:
            messagebox.showwarning("Warning", "Color could not be deleted. It might have already been removed.", parent=self.window)

    def show_help(self):
        """عرض مساعدة"""
        help_text = """
        Color Information Help:
        
        * Color Code: Unique identifier for the color (e.g., RED001, BLU202)
        * Color Name: Descriptive name of the color
        * Dye Type: Type of dye (Acid, Direct, Reactive, etc.)
        * Supplier: Manufacturer or supplier name
        * Price/kg: Cost per kilogram in Euros
        * Resa %: Percentage of dye residue/fixation
        
        Required fields are marked with *
        
        For new colors, make sure the code is unique.
        """

        messagebox.showinfo("Help", help_text, parent=self.window)
