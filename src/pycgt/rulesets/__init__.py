"""Concrete rulesets, and the shared grid machinery they are built on.

The rulesets exist to exercise the core: each one has published values or a
known closed form, so they double as the library's validation suite.
"""

from . import cram, domineering, nim
from .grid import Position, Ruleset, value

__all__ = ["Position", "Ruleset", "cram", "domineering", "nim", "value"]
