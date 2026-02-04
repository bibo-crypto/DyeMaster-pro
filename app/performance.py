"""
مساعد الأداء والتخزين المؤقت (Performance Helper)
"""
from app.cache import cache_manager, PaginationHelper
from app.database import DatabaseManager
from typing import Dict, Any, List, Optional


class PerformanceHelper:
    """مساعد لتحسين الأداء والاستفادة من الـ Cache و Pagination"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.cache_enabled = True
    
    def get_colors_smart(self, page: int = 1, per_page: int = 10, 
                         use_cache: bool = True) -> Dict:
        """
        الحصول على الألوان بذكاء:
        - استخدام Cache إذا كان متاحاً
        - تطبيق Pagination تلقائياً
        
        Args:
            page: رقم الصفحة
            per_page: عدد العناصر
            use_cache: هل نستخدم الـ Cache
        
        Returns:
            نتائج الصفحة مع معلومات الـ Cache
        """
        cache_key = f"colors_page_{page}_perpage_{per_page}"
        
        if use_cache and self.cache_enabled:
            cached = cache_manager.get(cache_key)
            if cached:
                cached['from_cache'] = True
                return cached
        
        result = self.db.get_colors_paginated(page, per_page)
        result['from_cache'] = False
        
        if use_cache and self.cache_enabled:
            cache_manager.set(cache_key, result, ttl=600)  # 10 دقائق
        
        return result
    
    def get_recipes_smart(self, page: int = 1, per_page: int = 10,
                         use_cache: bool = True) -> Dict:
        """الحصول على الوصفات بذكاء"""
        cache_key = f"recipes_page_{page}_perpage_{per_page}"
        
        if use_cache and self.cache_enabled:
            cached = cache_manager.get(cache_key)
            if cached:
                cached['from_cache'] = True
                return cached
        
        result = self.db.get_recipes_paginated(page, per_page)
        result['from_cache'] = False
        
        if use_cache and self.cache_enabled:
            cache_manager.set(cache_key, result, ttl=600)
        
        return result
    
    def search_colors_smart(self, code: str = "", name: str = "", 
                           dye_type: str = "", supplier: str = "",
                           price_min: float = 0, price_max: float = float('inf'),
                           page: int = 1, per_page: int = 10,
                           use_cache: bool = True) -> Dict:
        """
        بحث متقدم عن الألوان مع الـ Cache
        """
        cache_key = f"search_colors_{code}_{name}_{dye_type}_{supplier}_{price_min}_{price_max}_{page}_{per_page}"
        
        if use_cache and self.cache_enabled:
            cached = cache_manager.get(cache_key)
            if cached:
                cached['from_cache'] = True
                return cached
        
        result = self.db.advanced_search_colors(
            code, name, dye_type, supplier, price_min, price_max, page, per_page
        )
        result['from_cache'] = False
        
        if use_cache and self.cache_enabled:
            cache_manager.set(cache_key, result, ttl=300)  # 5 دقائق
        
        return result
    
    def search_recipes_smart(self, recipe_code: str = "", name: str = "",
                            dye_type: str = "", page: int = 1, per_page: int = 10,
                            use_cache: bool = True) -> Dict:
        """بحث متقدم عن الوصفات مع الـ Cache"""
        cache_key = f"search_recipes_{recipe_code}_{name}_{dye_type}_{page}_{per_page}"
        
        if use_cache and self.cache_enabled:
            cached = cache_manager.get(cache_key)
            if cached:
                cached['from_cache'] = True
                return cached
        
        result = self.db.advanced_search_recipes(
            recipe_code, name, dye_type, page, per_page
        )
        result['from_cache'] = False
        
        if use_cache and self.cache_enabled:
            cache_manager.set(cache_key, result, ttl=300)
        
        return result
    
    def invalidate_cache(self, pattern: Optional[str] = None):
        """
        إبطال الـ Cache
        
        Args:
            pattern: نمط معين (null = مسح الكل)
        """
        if pattern is None:
            cache_manager.clear()
        else:
            # مسح عناصر محددة
            for key in list(cache_manager._cache.keys()):
                if pattern in key:
                    cache_manager.delete(key)
    
    def get_performance_report(self) -> Dict:
        """الحصول على تقرير الأداء"""
        stats = cache_manager.get_stats()
        
        return {
            'cache_enabled': self.cache_enabled,
            'cache_stats': stats,
            'cache_available': True,
            'pagination_available': True,
            'advanced_search_available': True
        }
    
    def enable_cache(self, enabled: bool = True):
        """تفعيل أو تعطيل الـ Cache"""
        self.cache_enabled = enabled
        if not enabled:
            cache_manager.clear()
    
    def cleanup(self):
        """تنظيف الموارد"""
        cache_manager.cleanup_expired()
