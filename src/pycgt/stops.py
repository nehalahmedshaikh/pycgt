"""Stops, and the predicates built on them.

The *Left stop* of ``G`` is the number play settles on when Left moves first
and both players stop as soon as the position becomes a number. Stops matter
because they turn questions about *every* number -- "is this smaller than every
positive number?" -- into finite computations.

That is what makes infinitesimality decidable, and therefore what makes
:mod:`pycgt.reduced` and :mod:`pycgt.thermal` possible.
"""

from __future__ import annotations

import math
from fractions import Fraction
from functools import cache

from .game import Game
from .values import as_number

__all__ = [
    "confusion_interval",
    "is_hot",
    "is_infinitesimal",
    "is_tepid",
    "left_stop",
    "number_part",
    "right_stop",
    "stops",
]

#: Returned when a player has no move at all in a non-number. Only reachable
#: for non-canonical input: a canonical non-number offers both players a move.
NO_MOVE_LEFT = -math.inf
NO_MOVE_RIGHT = math.inf

Stop = Fraction | float


@cache
def left_stop(g: Game) -> Stop:
    """Where play stops with Left moving first."""
    value = as_number(g)
    if value is not None:
        return value
    if not g.left:
        return NO_MOVE_LEFT
    return max(right_stop(l) for l in g.left)


@cache
def right_stop(g: Game) -> Stop:
    """Where play stops with Right moving first."""
    value = as_number(g)
    if value is not None:
        return value
    if not g.right:
        return NO_MOVE_RIGHT
    return min(left_stop(r) for r in g.right)


def stops(g: Game) -> tuple[Stop, Stop]:
    """``(left_stop, right_stop)``."""
    return left_stop(g), right_stop(g)


def confusion_interval(g: Game) -> tuple[Stop, Stop]:
    """The interval of numbers ``g`` is confused with, as ``(low, high)``.

    ``g`` is confused with exactly those numbers strictly inside it.
    """
    return right_stop(g), left_stop(g)


def is_infinitesimal(g: Game) -> bool:
    """True if ``-x < g < x`` for every positive number ``x``.

    Equivalently both stops are zero, which is the finite test.

    >>> from pycgt.values import STAR, UP
    >>> is_infinitesimal(STAR) and is_infinitesimal(UP)
    True
    """
    return left_stop(g) == 0 and right_stop(g) == 0


def number_part(g: Game) -> Fraction | None:
    """The number ``g`` is infinitesimally close to, if there is one.

    ``g`` is infinitesimally close to ``x`` exactly when both stops equal
    ``x``. This is the formal content of Berlekamp's phrase "known to within
    ish": a value known up to an infinitesimal is a value whose stops are
    known.
    """
    low, high = left_stop(g), right_stop(g)
    if low == high and isinstance(low, Fraction):
        return low
    return None


def is_hot(g: Game) -> bool:
    """Left stop strictly above Right stop: there is something to fight over."""
    return left_stop(g) > right_stop(g)


def is_tepid(g: Game) -> bool:
    """Stops equal but not a number: infinitesimally shifted from a number."""
    return number_part(g) is not None and as_number(g) is None
