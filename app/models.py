"""
ColorChemSystem/app/models.py
"""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Color:
    """نموذج اللون"""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    dye_type: str = ""
    supplier: str = ""          # إضافة هذا الحقل
    price_kg: float = 0.0
    resa_percent: float = 0.0   # إضافة هذا الحقل أيضاً
    created_at: str = ""
    updated_at: str = ""

    def validate(self):
        """التحقق من صحة بيانات اللون"""
        errors = []
        if not self.code.strip():
            errors.append("Color code is required")
        if not self.name.strip():
            errors.append("Color name is required")
        if self.price_kg < 0:
            errors.append("Price must be positive")
        if self.resa_percent < 0 or self.resa_percent > 100:
            errors.append("RESA must be between 0 and 100")
        return errors

@dataclass
class Recipe:
    """نموذج الريتشت"""
    id: Optional[int] = None
    recipe_code: str = ""
    name: str = ""
    colors_count: int = 0
    total_percentage: float = 0.0
    created_at: str = ""
    dominant_dye_type: str = ""

@dataclass
class RecipeColor:
    """نموذج علاقة الريتشت باللون"""
    id: Optional[int] = None
    recipe_id: int = 0
    color_id: int = 0
    percentage: float = 0.0
    color_code: str = ""
    color_name: str = ""
    dye_type: str = ""
    price_kg: float = 0.0
    supplier: str = ""          # إضافة هذا الحقل

@dataclass
class Chemical:
    """نموذج الكيماويات"""
    code: str = ""
    name: str = ""
    quantity: float = 0.0
    unit: str = ""

@dataclass
class RecipeDetails:
    """تفاصيل الريتشت الكاملة"""
    recipe: Recipe
    colors: List[dict]
    chemicals: List[Chemical]
    total_percentage: float
    dominant_type: str
    cost: float
