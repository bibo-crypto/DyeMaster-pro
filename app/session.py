"""
Session and permission manager - DyeMaster Pro
"""
import hashlib
from app.database import DatabaseManager


class SessionManager:
    """Manage current logged-in user and role permissions."""

    ROLES = {
        "admin": {
            "can_add": True,
            "can_edit": True,
            "can_delete": True,
            "can_manage_users": True,
            "can_backup": True,
            "can_import_data": True,
            "can_edit_lab_settings": True,
            "can_check_updates": True,
        },
        "tech": {
            "can_add": True,
            "can_edit": True,
            "can_delete": False,
            "can_manage_users": False,
            "can_backup": False,
            "can_import_data": False,
            "can_edit_lab_settings": False,
            "can_check_updates": True,
        },
        "viewer": {
            "can_add": False,
            "can_edit": False,
            "can_delete": False,
            "can_manage_users": False,
            "can_backup": False,
            "can_import_data": False,
            "can_edit_lab_settings": False,
            "can_check_updates": False,
        },
    }

    def __init__(self):
        self.current_user = None
        self.db = DatabaseManager()

    def login(self, username: str, password: str) -> bool:
        """Authenticate user and open session."""
        user = self.db.get_user_by_username(username)
        if user and self._verify_password(password, user.password_hash):
            self.current_user = user
            self.db.update_user_last_login(user.id)
            return True
        return False

    def logout(self):
        """Close current session."""
        self.current_user = None

    def _verify_password(self, password: str, hash_str: str) -> bool:
        """Verify password hash (SHA256)."""
        return hashlib.sha256(password.encode()).hexdigest() == hash_str

    def _normalize_role(self, role: str) -> str:
        role_value = (role or "").strip().lower()
        if role_value == "technician":
            return "tech"
        if role_value in ("view", "read_only", "readonly"):
            return "viewer"
        return role_value

    def has_permission(self, permission: str) -> bool:
        """Check whether current user has a specific permission."""
        if not self.current_user:
            return False
        role = self._normalize_role(self.current_user.role)
        role_perms = self.ROLES.get(role, {})
        return role_perms.get(permission, False)

    def get_current_role(self) -> str:
        """Return normalized current role."""
        if not self.current_user:
            return "guest"
        return self._normalize_role(self.current_user.role)

    @classmethod
    def get_session(cls) -> "SessionManager":
        """Singleton accessor."""
        if not hasattr(cls, "_instance"):
            cls._instance = cls()
        return cls._instance
