"""
شاشة تسجيل الدخول - DyeMaster Pro
"""
import tkinter as tk
from tkinter import messagebox
from app.session import SessionManager


class LoginWindow:
    """شاشة تسجيل الدخول"""
    
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
        
        # ربط Enter
        self.root.bind('<Return>', lambda e: self.login())
        
        # labels المستخدمين الافتراضيين
        info_label = tk.Label(main_frame, text="Default: admin/__DEFAULT__ | tech/__DEFAULT__ | viewer/__DEFAULT__", 
                             font=("Arial", 9), fg="#95a5a6", bg="#2c3e50")
        info_label.pack(pady=(20, 0))
    
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
