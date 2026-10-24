import contextlib
import io
import unittest
from unittest.mock import patch

import Price3D


class CalculatorTests(unittest.TestCase):
    def setUp(self):
        self.original_settings = Price3D.settings.copy()

    def tearDown(self):
        Price3D.settings.clear()
        Price3D.settings.update(self.original_settings)

    def test_calculate_costs_includes_failure_reserve_and_batch_design(self):
        Price3D.settings["failPct"] = 5.0
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

        self.assertAlmostEqual(costs["material"], 2.2)
        self.assertAlmostEqual(costs["labor"], 4.0)
        self.assertAlmostEqual(costs["design"], 4.0)
        self.assertAlmostEqual(costs["unitCost"], 12.616315789473684)
        self.assertAlmostEqual(costs["breakEven"], costs["unitCost"] / 0.9)

    def test_recommended_tier_respects_hourly_profit_target(self):
        Price3D.settings["profitMoney"] = 1.0
        Price3D.settings["targetHourly"] = 3.0
        job = {"hours": 2.0, "feePct": 0.0, "vatPct": 0.0}
        costs = {"unitCost": 5.0}

        tiers = Price3D.build_tiers(costs, job)

        self.assertGreaterEqual(tiers[1]["profit"], 6.0)
        self.assertGreaterEqual(tiers[1]["perHour"], 3.0)

    def test_changing_currency_does_not_compound_conversion(self):
        with (
            patch.object(Price3D, "prompt_int", side_effect=[1, 2]),
            patch.object(Price3D, "get_fx", side_effect=[2.0, 3.0]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            Price3D.choose_currency()
            Price3D.choose_currency()

        self.assertAlmostEqual(Price3D.settings["fx"], 3.0)
        self.assertAlmostEqual(Price3D.settings["materialPrice"], 60.0)
        self.assertAlmostEqual(Price3D.settings["kwhPrice"], 0.6)

    def test_prompt_float_rejects_non_finite_values(self):
        with (
            patch.object(Price3D, "read_line", side_effect=["nan", "5"]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            value = Price3D.prompt_float("Value", 1.0, 0.0, 5.0)

        self.assertEqual(value, 5.0)


if __name__ == "__main__":
    unittest.main()
