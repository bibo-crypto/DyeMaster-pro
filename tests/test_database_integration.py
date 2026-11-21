from pathlib import Path

import pytest

from app.database import DatabaseManager
from app.models import Chemical, Color, Recipe
from app.session import SessionManager


def add_color(db, code, name):
    return db.add_color(
        Color(
            code=code,
            name=name,
            dye_type="Indanthren IN",
            supplier="Test Supplier",
            price_kg=10.0,
            resa_percent=100.0,
            created_at="2026-01-01 00:00:00",
            updated_at="2026-01-01 00:00:00",
        )
    )


def add_typed_color(db, code, name, dye_type):
    return db.add_color(
        Color(
            code=code,
            name=name,
            dye_type=dye_type,
            supplier="Test Supplier",
            price_kg=10.0,
            resa_percent=100.0,
            created_at="2026-01-01 00:00:00",
            updated_at="2026-01-01 00:00:00",
        )
    )


def test_database_creates_expected_tables(database):
    with database.get_connection() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"colors", "recipes", "recipe_colors", "recipe_chemicals", "users"} <= tables


def test_recipe_round_trip_preserves_colors_and_chemicals(database):
    add_color(database, "12345", "Red A")
    recipe_id = database.add_recipe(
        Recipe(recipe_code="12", name="Batch recipe", created_at="2026-01-01 00:00:00"),
        [{"code": "12345", "percentage": 2.5}],
        [Chemical(code="SALT", name="Salt", quantity=1.2, unit="kg")],
    )

    details = database.get_recipe_details(recipe_id)
    assert details["recipe"].recipe_code == "000012"
    assert details["colors"][0]["code"] == "12345"
    assert details["total_percentage"] == pytest.approx(2.5)
    assert details["chemicals"][0].name == "Salt"


def test_recipe_insert_rolls_back_when_color_is_missing(database):
    with pytest.raises(Exception, match="Unregistered color"):
        database.add_recipe(
            Recipe(recipe_code="123456", name="Invalid", created_at="2026-01-01 00:00:00"),
            [{"code": "99999", "percentage": 1.0}],
        )
    assert database.get_recipe_by_code("123456") is None


def test_passwords_are_hashed_and_session_permissions_work(database):
    user_id = database.add_user("operator", "correct horse", role="tech")
    assert user_id is not None
    user = database.get_user_by_username("operator")
    assert user is not None
    assert user.password_hash != "correct horse"
    assert database.verify_password("correct horse", user.password_hash)
    assert not database.verify_password("wrong", user.password_hash)

    session = SessionManager()
    session.db = database
    assert session.login("operator", "correct horse")
    assert session.has_permission("can_add")
    assert not session.has_permission("can_delete")


def test_backup_and_restore_keep_existing_recipe(database, tmp_path):
    add_color(database, "12345", "Red A")
    recipe_id = database.add_recipe(
        Recipe(recipe_code="123456", name="Original", created_at="2026-01-01 00:00:00"),
        [{"code": "12345", "percentage": 1.0}],
    )
    backup = database.backup_database()
    assert backup and Path(backup).is_file()

    assert database.update_recipe(recipe_id, "123457", "Changed")[0]
    assert database.restore_database(backup)
    assert database.get_recipe_by_id(recipe_id).name == "Original"
    assert database.get_recipe_by_id(recipe_id).recipe_code == "123456"


def test_recipe_editor_replaces_colors_atomically_and_records_history(database):
    add_color(database, "12345", "Red A")
    add_color(database, "54321", "Blue B")
    recipe_id = database.add_recipe(
        Recipe(recipe_code="123456", name="Original", created_at="2026-01-01 00:00:00"),
        [{"code": "12345", "percentage": 1.0}],
    )

    ok, message = database.update_recipe_contents(
        recipe_id,
        "123457",
        "Edited",
        [{"code": "54321", "percentage": 2.0}],
        [Chemical(code="ALK", name="Alkali", quantity=3.0, unit="g/l")],
        changed_by="operator",
    )
    assert ok, message
    details = database.get_recipe_details(recipe_id)
    assert details["recipe"].name == "Edited"
    assert details["colors"][0]["code"] == "54321"
    history = database.get_recipe_history(recipe_id)
    assert len(history) == 1
    assert history[0]["changed_by"] == "operator"
    assert history[0]["old_data"]["colors"][0]["code"] == "12345"
    assert history[0]["new_data"]["colors"][0]["code"] == "54321"


