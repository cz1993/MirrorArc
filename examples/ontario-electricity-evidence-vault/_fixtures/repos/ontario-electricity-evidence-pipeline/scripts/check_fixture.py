#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Run the two deterministic quality gates against local paths supplied by an operator."""
from pathlib import Path
import sys

from grid_evidence.load import load_annual_demand, load_monthly_ranges
from grid_evidence.quality import annual_demand_complete, peak_exceeds_minimum


def main(args: list[str]) -> int:
    if len(args) != 2:
        print("usage: check_fixture.py ANNUAL_DEMAND.csv MONTHLY_RANGES.csv")
        return 2
    annual_ok = annual_demand_complete(load_annual_demand(Path(args[0])))
    monthly_ok = peak_exceeds_minimum(load_monthly_ranges(Path(args[1])))
    print(f"annual_demand_complete={str(annual_ok).lower()}")
    print(f"peak_exceeds_minimum={str(monthly_ok).lower()}")
    return 0 if annual_ok and monthly_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
