"""
نافذة الريتشتات (مرادف لـ SavedRecipesWindow للتوافق)
"""
import tkinter as tk
from tkinter import ttk, messagebox

# استيرادات محلية من app
from app.models import Recipe
from app.database import DatabaseManager


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


class RecipesWindow:
    """نافذة الريتشتات - توافق كامل مع SavedRecipesWindow"""

    def __init__(self, parent, db: DatabaseManager, recipe_id=None):
        self.parent = parent
        self.db = db
        self.recipe_id = recipe_id

        # إنشاء النافذة
        self.window = tk.Toplevel(parent)
        _show_on_top(self.window, parent)
        self.window.title("Recipes - الريتشتات")
        
        # ضبط أبعاد النافذة لتكون متجاوبة
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.82)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # السماح بالتكبير والتصغير وإظهار أزرار التحكم
        self.window.resizable(True, True)
        self.window.minsize(980, 620)


        # تحميل البيانات
        self.recipes_data: list[Recipe] = [] # Explicitly type hint
        self.load_recipes_data()

        # إنشاء الواجهة
        self.setup_ui()

        # إذا تم تحديد recipe_id، عرض تفاصيله
        if recipe_id:
            self.show_recipe_details_by_id(recipe_id)

    def load_recipes_data(self):
        """تحميل بيانات الريتشتات"""
        try:
            # Always use the DatabaseManager method
            self.recipes_data = self.db.get_all_recipes()
        except Exception as e:
            print(f"Error loading recipes: {e}")
            self.recipes_data = []

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        # الإطار الرئيسي
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # إطار البحث
        search_frame = ttk.LabelFrame(main_frame, text="Search Recipes", padding=10)
        search_frame.pack(fill=tk.X, pady=(0, 10))

        # البحث بالكود
        ttk.Label(search_frame, text="Recipe Code:").grid(row=0, column=0, padx=5, pady=5)
        self.search_code_var = tk.StringVar()
        search_code_entry = ttk.Entry(search_frame, textvariable=self.search_code_var, width=20)
        search_code_entry.grid(row=0, column=1, padx=5, pady=5)

        # البحث بالاسم
        ttk.Label(search_frame, text="Recipe Name:").grid(row=0, column=2, padx=5, pady=5)
        self.search_name_var = tk.StringVar() # Changed from search_customer_var
        search_name_entry = ttk.Entry(search_frame, textvariable=self.search_name_var, width=20)
        search_name_entry.grid(row=0, column=3, padx=5, pady=5)

        # أزرار البحث
        ttk.Button(search_frame, text="Search",
                   command=self.perform_search, width=10).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(search_frame, text="Reset",
                   command=self.reset_search, width=10).grid(row=0, column=5, padx=5, pady=5)

        # إطار قائمة الريتشتات
        list_frame = ttk.LabelFrame(main_frame, text="Recipes List", padding=10)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # شجرة الريتشتات
        # Updated columns: removed 'customer' and 'fabric'
        columns = ("id", "code", "name", "colors", "total%", "created")
        self.recipes_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        # تعريف العناوين
        self.recipes_tree.heading("id", text="ID")
        self.recipes_tree.heading("code", text="Recipe Code")
        self.recipes_tree.heading("name", text="Recipe Name")
        # Removed customer and fabric headings
        self.recipes_tree.heading("colors", text="Colors")
        self.recipes_tree.heading("total%", text="Total %")
        self.recipes_tree.heading("created", text="Created Date")

        # تعريف الأعمدة
        self.recipes_tree.column("id", width=50, anchor="center")
        self.recipes_tree.column("code", width=100, anchor="center")
        self.recipes_tree.column("name", width=150, anchor="center")
        # Removed customer and fabric columns
        self.recipes_tree.column("colors", width=70, anchor="center")
        self.recipes_tree.column("total%", width=70, anchor="center")
        self.recipes_tree.column("created", width=100, anchor="center")

        # شريط التمرير
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.recipes_tree.yview)
        self.recipes_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recipes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # إطار تفاصيل الريتشت
        details_frame = ttk.LabelFrame(main_frame, text="Recipe Details", padding=10)
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # معلومات الريتشت
        info_frame = ttk.Frame(details_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(info_frame, text="Recipe Code:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky="w", pady=5)
        self.recipe_code_label = ttk.Label(info_frame, text="", font=('Arial', 10))
        self.recipe_code_label.grid(row=0, column=1, sticky="w", pady=5)

        ttk.Label(info_frame, text="Recipe Name:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky="w", pady=5)
        self.recipe_name_label = ttk.Label(info_frame, text="", font=('Arial', 10))
        self.recipe_name_label.grid(row=1, column=1, sticky="w", pady=5)

        # Removed customer and fabric labels from details
        ttk.Label(info_frame, text="Colors Count:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky="w", pady=5)
        self.colors_count_label = ttk.Label(info_frame, text="", font=('Arial', 10))
        self.colors_count_label.grid(row=2, column=1, sticky="w", pady=5)
        
        ttk.Label(info_frame, text="Total Percentage:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky="w", pady=5)
        self.total_percentage_label = ttk.Label(info_frame, text="", font=('Arial', 10))
        self.total_percentage_label.grid(row=3, column=1, sticky="w", pady=5)

        # قائمة الألوان في الريتشت
        colors_frame = ttk.LabelFrame(details_frame, text="Colors in Recipe", padding=10)
        colors_frame.pack(fill=tk.BOTH, expand=True)

        # شجرة الألوان
        columns = ("code", "name", "type", "percentage", "price")
        self.colors_tree = ttk.Treeview(colors_frame, columns=columns, show="headings", height=8)

        self.colors_tree.heading("code", text="Color Code")
        self.colors_tree.heading("name", text="Color Name")
        self.colors_tree.heading("type", text="Type")
        self.colors_tree.heading("percentage", text="Percentage")
        self.colors_tree.heading("price", text="Price/Kg")

        self.colors_tree.column("code", width=80, anchor="center")
        self.colors_tree.column("name", width=120, anchor="center")
        self.colors_tree.column("type", width=80, anchor="center")
        self.colors_tree.column("percentage", width=80, anchor="center")
        self.colors_tree.column("price", width=80, anchor="center")

        scrollbar_colors = ttk.Scrollbar(colors_frame, orient="vertical", command=self.colors_tree.yview)
        self.colors_tree.configure(yscrollcommand=scrollbar_colors.set)
        scrollbar_colors.pack(side=tk.RIGHT, fill=tk.Y)
        self.colors_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # أزرار التحكم
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        ttk.Button(control_frame, text="View Details",
                   command=self.view_selected_recipe, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Edit Recipe",
                   command=self.edit_recipe, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Delete Recipe",
                   command=self.delete_recipe, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Refresh",
                   command=self.refresh_data, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Close",
                   command=self.window.destroy, width=15).pack(side=tk.LEFT, padx=5)

        # شريط الحالة
        self.status_label = ttk.Label(self.window, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

        # ربط الأحداث
        self.recipes_tree.bind("<<TreeviewSelect>>", self.on_recipe_select)

        # ملء الشجرة
        self.populate_recipes_tree()

    def populate_recipes_tree(self):
        """ملء شجرة الريتشتات"""
        for item in self.recipes_tree.get_children():
            self.recipes_tree.delete(item)

        if not self.recipes_data:
            self.recipes_tree.insert("", tk.END, values=("No recipes found", "", "", "", "", ""))
            return

        for recipe in self.recipes_data:
            # Assuming recipe is a Recipe object now
            self.recipes_tree.insert("", tk.END, values=(
                recipe.id,
                recipe.recipe_code,
                recipe.name,
                self.db.get_recipe_colors_count(recipe.id), # Get colors count from DB
                f"{self.db.get_recipe_total_percentage(recipe.id):.2f}%", # Get total percentage from DB
                recipe.created_at[:10] if recipe.created_at else ''
            ))


    def on_recipe_select(self, event):
        """عند اختيار ريتشت من الشجرة"""
        selected = self.recipes_tree.selection()
        if not selected:
            return

        recipe_id = self.recipes_tree.item(selected[0])["values"][0]
        self.show_recipe_details_by_id(recipe_id)

    def show_recipe_details_by_id(self, recipe_id):
        """عرض تفاصيل الريتشت حسب ID"""
        try:
            # Use the DatabaseManager method to get full details
            recipe_details_obj = self.db.get_recipe_details(recipe_id)

            if not recipe_details_obj or not recipe_details_obj.get('recipe'):
                self.clear_recipe_details()
                return

            recipe = recipe_details_obj['recipe']
            colors_in_recipe = recipe_details_obj['colors']
            colors_count = recipe_details_obj['colors_count']
            total_percentage = recipe_details_obj['total_percentage']


            # تحديث التسميات
            self.recipe_code_label.config(text=recipe.recipe_code)
            self.recipe_name_label.config(text=recipe.name)
            self.colors_count_label.config(text=str(colors_count))
            self.total_percentage_label.config(text=f"{total_percentage:.2f}%")

            # مسح شجرة الألوان
            for item in self.colors_tree.get_children():
                self.colors_tree.delete(item)

            # إضافة الألوان
            if colors_in_recipe:
                for color in colors_in_recipe:
                    self.colors_tree.insert("", tk.END, values=(
                        color.get('code', ''),
                        color.get('name', ''),
                        color.get('dye_type', ''),
                        f"{color.get('percentage', 0):.2f}%",
                        f"€{color.get('price_kg', 0):.2f}"
                    ))

            self.status_label.config(text=f"Showing recipe: {recipe.recipe_code}")

        except Exception as e:
            print(f"Error showing recipe details: {e}")
            messagebox.showerror("Error", f"Failed to show recipe details: {str(e)}", parent=self.window)
            self.status_label.config(text="Error loading recipe details")

    def clear_recipe_details(self):
        """مسح تفاصيل الريتشت"""
        self.recipe_code_label.config(text="")
        self.recipe_name_label.config(text="")
        self.colors_count_label.config(text="")
        self.total_percentage_label.config(text="")

        for item in self.colors_tree.get_children():
            self.colors_tree.delete(item)

    def view_selected_recipe(self):
        """عرض الريتشت المحدد"""
        selected = self.recipes_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a recipe to view", parent=self.window)
            return

        recipe_id = self.recipes_tree.item(selected[0])["values"][0]
        self.show_recipe_details_by_id(recipe_id)

    def edit_recipe(self):
        """تعديل الريتشت المحدد"""
        selected = self.recipes_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a recipe to edit", parent=self.window)
            return

        recipe_id = self.recipes_tree.item(selected[0])["values"][0]

        try:
            from .recipe_creator_window import RecipeCreatorWindow # Assuming this is the edit window
            RecipeCreatorWindow(self.window, self.db, recipe_id_to_edit=recipe_id, refresh_callback=self.refresh_data)
        except ImportError as e:
            messagebox.showerror("Error", f"Cannot open edit window. Make sure 'recipe_creator_window.py' exists and is correctly imported: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred while trying to open the edit window: {str(e)}", parent=self.window)


    def delete_recipe(self):
        """حذف الريتشت المحدد"""
        selected = self.recipes_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a recipe to delete", parent=self.window)
            return

        recipe_id = self.recipes_tree.item(selected[0])["values"][0]
        recipe_code = self.recipes_tree.item(selected[0])["values"][1]

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete recipe '{recipe_code}'?\n\n"
            "Warning: This action cannot be undone!",
            parent=self.window
        )

        if confirm:
            try:
                # Use the DatabaseManager method
                success = self.db.delete_recipe(recipe_id)

                if success:
                    messagebox.showinfo("Success", f"Recipe '{recipe_code}' deleted successfully", parent=self.window)
                    self.refresh_data()
                else:
                    messagebox.showerror("Error", "Failed to delete recipe", parent=self.window)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete recipe: {str(e)}", parent=self.window)

    def perform_search(self):
        """تنفيذ البحث"""
        search_code = self.search_code_var.get().strip()
        search_name = self.search_name_var.get().strip() # Changed from search_customer

        # Use DatabaseManager's search method
        try:
            self.recipes_data = self.db.search_recipes(recipe_code_filter=search_code, name_filter=search_name)
            self.populate_recipes_tree()
            self.status_label.config(text=f"Found {len(self.recipes_data)} recipe(s)")

        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}", parent=self.window)

    def reset_search(self):
        """إعادة تعيين البحث"""
        self.search_code_var.set("")
        self.search_name_var.set("") # Changed from search_customer_var
        self.load_recipes_data()
        self.populate_recipes_tree()

    def refresh_data(self):
        """تحديث البيانات"""
        self.load_recipes_data()
        self.populate_recipes_tree()
        self.clear_recipe_details()
        self.status_label.config(text="Data refreshed")


# للإبقاء على التوافق مع الكود القديم
SavedRecipesWindow = RecipesWindow
