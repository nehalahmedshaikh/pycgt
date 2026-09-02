"""Reduced canonical form: the value with its infinitesimals quotiented away.

The reduced canonical form of ``G`` is the simplest game infinitesimally close
to ``G`` (Calistrate 1996; Grossman and Siegel later gave another existence
proof). It is the formal content of the informal phrase "known to within ish":
a value known up to an infinitesimal is a value whose reduced form is known.

So :func:`ish` -- the difference between a game and its reduced form -- isolates
exactly the infinitesimal part, and is infinitesimal by construction. The test
suite checks that property on every value it computes, which is the strongest
cheap check available on :func:`reduced_canonical_form`.
"""

from __future__ import annotations

from functools import cache

from .game import Game, add, canonical, negate
from .stops import is_infinitesimal, number_part
from .values import number

__all__ = ["is_reduced", "ish", "reduced_canonical_form"]


@cache
def reduced_canonical_form(g: Game) -> Game:
    """The simplest game infinitesimally close to ``g``.

    If ``g`` is infinitesimally close to a number, that number *is* the reduced
    form -- every infinitesimal detail is discarded. Otherwise ``g`` is hot, and
    the reduction applies to its options.

    >>> from pycgt.values import STAR, UP, number
    >>> reduced_canonical_form(STAR).is_zero
    True
    >>> reduced_canonical_form(add(number(1), UP)) == number(1)
    True
    """
    close = number_part(g)
    if close is not None:
        return number(close)
    left = frozenset(reduced_canonical_form(x) for x in g.left)
    right = frozenset(reduced_canonical_form(x) for x in g.right)
    return canonical(Game(left, right))


@cache
def ish(g: Game) -> Game:
    """``g`` minus its reduced canonical form: the infinitesimal remainder.

    Always infinitesimal. This is the quantity that classical "to within ish"
    results leave undetermined.
    """
    return add(canonical(g), negate(reduced_canonical_form(g)))


def is_reduced(g: Game) -> bool:
    """True if ``g`` is its own reduced canonical form."""
    return canonical(g) == reduced_canonical_form(g)


def ish_is_infinitesimal(g: Game) -> bool:
    """Must always hold; used as a self-check in the test suite."""
    return is_infinitesimal(ish(g))
