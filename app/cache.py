"""
نظام Cache لتحسين الأداء
"""
import time
from typing import Any, Dict, Optional, List, Callable
from threading import Lock
from datetime import datetime, timedelta
from functools import wraps


class CacheManager:
    """مدير التخزين المؤقت (Cache)"""
    
    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: الوقت الافتراضي لانتهاء صلاحية الـ Cache بالثواني (5 دقائق)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._locks: Dict[str, Lock] = {}
        self.default_ttl = default_ttl
        self.hits = 0  # عدد مرات النجاح في Cache
        self.misses = 0  # عدد مرات الفشل في Cache
    
    def get(self, key: str) -> Optional[Any]:
        """الحصول على قيمة من الـ Cache"""
        if key not in self._cache:
            self.misses += 1
            return None
        
        cache_entry = self._cache[key]
        
        # تحقق من انتهاء الصلاحية
        if datetime.now() > cache_entry['expires_at']:
            del self._cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        cache_entry['last_access'] = datetime.now()
        return cache_entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """حفظ قيمة في الـ Cache"""
        if key not in self._locks:
            self._locks[key] = Lock()
        
        with self._locks[key]:
            ttl = ttl or self.default_ttl
            self._cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl),
                'created_at': datetime.now(),
                'last_access': datetime.now()
            }
    
    def delete(self, key: str):
        """حذف قيمة من الـ Cache"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """مسح الـ Cache بالكامل"""
        self._cache.clear()
        self.hits = 0
        self.misses = 0
    
    def cleanup_expired(self):
        """تنظيف العناصر المنتهية الصلاحية"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if datetime.now() > entry['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الـ Cache"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'cached_items': len(self._cache),
            'memory_usage': self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> str:
        """تقدير استخدام الذاكرة"""
        import sys
        total_size = sys.getsizeof(self._cache)
        for entry in self._cache.values():
            total_size += sys.getsizeof(entry['value'])
        
        # تحويل إلى KB/MB
        if total_size < 1024:
            return f"{total_size} B"
        elif total_size < 1024 * 1024:
            return f"{total_size / 1024:.2f} KB"
        else:
            return f"{total_size / (1024 * 1024):.2f} MB"
    
    def cache_decorator(self, ttl: Optional[int] = None) -> Callable:
        """Decorator لتخزين نتائج الدوال"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # إنشاء مفتاح من اسم الدالة والمعاملات
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # محاولة الحصول من الـ Cache
                cached_result = self.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # تنفيذ الدالة وحفظ النتيجة
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            
            return wrapper
        return decorator


class PaginationHelper:
    """مساعد لـ Pagination"""
    
    @staticmethod
    def paginate(items: List[Any], page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        تقسيم قائمة إلى صفحات
        
        Args:
            items: القائمة الكاملة
            page: رقم الصفحة (من 1)
            per_page: عدد العناصر في الصفحة
        
        Returns:
            قاموس يحتوي على بيانات الصفحة
        """
        if page < 1:
            page = 1
        
        total_items = len(items)
        total_pages = (total_items + per_page - 1) // per_page
        
        if page > total_pages and total_pages > 0:
            page = total_pages
        
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        page_items = items[start_idx:end_idx]
        
        return {
            'items': page_items,
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'next_page': page + 1 if page < total_pages else None,
            'prev_page': page - 1 if page > 1 else None
        }
    
    @staticmethod
    def paginate_query(query_result: List[Any], page: int = 1, per_page: int = 10) -> tuple:
        """
        تقسيم نتائج الاستعلام
        
        Returns:
            (items, total_pages, current_page)
        """
        result = PaginationHelper.paginate(query_result, page, per_page)
        return result['items'], result['total_pages'], result['page']


# Global cache manager
cache_manager = CacheManager()
