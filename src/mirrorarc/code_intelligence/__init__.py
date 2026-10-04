# SPDX-License-Identifier: AGPL-3.0-or-later
"""Optional, revision-bound repository intelligence."""

from mirrorarc.code_intelligence.service import (
    CodeIntelligenceError,
    analyze_repository,
    catalog_report,
    doctor_report,
    status_report,
)

__all__ = [
    "CodeIntelligenceError",
    "analyze_repository",
    "catalog_report",
    "doctor_report",
    "status_report",
]