def test_recipe_editor_rejects_duplicate_colors_without_mutating_original(database):
    add_color(database, "12345", "Red A")
    recipe_id = database.add_recipe(
        Recipe(recipe_code="123456", name="Original", created_at="2026-01-01 00:00:00"),
        [{"code": "12345", "percentage": 1.0}],
    )
    ok, _ = database.update_recipe_contents(
        recipe_id,
        "123456",
        "Should Not Save",
        [{"code": "12345", "percentage": 1.0}, {"code": "12345", "percentage": 2.0}],
    )
    assert not ok
    assert database.get_recipe_by_id(recipe_id).name == "Original"
    assert database.get_recipe_history(recipe_id) == []


def test_replace_recipe_color_preserves_percentage_and_creates_no_new_recipe(database):
    add_color(database, "12345", "Red A")
    add_color(database, "54321", "Blue B")
    recipe_id = database.add_recipe(
        Recipe(recipe_code="123456", name="Replace me", created_at="2026-01-01 00:00:00"),
        [{"code": "12345", "percentage": 2.5}],
    )

    ok, message = database.replace_recipe_color(recipe_id, "12345", "54321", changed_by="operator")
    assert ok, message
    assert len(database.get_all_recipes()) == 1
    details = database.get_recipe_details(recipe_id)
    assert details["colors"][0]["code"] == "54321"
    assert details["colors"][0]["percentage"] == pytest.approx(2.5)
    assert details["chemicals"]
    history = database.get_recipe_history(recipe_id)
    assert history[0]["operation"] == "replace_color"
    assert history[0]["changed_by"] == "operator"
    assert history[0]["new_data"]["operation_details"] == {
        "old_color_code": "12345", "new_color_code": "54321"
    }


def test_replace_recipe_color_rejects_unregistered_color_without_history(database):
    add_color(database, "12345", "Red A")
    recipe_id = database.add_recipe(
        Recipe(recipe_code="123456", name="Replace me", created_at="2026-01-01 00:00:00"),
        [{"code": "12345", "percentage": 2.5}],
    )
    ok, message = database.replace_recipe_color(recipe_id, "12345", "00001")
    assert not ok
    assert "Unregistered color" in message
    assert database.get_recipe_details(recipe_id)["colors"][0]["code"] == "12345"
    assert database.get_recipe_history(recipe_id) == []


def test_database_rejects_incompatible_recipe_colors_at_persistence_boundary(database):
    add_typed_color(database, "12345", "Indigo", "Indanthren IN")
    add_typed_color(database, "54321", "Hot Reactive", "Reattivi Caldi")
    with pytest.raises(Exception, match="Cannot mix INDANTHREN"):
        database.add_recipe(
            Recipe(recipe_code="123456", name="Invalid mix", created_at="2026-01-01"),
            [{"code": "12345", "percentage": 1.0}, {"code": "54321", "percentage": 1.0}],
        )
    assert database.get_all_recipes() == []


def test_recipe_history_events_have_distinct_versions_and_snapshots(database):
    add_color(database, "12345", "Red A")
    add_color(database, "54321", "Blue B")
    recipe_id = database.add_recipe(
        Recipe(recipe_code="123456", name="History", created_at="2026-01-01"),
        [{"code": "12345", "percentage": 1.0}],
    )
    ok, message = database.update_recipe_contents(
        recipe_id,
        "123456",
        "History",
        [{"code": "54321", "percentage": 2.0}],
        [Chemical(code="ALK", name="Alkali", quantity=2.0, unit="g/l")],
        changed_by="operator",
        history_events=[
            {"operation": "delete_color", "details": {"old_color_code": "12345", "old_percentage": 1.0}},
            {"operation": "add_color", "details": {"new_color_code": "54321", "new_percentage": 2.0}},
        ],
    )
    assert ok, message
    history = database.get_recipe_history(recipe_id)
    assert [item["operation"] for item in history] == ["add_color", "delete_color"]
    assert history[0]["version_no"] != history[1]["version_no"]
    assert history[0]["old_data"]["colors"][0]["code"] == "12345"
    assert history[0]["new_data"]["operation_details"]["new_color_code"] == "54321"


