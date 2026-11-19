from pathlib import Path

import pytest

from app.database import DatabaseManager


@pytest.fixture
def database(tmp_path, monkeypatch):
    """Return a fresh real SQLite database isolated from user data."""
    import app.database as database_module

    db_path = tmp_path / "dyemaster-test.db"
    backup_dir = tmp_path / "backups"
    monkeypatch.setattr(database_module, "BACKUP_DIR", str(backup_dir))
    DatabaseManager._schema_verified = False
    db = DatabaseManager(str(db_path))
    yield db
    DatabaseManager._schema_verified = False


@pytest.fixture
def backup_dir(tmp_path):
    return tmp_path / "backups"
