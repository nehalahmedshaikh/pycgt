"""Concrete rulesets, and the shared grid machinery they are built on.

The rulesets exist to exercise the core: each one has published values or a
known closed form, so they double as the library's validation suite.
"""

from . import clobber, cram, domineering, nim
from .grid import Position, Ruleset, value
from .reachable import Move, Replay, reachable_from_rectangle, verify_replay

__all__ = [
    "Move",
    "Position",
    "Replay",
    "Ruleset",
    "clobber",
    "cram",
    "domineering",
    "nim",
    "reachable_from_rectangle",
    "value",
    "verify_replay",
]
