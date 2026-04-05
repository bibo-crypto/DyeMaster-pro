"""
مدير قاعدة البيانات
"""
import sqlite3
import os
import stat
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from app.utils import get_current_timestamp
from app.config import DATABASE_FILE, BACKUP_DIR
from app.models import Color, Recipe, Chemical
from app.cache import cache_manager


class ColorManager:
    """مدير الألوان - واجهة عالية المستوى لإدارة الألوان"""
    
    def __init__(self, db_manager):
        """تهيئة مدير الألوان"""
        self.db = db_manager

    def add_color(self, color_data: dict) -> Tuple[bool, str, Optional[Color]]:
        """إضافة لون جديد من قاموس"""
        try:
            from app.validators import Validators

            # التحقق من صحة البيانات
            is_valid, message, cleaned_data = Validators.validate_color_object(color_data)
            if not is_valid:
                return False, message, None

            # تنظيف الكود
            from app.utils import clean_color_code
            cleaned_code = clean_color_code(cleaned_data.get('code', ''))
            cleaned_data['code'] = cleaned_code

            # إضافة التواريخ إذا لم تكن موجودة
            if 'created_at' not in cleaned_data or not cleaned_data['created_at']:
                cleaned_data['created_at'] = get_current_timestamp()
            if 'updated_at' not in cleaned_data or not cleaned_data['updated_at']:
                cleaned_data['updated_at'] = get_current_timestamp()

            # التحقق من عدم وجود اللون مسبقاً
            existing = self.db.get_color_by_code(cleaned_code)
            if existing:
                return False, f"Color code '{cleaned_code}' already exists", None

            # إنشاء كائن Color
            color = Color(
                id=0,
                code=cleaned_data['code'],
                name=cleaned_data['name'],
                dye_type=cleaned_data['dye_type'],
                supplier=cleaned_data.get('supplier', ''),
                price_kg=cleaned_data.get('price_kg', 0.0),
                resa_percent=cleaned_data.get('resa_percent', 100.0),
                created_at=cleaned_data.get('created_at', ''),
                updated_at=cleaned_data.get('updated_at', '')
            )

            # إضافة اللون
            color_id = self.db.add_color(color)
            color.id = color_id

            return True, "Color added successfully", color

        except Exception as e:
            return False, str(e), None

    def update_color(self, old_code: str, color_data: dict) -> Tuple[bool, str, Optional[Color]]:
        """تحديث لون موجود"""
        try:
            from app.utils import clean_color_code, get_current_timestamp

            # الحصول على اللون القديم
            old_color = self.db.get_color_by_code(old_code)
            if not old_color:
                return False, f"Color code '{old_code}' not found", None

            from app.validators import Validators
            # التحقق من صحة البيانات
            is_valid, message, cleaned_data = Validators.validate_color_object(color_data)
            if not is_valid:
                return False, message, None

            # تنظيف الكود الجديد
            cleaned_code = clean_color_code(cleaned_data.get('code', old_code))
            cleaned_data['code'] = cleaned_code

            # إذا تغير الكود، التحقق من عدم وجود كود آخر بهذا الاسم
            if cleaned_code != old_code:
                existing = self.db.get_color_by_code(cleaned_code)
                if existing:
                    return False, f"Color code '{cleaned_code}' already exists", None

            # تحديث التاريخ
            cleaned_data['updated_at'] = get_current_timestamp()

            # إنشاء كائن Color محدث
            color = Color(
                id=old_color.id,
                code=cleaned_data['code'],
                name=cleaned_data.get('name', old_color.name),
                dye_type=cleaned_data.get('dye_type', old_color.dye_type),
                supplier=cleaned_data.get('supplier', old_color.supplier),
                price_kg=cleaned_data.get('price_kg', old_color.price_kg),
                resa_percent=cleaned_data.get('resa_percent', old_color.resa_percent),
                created_at=old_color.created_at,
                updated_at=cleaned_data['updated_at']
            )

            # تحديث اللون
            success = self.db.update_color(color)
            if success:
                return True, "Color updated successfully", color
            else:
                return False, "Failed to update color", None

        except Exception as e:
            return False, str(e), None

    def update_color_in_recipes(self, old_color_id: int, new_code: str) -> bool:
        """تحديث الألوان في الوصفات عند تغيير كود اللون"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # الحصول على ID اللون الجديد
            cursor.execute("SELECT id FROM colors WHERE code = ?", (new_code,))
            new_color_row = cursor.fetchone()
            
            if new_color_row:
                new_color_id = new_color_row[0]
                # تحديث جميع الوصفات التي تحتوي على اللون القديم
                cursor.execute("""
                    UPDATE recipe_colors 
                    SET color_id = ? 
                    WHERE color_id = ?
                """, (new_color_id, old_color_id))
                conn.commit()
                return True
            
            return False
        except Exception:
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            return False
        finally:
            if conn:
                conn.close()

    def delete_color(self, color_id: int) -> bool:
        """حذف لون من قاعدة البيانات"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # التحقق أولاً من وجود اللون
            cursor.execute("SELECT code FROM colors WHERE id = ?", (color_id,))
            row = cursor.fetchone()
            if not row:
                return True  # نعتبره ناجحاً لأنه غير موجود أصلاً

            color_code = row[0]

            # التحقق من استخدام اللون في الوصفات
            if self.is_color_in_use(color_code):
                return False  # لا يمكن الحذف إذا كان اللون مستخدماً

            # حذف ارتباطات اللون في الوصفات أولاً لتجنب السجلات اليتيمة
            cursor.execute("DELETE FROM recipe_colors WHERE color_id = ?", (color_id,))

            # حذف اللون
            cursor.execute("DELETE FROM colors WHERE id = ?", (color_id,))
            conn.commit()

            return True

        except Exception:
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            return False
        finally:
            if conn:
                conn.close()

    def get_color_by_id(self, color_id):
        """الحصول على لون بواسطة ID"""
        conn = None
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, code, name, dye_type, supplier, price_kg, resa_percent, created_at, updated_at
                FROM colors 
                WHERE id = ?
            """, (color_id,))

            row = cursor.fetchone()
            if row:
                return Color(
                    id=row[0],
                    code=row[1],
                    name=row[2],
                    dye_type=row[3],
                    supplier=row[4],
                    price_kg=row[5],
                    resa_percent=row[6],
                    created_at=row[7],
                    updated_at=row[8]
                )
            return None

        except sqlite3.Error as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

    def search_colors(self, search_term: str, search_in: str = 'both') -> List[Color]:
        """بحث في الألوان"""
        if search_in == 'code':
            return self.db.search_colors(code_filter=search_term)
        elif search_in == 'name':
            return self.db.search_colors(name_filter=search_term)
        else:  # 'both'
            colors_by_code = self.db.search_colors(code_filter=search_term)
            colors_by_name = self.db.search_colors(name_filter=search_term)
            # دمج القوائم مع تجنب التكرار
            all_colors = {color.code: color for color in colors_by_code}
            for color in colors_by_name:
                if color.code not in all_colors:
                    all_colors[color.code] = color
            return list(all_colors.values())

    def is_color_in_use(self, color_code: str) -> bool:
        """التحقق من استخدام اللون في ريتشتات"""
        conn = None
        try:
            from app.utils import clean_color_code
            normalized_code = clean_color_code(color_code)
            color = self.db.get_color_by_code(normalized_code)
            if not color:
                return False

            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM recipe_colors 
                WHERE color_id = ?
            ''', (color.id,))
            count = cursor.fetchone()[0]

            return count > 0
        except Exception:
            return False
        finally:
            if conn:
                conn.close()

    def get_recipes_using_color(self, color_code: str) -> List[Recipe]:
        """الحصول على جميع الريتشتات التي تستخدم هذا اللون"""
        conn = None
        try:
            from app.utils import clean_color_code
            normalized_code = clean_color_code(color_code)
            color = self.db.get_color_by_code(normalized_code)
            if not color:
                return []

            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.* FROM recipes r
                JOIN recipe_colors rc ON r.id = rc.recipe_id
                WHERE rc.color_id = ?
            ''', (color.id,))
            rows = cursor.fetchall()

            recipes = []
            for row in rows:
                recipes.append(Recipe(
                    id=row[0],
                    recipe_code=row[1],
                    name=row[2],
                    created_at=row[3]
                ))
            return recipes
        except Exception:
            return []
        finally:
            if conn:
                conn.close()


class DatabaseManager:
    """مدير قاعدة البيانات"""
    
    def __init__(self, db_file=None):
        """تهيئة مدير قاعدة البيانات"""
        self.db_file = db_file or DATABASE_FILE
        self.ensure_database_exists()
        self.color_manager = ColorManager(self)

    def _ensure_db_writable(self):
        """Attempt to clear read-only flags on DB path and parent directory."""
        db_dir = os.path.dirname(self.db_file)
        if db_dir and os.path.exists(db_dir):
            try:
                os.chmod(db_dir, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
            except Exception:
                pass

        if os.path.exists(self.db_file):
            try:
                os.chmod(self.db_file, stat.S_IREAD | stat.S_IWRITE)
            except Exception:
                pass

    def get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
        self._ensure_db_writable()
        try:
            conn = sqlite3.connect(self.db_file)
            conn.execute("PRAGMA foreign_keys = ON")
            return conn
        except sqlite3.OperationalError as e:
            if "readonly" in str(e).lower():
                self._ensure_db_writable()
                conn = sqlite3.connect(self.db_file)
                conn.execute("PRAGMA foreign_keys = ON")
                return conn
            raise

    def ensure_database_exists(self):
        """التأكد من وجود قاعدة البيانات والجداول"""
        conn = None
        try:
            # التأكد من وجود المجلد
            db_dir = os.path.dirname(self.db_file)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            
            conn = self.get_connection()
            cursor = conn.cursor()

            # إنشاء جدول الألوان
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS colors
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    dye_type TEXT NOT NULL,
                    supplier TEXT,
                    price_kg REAL DEFAULT 0.0,
                    resa_percent REAL DEFAULT 100.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # إنشاء جدول الريتشتات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recipes
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إنشاء جدول ألوان الريتشتات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recipe_colors
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_id INTEGER NOT NULL,
                    color_id INTEGER NOT NULL,
                    percentage REAL NOT NULL,
                    FOREIGN KEY (recipe_id) REFERENCES recipes (id),
                    FOREIGN KEY (color_id) REFERENCES colors (id)
                )
            ''')

            # إنشاء جدول كيماويات الريتشتات
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recipe_chemicals
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_id INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    FOREIGN KEY (recipe_id) REFERENCES recipes (id)
                )
            ''')

            # إضافة الأعمدة المفقودة إذا كان الجدول موجوداً
            try:
                cursor.execute('ALTER TABLE recipes ADD COLUMN colors_count INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass  # العمود موجود بالفعل

            try:
                cursor.execute('ALTER TABLE recipes ADD COLUMN total_percentage REAL DEFAULT 0.0')
            except sqlite3.OperationalError:
                pass  # العمود موجود بالفعل
            
            # إضافة الفهارس لتحسين الأداء
            self._create_indexes(cursor)
            
            conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Error ensuring database exists: {e}")
        finally:
            if conn:
                conn.close()

    def _create_indexes(self, cursor):
        """إنشاء الفهارس لتحسين الأداء"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_colors_code ON colors(code)",
            "CREATE INDEX IF NOT EXISTS idx_colors_name ON colors(name)",
            "CREATE INDEX IF NOT EXISTS idx_colors_dye_type ON colors(dye_type)",
            "CREATE INDEX IF NOT EXISTS idx_recipes_code ON recipes(recipe_code)",
            "CREATE INDEX IF NOT EXISTS idx_recipes_name ON recipes(name)",
            "CREATE INDEX IF NOT EXISTS idx_recipe_colors_recipe ON recipe_colors(recipe_id)",
            "CREATE INDEX IF NOT EXISTS idx_recipe_colors_color ON recipe_colors(color_id)",
            "CREATE INDEX IF NOT EXISTS idx_recipe_chemicals_recipe ON recipe_chemicals(recipe_id)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.OperationalError:
                pass  # الفهرس موجود بالفعل

    def initialize_database(self):
        """تهيئة قاعدة البيانات (للمرة الأولى)"""
        self.ensure_database_exists()

    def _cache_key(self, name: str, *parts) -> str:
        serialized = ":".join(str(part) for part in parts)
        return f"db:{name}:{serialized}" if serialized else f"db:{name}"

    def _invalidate_read_cache(self):
        """مسح كاش القراءات بعد أي كتابة على قاعدة البيانات."""
        cache_manager.clear()

    # ============ دوال الألوان ============

    def add_color(self, color: Color) -> int:
        """إضافة لون جديد"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # إذا لم تكن هناك تواريخ، استخدم القيم الحالية
            created_at = color.created_at if color.created_at else get_current_timestamp()
            updated_at = color.updated_at if color.updated_at else get_current_timestamp()

            cursor.execute('''
                           INSERT INTO colors (code, name, dye_type, supplier, price_kg, resa_percent, created_at,
                                               updated_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                           ''', (color.code, color.name, color.dye_type, color.supplier,
                                 color.price_kg, color.resa_percent, created_at, updated_at))

            conn.commit()
            color_id = cursor.lastrowid
            self._invalidate_read_cache()
            return color_id

        except sqlite3.IntegrityError as e:
            if conn:
                conn.rollback()
            raise Exception(f"Color code '{color.code}' already exists")
        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Failed to add color: {str(e)}")
        finally:
            if conn:
                conn.close()

    def update_color(self, color: Color) -> bool:
        """تحديث بيانات لون"""
        conn = None
        try:
            from app.utils import get_current_timestamp
            conn = self.get_connection()
            cursor = conn.cursor()

            updated_at = get_current_timestamp()

            cursor.execute('''
                UPDATE colors 
                SET code = ?, name = ?, dye_type = ?, supplier = ?, price_kg = ?, resa_percent = ?, updated_at = ?
                WHERE id = ?
            ''', (color.code, color.name, color.dye_type, color.supplier,
                  color.price_kg, color.resa_percent, updated_at, color.id))

            affected = cursor.rowcount
            conn.commit()
            if affected > 0:
                self._invalidate_read_cache()
            return affected > 0

        except Exception as e:
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            raise Exception(f"Failed to update color: {str(e)}")
        finally:
            if conn:
                conn.close()

    def delete_color(self, color_id: int) -> bool:
        """حذف لون مع حذف ارتباطاته في الوصفات"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # الحصول على اللون للتحقق من استخدامه
            cursor.execute("SELECT code FROM colors WHERE id = ?", (color_id,))
            row = cursor.fetchone()
            if not row:
                return True  # اللون غير موجود، نعتبره محذوفاً

            color_code = row[0]

            # التحقق من استخدام اللون في الوصفات
            if self.color_manager.is_color_in_use(color_code):
                return False  # لا يمكن الحذف إذا كان اللون مستخدماً

            # First, delete references in recipe_colors to avoid orphan records
            cursor.execute('DELETE FROM recipe_colors WHERE color_id = ?', (color_id,))

            # Then, delete the color itself
            cursor.execute('DELETE FROM colors WHERE id = ?', (color_id,))
            affected = cursor.rowcount
            conn.commit()
            if affected > 0:
                self._invalidate_read_cache()
            return affected > 0

        except Exception as e:
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            raise Exception(f"Failed to delete color: {str(e)}")
        finally:
            if conn:
                conn.close()

    def delete_color_by_code(self, color_code: str) -> bool:
        """حذف لون بواسطة الكود"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('DELETE FROM colors WHERE code = ?', (color_code,))
            affected = cursor.rowcount
            conn.commit()
            if affected > 0:
                self._invalidate_read_cache()
            return affected > 0

        except Exception as e:
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            raise Exception(f"Failed to delete color: {str(e)}")
        finally:
            if conn:
                conn.close()

    def _get_color_from_row(self, row, columns):
        """دالة مساعدة لإنشاء كائن Color من صف قاعدة البيانات"""
        color_dict = dict(zip(columns, row))
        return Color(
            id=color_dict.get('id', 0),
            code=color_dict.get('code', ''),
            name=color_dict.get('name', ''),
            dye_type=color_dict.get('dye_type', ''),
            supplier=color_dict.get('supplier', ''),
            price_kg=color_dict.get('price_kg', 0.0),
            resa_percent=color_dict.get('resa_percent', 0.0),
            created_at=color_dict.get('created_at', ''),
            updated_at=color_dict.get('updated_at', '')
        )

    def get_color_by_id(self, color_id):
        """الحصول على لون بواسطة ID"""
        conn = None
        try:
            cache_key = self._cache_key("color_by_id", color_id)
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return cached

            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                           SELECT id,
                                  code,
                                  name,
                                  dye_type,
                                  supplier,
                                  price_kg,
                                  resa_percent,
                                  created_at,
                                  updated_at
                           FROM colors
                           WHERE id = ?
                           """, (color_id,))

            row = cursor.fetchone()
            if row:
                color_obj = Color(
                    id=row[0],
                    code=row[1],
                    name=row[2],
                    dye_type=row[3],
                    supplier=row[4],
                    price_kg=row[5],
                    resa_percent=row[6],
                    created_at=row[7],
                    updated_at=row[8]
                )
                cache_manager.set(cache_key, color_obj)
                return color_obj
            return None

        except sqlite3.Error as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_color_by_code(self, color_code: str) -> Optional[Color]:
        """الحصول على لون بواسطة الكود"""
        conn = None
        try:
            from app.utils import clean_color_code
            raw_code = str(color_code).strip() if color_code is not None else ""
            normalized_code = clean_color_code(color_code)
            cache_key = self._cache_key("color_by_code", raw_code.lower(), normalized_code.lower())
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return cached

            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                '''
                SELECT * FROM colors
                WHERE code = ?
                   OR code = ?
                   OR LOWER(code) = LOWER(?)
                   OR LOWER(code) = LOWER(?)
                LIMIT 1
                ''',
                (raw_code, normalized_code, raw_code, normalized_code)
            )
            row = cursor.fetchone()

            if row:
                # الحصول على أسماء الأعمدة
                cursor.execute('PRAGMA table_info(colors)')
                columns = [col[1] for col in cursor.fetchall()]
                color_obj = self._get_color_from_row(row, columns)
                cache_manager.set(cache_key, color_obj)
                return color_obj
            return None

        except Exception as e:
            raise Exception(f"Failed to get color: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_all_colors(self):
        """الحصول على جميع الألوان"""
        conn = None
        try:
            cache_key = self._cache_key("all_colors")
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return cached

            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                           SELECT id,
                                  code,
                                  name,
                                  dye_type,
                                  supplier,
                                  price_kg,
                                  resa_percent,
                                  created_at,
                                  updated_at
                           FROM colors
                           ORDER BY code
                           """)

            colors = []
            for row in cursor.fetchall():
                color = Color(
                    id=row[0],
                    code=row[1],
                    name=row[2],
                    dye_type=row[3],
                    supplier=row[4],
                    price_kg=row[5],
                    resa_percent=row[6],
                    created_at=row[7],
                    updated_at=row[8]
                )
                colors.append(color)

            cache_manager.set(cache_key, colors)
            return colors

        except sqlite3.Error as e:
            raise Exception(f"Error in get_all_colors: {str(e)}")
        finally:
            if conn:
                conn.close()

    def search_colors(self, code_filter: str = "", name_filter: str = "",
                      type_filter: str = "") -> List[Color]:
        """بحث الألوان"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM colors WHERE 1=1"
            params = []

            if code_filter:
                query += " AND code LIKE ?"
                params.append(f"%{code_filter}%")

            if name_filter:
                query += " AND name LIKE ?"
                params.append(f"%{name_filter}%")

            if type_filter:
                query += " AND dye_type = ?"
                params.append(type_filter)

            query += " ORDER BY code"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # الحصول على أسماء الأعمدة
            cursor.execute('PRAGMA table_info(colors)')
            columns = [col[1] for col in cursor.fetchall()]

            colors = []
            for row in rows:
                colors.append(self._get_color_from_row(row, columns))

            return colors

        except Exception as e:
            raise Exception(f"Failed to search colors: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_colors_count(self) -> int:
        """عدد الألوان"""
        conn = None
        try:
            cache_key = self._cache_key("colors_count")
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return int(cached)

            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM colors')
            count = cursor.fetchone()[0]
            cache_manager.set(cache_key, int(count))
            return count

        except Exception:
            return 0
        finally:
            if conn:
                conn.close()

    # ============ دوال الريتشتات ============

    def add_recipe(self, recipe: Recipe, colors_data: List[Dict], chemicals: List = None) -> int:
        """إضافة ريتشت جديد مع حفظ الكيماويات المحسوبة"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # حساب إجمالي النسبة المئوية
            if not colors_data:
                raise Exception("Recipe must contain at least one color")

            resolved_colors = []
            missing_codes = []
            for color_data in colors_data:
                code = str(color_data.get('code', '')).strip()
                if not code:
                    missing_codes.append("<empty>")
                    continue

                cursor.execute('SELECT id FROM colors WHERE code = ?', (code,))
                color_row = cursor.fetchone()
                if not color_row:
                    missing_codes.append(code)
                    continue

                resolved_colors.append({
                    'color_id': color_row[0],
                    'percentage': float(color_data.get('percentage', 0))
                })

            if missing_codes:
                unique_missing = sorted(set(missing_codes))
                raise Exception(
                    "Cannot save recipe. Unregistered color code(s): "
                    + ", ".join(unique_missing)
                )

            if not resolved_colors:
                raise Exception("Recipe must contain at least one valid color")

            total_percentage = sum(item['percentage'] for item in resolved_colors)

            # إضافة الريتشت مع الأعمدة الجديدة
            cursor.execute('''
                           INSERT INTO recipes (recipe_code, name, colors_count, total_percentage, created_at)
                           VALUES (?, ?, ?, ?, ?)
                           ''',
                           (recipe.recipe_code, recipe.name, len(resolved_colors), total_percentage, recipe.created_at))

            recipe_id = cursor.lastrowid

            # إضافة الألوان المرتبطة
            for item in resolved_colors:
                cursor.execute('''
                               INSERT INTO recipe_colors (recipe_id, color_id, percentage)
                               VALUES (?, ?, ?)
                               ''', (recipe_id, item['color_id'], item['percentage']))

            # إضافة الكيماويات المحسوبة إذا كانت متوفرة
            if chemicals:
                for chemical in chemicals:
                    # التعامل مع كائنات Chemical أو dictionaries
                    if isinstance(chemical, dict):
                        code = chemical.get('code', '')
                        name = chemical.get('name', '')
                        quantity = chemical.get('quantity', 0)
                        unit = chemical.get('unit', '')
                    else:
                        # كائن Chemical
                        code = getattr(chemical, 'code', '')
                        name = getattr(chemical, 'name', '')
                        quantity = getattr(chemical, 'quantity', 0)
                        unit = getattr(chemical, 'unit', '')

                    cursor.execute('''
                                   INSERT INTO recipe_chemicals (recipe_id, code, name, quantity, unit)
                                   VALUES (?, ?, ?, ?, ?)
                                   ''', (recipe_id, code, name, quantity, unit))

            conn.commit()
            self._invalidate_read_cache()
            return recipe_id

        except sqlite3.IntegrityError as e:
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            raise Exception(f"Recipe code '{recipe.recipe_code}' already exists")
        except Exception as e:
            try:
                if conn:
                    conn.rollback()
            except Exception:
                pass
            raise Exception(f"Failed to add recipe: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_recipe_by_id(self, recipe_id: int) -> Optional[Recipe]:
        """الحصول على ريتشت بواسطة ID"""
        conn = None
        try:
            cache_key = self._cache_key("recipe_by_id", recipe_id)
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return cached

            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM recipes WHERE id = ?', (recipe_id,))
            row = cursor.fetchone()

            if row:
                recipe_obj = Recipe(
                    id=row[0],
                    recipe_code=row[1],
                    name=row[2],
                    created_at=row[3]
                )
                cache_manager.set(cache_key, recipe_obj)
                return recipe_obj
            return None

        except Exception as e:
            raise Exception(f"Failed to get recipe: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_recipe_by_code(self, recipe_code: str) -> Optional[Recipe]:
        """الحصول على ريتشت بواسطة الكود"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM recipes WHERE recipe_code = ?', (recipe_code,))
            row = cursor.fetchone()

            if row:
                return Recipe(
                    id=row[0],
                    recipe_code=row[1],
                    name=row[2],
                    created_at=row[3]
                )
            return None

        except Exception as e:
            raise Exception(f"Failed to get recipe: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_all_recipes(self) -> List[Recipe]:
        """الحصول على جميع الريتشتات"""
        conn = None
        try:
            cache_key = self._cache_key("all_recipes")
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return cached

            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM recipes ORDER BY created_at DESC')
            rows = cursor.fetchall()

            recipes = []
            for row in rows:
                recipes.append(Recipe(
                    id=row[0],
                    recipe_code=row[1],
                    name=row[2],
                    created_at=row[3]
                ))

            cache_manager.set(cache_key, recipes)
            return recipes

        except Exception as e:
            raise Exception(f"Failed to get recipes: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_recipes_using_color(self, color_code: str) -> List[Recipe]:
        """Calls the color manager to get all recipes using a specific color."""
        return self.color_manager.get_recipes_using_color(color_code)

    def get_recipe_details(self, recipe_id: int) -> dict:
        """الحصول على تفاصيل الوصفة مع ألوانها"""
        conn = None
        try:
            cache_key = self._cache_key("recipe_details", recipe_id)
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return cached

            conn = self.get_connection()
            cursor = conn.cursor()

            # الحصول على معلومات الوصفة
            cursor.execute("""
                           SELECT id,
                                  recipe_code,
                                  name,
                                  created_at,
                                  -- عدد الألوان
                                  (SELECT COUNT(*) FROM recipe_colors rc WHERE rc.recipe_id = r.id)        as colors_count,
                                  -- إجمالي النسبة المئوية للألوان
                                  (SELECT SUM(rc.percentage) FROM recipe_colors rc WHERE rc.recipe_id = r.id) as total_percentage
                           FROM recipes r
                           WHERE r.id = ?
                           """, (recipe_id,))

            recipe_row = cursor.fetchone()

            if not recipe_row:
                conn.close()
                return None

            # تحويل الصف إلى قاموس
            recipe_dict = {
                'id': recipe_row[0],
                'recipe_code': recipe_row[1],
                'name': recipe_row[2],
                'created_at': recipe_row[3],
                'colors_count': recipe_row[4],
                'total_percentage': recipe_row[5] if recipe_row[5] is not None else 0.0
            }

            # الحصول على ألوان الوصفة
            cursor.execute("""
                           SELECT c.id,
                                  c.code,
                                  c.name,
                                  c.dye_type,
                                  c.supplier,
                                  c.price_kg,
                                  c.resa_percent,
                                  rc.percentage
                           FROM recipe_colors rc
                                    JOIN colors c ON rc.color_id = c.id
                           WHERE rc.recipe_id = ?
                           ORDER BY rc.percentage DESC
                           """, (recipe_id,))

            colors = []
            total_cost = 0.0

            for row in cursor.fetchall():
                price_kg = row[5] if row[5] is not None else 0.0
                resa_percent = row[6] if row[6] is not None else 0.0
                color_data = {
                    'id': row[0],
                    'code': row[1],
                    'name': row[2],
                    'dye_type': row[3],
                    'supplier': row[4],
                    'price_kg': price_kg,
                    'resa_percent': resa_percent,
                    'percentage': row[7]
                }

                # حساب تكلفة هذا اللون في الوصفة
                color_cost = (color_data['percentage'] / 100) * price_kg
                total_cost += color_cost

                colors.append(color_data)

            # إضافة التكلفة الإجمالية
            recipe_dict['total_cost'] = total_cost

            # الحصول على الكيماويات المحفوظة
            cursor.execute("""
                           SELECT code, name, quantity, unit
                           FROM recipe_chemicals
                           WHERE recipe_id = ?
                           """, (recipe_id,))

            chemicals = []
            for row in cursor.fetchall():
                chem_row = {'code': row[0], 'name': row[1], 'quantity': row[2], 'unit': row[3]}
                chemicals.append(Chemical(
                    code=chem_row['code'],
                    name=chem_row['name'],
                    quantity=chem_row['quantity'],
                    unit=chem_row['unit']
                ))

            # إذا لم توجد كيماويات محفوظة (وصفات قديمة)، احسبها من جديد
            if not chemicals:
                from app.calculator import ChemicalCalculator
                total_percentage = recipe_dict.get('total_percentage', 0.0) or 0.0
                
                # تحديد النوع المهيمن من الألوان
                type_totals = {}
                for color in colors:
                    dye_type = color.get('dye_type', '')
                    type_totals[dye_type] = type_totals.get(dye_type, 0) + color.get('percentage', 0)
                
                dominant_type = max(type_totals, key=type_totals.get) if type_totals else 'GENERAL'
                chemicals = ChemicalCalculator.calculate_chemicals(total_percentage, dominant_type)

            conn.close()

            result = {
                'recipe': Recipe(
                    id=recipe_dict['id'],
                    recipe_code=recipe_dict['recipe_code'],
                    name=recipe_dict['name'],
                    created_at=recipe_dict['created_at']
                ),
                'colors': colors,
                'chemicals': chemicals,
                'colors_count': recipe_dict.get('colors_count', 0),
                'total_percentage': recipe_dict.get('total_percentage', 0.0) or 0.0,
                'total_cost': total_cost
            }
            cache_manager.set(cache_key, result)
            return result

        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()

    def delete_recipe(self, recipe_id: int) -> bool:
        """حذف ريتشت"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # حذف الكيماويات المرتبطة بالوصفة
            cursor.execute('DELETE FROM recipe_chemicals WHERE recipe_id = ?', (recipe_id,))

            # حذف الألوان المرتبطة بالوصفة
            cursor.execute('DELETE FROM recipe_colors WHERE recipe_id = ?', (recipe_id,))

            cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))
            affected = cursor.rowcount
            conn.commit()
            if affected > 0:
                self._invalidate_read_cache()
            return affected > 0

        except Exception as e:
            raise Exception(f"Failed to delete recipe: {str(e)}")
        finally:
            if conn:
                conn.close()

    def delete_color_and_associated_recipes(self, color_id: int, recipe_ids: List[int]) -> bool:
        """Deletes a color and all specified recipes in a single transaction."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Delete each recipe
            for recipe_id in recipe_ids:
                cursor.execute('DELETE FROM recipe_chemicals WHERE recipe_id = ?', (recipe_id,))
                cursor.execute('DELETE FROM recipe_colors WHERE recipe_id = ?', (recipe_id,))
                cursor.execute('DELETE FROM recipes WHERE id = ?', (recipe_id,))

            # Delete the color itself (and any remaining recipe_colors links, just in case)
            cursor.execute('DELETE FROM recipe_colors WHERE color_id = ?', (color_id,))
            cursor.execute('DELETE FROM colors WHERE id = ?', (color_id,))
            
            conn.commit()
            self._invalidate_read_cache()
            return True

        except Exception as e:
            if conn:
                conn.rollback()
            raise Exception(f"Failed to perform cascading delete: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_recipes_count(self) -> int:
        """عدد الريتشتات"""
        conn = None
        try:
            cache_key = self._cache_key("recipes_count")
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return int(cached)

            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM recipes')
            count = cursor.fetchone()[0]
            cache_manager.set(cache_key, int(count))
            return count

        except Exception:
            return 0
        finally:
            if conn:
                conn.close()

    # ============ دوال إحصائية ============

    def get_recipe_statistics(self) -> Dict:
        """إحصائيات الريتشتات"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # عدد الريتشتات
            cursor.execute('SELECT COUNT(*) FROM recipes')
            total_recipes = cursor.fetchone()[0]

            # عدد الألوان المستخدمة
            cursor.execute('SELECT COUNT(DISTINCT color_id) FROM recipe_colors')
            total_colors_used = cursor.fetchone()[0]

            # متوسط عدد الألوان لكل ريتشت
            cursor.execute('''
                SELECT AVG(color_count) 
                FROM (
                    SELECT recipe_id, COUNT(*) as color_count 
                    FROM recipe_colors 
                    GROUP BY recipe_id
                )
            ''')
            avg_colors_per_recipe = cursor.fetchone()[0] or 0

            # أحدث الريتشتات
            cursor.execute('''
                SELECT id, name, created_at 
                FROM recipes 
                ORDER BY created_at DESC 
                LIMIT 5
            ''')
            recent_recipes = cursor.fetchall()

            return {
                "total_recipes": total_recipes,
                "total_colors_used": total_colors_used,
                "avg_colors_per_recipe": round(avg_colors_per_recipe, 1),
                "recent_recipes": recent_recipes
            }

        except Exception as e:
            raise Exception(f"Failed to get statistics: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_color_statistics(self) -> Dict:
        """إحصائيات الألوان"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # عدد الألوان حسب النوع
            cursor.execute('''
                SELECT dye_type, COUNT(*) as count
                FROM colors
                GROUP BY dye_type
                ORDER BY count DESC
            ''')
            colors_by_type = cursor.fetchall()

            # الألوان الأكثر استخداماً
            cursor.execute('''
                SELECT c.code, c.name, c.dye_type, COUNT(rc.recipe_id) as usage_count
                FROM colors c
                LEFT JOIN recipe_colors rc ON c.id = rc.color_id
                GROUP BY c.id
                ORDER BY usage_count DESC
                LIMIT 10
            ''')
            most_used_colors = cursor.fetchall()

            return {
                "colors_by_type": colors_by_type,
                "most_used_colors": most_used_colors
            }

        except Exception as e:
            raise Exception(f"Failed to get color statistics: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_colors_in_use(self) -> Dict:
        """الحصول على الألوان المستخدمة في الريتشتات"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # الحصول على جميع الألوان المستخدمة مع تفاصيلها
            cursor.execute('''
                SELECT DISTINCT c.id, c.code, c.name, c.dye_type, c.supplier, c.price_kg
                FROM colors c
                INNER JOIN recipe_colors rc ON c.id = rc.color_id
                ORDER BY c.code
            ''')
            color_rows = cursor.fetchall()

            color_usage = {}

            for color_row in color_rows:
                color_id = color_row[0]
                color_code = color_row[1]

                # الحصول على الريتشتات التي تستخدم هذا اللون
                cursor.execute('''
                    SELECT r.id, r.recipe_code, r.name, rc.percentage
                    FROM recipes r
                    INNER JOIN recipe_colors rc ON r.id = rc.recipe_id
                    WHERE rc.color_id = ?
                    ORDER BY r.recipe_code
                ''', (color_id,))
                recipe_rows = cursor.fetchall()

                recipes_list = []
                total_percentage = 0.0

                for recipe_row in recipe_rows:
                    recipes_list.append({
                        'recipe_id': recipe_row[0],
                        'recipe_code': recipe_row[1],
                        'recipe_name': recipe_row[2],
                        'percentage': recipe_row[3]
                    })
                    total_percentage += recipe_row[3]

                color_usage[color_code] = {
                    'color_info': {
                        'name': color_row[2],
                        'dye_type': color_row[3],
                        'supplier': color_row[4] or '',
                        'price_kg': color_row[5] or 0.0
                    },
                    'recipes': recipes_list,
                    'total_recipes': len(recipes_list),
                    'total_percentage': total_percentage
                }

            return color_usage

        except Exception as e:
            raise Exception(f"Failed to get colors in use: {str(e)}")
        finally:
            if conn:
                conn.close()

    def backup_database(self, once_per_day: bool = False, always_latest: bool = False) -> Optional[str]:
        """إنشاء نسخة احتياطية من قاعدة البيانات.

        once_per_day: نسخة تاريخية مرة واحدة يومياً.
        always_latest: نسخ إلى DyeMasterPro_Backup_Latest.db في كل استدعاء (استبدال دائم).
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            day_stamp = datetime.now().strftime("%Y%m%d")
            backup_dir = BACKUP_DIR

            # التأكد من وجود مجلد النسخ الاحتياطية
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)

            backup_files = []

            # نسخ ملف النسخة الأخيرة دائماً
            if always_latest:
                latest_path = os.path.join(backup_dir, "DyeMasterPro_Backup_Latest.db")
                shutil.copy2(self.db_file, latest_path)
                backup_files.append(latest_path)

            # نسخة يومية مرة واحدة
            if once_per_day:
                daily_file = os.path.join(backup_dir, f"DyeMasterPro_Backup_{day_stamp}.db")
                if not os.path.exists(daily_file):
                    shutil.copy2(self.db_file, daily_file)
                    backup_files.append(daily_file)

            # افتراضي: حفظ نسخة مؤرخة (سابقاً)
            if not once_per_day and not always_latest:
                archive_file = os.path.join(backup_dir, f"DyeMasterPro_Backup_{timestamp}.db")
                shutil.copy2(self.db_file, archive_file)
                backup_files.append(archive_file)

            if backup_files:
                return backup_files[-1]
            return None

        except Exception as e:
            raise Exception(f"Failed to backup database: {str(e)}")

    def restore_database(self, backup_file: str) -> bool:
        """استعادة قاعدة البيانات من ملف نسخة احتياطية"""
        try:
            if not backup_file or not os.path.isfile(backup_file):
                raise FileNotFoundError(f"Backup file not found: {backup_file}")

            os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
            shutil.copy2(backup_file, self.db_file)

            # تأكيد أن الملف الجديد قابل للقراءة
            conn = sqlite3.connect(self.db_file)
            conn.execute("SELECT name FROM sqlite_master LIMIT 1")
            conn.close()
            return True
        except Exception as e:
            raise Exception(f"Failed to restore database: {str(e)}")

    # ============ دوال Pagination ============

    def get_colors_paginated(self, page: int = 1, per_page: int = 10) -> Dict:
        """الحصول على الألوان بصيغة مقسمة (Pagination)"""
        try:
            from app.cache import PaginationHelper
            all_colors = self.get_all_colors()
            return PaginationHelper.paginate(all_colors, page, per_page)
        except Exception as e:
            raise Exception(f"Failed to get paginated colors: {str(e)}")

    def get_recipes_paginated(self, page: int = 1, per_page: int = 10) -> Dict:
        """الحصول على الوصفات بصيغة مقسمة"""
        try:
            from app.cache import PaginationHelper
            all_recipes = self.get_all_recipes()
            return PaginationHelper.paginate(all_recipes, page, per_page)
        except Exception as e:
            raise Exception(f"Failed to get paginated recipes: {str(e)}")

    # ============ دوال البحث المتقدم ============

    def advanced_search_colors(self, 
                             code: str = "", 
                             name: str = "", 
                             dye_type: str = "",
                             supplier: str = "",
                             price_min: float = 0,
                             price_max: float = float('inf'),
                             page: int = 1,
                             per_page: int = 10) -> Dict:
        """
        بحث متقدم عن الألوان مع عدة فلاتر
        """
        from app.cache import PaginationHelper
        conn = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM colors WHERE 1=1"
            params = []
            
            if code:
                query += " AND code LIKE ?"
                params.append(f"%{code}%")
            
            if name:
                query += " AND name LIKE ?"
                params.append(f"%{name}%")
            
            if dye_type:
                query += " AND dye_type = ?"
                params.append(dye_type)
            
            if supplier:
                query += " AND supplier LIKE ?"
                params.append(f"%{supplier}%")
            
            if price_min > 0:
                query += " AND price_kg >= ?"
                params.append(price_min)
            
            if price_max < float('inf'):
                query += " AND price_kg <= ?"
                params.append(price_max)
            
            query += " ORDER BY code ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # تحويل النتائج إلى كائنات Color
            colors = []
            for row in rows:
                color = Color(
                    id=row[0],
                    code=row[1],
                    name=row[2],
                    dye_type=row[3],
                    supplier=row[4] or '',
                    price_kg=row[5] or 0.0,
                    resa_percent=row[6] or 0.0,
                    created_at=row[7] or '',
                    updated_at=row[8] or ''
                )
                colors.append(color)
            
            # تطبيق Pagination
            result = PaginationHelper.paginate(colors, page, per_page)
            result['total_results'] = len(colors)
            result['filters_applied'] = {
                'code': code,
                'name': name,
                'dye_type': dye_type,
                'supplier': supplier,
                'price_range': f"{price_min}-{price_max}"
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Advanced search failed: {str(e)}")
        finally:
            if conn:
                conn.close()

    def advanced_search_recipes(self,
                               recipe_code: str = "",
                               name: str = "",
                               dye_type: str = "",
                               page: int = 1,
                               per_page: int = 10) -> Dict:
        """
        بحث متقدم عن الوصفات مع فلاتر متعددة
        """
        from app.cache import PaginationHelper
        conn = None
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT r.* FROM recipes r
                WHERE 1=1
            """
            params = []
            
            if recipe_code:
                query += " AND r.recipe_code LIKE ?"
                params.append(f"%{recipe_code}%")
            
            if name:
                query += " AND r.name LIKE ?"
                params.append(f"%{name}%")
            
            if dye_type:
                # البحث عن الوصفات التي تحتوي على هذا النوع من الصباغة
                query += """
                    AND r.id IN (
                        SELECT DISTINCT rc.recipe_id FROM recipe_colors rc
                        JOIN colors c ON rc.color_id = c.id
                        WHERE c.dye_type = ?
                    )
                """
                params.append(dye_type)
            
            query += " ORDER BY r.created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # تحويل النتائج إلى كائنات Recipe
            recipes = []
            for row in rows:
                recipe = Recipe(
                    id=row[0],
                    recipe_code=row[1],
                    name=row[2],
                    created_at=row[3]
                )
                recipes.append(recipe)
            
            # تطبيق Pagination
            result = PaginationHelper.paginate(recipes, page, per_page)
            result['total_results'] = len(recipes)
            result['filters_applied'] = {
                'recipe_code': recipe_code,
                'name': name,
                'dye_type': dye_type
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"Advanced recipe search failed: {str(e)}")
        finally:
            if conn:
                conn.close()

    def search_recipes(self, recipe_code_filter: str = "", name_filter: str = "") -> List[Recipe]:
        """بحث بسيط في الوصفات بالكود والاسم."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            query = "SELECT id, recipe_code, name, created_at FROM recipes WHERE 1=1"
            params = []

            if recipe_code_filter:
                query += " AND recipe_code LIKE ?"
                params.append(f"%{recipe_code_filter}%")

            if name_filter:
                query += " AND name LIKE ?"
                params.append(f"%{name_filter}%")

            query += " ORDER BY created_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                Recipe(
                    id=row[0],
                    recipe_code=row[1],
                    name=row[2],
                    created_at=row[3] or ""
                )
                for row in rows
            ]
        except Exception as e:
            raise Exception(f"Failed to search recipes: {str(e)}")
        finally:
            if conn:
                conn.close()

    def get_recipe_colors_count(self, recipe_id: int) -> int:
        """عدد الألوان داخل وصفة واحدة."""
        conn = None
        try:
            cache_key = self._cache_key("recipe_colors_count", recipe_id)
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return int(cached)

            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM recipe_colors WHERE recipe_id = ?", (recipe_id,))
            count = int(cursor.fetchone()[0] or 0)
            cache_manager.set(cache_key, count)
            return count
        except Exception:
            return 0
        finally:
            if conn:
                conn.close()

    def get_recipe_total_percentage(self, recipe_id: int) -> float:
        """إجمالي نسبة الألوان داخل وصفة واحدة."""
        conn = None
        try:
            cache_key = self._cache_key("recipe_total_percentage", recipe_id)
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return float(cached)

            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(percentage) FROM recipe_colors WHERE recipe_id = ?", (recipe_id,))
            value = cursor.fetchone()[0]
            result = float(value or 0.0)
            cache_manager.set(cache_key, result)
            return result
        except Exception:
            return 0.0
        finally:
            if conn:
                conn.close()

    def get_cache_stats(self) -> Dict:
        """الحصول على إحصائيات الـ Cache"""
        return cache_manager.get_stats()

    def clear_cache(self):
        """مسح الـ Cache"""
        cache_manager.clear()

    def cleanup_expired_cache(self):
        """تنظيف عناصر الـ Cache المنتهية الصلاحية"""
        cache_manager.cleanup_expired()
