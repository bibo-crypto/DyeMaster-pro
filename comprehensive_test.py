"""
Comprehensive test for the Color and Chemical system
"""
import sys
import os

# Fix encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """اختبار جميع الاستيرادات"""
    print("\n" + "="*70)
    print("اختبار 1: الاستيرادات الأساسية")
    print("="*70)
    
    try:
        from app.database import DatabaseManager
        print("OK - DatabaseManager imported")
    except Exception as e:
        print(f"ERROR - DatabaseManager: {e}")
        return False
    
    try:
        from app.gui import ColorChemSystemGUI
        print("OK - ColorChemSystemGUI imported")
    except Exception as e:
        print(f"ERROR - ColorChemSystemGUI: {e}")
        return False
    
    try:
        from app.models import Recipe, RecipeDetails, Color
        print("OK - Models imported")
    except Exception as e:
        print(f"ERROR - Models: {e}")
        return False
    
    try:
        from app.calculator import ChemicalCalculator, CostCalculator
        print("OK - Calculators imported")
    except Exception as e:
        print(f"ERROR - Calculators: {e}")
        return False
    
    try:
        from app.pdf_exporter import PDFExporter
        print("OK - PDFExporter imported")
    except Exception as e:
        print(f"ERROR - PDFExporter: {e}")
        return False
    
    try:
        from ui.recipe_creator_window import RecipeCreatorWindow
        print("OK - RecipeCreatorWindow imported")
    except Exception as e:
        print(f"ERROR - RecipeCreatorWindow: {e}")
        return False
    
    try:
        from ui.saved_recipes_window import SavedRecipesWindow
        print("OK - SavedRecipesWindow imported")
    except Exception as e:
        print(f"ERROR - SavedRecipesWindow: {e}")
        return False
    
    return True


def test_recipe_creation():
    """اختبار إنشاء وصفة"""
    print("\n" + "="*70)
    print("اختبار 2: إنشاء وصفة وحساب الكيماويات")
    print("="*70)
    
    try:
        from app.models import Recipe, RecipeDetails
        from app.calculator import ChemicalCalculator, CostCalculator
        
        # إنشاء وصفة
        recipe = Recipe(
            id=0,
            recipe_code="TEST001",
            name="Test Recipe",
            created_at="2024-01-21 12:00:00"
        )
        print(f"OK - Recipe created: {recipe.name} ({recipe.recipe_code})")
        
        # إعداد الألوان
        selected_colors = [
            {
                "code": "IND-001",
                "name": "Indanthren Blue",
                "dye_type": "INDANTHREN",
                "price_kg": 50.0,
                "percentage": 25
            },
            {
                "code": "IND-002",
                "name": "Indanthren Red",
                "dye_type": "INDANTHREN",
                "price_kg": 55.0,
                "percentage": 25
            }
        ]
        print(f"OK - Colors prepared: {len(selected_colors)} colors")
        
        # حساب تفاصيل الوصفة
        recipe_details = ChemicalCalculator.calculate_recipe_details(recipe.name, selected_colors)
        print(f"OK - Recipe details calculated:")
        print(f"     - Total Percentage: {recipe_details.total_percentage:.2f}%")
        print(f"     - Chemicals: {len(recipe_details.chemicals)}")
        print(f"     - Cost: EUR {recipe_details.cost:.2f}")
        print(f"     - Dominant Type: {recipe_details.dominant_type}")
        
        # عرض الكيماويات
        print("     - Chemical Details:")
        for chem in recipe_details.chemicals:
            print(f"         {chem.code}: {chem.name} - {chem.quantity} {chem.unit}")
        
        # حساب تكلفة الوصفة
        recipe_cost = CostCalculator.calculate_recipe_cost(selected_colors)
        print(f"OK - Recipe cost: EUR {recipe_cost:.2f}")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
        return False


