# SPDX-License-Identifier: MIT
"""Quality gates whose results can be linked into curated evidence notes."""
from __future__ import annotations

from .contracts import AnnualDemand, MonthlyDemandRange


def annual_demand_complete(rows: list[AnnualDemand]) -> bool:
    return bool(rows) and all(row.total_twh > 0 for row in rows)


def peak_exceeds_minimum(rows: list[MonthlyDemandRange]) -> bool:
    return bool(rows) and all(row.peak_mw > row.minimum_mw > 0 for row in rows)


def publication_allowed(mape_percent: float, threshold: float = 5.0) -> bool:
    return 0 <= mape_percent <= threshold
# SPDX-License-Identifier: MIT
