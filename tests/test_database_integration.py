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