def test_save_and_export_logic():
    """اختبار منطق Save and Export"""
    print("\n" + "="*70)
    print("اختبار 3: منطق Save and Export")
    print("="*70)
    
    try:
        from app.models import Recipe, RecipeDetails
        from app.calculator import ChemicalCalculator
        
        # محاكاة البيانات المدخلة
        recipe_code = "123456"
        recipe_name = "My Test Recipe"
        selected_colors = [
            {
                "code": "IND-003",
                "name": "Indanthren Green",
                "dye_type": "INDANTHREN",
                "price_kg": 48.0,
                "percentage": 50
            }
        ]
        
        # إنشاء كائن Recipe
        recipe = Recipe(
            id=0,
            recipe_code=recipe_code,
            name=recipe_name,
            created_at="2024-01-21 12:00:00"
        )
        print(f"OK - Recipe object created: {recipe.name}")
        
        # حساب تفاصيل الوصفة (وهذا ما يحدث في save_and_export)
        recipe_details = ChemicalCalculator.calculate_recipe_details(recipe_name, selected_colors)
        print(f"OK - Recipe details calculated for export")
        
        # تعيين Recipe إلى RecipeDetails
        recipe.id = 1  # محاكاة ID من قاعدة البيانات
        recipe_details.recipe = recipe
        
        print(f"OK - RecipeDetails prepared for PDF export:")
        print(f"     - Recipe: {recipe_details.recipe.name}")
        print(f"     - Colors: {len(recipe_details.colors)}")
        print(f"     - Chemicals: {len(recipe_details.chemicals)}")
        print(f"     - Cost: EUR {recipe_details.cost:.2f}")
        
        # تحقق من أن PDFExporter يمكنه استخدام هذه البيانات
        from app.pdf_exporter import PDFExporter
        print(f"OK - PDFExporter is ready to export")
        
        return True
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
        return False


def test_pdf_export_data_handling():
    """اختبار معالجة البيانات في PDF export"""
    print("\n" + "="*70)
    print("اختبار 4: معالجة البيانات في PDF export")
    print("="*70)
    
    try:
        from app.models import Recipe, RecipeDetails, RecipeColor
        from app.calculator import ChemicalCalculator
        
        # اختبار مع قواموس (dictionaries)
        print("Testing with dictionaries...")
        selected_colors_dict = [
            {
                "code": "TEST-001",
                "name": "Test Color 1",
                "dye_type": "INDANTHREN",
                "price_kg": 50.0,
                "percentage": 33.33
            }
        ]
        
        recipe_details_dict = ChemicalCalculator.calculate_recipe_details("Test", selected_colors_dict)
        print(f"OK - Created RecipeDetails with dict colors")
        print(f"     - Type of colors[0]: {type(recipe_details_dict.colors[0])}")
        
        # محاكاة معالجة PDF
        for color in recipe_details_dict.colors:
            if isinstance(color, dict):
                percentage = color['percentage']
                code = color["code"]
                name = color["name"]
                print(f"     - Dict access OK: {code} - {name} ({percentage}%)")
            else:
                print(f"     - Object access: {getattr(color, 'color_code', '?')}")
        
        print("OK - PDF data handling test passed")
        return True
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()
        return False


def main():
    """الدالة الرئيسية"""
    print("\n" + "="*70)
    print("برنامج الاختبار الشامل لنظام إدارة الألوان والمواد الكيميائية")
    print("="*70)
    
    results = []
    
    # اختبار 1: الاستيرادات
    results.append(("الاستيرادات", test_imports()))
    
    # اختبار 2: إنشاء الوصفة
    results.append(("إنشاء الوصفة", test_recipe_creation()))
    
    # اختبار 3: منطق Save and Export
    results.append(("منطق Save & Export", test_save_and_export_logic()))
    
    # اختبار 4: معالجة بيانات PDF
    results.append(("معالجة بيانات PDF", test_pdf_export_data_handling()))
    
    # عرض النتائج
    print("\n" + "="*70)
    print("ملخص النتائج:")
    print("="*70)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "OK" if result else "ERROR"
        print(f"[{symbol}] {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("SUCCESS - جميع الاختبارات نجحت!")
        print("البرنامج جاهز للاستخدام بدون مشاكل.")
    else:
        print("FAILURE - هناك مشاكل في البرنامج.")
    print("="*70 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
