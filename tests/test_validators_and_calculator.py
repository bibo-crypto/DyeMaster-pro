import pytest

from app.calculator import ChemicalCalculator, CostCalculator
from app.validators import Validators


def test_recipe_code_validation_rejects_invalid_values():
    assert Validators.validate_recipe_code("123456")[0]
    assert not Validators.validate_recipe_code("12345")[0]
    assert not Validators.validate_recipe_code("12A456")[0]


def test_percentage_validation_rejects_negative_and_zero_by_default():
    assert Validators.validate_percentage("2.5")[2] == pytest.approx(2.5)
    assert not Validators.validate_percentage("0")[0]
    assert not Validators.validate_percentage("-1")[0]
    assert Validators.validate_percentage("0", allow_zero=True)[0]


def test_recipe_validation_requires_colors_when_supplied():
    valid, _, _ = Validators.validate_recipe_object(
        {"name": "Recipe", "recipe_code": "123456", "colors": [{"color_code": "12345", "percentage": 2.0}]}
    )
    assert valid
    invalid, message, _ = Validators.validate_recipe_object(
        {"name": "Recipe", "recipe_code": "123456", "colors": []}
    )
    assert not invalid
    assert "at least one color" in message


def test_chemical_calculator_uses_existing_domain_rules():
    chemicals = ChemicalCalculator.calculate_chemicals(2.5, "Indanthren IW")
    assert [chemical.code for chemical in chemicals] == ["31310", "31180-IW", "31360-IW"]
    assert [chemical.quantity for chemical in chemicals] == [13.0, 6.0, 15.0]


def test_cost_calculation_is_deterministic():
    colors = [{"percentage": 2.0, "price_kg": 10.0}, {"percentage": 3.0, "price_kg": 20.0}]
    assert CostCalculator.calculate_recipe_cost(colors) == pytest.approx(0.8)
    assert CostCalculator.calculate_batch_cost(0.8, 50) == pytest.approx(40.0)
    assert CostCalculator.calculate_with_waste(100.0, 10) == pytest.approx(110.0)
