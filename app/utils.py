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


def validate_color_code_input(code: str) -> tuple[bool, str]:
    """التحقق من صحة كود اللون - استدعاء المدقق المركزي"""
    from app.validators import Validators
    return Validators.validate_color_code(code)


def validate_recipe_code_input(code: str) -> tuple[bool, str]:
    """التحقق من صحة كود الوصفة - استدعاء المدقق المركزي"""
    from app.validators import Validators
    return Validators.validate_recipe_code(code)


def format_currency(amount: float) -> str:
    """تنسيق العملة"""
    return f"€{amount:.2f}"


def format_percentage(value: float) -> str:
    """تنسيق النسبة المئوية"""
    return f"{value:.2f}%"


def get_current_timestamp() -> str:
    """الحصول على الطابع الزمني الحالي"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate_age_from_timestamp(timestamp: str) -> str:
    """حساب العمر من الطابع الزمني"""
    try:
        created_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        delta = datetime.now() - created_date

        if delta.days > 365:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''}"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''}"
        elif delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''}"
        else:
            hours = delta.seconds // 3600
            if hours > 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                minutes = delta.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''}"
    except:
        return "Unknown"
