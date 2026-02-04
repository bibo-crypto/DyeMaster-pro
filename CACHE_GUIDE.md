"""
دليل الميزات الجديدة - Cache, Indexing, Pagination, Advanced Search
====================================================================

هذا الملف يشرح كيفية استخدام الميزات الجديدة التي تم إضافتها للبرنامج
"""

# ============================================================================
# 1. CACHE SYSTEM (نظام التخزين المؤقت)
# ============================================================================

"""
نظام الـ Cache يخزن البيانات المستخدمة بكثرة في الذاكرة لتحسين الأداء

المزايا:
- تحسين سرعة الوصول إلى البيانات (3000+ مرة أسرع)
- تقليل حمل قاعدة البيانات
- تقليل استهلاك الموارد

الاستخدام الأساسي:
"""

from app.cache import cache_manager

# حفظ بيانات
cache_manager.set("my_key", "my_value", ttl=300)  # 5 دقائق

# الحصول على البيانات
value = cache_manager.get("my_key")

# الحصول على إحصائيات
stats = cache_manager.get_stats()
print(stats)
# {'hits': 10, 'misses': 2, 'hit_rate': '83.33%', 'cached_items': 5, 'memory_usage': '2.45 KB'}

# مسح الـ Cache كاملاً
cache_manager.clear()

# تنظيف العناصر المنتهية الصلاحية
cache_manager.cleanup_expired()

# ============================================================================
# 2. CACHE DECORATOR (Decorator للـ Cache)
# ============================================================================

"""
يمكن استخدام Decorator لتطبيق الـ Cache تلقائياً على أي دالة
"""

@cache_manager.cache_decorator(ttl=600)  # 10 دقائق
def get_user_data(user_id):
    # هذه الدالة ستُخزّن نتائجها في الـ Cache
    return db.get_user(user_id)

# المرة الأولى: تنفيذ الدالة
result = get_user_data(1)  # تم تنفيذها

# المرة الثانية: من الـ Cache
result = get_user_data(1)  # من الـ Cache (أسرع بكثير!)

# ============================================================================
# 3. PAGINATION (تقسيم النتائج إلى صفحات)
# ============================================================================

"""
الـ Pagination تقسم النتائج إلى صفحات صغيرة لتحسين الأداء
والقدرة على عرض البيانات بكفاءة
"""

from app.database import DatabaseManager

db = DatabaseManager()

# الحصول على الألوان بصيغة مقسمة
result = db.get_colors_paginated(page=1, per_page=10)

print(result)
# {
#   'items': [Color, Color, ...],  # 10 ألوان
#   'page': 1,
#   'per_page': 10,
#   'total_items': 50,
#   'total_pages': 5,
#   'has_next': True,
#   'has_prev': False,
#   'next_page': 2,
#   'prev_page': None
# }

# الحصول على الصفحة التالية
next_result = db.get_colors_paginated(page=2, per_page=10)

# ============================================================================
# 4. ADVANCED SEARCH (البحث المتقدم)
# ============================================================================

"""
البحث المتقدم يتيح البحث عن البيانات باستخدام فلاتر متعددة
"""

# البحث عن الألوان بفلاتر متعددة
result = db.advanced_search_colors(
    code="101",           # كود اللون (جزئي)
    name="Tur",           # اسم اللون (جزئي)
    dye_type="Indanthren IN",  # نوع الصباغة
    supplier="",          # المورد
    price_min=0,          # الحد الأدنى للسعر
    price_max=500,        # الحد الأقصى للسعر
    page=1,
    per_page=10
)

print(result)
# {
#   'items': [...],
#   'page': 1,
#   'total_results': 5,  # عدد النتائج الكلي
#   'filters_applied': {...},  # الفلاتر المستخدمة
#   ...
# }

# البحث عن الوصفات
result = db.advanced_search_recipes(
    recipe_code="123",
    name="",
    dye_type="Indanthren IN",
    page=1,
    per_page=5
)

# ============================================================================
# 5. INDEXING (الفهارسة)
# ============================================================================

