"""Domineering: Left lays vertical dominoes, Right horizontal ones.

Whoever cannot move loses. The convention here matches CGSuite's
``game.grid.Domineering``: Left's direction is ``(1,0)`` and Right's is
``(0,1)``.

>>> from pycgt.notation import render
>>> render(rectangle(2, 4))
'Miny(2)'
>>> render(rectangle(2, 2))
'+-1'
"""

from __future__ import annotations

from ..game import Game
from .grid import Position, Ruleset, value

__all__ = ["DOMINEERING", "parse", "rectangle", "square"]

#: Left plays vertically, Right horizontally. Transposing exchanges the
#: players, so it is *not* value-preserving.
DOMINEERING = Ruleset(
    name="Domineering",
    left_shapes=(((0, 0), (1, 0)),),
    right_shapes=(((0, 0), (0, 1)),),
    transpose_invariant=False,
)


def rectangle(rows: int, cols: int) -> Game:
    """The value of an empty ``rows`` by ``cols`` board."""
    return value(Position.rectangle(rows, cols), DOMINEERING)


def square(side: int) -> Game:
    return rectangle(side, side)


def parse(text: str) -> Game:
    """The value of an ASCII position, where ``.`` marks an empty cell."""
    return value(Position.parse(text), DOMINEERING)
