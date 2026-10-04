# SPDX-License-Identifier: AGPL-3.0-or-later
"""Governed metadata, dynamic, and frozen context assembly."""

from mirrorarc.context_assembly.builder import (
    ContextAssemblyError,
    build_context,
    freeze_context,
    resolve_dynamic_context,
)

__all__ = [
    "ContextAssemblyError",
    "build_context",
    "freeze_context",
    "resolve_dynamic_context",
]
