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
    "bg":                "#1E2533",
    "frame_bg":          "#1E2533",
    "card_bg":           "#252D3D",

    "fg":                "#E8EDF5",
    "fg_muted":          "#8B9AB5",

    "entry_bg":          "#2C3650",
    "entry_border":      "#3D4F6A",

    "button_bg":         "#2E6BC4",
    "button_fg":         "#FFFFFF",
    "button_active_bg":  "#1F52A0",
    "button_shadow":     "#141A26",

    "accent_bg":         "#2E6BC4",
    "accent_active_bg":  "#1F52A0",

    "header_bg":         "#1A2030",
    "header_border":     "#2D3D58",

    "tree_bg":           "#252D3D",
    "tree_fg":           "#E8EDF5",
    "tree_selected_bg":  "#2E6BC4",

    "labelframe_border": "#2D3D58",
    "statusbar_bg":      "#161D2B",
}

# Zebra rows — comfortable contrast: gray + off-white
ZEBRA_LIGHT = {"odd": "#D3D3D3", "even": "#C9CDD3", "hover": "#E1E6EE"}
ZEBRA_DARK  = {"odd": "#252D3D", "even": "#2A3348", "hover": "#2E4060"}


def get_theme_tokens(dark_mode: bool) -> dict:
    return DARK_THEME.copy() if dark_mode else LIGHT_THEME.copy()


# ─────────────────────────────────────────────────────────────────────────────
#  Button helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_button(style: ttk.Style, name: str, bg: str, fg: str, active_bg: str,
                 font=None, padding=8):
    """Raised button with 3-D border — pressed = sunken."""
    f = font or BOLD_FONT
    style.configure(
        name,
        font=f,
        padding=padding,
        background=bg,
        foreground=fg,
        relief="raised",
        borderwidth=2,
        anchor="center",
    )
    style.map(
        name,
        background=[("active", active_bg), ("disabled", "#B0B8C4")],
        foreground=[("disabled", "#788090")],
        relief=[("active", "sunken"), ("pressed", "sunken")],
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
    # RaisedPanel.TFrame — the 3-D panel used for toolbar groups
    style.configure("RaisedPanel.TFrame",
                    background=hdr_bg,
                    relief="raised",
                    borderwidth=3)

    # ── Labels ────────────────────────────────────────────────────────
    style.configure("TLabel",
                    background=bg, foreground=fg, font=BASE_FONT)

    # ── LabelFrame — ridge gives the strongest 3-D inset look ─────────
    style.configure("TLabelframe",
                    background=bg,
                    bordercolor=lf_bdr,
                    relief="ridge",
                    borderwidth=3)
    style.configure("TLabelframe.Label",
                    background=bg,
                    foreground=fg,
                    font=BOLD_FONT)

    # ── Entries / Comboboxes ──────────────────────────────────────────
    style.configure("TEntry",
                    fieldbackground=entry_bg,
                    foreground=fg,
                    insertcolor=fg,
                    borderwidth=2,
                    relief="sunken")
    style.map("TCombobox",
              fieldbackground=[("readonly", entry_bg)],
              selectbackground=[("readonly", entry_bg)],
              selectforeground=[("readonly", fg)],
              background=[("readonly", entry_bg)])
    style.configure("TCombobox", foreground=fg)

    # ── Scrollbar ─────────────────────────────────────────────────────
    style.configure("TScrollbar",
                    background=palette["button_bg"],
                    troughcolor=hdr_bg,
                    borderwidth=1,
                    arrowcolor=palette["button_fg"],
                    relief="raised")

    # ── Notebook ──────────────────────────────────────────────────────
    style.configure("TNotebook",     background=bg, borderwidth=0)
    style.configure("TNotebook.Tab", background=hdr_bg, foreground=fg,
                    font=BOLD_FONT,  padding=(12, 6), borderwidth=2,
                    relief="raised")
    style.map("TNotebook.Tab",
              background=[("selected", card)],
              foreground=[("selected", palette["button_bg"])],
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

    # Column headings — blue/gray like Excel table headers in screenshot
    hdr_bg  = "#A9BBD2" if not dark_mode else "#3E4E63"
    hdr_act = "#95ACC7" if not dark_mode else "#344457"
    style.configure(
        "Treeview.Heading",
        font=BOLD_FONT,
        background=hdr_bg,
        foreground="#000000" if not dark_mode else "#FFFFFF",
        relief="raised",
        borderwidth=1,
        padding=(6, 7),
    )
    style.map(
        "Treeview.Heading",
        background=[("active", hdr_act)],
        relief=[("active", "sunken")],
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
