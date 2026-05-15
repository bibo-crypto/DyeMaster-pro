"""Shared UI tokens and style helpers — DyeMaster Pro modern theme."""

from tkinter import ttk
import tkinter as tk

FONT_FAMILY  = "Segoe UI"
BASE_FONT    = (FONT_FAMILY, 10)
BOLD_FONT    = (FONT_FAMILY, 10, "bold")
SMALL_FONT   = (FONT_FAMILY, 9)
HEADING_FONT = (FONT_FAMILY, 11, "bold")
TREE_BODY_FONT = (FONT_FAMILY, 10, "bold")

# ─────────────────────────────────────────────────────────────────────────────
#  Colour Palettes  (matching the Excel screenshot: white/light-blue theme)
# ─────────────────────────────────────────────────────────────────────────────

LIGHT_THEME = {
    "bg":                "#D9E1EE",   # outer window — medium blue-grey
    "frame_bg":          "#D9E1EE",
    "card_bg":           "#FFFFFF",

    "fg":                "#1C232B",
    "fg_muted":          "#5A6A7E",

    "entry_bg":          "#FFFFFF",
    "entry_border":      "#A8B8CC",

    "button_bg":         "#1565C0",   # rich royal blue — like Excel ribbon
    "button_fg":         "#FFFFFF",
    "button_active_bg":  "#0D47A1",
    "button_shadow":     "#8BAAD0",

    "accent_bg":         "#1565C0",
    "accent_active_bg":  "#0D47A1",

    "header_bg":         "#C5D2E4",   # slightly darker than bg for toolbar relief
    "header_border":     "#8BAAD0",

    "tree_bg":           "#D2D2D2",
    "tree_fg":           "#1C232B",
    "tree_selected_bg":  "#8F9FB2",

    "labelframe_border": "#8BAAD0",
    "statusbar_bg":      "#C5D2E4",
}

DARK_THEME = {
    # ── Backgrounds (layered depth) ──────────────────────────────────────
    "bg":                "#0F1117",   # deepest — window background
    "frame_bg":          "#0F1117",
    "card_bg":           "#1C1F2E",   # panels / cards

    # ── Text ─────────────────────────────────────────────────────────────
    "fg":                "#E2E8F0",   # primary text
    "fg_muted":          "#64748B",   # secondary / placeholder

    # ── Inputs ───────────────────────────────────────────────────────────
    "entry_bg":          "#1C1F2E",
    "entry_border":      "#334155",

    # ── Buttons ──────────────────────────────────────────────────────────
    "button_bg":         "#3B82F6",   # bright blue — stands out on dark bg
    "button_fg":         "#FFFFFF",
    "button_active_bg":  "#2563EB",
    "button_shadow":     "#0F1117",

    # ── Accent ───────────────────────────────────────────────────────────
    "accent_bg":         "#6366F1",   # indigo accent
    "accent_active_bg":  "#4F46E5",

    # ── Toolbar / header ─────────────────────────────────────────────────
    "header_bg":         "#161B2C",   # slightly lighter than bg
    "header_border":     "#1E293B",

    # ── Treeview ─────────────────────────────────────────────────────────
    "tree_bg":           "#1C1F2E",
    "tree_fg":           "#E2E8F0",
    "tree_selected_bg":  "#3B82F6",

    # ── Borders / frames ─────────────────────────────────────────────────
    "labelframe_border": "#1E293B",
    "statusbar_bg":      "#0A0D14",   # darkest — status bar
}

# Zebra rows — comfortable contrast: gray + off-white
ZEBRA_LIGHT = {"odd": "#D3D3D3", "even": "#C9CDD3", "hover": "#E1E6EE"}
ZEBRA_DARK  = {"odd": "#1C1F2E", "even": "#161B2C", "hover": "#1E293B"}


def get_theme_tokens(dark_mode: bool) -> dict:
    return DARK_THEME.copy() if dark_mode else LIGHT_THEME.copy()


# ─────────────────────────────────────────────────────────────────────────────
#  Button helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_button(style: ttk.Style, name: str, bg: str, fg: str, active_bg: str,
                 font=None, padding=8):
    """Modern button — flat in dark backgrounds, raised in light."""
    f = font or BOLD_FONT
    style.configure(
        name,
        font=f,
        padding=padding,
        background=bg,
        foreground=fg,
        relief="flat",
        borderwidth=0,
        anchor="center",
    )
    style.map(
        name,
        background=[("active", active_bg), ("pressed", active_bg),
                    ("disabled", "#334155")],
        foreground=[("disabled", "#64748B")],
        relief=[("pressed", "flat"), ("active", "flat")],
    )


def configure_sub_button_style(style: ttk.Style, style_name: str, palette: dict):
    """Used by all sub-windows (recipe creator, colors, etc.)."""
    _make_button(style, style_name,
                 palette["button_bg"], palette["button_fg"], palette["button_active_bg"],
                 font=BOLD_FONT, padding=7)