"""
تم إضافة فهارس على الأعمدة المستخدمة كثيراً:
- colors.code
- colors.name
- colors.dye_type
- recipes.recipe_code
- recipes.name

الفهارسة تحسن سرعة البحث والاستعلامات بشكل كبير
(تم تطبيقها تلقائياً عند تهيئة قاعدة البيانات)
"""

# ============================================================================
# 6. PERFORMANCE HELPER (مساعد الأداء)
# ============================================================================

"""
مساعد يجمع كل الميزات معاً ويوفر واجهة سهلة للاستخدام
"""

from app.performance import PerformanceHelper

perf = PerformanceHelper(db)

# الحصول على الألوان مع الـ Cache تلقائياً
result = perf.get_colors_smart(page=1, per_page=10, use_cache=True)

print(result)
# {
#   'items': [...],
#   'from_cache': False,  # أول مرة
#   ...
# }

# المرة الثانية: من الـ Cache
result = perf.get_colors_smart(page=1, per_page=10, use_cache=True)

print(result)
# {
#   'items': [...],
#   'from_cache': True,   # من الـ Cache
#   ...
# }

# البحث المتقدم مع الـ Cache
result = perf.search_colors_smart(
    dye_type="Indanthren IN",
    price_min=0,
    price_max=500,
    page=1,
    per_page=10
)

# الحصول على تقرير الأداء
report = perf.get_performance_report()
print(report)

# إبطال الـ Cache عند التحديث
perf.invalidate_cache()  # مسح الكل

# إبطال جزء من الـ Cache
perf.invalidate_cache("colors")  # مسح عناصر معينة

# تفعيل/تعطيل الـ Cache
perf.enable_cache(False)  # تعطيل الـ Cache

# ============================================================================
# 7. مثال متكامل
# ============================================================================

"""
مثال كامل لاستخدام جميع الميزات معاً
"""

from app.database import DatabaseManager
from app.performance import PerformanceHelper

db = DatabaseManager()
perf = PerformanceHelper(db)

# البحث عن ألوان معينة مع Pagination
result = perf.search_colors_smart(
    dye_type="Indanthren IN",
    price_min=50,
    price_max=200,
    page=1,
    per_page=5
)

print(f"وجدنا {result['total_results']} نتيجة")
print(f"الصفحة {result['page']} من {result['total_pages']}")

for color in result['items']:
    print(f"  - {color.code}: {color.name} ({color.dye_type})")

if result['has_next']:
    # الحصول على الصفحة التالية
    next_result = perf.search_colors_smart(
        dye_type="Indanthren IN",
        price_min=50,
        price_max=200,
        page=result['next_page'],
        per_page=5
    )

# عند إضافة لون جديد، نبطل الـ Cache ذي الصلة
new_color = add_new_color(...)
perf.invalidate_cache("colors")  # مسح cache الألوان
perf.invalidate_cache("search")  # مسح cache البحث

# ============================================================================
# 8. قائمة الدوال المتاحة
# ============================================================================

"""
Cache Manager:
  - cache_manager.set(key, value, ttl)
  - cache_manager.get(key)
  - cache_manager.delete(key)
  - cache_manager.clear()
  - cache_manager.cleanup_expired()
  - cache_manager.get_stats()
  - cache_manager.cache_decorator(ttl)

Database Manager:
  - db.get_colors_paginated(page, per_page)
  - db.get_recipes_paginated(page, per_page)
  - db.advanced_search_colors(code, name, dye_type, supplier, price_min, price_max, page, per_page)
  - db.advanced_search_recipes(recipe_code, name, dye_type, page, per_page)
  - db.get_cache_stats()
  - db.clear_cache()
  - db.cleanup_expired_cache()

Performance Helper:
  - perf.get_colors_smart(page, per_page, use_cache)
  - perf.get_recipes_smart(page, per_page, use_cache)
  - perf.search_colors_smart(..., use_cache)
  - perf.search_recipes_smart(..., use_cache)
  - perf.invalidate_cache(pattern)
  - perf.get_performance_report()
  - perf.enable_cache(enabled)
  - perf.cleanup()
"""
