# SPDX-License-Identifier: MIT
"""Dependency-free CSV loaders for the OGL demonstration fixtures."""
from __future__ import annotations

import csv
from pathlib import Path

from .contracts import AnnualDemand, MonthlyDemandRange


def numeric(value: str) -> float:
    return float(value.replace(",", "").replace("%", "").strip())


def load_annual_demand(path: Path) -> list[AnnualDemand]:
    rows: list[AnnualDemand] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if not row.get("Year"):
                continue
            rows.append(AnnualDemand(int(row["Year"]), numeric(row["Total TWh"]), numeric(row["Change over Previous Year"])))
    return rows


def load_monthly_ranges(path: Path) -> list[MonthlyDemandRange]:
    rows: list[MonthlyDemandRange] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if not row.get("Year"):
                continue
            rows.append(MonthlyDemandRange(int(row["Year"]), row["Month"], int(numeric(row["Peak MW"])), int(numeric(row["Minimum MW"]))))
    return rows
# SPDX-License-Identifier: MIT
