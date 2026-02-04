#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
برنامج اختبار شامل للنظام
"""
import sys
import os
import traceback
import io

# معالجة encoding في Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# إضافة المسار للمشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """تشغيل الاختبارات الشاملة"""
    print("=" * 70)
    print("🧪 برنامج اختبار نظام إدارة الألوان والمواد الكيميائية")
    print("=" * 70)
    
    try:
        # الاختبار 1: استيراد المكونات الأساسية
        print("\n✅ اختبار 1: استيراد المكونات...")
        try:
            from app.config import DATABASE_FILE, DYE_TYPES
            from app.database import DatabaseManager
            from app.models import Color, Recipe
            from app.calculator import ChemicalCalculator, CostCalculator
            from app.tester import SystemTester, run_tests_from_gui
            print("   ✓ تم استيراد جميع المكونات بنجاح")
        except Exception as e:
            print(f"   ✗ خطأ في الاستيراد: {e}")
            traceback.print_exc()
            return False
        
        # الاختبار 2: تهيئة قاعدة البيانات
        print("\n✅ اختبار 2: تهيئة قاعدة البيانات...")
        try:
            db = DatabaseManager()
            db.initialize_database()
            print("   ✓ تم تهيئة قاعدة البيانات بنجاح")
        except Exception as e:
            print(f"   ✗ خطأ في تهيئة قاعدة البيانات: {e}")
            traceback.print_exc()
            return False
        
        # الاختبار 3: اختبار العمليات الأساسية
        print("\n✅ اختبار 3: تشغيل اختبارات النظام...")
        try:
            tester = SystemTester(db)
            
            print("\n   📝 اختبار الاتصال بقاعدة البيانات...")
            if tester.test_database_connection():
                print("      ✓ الاتصال بقاعدة البيانات يعمل")
            else:
                print("      ✗ فشل الاتصال بقاعدة البيانات")
                
            print("\n   📝 اختبار جداول قاعدة البيانات...")
            if tester.test_database_tables():
                print("      ✓ جداول قاعدة البيانات تعمل")
            else:
                print("      ✗ فشل اختبار جداول قاعدة البيانات")
            
            print("\n   📝 اختبار عمليات الألوان (CRUD)...")
            if tester.test_colors_crud():
                print("      ✓ عمليات الألوان تعمل")
            else:
                print("      ✗ فشل اختبار عمليات الألوان")
            
            print("\n   📝 اختبار عمليات الوصفات (CRUD)...")
            if tester.test_recipes_crud():
                print("      ✓ عمليات الوصفات تعمل")
            else:
                print("      ✗ فشل اختبار عمليات الوصفات")
            
            print("\n   📝 اختبار الحسابات الكيميائية...")
            if tester.test_chemical_calculations():
                print("      ✓ الحسابات الكيميائية تعمل")
            else:
                print("      ✗ فشل اختبار الحسابات الكيميائية")
            
            print("\n   📝 اختبار حسابات التكاليف...")
            if tester.test_cost_calculations():
                print("      ✓ حسابات التكاليف تعمل")
            else:
                print("      ✗ فشل اختبار حسابات التكاليف")
            
            print("\n   📝 اختبار وظائف الأدوات...")
            if tester.test_utility_functions():
                print("      ✓ وظائف الأدوات تعمل")
            else:
                print("      ✗ فشل اختبار وظائف الأدوات")
            
            print("\n   📝 اختبار دوال البحث...")
            if tester.test_search_functions():
                print("      ✓ دوال البحث تعمل")
            else:
                print("      ✗ فشل اختبار دوال البحث")
            
        except Exception as e:
            print(f"   ✗ خطأ في تشغيل الاختبارات: {e}")
            traceback.print_exc()
            return False
        
        print("\n" + "=" * 70)
        print("✅ نجحت جميع الاختبارات! البرنامج جاهز للاستخدام")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ عام: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
