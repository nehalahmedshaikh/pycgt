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

from .game import Game, add, canonical, negate
from .values import as_number

__all__ = [
    "confusion_interval",
    "is_hot",
    "is_infinitesimal",
    "is_number_tiny",
    "is_numberish",
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


def is_numberish(g: Game) -> bool:
    """True if ``g`` is infinitesimally close to some number.

    Equivalently, both stops agree. Every number and every infinitesimal
    qualifies; a hot game does not.

    >>> from pycgt.game import add
    >>> from pycgt.values import STAR, UP, integer, plus_minus
    >>> is_numberish(add(integer(1), UP)), is_numberish(STAR)
    (True, True)
    >>> is_numberish(plus_minus(1))
    False
    """
    return number_part(g) is not None


def is_number_tiny(g: Game) -> bool:
    """True if ``g`` is a number plus a tiny or miny value.

    A *tiny* value has the form ``tiny-y`` = ``{0 || 0 | -y}``, and a *miny* is
    its negative. Numbers themselves count, with a zero tiny part.

    The argument ``y`` must have a positive Left stop, which rules out
    ``tiny-0`` -- that is just ``^`` -- and ``tiny-*``. The boundary is
    calibrated against CGSuite rather than taken from its wording: the
    documented condition asks that the inner option be at most some negative
    number, which would exclude ``tiny-(+-1)``, yet CGSuite reports that one as
    number-tiny. A positive Left stop agrees with CGSuite on every case tested,
    switches included.

    >>> from pycgt.game import add
    >>> from pycgt.values import STAR, UP, integer, miny, plus_minus, tiny
    >>> is_number_tiny(tiny(2)), is_number_tiny(add(integer(1), miny(2)))
    (True, True)
    >>> is_number_tiny(integer(1)), is_number_tiny(add(integer(1), STAR))
    (True, False)
    >>> is_number_tiny(add(tiny(2), tiny(2)))
    False
    >>> is_number_tiny(UP), is_number_tiny(tiny(STAR))
    (False, False)
    >>> is_number_tiny(tiny(plus_minus(1)))
    True
    """
    from .values import as_miny, as_tiny, number

    c = canonical(g)
    if as_number(c) is not None:
        return True
    part = number_part(c)
    if part is None:
        return False
    rest = canonical(add(c, negate(number(part))))
    argument = as_tiny(rest)
    if argument is None:
        argument = as_miny(rest)
    return argument is not None and left_stop(argument) > 0
