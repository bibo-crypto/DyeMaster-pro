"""
نظام التحديث التلقائي من GitHub
"""
import os
import sys
import requests
import subprocess
import shutil
from tkinter import messagebox
import tempfile

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
                    # البحث عن رابط التحميل للـ exe
                    exe_url = None
                    if release_data.get("assets"):
                        for asset in release_data["assets"]:
                            if asset["name"].endswith(".exe"):
                                exe_url = asset["browser_download_url"]
                                break
                    if not exe_url:
                        # إذا لم يوجد exe، استخدم أول asset
                        exe_url = release_data["assets"][0]["browser_download_url"] if release_data.get("assets") else None

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

            # Compare version parts
            min_len = min(len(l_parts), len(c_parts))
            for i in range(min_len):
                if l_parts[i] > c_parts[i]:
                    return True
                elif l_parts[i] < c_parts[i]:
                    return False

            # If all compared parts are equal, longer version is considered newer
            return len(l_parts) > len(c_parts)
        except:
            return latest > current

    def download_and_install(self, exe_url):
        """تحميل وتثبيت التحديث مع إعادة التشغيل التلقائي - حسب الخطة المحددة"""
        if not exe_url:
            messagebox.showerror("Update Error", "No update file found on GitHub.")
            return False

        try:
            # الحصول على حجم الملف من GitHub
            head_response = requests.head(exe_url, timeout=10)
            expected_size = int(head_response.headers.get('content-length', 0))

            # التحقق من نوع التطبيق (مصدر أو exe)
            main_script = os.path.join(os.path.dirname(__file__), '..', 'main.py')
            main_script = os.path.abspath(main_script)

            if os.path.exists(main_script) and main_script.endswith('.py'):
                # تطبيق مصدر - نحتاج لاستبدال main.py
                exe_path = main_script
                exe_dir = os.path.dirname(exe_path)
                temp_exe_name = 'main_new.py'
                is_source_app = True
                python_cmd = sys.executable
            else:
                # تطبيق exe
                exe_path = sys.executable
                exe_dir = os.path.dirname(exe_path)
                temp_exe_name = 'update_temp.exe'
                is_source_app = False
                python_cmd = None

            temp_exe_path = os.path.join(exe_dir, temp_exe_name)

            # تحميل مع التحقق من الاكتمال (خطوة 3: Download silently)
            print("Downloading update silently...")
            response = requests.get(exe_url, stream=True, timeout=30)
            downloaded_size = 0
            with open(temp_exe_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

            # التحقق من حجم الملف
            if expected_size > 0 and downloaded_size != expected_size:
                os.remove(temp_exe_path)
                messagebox.showerror("Update Error", f"Downloaded file is incomplete. Expected {expected_size} bytes, got {downloaded_size} bytes.")
                return False

            # التحقق من أن الملف ليس فارغاً
            if os.path.getsize(temp_exe_path) == 0:
                os.remove(temp_exe_path)
                messagebox.showerror("Update Error", "Downloaded file is empty.")
                return False

            # التحقق من أن الملف قابل للتنفيذ (exe header)
            try:
                with open(temp_exe_path, 'rb') as f:
                    header = f.read(2)
                    if header != b'MZ':
                        os.remove(temp_exe_path)
                        messagebox.showerror("Update Error", "Downloaded file is not a valid executable.")
                        return False
            except Exception as e:
                os.remove(temp_exe_path)
                messagebox.showerror("Update Error", f"Failed to verify downloaded file: {e}")
                return False

            # تحديث ملف الإصدار
            version_file = os.path.join(exe_dir, 'version.txt')
            try:
                # قراءة الإصدار الجديد من GitHub
                headers = {'Accept': 'application/vnd.github.v3+json'}
                response = requests.get(self.api_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    release_data = response.json()
                    new_version = release_data.get("tag_name", "1.0.0").lstrip('vV')
                    with open(version_file, 'w', encoding='utf-8') as f:
                        f.write(new_version)
            except:
                pass

            # إنشاء ملف batch محسن للتحديث (خطوة 5: Run updater, خطوة 6: Replace files)
            batch_path = os.path.join(exe_dir, 'update.bat')
            old_exe_path = exe_path + '.old'
            backup_exe_path = exe_path + '.backup'

            with open(batch_path, 'w') as f:
                f.write('@echo off\n')
                f.write('echo Starting update process...\n')
                f.write('timeout /t 15 /nobreak > nul\n')  # انتظار أطول للتأكد من إغلاق البرنامج بالكامل

                if is_source_app:
                    # للتطبيقات المصدر: لا نحتاج لإغلاق عمليات python لأن العملية الحالية ستغلق نفسها
                    f.write('echo Testing new Python script...\n')
                    f.write(f'"{python_cmd}" "{temp_exe_path}" --help >nul 2>&1\n')
                    f.write('if %errorlevel% neq 0 (\n')
                    f.write('    echo ERROR: New Python script failed to run. Update cancelled.\n')
                    f.write('    echo The original application should still be running.\n')
                    f.write('    pause\n')
                    f.write('    exit /b 1\n')
                    f.write(')\n')
                else:
                    # للتطبيقات الـ exe: إغلاق العمليات المحددة
                    f.write('echo Ensuring program is closed...\n')
                    f.write('taskkill /f /im "python.exe" >nul 2>&1\n')
                    f.write('taskkill /f /im "pythonw.exe" >nul 2>&1\n')
                    f.write('timeout /t 3 /nobreak > nul\n')
                    f.write('echo Testing new executable...\n')
                    f.write(f'"{temp_exe_path}" --help >nul 2>&1\n')
                    f.write('if %errorlevel% neq 0 (\n')
                    f.write('    echo ERROR: New executable failed to run. Restoring backup...\n')
                    f.write(f'    move /y "{exe_path}" "{exe_path}.failed" >nul 2>&1\n')
                    f.write(f'    copy /y "{backup_exe_path}" "{exe_path}" >nul 2>&1\n')
                    f.write(f'    start "" "{exe_path}"\n')
                    f.write('    echo Update failed. Original version restored.\n')
                    f.write('    pause\n')
                    f.write('    exit /b 1\n')
                    f.write(')\n')

                f.write('echo New file test passed. Proceeding with replacement...\n')
                f.write(f'copy /y "{exe_path}" "{backup_exe_path}" >nul 2>&1\n')  # نسخة احتياطية
                f.write(f'move /y "{exe_path}" "{old_exe_path}" >nul 2>&1\n')  # نقل القديم
                f.write(f'move /y "{temp_exe_path}" "{exe_path}" >nul 2>&1\n')  # نقل الجديد
                f.write('echo Files replaced successfully\n')
                f.write('timeout /t 3 /nobreak > nul\n')
                f.write('echo Starting new version...\n')

                if is_source_app:
                    # تشغيل التطبيق المصدر بالبايثون - بدون إغلاق جميع عمليات python
                    f.write(f'start "" "{python_cmd}" "{exe_path}"\n')  # خطوة 7: Run new version
                else:
                    # تشغيل الـ exe مباشرة
                    f.write(f'start "" "{exe_path}"\n')  # خطوة 7: Run new version

                f.write('echo New version started\n')
                f.write('timeout /t 3 /nobreak > nul\n')
                f.write('echo Cleaning up...\n')
                f.write(f'del "{old_exe_path}" >nul 2>&1\n')  # حذف القديم
                f.write(f'del "{backup_exe_path}" >nul 2>&1\n')  # حذف النسخة الاحتياطية
                f.write(f'del "%~f0" >nul 2>&1\n')  # حذف ملف الـ batch

            print("Update files prepared. Closing current program...")

            # خطوة 4: Close program
            # تشغيل الـ batch
            subprocess.Popen([batch_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

            # إغلاق التطبيق الحالي
            sys.exit(0)

        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to install update: {e}")
            return False
