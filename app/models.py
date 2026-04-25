from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Color:
    """نموذج اللون"""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    dye_type: str = ""
    supplier: str = ""
    price_kg: float = 0.0
    resa_percent: float = 100.0
    created_at: str = ""
    updated_at: str = ""

@dataclass
class Recipe:
    """نموذج الوصفة"""
    id: Optional[int] = None
    recipe_code: str = ""
    name: str = ""
    colors_count: int = 0
    total_percentage: float = 0.0
    created_at: str = ""
    dominant_dye_type: str = ""

@dataclass 
class User:
    """نموذج المستخدم لنظام Login"""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    role: str = "viewer"  # admin | tech | viewer
    created_at: str = ""
    last_login: Optional[str] = None
    active: bool = True

@dataclass
class Chemical:
    """نموذج الكيماويات"""
    code: str = ""
    name: str = ""
    quantity: float = 0.0
    unit: str = ""

@dataclass
class RecipeDetails:
    """تفاصيل الوصفة"""
    recipe: Recipe
    colors: List[dict]
    chemicals: List[Chemical]
    total_percentage: float = 0.0
    dominant_type: str = ""
    cost: float = 0.0
