"""
موديول الاختبار الشامل للنظام
"""
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import tempfile
from datetime import datetime
import sys
import traceback

# استيراد مكونات النظام
from app.database import DatabaseManager
from app.calculator import ChemicalCalculator, CostCalculator
from app.pdf_exporter import PDFExporter
from app.models import Color, Recipe, Chemical
from app.utils import (
    clean_recipe_code,
    format_currency,
    format_percentage,
    get_current_timestamp,
    validate_recipe_code_input,
)


def _configure_stdout_for_unicode() -> None:
    """Avoid UnicodeEncodeError on Windows terminals with cp1252 default encoding."""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


_configure_stdout_for_unicode()


class SystemTester:
    """مختبر النظام الشامل"""

    def __init__(self, parent=None):
        self.parent = parent
        self.test_db_file = os.path.join(tempfile.gettempdir(), "dyemasterpro_test.db")
        self._reset_test_database()
        self.db = DatabaseManager(self.test_db_file)
        self.test_results = []
        self.errors = []

    def _reset_test_database(self):
        """Ensure tests run against a fresh writable DB, isolated from user data."""
        for suffix in ("", "-wal", "-shm"):
            test_file = f"{self.test_db_file}{suffix}"
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except Exception:
                    pass

    def run_full_test_suite(self):
        """تشغيل جميع الاختبارات"""
        print("=" * 60)
        print("🚀 بدء الاختبار الشامل لنظام DyeMaster Pro")
        print("=" * 60)

        self.test_results.clear()
        self.errors.clear()

        # قائمة الاختبارات
        tests = [
            ("اختبار اتصال قاعدة البيانات", self.test_database_connection),
            ("اختبار إنشاء جداول قاعدة البيانات", self.test_database_tables),
            ("اختبار إضافة/حذف/تعديل الألوان", self.test_colors_crud),
            ("اختبار إضافة/حذف الوصفات", self.test_recipes_crud),
            ("اختبار حساب الكيماويات", self.test_chemical_calculations),
            ("اختبار حساب التكاليف", self.test_cost_calculations),
            ("اختبار الدوال المساعدة", self.test_utility_functions),
            ("اختبار تصدير PDF", self.test_pdf_export),
            ("اختبار البحث والفلترة", self.test_search_functions),
            ("اختبار واجهة المستخدم الأساسية", self.test_basic_ui)
        ]

        # تشغيل جميع الاختبارات
        for test_name, test_func in tests:
            try:
                print(f"\n🔍 تشغيل: {test_name}")
                result = test_func()
                if result:
                    self.test_results.append((test_name, "✅ نجح"))
                    print(f"   ✅ {test_name} - نجح")
                else:
                    self.test_results.append((test_name, "❌ فشل"))
                    print(f"   ❌ {test_name} - فشل")
            except Exception as e:
                self.test_results.append((test_name, f"❌ خطأ: {str(e)}"))
                self.errors.append((test_name, str(e), traceback.format_exc()))
                print(f"   💥 {test_name} - خطأ: {str(e)}")

        # عرض النتائج وإرجاع الحالة الحقيقية (نجاح/فشل)
        return self.display_results()

    def test_database_connection(self):
        """اختبار اتصال قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()

            # اختبار الاستعلام البسيط
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            conn.close()

            if tables:
                print(f"   📊 عدد الجداول: {len(tables)}")
                return True
            return False

        except Exception as e:
            print(f"   💥 خطأ في اتصال قاعدة البيانات: {e}")
            return False

    def test_database_tables(self):
        """اختبار إنشاء الجداول"""
        try:
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()

            # التحقق من وجود الجداول الأساسية
            required_tables = ['colors', 'recipes', 'recipe_colors']
            existing_tables = []

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            for table in tables:
                existing_tables.append(table[0])

            conn.close()

            # التحقق من وجود جميع الجداول المطلوبة
            missing_tables = []
            for table in required_tables:
                if table not in existing_tables:
                    missing_tables.append(table)

            if missing_tables:
                print(f"   ⚠️ الجداول الناقصة: {missing_tables}")
                return False

            print(f"   📋 الجداول الموجودة: {existing_tables}")
            return True

        except Exception as e:
            print(f"   💥 خطأ في جداول قاعدة البيانات: {e}")
            return False

    def test_colors_crud(self):
        """اختبار عمليات CRUD على الألوان"""
        try:
            # اختبار الإضافة
            test_color = Color(
                id=0,
                code="TEST001",
                name="Test Color Red",
                dye_type="INDANTHREN",
                supplier="Test Supplier",
                price_kg=45.50,
                resa_percent=2.5,
                created_at=get_current_timestamp(),
                updated_at=get_current_timestamp()
            )

            # إضافة لون اختبار
            color_id = self.db.add_color(test_color)

            if color_id <= 0:
                print("   ❌ فشل إضافة اللون")
                return False

            print(f"   ➕ تم إضافة لون اختبار (ID: {color_id})")

            # اختبار القراءة
            retrieved_color = self.db.get_color_by_code("TEST001")
            if not retrieved_color or retrieved_color.name != "Test Color Red":
                print("   ❌ فشل قراءة اللون")
                self.db.delete_color(color_id)
                return False

            print("   👁️ تم قراءة اللون بنجاح")

            # اختبار التعديل
            updated_color = Color(
                id=color_id,
                code="TEST001",
                name="Test Color Blue",
                dye_type="INDANTHREN",
                supplier="Test Supplier Updated",
                price_kg=50.00,
                resa_percent=3.0,
                created_at=retrieved_color.created_at,
                updated_at=get_current_timestamp()
            )

            success = self.db.update_color(updated_color)
            if not success:
                print("   ❌ فشل تعديل اللون")
                self.db.delete_color(color_id)
                return False

            print("   ✏️ تم تعديل اللون بنجاح")

            # اختبار الحذف
            self.db.delete_color(color_id)

            # التحقق من الحذف
            deleted_color = self.db.get_color_by_code("TEST001")
            if deleted_color:
                print("   ❌ فشل حذف اللون")
                return False

            print("   🗑️ تم حذف اللون بنجاح")
            return True

        except Exception as e:
            print(f"   💥 خطأ في اختبار الألوان: {e}")
            # تنظيف في حالة الخطأ
            try:
                color_to_delete = self.db.get_color_by_code("TEST001")
                if color_to_delete:
                    self.db.delete_color(color_to_delete.id)
            except:
                pass
            return False

    def test_recipes_crud(self):
        """اختبار عمليات CRUD على الوصفات - نسخة محسنة"""
        try:
            # أولاً: تنظيف كامل لبيانات الاختبار القديمة
            self.cleanup_test_data()

            import time
            timestamp = str(int(time.time()))[-6:]  # الحصول على جزء من timestamp

            # إنشاء أكواد فريدة
            color1_code = f"TCOL1_{timestamp}"
            color2_code = f"TCOL2_{timestamp}"
            recipe_code = f"TREC_{timestamp}"

            # 1. اختبار إنشاء الألوان
            color1 = Color(
                id=0,
                code=color1_code,
                name=f"Test Color 1_{timestamp}",
                dye_type="INDANTHREN",
                supplier="Test Supplier",
                price_kg=40.0,
                resa_percent=2.0,
                created_at=get_current_timestamp(),
                updated_at=get_current_timestamp()
            )

            color2 = Color(
                id=0,
                code=color2_code,
                name=f"Test Color 2_{timestamp}",
                dye_type="REATTIVI CALDI",
                supplier="Test Supplier",
                price_kg=35.0,
                resa_percent=1.5,
                created_at=get_current_timestamp(),
                updated_at=get_current_timestamp()
            )

            color1_id = self.db.add_color(color1)
            color2_id = self.db.add_color(color2)

            if color1_id <= 0 or color2_id <= 0:
                print("   ❌ فشل إنشاء ألوان الاختبار")
                return False

            print(f"   ➕ تم إنشاء ألوان اختبار (IDs: {color1_id}, {color2_id})")

            # 2. اختبار إنشاء الوصفة
            test_recipe = Recipe(
                id=0,
                recipe_code=recipe_code,
                name=f"Test Recipe {timestamp}",
                created_at=get_current_timestamp()
            )

            selected_colors = [
                {
                    "id": color1_id,
                    "code": color1_code,
                    "name": color1.name,
                    "dye_type": color1.dye_type,
                    "price_kg": color1.price_kg,
                    "percentage": 1.5
                },
                {
                    "id": color2_id,
                    "code": color2_code,
                    "name": color2.name,
                    "dye_type": color2.dye_type,
                    "price_kg": color2.price_kg,
                    "percentage": 2.0
                }
            ]

            # حساب الكيماويات للاختبار
            total_percentage = sum(c.get('percentage', 0) for c in selected_colors)
            type_totals = {}
            for color in selected_colors:
                dye_type = color.get('dye_type', '')
                type_totals[dye_type] = type_totals.get(dye_type, 0) + color.get('percentage', 0)
            dominant_type = max(type_totals, key=type_totals.get) if type_totals else 'GENERAL'
            chemicals = ChemicalCalculator.calculate_chemicals(total_percentage, dominant_type)

            recipe_id = self.db.add_recipe(test_recipe, selected_colors, chemicals)

            if recipe_id <= 0:
                print("   ❌ فشل إضافة الوصفة")
                return False

            print(f"   ➕ تم إضافة وصفة اختبار (ID: {recipe_id})")

            # 3. اختبار قراءة الوصفة
            recipe_details = self.db.get_recipe_details(recipe_id)
            if not recipe_details:
                print("   ❌ فشل قراءة تفاصيل الوصفة")
                return False

            print("   👁️ تم قراءة تفاصيل الوصفة بنجاح")
            print(f"   ℹ️ عدد الألوان في الوصفة: {len(recipe_details['colors'])}")
            print(f"   ℹ️ التكلفة الإجمالية: €{recipe_details['total_cost']:.2f}")

            # 4. اختبار الحذف
            print("   🗑️ جاري حذف الوصفة...")
            self.db.delete_recipe(recipe_id)

            # التحقق من الحذف
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM recipes WHERE id = ?", (recipe_id,))
            recipe_exists = cursor.fetchone()[0] > 0

            # التحقق من حذف الألوان المرتبطة
            cursor.execute("SELECT COUNT(*) FROM recipe_colors WHERE recipe_id = ?", (recipe_id,))
            colors_exist = cursor.fetchone()[0] > 0

            conn.close()

            if recipe_exists:
                print("   ❌ فشل حذف الوصفة (السجل الرئيسي)")
                return False
                
            if colors_exist:
                print("   ❌ فشل حذف الوصفة (لم يتم حذف الألوان المرتبطة)")
                return False

            print("   ✅ تم حذف الوصفة بنجاح")

            # 5. حذف الألوان
            print("   🗑️ جاري حذف ألوان الاختبار...")

            # حذف باستخدام الكود بدلاً من الـ ID (أكثر أماناً)
            color1_to_delete = self.db.get_color_by_code(color1_code)
            color2_to_delete = self.db.get_color_by_code(color2_code)

            if color1_to_delete:
                self.db.delete_color(color1_to_delete.id)
                print(f"   ✅ تم حذف اللون: {color1_code}")

            if color2_to_delete:
                self.db.delete_color(color2_to_delete.id)
                print(f"   ✅ تم حذف اللون: {color2_code}")

            # التحقق النهائي
            final_check1 = self.db.get_color_by_code(color1_code)
            final_check2 = self.db.get_color_by_code(color2_code)

            if final_check1 or final_check2:
                print("   ⚠️ بعض ألوان الاختبار لا تزال موجودة")
                return False

            print("   ✅ تم تنظيف جميع بيانات الاختبار بنجاح")
            return True

        except Exception as e:
            print(f"   💥 خطأ في اختبار الوصفات: {e}")
            import traceback
            traceback.print_exc()

            # محاولة تنظيف في حالة الخطأ
            try:
                self.cleanup_test_data()
            except:
                pass

            return False

    def cleanup_test_data(self):
        """تنظيف جميع بيانات الاختبار"""
        try:
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()

            # 1. حذف أي وصفات اختبارية
            cursor.execute("SELECT id, recipe_code FROM recipes WHERE recipe_code LIKE '%TEST%'")
            test_recipes = cursor.fetchall()

            for recipe_id, recipe_code in test_recipes:
                print(f"   🗑️ حذف وصفة اختبار: {recipe_code}")
                # حذف أولاً من جدول recipe_colors
                cursor.execute("DELETE FROM recipe_colors WHERE recipe_id = ?", (recipe_id,))
                # ثم حذف الوصفة
                cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))

            # 2. حذف أي ألوان اختبارية
            cursor.execute("SELECT id, code FROM colors WHERE code LIKE '%TEST%' OR code LIKE '%TCOLOR%'")
            test_colors = cursor.fetchall()

            for color_id, color_code in test_colors:
                print(f"   🗑️ حذف لون اختبار: {color_code}")
                cursor.execute("DELETE FROM colors WHERE id = ?", (color_id,))

            conn.commit()
            conn.close()

            print("   ✅ تم تنظيف بيانات الاختبار بنجاح")

        except Exception as e:
            print(f"   ⚠️ خطأ في تنظيف بيانات الاختبار: {e}")

    def cleanup_test_colors(self, color_ids):
        """تنظيف ألوان الاختبار"""
        for color_id in color_ids:
            try:
                # التحقق أولاً من وجود اللون
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM colors WHERE id = ?", (color_id,))
                count = cursor.fetchone()[0]
                conn.close()

                if count > 0:
                    self.db.delete_color(color_id)
                    print(f"   🗑️ تم حذف اللون ID: {color_id}")
                else:
                    print(f"   ℹ️ اللون ID: {color_id} غير موجود (ربما تم حذفه مسبقاً)")

            except Exception as e:
                print(f"   ⚠️ خطأ في حذف اللون {color_id}: {e}")

    def cleanup_test_recipe(self, recipe_id, color_ids):
        """تنظيف وصفة الاختبار"""
        try:
            self.db.delete_recipe(recipe_id)
            self.cleanup_test_colors(color_ids)
        except:
            pass

    def test_chemical_calculations(self):
        """اختبار حسابات الكيماويات"""
        try:
            # اختبار حساب كيماويات INDANTHREN
            chemicals_ind = ChemicalCalculator.calculate_chemicals(2.5, "INDANTHREN")
            if not chemicals_ind or len(chemicals_ind) == 0:
                print("   ❌ فشل حساب كيماويات INDANTHREN")
                return False

            print(f"   🧪 كيماويات INDANTHREN: {len(chemicals_ind)} عنصر")

            # اختبار حساب كيماويات REATTIVI CALDI
            chemicals_caldi = ChemicalCalculator.calculate_chemicals(1.8, "REATTIVI CALDI")
            if not chemicals_caldi or len(chemicals_caldi) == 0:
                print("   ❌ فشل حساب كيماويات REATTIVI CALDI")
                return False

            print(f"   🧪 كيماويات REATTIVI CALDI: {len(chemicals_caldi)} عنصر")

            # اختبار حساب كيماويات REATTIVI FREDDI
            chemicals_freddi = ChemicalCalculator.calculate_chemicals(3.2, "REATTIVI FREDDI")
            if not chemicals_freddi or len(chemicals_freddi) == 0:
                print("   ❌ فشل حساب كيماويات REATTIVI FREDDI")
                return False

            print(f"   🧪 كيماويات REATTIVI FREDDI: {len(chemicals_freddi)} عنصر")

            # عرض عينة من الحسابات
            for chem in chemicals_ind[:2]:
                print(f"     - {chem.name}: {chem.quantity} {chem.unit}")

            return True

        except Exception as e:
            print(f"   💥 خطأ في حساب الكيماويات: {e}")
            return False

    def test_cost_calculations(self):
        """اختبار حسابات التكاليف"""
        try:
            # بيانات اختبارية
            test_colors = [
                {"percentage": 1.5, "price_kg": 45.0},
                {"percentage": 2.0, "price_kg": 38.5},
                {"percentage": 0.5, "price_kg": 52.0}
            ]

            # حساب تكلفة الوصفة
            recipe_cost = CostCalculator.calculate_recipe_cost(test_colors)

            if recipe_cost <= 0:
                print("   ❌ فشل حساب تكلفة الوصفة")
                return False

            print(f"   💰 تكلفة الوصفة: €{recipe_cost:.2f}")

            # حساب تكلفة الدفعة
            batch_cost = CostCalculator.calculate_batch_cost(recipe_cost, 50)
            print(f"   📦 تكلفة دفعة 50kg: €{batch_cost:.2f}")

            # حساب مع الهالك
            waste_cost = CostCalculator.calculate_with_waste(recipe_cost, 10)
            print(f"   ♻️  التكلفة مع 10% هالك: €{waste_cost:.2f}")

            return True

        except Exception as e:
            print(f"   💥 خطأ في حساب التكاليف: {e}")
            return False

    def test_utility_functions(self):
        """اختبار الدوال المساعدة"""
        all_passed = True
        try:
            # اختبار clean_recipe_code
            print("   - Testing clean_recipe_code...")
            # Note: The function was fixed to correctly remove non-digits and zfill to 6.
            # The test is now updated to reflect the CORRECT behavior.
            test_codes = {
                " 123 ": "000123",
                "ABC123XYZ": "000123",
                "00123": "000123",
                "12-34-56": "123456",
                " 12 34 56 ": "123456",
                "": "000000", # Empty string becomes all zeros
                "999999": "999999"
            }

            clean_code_passed = True
            for code, expected in test_codes.items():
                cleaned = clean_recipe_code(code)
                if cleaned != expected:
                    print(f"   ⚠️ clean_recipe_code: Input '{code}' -> Actual '{cleaned}', Expected '{expected}'")
                    clean_code_passed = False
            
            if not clean_code_passed:
                all_passed = False
            else:
                print("     ✓ clean_recipe_code works as expected.")

            # اختبار validate_recipe_code_input
            print("   - Testing validate_recipe_code_input...")
            # The validation function is correct. The test expectations were wrong.
            # Correct expectations: code must be exactly 6 digits.
            validation_tests = {
                "123": False,
                "123456": True,
                "1234567": False,
                "abc123": False,
                "": False,
                "123 456": False
            }
            
            validation_passed = True
            for input_val, expected_valid in validation_tests.items():
                valid, message = validate_recipe_code_input(input_val)
                if valid != expected_valid:
                    print(f"   ⚠️ validate_recipe_code_input: Input '{input_val}' -> Actual '{valid}', Expected '{expected_valid}' - Msg: {message}")
                    validation_passed = False
            
            if not validation_passed:
                all_passed = False
            else:
                print("     ✓ validate_recipe_code_input works as expected.")

            # اختبار format_currency
            print("   - Testing format_currency...")
            amount = 45.5
            formatted = format_currency(amount)
            if formatted == "€45.50":
                print("     ✓ format_currency works as expected.")
            else:
                print(f"   ⚠️ format_currency: -> Actual '{formatted}', Expected '€45.50'")
                all_passed = False

            # اختبار format_percentage
            print("   - Testing format_percentage...")
            percent = 2.5
            formatted_percent = format_percentage(percent)
            if formatted_percent == "2.5%":
                 print("     ✓ format_percentage works as expected.")
            else:
                print(f"   ⚠️ format_percentage: -> Actual '{formatted_percent}', Expected '2.5%'")
                all_passed = False

            return all_passed

        except Exception as e:
            print(f"   💥 خطأ في الدوال المساعدة: {e}")
            traceback.print_exc()
            return False

    def test_pdf_export(self):
        """اختبار تصدير PDF"""
        try:
            # إنشاء بيانات اختبارية لـ PDF
            from app.models import Recipe, RecipeDetails

            test_recipe = Recipe(
                id=999,
                recipe_code="TESTPDF001",
                name="Test Recipe for PDF",
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            test_colors = [
                {
                    "code": "TEST001",
                    "name": "Test Color Red",
                    "dye_type": "INDANTHREN",
                    "percentage": 1.5,
                    "price_kg": 45.0
                },
                {
                    "code": "TEST002",
                    "name": "Test Color Blue",
                    "dye_type": "REATTIVI CALDI",
                    "percentage": 2.0,
                    "price_kg": 38.5
                }
            ]

            test_chemicals = [
                Chemical("Caustic Soda", 8.0, "g/l"),
                Chemical("Hydrosulfite", 8.0, "g/l"),
                Chemical("Salt", 30.0, "g/l")
            ]

            recipe_details = RecipeDetails(
                recipe=test_recipe,
                colors=test_colors,
                chemicals=test_chemicals,
                total_percentage=3.5,
                dominant_type="INDANTHREN",
                cost=1.42
            )

            # اختبار التصدير التلقائي على مسار مؤقت قابل للكتابة
            test_pdf_path = os.path.join(
                tempfile.gettempdir(),
                f"test_export_{int(datetime.now().timestamp())}.pdf"
            )

            # حذف الملف إذا كان موجوداً
            if os.path.exists(test_pdf_path):
                os.remove(test_pdf_path)

            # تصدير PDF
            pdf_path = PDFExporter.export_recipe_to_pdf(recipe_details, test_pdf_path)

            if pdf_path and os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path) / 1024
                print(f"   📄 تم إنشاء ملف PDF بنجاح: {os.path.basename(pdf_path)} ({file_size:.1f} KB)")

                # تنظيف الملف الاختباري
                try:
                    os.remove(pdf_path)
                except:
                    pass

                return True
            else:
                print("   ❌ فشل إنشاء ملف PDF")
                return False

        except Exception as e:
            print(f"   💥 خطأ في تصدير PDF: {e}")
            return False

    def test_search_functions(self):
        """اختبار وظائف البحث"""
        try:
            # إضافة بيانات اختبارية للبحث
            test_colors = [
                Color(id=0, code="SEARCH01", name="Red Color Test", dye_type="INDANTHREN",
                      supplier="Supplier A", price_kg=45.0, resa_percent=2.0),
                Color(id=0, code="SEARCH02", name="Blue Test Color", dye_type="REATTIVI CALDI",
                      supplier="Supplier B", price_kg=38.5, resa_percent=1.5),
                Color(id=0, code="SEARCH03", name="Green Color", dye_type="REATTIVI FREDDI",
                      supplier="Supplier A", price_kg=42.0, resa_percent=2.2)
            ]

            color_ids = []
            for color in test_colors:
                color_id = self.db.add_color(color)
                if color_id > 0:
                    color_ids.append(color_id)

            if len(color_ids) < 3:
                print("   ⚠️ لم يتم إضافة جميع ألوان الاختبار")
                self.cleanup_test_colors(color_ids)
                return False

            # الحصول على جميع الألوان
            all_colors = self.db.get_all_colors()
            if len(all_colors) < 3:
                print("   ❌ فشل استرجاع الألوان")
                self.cleanup_test_colors(color_ids)
                return False

            print(f"   🔍 عدد الألوان الكلي: {len(all_colors)}")

            # البحث بلون معين (محاكاة بحث يدوي)
            search_term = "Test"
            filtered_colors = []
            for color in all_colors:
                if (search_term.lower() in color.name.lower() or
                        search_term.lower() in color.code.lower() or
                        search_term.lower() in color.dye_type.lower() or
                        search_term.lower() in color.supplier.lower()):
                    filtered_colors.append(color)

            print(f"   🔎 نتيجة البحث بـ '{search_term}': {len(filtered_colors)} لون")

            # تنظيف
            self.cleanup_test_colors(color_ids)

            return len(filtered_colors) >= 2  # يجب أن يجد على الأقل لونين

        except Exception as e:
            print(f"   💥 خطأ في اختبار البحث: {e}")
            return False

    def test_basic_ui(self):
        """اختبار واجهة المستخدم الأساسية"""
        try:
            # اختبار إنشاء عناصر واجهة المستخدم الأساسية
            if self.parent:
                # إنشاء نافذة اختبارية
                test_window = tk.Toplevel(self.parent)
                test_window.title("UI Test Window")
                test_window.geometry("400x300")

                # إنشاء عناصر واجهة المستخدم الأساسية
                label = ttk.Label(test_window, text="UI Test Label")
                label.pack(pady=10)

                button = ttk.Button(test_window, text="Test Button",
                                    command=lambda: print("Button clicked"))
                button.pack(pady=10)

                entry = ttk.Entry(test_window)
                entry.pack(pady=10)
                entry.insert(0, "Test text")

                combo = ttk.Combobox(test_window, values=["Option 1", "Option 2", "Option 3"])
                combo.pack(pady=10)
                combo.set("Option 1")

                # إغلاق النافذة بعد وقت قصير
                test_window.after(1000, test_window.destroy)

                print("   🖥️  عناصر واجهة المستخدم: ✅")
                return True
            else:
                print("   ⚠️  لا يوجد parent لاختبار واجهة المستخدم")
                return True  # نعتبره ناجحاً إذا لم يكن هناك parent

        except Exception as e:
            print(f"   💥 خطأ في اختبار واجهة المستخدم: {e}")
            return False

    def display_results(self):
        """عرض نتائج الاختبار"""
        print("\n" + "=" * 60)
        print("📊 نتائج الاختبار الشامل")
        print("=" * 60)

        passed = 0
        failed = 0
        errors = 0

        for test_name, result in self.test_results:
            if "✅" in result:
                passed += 1
                print(f"{result} {test_name}")
            elif "❌" in result:
                failed += 1
                print(f"{result} {test_name}")
            else:
                errors += 1
                print(f"{result} {test_name}")

        print("\n" + "=" * 60)
        print(f"النتيجة النهائية:")
        print(f"✅ نجح: {passed}")
        print(f"❌ فشل: {failed}")
        print(f"💥 أخطاء: {errors}")
        print("=" * 60)

        if self.errors:
            print("\n📋 تفاصيل الأخطاء:")
            for i, (test_name, error, trace) in enumerate(self.errors, 1):
                print(f"\n{i}. {test_name}:")
                print(f"   الخطأ: {error}")
                # طباعة أول سطرين فقط من التتبع لتجنب الفوضى
                trace_lines = trace.split('\n')[:4]
                for line in trace_lines:
                    print(f"   {line}")

        if failed == 0 and errors == 0:
            print("\n🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام.")
            return True
        else:
            print(f"\n⚠️  يوجد {failed} اختبار فاشل و {errors} خطأ.")
            return False

    def run_quick_test(self):
        """تشغيل اختبار سريع"""
        print("\n⚡ تشغيل اختبار سريع...")

        quick_tests = [
            self.test_database_connection,
            self.test_chemical_calculations,
            self.test_cost_calculations,
            self.test_utility_functions
        ]

        test_names = [
            "اتصال قاعدة البيانات",
            "حساب الكيماويات",
            "حساب التكاليف",
            "الدوال المساعدة"
        ]

        all_passed = True
        for i, test_func in enumerate(quick_tests):
            try:
                print(f"\n🔍 {test_names[i]}...")
                result = test_func()
                if result:
                    print(f"   ✅ نجح")
                else:
                    print(f"   ❌ فشل")
                    all_passed = False
            except Exception as e:
                print(f"   💥 خطأ: {e}")
                all_passed = False

        if all_passed:
            print("\n🎉 الاختبار السريع نجح!")
        else:
            print("\n⚠️  الاختبار السريع فشل في بعض الأجزاء")

        return all_passed


def run_tests_from_gui(parent):
    """تشغيل الاختبارات من واجهة المستخدم"""
    try:
        # إنشاء نافذة الاختبار
        test_window = tk.Toplevel(parent)
        test_window.title("System Test Suite")
        test_window.geometry("600x500")

        # Make window modal
        test_window.transient(parent)
        test_window.lift()
        test_window.focus_force()
        test_window.grab_set()
        test_window.attributes("-topmost", True)
        test_window.after(250, lambda: test_window.attributes("-topmost", False))

        # عنوان
        title_label = ttk.Label(test_window, text="🔬 System Test Suite",
                                font=('Arial', 14, 'bold'))
        title_label.pack(pady=20)

        # منطقة النتائج
        result_frame = ttk.LabelFrame(test_window, text="Test Results", padding=20)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # مربع النص للنتائج
        result_text = tk.Text(result_frame, height=20, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=result_text.yview)
        result_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # إعادة توجيه الطباعة إلى مربع النص
        class TextRedirector:
            def __init__(self, text_widget):
                self.text_widget = text_widget

            def write(self, string):
                self.text_widget.insert(tk.END, string)
                self.text_widget.see(tk.END)
                self.text_widget.update()

            def flush(self):
                pass

        # حفظ stdout الأصلي
        old_stdout = sys.stdout

        # إطار الأزرار
        button_frame = ttk.Frame(test_window)
        button_frame.pack(pady=20)

        def run_full_tests():
            """تشغيل الاختبارات الكاملة"""
            result_text.delete(1.0, tk.END)
            sys.stdout = TextRedirector(result_text)

            tester = SystemTester(parent)
            tester.run_full_test_suite()

            sys.stdout = old_stdout

        def run_quick_test():
            """تشغيل اختبار سريع"""
            result_text.delete(1.0, tk.END)
            sys.stdout = TextRedirector(result_text)

            tester = SystemTester(parent)
            tester.run_quick_test()

            sys.stdout = old_stdout

        def clear_results():
            """مسح النتائج"""
            result_text.delete(1.0, tk.END)

        # أزرار التحكم
        ttk.Button(button_frame, text="🚀 Run Full Test Suite",
                   command=run_full_tests, width=20).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="⚡ Run Quick Test",
                   command=run_quick_test, width=20).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="🗑️ Clear Results",
                   command=clear_results, width=15).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="✖ Close",
                   command=test_window.destroy, width=15).pack(side=tk.LEFT, padx=5)

        # رسالة ترحيب
        result_text.insert(tk.END, "Welcome to System Test Suite\n")
        result_text.insert(tk.END, "=" * 40 + "\n")
        result_text.insert(tk.END, "Click 'Run Full Test Suite' to test all system components\n")
        result_text.insert(tk.END, "or 'Run Quick Test' for a basic check.\n\n")

        return test_window

    except Exception as e:
        messagebox.showerror("Test Error", f"Failed to open test window: {str(e)}")
        return None


# دالة للاستخدام المباشر من السكريبت
if __name__ == "__main__":
    print("Starting DyeMaster Pro Tests...")

    # إنشاء نافذة Tkinter مخفية
    root = tk.Tk()
    root.withdraw()  # إخفاء النافذة الرئيسية

    # تشغيل الاختبارات
    tester = SystemTester()

    # سؤال المستخدم عن نوع الاختبار
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        success = tester.run_quick_test()
    else:
        success = tester.run_full_test_suite()

    # عرض النتائج في messagebox
    if success:
        messagebox.showinfo("Test Complete", "✅ All tests passed! System is ready.")
    else:
        messagebox.showwarning("Test Complete", "⚠️ Some tests failed. Check console for details.")

    root.destroy()


def run_automatic_full_test(parent=None):
    """تشغيل اختبار كامل تلقائياً"""
    print("🚀 Starting Automatic Full System Test...")
    print("=" * 60)

    tester = SystemTester(parent)
    success = tester.run_full_test_suite()

    if success:
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! SYSTEM IS READY.")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("⚠️ SOME TESTS FAILED. PLEASE CHECK THE RESULTS.")
        print("=" * 60)
        return False


def run_automatic_quick_test(parent=None):
    """تشغيل اختبار سريع تلقائياً"""
    print("⚡ Starting Automatic Quick Test...")
    print("=" * 60)

    tester = SystemTester(parent)
    success = tester.run_quick_test()

    if success:
        print("\n" + "=" * 60)
        print("✅ QUICK TEST PASSED!")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ QUICK TEST FAILED!")
        print("=" * 60)
        return False
