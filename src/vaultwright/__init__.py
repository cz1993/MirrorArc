# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compatibility namespace for the pre-release Vaultwright package name.

NoeticWeave is the canonical package. This namespace keeps existing technical-alpha
vault-local shims importable during the rename transition without duplicating runtime code.
"""
from __future__ import annotations

from noeticweave import __path__ as _canonical_path
from noeticweave import __version__

__path__ = _canonical_path

__all__ = ["__version__"]
