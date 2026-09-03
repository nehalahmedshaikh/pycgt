"""Shared test data.

Positions large enough to be worth defining once, with their sources.
"""

from __future__ import annotations

import pytest

from pycgt.rulesets import Position

#: Connected 26-cell core of the position in Mazur (2026), "A Domineering
#: temperature counterexample". Published coordinates are Cartesian (x, y);
#: pycgt uses (row, col), hence the swap.
_CORE_CARTESIAN = [
    (0, 0),
    (0, 1),
    (0, 2),
    (1, 2),
    (1, 5),
    (1, 7),
    (2, 2),
    (2, 5),
    (2, 6),
    (2, 7),
    (3, 2),
    (3, 3),
    (3, 4),
    (3, 5),
    (3, 6),
    (4, 4),
    (4, 5),
    (4, 6),
    (5, 2),
    (5, 3),
    (5, 4),
    (6, 2),
    (7, 2),
    (8, 0),
    (8, 1),
    (8, 2),
]


@pytest.fixture(scope="session")
def high_temperature_core() -> Position:
    """The 26-cell connected core. Value ``{17/8|-2*}``."""
    return Position(frozenset((y, x + 2) for x, y in _CORE_CARTESIAN))


@pytest.fixture(scope="session")
def high_temperature_position() -> Position:
    """The 28-cell position: the core plus two isolated cells.

    A lone cell affords no move, so each contributes 0 and the value is
    unchanged. Sits inside an 11x8 rectangle.
    """
    return Position(
        frozenset([(y, x + 2) for x, y in _CORE_CARTESIAN] + [(1, 0), (4, 1)])
    )
