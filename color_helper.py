"""
دوال مساعدة للتعامل مع الألوان
"""
def fix_color_code(code: str) -> str:
    """إصلاح كود اللون — متوافق مع clean_color_code في utils.py (lowercase)"""
    from app.utils import clean_color_code
    return clean_color_code(code)
