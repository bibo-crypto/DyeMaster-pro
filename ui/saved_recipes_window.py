"""
Ù†Ø§ÙØ°Ø© Ø¹Ø±Ø¶ Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª Ø§Ù„Ù…Ø­ÙÙˆØ¸Ø©
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import List, Optional

from app.database import DatabaseManager
from app.pdf_exporter import PDFExporter


def _show_on_top(window, parent):
    """Ensure new windows open above their parent."""
    try:
        window.lift()
        window.focus_force()
        window.attributes("-topmost", True)
        window.after(250, lambda: window.attributes("-topmost", False))
    except Exception:
        pass


class SavedRecipesWindow:
    """Ù†Ø§ÙØ°Ø© Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª Ø§Ù„Ù…Ø­ÙÙˆØ¸Ø©"""

    def __init__(self, parent, db: DatabaseManager, recipe_id: Optional[int] = None):
        self.parent = parent
        self.db = db
        self.selected_recipe_id = recipe_id
        self.all_recipes_data = []  # ØªØ®Ø²ÙŠÙ† Ø¬Ù…ÙŠØ¹ Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª Ù„Ù„Ø¨Ø­Ø«

        self.window = tk.Toplevel(parent)
        _show_on_top(self.window, parent)
        self.window.title("Saved Recipes - Ricette")
        
        # Ø¶Ø¨Ø· Ø£Ø¨Ø¹Ø§Ø¯ Ø§Ù„Ù†Ø§ÙØ°Ø© Ù„ØªÙƒÙˆÙ† Ù…ØªØ¬Ø§ÙˆØ¨Ø©
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.82)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.configure(bg="#f0f0f0")
        
        # Ø§Ù„Ø³Ù…Ø§Ø­ Ø¨Ø§Ù„ØªÙƒØ¨ÙŠØ± ÙˆØ§Ù„ØªØµØºÙŠØ± ÙˆØ¥Ø¸Ù‡Ø§Ø± Ø£Ø²Ø±Ø§Ø± Ø§Ù„ØªØ­ÙƒÙ…
        self.window.resizable(True, True)
        self.window.minsize(980, 620)

        # Keep this as a normal top-level window (with full title-bar controls).

        # Ù…Ù†Ø¹ ØªØºÙŠÙŠØ± Ø§Ù„Ø­Ø¬Ù…
        self.window.resizable(True, True)

        # Ù…ØªØºÙŠØ±Ø§Øª Ø§Ù„Ø¨Ø­Ø«
        self.search_code_var = tk.StringVar()
        self.search_name_var = tk.StringVar()

        # Ù…ØªØºÙŠØ±Ø§Øª Ø§Ù„ØªØ±ØªÙŠØ¨
        self.sort_column = "id"
        self.sort_reverse = False
        self.current_displayed_data = []  # ØªØ®Ø²ÙŠÙ† Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ø¹Ø±ÙˆØ¶Ø© Ø­Ø§Ù„ÙŠØ§Ù‹ Ù„Ù„ØªØ±ØªÙŠØ¨


        # ØªÙ‡ÙŠØ¦Ø© Ø§Ù„Ø£Ù†Ù…Ø§Ø·
        self.configure_styles()

        # Ø¥Ù†Ø´Ø§Ø¡ Ø§Ù„ÙˆØ§Ø¬Ù‡Ø©
        self.setup_ui()

        # ØªØ­Ù…ÙŠÙ„ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª
        self.load_recipes()

        # Ø¥Ø°Ø§ ÙƒØ§Ù† Ù‡Ù†Ø§Ùƒ recipe_id Ù…Ø­Ø¯Ø¯ØŒ Ø¹Ø±Ø¶ ØªÙØ§ØµÙŠÙ„Ù‡
        if self.selected_recipe_id:
            self.select_recipe_by_id(self.selected_recipe_id)

    def configure_styles(self):
        """ØªÙƒÙˆÙŠÙ† Ø£Ù†Ù…Ø§Ø· Ø§Ù„ÙˆØ§Ø¬Ù‡Ø©"""
        style = ttk.Style(self.window)
        style.configure('Sub.TButton',
                        font=('Arial', 10, 'bold'),
                        padding=6,
                        background='#3498DB',
                        foreground='white')
        style.map('Sub.TButton',
                  background=[('active', '#2980B9')])

    def setup_ui(self):
        """Ø¥Ø¹Ø¯Ø§Ø¯ ÙˆØ§Ø¬Ù‡Ø© Ø§Ù„Ù…Ø³ØªØ®Ø¯Ù…"""
        # Ø¥Ø·Ø§Ø± Ø§Ù„Ø¨Ø­Ø«
        search_frame = ttk.LabelFrame(self.window, text="Search Recipes", padding=8)
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        # Ø¨Ø­Ø« Ø¨Ø§Ù„ÙƒÙˆØ¯
        ttk.Label(search_frame, text="Search by Code:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.search_code_entry = ttk.Entry(search_frame, textvariable=self.search_code_var, width=15)
        self.search_code_entry.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.search_code_entry.bind('<Return>', lambda e: self.perform_search())

        # Ø¨Ø­Ø« Ø¨Ø§Ù„Ø§Ø³Ù…
        ttk.Label(search_frame, text="Search by Name:").grid(row=0, column=2, padx=5, pady=3, sticky="e")
        self.search_name_entry = ttk.Entry(search_frame, textvariable=self.search_name_var, width=25)
        self.search_name_entry.grid(row=0, column=3, padx=5, pady=3, sticky="w")
        self.search_name_entry.bind('<Return>', lambda e: self.perform_search())

        # Ø£Ø²Ø±Ø§Ø± Ø§Ù„Ø¨Ø­Ø«
        ttk.Button(search_frame, text="Search",
                   command=self.perform_search, width=12, style='Sub.TButton').grid(row=0, column=4, padx=5, pady=3)

        ttk.Button(search_frame, text="Reset",
                   command=self.reset_search, width=10, style='Sub.TButton').grid(row=0, column=5, padx=5, pady=3)

        # Ø§Ù„Ø¥Ø·Ø§Ø± Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠ
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Ø¥Ø·Ø§Ø± Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª (Ø§Ù„Ø´Ù…Ø§Ù„) - Ø£ØµØºØ±
        list_frame = ttk.LabelFrame(self.main_frame, text="Saved Recipes List", padding=10)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))

        # Ø´Ø¬Ø±Ø© Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª - Ø§Ø±ØªÙØ§Ø¹ Ø£Ù‚Ù„
        self.recipe_tree = ttk.Treeview(
            list_frame,
            columns=("id", "recipe_code", "name", "created_at"),
            show="headings",
            height=15  # ØªÙ‚Ù„ÙŠÙ„ Ø§Ù„Ø§Ø±ØªÙØ§Ø¹
        )

        # Ø¹Ù†Ø§ÙˆÙŠÙ† Ø§Ù„Ø£Ø¹Ù…Ø¯Ø©
        self.recipe_tree.heading("id", text="ID", command=lambda: self.sort_treeview("id"))
        self.recipe_tree.heading("recipe_code", text="Recipe Code", command=lambda: self.sort_treeview("recipe_code"))
        self.recipe_tree.heading("name", text="Recipe Name", command=lambda: self.sort_treeview("name"))
        self.recipe_tree.heading("created_at", text="Created Date", command=lambda: self.sort_treeview("created_at"))

        # Ø£Ø¨Ø¹Ø§Ø¯ Ø§Ù„Ø£Ø¹Ù…Ø¯Ø© - Ø£ØµØºØ±
        self.recipe_tree.column("id", width=50, anchor="center")
        self.recipe_tree.column("recipe_code", width=100, anchor="center")
        self.recipe_tree.column("name", width=180, anchor="center")
        self.recipe_tree.column("created_at", width=100, anchor="center")

        # Ø´Ø±ÙŠØ· Ø§Ù„ØªÙ…Ø±ÙŠØ±
        scrollbar_tree = ttk.Scrollbar(list_frame, orient="vertical", command=self.recipe_tree.yview)
        self.recipe_tree.configure(yscrollcommand=scrollbar_tree.set)
        scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
        self.recipe_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Ø±Ø¨Ø· Ø£Ø­Ø¯Ø§Ø«
        self.recipe_tree.bind("<<TreeviewSelect>>", self.on_recipe_select)

        # Ø¥Ø·Ø§Ø± ØªÙØ§ØµÙŠÙ„ Ø§Ù„Ø±ÙŠØªØ´Øª (Ø§Ù„ÙŠÙ…ÙŠÙ†)
        details_frame = ttk.LabelFrame(self.main_frame, text="Recipe Full Details", padding=10)
        details_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Ø¥Ø·Ø§Ø± Ø§Ù„ØªÙØ§ØµÙŠÙ„ Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ© Ù…Ø¨Ø§Ø´Ø±Ø© (Ø¨Ø¯ÙˆÙ† ØªØ¨ÙˆÙŠØ¨Ø§Øª)
        self.main_details_frame = ttk.Frame(details_frame)
        self.main_details_frame.pack(fill=tk.BOTH, expand=True)

        # Ø¥Ø¹Ø¯Ø§Ø¯ Ù…Ø­ØªÙˆÙ‰ Ø§Ù„ØªØ¨ÙˆÙŠØ¨Ø§Øª
        self.setup_main_details_tab()

        # Ø£Ø²Ø±Ø§Ø± Ø§Ù„ØªØ­ÙƒÙ… ÙÙŠ Ø§Ù„Ø£Ø³ÙÙ„
        self.setup_control_buttons()

    def setup_main_details_tab(self):
        """Ø¥Ø¹Ø¯Ø§Ø¯ ØªØ¨ÙˆÙŠØ¨ Ø§Ù„ØªÙØ§ØµÙŠÙ„ Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ© (Recipe Info + Colors & Chemicals)"""
        # Ø¥Ø·Ø§Ø± Ø±Ø¦ÙŠØ³ÙŠ Ù…Ø¹ ØªÙ…Ø±ÙŠØ± Ø¹Ù…ÙˆØ¯ÙŠ ÙÙ‚Ø·
        main_container = ttk.Frame(self.main_details_frame)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Canvas Ù…Ø¹ Ø´Ø±ÙŠØ· ØªÙ…Ø±ÙŠØ± Ø¹Ù…ÙˆØ¯ÙŠ ÙÙ‚Ø·
        self.details_canvas = tk.Canvas(main_container, bg="#f0f0f0")  # Ù„ÙˆÙ† Ø§Ù„Ø®Ù„ÙÙŠØ© Ù…ØªÙ†Ø§Ø³Ù‚
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=self.details_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.details_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.details_canvas.configure(scrollregion=self.details_canvas.bbox("all"))
        )

        # Ø¥Ù†Ø´Ø§Ø¡ Ø§Ù„Ù†Ø§ÙØ°Ø© Ø¯Ø§Ø®Ù„ Ø§Ù„ÙƒØ§Ù†ÙØ§Ø³ ÙˆØ­ÙØ¸ Ø§Ù„Ù…Ø¹Ø±Ù Ù„Ù„ØªØ­ÙƒÙ… ÙÙŠ Ø§Ù„Ø¹Ø±Ø¶
        window_id = self.details_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Ø¬Ø¹Ù„ Ø§Ù„Ø¥Ø·Ø§Ø± Ø§Ù„Ø¯Ø§Ø®Ù„ÙŠ ÙŠÙ…Ù„Ø£ Ø¹Ø±Ø¶ Ø§Ù„ÙƒØ§Ù†ÙØ§Ø³ (Ù„Ø¥Ø²Ø§Ù„Ø© Ø§Ù„Ù…Ø³Ø§Ø­Ø© Ø§Ù„Ø¨ÙŠØ¶Ø§Ø¡ ÙŠÙ…ÙŠÙ†Ø§Ù‹)
        self.details_canvas.bind("<Configure>", lambda e: self.details_canvas.itemconfig(window_id, width=e.width))
        
        self.details_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.details_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ========== SECTION 1: RECIPE INFORMATION ==========
        recipe_info_frame = ttk.LabelFrame(self.scrollable_frame, text="RECIPE INFORMATION", padding=10)
        recipe_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Ø´Ø¨ÙƒØ© Ù…Ø¹Ù„ÙˆÙ…Ø§Øª Ø§Ù„ÙˆØµÙØ© - Ø£ÙƒØ«Ø± Ø¥Ø­ÙƒØ§Ù…Ø§
        info_grid = ttk.Frame(recipe_info_frame)
        info_grid.pack(fill=tk.X, padx=5, pady=5)

        # Ø§Ù„ØµÙ Ø§Ù„Ø£ÙˆÙ„
        ttk.Label(info_grid, text="Recipe Code:",
                  font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2, padx=2)
        self.recipe_code_value = ttk.Label(info_grid, text="", font=('Arial', 9))
        self.recipe_code_value.grid(row=0, column=1, sticky=tk.W, pady=2, padx=10)

        ttk.Label(info_grid, text="Recipe Name:",
                  font=('Arial', 9, 'bold')).grid(row=0, column=2, sticky=tk.W, pady=2, padx=2)
        self.recipe_name_value = ttk.Label(info_grid, text="", font=('Arial', 9))
        self.recipe_name_value.grid(row=0, column=3, sticky=tk.W, pady=2, padx=10)

        # Ø§Ù„ØµÙ Ø§Ù„Ø«Ø§Ù†ÙŠ
        ttk.Label(info_grid, text="Created Date:",
                  font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2, padx=2)
        self.created_date_value = ttk.Label(info_grid, text="", font=('Arial', 9))
        self.created_date_value.grid(row=1, column=1, sticky=tk.W, pady=2, padx=10)

        ttk.Label(info_grid, text="Dominant Type:",
                  font=('Arial', 9, 'bold')).grid(row=1, column=2, sticky=tk.W, pady=2, padx=2)
        self.dominant_type_value = ttk.Label(info_grid, text="", font=('Arial', 9))
        self.dominant_type_value.grid(row=1, column=3, sticky=tk.W, pady=2, padx=10)

        # Ø§Ù„ØµÙ Ø§Ù„Ø«Ø§Ù„Ø«
        ttk.Label(info_grid, text="Total %:",
                  font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=2, padx=2)
        self.total_percentage_value = ttk.Label(info_grid, text="", font=('Arial', 9))
        self.total_percentage_value.grid(row=2, column=1, sticky=tk.W, pady=2, padx=10)


        # ========== SECTION 2: COLORS DETAILS ==========
        colors_frame = ttk.LabelFrame(self.scrollable_frame, text="COLORS DETAILS", padding=10)
        colors_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # ØªÙ…Ø¯Ø¯ Ù„Ù…Ù„Ø¡ Ø§Ù„ÙØ±Ø§Øº

        # Ø´Ø¬Ø±Ø© Ø§Ù„Ø£Ù„ÙˆØ§Ù† - Ø§Ø±ØªÙØ§Ø¹ Ø£Ù‚Ù„
        self.colors_tree = ttk.Treeview(
            colors_frame,
            columns=("code", "name", "dye_type", "percentage", "price_kg"),
            show="headings",
            height=6  # Ø§Ø±ØªÙØ§Ø¹ Ø£Ù‚Ù„
        )

        self.colors_tree.heading("code", text="Color Code")
        self.colors_tree.heading("name", text="Color Name")
        self.colors_tree.heading("dye_type", text="Dye Type")
        self.colors_tree.heading("percentage", text="%")
        self.colors_tree.heading("price_kg", text="Price EUR/kg")

        # Ø£Ø¨Ø¹Ø§Ø¯ Ø§Ù„Ø£Ø¹Ù…Ø¯Ø© - Ø£ØµØºØ± Ø¨ÙƒØ«ÙŠØ±
        self.colors_tree.column("code", width=80, anchor="center", minwidth=70)
        self.colors_tree.column("name", width=120, anchor="center", minwidth=100)
        self.colors_tree.column("dye_type", width=90, anchor="center", minwidth=80)
        self.colors_tree.column("percentage", width=60, anchor="center", minwidth=50)
        self.colors_tree.column("price_kg", width=80, anchor="center", minwidth=70)

        scrollbar_colors = ttk.Scrollbar(colors_frame, orient="vertical", command=self.colors_tree.yview)
        self.colors_tree.configure(yscrollcommand=scrollbar_colors.set)
        scrollbar_colors.pack(side=tk.RIGHT, fill=tk.Y)
        self.colors_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Ù…Ù„Ø®Øµ Ø§Ù„Ø£Ù„ÙˆØ§Ù† - Ø£ÙƒØ«Ø± Ø¥Ø­ÙƒØ§Ù…Ø§
        colors_summary_frame = ttk.Frame(colors_frame)
        colors_summary_frame.pack(fill=tk.X, pady=5)

        ttk.Label(colors_summary_frame, text="Colors:",
                  font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        self.colors_count_label = ttk.Label(colors_summary_frame, text="0",
                                            font=('Arial', 9, 'bold'))
        self.colors_count_label.pack(side=tk.LEFT, padx=2)

        ttk.Label(colors_summary_frame, text="Total %:",
                  font=('Arial', 9)).pack(side=tk.LEFT, padx=10)
        self.colors_percentage_label = ttk.Label(colors_summary_frame, text="0.00%",
                                                 font=('Arial', 9, 'bold'))
        self.colors_percentage_label.pack(side=tk.LEFT, padx=2)

        # ========== SECTION 3: CHEMICALS REQUIRED ==========
        chemicals_frame = ttk.LabelFrame(self.scrollable_frame, text="CHEMICALS REQUIRED", padding=10)
        chemicals_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5) # ØªÙ…Ø¯Ø¯ Ù„Ù…Ù„Ø¡ Ø§Ù„ÙØ±Ø§Øº

        # Ø´Ø¬Ø±Ø© Ø§Ù„ÙƒÙŠÙ…Ø§ÙˆÙŠØ§Øª - Ø§Ø±ØªÙØ§Ø¹ Ø£Ù‚Ù„ ÙˆØ¹Ø±Ø¶ Ù…Ø¶Ø¨ÙˆØ·
        self.chemicals_tree = ttk.Treeview(
            chemicals_frame,
            columns=("code", "name", "quantity", "unit"),
            show="headings",
            height=4  # Ø§Ø±ØªÙØ§Ø¹ Ø£Ù‚Ù„
        )

        self.chemicals_tree.heading("code", text="Code")
        self.chemicals_tree.heading("name", text="Chemical Name")
        self.chemicals_tree.heading("quantity", text="Quantity")
        self.chemicals_tree.heading("unit", text="Unit")

        # Ø£Ø¨Ø¹Ø§Ø¯ Ø§Ù„Ø£Ø¹Ù…Ø¯Ø© Ù…Ø¶Ø¨ÙˆØ·Ø© ØªÙ…Ø§Ù…Ø§Ù‹ Ù„Ø±Ø¤ÙŠØ© g/l
        self.chemicals_tree.column("code", width=80, anchor="center", minwidth=60)
        self.chemicals_tree.column("name", width=200, anchor="center", minwidth=180)
        self.chemicals_tree.column("quantity", width=100, anchor="center", minwidth=80)
        self.chemicals_tree.column("unit", width=60, anchor="center", minwidth=50)  # Ø¹Ø±Ø¶ ÙƒØ§ÙÙŠ Ù„Ù€ g/l

        scrollbar_chem = ttk.Scrollbar(chemicals_frame, orient="vertical", command=self.chemicals_tree.yview)
        self.chemicals_tree.configure(yscrollcommand=scrollbar_chem.set)
        scrollbar_chem.pack(side=tk.RIGHT, fill=tk.Y)
        self.chemicals_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def setup_control_buttons(self):
        """Ø¥Ø¹Ø¯Ø§Ø¯ Ø£Ø²Ø±Ø§Ø± Ø§Ù„ØªØ­ÙƒÙ… ÙÙŠ Ø§Ù„Ø£Ø³ÙÙ„"""
        # Ø¥Ø·Ø§Ø± Ù„Ø£Ø²Ø±Ø§Ø± Ø§Ù„ØªØ­ÙƒÙ… ÙÙŠ Ø£Ø³ÙÙ„ Ø§Ù„Ù†Ø§ÙØ°Ø©
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=5, side=tk.BOTTOM)

        # Ø¬Ø¹Ù„ Ø§Ù„Ø£Ø²Ø±Ø§Ø± ÙÙŠ ØµÙ ÙˆØ§Ø­Ø¯
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Export to PDF",
                   command=self.export_selected_recipe, width=15, style='Sub.TButton').pack(side=tk.LEFT, padx=5)



        ttk.Button(button_frame, text="Delete Recipe",
                   command=self.delete_recipe, width=15, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Refresh",
                   command=self.refresh_recipes, width=15, style='Sub.TButton').pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Close",
                   command=self.window.destroy, width=15, style='Sub.TButton').pack(side=tk.RIGHT, padx=5)

    # Ø¨Ø§Ù‚ÙŠ Ø§Ù„Ø¯ÙˆØ§Ù„ ØªØ¨Ù‚Ù‰ ÙƒÙ…Ø§ Ù‡ÙŠ (Ø¯ÙˆÙ† ØªØºÙŠÙŠØ±)
    # load_recipes, perform_search, reset_search, display_recipes, select_recipe_by_id
    # on_recipe_select, show_recipe_details, update_main_details_tab, update_cost_tab
    # calculate_custom_batch, clear_all_tabs, export_selected_recipe, delete_recipe
    # refresh_recipes, copy_recipe

    def load_recipes(self):
        """ØªØ­Ù…ÙŠÙ„ Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª"""
        try:
            # ØªØ­Ù…ÙŠÙ„ Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª
            recipes = self.db.get_all_recipes()

            # Ø­ÙØ¸ Ø¬Ù…ÙŠØ¹ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ù„Ù„Ø¨Ø­Ø« ÙˆØ§Ù„ØªØ±ØªÙŠØ¨
            self.all_recipes_data = []

            # Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª Ø¥Ù„Ù‰ Ø§Ù„Ø´Ø¬Ø±Ø©
            for recipe in recipes:
                recipe_data = (
                    recipe.id,
                    recipe.recipe_code,
                    recipe.name,
                    recipe.created_at.split()[0] if recipe.created_at else ""
                )

                # Ø­ÙØ¸ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª
                self.all_recipes_data.append(recipe_data)

            # Ø¹Ø±Ø¶ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø¨Ø§Ø³ØªØ®Ø¯Ø§Ù… display_recipes Ù„Ø¶Ù…Ø§Ù† ØªØ­Ø¯ÙŠØ« current_displayed_data
            self.display_recipes(self.all_recipes_data)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load recipes: {str(e)}", parent=self.window)

    def perform_search(self):
        """ØªÙ†ÙÙŠØ° Ø§Ù„Ø¨Ø­Ø«"""
        code_search = self.search_code_var.get().strip().upper()
        name_search = self.search_name_var.get().strip().lower()

        if not code_search and not name_search:
            # Ø¥Ø°Ø§ ÙƒØ§Ù† Ø§Ù„Ø¨Ø­Ø« ÙØ§Ø±ØºØ§Ù‹ØŒ Ø¹Ø±Ø¶ Ø¬Ù…ÙŠØ¹ Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª
            self.display_recipes(self.all_recipes_data)
            return

        filtered_recipes = []
        for recipe_data in self.all_recipes_data:
            # Ø§Ù„Ø¨Ø­Ø« Ø¨Ø§Ù„ÙƒÙˆØ¯
            code_match = code_search in str(recipe_data[1]).upper() if code_search else True

            # Ø§Ù„Ø¨Ø­Ø« Ø¨Ø§Ù„Ø§Ø³Ù…
            name_match = name_search in str(recipe_data[2]).lower() if name_search else True

            if code_match and name_match:
                filtered_recipes.append(recipe_data)

        if filtered_recipes:
            self.display_recipes(filtered_recipes)
        else:
            messagebox.showinfo("Search Result", "No recipes found matching your search criteria", parent=self.window)
            self.display_recipes([])

    def reset_search(self):
        """Ø¥Ø¹Ø§Ø¯Ø© ØªØ¹ÙŠÙŠÙ† Ø§Ù„Ø¨Ø­Ø«"""
        self.search_code_var.set("")
        self.search_name_var.set("")
        self.display_recipes(self.all_recipes_data)
        self.search_code_entry.focus()

    def display_recipes(self, recipes_data):
        """Ø¹Ø±Ø¶ Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª ÙÙŠ Ø§Ù„Ø´Ø¬Ø±Ø©"""
        # Ù…Ø³Ø­ Ø§Ù„Ø´Ø¬Ø±Ø©
        for item in self.recipe_tree.get_children():
            self.recipe_tree.delete(item)

        # Ø­ÙØ¸ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ø¹Ø±ÙˆØ¶Ø© Ø­Ø§Ù„ÙŠØ§Ù‹
        self.current_displayed_data = list(recipes_data)

        # Ø¥Ø¶Ø§ÙØ© Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª
        for recipe_data in recipes_data:
            self.recipe_tree.insert("", tk.END, values=recipe_data)

    def select_recipe_by_id(self, recipe_id: int):
        """ØªØ­Ø¯ÙŠØ¯ Ø±ÙŠØªØ´Øª Ø¨ÙˆØ§Ø³Ø·Ø© ID"""
        # Ø§Ù„Ø¨Ø­Ø« Ø¹Ù† Ø§Ù„Ø±ÙŠØªØ´Øª ÙÙŠ Ø§Ù„Ø´Ø¬Ø±Ø©
        for item in self.recipe_tree.get_children():
            values = self.recipe_tree.item(item, "values")
            if values and int(values[0]) == recipe_id:
                self.recipe_tree.selection_set(item)
                self.recipe_tree.focus(item)
                self.recipe_tree.see(item)
                # ØªØ£Ø®ÙŠØ± Ø¹Ø±Ø¶ Ø§Ù„ØªÙØ§ØµÙŠÙ„ Ù‚Ù„ÙŠÙ„Ø§Ù‹ Ù„Ù„ØªØ£ÙƒØ¯ Ù…Ù† ØªØ­Ù…ÙŠÙ„ Ø§Ù„Ø´Ø¬Ø±Ø©
                self.window.after(100, lambda: self.on_recipe_select())
                break

    def on_recipe_select(self, event=None):
        """Ø¹Ù†Ø¯ ØªØ­Ø¯ÙŠØ¯ Ø±ÙŠØªØ´Øª"""
        selected = self.recipe_tree.selection()
        if not selected:
            return

        recipe_id = int(self.recipe_tree.item(selected[0], "values")[0])
        self.show_recipe_details(recipe_id)

    def show_recipe_details(self, recipe_id: int):
        """Ø¹Ø±Ø¶ ØªÙØ§ØµÙŠÙ„ Ø§Ù„Ø±ÙŠØªØ´Øª ÙÙŠ Ø¬Ù…ÙŠØ¹ Ø§Ù„ØªØ¨ÙˆÙŠØ¨Ø§Øª"""
        try:
            # Ø§Ù„Ø­ØµÙˆÙ„ Ø¹Ù„Ù‰ ØªÙØ§ØµÙŠÙ„ Ø§Ù„Ø±ÙŠØªØ´Øª Ù…Ù† Ù‚Ø§Ø¹Ø¯Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª
            recipe_data = self.db.get_recipe_details(recipe_id)
            
            if not recipe_data:
                self.clear_all_tabs()
                return

            recipe_obj = recipe_data['recipe']
            colors_list = recipe_data['colors']
            chemicals = recipe_data.get('chemicals', [])  # Ø§Ø³ØªØ±Ø¬Ø§Ø¹ Ø§Ù„ÙƒÙŠÙ…Ø§ÙˆÙŠØ§Øª Ø§Ù„Ù…Ø­ÙÙˆØ¸Ø©
            total_percentage = recipe_data.get('total_percentage', 0.0) or 0.0
            total_cost = recipe_data.get('total_cost', 0.0) or 0.0
            
            # ØªØ­Ø¯ÙŠØ¯ Ø§Ù„Ù†ÙˆØ¹ Ø§Ù„Ù…Ù‡ÙŠÙ…Ù† Ù…Ù† Ø§Ù„Ø£Ù„ÙˆØ§Ù†
            type_totals = {}
            for color in colors_list:
                dye_type = color["dye_type"]
                type_totals[dye_type] = type_totals.get(dye_type, 0) + color["percentage"]

            dominant_type = max(type_totals, key=type_totals.get) if type_totals else "Unknown"

            # ØªØ­Ø¯ÙŠØ« Ø¬Ù…ÙŠØ¹ Ø§Ù„ØªØ¨ÙˆÙŠØ¨Ø§Øª
            self.update_main_details_tab(recipe_obj.recipe_code, recipe_obj.name, recipe_obj.created_at,
                                         dominant_type, total_percentage, total_cost,
                                         colors_list, chemicals)

            # Ø­ÙØ¸ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ø­Ø§Ù„ÙŠØ© Ø¨Ø´ÙƒÙ„ ØµØ­ÙŠØ­
            self.current_recipe_data = {
                'id': recipe_id,
                'recipe_code': recipe_obj.recipe_code,
                'name': recipe_obj.name,
                'created_at': recipe_obj.created_at,
                'colors': colors_list,
                'chemicals': chemicals,
                'total_percentage': total_percentage,
                'dominant_type': dominant_type,
                'total_cost': total_cost
            }

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load recipe details: {str(e)}", parent=self.window)

    def update_main_details_tab(self, recipe_code, recipe_name, created_at,
                                dominant_type, total_percentage, total_cost,
                                colors_list, chemicals):
        """ØªØ­Ø¯ÙŠØ« ØªØ¨ÙˆÙŠØ¨ Ø§Ù„ØªÙØ§ØµÙŠÙ„ Ø§Ù„Ø±Ø¦ÙŠØ³ÙŠØ©"""
        # ØªØ­Ø¯ÙŠØ« Ù…Ø¹Ù„ÙˆÙ…Ø§Øª Ø§Ù„ÙˆØµÙØ©
        self.recipe_code_value.config(text=recipe_code or "N/A")
        self.recipe_name_value.config(text=recipe_name)
        self.created_date_value.config(text=created_at)
        self.dominant_type_value.config(text=dominant_type)
        self.total_percentage_value.config(text=f"{(total_percentage or 0.0):.2f}%")

        # ØªØ­Ø¯ÙŠØ« Ø´Ø¬Ø±Ø© Ø§Ù„Ø£Ù„ÙˆØ§Ù†
        for item in self.colors_tree.get_children():
            self.colors_tree.delete(item)

        for color in colors_list:
            self.colors_tree.insert("", tk.END, values=(
                color["code"],
                color["name"],
                color["dye_type"],
                f"{(color.get('percentage', 0.0) or 0.0):.2f}%",
                f"EUR {(color.get('price_kg', 0.0) or 0.0):.2f}"
            ))

        # ØªØ­Ø¯ÙŠØ« Ù…Ù„Ø®Øµ Ø§Ù„Ø£Ù„ÙˆØ§Ù†
        self.colors_count_label.config(text=str(len(colors_list)))
        self.colors_percentage_label.config(text=f"{(total_percentage or 0.0):.2f}%")

        # ØªØ­Ø¯ÙŠØ« Ø´Ø¬Ø±Ø© Ø§Ù„ÙƒÙŠÙ…Ø§ÙˆÙŠØ§Øª
        for item in self.chemicals_tree.get_children():
            self.chemicals_tree.delete(item)

        for chemical in chemicals:
            self.chemicals_tree.insert("", tk.END, values=(
                chemical.code,
                chemical.name,
                chemical.quantity,
                chemical.unit
            ))

    def clear_all_tabs(self):
        """Ù…Ø³Ø­ Ø¬Ù…ÙŠØ¹ Ø§Ù„ØªØ¨ÙˆÙŠØ¨Ø§Øª"""
        # Ù…Ø¹Ù„ÙˆÙ…Ø§Øª Ø§Ù„ÙˆØµÙØ©
        self.recipe_code_value.config(text="")
        self.recipe_name_value.config(text="")
        self.created_date_value.config(text="")
        self.dominant_type_value.config(text="")
        self.total_percentage_value.config(text="")

        # Ø§Ù„Ø£Ù„ÙˆØ§Ù†
        for item in self.colors_tree.get_children():
            self.colors_tree.delete(item)
        self.colors_count_label.config(text="0")
        self.colors_percentage_label.config(text="0.00%")

        # Ø§Ù„ÙƒÙŠÙ…Ø§ÙˆÙŠØ§Øª
        for item in self.chemicals_tree.get_children():
            self.chemicals_tree.delete(item)

    def export_selected_recipe(self):
        """ØªØµØ¯ÙŠØ± Ø§Ù„Ø±ÙŠØªØ´Øª Ø§Ù„Ù…Ø­Ø¯Ø¯ Ø¥Ù„Ù‰ PDF"""
        if not hasattr(self, 'current_recipe_data') or self.current_recipe_data is None:
            messagebox.showwarning("Warning", "Please select a recipe first", parent=self.window)
            return

        try:
            # Ø¥Ù†Ø´Ø§Ø¡ ÙƒØ§Ø¦Ù† RecipeDetails
            from app.models import Recipe, RecipeDetails

            recipe_obj = Recipe(
                id=self.current_recipe_data['id'],
                recipe_code=self.current_recipe_data['recipe_code'],
                name=self.current_recipe_data['name'],
                created_at=self.current_recipe_data['created_at']
            )

            recipe_details = RecipeDetails(
                recipe=recipe_obj,
                colors=self.current_recipe_data['colors'],
                chemicals=self.current_recipe_data['chemicals'],
                total_percentage=self.current_recipe_data['total_percentage'],
                dominant_type=self.current_recipe_data['dominant_type'],
                cost=self.current_recipe_data['total_cost']
            )

            # Ø§Ø³ØªØ®Ø¯Ø§Ù… Ø§Ù„ØªØµØ¯ÙŠØ± Ø§Ù„ØªÙ„Ù‚Ø§Ø¦ÙŠ
            pdf_path = PDFExporter.export_recipe_to_pdf_auto(recipe_details)

            if pdf_path:
                messagebox.showinfo("âœ… PDF Exported",
                                    f"Recipe exported successfully!\n\n"
                                    f"File saved to:\n{pdf_path}",
                                    parent=self.window)
            else:
                messagebox.showwarning("Warning", "Failed to export PDF", parent=self.window)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export recipe: {str(e)}", parent=self.window)

    def delete_recipe(self):
        """Ø­Ø°Ù Ø§Ù„Ø±ÙŠØªØ´Øª Ø§Ù„Ù…Ø­Ø¯Ø¯"""
        selected = self.recipe_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a recipe to delete", parent=self.window)
            return

        recipe_id = int(self.recipe_tree.item(selected[0], "values")[0])
        recipe_code = self.recipe_tree.item(selected[0], "values")[1]
        recipe_name = self.recipe_tree.item(selected[0], "values")[2]

        # Ø·Ù„Ø¨ Ø§Ù„ØªØ£ÙƒÙŠØ¯
        confirm_msg = f"Are you sure you want to delete recipe '{recipe_name}'?"
        if recipe_code:
            confirm_msg = f"Are you sure you want to delete recipe '{recipe_code} - {recipe_name}'?"

        confirm = messagebox.askyesno("Confirm Delete", confirm_msg, parent=self.window)

        if confirm:
            try:
                self.db.delete_recipe(recipe_id)
                self.load_recipes()
                self.clear_all_tabs()
                messagebox.showinfo("Success", f"Recipe '{recipe_name}' deleted successfully!", parent=self.window)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete recipe: {str(e)}", parent=self.window)

    def sort_treeview(self, col):
        """ØªØ±ØªÙŠØ¨ Ø§Ù„Ø´Ø¬Ø±Ø© Ø­Ø³Ø¨ Ø§Ù„Ø¹Ù…ÙˆØ¯ Ø§Ù„Ù…Ø­Ø¯Ø¯"""
        if not self.current_displayed_data:
            return

        # ØªØ­Ø¯ÙŠØ¯ Ø¥Ø°Ø§ ÙƒØ§Ù† Ù†ÙØ³ Ø§Ù„Ø¹Ù…ÙˆØ¯ØŒ Ø¹ÙƒØ³ Ø§Ù„ØªØ±ØªÙŠØ¨
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = col
            self.sort_reverse = False

        # ØªØ±ØªÙŠØ¨ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª
        if col == "id":
            # ØªØ±ØªÙŠØ¨ Ø±Ù‚Ù…ÙŠ Ù„Ù„Ù€ ID
            sorted_data = sorted(self.current_displayed_data, key=lambda x: int(x[0]), reverse=self.sort_reverse)
        else:
            # ØªØ±ØªÙŠØ¨ Ù†ØµÙŠ Ù„Ù„Ø£Ø¹Ù…Ø¯Ø© Ø§Ù„Ø£Ø®Ø±Ù‰
            col_index = {"recipe_code": 1, "name": 2, "created_at": 3}[col]
            sorted_data = sorted(self.current_displayed_data, key=lambda x: str(x[col_index]).lower(), reverse=self.sort_reverse)

        # Ø¹Ø±Ø¶ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ø±ØªØ¨Ø©
        self.display_recipes(sorted_data)

    def refresh_recipes(self):
        """ØªØ­Ø¯ÙŠØ« Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ø±ÙŠØªØ´ØªØ§Øª"""
        self.load_recipes()
        self.clear_all_tabs()

