"""
شاشة تسجيل الدخول - DyeMaster Pro
"""
import tkinter as tk
from tkinter import messagebox
import os
from datetime import datetime
from app.session import SessionManager
from app.database import DatabaseManager
from app.utils import get_desktop_exports_dir
from ui.theme_tokens import show_on_top


class LoginWindow:
    """شاشة تسجيل الدخول"""

    # Fixed emergency reset code (letters/numbers only). Deliver this to the client.
    RESET_ALL_CODE = "__REDACTED__"
    
    def __init__(self, root, on_success_callback):
        self.root = root
        self.on_success_callback = on_success_callback
        self.session = SessionManager.get_session()
        
        self.create_login_ui()
    
    def create_login_ui(self):
        """إنشاء واجهة تسجيل الدخول"""
        self.root.title("DyeMaster Pro - Login")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#2c3e50")
        
        # الإطار الرئيسي
        main_frame = tk.Frame(self.root, bg="#2c3e50", padx=50, pady=50)
        main_frame.pack(expand=True)
        
        # الشعار
        title_label = tk.Label(
            main_frame, 
            text="DyeMaster Pro", 
            font=("Arial", 24, "bold"),
            fg="#ecf0f1", 
            bg="#2c3e50"
        )
        title_label.pack(pady=(0, 30))
        
        subtitle_label = tk.Label(
            main_frame,
            text="Color & Dye Management System", 
            font=("Arial", 12),
            fg="#bdc3c7", 
            bg="#2c3e50"
        )
        subtitle_label.pack(pady=(0, 40))
        
        # إطار الإدخال
        input_frame = tk.Frame(main_frame, bg="#34495e", relief="raised", bd=1, padx=30, pady=30)
        input_frame.pack(pady=20)
        
        # Username
        tk.Label(input_frame, text="Username:", font=("Arial", 11), fg="#ecf0f1", bg="#34495e").pack(anchor="w")
        self.username_var = tk.StringVar()
        username_entry = tk.Entry(input_frame, textvariable=self.username_var, font=("Arial", 11), width=25,
                                 relief="solid", bd=1, bg="white", fg="black", insertbackground="black")
        username_entry.pack(fill="x", pady=(5, 15))
        username_entry.focus_set()
        
        # Password
        tk.Label(input_frame, text="Password:", font=("Arial", 11), fg="#ecf0f1", bg="#34495e").pack(anchor="w")
        self.password_var = tk.StringVar()
        password_entry = tk.Entry(input_frame, textvariable=self.password_var, font=("Arial", 11), width=25, show="*",
                                 relief="solid", bd=1, bg="white", fg="black", insertbackground="black")
        password_entry.pack(fill="x", pady=(5, 20))
        
        # أزرار
        button_frame = tk.Frame(input_frame, bg="#34495e")
        button_frame.pack()
        
        login_btn = tk.Button(button_frame, text="Login", command=self.login,
                             font=("Arial", 11, "bold"), bg="#3498db", fg="white",
                             relief="flat", padx=20, pady=5, cursor="hand2")
        login_btn.pack(side="right", padx=(10, 0))

        reset_btn = tk.Button(
            button_frame,
            text="Reset All Passwords",
            command=self.reset_all_passwords,
            font=("Arial", 9, "bold"),
            bg="#e67e22",
            fg="white",
            relief="flat",
            padx=12,
            pady=5,
            cursor="hand2",
        )
        reset_btn.pack(side="left", padx=(0, 10))
        
        # ربط Enter
        self.root.bind('<Return>', lambda e: self.login())
        
        # Note: Default credentials are documented in the admin guide
        # Not displayed in UI for security reasons
    
    def login(self):
        """معالج تسجيل الدخول"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        if self.session.login(username, password):
            messagebox.showinfo("Success", f"Welcome {username} ({self.session.get_current_role().title()})!")
            self.on_success_callback()
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Invalid username or password!")
            self.password_var.set("")
            self.username_var.set("")

    def reset_all_passwords(self):
        """Emergency: restore default system users (admin/tech/viewer) if code matches."""
        entered = ResetCodeDialog.ask(self.root)
        if entered is None:
            return
        if entered.strip() != self.RESET_ALL_CODE:
            messagebox.showerror("Denied", "Invalid reset code.", parent=self.root)
            return

        if messagebox.askyesno(
            "Confirm",
            "This will restore default system users passwords:\n"
            "admin/__DEFAULT__\ntech/__DEFAULT__\nviewer/__DEFAULT__\n\nContinue?",
            parent=self.root,
        ) is not True:
            return

        db = DatabaseManager()
        ok = db.reset_default_system_users()
        if not ok:
            messagebox.showerror("Error", "Password reset failed.", parent=self.root)
            return

        messagebox.showinfo(
            "Done",
            "Default system users restored:\n\n"
            "admin / __DEFAULT__\n"
            "tech  / __DEFAULT__\n"
            "viewer / __DEFAULT__\n\n"
            "Other users were NOT changed.",
            parent=self.root,
        )


class ResetCodeDialog:
    """Small dialog that makes copy/paste easy for reset-code entry."""

    @staticmethod
    def ask(parent) -> str | None:
        win = tk.Toplevel(parent)
        win.title("Reset All Passwords")
        win.resizable(False, False)

        result = {"value": None}

        frame = tk.Frame(win, padx=14, pady=12)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Enter reset code (letters/numbers):").pack(anchor="w")

        code_var = tk.StringVar()
        entry = tk.Entry(frame, textvariable=code_var, width=34)
        entry.pack(fill="x", pady=(6, 10))
        entry.focus_set()

        btns = tk.Frame(frame)
        btns.pack(fill="x")

        def do_paste():
            try:
                text = parent.clipboard_get()
                code_var.set((text or "").strip())
                entry.icursor(tk.END)
            except Exception:
                pass

        def do_ok():
            result["value"] = code_var.get().strip()
            win.destroy()

        def do_cancel():
            result["value"] = None
            win.destroy()

        tk.Button(btns, text="Paste", command=do_paste, width=10).pack(side="left")
        tk.Button(btns, text="Cancel", command=do_cancel, width=10).pack(side="right", padx=(8, 0))
        tk.Button(btns, text="OK", command=do_ok, width=10).pack(side="right")

        win.bind("<Return>", lambda _e: do_ok())
        win.bind("<Escape>", lambda _e: do_cancel())
        win.transient(parent)
        show_on_top(win, parent)

        parent.wait_window(win)
        return result["value"]
