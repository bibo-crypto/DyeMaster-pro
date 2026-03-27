"""UI package exports with lazy imports.

Avoid eager importing all window modules at package import time so a single
broken module does not block the rest of the child windows.
"""

from importlib import import_module

__all__ = [
    "ColorsInUseWindow",
    "RecipeCreatorWindow",
    "SavedRecipesWindow",
]


_LAZY_EXPORTS = {
    "ColorsInUseWindow": "ui.colors_in_use_window",
    "RecipeCreatorWindow": "ui.recipe_creator_window",
    "SavedRecipesWindow": "ui.saved_recipes_window",
}


def __getattr__(name):
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module 'ui' has no attribute '{name}'")
    module = import_module(module_name)
    return getattr(module, name)
