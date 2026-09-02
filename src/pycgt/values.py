"""Numbers and the standard named values.

Two families live here.

**Numbers.** The dyadic rationals sit inside the games, and :func:`number` and
:func:`as_number` move between the two representations. A game is a *number*
exactly when every Left option is strictly below every Right option, and its
value is then the simplest number in between -- Conway's simplicity rule.

**Named values.** ``*``, ``^``, ``v``, the nimbers, the switches, and the tiny
and miny families. These are the vocabulary that makes real game values
readable: the value of a 2x4 Domineering board is not an inscrutable four-deep
tree, it is ``miny-2``.
"""

from __future__ import annotations

import math
from fractions import Fraction
from functools import cache

from .game import ZERO, Game, canonical, game, multiple, negate

__all__ = [
    "DOWN",
    "STAR",
    "UP",
    "as_number",
    "integer",
    "is_number",
    "miny",
    "nimber",
    "number",
    "plus_minus",
    "simplest_between",
    "switch",
    "tiny",
    "up_multiple",
]


# ---------------------------------------------------------------------------
# Numbers
# ---------------------------------------------------------------------------


def simplest_between(lo: Fraction | None, hi: Fraction | None) -> Fraction:
    """The simplest dyadic rational strictly between ``lo`` and ``hi``.

    ``None`` means unbounded on that side. "Simplest" is Conway's sense: zero
    first, then integers of small magnitude, then halves, then quarters, and so
    on -- the number with the earliest birthday.
    """
    if (lo is None or lo < 0) and (hi is None or hi > 0):
        return Fraction(0)

    if lo is not None and lo >= 0:
        candidate = math.floor(lo) + 1
        if hi is None or candidate < hi:
            return Fraction(candidate)
    if hi is not None and hi <= 0:
        candidate = math.ceil(hi) - 1
        if lo is None or candidate > lo:
            return Fraction(candidate)

    # Both bounds are finite, on the same side of zero, with no integer
    # between them: descend through the dyadic rationals by denominator.
    assert lo is not None and hi is not None
    for k in range(1, 64):
        denominator = 2**k
        lowest = math.floor(lo * denominator) + 1
        highest = math.ceil(hi * denominator) - 1
        found = [
            Fraction(m, denominator)
            for m in range(lowest, highest + 1)
            if lo < Fraction(m, denominator) < hi
        ]
        if found:
            return min(found, key=lambda x: (abs(x), x))
    raise ValueError(f"no dyadic rational found between {lo} and {hi}")


@cache
def as_number(g: Game) -> Fraction | None:
    """``g`` as a dyadic rational, or ``None`` if ``g`` is not a number."""
    lows: list[Fraction] = []
    for l in g.left:
        value = as_number(l)
        if value is None:
            return None
        lows.append(value)
    highs: list[Fraction] = []
    for r in g.right:
        value = as_number(r)
        if value is None:
            return None
        highs.append(value)

    lo = max(lows) if lows else None
    hi = min(highs) if highs else None
    if lo is not None and hi is not None and lo >= hi:
        return None  # a switch, not a number
    return simplest_between(lo, hi)


def is_number(g: Game) -> bool:
    """True if ``g`` is a dyadic rational."""
    return as_number(g) is not None


@cache
def number(value: Fraction | int | str) -> Game:
    """The canonical game whose value is the dyadic rational ``value``.

    Inverse of :func:`as_number`. Integers are towers, ``{n-1 | }``; a dyadic
    ``a/2**k`` in lowest terms is ``{value - 1/2**k | value + 1/2**k}``.

    >>> as_number(number("3/4")) == Fraction(3, 4)
    True
    """
    value = Fraction(value)
    if value.denominator == 1:
        n = value.numerator
        if n == 0:
            return ZERO
        if n > 0:
            return Game(frozenset({number(n - 1)}), frozenset())
        return Game(frozenset(), frozenset({number(n + 1)}))

    if value.denominator & (value.denominator - 1):
        raise ValueError(f"not a dyadic rational: {value}")
    step = Fraction(1, value.denominator)
    return Game(frozenset({number(value - step)}), frozenset({number(value + step)}))


def integer(n: int) -> Game:
    """The game equal to the integer ``n``."""
    return number(Fraction(n))


# ---------------------------------------------------------------------------
# Named values
# ---------------------------------------------------------------------------

#: ``*`` = ``{0 | 0}``. The simplest game confused with zero.
STAR = Game(frozenset({ZERO}), frozenset({ZERO}))

#: ``^`` = ``{0 | *}``. Positive, but below every positive number.
UP = Game(frozenset({ZERO}), frozenset({STAR}))

#: ``v`` = ``{* | 0}``, the negative of :data:`UP`.
DOWN = Game(frozenset({STAR}), frozenset({ZERO}))


@cache
def nimber(n: int) -> Game:
    """``*n``, the value of a Nim heap of size ``n``.

    Nimbers add by exclusive-or, which :func:`~pycgt.game.add` reproduces.
    """
    if n < 0:
        raise ValueError("a nim heap cannot have negative size")
    options = frozenset(nimber(i) for i in range(n))
    return canonical(Game(options, options))


def up_multiple(n: int) -> Game:
    """``n`` copies of ``^`` summed (negative ``n`` gives multiples of ``v``)."""
    return multiple(UP, n)


def switch(left: Fraction | int | str, right: Fraction | int | str) -> Game:
    """The switch ``{left | right}`` between two numbers.

    Hot when ``left > right``; a number otherwise.
    """
    return game({number(left)}, {number(right)})


def plus_minus(value: Fraction | int | str) -> Game:
    """``+-value`` = ``{value | -value}``.

    A switch is its own negative, so ``plus_minus(x) + plus_minus(x) == 0``.
    """
    magnitude = Fraction(value)
    return switch(magnitude, -magnitude)


def tiny(g: Game | Fraction | int | str) -> Game:
    """``tiny-g`` = ``{0 || 0 | -g}``: a positive infinitesimal.

    For ``g >= 0`` this is positive but smaller than every positive number, and
    smaller still for larger ``g``. Domineering values are full of these.
    """
    if not isinstance(g, Game):
        g = number(g)
    return game({ZERO}, {game({ZERO}, {negate(g)})})


def miny(g: Game | Fraction | int | str) -> Game:
    """``miny-g`` = ``-tiny-g``: a negative infinitesimal."""
    return negate(tiny(g))
