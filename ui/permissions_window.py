"""
Admin permissions & users manager - DyeMaster Pro

Shows all users, allows editing:
- username / role / active
- per-user permission checkboxes
- reset password (without exposing existing passwords)
"""

import tkinter as tk
from tkinter import ttk, messagebox

from app.database import DatabaseManager
from app.session import SessionManager
from ui.theme_tokens import get_theme_tokens, apply_excel_treeview_style, show_on_top


PERMISSIONS_META = [
    ("can_add", "Add/Create", "Add colors and create recipes."),
    ("can_edit", "Edit/Modify", "Modify existing colors/recipes."),
    ("can_delete", "Delete", "Delete colors/recipes (destructive)."),
    ("can_manage_users", "Manage Users", "Open the Users/Permissions page and manage accounts."),
    ("can_backup", "Backup DB", "Create database backups and restore/handle safety copies."),
    ("can_import_data", "Import Data", "Import data or restore backups into the database."),
    ("can_edit_lab_settings", "Lab Settings", "Change lab defaults used in calculations/reports."),
    ("can_check_updates", "Updates", "Check for app updates and run updater actions."),
]


class PermissionsWindow:
    def __init__(self, parent, db: DatabaseManager, session: SessionManager, dark_mode: bool = False, on_changed=None):
        self.parent = parent
        self.db = db
        self.session = session
        self.dark_mode = dark_mode
        self.on_changed = on_changed

        if self.session.get_current_role() != "admin" and not self.session.has_permission("can_manage_users"):
            messagebox.showwarning("Permission Denied", "You do not have permission to manage users.", parent=parent)
            return

        self.window = tk.Toplevel(parent)
        self.window.title("Users & Permissions")
        self.window.grab_set()
        show_on_top(self.window)

        palette = get_theme_tokens(self.dark_mode)
        self.window.configure(bg=palette["bg"])

        sw, sh = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        w, h = min(int(sw * 0.92), 1200), min(int(sh * 0.88), 720)
        self.window.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.window.minsize(980, 600)

        self.style = ttk.Style(self.window)
        apply_excel_treeview_style(self.style, palette, self.dark_mode)

        self._selected_user_id = None
        self._permission_vars: dict[str, tk.BooleanVar] = {}
        self._suppress_select_event = False

        self._build()
        self._load_users()

        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        main = ttk.Frame(self.window)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: users list
        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(left, text="Users").pack(anchor="w")
        self.users_tree = ttk.Treeview(
            left,
            columns=("username", "role", "active", "last_login"),
            show="headings",
            height=18,
        )
        self.users_tree.heading("username", text="Username")
        self.users_tree.heading("role", text="Role")
        self.users_tree.heading("active", text="Active")
        self.users_tree.heading("last_login", text="Last Login")
        self.users_tree.column("username", width=180, anchor="w")
        self.users_tree.column("role", width=90, anchor="center")
        self.users_tree.column("active", width=70, anchor="center")
        self.users_tree.column("last_login", width=160, anchor="center")
        self.users_tree.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        sb = ttk.Scrollbar(left, orient="vertical", command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=sb.set)
        sb.place(in_=self.users_tree, relx=1.0, rely=0, relheight=1.0, anchor="ne")

        self.users_tree.bind("<<TreeviewSelect>>", lambda _e: self._on_user_selected())

        # Right: editor
        right = ttk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        ttk.Label(right, text="Selected User").pack(anchor="w")

        form = ttk.LabelFrame(right, text="Account", padding=10)
        form.pack(fill=tk.X, pady=(6, 10))

        self.username_var = tk.StringVar()
        self.role_var = tk.StringVar()
        self.active_var = tk.BooleanVar(value=True)
        self.last_login_var = tk.StringVar(value="—")

        r1 = ttk.Frame(form)
        r1.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(r1, text="Username:", width=12).pack(side=tk.LEFT)
        self.username_entry = ttk.Entry(r1, textvariable=self.username_var, width=22)
        self.username_entry.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(r1, text="Role:", width=6).pack(side=tk.LEFT)
        self.role_combo = ttk.Combobox(r1, textvariable=self.role_var, width=10, state="readonly")
        self.role_combo["values"] = ("admin", "tech", "viewer")
        self.role_combo.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(r1, text="Active", variable=self.active_var).pack(side=tk.LEFT)

        r2 = ttk.Frame(form)
        r2.pack(fill=tk.X)
        ttk.Label(r2, text="Last login:", width=12).pack(side=tk.LEFT)
        ttk.Label(r2, textvariable=self.last_login_var).pack(side=tk.LEFT)

        pw = ttk.LabelFrame(right, text="Reset Password", padding=10)
        pw.pack(fill=tk.X, pady=(0, 10))
        self.new_pw_var = tk.StringVar()
        self.new_pw2_var = tk.StringVar()
        pwr1 = ttk.Frame(pw)
        pwr1.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(pwr1, text="New:", width=12).pack(side=tk.LEFT)
        ttk.Entry(pwr1, textvariable=self.new_pw_var, show="*", width=22).pack(side=tk.LEFT)
        pwr2 = ttk.Frame(pw)
        pwr2.pack(fill=tk.X)
        ttk.Label(pwr2, text="Confirm:", width=12).pack(side=tk.LEFT)
        ttk.Entry(pwr2, textvariable=self.new_pw2_var, show="*", width=22).pack(side=tk.LEFT)
        ttk.Button(pw, text="Set Password", command=self._set_password, width=14).pack(anchor="e", pady=(8, 0))

        perms = ttk.LabelFrame(right, text="Permissions", padding=10)
        perms.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(perms, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb = ttk.Scrollbar(perms, orient="vertical", command=canvas.yview)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=ysb.set)

        self.perms_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self.perms_frame, anchor="nw")
        self.perms_frame.bind(
            "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        for perm_key, perm_label, perm_desc in PERMISSIONS_META:
            var = tk.BooleanVar(value=False)
            self._permission_vars[perm_key] = var
            row = ttk.Frame(self.perms_frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Checkbutton(row, text=perm_label, variable=var, width=16).pack(side=tk.LEFT)
            ttk.Label(row, text=perm_desc).pack(side=tk.LEFT, padx=(10, 0))

        actions = ttk.Frame(right)
        actions.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(actions, text="Add User", command=self._open_add_user, width=10).pack(side=tk.LEFT)
        ttk.Button(actions, text="Delete User", command=self._delete_user, width=10).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Button(actions, text="Save Changes", command=self._save_changes, width=14).pack(side=tk.RIGHT)

    def _load_users(self):
        self._suppress_select_event = True
        current_sel = self.users_tree.selection()
        selected_iid = current_sel[0] if current_sel else None

        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        users = self.db.get_users_detailed()
        for u in users:
            self.users_tree.insert(
                "",
                "end",
                iid=str(u["id"]),
                values=(
                    u["username"],
                    u["role"],
                    "Yes" if u["active"] else "No",
                    u["last_login"] or "—",
                ),
            )
        
        if selected_iid and self.users_tree.exists(selected_iid):
            self.users_tree.selection_set(selected_iid)
        
        self._suppress_select_event = False
        self.window.update_idletasks()

    def _clear_editor(self):
        self.username_var.set("")
        self.role_var.set("viewer")
        self.active_var.set(True)
        self.last_login_var.set("—")
        self.new_pw_var.set("")
        self.new_pw2_var.set("")
        for v in self._permission_vars.values():
            v.set(False)

    def _on_user_selected(self):
        if self._suppress_select_event:
            return
        sel = self.users_tree.selection()
        if not sel:
            self._selected_user_id = None
            self._clear_editor()
            return
        user_id = int(sel[0])
        self._selected_user_id = user_id

        # Load user row from tree
        vals = self.users_tree.item(sel[0], "values")
        username, role, active_text, last_login = vals[0], vals[1], vals[2], vals[3]
        self.username_var.set(username)
        self.role_var.set(role)
        self.active_var.set(active_text == "Yes")
        self.last_login_var.set(last_login or "—")
        self.new_pw_var.set("")
        self.new_pw2_var.set("")

        overrides = self.db.get_user_permission_overrides(user_id)
        # Show effective permissions: overrides if present else role defaults
        role_defaults = SessionManager.ROLES.get(str(role).strip().lower(), {})
        for perm_key, _, _ in PERMISSIONS_META:
            if perm_key in overrides:
                self._permission_vars[perm_key].set(bool(overrides[perm_key]))
            else:
                self._permission_vars[perm_key].set(bool(role_defaults.get(perm_key, False)))

    def _set_password(self):
        if not self._selected_user_id:
            messagebox.showwarning("No Selection", "Please select a user first.", parent=self.window)
            return
        pw1 = self.new_pw_var.get()
        pw2 = self.new_pw2_var.get()
        if not pw1 or not pw2:
            messagebox.showwarning("Missing", "Please enter and confirm the new password.", parent=self.window)
            return
        if pw1 != pw2:
            messagebox.showerror("Mismatch", "Passwords do not match.", parent=self.window)
            return
        if len(pw1) < 4:
            messagebox.showwarning("Weak Password", "Password must be at least 4 characters.", parent=self.window)
            return
        if messagebox.askyesno("Confirm", "Change this user's password?", parent=self.window) is not True:
            return
        ok = self.db.update_user_password(self._selected_user_id, pw1)
        if ok:
            self.new_pw_var.set("")
            self.new_pw2_var.set("")
            messagebox.showinfo("Success", "Password updated.", parent=self.window)
            self._notify_changed()
            self._load_users()

            # If the admin also edited account fields (username/role/active/permissions),
            # they must click "Save Changes" to persist those edits. Many users expect
            # the password action to save everything, so show a clear prompt.
            try:
                sel = self.users_tree.selection()
                if sel:
                    vals = self.users_tree.item(sel[0], "values")
                    current_username = str(vals[0]).strip() if vals else ""
                    current_role = str(vals[1]).strip().lower() if vals else ""
                    current_active = (str(vals[2]).strip().lower() == "yes") if vals else True

                    edited_username = (self.username_var.get() or "").strip()
                    edited_role = (self.role_var.get() or "").strip().lower()
                    edited_active = bool(self.active_var.get())

                    if (
                        edited_username
                        and (
                            edited_username != current_username
                            or edited_role != current_role
                            or edited_active != current_active
                        )
                    ):
                        messagebox.showwarning(
                            "Account Not Saved",
                            "Password was updated.\n\n"
                            "You also edited Username/Role/Active.\n"
                            "Click 'Save Changes' to apply those edits.",
                            parent=self.window,
                        )
            except Exception:
                pass
        else:
            messagebox.showerror("Error", "Failed to update password.", parent=self.window)

    def _save_changes(self):
        if not self._selected_user_id:
            messagebox.showwarning("No Selection", "Please select a user first.", parent=self.window)
            return

        new_username = self.username_var.get().strip()
        if not new_username:
            messagebox.showerror("Invalid", "Username cannot be empty.", parent=self.window)
            return

        new_role = (self.role_var.get() or "viewer").strip().lower()
        if new_role not in ("admin", "tech", "viewer"):
            messagebox.showerror("Invalid", "Role must be admin/tech/viewer.", parent=self.window)
            return

        active = bool(self.active_var.get())

        # ── Self-edit guard ──────────────────────────────────────────────
        current_uid = getattr(
            getattr(self.session, "current_user", None), "id", None
        )
        if current_uid and self._selected_user_id == current_uid:
            # Prevent admin from locking themselves out
            if not active:
                messagebox.showerror(
                    "Blocked",
                    "You cannot deactivate your own account.",
                    parent=self.window,
                )
                self.active_var.set(True)
                return
            if new_role != "admin":
                if not messagebox.askyesno(
                    "Warning",
                    "You are changing your own role away from admin.\n"
                    "This may remove your ability to manage users.\n\nContinue?",
                    parent=self.window,
                ):
                    return
            manage_perm = self._permission_vars.get("can_manage_users")
            if manage_perm and not manage_perm.get():
                if not messagebox.askyesno(
                    "Warning",
                    "You are removing your own \'Manage Users\' permission.\n"
                    "You will not be able to open this page anymore.\n\nContinue?",
                    parent=self.window,
                ):
                    return

        # Collect permissions from checkboxes and store as explicit overrides
        overrides = {k: bool(v.get()) for k, v in self._permission_vars.items()}
        updated_by = getattr(self.session.current_user, "username", None) if self.session.current_user else None

        # Apply
        if not self.db.update_user_username(self._selected_user_id, new_username):
            messagebox.showerror("Error", "Failed to update username (maybe duplicate).", parent=self.window)
            return
        self.db.update_user_role(self._selected_user_id, new_role)
        self.db.set_user_active(self._selected_user_id, active)
        self.db.set_user_permission_overrides(self._selected_user_id, overrides, updated_by=updated_by)

        messagebox.showinfo("Saved", "User changes saved.", parent=self.window)
        self._load_users()
        try:
            self.users_tree.selection_set(str(self._selected_user_id))
        except Exception:
            pass
        self._notify_changed()

    def _notify_changed(self):
        try:
            if callable(self.on_changed):
                self.on_changed()
        except Exception:
            pass

    def _on_close(self):
        # تحديث تلقائي للنافذة الأم عند إغلاق صفحة الصلاحيات لضمان مزامنة البيانات
        try:
            self._notify_changed()
        except Exception:
            pass

        try:
            self.window.grab_release()
        except Exception:
            pass
        try:
            self.window.destroy()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Add user dialog
    # ------------------------------------------------------------------

    def _open_add_user(self):
        AddUserDialog(self.window, self.db, self.session, dark_mode=self.dark_mode, on_created=self._on_user_created)

    def _delete_user(self):
        if not self._selected_user_id:
            messagebox.showwarning("No Selection", "Please select a user first.", parent=self.window)
            return

        current_uid = getattr(getattr(self.session, "current_user", None), "id", None)
        if current_uid and self._selected_user_id == current_uid:
            messagebox.showerror("Blocked", "You cannot delete your own account.", parent=self.window)
            return

        # Determine selected username/role from the tree.
        try:
            sel = self.users_tree.selection()
            vals = self.users_tree.item(sel[0], "values") if sel else ()
            username = str(vals[0]).strip() if vals else ""
            role = str(vals[1]).strip().lower() if vals else ""
        except Exception:
            username, role = "", ""

        # Block deleting the 3 primary system accounts.
        if str(username).strip().lower() in ("admin", "tech", "viewer"):
            messagebox.showerror(
                "Blocked",
                "You cannot delete the primary system accounts (admin/tech/viewer).",
                parent=self.window,
            )
            return

        # Prevent deleting the last admin account.
        try:
            users = self.db.get_users_detailed()
            admin_count = sum(1 for u in (users or []) if str(u.get("role", "")).strip().lower() == "admin")
            if role == "admin" and admin_count <= 1:
                messagebox.showerror("Blocked", "You cannot delete the last admin account.", parent=self.window)
                return
        except Exception:
            pass

        label = f"'{username}'" if username else "this user"
        if messagebox.askyesno(
            "Confirm Delete",
            f"Delete {label} permanently?\n\nThis cannot be undone.",
            parent=self.window,
        ) is not True:
            return

        ok = self.db.delete_user(self._selected_user_id)
        if not ok:
            messagebox.showerror("Error", "Failed to delete user.", parent=self.window)
            return

        messagebox.showinfo("Deleted", "User deleted.", parent=self.window)
        self._selected_user_id = None
        self._clear_editor()
        self._load_users()
        self._notify_changed()

    def _on_user_created(self, user_id: int | None):
        if not user_id:
            return
        self._load_users()
        try:
            self.users_tree.selection_set(str(user_id))
            self.users_tree.focus(str(user_id))
            self.users_tree.see(str(user_id))
            self._on_user_selected()
        except Exception:
            pass
        self._notify_changed()


class AddUserDialog:
    def __init__(self, parent, db: DatabaseManager, session: SessionManager, dark_mode: bool = False, on_created=None):
        self.parent = parent
        self.db = db
        self.session = session
        self.dark_mode = dark_mode
        self.on_created = on_created

        if session.get_current_role() != "admin" and not session.has_permission("can_manage_users"):
            messagebox.showwarning("Permission Denied", "You do not have permission to add users.", parent=parent)
            return

        self.win = tk.Toplevel(parent)
        self.win.title("Add User")
        self.win.grab_set()
        show_on_top(self.win)

        palette = get_theme_tokens(self.dark_mode)
        self.win.configure(bg=palette["bg"])

        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        w, h = min(720, int(sw * 0.7)), min(620, int(sh * 0.7))
        self.win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.win.minsize(640, 520)

        self.username_var = tk.StringVar()
        self.role_var = tk.StringVar(value="viewer")
        self.active_var = tk.BooleanVar(value=True)
        self.pw1_var = tk.StringVar()
        self.pw2_var = tk.StringVar()
        self.perm_vars = {k: tk.BooleanVar(value=False) for k, _, _ in PERMISSIONS_META}

        self._build()
        self.win.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self):
        root = ttk.Frame(self.win)
        root.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        account = ttk.LabelFrame(root, text="Account", padding=10)
        account.pack(fill=tk.X)

        r1 = ttk.Frame(account)
        r1.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(r1, text="Username:", width=12).pack(side=tk.LEFT)
        ttk.Entry(r1, textvariable=self.username_var, width=24).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(r1, text="Role:", width=6).pack(side=tk.LEFT)
        role = ttk.Combobox(r1, textvariable=self.role_var, width=10, state="readonly")
        role["values"] = ("admin", "tech", "viewer")
        role.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(r1, text="Active", variable=self.active_var).pack(side=tk.LEFT)

        r2 = ttk.Frame(account)
        r2.pack(fill=tk.X)
        ttk.Label(r2, text="Password:", width=12).pack(side=tk.LEFT)
        ttk.Entry(r2, textvariable=self.pw1_var, show="*", width=24).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(r2, text="Confirm:", width=8).pack(side=tk.LEFT)
        ttk.Entry(r2, textvariable=self.pw2_var, show="*", width=24).pack(side=tk.LEFT)

        perms = ttk.LabelFrame(root, text="Permissions (explicit)", padding=10)
        perms.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        ttk.Label(
            perms,
            text="Tip: These checkboxes are saved as per-user overrides (independent of role).",
        ).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(perms, highlightthickness=0)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb = ttk.Scrollbar(perms, orient="vertical", command=canvas.yview)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=ysb.set)

        frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

        for perm_key, perm_label, perm_desc in PERMISSIONS_META:
            row = ttk.Frame(frame)
            row.pack(fill=tk.X, pady=2)
            ttk.Checkbutton(row, text=perm_label, variable=self.perm_vars[perm_key], width=16).pack(side=tk.LEFT)
            ttk.Label(row, text=perm_desc).pack(side=tk.LEFT, padx=(10, 0))

        buttons = ttk.Frame(root)
        buttons.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(buttons, text="Cancel", command=self._close, width=10).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Create", command=self._create, width=12).pack(side=tk.RIGHT)

    def _create(self):
        username = self.username_var.get().strip()
        role = (self.role_var.get() or "viewer").strip().lower()
        active = bool(self.active_var.get())
        pw1 = self.pw1_var.get()
        pw2 = self.pw2_var.get()

        if not username:
            messagebox.showerror("Invalid", "Username cannot be empty.", parent=self.win)
            return
        if not pw1 or not pw2:
            messagebox.showerror("Invalid", "Password cannot be empty.", parent=self.win)
            return
        if pw1 != pw2:
            messagebox.showerror("Mismatch", "Passwords do not match.", parent=self.win)
            return
        if len(pw1) < 4:
            messagebox.showwarning("Weak Password", "Password must be at least 4 characters.", parent=self.win)
            return

        user_id = self.db.add_user(username=username, password=pw1, role=role, active=active)
        if not user_id:
            messagebox.showerror("Error", "Failed to create user (maybe username already exists).", parent=self.win)
            return

        overrides = {k: bool(v.get()) for k, v in self.perm_vars.items()}
        updated_by = getattr(self.session.current_user, "username", None) if self.session.current_user else None
        self.db.set_user_permission_overrides(user_id, overrides, updated_by=updated_by)

        messagebox.showinfo("Success", "User created.", parent=self.win)
        try:
            if callable(self.on_created):
                self.on_created(user_id)
        except Exception:
            pass
        self._close()

    def _close(self):
        try:
            self.win.grab_release()
        except Exception:
            pass
        try:
            self.win.destroy()
        except Exception:
            pass
