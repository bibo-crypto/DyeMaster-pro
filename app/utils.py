"""
دوال مساعدة
"""
import math
from typing import Any
from datetime import datetime


def _is_missing(value: Any) -> bool:
    """Return True for None/NaN-like values without requiring pandas."""
    if value is None:
        return True
    if isinstance(value, float):
        return math.isnan(value)
    return False


def clean_color_code(code: Any) -> str:
    """
    تنظيف كود اللون
    """
    if _is_missing(code):
        return ""

    code_str = str(code).strip()

    # إزالة .0 من النهاية
    if '.' in code_str:
        parts = code_str.split('.')
        if len(parts) == 2:
            # إذا كان الجزء العشري أصفار فقط
            if parts[1].replace('0', '') == '':
                code_str = parts[0]

    code_str = code_str.lower()

    return code_str


def clean_recipe_code(code: Any) -> str:
    """تنظيف كود الريتشتة"""
    import re
    if _is_missing(code):
        return ""

    # First, keep only digits from the string
    code_str = re.sub(r'\D', '', str(code))

    # Then, pad with leading zeros to ensure it's 6 digits long
    return code_str.zfill(6)


def parse_percentage_input(value: Any, default: float = 100.0) -> float:
    """Parse RESA percentage using English digits only (0-9 and optional dot)."""
    if _is_missing(value):
        return default

    value_str = str(value).strip()
    if not value_str:
        return default

    # Allow optional trailing percent symbols, but enforce English numeric format.
    value_str = value_str.replace('%', '').strip()
    if not value_str:
        return default

    import re
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", value_str):
        raise ValueError(
            "RESA must use English digits only (0-9). Use '.' for decimals, e.g. 85 or 85.5"
        )
    return float(value_str)

def parse_number_input(value: Any, default: float = 0.0) -> float:
    """Parse numeric user input for price/amount fields."""
    if _is_missing(value):
        return default

    value_str = str(value).strip()
    if not value_str:
        return default

    # Strip common currency prefixes/symbols.
    normalized = (
        value_str
        .replace("EUR", "")
        .replace("€", "")
        .replace("€", "")
        .strip()
    )

    # Normalize Arabic/Persian digits safely using unicode escapes.
    arabic_digits = "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669"
    persian_digits = "\u06F0\u06F1\u06F2\u06F3\u06F4\u06F5\u06F6\u06F7\u06F8\u06F9"
    digit_map = {ord(ch): str(i) for i, ch in enumerate(arabic_digits)}
    digit_map.update({ord(ch): str(i) for i, ch in enumerate(persian_digits)})
    normalized = normalized.translate(digit_map)

    normalized = (
        normalized
        .replace('\u066B', '.')
        .replace(',', '.')
        .replace('\u060C', '.')
        .replace('\u066C', '')
        .replace(' ', '')
    )
    # Remove any remaining non-numeric symbols (currency artifacts, etc.).
    import re
    normalized = re.sub(r"[^0-9.\-]", "", normalized)
    try:
        return float(normalized)
    except ValueError:
        raise ValueError(f"Invalid numeric value: {value}")


def validate_color_code_input(code: str) -> tuple[bool, str]:
    """التحقق من صحة كود اللون - استدعاء المدقق المركزي"""
    from app.validators import Validators
    return Validators.validate_color_code(code)


def validate_recipe_code_input(code: str) -> tuple[bool, str]:
    """التحقق من صحة كود الوصفة - استدعاء المدقق المركزي"""
    from app.validators import Validators
    return Validators.validate_recipe_code(code)


def _format_number_no_trailing_zeros(value: float, decimals: int = 2) -> str:
    """Format a number without trailing zeros after decimal point."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "0"

    formatted = f"{f:.{decimals}f}".rstrip('0').rstrip('.')
    return formatted if formatted != "" else "0"


def format_currency(amount: float) -> str:
    """تنسيق العملة"""
    try:
        return f"€{float(amount):.2f}"
    except (TypeError, ValueError):
        return "€0.00"


def format_percentage(value: float) -> str:
    """تنسيق النسبة المئوية"""
    return f"{_format_number_no_trailing_zeros(value)}%"


def get_current_timestamp() -> str:
    """الحصول على الطابع الزمني الحالي"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")




def normalize_dye_type_label(dye_type: Any) -> str:
    """
    Normalize dye-type text and map it to a canonical configured label when possible.
    Falls back to trimmed original text if no canonical match is found.
    """
    raw = str(dye_type or "").strip()
    normalized = " ".join(raw.lower().split())
    if not normalized:
        return ""

    aliases = {
        "reattivi oltre": "reattivi oltri",
        "reattivi altri": "reattivi oltri",
    }
    normalized = aliases.get(normalized, normalized)

    try:
        from app.config import DYE_TYPES
        canonical_map = {" ".join(item.strip().lower().split()): item for item in DYE_TYPES}
        return canonical_map.get(normalized, raw)
    except Exception:
        return raw
