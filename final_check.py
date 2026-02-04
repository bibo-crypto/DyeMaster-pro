#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص شامل نهائي لجميع مشاكل البرنامج
"""
import sys
import os
import io
import warnings

# معالجة encoding في Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "="*70)
print("🔍 الفحص الشامل النهائي للبرنامج")
print("="*70)

checks_passed = 0
checks_failed = 0

# الفحص 1: التحقق من أي استيرادات ColorChemSystem متبقية
print("\n✅ الفحص 1: البحث عن استيرادات ColorChemSystem المتبقية...")
try:
    import re
    python_files = []
    exclude_files = ['check_errors.py', 'test_runner.py', 'test_pdf_export.py', 'test_pdf_comprehensive.py', 'final_check.py']
    for root, dirs, files in os.walk('.'):
        # تخطي مجلدات cache
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.pytest_cache']]
        for file in files:
            if file.endswith('.py') and file not in exclude_files:
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines, 1):
                        # البحث عن استيرادات ColorChemSystem الفعلية فقط (وليس أسماء الفئات)
                        if re.search(r'\b(from|import)\s+ColorChemSystem\b', line):
                            print(f"   ⚠️ وجد استيراد في: {filepath} (السطر {i})")
                            print(f"      {line.strip()}")
                            checks_failed += 1
                            break
    if checks_failed == 0:
        print("   ✓ لا توجد استيرادات ColorChemSystem في ملفات المشروع")
        checks_passed += 1
except Exception as e:
    print(f"   ✗ خطأ: {e}")
    checks_failed += 1

# الفحص 2: التحقق من الاستيرادات الأساسية
print("\n✅ الفحص 2: التحقق من الاستيرادات الأساسية...")
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    from app.config import *
    from app.database import DatabaseManager
    from app.gui import ColorChemSystemGUI
    from app.models import Color, Recipe, RecipeDetails
    from app.calculator import ChemicalCalculator, CostCalculator
    from app.pdf_exporter import PDFExporter
    from app.tester import SystemTester
    print("   ✓ جميع الاستيرادات الأساسية بخير")
    checks_passed += 1
except Exception as e:
    print(f"   ✗ خطأ: {e}")
    checks_failed += 1

# الفحص 3: التحقق من UI modules
print("\n✅ الفحص 3: التحقق من UI modules...")
try:
    from ui.colors_window import ColorsWindow
    from ui.recipes_window import RecipesWindow
    from ui.colors_in_use_window import ColorsInUseWindow
    from ui.recipe_creator_window import RecipeCreatorWindow
    from ui.saved_recipes_window import SavedRecipesWindow
    print("   ✓ جميع UI modules بخير")
    checks_passed += 1
except Exception as e:
    print(f"   ✗ خطأ: {e}")
    checks_failed += 1

# الفحص 4: التحقق من قاعدة البيانات
print("\n✅ الفحص 4: التحقق من قاعدة البيانات...")
try:
    db = DatabaseManager()
    db.initialize_database()
    print("   ✓ قاعدة البيانات تعمل بشكل صحيح")
    checks_passed += 1
except Exception as e:
    print(f"   ✗ خطأ: {e}")
    checks_failed += 1

# الفحص 5: التحقق من PDF export
print("\n✅ الفحص 5: التحقق من PDF export...")
try:
    from app.models import RecipeColor
    recipe = Recipe(
        id=1,
        recipe_code="CHECK01",
        name="Check Recipe",
        created_at="2026-01-19 10:00:00"
    )
    colors = [
        RecipeColor(
            id=1,
            recipe_id=1,
            color_id=1,
            percentage=100.0,
            color_code="COL001",
            color_name="Test Color",
            dye_type="INDANTHREN",
            price_kg=10.0
        )
    ]
    recipe_details = RecipeDetails(
        recipe=recipe,
        colors=colors,
        chemicals={},
        total_percentage=100.0,
        dominant_type="INDANTHREN",
        cost=10.0
    )
    test_path = os.path.join(os.path.expanduser("~"), "Desktop", "check_test.pdf")
    pdf = PDFExporter.export_recipe_to_pdf(recipe_details, test_path)
    if pdf and os.path.exists(pdf):
        print("   ✓ PDF export يعمل بشكل صحيح")
        checks_passed += 1
        os.remove(pdf)  # تنظيف
    else:
        print("   ✗ فشل PDF export")
        checks_failed += 1
except Exception as e:
    print(f"   ✗ خطأ: {e}")
    checks_failed += 1

# الفحص 6: التحقق من main.py functions
print("\n✅ الفحص 6: التحقق من main.py functions...")
try:
    from main import initialize_application, check_database_status
    if initialize_application():
        print("   ✓ initialize_application() يعمل")
    if check_database_status():
        print("   ✓ check_database_status() يعمل")
    checks_passed += 1
except Exception as e:
    print(f"   ✗ خطأ: {e}")
    checks_failed += 1

# الفحص 7: التحقق من الأخطاء في syntax
print("\n✅ الفحص 7: التحقق من syntax errors...")
try:
    import py_compile
    import glob
    errors = []
    for pyfile in glob.glob('**/*.py', recursive=True):
        if '__pycache__' not in pyfile:
            try:
                py_compile.compile(pyfile, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"{pyfile}: {e}")
    
    if errors:
        for error in errors:
            print(f"   ✗ {error}")
        checks_failed += 1
    else:
        print("   ✓ لا توجد syntax errors")
        checks_passed += 1
except Exception as e:
    print(f"   ✗ خطأ: {e}")
    checks_failed += 1

# الملخص
print("\n" + "="*70)
print(f"📊 النتائج:")
print(f"   ✅ نجح: {checks_passed}")
print(f"   ❌ فشل: {checks_failed}")
print("="*70)

if checks_failed == 0:
    print("\n🎉 جميع الفحوصات نجحت! البرنامج جاهز للاستخدام")
    sys.exit(0)
else:
    print(f"\n⚠️ هناك {checks_failed} مشكلة تحتاج حل")
    sys.exit(1)