def configure_all_button_styles(style: ttk.Style, palette: dict) -> None:
    """Register every named button style used across the whole app."""
    _make_button(style, "App.TButton",
                 palette["button_bg"], palette["button_fg"], palette["button_active_bg"],
                 font=BOLD_FONT, padding=7)
    _make_button(style, "Import.TButton",  "#1B8A4C", "#FFFFFF", "#136836")
    _make_button(style, "Test.TButton",    "#D45500", "#FFFFFF", "#B04400")
    _make_button(style, "Data.TButton",    "#1A6B7A", "#FFFFFF", "#125565")
    _make_button(style, "Accent.TButton",
                 palette["accent_bg"], palette["button_fg"], palette["accent_active_bg"],
                 font=BOLD_FONT, padding=7)
    _make_button(style, "Danger.TButton",  "#B02020", "#FFFFFF", "#8C1818")
    _make_button(style, "Toggle.TButton",
                 palette["header_bg"], palette["fg"], palette["labelframe_border"],
                 font=BASE_FONT, padding=6)
    # Sub.TButton for child windows
    configure_sub_button_style(style, "Sub.TButton", palette)


# ─────────────────────────────────────────────────────────────────────────────
#  Global ttk styles  (frames, labels, entries, treeview, notebook)
# ─────────────────────────────────────────────────────────────────────────────

def apply_global_styles(style: ttk.Style, palette: dict, dark_mode: bool) -> None:
    """Call once at startup and again after every theme toggle."""
    bg       = palette["bg"]
    fg       = palette["fg"]
    entry_bg = palette["entry_bg"]
    hdr_bg   = palette["header_bg"]
    lf_bdr   = palette["labelframe_border"]
    card     = palette["card_bg"]

    # ── Frames ────────────────────────────────────────────────────────
    style.configure("TFrame",      background=bg)
    style.configure("RaisedPanel.TFrame",
                    background=hdr_bg,
                    relief="raised",
                    borderwidth=3)

    # ── Labels ────────────────────────────────────────────────────────
    style.configure("TLabel",
                    background=bg, foreground=fg, font=BASE_FONT)

    # ── LabelFrame ────────────────────────────────────────────────────
    # Dark: subtle flat border | Light: ridge 3-D inset
    style.configure("TLabelframe",
                    background=bg,
                    bordercolor=lf_bdr,
                    relief="flat" if dark_mode else "ridge",
                    borderwidth=2 if dark_mode else 3)
    style.configure("TLabelframe.Label",
                    background=bg,
                    foreground=palette["accent_bg"] if dark_mode else fg,
                    font=BOLD_FONT)

    # ── Entries ───────────────────────────────────────────────────────
    style.configure("TEntry",
                    fieldbackground=entry_bg,
                    foreground=fg,
                    insertcolor=fg,
                    borderwidth=2 if dark_mode else 2,
                    relief="flat" if dark_mode else "sunken")
    style.map("TCombobox",
              fieldbackground=[("readonly", entry_bg)],
              selectbackground=[("readonly", entry_bg)],
              selectforeground=[("readonly", fg)],
              background=[("readonly", entry_bg)])
    style.configure("TCombobox", foreground=fg)

    # ── Scrollbar ─────────────────────────────────────────────────────
    scrollbar_bg = "#1E293B" if dark_mode else palette["button_bg"]
    scrollbar_trough = "#0F1117" if dark_mode else hdr_bg
    style.configure("TScrollbar",
                    background=scrollbar_bg,
                    troughcolor=scrollbar_trough,
                    borderwidth=0 if dark_mode else 1,
                    arrowcolor=palette["button_fg"],
                    relief="flat" if dark_mode else "raised")
    style.map("TScrollbar",
              background=[("active", palette["button_bg"])])

    # ── Notebook ──────────────────────────────────────────────────────
    style.configure("TNotebook",     background=bg, borderwidth=0)
    style.configure("TNotebook.Tab",
                    background="#1E293B" if dark_mode else hdr_bg,
                    foreground=fg,
                    font=BOLD_FONT, padding=(12, 6), borderwidth=0,
                    relief="flat")
    style.map("TNotebook.Tab",
              background=[("selected", card)],
              foreground=[("selected", palette["accent_bg"] if dark_mode else palette["button_bg"])],
              relief=[("selected", "flat")])

    # ── Separator ─────────────────────────────────────────────────────
    style.configure("TSeparator", background=lf_bdr)

    # ── Treeview ──────────────────────────────────────────────────────
    apply_excel_treeview_style(style, palette, dark_mode)

    # ── All button styles ─────────────────────────────────────────────
    configure_all_button_styles(style, palette)


