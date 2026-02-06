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
                    # البحث عن رابط التحميل لملف exe
                    exe_url = None
                    if release_data.get("assets"):
                        for asset in release_data["assets"]:
                            if asset["name"].endswith(".exe"):
                                exe_url = asset["browser_download_url"]
                                break

                    if exe_url:
                        return True, latest_version, release_data.get("body", ""), exe_url

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

    def download_and_install(self, exe_url):
        """تحميل وتثبيت التحديث"""
        try:
            # تحميل ملف الـ exe
            response = requests.get(exe_url, stream=True)
            temp_exe_path = "update_temp.exe"
            with open(temp_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            messagebox.showinfo("Update", "Update downloaded successfully. Please restart the application to apply changes.")
            return True
        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to download update: {e}")
            return False
