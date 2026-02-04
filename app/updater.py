"""
نظام التحديث التلقائي من GitHub
"""
import os
import sys
import requests
import subprocess
import zipfile
import shutil
from tkinter import messagebox

class AppUpdater:
    def __init__(self, current_version="1.0.0"):
        self.repo_owner = "bibo-crypto"
        self.repo_name = "DyeMaster-pro"
        self.current_version = current_version
        self.api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"

    def check_for_updates(self):
        """التحقق من وجود تحديثات جديدة على GitHub"""
        try:
            # إضافة Headers لتجنب مشاكل الـ Rate Limit من GitHub
            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(self.api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                release_data = response.json()
                # تنظيف رقم الإصدار من أي أحرف غير رقمية في البداية مثل 'v'
                latest_version_raw = release_data.get("tag_name", "1.0.0")
                latest_version = latest_version_raw.lstrip('vV')
                
                if self._is_newer(latest_version, self.current_version):
                    # البحث عن رابط التحميل (يفضل zipball_url أو أول asset)
                    zip_url = release_data.get("zipball_url")
                    if not zip_url and release_data.get("assets"):
                        zip_url = release_data["assets"][0].get("browser_download_url")
                        
                    return True, latest_version, release_data.get("body", ""), zip_url
            
            return False, self.current_version, "", None
        except Exception as e:
            print(f"Update check failed: {e}")
            return False, self.current_version, "", None

    def _is_newer(self, latest, current):
        """مقارنة إصدارات البرنامج"""
        try:
            l_parts = [int(p) for p in latest.split('.')]
            c_parts = [int(p) for p in current.split('.')]
            return l_parts > c_parts
        except:
            return latest > current

    def download_and_install(self, zip_url):
        """تحميل وتثبيت التحديث"""
        try:
            # تحميل الملف المضغوط
            response = requests.get(zip_url, stream=True)
            zip_path = "update.zip"
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # فك الضغط (في مجلد مؤقت)
            temp_dir = "temp_update"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # ملاحظة: في بيئة حقيقية، ستحتاج لبرنامج خارجي لاستبدال الملفات أثناء تشغيل البرنامج
            # هنا سنقوم فقط بإخطار المستخدم أو محاولة الاستبدال إذا كان ذلك ممكناً
            messagebox.showinfo("Update", "Update downloaded. Please restart the application to apply changes.")
            
            # تنظيف
            os.remove(zip_path)
            return True
        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to install update: {e}")
            return False
