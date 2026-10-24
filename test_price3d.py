import contextlib
import io
from unittest.mock import patch
import pytest

import Price3D


@pytest.fixture(autouse=True)
def reset_settings():
    """Automatically backs up and restores Price3D settings before and after each test."""
    original_settings = Price3D.settings.copy()
    yield
    Price3D.settings.clear()
    Price3D.settings.update(original_settings)


def test_calculate_costs_includes_failure_reserve_and_batch_design():
    # Set failure reserve percentage in global settings
    Price3D.settings["failPct"] = 5.0
    
    # Sample print job parameters
    job = {
        "grams": 100.0,
        "hours": 2.0,
        "qty": 3,
        "workMin": 30.0,
        "laborRate": 8.0,
        "consumables": 0.5,
        "design": 12.0,
        "packaging": 1.0,
        "shipping": 0.25,
        "feePct": 10.0,
        "vatPct": 0.0,
    }

    costs = Price3D.calculate_costs(job)

    # Verify material, labor, design, and final unit costs match expected calculations
    assert costs["material"] == pytest.approx(2.2)
    assert costs["labor"] == pytest.approx(4.0)
    assert costs["design"] == pytest.approx(4.0)
    assert costs["unitCost"] == pytest.approx(12.616315789473684)
    assert costs["breakEven"] == pytest.approx(costs["unitCost"] / 0.9)


def test_recommended_tier_respects_hourly_profit_target():
    # Set profit margins and target hourly rates
    Price3D.settings["profitMoney"] = 1.0
    Price3D.settings["targetHourly"] = 3.0
    job = {"hours": 2.0, "feePct": 0.0, "vatPct": 0.0}
    costs = {"unitCost": 5.0}

    tiers = Price3D.build_tiers(costs, job)

    # Ensure the pricing tier meets minimum hourly profit constraints
    assert tiers[1]["profit"] >= 6.0
    assert tiers[1]["perHour"] >= 3.0


def test_changing_currency_does_not_compound_conversion():
    # Mock user input and FX rates to test currency switching
    with (
        patch.object(Price3D, "prompt_int", side_effect=[1, 2]),
        patch.object(Price3D, "get_fx", side_effect=[2.0, 3.0]),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        Price3D.choose_currency()
        Price3D.choose_currency()

    # Ensure exchange rate conversions are recalculated directly, not compounded
    assert Price3D.settings["fx"] == pytest.approx(3.0)
    assert Price3D.settings["materialPrice"] == pytest.approx(60.0)
    assert Price3D.settings["kwhPrice"] == pytest.approx(0.6)


def test_prompt_float_rejects_non_finite_values():
    # Mock invalid user input ('nan') followed by a valid input ('5')
    with (
        patch.object(Price3D, "read_line", side_effect=["nan", "5"]),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        value = Price3D.prompt_float("Value", 1.0, 0.0, 5.0)

    # Verify that 'nan' was rejected and valid input was accepted
    assert value == 5.0