# ─────────────────────────────────────────────────────────────────────────────
#  Excel-like Treeview
# ─────────────────────────────────────────────────────────────────────────────

def apply_excel_treeview_style(style: ttk.Style, palette: dict, dark_mode: bool) -> None:
    """Configure global Excel-like Treeview: grid lines, zebra rows, bold headings."""
    zc = ZEBRA_DARK if dark_mode else ZEBRA_LIGHT
    style._dyemaster_zc = zc          # type: ignore[attr-defined]

    # Body rows
    style.configure(
        "Treeview",
        background=zc["odd"],
        foreground=palette["tree_fg"],
        fieldbackground=zc["odd"],
        font=TREE_BODY_FONT,
        rowheight=32,
        borderwidth=1,
        relief="solid",
    )
    style.map(
        "Treeview",
        background=[("selected", palette["tree_selected_bg"])],
        foreground=[("selected", "#FFFFFF")],
    )

    # Column headings — rich dark blue in dark mode
    hdr_bg  = "#A9BBD2" if not dark_mode else "#1E293B"
    hdr_act = "#95ACC7" if not dark_mode else "#334155"
    hdr_fg  = "#000000" if not dark_mode else "#93C5FD"  # light blue text in dark
    style.configure(
        "Treeview.Heading",
        font=BOLD_FONT,
        background=hdr_bg,
        foreground=hdr_fg,
        relief="flat" if dark_mode else "raised",
        borderwidth=1,
        padding=(6, 7),
    )
    style.map(
        "Treeview.Heading",
        background=[("active", hdr_act)],
        relief=[("active", "sunken" if not dark_mode else "flat")],
    )


def setup_tree_tags(tree: ttk.Treeview, dark_mode: bool) -> None:
    """Set oddrow / evenrow colour tags on a specific Treeview widget."""
    style = ttk.Style(tree)
    zc = getattr(style, "_dyemaster_zc", None)
    if not isinstance(zc, dict):
        zc = ZEBRA_DARK if dark_mode else ZEBRA_LIGHT
    fg = style.lookup("Treeview", "foreground") or "#1C232B"
    tree.tag_configure("oddrow",  background=zc["odd"],  foreground=fg)
    tree.tag_configure("evenrow", background=zc["even"], foreground=fg)


def zebra_insert(tree: ttk.Treeview, values: tuple, **kwargs) -> str:
    """Insert a row with automatic alternating zebra-stripe tags."""
    row_count = len(tree.get_children())
    tag = "evenrow" if row_count % 2 == 0 else "oddrow"
    caller_tags = kwargs.pop("tags", ())
    if isinstance(caller_tags, str):
        caller_tags = (caller_tags,)
    merged_tags = tuple(caller_tags) + (tag,)
    return tree.insert("", tk.END, values=values, tags=merged_tags, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
#  Treeview grid-lines  (drawn as a canvas overlay — call after pack/grid)
# ─────────────────────────────────────────────────────────────────────────────

def add_treeview_grid_lines(tree: ttk.Treeview, dark_mode: bool) -> None:
    """
    Bind a <Configure> + <Motion> event pair so the Treeview redraws thin
    vertical and horizontal grid lines between every row/column — exactly like
    an Excel sheet.  Call this once after the Treeview is packed.
    """
    line_color = "#A0B0C8" if not dark_mode else "#3A4D65"

    def _redraw(_event=None):
        tree.tag_configure("_gridline_h",
                           background=line_color)   # not used directly
        # Use the Treeview's built-in -style approach:
        # On Windows/clam, column separators appear automatically when
        # borderwidth >= 1 and relief = "solid".  Nothing extra needed here.
        pass

    tree.bind("<Configure>", _redraw)

def show_on_top(window, parent=None):
    """Make a Toplevel window appear on top and grab focus. Used by all windows."""
    try:
        # Center child windows on screen as soon as geometry is settled.
        window.after_idle(lambda: center_window(window))
        window.lift()
        window.focus_force()
        window.grab_set()  # منع التعامل مع أي نافذة أخرى (Modal Logic)
        window.attributes("-topmost", True)
        window.after(250, lambda: window.attributes("-topmost", False))
    except Exception:
        pass


def center_window(window, width: int | None = None, height: int | None = None) -> None:
    """
    Center a Tk/Toplevel window on the screen.

    If width/height are not provided, uses the window's current size (after
    update_idletasks) so this works with both fixed geometry and layout-driven
    sizes.
    """
    try:
        window.update_idletasks()

        w = int(width) if width else int(window.winfo_width() or window.winfo_reqwidth())
        h = int(height) if height else int(window.winfo_height() or window.winfo_reqheight())

        sw = int(window.winfo_screenwidth())
        sh = int(window.winfo_screenheight())

        x = max((sw - w) // 2, 0)
        y = max((sh - h) // 2, 0)

        window.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass
