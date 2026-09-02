"""Cram: the impartial cousin of Domineering.

Both players may lay a domino in either orientation, so every value is a
nimber. Because the players' shapes coincide, transposition preserves value and
the memo table can exploit all eight symmetries of the square.

>>> from pycgt.notation import render
>>> render(rectangle(2, 2))
'0'
"""

from __future__ import annotations

from ..game import Game
from .grid import Position, Ruleset, value

__all__ = ["CRAM", "parse", "rectangle"]

_DOMINOES = (((0, 0), (1, 0)), ((0, 0), (0, 1)))

CRAM = Ruleset(
    name="Cram",
    left_shapes=_DOMINOES,
    right_shapes=_DOMINOES,
    transpose_invariant=True,
)


def rectangle(rows: int, cols: int) -> Game:
    return value(Position.rectangle(rows, cols), CRAM)


def parse(text: str) -> Game:
    return value(Position.parse(text), CRAM)
