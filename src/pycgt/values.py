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

from .game import ZERO, Game, add, canonical, game, multiple, negate

__all__ = [
    "DOWN",
    "STAR",
    "UP",
    "as_miny",
    "as_nimber",
    "as_number",
    "as_up_multiple",
    "as_tiny",
    "integer",
    "is_integer",
    "is_nimber",
    "is_number",
    "miny",
    "nimber",
    "norton_product",
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


def is_integer(g: Game) -> bool:
    """True if ``g`` is a whole number.

    >>> from pycgt.game import ZERO
    >>> is_integer(number(2)), is_integer(number("1/2")), is_integer(ZERO)
    (True, False, True)
    """
    value = as_number(g)
    return value is not None and value.denominator == 1


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


@cache
def as_nimber(g: Game) -> int | None:
    """If ``g`` is the nimber ``*n``, return ``n``; else None.

    Detected structurally and without a bound: a canonical nimber has the same
    options on both sides, and they are exactly the smaller nimbers.

    >>> as_nimber(nimber(7)), as_nimber(UP)
    (7, None)
    """
    if not g.left and not g.right:
        return 0
    if g.left != g.right:
        return None
    seen = set()
    for option in g.left:
        value = as_nimber(option)
        if value is None:
            return None
        seen.add(value)
    return len(seen) if seen == set(range(len(g.left))) else None


def is_nimber(g: Game) -> bool:
    """True if ``g`` is a nimber, zero included.

    >>> is_nimber(nimber(3)), is_nimber(STAR), is_nimber(UP)
    (True, True, False)
    """
    return as_nimber(canonical(g)) is not None


def up_multiple(n: int) -> Game:
    """``n`` copies of ``^`` summed (negative ``n`` gives multiples of ``v``)."""
    return multiple(UP, n)


@cache
def as_up_multiple(g: Game) -> tuple[int, bool] | None:
    """If ``g`` is ``n`` ups, optionally plus ``*``, return ``(n, has_star)``.

    Negative ``n`` means downs. Returns ``(0, True)`` for ``*`` itself and
    ``(0, False)`` for zero.

    Recognised structurally, from the fact that ``n`` ups has canonical form
    ``{0 | (n-1) ups + *}``, so there is no bound on ``n``. The result is then
    confirmed by one equality, which makes a false positive impossible.

    >>> as_up_multiple(up_multiple(5))
    (5, False)
    >>> as_up_multiple(canonical(add(up_multiple(3), STAR)))
    (3, True)
    >>> as_up_multiple(up_multiple(-2))
    (-2, False)
    >>> as_up_multiple(nimber(2)) is None
    True
    """
    found = _as_ups(canonical(g))
    if found is not None:
        return found
    found = _as_ups(canonical(negate(g)))
    if found is None:
        return None
    count, star = found
    return (-count, star)


@cache
def _as_ups(g: Game) -> tuple[int, bool] | None:
    """The non-negative half of :func:`as_up_multiple`."""
    if not g.left and not g.right:
        return (0, False)
    if g == STAR:
        return (0, True)
    # `^*` is the one shape that does not fit the spine below.
    if g.left == frozenset({ZERO, STAR}) and g.right == frozenset({ZERO}):
        return (1, True)
    if g.left != frozenset({ZERO}) or len(g.right) != 1:
        return None
    below = _as_ups(next(iter(g.right)))
    if below is None:
        return None
    count, star = below
    if star:
        result = (count + 1, False)
    elif count >= 1:
        result = (count + 1, True)
    else:
        return None
    expected = (
        add(up_multiple(result[0]), STAR) if result[1] else up_multiple(result[0])
    )
    return result if canonical(expected) == g else None


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


@cache
def as_tiny(g: Game) -> Game | None:
    """If ``g`` is ``tiny-x`` for some ``x``, return that ``x``; else None.

    >>> as_tiny(tiny(2)) == number(2)
    True
    >>> as_tiny(STAR) is None
    True
    """
    c = canonical(g)
    if len(c.left) != 1 or len(c.right) != 1:
        return None
    if next(iter(c.left)) != ZERO:
        return None
    inner = next(iter(c.right))
    if len(inner.left) != 1 or len(inner.right) != 1:
        return None
    if next(iter(inner.left)) != ZERO:
        return None
    candidate = canonical(negate(next(iter(inner.right))))
    return candidate if c == canonical(tiny(candidate)) else None


def as_miny(g: Game) -> Game | None:
    """If ``g`` is ``miny-x`` for some ``x``, return that ``x``; else None."""
    return as_tiny(canonical(negate(g)))


def norton_product(g: Game, unit: Game) -> Game:
    """The Norton product ``g . unit``, also written ``g`` copies of ``unit``.

    For integer ``g`` this is literally that many copies summed. Otherwise

        ``g . U = {g^L . U + (U + I) | g^R . U - (U + I)}``

    where ``I`` ranges over the incentives of ``U``. Overheating in disguise:
    the unit replaces the number 1 as the step by which play moves.

    >>> from pycgt.notation import render
    >>> render(norton_product(integer(3), UP))
    '^3'
    >>> render(norton_product(integer(2), STAR))
    '0'
    >>> render(norton_product(number("1/2"), UP))
    '{^^*|v*}'
    """
    return _norton(canonical(g), canonical(unit))


@cache
def _norton(g: Game, unit: Game) -> Game:
    from .game import incentives

    count = as_number(g)
    if count is not None and count.denominator == 1:
        return multiple(unit, count.numerator)
    steps = [add(unit, i) for i in incentives(unit)]
    left = frozenset(add(_norton(l, unit), s) for l in g.left for s in steps)
    right = frozenset(add(_norton(r, unit), negate(s)) for r in g.right for s in steps)
    return canonical(Game(left, right))
