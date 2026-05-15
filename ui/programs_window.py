"""
Programs window — recipe list + inline dyeing curve + step-by-step program text.
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional

from app.database import DatabaseManager
from app.dyeing_curves import determine_process, get_curve_data, get_phase_legend, get_program_text
from ui.theme_tokens import (
    setup_tree_tags, zebra_insert, get_theme_tokens,
    apply_excel_treeview_style, configure_sub_button_style, show_on_top,
)



class ProgramsWindow:
    """Programs page — recipe list left, curve + program steps right."""

    PAD_LEFT   = 65
    PAD_RIGHT  = 25
    PAD_TOP    = 40
    PAD_BOTTOM = 48

    def __init__(self, parent, db: DatabaseManager, dark_mode: bool = False):
        self.parent   = parent
        self.db       = db
        self.dark_mode = dark_mode
        self.palette  = get_theme_tokens(dark_mode)

        self.all_recipes_data      = []
        self.current_displayed_data = []
        self.current_recipe_data: Optional[Dict] = None
        self.curve = None
        self.sort_column  = "id"
        self.sort_reverse = False

        self.search_code_var = tk.StringVar()
        self.search_name_var = tk.StringVar()

        self.window = tk.Toplevel(parent)
        show_on_top(self.window, parent)
        self.window.title("Programs — Dyeing Curves")
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)

        sw = self.window.winfo_screenwidth()
        sh = self.window.winfo_screenheight()
        w  = int(sw * 0.94)
        h  = int(sh * 0.88)
        self.window.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.window.configure(bg=self.palette["bg"])
        self.window.resizable(True, True)
        self.window.minsize(1150, 740)

        self._configure_styles()
        self._build_ui()
        self.load_recipes()

    # ── Styles ──────────────────────────────────────────────────────────
    def _configure_styles(self):
        style = ttk.Style(self.window)
        apply_excel_treeview_style(style, self.palette, self.dark_mode)
        configure_sub_button_style(style, "Sub.TButton", self.palette)
        style.configure("PHV.TLabel",
                        font=("Arial", 9, "bold"),
                        foreground="#1565C0" if not self.dark_mode else "#7ab8f5")

    # ── Main UI ─────────────────────────────────────────────────────────
    def _build_ui(self):
        root = ttk.Frame(self.window)
        root.pack(fill=tk.BOTH, expand=True)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)

        # Search bar
        sf = ttk.LabelFrame(root, text="Recipe Filters", padding=8)
        sf.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        ttk.Label(sf, text="Code:").grid(row=0, column=0, padx=5, sticky="e")
        ce = ttk.Entry(sf, textvariable=self.search_code_var, width=15)
        ce.grid(row=0, column=1, padx=5, sticky="w")
        ce.bind("<KeyRelease>", lambda _e: self.perform_search())

        ttk.Label(sf, text="Name:").grid(row=0, column=2, padx=5, sticky="e")
        ne = ttk.Entry(sf, textvariable=self.search_name_var, width=25)
        ne.grid(row=0, column=3, padx=5, sticky="w")
        ne.bind("<KeyRelease>", lambda _e: self.perform_search())

        ttk.Button(sf, text="Clear", command=self.reset_search,
                   width=10, style="Sub.TButton").grid(row=0, column=4, padx=5)

        # Main paned: left list | right detail
        self.main_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self._build_left_panel()
        self._build_right_panel()
        self._build_bottom_buttons(root)
        self.window.after(80, self._apply_layout_tuning)

    # ── Left panel: recipe list ──────────────────────────────────────────
    def _build_left_panel(self):
        lf = ttk.LabelFrame(self.main_paned, text="Programs List", padding=8)
        self.main_paned.add(lf, weight=2)

        self.recipe_tree = ttk.Treeview(
            lf,
            columns=("id", "recipe_code", "name", "created_at"),
            show="headings", height=10,
        )
        self.recipe_tree["displaycolumns"] = ("recipe_code", "name", "created_at")
        for col, text, w in [
            ("id",         "ID",           55),
            ("recipe_code","Recipe Code",  110),
            ("name",       "Recipe Name",  230),
            ("created_at", "Created Date", 110),
        ]:
            self.recipe_tree.heading(col, text=text,
                                     command=lambda c=col: self.sort_treeview(c))
            self.recipe_tree.column(col, width=w, anchor="center")

        self.recipe_tree.bind("<<TreeviewSelect>>", self.on_recipe_select)

        sb = ttk.Scrollbar(lf, orient="vertical", command=self.recipe_tree.yview)
        self.recipe_tree.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.recipe_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        setup_tree_tags(self.recipe_tree, self.dark_mode)

    # ── Right panel: header + legend + curve + program ──────────────────
    def _build_right_panel(self):
        rf = ttk.Frame(self.main_paned)
        self.main_paned.add(rf, weight=4)

        # Header info
        header = ttk.LabelFrame(rf, text="Program Details", padding=4)
        header.pack(fill=tk.X, padx=2, pady=(0, 2))

        self.hdr_code    = ttk.Label(header, text="—", style="PHV.TLabel")
        self.hdr_name    = ttk.Label(header, text="—", style="PHV.TLabel")
        self.hdr_process = ttk.Label(header, text="—", style="PHV.TLabel")
        self.hdr_pct     = ttk.Label(header, text="0.00%", style="PHV.TLabel")

        for idx, (lbl, widget) in enumerate([
            ("Code:", self.hdr_code), ("Name:", self.hdr_name),
            ("Process:", self.hdr_process), ("Total %:", self.hdr_pct),
        ]):
            ttk.Label(header, text=lbl, font=("Arial", 9, "bold")).grid(
                row=0, column=idx*2, padx=(8,2), pady=2, sticky="e")
            widget.grid(row=0, column=idx*2+1, padx=(0,12), pady=2, sticky="w")

        self.hdr_desc = ttk.Label(
            header, text="Select a recipe to preview its dyeing curve program.",
            font=("Arial", 8, "italic"),
            foreground="#555" if not self.dark_mode else "#aaa")
        self.hdr_desc.grid(row=1, column=0, columnspan=8, padx=8, pady=(0,2), sticky="w")

        # Classification bar
        self.class_frame = ttk.LabelFrame(rf, text="Dye Classification", padding=3)
        self.class_frame.pack(fill=tk.X, padx=2, pady=(0, 2))
        self.class_labels = {}
        for idx, key in enumerate(["Group", "Exhaustion Temp", "Alkalinity", "Electrolyte"]):
            ttk.Label(self.class_frame, text=f"{key}:",
                      font=("Arial", 8, "bold")).grid(row=0, column=idx*2, padx=(8,2), sticky="e")
            lbl = ttk.Label(self.class_frame, text="—", font=("Arial", 8),
                            foreground="#1565C0" if not self.dark_mode else "#7ab8f5")
            lbl.grid(row=0, column=idx*2+1, padx=(0,14), sticky="w")
            self.class_labels[key] = lbl

        # Legend
        leg = ttk.Frame(rf)
        leg.pack(fill=tk.X, padx=2, pady=(0, 2))
        ttk.Label(leg, text="Phase Legend:", font=("Arial", 8, "bold")).pack(side=tk.LEFT, padx=4)
        for item in get_phase_legend():
            tk.Label(leg, text="●", fg=item["color"],
                     bg=self.palette["bg"], font=("Arial", 11)).pack(side=tk.LEFT, padx=(4,0))
            ttk.Label(leg, text=item["label"], font=("Arial", 8)).pack(side=tk.LEFT, padx=(0,5))

        # Content: curve | annotations | program steps
        content = ttk.PanedWindow(rf, orient=tk.HORIZONTAL)
        content.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0,2))
        self.content_paned = content

        # Curve canvas
        cf = ttk.LabelFrame(content, text="Temperature / Time Curve", padding=4)
        content.add(cf, weight=6)
        curve_bg = "#1a1a2e" if self.dark_mode else "#f8f9fa"
        self.canvas = tk.Canvas(cf, bg=curve_bg, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._draw_curve())

        # Right side: annotations + program steps
        right_side = ttk.Frame(content)
        content.add(right_side, weight=1)
        right_side.grid_columnconfigure(0, weight=1)
        right_side.grid_rowconfigure(0, weight=1)
        right_side.grid_rowconfigure(1, weight=1)

        # Annotations
        ann_lf = ttk.LabelFrame(right_side, text="Step Chemicals & Annotations", padding=6)
        ann_lf.grid(row=0, column=0, sticky="nsew")
        ann_sb = ttk.Scrollbar(ann_lf, orient="vertical")
        self.ann_text = tk.Text(
            ann_lf, wrap=tk.WORD, font=("Consolas", 9),
            yscrollcommand=ann_sb.set,
            bg="#1e1e2e" if self.dark_mode else "#ffffff",
            fg="#e0e0e0" if self.dark_mode else "#212121",
            relief="flat", padx=8, pady=6, height=8,
        )
        ann_sb.config(command=self.ann_text.yview)
        ann_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.ann_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.ann_text.config(state="disabled")

        # Program steps text
        prog_lf = ttk.LabelFrame(right_side, text="Dyeing Program Steps", padding=6)
        prog_lf.grid(row=1, column=0, sticky="nsew", pady=(4,0))
        prog_sb = ttk.Scrollbar(prog_lf, orient="vertical")
        self.prog_text = tk.Text(
            prog_lf, wrap=tk.WORD, font=("Consolas", 9),
            yscrollcommand=prog_sb.set,
            bg="#1a1a2e" if self.dark_mode else "#f0f4ff",
            fg="#e0e0e0" if self.dark_mode else "#212121",
            relief="flat", padx=8, pady=4, height=4,
        )
        prog_sb.config(command=self.prog_text.yview)
        prog_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.prog_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.prog_text.config(state="disabled")

        # Notes
        notes_lf = ttk.LabelFrame(right_side, text="Process Notes", padding=6)
        notes_lf.grid(row=2, column=0, sticky="ew", pady=(4,0))
        self.notes_text = tk.Text(
            notes_lf, wrap=tk.WORD, font=("Arial", 8),
            bg="#1e1e2e" if self.dark_mode else "#fffde7",
            fg="#e0e0e0" if self.dark_mode else "#212121",
            height=2, relief="flat", padx=6, pady=3,
        )
        self.notes_text.pack(fill=tk.BOTH, expand=True)
        self.notes_text.config(state="disabled")

    # ── Bottom buttons ───────────────────────────────────────────────────
    def _build_bottom_buttons(self, parent):
        bf = ttk.Frame(parent)
        bf.grid(row=2, column=0, sticky="ew", padx=10, pady=(2,8))

        ttk.Button(bf, text="Export Program PDF",
                   command=self.export_selected_recipe,
                   width=18, style="Sub.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(bf, text="Refresh",
                   command=self.refresh_recipes,
                   width=12, style="Sub.TButton").pack(side=tk.LEFT, padx=5)

        ttk.Button(bf, text="Close",
                   command=self.window.destroy,
                   width=12, style="Sub.TButton").pack(side=tk.RIGHT, padx=5)

    def _apply_layout_tuning(self):
        """Tune sash positions so curve is wider and right panels are narrower."""
        try:
            total_w = self.main_paned.winfo_width()
            if total_w > 200:
                self.main_paned.sashpos(0, int(total_w * 0.32))
        except Exception:
            pass
        try:
            total_w = self.content_paned.winfo_width()
            if total_w > 200:
                self.content_paned.sashpos(0, int(total_w * 0.68))
        except Exception:
            pass

    # ── Data loading ─────────────────────────────────────────────────────
    def load_recipes(self):
        try:
            recipes = self.db.get_all_recipes()
            self.all_recipes_data = [
                (r.id, r.recipe_code, r.name, r.created_at) for r in recipes
            ]
            self.display_recipes(self.all_recipes_data)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load recipes: {exc}", parent=self.window)

    def display_recipes(self, data):
        for item in self.recipe_tree.get_children():
            self.recipe_tree.delete(item)
        self.current_displayed_data = list(data)
        for row in data:
            zebra_insert(self.recipe_tree, row)

    def perform_search(self):
        code_s = self.search_code_var.get().strip().upper()
        name_s = self.search_name_var.get().strip().lower()
        if not code_s and not name_s:
            self.display_recipes(self.all_recipes_data)
            return
        filtered = [
            r for r in self.all_recipes_data
            if (not code_s or code_s in str(r[1]).upper()) and
               (not name_s or name_s in str(r[2]).lower())
        ]
        self.display_recipes(filtered)

    def reset_search(self):
        self.search_code_var.set("")
        self.search_name_var.set("")
        self.display_recipes(self.all_recipes_data)

    def sort_treeview(self, col: str):
        if not self.current_displayed_data:
            return
        if self.sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column  = col
            self.sort_reverse = False
        col_idx = {"id": 0, "recipe_code": 1, "name": 2, "created_at": 3}[col]
        key_fn  = (lambda x: int(x[0])) if col == "id" else (lambda x: str(x[col_idx]).lower())
        self.display_recipes(sorted(self.current_displayed_data,
                                    key=key_fn, reverse=self.sort_reverse))

    # ── Selection ────────────────────────────────────────────────────────
    def on_recipe_select(self, _event=None):
        sel = self.recipe_tree.selection()
        if not sel:
            return
        recipe_id = int(self.recipe_tree.item(sel[0], "values")[0])
        self.show_recipe_program(recipe_id)

    def show_recipe_program(self, recipe_id: int):
        try:
            data = self.db.get_recipe_details(recipe_id)
            if not data:
                return
            recipe_obj     = data["recipe"]
            colors_list    = data["colors"]
            chemicals      = data.get("chemicals", [])
            total_pct      = data.get("total_percentage", 0.0) or 0.0

            type_totals = {}
            for c in colors_list:
                dt = c.get("dye_type", "")
                type_totals[dt] = type_totals.get(dt, 0.0) + (c.get("percentage", 0.0) or 0.0)
            dominant = max(type_totals, key=type_totals.get) if type_totals else "Unknown"

            self.current_recipe_data = {
                "id":               recipe_id,
                "recipe_code":      recipe_obj.recipe_code,
                "name":             recipe_obj.name,
                "created_at":       recipe_obj.created_at,
                "colors":           colors_list,
                "chemicals":        chemicals,
                "total_percentage": total_pct,
                "dominant_type":    dominant,
                "total_cost":       data.get("total_cost", 0.0) or 0.0,
            }
            self._refresh_curve_view()
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load recipe: {exc}", parent=self.window)

    # ── Refresh all panels ───────────────────────────────────────────────
    def _refresh_curve_view(self):
        if not self.current_recipe_data:
            return
        colors    = self.current_recipe_data.get("colors", [])
        total_pct = self.current_recipe_data.get("total_percentage", 0.0) or 0.0
        pkey, pname, pdesc = determine_process(colors)
        self.curve = get_curve_data(pkey, total_pct)
        # تحديث اسم العملية في كائن المنحنى لضمان ظهوره في الـ PDF والرسوم البيانية
        if self.curve:
            self.curve["process_name"] = pname

        # Header
        self.hdr_code.config(text=self.current_recipe_data.get("recipe_code", "—"))
        self.hdr_name.config(text=self.current_recipe_data.get("name", "—"))
        self.hdr_process.config(text=pname)
        self.hdr_pct.config(text=f"{total_pct:.2f}%")
        self.hdr_desc.config(text=pdesc)

        # Classification bar
        cls = self.curve.get("classification", {})
        self.class_labels["Group"].config(text=cls.get("group", "—"))
        self.class_labels["Exhaustion Temp"].config(text=cls.get("exhaustion_temp", "—"))
        self.class_labels["Alkalinity"].config(text=cls.get("alkalinity", "—"))
        self.class_labels["Electrolyte"].config(text=cls.get("electrolyte", "—"))

        self._populate_annotations()
        self._populate_program_steps()
        self._populate_notes()
        self._draw_curve()

    # ── Annotations panel ────────────────────────────────────────────────
    def _populate_annotations(self):
        self.ann_text.config(state="normal")
        self.ann_text.delete("1.0", tk.END)
        self.ann_text.tag_configure("num",  font=("Consolas", 10, "bold"), foreground="#FF9800")
        self.ann_text.tag_configure("chem", font=("Consolas", 9),
                                    foreground="#4CAF50" if self.dark_mode else "#1565C0")
        self.ann_text.tag_configure("hr",   foreground="#555")

        if self.curve:
            # قاموس لتحويل أسماء المراحل الداخلية إلى أسماء عرض
            display_map = {
                "dyeing":     "Dyeing",
                "reduction":  "Reduction / Vatting",
                "oxidation":  "Oxidation",
                "soaping":    "Soaping",
                "rinse":      "Rinse",
                "neutralize": "Rinse / Neutralise",
            }

            for ann in self.curve.get("annotations", []):
                # تحديد اسم المرحلة بناءً على توقيت الخطوة
                t = ann['time']
                p_key = next((s["phase"] for s in self.curve.get("steps", []) if s["start_time"] <= t <= s["end_time"]), "Step")
                phase_name = display_map.get(p_key, p_key.title())

                self.ann_text.insert(tk.END, f"  {ann['number']}-{phase_name}  ", "num")
                self.ann_text.insert(tk.END, f"@ {ann['time']} min\n", "hr")
                for chem in ann.get("chemicals", []):
                    self.ann_text.insert(tk.END, f"    {chem}\n", "chem")
                self.ann_text.insert(tk.END, "\n")
        self.ann_text.config(state="disabled")

    # ── Program steps panel ──────────────────────────────────────────────
    def _populate_program_steps(self):
        self.prog_text.config(state="normal")
        self.prog_text.delete("1.0", tk.END)

        # Tags
        self.prog_text.tag_configure("phase_hdr",
                                     font=("Arial", 9, "bold"),
                                     foreground="#ffffff" if self.dark_mode else "#ffffff")
        self.prog_text.tag_configure("step_line",
                                     font=("Consolas", 9),
                                     foreground="#e0e0e0" if self.dark_mode else "#212121")

        if not self.curve:
            self.prog_text.config(state="disabled")
            return

        program = get_program_text(self.curve)
        for block in program:
            phase_name = block["phase"]
            color      = block["color"]
            lines      = block["lines"]

            # Dynamic tag per phase color
            tag_name = f"phase_{phase_name.replace(' ','_').replace('/','_')}"
            self.prog_text.tag_configure(tag_name,
                                         font=("Arial", 9, "bold"),
                                         foreground=color)
            self.prog_text.insert(tk.END, f"  {phase_name}\n", tag_name)
            for line in lines:
                self.prog_text.insert(tk.END, f"    {line}\n", "step_line")
            self.prog_text.insert(tk.END, "\n")

        self.prog_text.config(state="disabled")

    # ── Notes panel ──────────────────────────────────────────────────────
    def _populate_notes(self):
        self.notes_text.config(state="normal")
        self.notes_text.delete("1.0", tk.END)
        if self.curve:
            for note in self.curve.get("notes", []):
                self.notes_text.insert(tk.END, f"• {note}\n")
        self.notes_text.config(state="disabled")

    # ── Curve drawing ────────────────────────────────────────────────────
    def _draw_curve(self):
        c = self.canvas
        c.delete("all")
        if not self.curve:
            c.create_text(
                max(c.winfo_width()//2, 150), max(c.winfo_height()//2, 80),
                text="Select a recipe to show the dyeing curve.",
                fill="#666" if not self.dark_mode else "#bbb",
                font=("Arial", 10, "italic"),
            )
            return

        W, H = c.winfo_width(), c.winfo_height()
        if W < 140 or H < 140:
            return

        PL, PR, PT, PB = self.PAD_LEFT, self.PAD_RIGHT, self.PAD_TOP, self.PAD_BOTTOM
        pw = W - PL - PR
        ph = H - PT - PB
        total_time = self.curve["total_time"]
        max_temp   = self.curve["max_temp"]

        dark       = self.dark_mode
        axis_col   = "#cccccc" if dark else "#333333"
        grid_col   = "#333355" if dark else "#dddddd"
        lbl_col    = "#e0e0e0" if dark else "#333333"
        bg_plot    = "#1a1a2e" if dark else "#f8f9fa"

        def tx(t):   return PL + (t / total_time) * pw
        def ty(tmp): return PT + ph - (tmp / max_temp) * ph

        c.create_rectangle(PL, PT, PL+pw, PT+ph, fill=bg_plot, outline="")

        for temp in range(0, max_temp+1, 20):
            y = ty(temp)
            c.create_line(PL, y, PL+pw, y, fill=grid_col, dash=(3,4))
            c.create_text(PL-5, y, text=str(temp), anchor="e",
                          font=("Arial", 7), fill=lbl_col)
        for t in range(0, total_time+1, 20):
            x = tx(t)
            c.create_line(x, PT, x, PT+ph, fill=grid_col, dash=(3,4))
            c.create_text(x, PT+ph+5, text=str(t), anchor="n",
                          font=("Arial", 7), fill=lbl_col)

        c.create_line(PL, PT, PL, PT+ph,    fill=axis_col, width=2)
        c.create_line(PL, PT+ph, PL+pw, PT+ph, fill=axis_col, width=2)
        c.create_text(PL-38, PT+ph//2, text="Temp [°C]", angle=90,
                      font=("Arial", 8, "bold"), fill=lbl_col)
        c.create_text(PL+pw//2, PT+ph+34, text="Time [min]",
                      font=("Arial", 8, "bold"), fill=lbl_col)

        for step in self.curve.get("steps", []):
            x1 = tx(step["start_time"]); x2 = tx(step["end_time"])
            y1 = ty(step["start_temp"]); y2 = ty(step["end_temp"])
            yb = ty(0); col = step["color"]
            c.create_polygon(x1, yb, x1, y1, x2, y2, x2, yb,
                             fill=col, outline="", stipple="gray25")
            c.create_line(x1, y1, x2, y2, fill=col, width=3)
            # Step label inside the shaded band — placed below midline
            # so it never overlaps the numbered annotation circles above
            lbl = step.get("label", "")
            if lbl and (x2 - x1) > 35:
                label_y = min((y1 + y2) / 2 + 14, ty(0) - 8)
                c.create_text((x1 + x2) / 2, label_y,
                              text=lbl, font=("Arial", 7),
                              fill=col, justify="center")

        for ann in self.curve.get("annotations", []):
            t        = ann["time"]
            x        = tx(t)
            curve_y  = ty(self._temp_at(t))   # y on the curve line
            r        = 10
            # Place circle well above the curve so it never overlaps step labels
            circle_y = curve_y - 34
            # Clamp so circle doesn't go above the plot area
            circle_y = max(PT + r + 2, circle_y)

            # Dashed vertical line from curve to circle bottom
            c.create_line(x, curve_y, x, circle_y + r,
                          fill="#FF9800", dash=(2, 4), width=1)
            # Circle
            c.create_oval(x - r, circle_y - r, x + r, circle_y + r,
                          fill="#FF9800", outline="#E65100", width=2)
            # Number centred inside circle
            c.create_text(x, circle_y, text=str(ann["number"]),
                          font=("Arial", 9, "bold"), fill="white")

        c.create_text(PL+pw//2, PT//2, text=self.curve["process_name"],
                      font=("Arial", 11, "bold"), fill=lbl_col)

    def _temp_at(self, time_min: int) -> int:
        if not self.curve:
            return 0
        for step in self.curve.get("steps", []):
            st, et = step["start_time"], step["end_time"]
            if st <= time_min <= et:
                if et == st:
                    return step["start_temp"]
                r = (time_min - st) / (et - st)
                return int(step["start_temp"] + r * (step["end_temp"] - step["start_temp"]))
        steps = self.curve.get("steps", [])
        return steps[-1]["end_temp"] if steps else 0

    # ── Export ───────────────────────────────────────────────────────────
    def export_selected_recipe(self):
        """Export the Dyeing Program (curve steps) to PDF."""
        if not self.current_recipe_data or not self.curve:
            messagebox.showwarning("Warning", "Please select a recipe first.", parent=self.window)
            return
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                             Paragraph, Spacer, HRFlowable)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors as rl_colors
            from reportlab.lib.units import cm
            from datetime import datetime
            from app.utils import get_desktop_exports_dir

            folder = get_desktop_exports_dir()
            ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
            code = self.current_recipe_data.get("recipe_code", "NoCode")
            name = self.current_recipe_data.get("name", "Recipe")
            path = os.path.join(folder, f"Program_{code}_{ts}.pdf")

            doc    = SimpleDocTemplate(path, pagesize=A4,
                                       leftMargin=2*cm, rightMargin=2*cm,
                                       topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            elems  = []

            # Header
            elems.append(Paragraph("Dyeing Program", styles["Title"]))
            elems.append(Spacer(1, 0.2*cm))
            meta = [
                ["Recipe Code:", code,  "Recipe Name:", name],
                ["Process:", self.curve.get("process_name","—"),
                 "Total %:", f"{self.current_recipe_data.get('total_percentage',0):.2f}%"],
                ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M"), "", ""],
            ]
            mt = Table(meta, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 4.5*cm])
            mt.setStyle(TableStyle([
                ("FONTNAME",  (0,0),(0,-1), "Helvetica-Bold"),
                ("FONTNAME",  (2,0),(2,-1), "Helvetica-Bold"),
                ("FONTSIZE",  (0,0),(-1,-1), 9),
                ("TEXTCOLOR", (0,0),(0,-1), rl_colors.HexColor("#1565C0")),
                ("TEXTCOLOR", (2,0),(2,-1), rl_colors.HexColor("#1565C0")),
                ("TOPPADDING",    (0,0),(-1,-1), 3),
                ("BOTTOMPADDING", (0,0),(-1,-1), 3),
            ]))
            elems.append(mt)
            elems.append(HRFlowable(width="100%", thickness=1,
                                    color=rl_colors.HexColor("#1565C0")))
            elems.append(Spacer(1, 0.3*cm))

            # Classification
            cls = self.curve.get("classification", {})
            cls_data = [
                ["Group","Exhaustion Temp","Alkalinity","Electrolyte"],
                [cls.get("group","—"), cls.get("exhaustion_temp","—"),
                 cls.get("alkalinity","—"), cls.get("electrolyte","—")],
            ]
            ct = Table(cls_data, colWidths=[4.25*cm]*4)
            ct.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0), rl_colors.HexColor("#37474F")),
                ("TEXTCOLOR", (0,0),(-1,0), rl_colors.white),
                ("FONTNAME",  (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE",  (0,0),(-1,-1), 9),
                ("ALIGN",     (0,0),(-1,-1), "CENTER"),
                ("GRID",      (0,0),(-1,-1), 0.5, rl_colors.grey),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[rl_colors.HexColor("#E3F2FD")]),
                ("TOPPADDING",    (0,0),(-1,-1), 4),
                ("BOTTOMPADDING", (0,0),(-1,-1), 4),
            ]))
            elems.append(ct)
            elems.append(Spacer(1, 0.4*cm))

            # Program Steps
            elems.append(Paragraph("<b>Dyeing Program Steps</b>", styles["Heading2"]))
            elems.append(Spacer(1, 0.15*cm))
            PHASE_COLORS = {
                "Dyeing":"#2196F3","Reduction / Vatting":"#9C27B0",
                "Oxidation":"#FF9800","Soaping":"#F44336",
                "Rinse":"#4CAF50","Rinse / Neutralise":"#4CAF50",
            }
            program   = get_program_text(self.curve)
            prog_data = [["Phase","Step Details"]]
            for block in program:
                for i, line in enumerate(block["lines"]):
                    prog_data.append([block["phase"] if i==0 else "", line])
            pt = Table(prog_data, colWidths=[5*cm, 12*cm])
            rstyles = [
                ("BACKGROUND",(0,0),(-1,0), rl_colors.HexColor("#1565C0")),
                ("TEXTCOLOR", (0,0),(-1,0), rl_colors.white),
                ("FONTNAME",  (0,0),(-1,0), "Helvetica-Bold"),
                ("FONTSIZE",  (0,0),(-1,-1), 9),
                ("GRID",      (0,0),(-1,-1), 0.4, rl_colors.HexColor("#cccccc")),
                ("LEFTPADDING",(0,0),(-1,-1), 8),
                ("TOPPADDING",   (0,0),(-1,-1), 4),
                ("BOTTOMPADDING",(0,0),(-1,-1), 4),
                ("ALIGN",(0,0),(-1,-1),"LEFT"),
            ]
            r = 1
            for block in program:
                col = PHASE_COLORS.get(block["phase"], "#555")
                for i in range(len(block["lines"])):
                    if i == 0:
                        rstyles.append(("TEXTCOLOR",(0,r),(0,r), rl_colors.HexColor(col)))
                        rstyles.append(("FONTNAME", (0,r),(0,r), "Helvetica-Bold"))
                    bg = rl_colors.HexColor("#F5F5F5") if r%2 else rl_colors.white
                    rstyles.append(("BACKGROUND",(0,r),(-1,r), bg))
                    r += 1
            pt.setStyle(TableStyle(rstyles))
            elems.append(pt)
            elems.append(Spacer(1, 0.4*cm))

            # Annotations
            elems.append(Paragraph("<b>Step Chemicals & Annotations</b>", styles["Heading2"]))
            elems.append(Spacer(1, 0.15*cm))
            
            # قاموس لتحويل أسماء المراحل الداخلية إلى أسماء عرض (مكرر من _populate_annotations)
            display_map = {
                "dyeing":     "Dyeing",
                "reduction":  "Reduction / Vatting",
                "oxidation":  "Oxidation",
                "soaping":    "Soaping",
                "rinse":      "Rinse",
                "neutralize": "Rinse / Neutralise",
            }

            for ann in self.curve.get("annotations", []):
                t = ann['time']
                p_key = next((s["phase"] for s in self.curve.get("steps", []) if s["start_time"] <= t <= s["end_time"]), "Step")
                phase_name = display_map.get(p_key, p_key.title())
                elems.append(Paragraph(
                    f"<b>{ann['number']}-{phase_name}  @  {ann['time']} min</b>",
                    ParagraphStyle("ah", parent=styles["Normal"],
                                   textColor=rl_colors.HexColor("#E65100"),
                                   fontSize=9, spaceAfter=2)))
                for chem in ann.get("chemicals", []):
                    elems.append(Paragraph(
                        f"&nbsp;&nbsp;&nbsp;{chem}",
                        ParagraphStyle("cl", parent=styles["Normal"],
                                       fontSize=8, leading=12,
                                       textColor=rl_colors.HexColor("#1565C0"))))
                elems.append(Spacer(1, 0.2*cm))

            # Notes
            notes = self.curve.get("notes", [])
            if notes:
                elems.append(HRFlowable(width="100%", thickness=0.5, color=rl_colors.grey))
                elems.append(Spacer(1, 0.2*cm))
                elems.append(Paragraph("<b>Process Notes</b>", styles["Heading3"]))
                for note in notes:
                    elems.append(Paragraph(f"• {note}",
                        ParagraphStyle("nt", parent=styles["Normal"], fontSize=8, leading=12)))

            doc.build(elems)
            messagebox.showinfo("PDF Exported",
                                f"Dyeing program exported to:\n{path}", parent=self.window)
        except ImportError:
            messagebox.showerror("Error", "reportlab is required for PDF export.", parent=self.window)
        except Exception as exc:
            messagebox.showerror("Error", f"Export failed:\n{exc}", parent=self.window)


    def refresh_recipes(self):
        self.load_recipes()
