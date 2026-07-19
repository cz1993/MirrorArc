# SPDX-License-Identifier: MIT
import unittest

from grid_evidence.contracts import AnnualDemand, MonthlyDemandRange
from grid_evidence.quality import annual_demand_complete, peak_exceeds_minimum, publication_allowed


class QualityTests(unittest.TestCase):
    def test_happy_path(self) -> None:
        self.assertTrue(annual_demand_complete([AnnualDemand(2023, 137.1, -0.5)]))
        self.assertTrue(peak_exceeds_minimum([MonthlyDemandRange(2023, "July", 22686, 11987)]))

    def test_publication_gate_fails_closed(self) -> None:
        self.assertTrue(publication_allowed(4.9))
        self.assertFalse(publication_allowed(7.7))


if __name__ == "__main__":
    unittest.main()
# SPDX-License-Identifier: MIT
