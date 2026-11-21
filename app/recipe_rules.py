"""Business rules shared by Recipe Editor and database persistence."""

from typing import Dict, Iterable, Tuple


def _family(dye_type: str) -> str:
    value = str(dye_type or "").upper()
    if "INDANTHREN" in value:
        return "INDANTHREN"
    if "CALDI" in value:
        return "REATTIVI_CALDI"
    if "FREDDI" in value:
        return "REATTIVI_FREDDI"
    return "OTHER_REATTIVI"


def validate_color_compatibility(colors: Iterable[Dict]) -> Tuple[bool, str]:
    """Validate the existing recipe compatibility rules for all colors."""
    items = list(colors or [])
    families = {_family(item.get("dye_type", "")) for item in items}
    if "INDANTHREN" in families and any(f != "INDANTHREN" for f in families):
        return False, "Cannot mix INDANTHREN colors with REATTIVI colors in the same recipe."
    if "REATTIVI_CALDI" in families and "REATTIVI_FREDDI" in families:
        return False, "Cannot mix REATTIVI CALDI with REATTIVI FREDDI in the same recipe."
    return True, ""


def validate_recipe_colors(colors: Iterable[Dict]) -> Tuple[bool, str]:
    """Validate duplicate, percentage, and compatibility rules before persistence."""
    items = list(colors or [])
    if not items:
        return False, "Recipe must contain at least one color"
    seen = set()
    total = 0.0
    for item in items:
        code = str(item.get("code", "")).strip()
        if not code:
            return False, "Color code cannot be empty"
        if code in seen:
            return False, f"Color '{code}' is duplicated in the recipe"
        seen.add(code)
        try:
            percentage = float(item.get("percentage", 0))
        except (TypeError, ValueError):
            return False, f"Invalid percentage for color '{code}'"
        if percentage <= 0 or percentage > 100:
            return False, f"Color percentage for '{code}' must be between 0.01 and 100"
        total += percentage
    if total > 100:
        return False, f"Total percentage ({total:.2f}%) cannot exceed 100%"
    return validate_color_compatibility(items)
