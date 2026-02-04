"""
دوال مساعدة للتعامل مع الألوان
"""
import sqlite3
import re
from typing import Optional


def get_color_types_from_db(db_file: str) -> list:
    """الحصول على أنواع الصبغة من قاعدة البيانات"""
    try:
        # استخدام context manager لضمان إغلاق الاتصال
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            # الحصول على أنواع الصبغة المميزة من جدول colors
            cursor.execute("SELECT DISTINCT dye_type FROM colors WHERE dye_type IS NOT NULL AND dye_type != ''")
            db_types = [row[0] for row in cursor.fetchall()]

        # أنواع افتراضية إذا لم يكن هناك أنواع في قاعدة البيانات
        default_types = ['Acid', 'Direct', 'Reactive', 'Disperse', 'Pigment', 'Vat', 'Other']

        # دمج الأنواع من قاعدة البيانات مع الأنواع الافتراضية
        all_types = list(set(db_types + default_types))
        all_types.sort()

        return all_types

    except Exception as e:
        print(f"Error getting color types: {e}")
        return ['Acid', 'Direct', 'Reactive', 'Disperse', 'Pigment', 'Vat', 'Other']


def fix_color_code(code: str) -> str:
    """إصلاح كود اللون"""
    if not code:
        return code

    # تنظيف الكود من الفراغات
    code = code.strip().upper()

    # إزالة أي أحرف غير مرغوب فيها
    code = re.sub(r'[^\w\-]', '', code)

    return code


def validate_color_data(color_data: dict) -> tuple[bool, str]:
    """التحقق من صحة بيانات اللون"""
    try:
        # التحقق من الاسم
        if not color_data.get('name', '').strip():
            return False, "Color name is required"

        # التحقق من السعر
        try:
            price = float(color_data.get('price_kg', 0))
            if price < 0:
                return False, "Price cannot be negative"
        except ValueError:
            return False, "Invalid price value"

        # التحقق من نسبة الصباغة
        try:
            resa = float(color_data.get('resa_percent', 0))
            if resa < 0 or resa > 100:
                return False, "Resa percentage must be between 0 and 100"
        except ValueError:
            return False, "Invalid resa percentage value"

        return True, "Valid"

    except Exception as e:
        return False, f"Validation error: {str(e)}"