def test_production_snapshot_is_unchanged_after_recipe_edit(database):
    add_color(database, "12345", "Red A")
    add_color(database, "54321", "Blue B")
    add_color(database, "67890", "Green C")
    recipe_id = database.add_recipe(
        Recipe(recipe_code="123456", name="Production recipe", created_at="2026-01-01"),
        [{"code": "12345", "percentage": 1.0}, {"code": "54321", "percentage": 2.0}, {"code": "67890", "percentage": 3.0}],
    )
    record_id = database.create_production_record(recipe_id, created_by="operator")
    before = database.get_production_record(record_id)
    ok, message = database.replace_recipe_color(recipe_id, "12345", "67890", changed_by="operator")
    assert not ok
    assert "already used" in message
    ok, message = database.update_recipe_contents(
        recipe_id,
        "123456",
        "Production recipe revised",
        [{"code": "54321", "percentage": 2.0}, {"code": "67890", "percentage": 4.0}],
        [Chemical(code="ALK", name="Alkali", quantity=4.0, unit="g/l")],
        changed_by="operator",
    )
    assert ok, message
    after = database.get_production_record(record_id)
    current = database.get_recipe_details(recipe_id)
    assert after["snapshot"] == before["snapshot"]
    assert {color["code"] for color in after["snapshot"]["colors"]} == {"12345", "54321", "67890"}
    assert {color["code"] for color in current["colors"]} == {"54321", "67890"}


def test_existing_database_gets_idempotent_schema_migrations(tmp_path):
    import sqlite3
    old_db = tmp_path / "old.db"
    with sqlite3.connect(old_db) as connection:
        connection.execute("CREATE TABLE recipes (id INTEGER PRIMARY KEY, recipe_code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, created_at TEXT)")
    DatabaseManager._schema_verified = False
    database = DatabaseManager(str(old_db))
    with database.get_connection() as connection:
        versions = [row[0] for row in connection.execute("SELECT version FROM schema_migrations ORDER BY version")]
        assert versions == [1, 2]
        assert connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'production_records'").fetchone()
    DatabaseManager._schema_verified = False
    reopened = DatabaseManager(str(old_db))
    with reopened.get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 2


def test_database_rejects_mixed_reactive_processes(database):
    add_typed_color(database, "12345", "Hot", "Reattivi Caldi")
    add_typed_color(database, "54321", "Cold", "Reattivi Freddi")
    with pytest.raises(Exception, match="CALDI"):
        database.add_recipe(
            Recipe(recipe_code="123456", name="Invalid process", created_at="2026-01-01"),
            [{"code": "12345", "percentage": 1.0}, {"code": "54321", "percentage": 1.0}],
        )


def test_update_quantity_preserves_recipe_id_and_records_old_and_new_values(database):
    add_color(database, "12345", "Red A")
    recipe_id = database.add_recipe(
        Recipe(recipe_code="123456", name="Quantity", created_at="2026-01-01"),
        [{"code": "12345", "percentage": 1.0}],
    )
    ok, message = database.update_recipe_color_percentage(recipe_id, "12345", 4.0, changed_by="operator")
    assert ok, message
    assert database.get_recipe_by_id(recipe_id).id == recipe_id
    assert database.get_recipe_details(recipe_id)["colors"][0]["percentage"] == pytest.approx(4.0)
    history = database.get_recipe_history(recipe_id)
    assert history[0]["operation"] == "update_quantity"
    assert history[0]["new_data"]["operation_details"] == {
        "color_code": "12345", "old_percentage": 1.0, "new_percentage": 4.0
    }


def test_failed_migration_rolls_back_schema_changes(tmp_path, monkeypatch):
    import sqlite3
    db_path = tmp_path / "migration-failure.db"
    original = DatabaseManager._create_indexes
    monkeypatch.setattr(DatabaseManager, "_create_indexes", lambda self, cursor: (_ for _ in ()).throw(RuntimeError("migration failed")))
    DatabaseManager._schema_verified = False
    with pytest.raises(Exception, match="migration failed"):
        DatabaseManager(str(db_path))
    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT 1 FROM sqlite_master WHERE name = 'schema_migrations'").fetchone() is None
    monkeypatch.setattr(DatabaseManager, "_create_indexes", original)
    DatabaseManager._schema_verified = False
    reopened = DatabaseManager(str(db_path))
    with reopened.get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0] == 2
