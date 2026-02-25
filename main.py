"""
نقطة الدخول الرئيسية للتطبيق - نسخة مبسطة
"""
import tkinter as tk
from tkinter import messagebox
import os
import sys

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    try:
        # إنشاء النافذة الرئيسية
        root = tk.Tk()
        root.title("ColorChem System v1.0.0")
        root.geometry("1200x700")
        
        # محاولة استيراد وتشغيل الواجهة
        try:
            from app.gui import ColorChemSystemGUI
            app = ColorChemSystemGUI(root)
            print("GUI created successfully")
            app.run()
        except Exception as e:
            # إذا فشل تحميل GUI، اعرض رسالة خطأ
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to load GUI: {str(e)}")
            root.destroy()
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            messagebox.showerror("Fatal Error", f"Application error: {str(e)}")
        except:
            print(f"Fatal Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
