import base64
import hashlib
import json
import os
import platform
import uuid
from dataclasses import dataclass

import tkinter as tk
from tkinter import messagebox, ttk

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from app.config import APP_ID, APP_DISPLAY_NAME, USER_DATA_DIR

# Public key used to verify customer serials.
DEFAULT_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEA1I4CMRR5u7LHK/YiL/krfNBoBn/PVVl860weDAHless=
-----END PUBLIC KEY-----
"""


@dataclass
class LicenseStatus:
    ok: bool
    reason: str = ""
    payload: dict | None = None


def _b64url_decode(text: str) -> bytes:
    pad = "=" * ((4 - len(text) % 4) % 4)
    return base64.urlsafe_b64decode((text + pad).encode("ascii"))


def _license_dir() -> str:
    path = os.path.join(USER_DATA_DIR, "license")
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except Exception:
        fallback = os.path.join(os.getcwd(), ".license_data")
        os.makedirs(fallback, exist_ok=True)
        return fallback


def _activation_file() -> str:
    return os.path.join(_license_dir(), "activation.json")


def _installer_serial_file() -> str:
    return os.path.join(_license_dir(), "serial.txt")


def _public_key_pem() -> str:
    env_key = os.environ.get("DYEMASTER_LICENSE_PUBLIC_KEY", "").strip()
    return env_key if env_key else DEFAULT_PUBLIC_KEY_PEM


def _public_key() -> Ed25519PublicKey:
    return serialization.load_pem_public_key(_public_key_pem().encode("utf-8"))


def get_device_id() -> str:
    raw = "|".join([
        str(uuid.getnode()),
        platform.node(),
        platform.machine(),
        platform.system(),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20].upper()


def _verify_serial(serial_code: str) -> LicenseStatus:
    try:
        parts = serial_code.strip().split(".")
        if len(parts) != 2:
            return LicenseStatus(False, "Invalid serial format")

        payload_b64, sig_b64 = parts
        payload_raw = _b64url_decode(payload_b64)
        signature = _b64url_decode(sig_b64)

        try:
            _public_key().verify(signature, payload_raw)
        except InvalidSignature:
            return LicenseStatus(False, "Invalid serial signature")

        payload = json.loads(payload_raw.decode("utf-8"))

        if payload.get("product") != APP_ID:
            return LicenseStatus(False, "Serial is for another product")

        slot = int(payload.get("slot", 0))
        if slot < 1 or slot > 3:
            return LicenseStatus(False, "Serial slot is out of allowed range (1..3)")

        if payload.get("device_id") != get_device_id():
            return LicenseStatus(False, "Serial does not belong to this device")

        return LicenseStatus(True, payload=payload)
    except Exception as exc:
        return LicenseStatus(False, f"Serial validation failed: {exc}")


def _save_activation(serial_code: str, payload: dict) -> None:
    data = {
        "serial_code": serial_code.strip(),
        "license_id": payload.get("license_id", ""),
        "slot": payload.get("slot", ""),
        "device_id": payload.get("device_id", ""),
    }
    try:
        with open(_activation_file(), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        return
    except Exception:
        pass

    # Fallback to workspace-local file if LOCALAPPDATA write is blocked.
    try:
        fallback_dir = os.path.join(os.getcwd(), ".license_data")
        os.makedirs(fallback_dir, exist_ok=True)
        with open(os.path.join(fallback_dir, "activation.json"), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _load_serial_candidates() -> list[str]:
    codes: list[str] = []

    path = _activation_file()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8-sig") as fh:
                data = json.load(fh)
            code = str(data.get("serial_code", "")).strip()
            if code:
                codes.append(code)
        except Exception:
            pass

    path2 = _installer_serial_file()
    if os.path.exists(path2):
        try:
            with open(path2, "r", encoding="utf-8-sig") as fh:
                code = fh.read().strip()
            if code and code not in codes:
                codes.append(code)
        except Exception:
            pass

    return codes


def current_license_status() -> LicenseStatus:
    codes = _load_serial_candidates()
    if not codes:
        return LicenseStatus(False, "No serial found")

    first_error: LicenseStatus | None = None
    for code in codes:
        st = _verify_serial(code)
        if st.ok:
            _save_activation(code, st.payload or {})
            return st
        if first_error is None:
            first_error = st

    return first_error or LicenseStatus(False, "No serial found")


def activate_with_serial(serial_code: str) -> LicenseStatus:
    st = _verify_serial(serial_code)
    if st.ok:
        _save_activation(serial_code, st.payload or {})
    return st


class _SerialDialog:
    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.ok = False

        self.win = tk.Toplevel(parent)
        self.win.title(f"{APP_DISPLAY_NAME} Activation")
        self.win.geometry("700x330")
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        self.win.lift()
        self.win.focus_force()
        self.win.attributes("-topmost", True)
        self.win.after(250, lambda: self.win.attributes("-topmost", False))
        self.win.update_idletasks()
        try:
            sw = self.win.winfo_screenwidth()
            sh = self.win.winfo_screenheight()
            ww = self.win.winfo_width()
            wh = self.win.winfo_height()
            x = max(0, (sw - ww) // 2)
            y = max(0, (sh - wh) // 3)
            self.win.geometry(f"{ww}x{wh}+{x}+{y}")
        except Exception:
            pass

        frame = ttk.Frame(self.win, padding=14)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"{APP_DISPLAY_NAME} needs activation", font=("Arial", 11, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Paste your serial code from the customer TXT file.").pack(anchor="w", pady=(4, 10))

        ttk.Label(frame, text=f"Device ID: {get_device_id()}", foreground="#1f4f99").pack(anchor="w", pady=(0, 8))

        ttk.Label(frame, text="Serial code:").pack(anchor="w")
        self.serial_box = tk.Text(frame, height=8, wrap=tk.WORD)
        self.serial_box.pack(fill=tk.BOTH, expand=True, pady=(4, 8))

        row = ttk.Frame(frame)
        row.pack(fill=tk.X)
        ttk.Button(row, text="Activate", command=self._activate).pack(side=tk.LEFT)
        ttk.Button(row, text="Exit", command=self._exit).pack(side=tk.RIGHT)

        self.win.protocol("WM_DELETE_WINDOW", self._exit)

    def _activate(self):
        code = self.serial_box.get("1.0", tk.END).strip()
        st = activate_with_serial(code)
        if st.ok:
            messagebox.showinfo("Activation", "Activation successful.")
            self.ok = True
            self.win.destroy()
            return
        messagebox.showerror("Activation Failed", st.reason)

    def _exit(self):
        self.ok = False
        self.win.destroy()


def ensure_license_activated(root: tk.Tk) -> bool:
    st = current_license_status()
    if st.ok:
        return True

    try:
        root.deiconify()
        root.lift()
        root.focus_force()
        root.attributes("-topmost", True)
        root.after(200, lambda: root.attributes("-topmost", False))
    except Exception:
        pass

    dlg = _SerialDialog(root)
    root.wait_window(dlg.win)
    if dlg.ok:
        root.deiconify()
        return True
    return False
