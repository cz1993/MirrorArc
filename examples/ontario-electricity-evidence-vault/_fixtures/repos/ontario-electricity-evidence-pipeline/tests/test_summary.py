# SPDX-License-Identifier: MIT
import unittest

from grid_evidence.contracts import AnnualDemand, MonthlyDemandRange
from grid_evidence.summary import demand_change, widest_monthly_range


class SummaryTests(unittest.TestCase):
    def test_demand_change(self) -> None:
        rows = [AnnualDemand(2022, 137.6, 3.8), AnnualDemand(2023, 137.1, -0.5)]
        self.assertEqual(demand_change(rows), -0.5)

    def test_widest_monthly_range(self) -> None:
        rows = [
            MonthlyDemandRange(2023, "January", 20486, 12603),
            MonthlyDemandRange(2023, "September", 23713, 11402),
        ]
        self.assertEqual(widest_monthly_range(rows).month, "September")


if __name__ == "__main__":
    unittest.main()
# SPDX-License-Identifier: MIT
