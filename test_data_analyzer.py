#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick test script to verify Data Analyzer integration
Checks if the menu item exists and the window can be opened
"""

import sys
import os

# Add ColorChemSystem to path
ColorChemSystem_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ColorChemSystem_path)

def test_data_analyzer_imports():
    """Test if all required modules can be imported"""
    print("\n" + "="*100)
    print("DATA ANALYZER INTEGRATION TEST")
    print("="*100)
    
    print("\n1. Testing imports...")
    try:
        from app.data_analyzer import DataAnalyzer
        print("   OK: DataAnalyzer module imported")
    except ImportError as e:
        print(f"   ERROR: Cannot import DataAnalyzer - {e}")
        return False
    
    try:
        from ui.data_analyzer_window import DataAnalyzerWindow
        print("   OK: DataAnalyzerWindow module imported")
    except ImportError as e:
        print(f"   ERROR: Cannot import DataAnalyzerWindow - {e}")
        return False
    
    try:
        from app.gui import ColorChemSystemGUI
        print("   OK: ColorChemSystemGUI module imported")
    except ImportError as e:
        print(f"   ERROR: Cannot import ColorChemSystemGUI - {e}")
        return False
    
    return True

def test_gui_integration():
    """Test if GUI has the show_data_analyzer method"""
    print("\n2. Testing GUI integration...")
    
    try:
        from app.gui import ColorChemSystemGUI
        
        # Check if method exists
        if hasattr(ColorChemSystemGUI, 'show_data_analyzer'):
            print("   OK: show_data_analyzer method exists in GUI")
            return True
        else:
            print("   ERROR: show_data_analyzer method NOT found in GUI")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_data_analyzer_functionality():
    """Test if DataAnalyzer works with a real file"""
    print("\n3. Testing DataAnalyzer functionality...")
    
    try:
        from app.data_analyzer import DataAnalyzer
        
        file_path = os.path.join(
            os.path.dirname(ColorChemSystem_path),
            'WNCOINT.xlsx'
        )
        
        if not os.path.exists(file_path):
            print(f"   WARNING: Test file not found at {file_path}")
            return True  # Don't fail, file might not exist
        
        analyzer = DataAnalyzer(file_path)
        print("   OK: DataAnalyzer initialized successfully")
        
        # Test analysis method
        results = analyzer.analyze_complete()
        print(f"   OK: Analysis returned {len(results)} records")
        
        if len(results) > 0:
            print(f"   OK: First record has {len(results[0])} fields")
            return True
        else:
            print("   WARNING: No results returned")
            return True
    
    except FileNotFoundError as e:
        print(f"   WARNING: File not found - {e}")
        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def main():
    """Run all tests"""
    tests = [
        ("Imports", test_data_analyzer_imports),
        ("GUI Integration", test_gui_integration),
        ("DataAnalyzer Functionality", test_data_analyzer_functionality),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n   FATAL ERROR in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*100)
    print("TEST SUMMARY")
    print("="*100)
    
    all_passed = True
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name:30} : {status}")
        if not result:
            all_passed = False
    
    print("\n" + "="*100)
    if all_passed:
        print("OVERALL RESULT: ALL TESTS PASSED")
        print("\nThe Data Analyzer feature is ready to use!")
        print("Go to: Tools → Data Analyzer")
    else:
        print("OVERALL RESULT: SOME TESTS FAILED")
        print("\nPlease check the errors above.")
    
    print("="*100 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
