"""
In-app updater for PyInstaller --onedir builds.

GitHub Release format expected:
  - Asset: main.zip  (contains the full onedir folder: main.exe + _internal/ + DLLs)
  - Asset: version.txt  (optional, plain text version number)

Update flow:
  1. Download main.zip into a staging folder next to the current exe
  2. Extract zip into staging/_new_version/
  3. Write a .bat that:
       a) Waits for this process to exit (tasklist loop)
       b) Renames current folder contents to .old
       c) Moves new contents into place
       d) Launches new main.exe
       e) Cleans up .old files and itself
"""

import hashlib
import ctypes
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import zipfile

import requests


# ─────────────────────────────────────────────────────────────────────────── #

def _get_install_dir() -> str:
    """Folder that contains the running executable (works for onedir & onefile)."""
    return os.path.dirname(os.path.abspath(sys.executable))


def _is_dir_writable(path: str) -> bool:
    """Best-effort check whether current user can write in target directory."""
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, f".write_test_{os.getpid()}.tmp")
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write("ok")
        os.remove(probe)
        return True
    except Exception:
        return False


def _get_user_update_root() -> str:
    """Per-user writable folder used for updater staging and batch file."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "ColorChemSystem")


def _get_pending_restore_marker() -> str:
    """Marker file that points to DB backup to restore after updater launches new version."""
    try:
        from app.config import BACKUP_DIR
        os.makedirs(BACKUP_DIR, exist_ok=True)
        return os.path.join(BACKUP_DIR, "pending_update_restore.txt")
    except Exception:
        return os.path.join(_get_user_update_root(), "pending_update_restore.txt")


def _write_pending_restore(backup_path: str):
    marker = _get_pending_restore_marker()
    try:
        os.makedirs(os.path.dirname(marker), exist_ok=True)
        with open(marker, "w", encoding="utf-8") as fh:
            fh.write(backup_path or "")
    except Exception:
        pass


def _clear_pending_restore():
    marker = _get_pending_restore_marker()
    try:
        if os.path.exists(marker):
            os.remove(marker)
    except Exception:
        pass


def _read_pending_restore() -> str | None:
    marker = _get_pending_restore_marker()
    if os.path.exists(marker):
        try:
            with open(marker, "r", encoding="utf-8") as fh:
                path = fh.read().strip()
                return path if path else None
        except Exception:
            return None
    return None


# ─────────────────────────────────────────────────────────────────────────── #

class AppUpdater:
    def __init__(self, current_version: str = "1.0.0"):
        self.repo_owner      = "bibo-crypto"
        self.repo_name       = "DyeMaster-pro"
        self.current_version = (current_version or "1.0.0").strip()
        self.api_url = (
            f"https://api.github.com/repos/"
            f"{self.repo_owner}/{self.repo_name}/releases/latest"
        )

    # ── Public API ────────────────────────────────────────────────────── #

    def check_for_updates(self):
        ok, ver, notes, payload = self.get_latest_release()
        if not ok:
            return False, self.current_version, "", None
        return self._is_newer(ver, self.current_version), ver, notes, payload

    def get_latest_release(self):
        try:
            headers  = {"Accept": "application/vnd.github.v3+json"}
            resp     = self._http_get(self.api_url, headers=headers, timeout=15)
            resp.raise_for_status()
            data     = resp.json()
            raw_ver  = data.get("tag_name", self.current_version)
            ver      = raw_ver.lstrip("vV").strip() or self.current_version
            zip_url, ver_url = self._extract_asset_urls(data)
            if not zip_url:
                return False, self.current_version, "", None
            payload = {"zip_url": zip_url, "ver_url": ver_url}
            return True, ver, data.get("body", ""), payload
        except Exception as exc:
            print(f"[Updater] get_latest_release: {exc}")
            return False, self.current_version, "", None

    def download_and_install(self, download_info, latest_version, parent_window=None, db_backup_path=None):
        """
        Download the zip release, extract it, then hand off to a .bat for the swap.
        Returns True when the batch updater has been launched.
        Caller must immediately call sys.exit(0).

        db_backup_path: path to database backup to be restored automatically after update.
        """
        try:
            if not getattr(sys, "frozen", False):
                messagebox.showwarning(
                    "Update",
                    "Automatic update only works when running as a compiled EXE."
                )
                return False

            zip_url = (
                download_info.get("zip_url")
                if isinstance(download_info, dict) else download_info
            )
            if not zip_url:
                messagebox.showerror("Update Error", "No download URL found in release.")
                _clear_pending_restore()
                return False

            if db_backup_path:
                _write_pending_restore(db_backup_path)

            install_dir = _get_install_dir()          # e.g. E:\dist\main
            exe_name    = os.path.basename(sys.executable)   # main.exe
            exe_stem    = os.path.splitext(exe_name)[0]      # main
            current_exe = os.path.abspath(sys.executable)

            # Staging paths – all inside install_dir (same NTFS volume)
            install_writable = _is_dir_writable(install_dir)
            staging_root = install_dir if install_writable else _get_user_update_root()
            os.makedirs(staging_root, exist_ok=True)

            staging_dir  = os.path.join(staging_root, "_update_staging")
            zip_path     = os.path.join(staging_dir, "update.zip")
            extract_dir  = os.path.join(staging_dir, "extracted")
            bat_path     = os.path.join(staging_root, f"_{exe_stem}_update.bat")

            # Clean up old staging
            for path in (bat_path,):
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass
            if os.path.exists(staging_dir):
                shutil.rmtree(staging_dir, ignore_errors=True)
            os.makedirs(staging_dir, exist_ok=True)

            # ── Progress window ──────────────────────────────────────── #
            result_holder  = [None]
            progress_win   = None
            progress_var   = None
            progress_label = None
            speed_label    = None
            eta_label      = None

            try:
                progress_win = tk.Toplevel(parent_window)
                progress_win.title("Downloading Update")
                progress_win.geometry("460x185")
                progress_win.resizable(False, False)
                if parent_window:
                    progress_win.transient(parent_window)
                progress_win.lift()
                progress_win.focus_force()
                progress_win.grab_set()
                progress_win.attributes("-topmost", True)
                progress_win.after(250, lambda: progress_win.attributes("-topmost", False))

                tk.Label(
                    progress_win,
                    text="Downloading new version – please wait…",
                    font=("Arial", 10, "bold"),
                    pady=10,
                ).pack()

                progress_var = tk.DoubleVar(value=0)
                ttk.Progressbar(
                    progress_win,
                    variable=progress_var,
                    maximum=100,
                    length=410,
                    mode="determinate",
                ).pack(pady=4, padx=20)

                progress_label = tk.Label(progress_win, text="Connecting…", font=("Arial", 9))
                progress_label.pack()
                speed_label = tk.Label(progress_win, text="", font=("Arial", 9), fg="#555")
                speed_label.pack()
                eta_label = tk.Label(progress_win, text="", font=("Arial", 9), fg="#555")
                eta_label.pack()
                progress_win.update()
            except Exception:
                progress_win = None

            import time as _time
            _t0        = [_time.monotonic()]
            _last_b    = [0]
            _last_t    = [_time.monotonic()]

            def _on_progress(done: int, total: int):
                if not progress_win:
                    return
                now = _time.monotonic()
                dt  = now - _last_t[0]
                if dt > 0.2:
                    spd      = (done - _last_b[0]) / dt
                    _last_b[0] = done
                    _last_t[0] = now
                    spd_str  = (f"{spd/1048576:.1f} MB/s" if spd >= 1048576
                                else f"{spd/1024:.0f} KB/s")
                    speed_label.config(text=f"Speed: {spd_str}")
                if total > 0:
                    pct     = done / total * 100
                    done_mb = done  / 1048576
                    tot_mb  = total / 1048576
                    elapsed = now - _t0[0]
                    avg     = done / elapsed if elapsed > 0 else 0
                    rem     = (total - done) / avg if avg > 0 else 0
                    progress_var.set(pct)
                    progress_label.config(
                        text=f"{pct:.1f}%   –   {done_mb:.1f} MB / {tot_mb:.1f} MB"
                    )
                    if rem > 0:
                        eta_label.config(
                            text=(f"Time remaining: {rem:.0f} sec"
                                  if rem < 60 else f"Time remaining: {rem/60:.1f} min")
                        )
                else:
                    progress_label.config(text=f"Downloaded: {done//1024} KB")
                    progress_var.set((progress_var.get() + 1) % 100)
                progress_win.update()

            def _do_download():
                try:
                    self._download_file(zip_url, zip_path, progress_callback=_on_progress)
                    result_holder[0] = True
                except Exception as exc:
                    result_holder[0] = exc
                finally:
                    if progress_win:
                        try:
                            progress_win.after(0, progress_win.destroy)
                        except Exception:
                            pass

            dl_thread = threading.Thread(target=_do_download, daemon=True)
            dl_thread.start()
            if progress_win:
                progress_win.wait_window()
            dl_thread.join(timeout=15)

            if isinstance(result_holder[0], Exception):
                messagebox.showerror("Update Error", f"Download failed:\n{result_holder[0]}")
                shutil.rmtree(staging_dir, ignore_errors=True)
                return False
            if result_holder[0] is not True:
                messagebox.showerror("Update Error", "Download did not complete.")
                shutil.rmtree(staging_dir, ignore_errors=True)
                return False

            # ── Validate & extract zip ───────────────────────────────── #
            if not zipfile.is_zipfile(zip_path):
                messagebox.showerror("Update Error", "Downloaded file is not a valid ZIP.")
                shutil.rmtree(staging_dir, ignore_errors=True)
                return False

            os.makedirs(extract_dir, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            # Find the new exe inside the extracted folder.
            # Supports two layouts:
            #   Layout A: extracted/main.exe  (flat)
            #   Layout B: extracted/main/main.exe  (subfolder = zip root folder)
            new_exe = self._find_exe_in_dir(extract_dir, exe_name)
            if not new_exe:
                messagebox.showerror(
                    "Update Error",
                    f"Could not find {exe_name} inside the downloaded ZIP.\n"
                    f"Please make sure the release ZIP contains the correct files."
                )
                shutil.rmtree(staging_dir, ignore_errors=True)
                return False

            new_exe_dir = os.path.dirname(new_exe)   # folder containing new exe

            # Write version.txt into staging so bat can deploy it
            ver_target_in_staging = os.path.join(new_exe_dir, "version.txt")
            try:
                with open(ver_target_in_staging, "w", encoding="utf-8") as vf:
                    vf.write((latest_version or self.current_version).strip())
            except Exception:
                pass

            # ── Build the batch updater ──────────────────────────────── #
            # Strategy:
            #   - cd into install_dir
            #   - rename main.exe → main.exe.old
            #   - copy all files from new_exe_dir → install_dir  (xcopy)
            #   - launch new main.exe
            #   - cleanup

            pid = os.getpid()

            bat = [
                "@echo off",
                "setlocal",
                f'cd /D "{install_dir}"',
                "",
                ":: ── Wait for old process to exit ──────────────────────────",
                ":WAIT",
                f'  tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul 2>&1',
                "  if not errorlevel 1 (",
                "    ping 127.0.0.1 -n 2 -w 1000 >nul",
                "    goto WAIT",
                "  )",
                ":: Extra settle – wait for Windows to release file handles",
                "ping 127.0.0.1 -n 5 -w 1000 >nul",
                "",
                ":: ── Backup current exe ─────────────────────────────────────",
                f'if exist "{exe_name}.old" del /F /Q "{exe_name}.old"',
                f'ren "{exe_name}" "{exe_name}.old"',
                f'if not exist "{exe_name}.old" (',
                '  echo ERROR: Could not rename current exe - aborting.',
                '  goto CLEANUP',
                ')',
                "",
                ":: ── Copy new files into place (xcopy overwrites everything) ─",
                f'xcopy /E /Y /I /Q "{new_exe_dir}\\*" "{install_dir}\\"',
                f'if not exist "{exe_name}" (',
                '  echo ERROR: New exe not found after copy - rolling back.',
                f'  ren "{exe_name}.old" "{exe_name}"',
                '  goto CLEANUP',
                ')',
                "",
                ":: ── Launch new version ─────────────────────────────────────",
                f'start "" /D "{install_dir}" "{current_exe}"',
                "",
                ":CLEANUP",
                "ping 127.0.0.1 -n 4 -w 1000 >nul",
                f'if exist "{exe_name}.old" del /F /Q "{exe_name}.old"',
                f'if exist "{staging_dir}" rmdir /S /Q "{staging_dir}"',
                'del /F /Q "%~f0"',
                "endlocal",
            ]

            bat_content = "\r\n".join(bat) + "\r\n"
            with open(bat_path, "w", encoding="ascii", errors="replace") as bf:
                bf.write(bat_content)

            # ── Launch batch ─────────────────────────────────────────── #
            if install_writable:
                subprocess.Popen(
                    ["cmd.exe", "/C", bat_path],
                    cwd=install_dir,
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    close_fds=True,
                )
            else:
                # Protected install path (Program Files): require elevation for file replacement.
                rc = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    "cmd.exe",
                    f'/C "{bat_path}"',
                    install_dir,
                    0,
                )
                if int(rc) <= 32:
                    raise RuntimeError(
                        "Failed to start elevated updater (UAC denied or unavailable)."
                    )
            return True   # caller must immediately call sys.exit(0)

        except Exception as exc:
            try:
                if progress_win:
                    progress_win.destroy()
            except Exception:
                pass
            _clear_pending_restore()
            messagebox.showerror("Update Error", f"Failed to prepare update:\n{exc}")
            return False

    # ── Internal helpers ──────────────────────────────────────────────── #

    def _find_exe_in_dir(self, root: str, exe_name: str) -> str | None:
        """
        Search for exe_name inside root, up to 2 levels deep.
        Returns full path or None.
        """
        # Level 0: root/main.exe
        candidate = os.path.join(root, exe_name)
        if os.path.isfile(candidate):
            return candidate
        # Level 1: root/subfolder/main.exe
        try:
            for entry in os.scandir(root):
                if entry.is_dir():
                    candidate = os.path.join(entry.path, exe_name)
                    if os.path.isfile(candidate):
                        return candidate
        except Exception:
            pass
        return None

    def _extract_asset_urls(self, release_data):
        """
        Look for a .zip asset (preferred) that contains the full app folder,
        and optionally a version.txt asset.
        Falls back to .exe if no zip found (onefile compatibility).
        """
        zip_url = None
        ver_url = None

        exe_stem = ""
        try:
            exe_stem = os.path.splitext(os.path.basename(sys.executable))[0].lower()
        except Exception:
            pass

        zip_candidates = []
        exe_candidates = []

        for asset in release_data.get("assets", []):
            raw  = asset.get("name", "")
            name = raw.lower()
            url  = asset.get("browser_download_url")
            if not url:
                continue

            if name == "version.txt":
                ver_url = url

            elif name.endswith(".zip"):
                score = 0
                if exe_stem and exe_stem in name: score += 50
                if any(t in name for t in ("colorchem", "dyemaster", "main")): score += 20
                zip_candidates.append((score, raw, url))

            elif name.endswith(".exe"):
                score = 0
                if exe_stem and exe_stem in name: score += 50
                if any(t in name for t in ("colorchem", "dyemaster", "main")): score += 20
                if any(b in name for b in ("setup", "installer")): score -= 20
                exe_candidates.append((score, raw, url))

        # Prefer zip over exe (onedir support)
        if zip_candidates:
            zip_candidates.sort(key=lambda x: x[0], reverse=True)
            _, best_name, zip_url = zip_candidates[0]
            print(f"[Updater] selected ZIP: {best_name}")
        elif exe_candidates:
            exe_candidates.sort(key=lambda x: x[0], reverse=True)
            _, best_name, zip_url = exe_candidates[0]   # reuse zip_url slot
            print(f"[Updater] selected EXE (no zip found): {best_name}")

        return zip_url, ver_url

    def _http_get(self, url, **kwargs):
        try:
            return requests.get(url, **kwargs)
        except requests.exceptions.RequestException:
            s = requests.Session()
            s.trust_env = False
            return s.get(url, **kwargs)

    def _download_file(self, url: str, destination: str, progress_callback=None):
        if url.startswith("file://"):
            shutil.copy2(url[7:], destination)
            return
        tmp     = destination + ".part"
        written = 0
        try:
            with self._http_get(url, stream=True, timeout=(20, 600)) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                with open(tmp, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=256 * 1024):
                        if chunk:
                            fh.write(chunk)
                            written += len(chunk)
                            if progress_callback:
                                progress_callback(written, total)
            if written == 0:
                raise RuntimeError("Downloaded file is empty.")
            if os.path.exists(destination):
                os.remove(destination)
            os.replace(tmp, destination)
        except Exception:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            raise

    def _is_newer(self, latest: str, current: str) -> bool:
        def _v(s):
            parts = []
            for p in str(s).split("."):
                try:    parts.append(int(p))
                except: parts.append(0)
            while len(parts) < 3:
                parts.append(0)
            return tuple(parts[:3])
        try:
            return _v(latest) > _v(current)
        except Exception:
            return str(latest) > str(current)

    def _calculate_file_hash(self, path: str, algo: str = "sha256"):
        h = hashlib.new(algo)
        try:
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None
