"""
Ù…Ø¯Ù‚Ù‚ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª (Validators) Ù„Ù„ØªØ·Ø¨ÙŠÙ‚
"""
import re
from datetime import datetime
from typing import Tuple, Optional, Union


class Validators:
    """ÙØ¦Ø© ØªØ­ØªÙˆÙŠ Ø¹Ù„Ù‰ Ø¬Ù…ÙŠØ¹ Ø¯ÙˆØ§Ù„ Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª"""

    @staticmethod
    def validate_color_code(code: str, allow_empty: bool = False) -> Tuple[bool, str]:
        """
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© ÙƒÙˆØ¯ Ø§Ù„Ù„ÙˆÙ†

        Args:
            code: ÙƒÙˆØ¯ Ø§Ù„Ù„ÙˆÙ† Ø§Ù„Ù…Ø¯Ø®Ù„ (5 Ø£Ø±Ù‚Ø§Ù…)
            allow_empty: Ø§Ù„Ø³Ù…Ø§Ø­ Ø¨Ø§Ù„Ù‚ÙŠÙ… Ø§Ù„ÙØ§Ø±ØºØ©

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£)
        """
        if not code and allow_empty:
            return True, ""

        if not code:
            return False, "Color code cannot be empty"

        # Ø¥Ø²Ø§Ù„Ø© Ø§Ù„Ù…Ø³Ø§ÙØ§Øª
        code = code.strip()

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø·ÙˆÙ„ (5 Ø£Ø±Ù‚Ø§Ù…)
        if len(code) != 5:
            return False, "Color code must be exactly 5 digits"

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø£Ù† Ø¬Ù…ÙŠØ¹ Ø§Ù„Ø£Ø­Ø±Ù Ø£Ø±Ù‚Ø§Ù…
        if not code.isdigit():
            return False, "Color code must contain only numbers"

        return True, ""

    @staticmethod
    def validate_recipe_code(code: str, allow_empty: bool = False) -> Tuple[bool, str]:
        """
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© ÙƒÙˆØ¯ Ø§Ù„ÙˆØµÙØ©

        Args:
            code: ÙƒÙˆØ¯ Ø§Ù„ÙˆØµÙØ© Ø§Ù„Ù…Ø¯Ø®Ù„
            allow_empty: Ø§Ù„Ø³Ù…Ø§Ø­ Ø¨Ø§Ù„Ù‚ÙŠÙ… Ø§Ù„ÙØ§Ø±ØºØ©

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£)
        """
        if not code and allow_empty:
            return True, ""

        if not code:
            return False, "Recipe code cannot be empty"

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø·ÙˆÙ„
        if len(code) > 20:
            return False, "Recipe code cannot exceed 20 characters"

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„ØªÙ†Ø³ÙŠÙ‚ (6 Ø£Ø±Ù‚Ø§Ù…)
        if not code.isdigit():
            return False, "Recipe code must contain only numbers"

        if len(code) != 6:
            return False, "Recipe code must be 6 digits"

        return True, ""

    @staticmethod
    def validate_name(name: str, field_name: str = "Name", max_length: int = 100,
                      allow_empty: bool = False) -> Tuple[bool, str]:
        """
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ø§Ù„Ø§Ø³Ù…

        Args:
            name: Ø§Ù„Ø§Ø³Ù… Ø§Ù„Ù…Ø¯Ø®Ù„
            field_name: Ø§Ø³Ù… Ø§Ù„Ø­Ù‚Ù„ (Ù„Ù„Ø±Ø³Ø§Ø¦Ù„)
            max_length: Ø§Ù„Ø­Ø¯ Ø§Ù„Ø£Ù‚ØµÙ‰ Ù„Ù„Ø·ÙˆÙ„
            allow_empty: Ø§Ù„Ø³Ù…Ø§Ø­ Ø¨Ø§Ù„Ù‚ÙŠÙ… Ø§Ù„ÙØ§Ø±ØºØ©

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£)
        """
        if not name and allow_empty:
            return True, ""

        if not name:
            return False, f"{field_name} cannot be empty"

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø·ÙˆÙ„
        if len(name) > max_length:
            return False, f"{field_name} cannot exceed {max_length} characters"

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø£Ø­Ø±Ù Ø§Ù„Ù…Ø³Ù…ÙˆØ­Ø©
        if not re.match(r'^[a-zA-Z0-9\s\-_\.\,\'\"]+$', name):
            return False, f"{field_name} contains invalid characters"

        return True, ""

    @staticmethod
    def validate_dye_type(dye_type: str, allowed_types: list) -> Tuple[bool, str]:
        """
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ù†ÙˆØ¹ Ø§Ù„ØµØ¨Ø§ØºØ©

        Args:
            dye_type: Ù†ÙˆØ¹ Ø§Ù„ØµØ¨Ø§ØºØ© Ø§Ù„Ù…Ø¯Ø®Ù„
            allowed_types: Ø§Ù„Ù‚Ø§Ø¦Ù…Ø© Ø§Ù„Ù…Ø³Ù…ÙˆØ­Ø©

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£)
        """
        if not dye_type:
            return False, "Dye type cannot be empty"

        if dye_type not in allowed_types:
            return False, f"Dye type must be one of: {', '.join(allowed_types)}"

        return True, ""

    @staticmethod
    def validate_supplier(supplier: str, allow_empty: bool = True) -> Tuple[bool, str]:
        """
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ø§Ù„Ù…ÙˆØ±Ø¯

        Args:
            supplier: Ø§Ø³Ù… Ø§Ù„Ù…ÙˆØ±Ø¯
            allow_empty: Ø§Ù„Ø³Ù…Ø§Ø­ Ø¨Ø§Ù„Ù‚ÙŠÙ… Ø§Ù„ÙØ§Ø±ØºØ©

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£)
        """
        if not supplier and allow_empty:
            return True, ""

        if supplier:
            if len(supplier) > 100:
                return False, "Supplier name cannot exceed 100 characters"

            # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø£Ø­Ø±Ù Ø§Ù„Ù…Ø³Ù…ÙˆØ­Ø©
            if not re.match(r'^[a-zA-Z0-9\s\-_\.\,\&\@\(\)]+$', supplier):
                return False, "Supplier name contains invalid characters"

        return True, ""

    @staticmethod
    def validate_price(price: Union[str, float], field_name: str = "Price",
                       allow_zero: bool = True, allow_negative: bool = False) -> Tuple[bool, str, Optional[float]]:
        """
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ø§Ù„Ø³Ø¹Ø±

        Args:
            price: Ø§Ù„Ø³Ø¹Ø± Ø§Ù„Ù…Ø¯Ø®Ù„
            field_name: Ø§Ø³Ù… Ø§Ù„Ø­Ù‚Ù„ (Ù„Ù„Ø±Ø³Ø§Ø¦Ù„)
            allow_zero: Ø§Ù„Ø³Ù…Ø§Ø­ Ø¨Ø§Ù„Ù‚ÙŠÙ…Ø© ØµÙØ±
            allow_negative: Ø§Ù„Ø³Ù…Ø§Ø­ Ø¨Ø§Ù„Ù‚ÙŠÙ… Ø§Ù„Ø³Ø§Ù„Ø¨Ø©

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£, Ø§Ù„Ù‚ÙŠÙ…Ø© Ø§Ù„Ø±Ù‚Ù…ÙŠØ©)
        """
        if price is None:
            return False, f"{field_name} cannot be empty", None

        if isinstance(price, str):
            price_str = price.strip()
            if not price_str:
                return False, f"{field_name} cannot be empty", None

            try:
                # Ù…Ø­Ø§ÙˆÙ„Ø© Ø§Ù„ØªØ­ÙˆÙŠÙ„ Ø¥Ù„Ù‰ float
                price_value = float(price_str)
            except ValueError:
                return False, f"{field_name} must be a valid number", None
        else:
            price_value = float(price)

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ù‚ÙŠÙ… Ø§Ù„Ø³Ø§Ù„Ø¨Ø©
        if not allow_negative and price_value < 0:
            return False, f"{field_name} cannot be negative", None

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ù‚ÙŠÙ…Ø© ØµÙØ±
        if not allow_zero and price_value == 0:
            return False, f"{field_name} cannot be zero", None

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø¯Ù‚Ø©
        if price_value > 1000000:  # Ù…Ù„ÙŠÙˆÙ†
            return False, f"{field_name} is too high", None

        return True, "", price_value

    @staticmethod
    def validate_percentage(percentage: Union[str, float], field_name: str = "Percentage",
                            min_value: float = 0, max_value: float = 100,
                            allow_zero: bool = False) -> Tuple[bool, str, Optional[float]]:
        """
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ø§Ù„Ù†Ø³Ø¨Ø© Ø§Ù„Ù…Ø¦ÙˆÙŠØ©

        Args:
            percentage: Ø§Ù„Ù†Ø³Ø¨Ø© Ø§Ù„Ù…Ø¦ÙˆÙŠØ© Ø§Ù„Ù…Ø¯Ø®Ù„Ø©
            field_name: Ø§Ø³Ù… Ø§Ù„Ø­Ù‚Ù„ (Ù„Ù„Ø±Ø³Ø§Ø¦Ù„)
            min_value: Ø§Ù„Ø­Ø¯ Ø§Ù„Ø£Ø¯Ù†Ù‰
            max_value: Ø§Ù„Ø­Ø¯ Ø§Ù„Ø£Ù‚ØµÙ‰
            allow_zero: Ø§Ù„Ø³Ù…Ø§Ø­ Ø¨Ø§Ù„Ù‚ÙŠÙ…Ø© ØµÙØ±

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£, Ø§Ù„Ù‚ÙŠÙ…Ø© Ø§Ù„Ø±Ù‚Ù…ÙŠØ©)
        """
        if percentage is None:
            return False, f"{field_name} cannot be empty", None

        if isinstance(percentage, str):
            percentage_str = percentage.strip()
            if not percentage_str:
                return False, f"{field_name} cannot be empty", None

            try:
                # Ù…Ø­Ø§ÙˆÙ„Ø© Ø§Ù„ØªØ­ÙˆÙŠÙ„ Ø¥Ù„Ù‰ float
                percentage_value = float(percentage_str)
            except ValueError:
                return False, f"{field_name} must be a valid number", None
        else:
            percentage_value = float(percentage)

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ù‚ÙŠÙ… Ø§Ù„Ø³Ø§Ù„Ø¨Ø©
        if percentage_value < 0:
            return False, f"{field_name} cannot be negative", None

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ù‚ÙŠÙ…Ø© ØµÙØ±
        if not allow_zero and percentage_value == 0:
            return False, f"{field_name} cannot be zero", None

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø­Ø¯ÙˆØ¯
        if percentage_value < min_value:
            return False, f"{field_name} must be at least {min_value}", None

        if percentage_value > max_value:
            return False, f"{field_name} cannot exceed {max_value}", None

        return True, "", percentage_value

    @staticmethod
    def validate_timestamp(timestamp: str) -> Tuple[bool, str]:
        """
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ø§Ù„Ø·Ø§Ø¨Ø¹ Ø§Ù„Ø²Ù…Ù†ÙŠ

        Args:
            timestamp: Ø§Ù„Ø·Ø§Ø¨Ø¹ Ø§Ù„Ø²Ù…Ù†ÙŠ

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£)
        """
        if not timestamp:
            return False, "Timestamp cannot be empty"

        try:
            # Ù…Ø­Ø§ÙˆÙ„Ø© ØªØ­Ù„ÙŠÙ„ Ø§Ù„Ø·Ø§Ø¨Ø¹ Ø§Ù„Ø²Ù…Ù†ÙŠ
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
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ø§Ù„Ø¨Ø±ÙŠØ¯ Ø§Ù„Ø¥Ù„ÙƒØªØ±ÙˆÙ†ÙŠ

        Args:
            email: Ø§Ù„Ø¨Ø±ÙŠØ¯ Ø§Ù„Ø¥Ù„ÙƒØªØ±ÙˆÙ†ÙŠ
            allow_empty: Ø§Ù„Ø³Ù…Ø§Ø­ Ø¨Ø§Ù„Ù‚ÙŠÙ… Ø§Ù„ÙØ§Ø±ØºØ©

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£)
        """
        if not email and allow_empty:
            return True, ""

        if email:
            # Ù†Ù…Ø· Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø¨Ø±ÙŠØ¯ Ø§Ù„Ø¥Ù„ÙƒØªØ±ÙˆÙ†ÙŠ
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                return False, "Invalid email format"

            if len(email) > 100:
                return False, "Email cannot exceed 100 characters"

        return True, ""

    @staticmethod
    def validate_phone(phone: str, allow_empty: bool = True) -> Tuple[bool, str]:
        """Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ø±Ù‚Ù… Ø§Ù„Ù‡Ø§ØªÙ"""
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
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© Ø§Ù„ÙƒÙ…ÙŠØ©

        Args:
            quantity: Ø§Ù„ÙƒÙ…ÙŠØ© Ø§Ù„Ù…Ø¯Ø®Ù„Ø©
            unit: ÙˆØ­Ø¯Ø© Ø§Ù„Ù‚ÙŠØ§Ø³
            allow_zero: Ø§Ù„Ø³Ù…Ø§Ø­ Ø¨Ø§Ù„Ù‚ÙŠÙ…Ø© ØµÙØ±

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£, Ø§Ù„Ù‚ÙŠÙ…Ø© Ø§Ù„Ø±Ù‚Ù…ÙŠØ©)
        """
        return Validators.validate_price(quantity, f"Quantity ({unit})" if unit else "Quantity",
                                         allow_zero=allow_zero, allow_negative=False)

    @staticmethod
    def validate_color_object(color_data: dict, allowed_dye_types: list = None) -> Tuple[bool, str, Optional[dict]]:
        """
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© ÙƒØ§Ø¦Ù† Ø§Ù„Ù„ÙˆÙ† Ø§Ù„ÙƒØ§Ù…Ù„

        Args:
            color_data: Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù„ÙˆÙ†
            allowed_dye_types: Ù‚Ø§Ø¦Ù…Ø© Ø£Ù†ÙˆØ§Ø¹ Ø§Ù„ØµØ¨Ø§ØºØ© Ø§Ù„Ù…Ø³Ù…ÙˆØ­Ø© (Ø§Ø®ØªÙŠØ§Ø±ÙŠ)

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£, Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ù†Ø¸ÙØ©)
        """
        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø­Ù‚ÙˆÙ„ Ø§Ù„Ù…Ø·Ù„ÙˆØ¨Ø©
        required_fields = ['code', 'name', 'dye_type']
        for field in required_fields:
            if field not in color_data or not color_data[field]:
                return False, f"Missing required field: {field}", None

        # ØªÙ†Ø¸ÙŠÙ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª
        cleaned_data = color_data.copy()

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ÙƒÙˆØ¯ Ø§Ù„Ù„ÙˆÙ†
        is_valid, message = Validators.validate_color_code(cleaned_data['code'])
        if not is_valid:
            return False, f"Color code: {message}", None

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ø³Ù… Ø§Ù„Ù„ÙˆÙ†
        is_valid, message = Validators.validate_name(cleaned_data['name'], "Color name", max_length=150)
        if not is_valid:
            return False, f"Color name: {message}", None

        # âœ… Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ù†ÙˆØ¹ Ø§Ù„ØµØ¨Ø§ØºØ© Ø¥Ø°Ø§ ØªÙ… ØªÙˆÙÙŠØ± Ø§Ù„Ù‚Ø§Ø¦Ù…Ø©
        if allowed_dye_types:
            is_valid, message = Validators.validate_dye_type(cleaned_data['dye_type'], allowed_dye_types)
            if not is_valid:
                return False, f"Dye type: {message}", None

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ù…ÙˆØ±Ø¯
        is_valid, message = Validators.validate_supplier(cleaned_data.get('supplier', ''))
        if not is_valid:
            return False, f"Supplier: {message}", None

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø³Ø¹Ø±
        is_valid, message, price = Validators.validate_price(
            cleaned_data.get('price_kg', 0), "Price per kg", allow_zero=True
        )
        if not is_valid:
            return False, f"Price: {message}", None
        cleaned_data['price_kg'] = price

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ù†Ø³Ø¨Ø© RESA
        is_valid, message, resa = Validators.validate_percentage(
            cleaned_data.get('resa_percent', 100), "RESA percentage", min_value=0, max_value=1000, allow_zero=True
        )
        if not is_valid:
            return False, f"RESA: {message}", None
        cleaned_data['resa_percent'] = resa

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„ØªÙˆØ§Ø±ÙŠØ®
        for date_field in ['created_at', 'updated_at']:
            if date_field in cleaned_data and cleaned_data[date_field]:
                is_valid, message = Validators.validate_timestamp(cleaned_data[date_field])
                if not is_valid:
                    # Ø¥Ø°Ø§ ÙƒØ§Ù† Ø§Ù„ØªØ§Ø±ÙŠØ® ØºÙŠØ± ØµØ§Ù„Ø­ØŒ Ø§Ø³ØªØ®Ø¯Ù… Ø§Ù„ØªØ§Ø±ÙŠØ® Ø§Ù„Ø­Ø§Ù„ÙŠ
                    cleaned_data[date_field] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return True, "Color data is valid", cleaned_data

    @staticmethod
    def validate_recipe_object(recipe_data: dict) -> Tuple[bool, str, Optional[dict]]:
        """
        Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ØµØ­Ø© ÙƒØ§Ø¦Ù† Ø§Ù„ÙˆØµÙØ© Ø§Ù„ÙƒØ§Ù…Ù„

        Args:
            recipe_data: Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„ÙˆØµÙØ©

        Returns:
            tuple: (ØµØ§Ù„Ø­/ØºÙŠØ± ØµØ§Ù„Ø­, Ø±Ø³Ø§Ù„Ø© Ø§Ù„Ø®Ø·Ø£, Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª Ø§Ù„Ù…Ù†Ø¸ÙØ©)
        """
        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø­Ù‚ÙˆÙ„ Ø§Ù„Ù…Ø·Ù„ÙˆØ¨Ø©
        if 'name' not in recipe_data or not recipe_data['name']:
            return False, "Missing required field: name", None

        # ØªÙ†Ø¸ÙŠÙ Ø§Ù„Ø¨ÙŠØ§Ù†Ø§Øª
        cleaned_data = recipe_data.copy()

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ÙƒÙˆØ¯ Ø§Ù„ÙˆØµÙØ© (Ø¥Ø°Ø§ ÙƒØ§Ù† Ù…ÙˆØ¬ÙˆØ¯Ø§Ù‹)
        if 'recipe_code' in cleaned_data and cleaned_data['recipe_code']:
            is_valid, message = Validators.validate_recipe_code(cleaned_data['recipe_code'])
            if not is_valid:
                return False, f"Recipe code: {message}", None

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ø³Ù… Ø§Ù„ÙˆØµÙØ©
        is_valid, message = Validators.validate_name(cleaned_data['name'], "Recipe name", max_length=200)
        if not is_valid:
            return False, f"Recipe name: {message}", None

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„ØªÙˆØ§Ø±ÙŠØ®
        for date_field in ['created_at']:
            if date_field in cleaned_data and cleaned_data[date_field]:
                is_valid, message = Validators.validate_timestamp(cleaned_data[date_field])
                if not is_valid:
                    # Ø¥Ø°Ø§ ÙƒØ§Ù† Ø§Ù„ØªØ§Ø±ÙŠØ® ØºÙŠØ± ØµØ§Ù„Ø­ØŒ Ø§Ø³ØªØ®Ø¯Ù… Ø§Ù„ØªØ§Ø±ÙŠØ® Ø§Ù„Ø­Ø§Ù„ÙŠ
                    cleaned_data[date_field] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ø£Ù„ÙˆØ§Ù† (Ø¥Ø°Ø§ ÙƒØ§Ù†Øª Ù…ÙˆØ¬ÙˆØ¯Ø©)
        if 'colors' in cleaned_data:
            if not isinstance(cleaned_data['colors'], list):
                return False, "Colors must be a list", None

            if not cleaned_data['colors']:
                return False, "Recipe must contain at least one color", None

            # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ÙƒÙ„ Ù„ÙˆÙ† ÙÙŠ Ø§Ù„ÙˆØµÙØ©
            total_percentage = 0
            for i, color in enumerate(cleaned_data['colors']):
                if not isinstance(color, dict):
                    return False, f"Color at index {i} must be a dictionary", None

                # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† ÙˆØ¬ÙˆØ¯ Ø§Ù„Ø­Ù‚ÙˆÙ„ Ø§Ù„Ù…Ø·Ù„ÙˆØ¨Ø©
                if 'color_code' not in color:
                    return False, f"Color at index {i} missing 'color_code'", None

                if 'percentage' not in color:
                    return False, f"Color at index {i} missing 'percentage'", None

                # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ù†Ø³Ø¨Ø© Ø§Ù„Ù…Ø¦ÙˆÙŠØ©
                is_valid, message, percentage = Validators.validate_percentage(
                    color['percentage'], f"Percentage for color {i + 1}",
                    min_value=0.01, max_value=100, allow_zero=False
                )
                if not is_valid:
                    return False, message, None

                total_percentage += percentage

            # Ø§Ù„ØªØ­Ù‚Ù‚ Ù…Ù† Ø§Ù„Ù†Ø³Ø¨Ø© Ø§Ù„ÙƒÙ„ÙŠØ©
            if total_percentage > 100:
                return False, f"Total percentage ({total_percentage:.2f}%) cannot exceed 100%", None

        return True, "Recipe data is valid", cleaned_data

