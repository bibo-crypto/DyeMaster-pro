"""
مدقق البيانات (Validators) للتطبيق
"""
import re
from datetime import datetime
from typing import Tuple, Optional, Union


class Validators:
    """فئة تحتوي على جميع دوال التحقق من صحة البيانات"""

    @staticmethod
    def validate_color_code(code: str, allow_empty: bool = False) -> Tuple[bool, str]:
        """
        التحقق من صحة كود اللون

        Args:
            code: كود اللون المدخل (5 أرقام)
            allow_empty: السماح بالقيم الفارغة

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ)
        """
        if not code and allow_empty:
            return True, ""

        if not code:
            return False, "Color code cannot be empty"

        # إزالة المسافات
        code = code.strip()

        # التحقق من الطول (5 أرقام)
        if len(code) != 5:
            return False, "Color code must be exactly 5 digits"

        # التحقق من أن جميع الأحرف أرقام
        if not code.isdigit():
            return False, "Color code must contain only numbers"

        return True, ""

    @staticmethod
    def validate_recipe_code(code: str, allow_empty: bool = False) -> Tuple[bool, str]:
        """
        التحقق من صحة كود الوصفة

        Args:
            code: كود الوصفة المدخل
            allow_empty: السماح بالقيم الفارغة

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ)
        """
        if not code and allow_empty:
            return True, ""

        if not code:
            return False, "Recipe code cannot be empty"

        # التحقق من الطول
        if len(code) > 20:
            return False, "Recipe code cannot exceed 20 characters"

        # التحقق من التنسيق (6 أرقام)
        if not code.isdigit():
            return False, "Recipe code must contain only numbers"

        if len(code) != 6:
            return False, "Recipe code must be 6 digits"

        return True, ""

    @staticmethod
    def validate_name(name: str, field_name: str = "Name", max_length: int = 100,
                      allow_empty: bool = False) -> Tuple[bool, str]:
        """
        التحقق من صحة الاسم

        Args:
            name: الاسم المدخل
            field_name: اسم الحقل (للرسائل)
            max_length: الحد الأقصى للطول
            allow_empty: السماح بالقيم الفارغة

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ)
        """
        if not name and allow_empty:
            return True, ""

        if not name:
            return False, f"{field_name} cannot be empty"

        # التحقق من الطول
        if len(name) > max_length:
            return False, f"{field_name} cannot exceed {max_length} characters"

        # التحقق من الأحرف المسموحة
        if not re.match(r'^[a-zA-Z0-9\s\-_\.\,\'\"]+$', name):
            return False, f"{field_name} contains invalid characters"

        return True, ""

    @staticmethod
    def validate_dye_type(dye_type: str, allowed_types: list) -> Tuple[bool, str]:
        """
        التحقق من صحة نوع الصباغة

        Args:
            dye_type: نوع الصباغة المدخل
            allowed_types: القائمة المسموحة

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ)
        """
        if not dye_type:
            return False, "Dye type cannot be empty"

        if dye_type not in allowed_types:
            return False, f"Dye type must be one of: {', '.join(allowed_types)}"

        return True, ""

    @staticmethod
    def validate_supplier(supplier: str, allow_empty: bool = True) -> Tuple[bool, str]:
        """
        التحقق من صحة المورد

        Args:
            supplier: اسم المورد
            allow_empty: السماح بالقيم الفارغة

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ)
        """
        if not supplier and allow_empty:
            return True, ""

        if supplier:
            if len(supplier) > 100:
                return False, "Supplier name cannot exceed 100 characters"

            # التحقق من الأحرف المسموحة
            if not re.match(r'^[a-zA-Z0-9\s\-_\.\,\&\@\(\)]+$', supplier):
                return False, "Supplier name contains invalid characters"

        return True, ""

    @staticmethod
    def validate_price(price: Union[str, float], field_name: str = "Price",
                       allow_zero: bool = True, allow_negative: bool = False) -> Tuple[bool, str, Optional[float]]:
        """
        التحقق من صحة السعر

        Args:
            price: السعر المدخل
            field_name: اسم الحقل (للرسائل)
            allow_zero: السماح بالقيمة صفر
            allow_negative: السماح بالقيم السالبة

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ, القيمة الرقمية)
        """
        if price is None:
            return False, f"{field_name} cannot be empty", None

        if isinstance(price, str):
            price_str = price.strip()
            if not price_str:
                return False, f"{field_name} cannot be empty", None

            try:
                # محاولة التحويل إلى float
                price_value = float(price_str)
            except ValueError:
                return False, f"{field_name} must be a valid number", None
        else:
            price_value = float(price)

        # التحقق من القيم السالبة
        if not allow_negative and price_value < 0:
            return False, f"{field_name} cannot be negative", None

        # التحقق من القيمة صفر
        if not allow_zero and price_value == 0:
            return False, f"{field_name} cannot be zero", None

        # التحقق من الدقة
        if price_value > 1000000:  # مليون
            return False, f"{field_name} is too high", None

        return True, "", price_value

    @staticmethod
    def validate_percentage(percentage: Union[str, float], field_name: str = "Percentage",
                            min_value: float = 0, max_value: float = 100,
                            allow_zero: bool = False) -> Tuple[bool, str, Optional[float]]:
        """
        التحقق من صحة النسبة المئوية

        Args:
            percentage: النسبة المئوية المدخلة
            field_name: اسم الحقل (للرسائل)
            min_value: الحد الأدنى
            max_value: الحد الأقصى
            allow_zero: السماح بالقيمة صفر

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ, القيمة الرقمية)
        """
        if percentage is None:
            return False, f"{field_name} cannot be empty", None

        if isinstance(percentage, str):
            percentage_str = percentage.strip()
            if not percentage_str:
                return False, f"{field_name} cannot be empty", None

            try:
                # محاولة التحويل إلى float
                percentage_value = float(percentage_str)
            except ValueError:
                return False, f"{field_name} must be a valid number", None
        else:
            percentage_value = float(percentage)

        # التحقق من القيم السالبة
        if percentage_value < 0:
            return False, f"{field_name} cannot be negative", None

        # التحقق من القيمة صفر
        if not allow_zero and percentage_value == 0:
            return False, f"{field_name} cannot be zero", None

        # التحقق من الحدود
        if percentage_value < min_value:
            return False, f"{field_name} must be at least {min_value}", None

        if percentage_value > max_value:
            return False, f"{field_name} cannot exceed {max_value}", None

        return True, "", percentage_value

    @staticmethod
    def validate_timestamp(timestamp: str) -> Tuple[bool, str]:
        """
        التحقق من صحة الطابع الزمني

        Args:
            timestamp: الطابع الزمني

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ)
        """
        if not timestamp:
            return False, "Timestamp cannot be empty"

        try:
            # محاولة تحليل الطابع الزمني
            datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            return True, ""
        except ValueError:
            try:
                datetime.strptime(timestamp, "%Y-%m-%d")
                return True, ""
            except ValueError:
                return False, "Timestamp must be in format: YYYY-MM-DD HH:MM:SS or YYYY-MM-DD"

    @staticmethod
    def validate_email(email: str, allow_empty: bool = True) -> Tuple[bool, str]:
        """
        التحقق من صحة البريد الإلكتروني

        Args:
            email: البريد الإلكتروني
            allow_empty: السماح بالقيم الفارغة

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ)
        """
        if not email and allow_empty:
            return True, ""

        if email:
            # نمط التحقق من البريد الإلكتروني
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                return False, "Invalid email format"

            if len(email) > 100:
                return False, "Email cannot exceed 100 characters"

        return True, ""

    @staticmethod
    def validate_phone(phone: str, allow_empty: bool = True) -> Tuple[bool, str]:
        """التحقق من صحة رقم الهاتف"""
        if not phone and allow_empty:
            return True, ""
        if phone:
            cleaned = re.sub(r'[\s\-\(\)]+', '', phone)
            if not cleaned.isdigit():
                return False, "Phone number must contain only digits"
            if len(cleaned) < 8 or len(cleaned) > 15:
                return False, "Phone number must be between 8 and 15 digits"
        return True, ""
    @staticmethod
    def validate_quantity(quantity: Union[str, float], unit: str = "",
                          allow_zero: bool = False) -> Tuple[bool, str, Optional[float]]:
        """
        التحقق من صحة الكمية

        Args:
            quantity: الكمية المدخلة
            unit: وحدة القياس
            allow_zero: السماح بالقيمة صفر

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ, القيمة الرقمية)
        """
        return Validators.validate_price(quantity, f"Quantity ({unit})" if unit else "Quantity",
                                         allow_zero=allow_zero, allow_negative=False)

    @staticmethod
    def validate_color_object(color_data: dict, allowed_dye_types: list = None) -> Tuple[bool, str, Optional[dict]]:
        """
        التحقق من صحة كائن اللون الكامل

        Args:
            color_data: بيانات اللون
            allowed_dye_types: قائمة أنواع الصباغة المسموحة (اختياري)

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ, البيانات المنظفة)
        """
        # التحقق من الحقول المطلوبة
        required_fields = ['code', 'name', 'dye_type']
        for field in required_fields:
            if field not in color_data or not color_data[field]:
                return False, f"Missing required field: {field}", None

        # تنظيف البيانات
        cleaned_data = color_data.copy()

        # التحقق من كود اللون
        is_valid, message = Validators.validate_color_code(cleaned_data['code'])
        if not is_valid:
            return False, f"Color code: {message}", None

        # التحقق من اسم اللون
        is_valid, message = Validators.validate_name(cleaned_data['name'], "Color name", max_length=150)
        if not is_valid:
            return False, f"Color name: {message}", None

        # ✅ التحقق من نوع الصباغة إذا تم توفير القائمة
        if allowed_dye_types:
            is_valid, message = Validators.validate_dye_type(cleaned_data['dye_type'], allowed_dye_types)
            if not is_valid:
                return False, f"Dye type: {message}", None

        # التحقق من المورد
        is_valid, message = Validators.validate_supplier(cleaned_data.get('supplier', ''))
        if not is_valid:
            return False, f"Supplier: {message}", None

        # التحقق من السعر
        is_valid, message, price = Validators.validate_price(
            cleaned_data.get('price_kg', 0), "Price per kg", allow_zero=True
        )
        if not is_valid:
            return False, f"Price: {message}", None
        cleaned_data['price_kg'] = price

        # التحقق من نسبة RESA
        is_valid, message, resa = Validators.validate_percentage(
            cleaned_data.get('resa_percent', 100), "RESA percentage", min_value=0, max_value=1000, allow_zero=True
        )
        if not is_valid:
            return False, f"RESA: {message}", None
        cleaned_data['resa_percent'] = resa

        # التحقق من التواريخ
        for date_field in ['created_at', 'updated_at']:
            if date_field in cleaned_data and cleaned_data[date_field]:
                is_valid, message = Validators.validate_timestamp(cleaned_data[date_field])
                if not is_valid:
                    # إذا كان التاريخ غير صالح، استخدم التاريخ الحالي
                    cleaned_data[date_field] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return True, "Color data is valid", cleaned_data

    @staticmethod
    def validate_recipe_object(recipe_data: dict) -> Tuple[bool, str, Optional[dict]]:
        """
        التحقق من صحة كائن الوصفة الكامل

        Args:
            recipe_data: بيانات الوصفة

        Returns:
            tuple: (صالح/غير صالح, رسالة الخطأ, البيانات المنظفة)
        """
        # التحقق من الحقول المطلوبة
        if 'name' not in recipe_data or not recipe_data['name']:
            return False, "Missing required field: name", None

        # تنظيف البيانات
        cleaned_data = recipe_data.copy()

        # التحقق من كود الوصفة (إذا كان موجوداً)
        if 'recipe_code' in cleaned_data and cleaned_data['recipe_code']:
            is_valid, message = Validators.validate_recipe_code(cleaned_data['recipe_code'])
            if not is_valid:
                return False, f"Recipe code: {message}", None

        # التحقق من اسم الوصفة
        is_valid, message = Validators.validate_name(cleaned_data['name'], "Recipe name", max_length=200)
        if not is_valid:
            return False, f"Recipe name: {message}", None

        # التحقق من التواريخ
        for date_field in ['created_at']:
            if date_field in cleaned_data and cleaned_data[date_field]:
                is_valid, message = Validators.validate_timestamp(cleaned_data[date_field])
                if not is_valid:
                    # إذا كان التاريخ غير صالح، استخدم التاريخ الحالي
                    cleaned_data[date_field] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # التحقق من الألوان (إذا كانت موجودة)
        if 'colors' in cleaned_data:
            if not isinstance(cleaned_data['colors'], list):
                return False, "Colors must be a list", None

            if not cleaned_data['colors']:
                return False, "Recipe must contain at least one color", None

            # التحقق من كل لون في الوصفة
            total_percentage = 0
            for i, color in enumerate(cleaned_data['colors']):
                if not isinstance(color, dict):
                    return False, f"Color at index {i} must be a dictionary", None

                # التحقق من وجود الحقول المطلوبة
                if 'color_code' not in color:
                    return False, f"Color at index {i} missing 'color_code'", None

                if 'percentage' not in color:
                    return False, f"Color at index {i} missing 'percentage'", None

                # التحقق من النسبة المئوية
                is_valid, message, percentage = Validators.validate_percentage(
                    color['percentage'], f"Percentage for color {i + 1}",
                    min_value=0.01, max_value=100, allow_zero=False
                )
                if not is_valid:
                    return False, message, None

                total_percentage += percentage

            # التحقق من النسبة الكلية
            if total_percentage > 100:
                return False, f"Total percentage ({total_percentage:.2f}%) cannot exceed 100%", None

        return True, "Recipe data is valid", cleaned_data

