"""Shared UI tokens and style helpers."""

from tkinter import ttk

FONT_FAMILY = "Segoe UI"
BASE_FONT = (FONT_FAMILY, 10)
BOLD_FONT = (FONT_FAMILY, 10, "bold")

LIGHT_THEME = {
    "bg": "#F4F6F9",
    "fg": "#1C232B",
    "frame_bg": "#F4F6F9",
    "entry_bg": "#FFFFFF",
    "button_bg": "#0A66CC",
    "button_fg": "#FFFFFF",
    "button_active_bg": "#084F9E",
    "accent_bg": "#0A66CC",
    "accent_active_bg": "#084F9E",
    "header_bg": "#E8EDF3",
    "tree_bg": "#FFFFFF",
    "tree_fg": "#1C232B",
    "tree_selected_bg": "#0A66CC",
}

DARK_THEME = {
    "bg": "#1A1F27",
    "fg": "#F4F7FA",
    "frame_bg": "#1A1F27",
    "entry_bg": "#2A3340",
    "button_bg": "#2E8BFF",
    "button_fg": "#FFFFFF",
    "button_active_bg": "#1D6FD6",
    "accent_bg": "#2E8BFF",
    "accent_active_bg": "#1D6FD6",
    "header_bg": "#27313D",
    "tree_bg": "#1F2833",
    "tree_fg": "#F4F7FA",
    "tree_selected_bg": "#2E8BFF",
}


def get_theme_tokens(dark_mode: bool) -> dict:
    return DARK_THEME.copy() if dark_mode else LIGHT_THEME.copy()


def configure_sub_button_style(style: ttk.Style, style_name: str, palette: dict):
    style.configure(
        style_name,
        font=BOLD_FONT,
        padding=6,
        background=palette["button_bg"],
        foreground=palette["button_fg"],
    )
    style.map(
        style_name,
        background=[("active", palette["button_active_bg"])],
    )

