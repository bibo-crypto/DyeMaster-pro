from types import SimpleNamespace

import pytest

pytest.importorskip("tkinter")

from app.models import Color, Recipe
from ui import recipe_creator_window as recipe_editor_module
from ui.recipe_creator_window import RecipeCreatorWindow


class FakeTree:
    def __init__(self, selection_values):
        self.values = selection_values

    def selection(self):
        return ["selected"] if self.values is not None else []

    def item(self, _item, _option=None):
        return {"values": self.values}


class FakeVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class FakeWindow:
    def __init__(self):
        self.destroyed = False

    def destroy(self):
        self.destroyed = True


class FakeParent:
    def __init__(self):
        self.loaded = False

    def load_data(self):
        self.loaded = True


def test_replace_color_controller_preserves_percentage_and_marks_history(monkeypatch):
    editor = RecipeCreatorWindow.__new__(RecipeCreatorWindow)
    editor.window = object()
    editor.selected_tree = FakeTree(("12345", "Red A", "Indanthren IN", "2.50", "€0.25"))
    editor.indanthren_tree = FakeTree(("54321", "Blue B", "Indanthren IN", "Supplier", "10.00", "100", ""))
    editor.reattivi_tree = FakeTree(None)
    editor.selected_colors = [{
        "code": "12345", "name": "Red A", "dye_type": "Indanthren IN",
        "percentage": 2.5, "price_kg": 10.0,
    }]
    editor._pending_history_operation = None
    editor._pending_history_details = None
    editor._find_color_resa_percent = lambda _code: 100.0
    editor._refresh_recipe_calculations = lambda: None

    editor.replace_selected_color()

    assert editor.selected_colors[0]["code"] == "54321"
    assert editor.selected_colors[0]["percentage"] == pytest.approx(2.5)
    assert editor._pending_history_operation == "replace_color"
    assert editor._pending_history_details == {"old_color_code": "12345", "new_color_code": "54321"}


def test_save_and_export_edit_saves_same_recipe_before_pdf_failure(database, monkeypatch):
    database.add_color(Color(
        code="12345", name="Red A", dye_type="Indanthren IN", supplier="Test",
        price_kg=10.0, resa_percent=100.0, created_at="2026-01-01", updated_at="2026-01-01",
    ))
    recipe_id = database.add_recipe(
        Recipe(recipe_code="123456", name="Original", created_at="2026-01-01"),
        [{"code": "12345", "percentage": 1.0}],
    )
    details = database.get_recipe_details(recipe_id)
    editor = RecipeCreatorWindow.__new__(RecipeCreatorWindow)
    editor.parent = FakeParent()
    editor.window = FakeWindow()
    editor.db = database
    editor.editing_recipe_id = recipe_id
    editor.editing_recipe_created_at = details["recipe"].created_at
    editor.recipe_code_var = FakeVar("123456")
    editor.recipe_name_var = FakeVar("Edited before export")
    editor.selected_colors = [dict(details["colors"][0])]
    editor.session = SimpleNamespace(
        has_permission=lambda _permission: True,
        current_user=SimpleNamespace(username="operator"),
    )
    editor.validate_inputs = lambda: True
    editor._get_lab_params = lambda: {}
    editor.on_saved = None
    editor._pending_history_operation = None
    editor._pending_history_details = None
    errors = []
    monkeypatch.setattr(recipe_editor_module.messagebox, "showerror", lambda *_args, **_kwargs: errors.append(True))

    from app.pdf_exporter import PDFExporter
    monkeypatch.setattr(PDFExporter, "export_recipe_to_pdf", staticmethod(lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("PDF failed"))))

    editor.save_and_export()

    assert errors
    assert not editor.window.destroyed
    saved = database.get_recipe_by_id(recipe_id)
    assert saved.id == recipe_id
    assert saved.name == "Edited before export"
    assert len(database.get_all_recipes()) == 1
    assert database.get_recipe_history(recipe_id)[0]["operation"] == "edit_recipe"
