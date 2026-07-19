# SPDX-License-Identifier: MIT
"""Deterministic, descriptive summaries; no live forecasting or alerting."""
from __future__ import annotations

from .contracts import AnnualDemand, MonthlyDemandRange


def demand_change(rows: list[AnnualDemand]) -> float:
    if len(rows) < 2:
        return 0.0
    return round(rows[-1].total_twh - rows[-2].total_twh, 2)


def widest_monthly_range(rows: list[MonthlyDemandRange]) -> MonthlyDemandRange:
    if not rows:
        raise ValueError("at least one monthly demand range is required")
    return max(rows, key=lambda row: row.peak_mw - row.minimum_mw)
# SPDX-License-Identifier: MIT
