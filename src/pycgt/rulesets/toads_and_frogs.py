"""Toads-and-Frogs: a partizan game on a strip.

Left owns the toads (``t``) and moves them **rightward**; Right owns the frogs
(``f``) and moves them **leftward**. A piece may step into the next square if
it is empty, or **jump over exactly one opposing piece** into the square
beyond if that is empty. A piece never moves backwards, and never jumps a
piece of its own colour. A player with no move loses.

The library's third board shape, after grids of empty cells (Domineering,
Cram) and grids of coloured stones (Clobber): here the state is a
one-dimensional word, and unlike those two the pieces have a *direction*, so
neither reflection nor colour exchange alone is a symmetry -- reversing the
strip **and** swapping the colours is.

Values are not confined to infinitesimals: ``"t."`` is 1, since Left has a free
move and Right has none.

>>> from pycgt.notation import render
>>> render(parse("t."))
'1'
>>> render(parse("t.f"))
'*'
>>> render(parse("tf"))
'0'
"""

from __future__ import annotations

from functools import cache

from ..game import Game, canonical
from ..notation import render as _render

__all__ = ["EMPTY", "FROG", "TOAD", "left_moves", "parse", "right_moves", "value"]

TOAD = "t"
FROG = "f"
EMPTY = "."
_ALLOWED = frozenset({TOAD, FROG, EMPTY})


def _check(board: str) -> str:
    bad = set(board) - _ALLOWED
    if bad:
        raise ValueError(
            f"expected only {TOAD!r}, {FROG!r} and {EMPTY!r}, found {sorted(bad)}"
        )
    return board


@cache
def left_moves(board: str) -> tuple[str, ...]:
    """Positions after one toad move. Toads travel rightward."""
    out = []
    last = len(board) - 1
    for i, square in enumerate(board):
        if square != TOAD:
            continue
        if i < last and board[i + 1] == EMPTY:
            out.append(board[:i] + EMPTY + TOAD + board[i + 2 :])
        elif i + 1 < last and board[i + 1] == FROG and board[i + 2] == EMPTY:
            out.append(board[:i] + EMPTY + FROG + TOAD + board[i + 3 :])
    return tuple(out)


@cache
def right_moves(board: str) -> tuple[str, ...]:
    """Positions after one frog move. Frogs travel leftward."""
    out = []
    for i, square in enumerate(board):
        if square != FROG:
            continue
        if i >= 1 and board[i - 1] == EMPTY:
            out.append(board[: i - 1] + FROG + EMPTY + board[i + 1 :])
        elif i >= 2 and board[i - 1] == TOAD and board[i - 2] == EMPTY:
            out.append(board[: i - 2] + FROG + TOAD + EMPTY + board[i + 1 :])
    return tuple(out)


@cache
def value(board: str) -> Game:
    """The exact canonical value of a Toads-and-Frogs position.

    No component decomposition: a toad can travel across empty squares, so a
    gap does not separate the strip into independent halves the way it does in
    a placement game.
    """
    _check(board)
    left = frozenset(value(after) for after in left_moves(board))
    right = frozenset(value(after) for after in right_moves(board))
    return canonical(Game(left, right))


def parse(board: str) -> Game:
    """The value of a position written as a word over ``t``, ``f`` and ``.``."""
    return value(_check(board))


def reverse_and_swap(board: str) -> str:
    """The symmetry of this game: reverse the strip and exchange the colours.

    Reversing alone is not a symmetry, because pieces have a direction. Doing
    both negates the value.

    >>> reverse_and_swap("tt.f")
    't.ff'
    """
    swapped = {TOAD: FROG, FROG: TOAD, EMPTY: EMPTY}
    return "".join(swapped[square] for square in reversed(_check(board)))


def table(length: int) -> dict[str, str]:
    """Every position of the given length, with its value rendered.

    Handy for spotting patterns; the values are exact.
    """
    import itertools

    return {
        "".join(combo): _render(value("".join(combo)))
        for combo in itertools.product(TOAD + FROG + EMPTY, repeat=length)
    }
