# SPDX-License-Identifier: MIT
"""Small explicit data contracts used by the demonstration pipeline."""
from dataclasses import dataclass


@dataclass(frozen=True)
class AnnualDemand:
    year: int
    total_twh: float
    change_twh: float


@dataclass(frozen=True)
class MonthlyDemandRange:
    year: int
    month: str
    peak_mw: int
    minimum_mw: int
# SPDX-License-Identifier: MIT
