"""
In-app updater for Windows executable releases from GitHub.
"""
import hashlib
import os
import subprocess
import sys

import requests
from tkinter import messagebox


class AppUpdater:
    def __init__(self, current_version="1.0.0"):
        self.repo_owner = "bibo-crypto"
        self.repo_name = "DyeMaster-pro"
        self.current_version = (current_version or "1.0.0").strip()
        self.api_url = (
            f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
        )

    def check_for_updates(self):
        """Check GitHub latest release and compare with current version."""
        is_available, latest_version, notes, payload = self.get_latest_release()
        if not is_available:
            return False, self.current_version, "", None
        return self._is_newer(latest_version, self.current_version), latest_version, notes, payload

    def get_latest_release(self):
        """Fetch latest release info from GitHub."""
        try:
            headers = {"Accept": "application/vnd.github.v3+json"}
            response = self._http_get(self.api_url, headers=headers, timeout=15)
            response.raise_for_status()
            release_data = response.json()

            latest_version_raw = release_data.get("tag_name", self.current_version)
            latest_version = latest_version_raw.lstrip("vV").strip() or self.current_version
            exe_url, ico_url = self._extract_asset_urls(release_data)
            if not exe_url:
                return False, self.current_version, "", None

            payload = {"exe_url": exe_url, "ico_url": ico_url}
            return True, latest_version, release_data.get("body", ""), payload
        except Exception as exc:
            print(f"Latest release fetch failed: {exc}")
            return False, self.current_version, "", None

    def _http_get(self, url, **kwargs):
        try:
            return requests.get(url, **kwargs)
        except requests.exceptions.RequestException:
            # Fallback for broken proxy/system network env.
            session = requests.Session()
            session.trust_env = False
            return session.get(url, **kwargs)

    def _extract_asset_urls(self, release_data):
        exe_url = None
        ico_url = None

        preferred_exe = ""
        preferred_stem = ""
        try:
            preferred_exe = os.path.basename(sys.executable).lower()
            preferred_stem = os.path.splitext(preferred_exe)[0]
        except Exception:
            pass

        exe_candidates = []
        for asset in release_data.get("assets", []):
            raw_name = asset.get("name", "")
            name = raw_name.lower()
            url = asset.get("browser_download_url")
            if not url:
                continue

            if name.endswith(".exe"):
                score = 0
                if preferred_exe and name == preferred_exe:
                    score += 100
                if preferred_stem and preferred_stem in name:
                    score += 40
                if any(tag in name for tag in ("colorchem", "dyemaster", "main")):
                    score += 20
                if any(bad in name for bad in ("setup", "installer")):
                    score -= 20
                exe_candidates.append((score, raw_name, url))

            if (name.endswith(".ico") or "icon" in name) and ico_url is None:
                ico_url = url

        if exe_candidates:
            exe_candidates.sort(key=lambda item: item[0], reverse=True)
            best_score, best_name, best_url = exe_candidates[0]
            exe_url = best_url
            print(f"Updater selected asset: {best_name} (score={best_score})")

        return exe_url, ico_url

    def _is_newer(self, latest, current):
        """Compare semantic versions safely."""
        def parse_version(version):
            parts = []
            for part in str(version).split("."):
                try:
                    parts.append(int(part))
                except ValueError:
                    parts.append(0)
            while len(parts) < 3:
                parts.append(0)
            return tuple(parts[:3])

        try:
            return parse_version(latest) > parse_version(current)
        except Exception:
            return str(latest) > str(current)

    def _download_file(self, url, destination):
        if url.startswith("file://"):
            local_path = url[7:]
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Local file not found: {local_path}")
            import shutil
            shutil.copy2(local_path, destination)
            return

        tmp_destination = f"{destination}.part"
        bytes_written = 0
        try:
            with self._http_get(url, stream=True, timeout=(20, 300)) as response:
                response.raise_for_status()
                with open(tmp_destination, "wb") as handle:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            handle.write(chunk)
                            bytes_written += len(chunk)
            if bytes_written <= 0:
                raise RuntimeError("Downloaded file is empty.")
            if os.path.exists(destination):
                os.remove(destination)
            os.replace(tmp_destination, destination)
        except Exception:
            try:
                if os.path.exists(tmp_destination):
                    os.remove(tmp_destination)
            except Exception:
                pass
            raise

    def _calculate_file_hash(self, file_path, hash_type="sha256"):
        hash_func = hashlib.new(hash_type)
        try:
            with open(file_path, "rb") as handle:
                for chunk in iter(lambda: handle.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception:
            return None

    def _is_valid_windows_exe(self, file_path):
        try:
            if not os.path.exists(file_path):
                return False
            if os.path.getsize(file_path) < 1024:
                return False
            with open(file_path, "rb") as handle:
                return handle.read(2) == b"MZ"
        except Exception:
            return False

    @staticmethod
    def _ps_quote(value):
        return str(value).replace("'", "''")

    def download_and_install(self, download_info, latest_version):
        """
        Download new executable, close current instance, replace files, then relaunch.
        """
        try:
            print("Starting update process...")
            if not getattr(sys, "frozen", False):
                messagebox.showwarning("Update", "Automatic replacement works in EXE mode only.")
                return False

            exe_url = download_info.get("exe_url") if isinstance(download_info, dict) else download_info
            ico_url = download_info.get("ico_url") if isinstance(download_info, dict) else None
            if not exe_url:
                messagebox.showerror("Update Error", "Executable download link not found.")
                return False

            current_exe = os.path.abspath(sys.executable)
            install_dir = os.path.dirname(current_exe)
            exe_name = os.path.basename(current_exe)

            new_exe_path = os.path.join(install_dir, f"{exe_name}.new")
            new_icon_path = os.path.join(install_dir, "icon.ico.new")
            version_new_path = os.path.join(install_dir, "version.txt.new")

            for stale_file in (new_exe_path, new_icon_path, version_new_path):
                try:
                    if os.path.exists(stale_file):
                        os.remove(stale_file)
                except Exception:
                    pass

            self._download_file(exe_url, new_exe_path)
            if not self._is_valid_windows_exe(new_exe_path):
                try:
                    os.remove(new_exe_path)
                except Exception:
                    pass
                messagebox.showerror("Update Error", "Downloaded file is not a valid Windows executable.")
                return False

            if ico_url:
                try:
                    self._download_file(ico_url, new_icon_path)
                except Exception:
                    # Icon replacement is optional.
                    new_icon_path = ""

            with open(version_new_path, "w", encoding="utf-8") as version_file:
                version_file.write((latest_version or self.current_version).strip())

            ps_path = os.path.join(install_dir, f"_colorchem_update_{os.getpid()}.ps1")
            ps_content = f"""$ErrorActionPreference = 'Stop'
$SourcePid = {os.getpid()}
$TargetExe = '{self._ps_quote(current_exe)}'
$OldExe = '{self._ps_quote(current_exe)}.old'
$NewExe = '{self._ps_quote(new_exe_path)}'
$TargetIcon = '{self._ps_quote(os.path.join(install_dir, "icon.ico"))}'
$NewIcon = '{self._ps_quote(new_icon_path)}'
$TargetVersion = '{self._ps_quote(os.path.join(install_dir, "version.txt"))}'
$NewVersion = '{self._ps_quote(version_new_path)}'

for($i = 0; $i -lt 60; $i++) {{
    if(-not (Get-Process -Id $SourcePid -ErrorAction SilentlyContinue)) {{ break }}
    Start-Sleep -Seconds 1
}}

if(Test-Path $TargetExe) {{
    Move-Item -Force $TargetExe $OldExe
}}

if(Test-Path $NewExe) {{
    Move-Item -Force $NewExe $TargetExe
}} else {{
    throw 'Downloaded executable file not found.'
}}

if(Test-Path $NewIcon) {{
    if(Test-Path $TargetIcon) {{ Remove-Item -Force $TargetIcon -ErrorAction SilentlyContinue }}
    Move-Item -Force $NewIcon $TargetIcon
}}

if(Test-Path $NewVersion) {{
    Move-Item -Force $NewVersion $TargetVersion
}}

Start-Process -FilePath $TargetExe -WorkingDirectory '{self._ps_quote(install_dir)}'

if(Test-Path $OldExe) {{
    Remove-Item -Force $OldExe -ErrorAction SilentlyContinue
}}
Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
"""
            with open(ps_path, "w", encoding="utf-8") as script_file:
                script_file.write(ps_content)

            creation_flags = 0
            if hasattr(subprocess, "CREATE_NO_WINDOW"):
                creation_flags = subprocess.CREATE_NO_WINDOW

            system_root = os.environ.get("SystemRoot", r"C:\Windows")
            candidate_ps = os.path.join(
                system_root,
                "System32",
                "WindowsPowerShell",
                "v1.0",
                "powershell.exe",
            )
            powershell_exe = candidate_ps if os.path.exists(candidate_ps) else "powershell"
            subprocess.Popen(
                [powershell_exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path],
                cwd=install_dir,
                creationflags=creation_flags,
            )
            return True
        except Exception as exc:
            messagebox.showerror("Update Error", f"Failed to install update: {exc}")
            return False
