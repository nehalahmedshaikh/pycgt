"""Thermography: heating, overheating, cooling, temperature and mean value.

Cooling asks how much of a game's apparent value survives a tax on moving.
Heating and overheating run the process backwards, and are how closed-form
solutions to hot games are usually expressed -- Berlekamp's solutions to
Blockbusting and to Domineering are both stated with overheating operators.

Temperature and mean come from the **thermograph**, computed exactly. The two
boundaries

    L_G(t) = max over G^L of  R_(G^L)(t) - t
    R_G(t) = min over G^R of  L_(G^R)(t) + t

are piecewise-linear functions of ``t``; they meet at the temperature, and the
value where they meet is the mean. Both are represented exactly by
:mod:`pycgt._piecewise`, so temperatures come out as exact
:class:`~fractions.Fraction` s.

It is tempting to skip the thermograph and instead cool by successive values of
``t`` until the result is a number. That does not work: once the boundaries
cross, the crossing value is lost, and canonicalising the crossed game yields
the *simplest* number in the overshoot rather than the mast. That mistake makes
cooling non-monotone, which is how it was caught here.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import cache

from ._piecewise import PiecewiseLinear
from .game import Game, add, canonical, game, negate
from .values import as_number, is_number, number

__all__ = [
    "Thermograph",
    "cool",
    "heat",
    "mean",
    "overheat",
    "temperature",
    "thermograph",
]


# ---------------------------------------------------------------------------
# Heating and overheating
# ---------------------------------------------------------------------------


@cache
def heat(g: Game, t: Game) -> Game:
    """``g`` heated by ``t``: ``{t + heat(G^L) | -t + heat(G^R)}``.

    Stops at numbers. ``t`` may itself be a game -- a number, or a number plus
    star, is the usual case.

    >>> from pycgt.values import STAR, number
    >>> from pycgt.notation import render
    >>> render(heat(STAR, number("3/4")))
    '+-3/4'
    """
    g = canonical(g)
    if is_number(g):
        return g
    minus_t = negate(t)
    left = frozenset(add(t, heat(l, t)) for l in g.left)
    right = frozenset(add(minus_t, heat(r, t)) for r in g.right)
    return canonical(Game(left, right))


@cache
def overheat(g: Game, s: Game, t: Game) -> Game:
    """``g`` overheated from ``s`` to ``t``.

    Differs from :func:`heat` in its base case: overheating stops only at
    *integers*, and maps the integer ``n`` to ``n`` copies of ``s``. That is
    what makes a term linear in ``n`` appear in closed-form solutions.

    >>> from pycgt.values import number
    >>> from pycgt.notation import render
    >>> render(overheat(number(3), number("1/2"), number("1/2")))
    '3/2'
    """
    g = canonical(g)
    value = as_number(g)
    if value is not None and value.denominator == 1:
        total = Game(frozenset(), frozenset())
        for _ in range(abs(value.numerator)):
            total = add(total, s)
        return negate(total) if value.numerator < 0 else total
    minus_t = negate(t)
    left = frozenset(add(t, overheat(l, s, t)) for l in g.left)
    right = frozenset(add(minus_t, overheat(r, s, t)) for r in g.right)
    return canonical(Game(left, right))


# ---------------------------------------------------------------------------
# Thermographs
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Thermograph:
    """The two boundaries of a game, plus where and at what value they meet."""

    left: PiecewiseLinear
    right: PiecewiseLinear
    temperature: Fraction
    mast: Fraction

    def at(self, t: Fraction) -> tuple[Fraction, Fraction]:
        """``(left boundary, right boundary)`` at temperature ``t``."""
        return self.left(t), self.right(t)


@cache
def thermograph(g: Game) -> Thermograph:
    """The exact thermograph of ``g``.

    A number does not cool: its boundaries are the constant function, and by
    the convention CGSuite reports, a number with denominator ``2**k`` is
    assigned temperature ``-1/2**k``.
    """
    g = canonical(g)
    value = as_number(g)
    if value is not None:
        constant = PiecewiseLinear.constant(value)
        return Thermograph(
            left=constant,
            right=constant,
            temperature=Fraction(-1, value.denominator),
            mast=value,
        )

    left_candidate = PiecewiseLinear.max_of(
        thermograph(l).right.minus_t() for l in g.left
    )
    right_candidate = PiecewiseLinear.min_of(
        thermograph(r).left.plus_t() for r in g.right
    )

    tau = left_candidate.first_at_or_below(right_candidate)
    if tau < 0:
        tau = Fraction(0)
    mast = left_candidate(tau)

    return Thermograph(
        left=left_candidate.frozen_from(tau, mast),
        right=right_candidate.frozen_from(tau, mast),
        temperature=tau,
        mast=mast,
    )


def temperature(g: Game) -> Fraction:
    """The temperature of ``g``: how much is at stake in moving.

    For a non-number this is where the thermograph's boundaries meet. Numbers
    are cold; see :func:`thermograph` for the convention used.

    >>> from pycgt.values import plus_minus
    >>> temperature(plus_minus(1))
    Fraction(1, 1)
    """
    return thermograph(g).temperature


def mean(g: Game) -> Fraction:
    """The mean value of ``g``: the number it cools to, also called the mast.

    >>> from pycgt.notation import parse
    >>> mean(parse("{2|-1/2}"))
    Fraction(3, 4)
    """
    return thermograph(g).mast


# ---------------------------------------------------------------------------
# Cooling
# ---------------------------------------------------------------------------


@cache
def cool(g: Game, t: Fraction) -> Game:
    """``g`` cooled by ``t``, for ``t >= 0``.

    Each move is taxed ``t``. At and beyond the temperature the game freezes at
    its mean -- taken from the thermograph, not guessed from the cooled options.
    """
    if t < 0:
        raise ValueError("cooling temperature must be non-negative")
    g = canonical(g)
    if is_number(g):
        return g

    graph = thermograph(g)
    if t >= graph.temperature:
        return number(graph.mast)

    tax = number(t)
    left = frozenset(add(cool(l, t), negate(tax)) for l in g.left)
    right = frozenset(add(cool(r, t), tax) for r in g.right)
    return game(left, right)
