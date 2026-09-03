"""Structural properties of a game, and the two non-disjunctive sums.

Nothing here is about *values* in the ordinary sense. These are questions about
the shape of a game tree -- how many stops it has, whether its play length is
forced to be even or odd, what positions it can reach -- together with the two
other ways of combining games that come up in practice.
"""

from __future__ import annotations

from functools import cache

from .game import Game, add, canonical
from .values import is_number

__all__ = [
    "conjunctive_sum",
    "follower_count",
    "followers",
    "is_even_tempered",
    "is_idempotent",
    "is_odd_tempered",
    "selective_sum",
    "stop_count",
]


@cache
def stop_count(g: Game) -> int:
    """How many stops ``g`` has, counted with multiplicity.

    One for a number, and otherwise the total over every option on both sides.
    It measures how much of the tree survives to the end of play.

    >>> from pycgt.values import STAR, UP, nimber, number
    >>> stop_count(number(3)), stop_count(STAR), stop_count(UP)
    (1, 2, 3)
    >>> stop_count(nimber(2))
    6
    """
    c = canonical(g)
    if is_number(c):
        return 1
    return sum(stop_count(option) for option in list(c.left) + list(c.right))


@cache
def is_even_tempered(g: Game) -> bool:
    """True if every line of play in ``g`` lasts an even number of moves.

    A game is *even-tempered* if it is a number, or every option is
    odd-tempered; *odd-tempered* if it is not a number and every option is
    even-tempered. Plenty of games are neither -- ``*2`` has both a number and
    an odd-tempered game among its options.

    >>> from pycgt.values import STAR, nimber, number, plus_minus
    >>> is_even_tempered(number(1)), is_even_tempered(STAR)
    (True, False)
    >>> is_even_tempered(nimber(2)), is_odd_tempered(nimber(2))
    (False, False)
    >>> is_odd_tempered(plus_minus(1))
    True
    """
    c = canonical(g)
    if is_number(c):
        return True
    return all(is_odd_tempered(option) for option in list(c.left) + list(c.right))


@cache
def is_odd_tempered(g: Game) -> bool:
    """True if every line of play in ``g`` lasts an odd number of moves.

    See :func:`is_even_tempered`.
    """
    c = canonical(g)
    if is_number(c):
        return False
    return all(is_even_tempered(option) for option in list(c.left) + list(c.right))


@cache
def followers(g: Game) -> frozenset[Game]:
    """Every position reachable from ``g``, including ``g`` itself.

    Values, not tree nodes: two options of the same value count once.

    >>> from pycgt.notation import render
    >>> from pycgt.values import up_multiple
    >>> sorted(render(x) for x in followers(up_multiple(2)))
    ['*', '0', '^*', '^^']
    """
    c = canonical(g)
    reached = {c}
    for option in list(c.left) + list(c.right):
        reached |= followers(option)
    return frozenset(reached)


def follower_count(g: Game) -> int:
    """How many distinct positions ``g`` can reach, itself included.

    >>> from pycgt.values import plus_minus, tiny, up_multiple
    >>> follower_count(up_multiple(2)), follower_count(plus_minus(1))
    (4, 4)
    >>> follower_count(tiny(2))
    5
    """
    return len(followers(g))


def is_idempotent(g: Game) -> bool:
    """True if ``g + g == g``.

    Among short games only zero qualifies, since every short game has an
    additive inverse. The test earns its keep on loopy games, where ``on`` and
    ``off`` are idempotent too.

    >>> from pycgt.game import ZERO
    >>> from pycgt.values import STAR
    >>> is_idempotent(ZERO), is_idempotent(STAR)
    (True, False)
    """
    c = canonical(g)
    return add(c, c) == c


# ---------------------------------------------------------------------------
# Sums that are not the disjunctive sum
# ---------------------------------------------------------------------------


@cache
def conjunctive_sum(g: Game, h: Game) -> Game:
    """Move in **both** components at once; play ends when either does.

    ``G and H = {G^L and H^L | G^R and H^R}``. A component with no options
    stops the whole game, so any summand equal to zero makes the sum zero.

    >>> from pycgt.notation import render
    >>> from pycgt.values import STAR, UP, integer
    >>> render(conjunctive_sum(UP, UP)), render(conjunctive_sum(UP, STAR))
    ('^', '*')
    >>> render(conjunctive_sum(integer(2), integer(1)))
    '1'
    """
    left = frozenset(
        conjunctive_sum(a, b) for a in canonical(g).left for b in canonical(h).left
    )
    right = frozenset(
        conjunctive_sum(a, b) for a in canonical(g).right for b in canonical(h).right
    )
    return canonical(Game(left, right))


@cache
def selective_sum(g: Game, h: Game) -> Game:
    """Move in **either or both** components.

    ``G or H = {G^L or H, G or H^L, G^L or H^L | ... }``. A move in any
    non-empty set of components leaves a selective sum again, which is what
    makes the recursion selective throughout. Unlike the disjunctive sum this
    does not cancel: ``*`` selectively plus ``*`` is ``*2``, where
    disjunctively it would be zero.

    .. warning::
       **CGSuite computes something else here**, and the two disagree on 52 of
       the 121 pairs drawn from a small pool of standard values. CGSuite's own
       documentation states the formula above, but its option list shows a move
       in one component leaving a *disjunctive* sum and a move in both leaving a
       *conjunctive* one, and its values follow that instead.

       The clearest witness is ``1/2`` against ``1/2``, where CGSuite gives
       ``3/4`` and this gives ``1``. Right moving in both components must land
       in ``1 or 1``, which is ``2`` and so a poor move; CGSuite instead lands
       in the conjunctive ``1 and 1``, which is ``1`` and looks attractive.
       Since a selective sum stays selective, ``1`` is the defensible answer,
       and it agrees with CGSuite's prose. :func:`conjunctive_sum`, by
       contrast, matches CGSuite everywhere tested.

    >>> from pycgt.notation import render
    >>> from pycgt.values import STAR, integer, number
    >>> render(selective_sum(STAR, STAR)), render(selective_sum(integer(1), integer(1)))
    ('*2', '2')
    >>> render(selective_sum(number("1/2"), number("1/2")))
    '1'
    """
    a, b = canonical(g), canonical(h)
    left = (
        {selective_sum(x, b) for x in a.left}
        | {selective_sum(a, y) for y in b.left}
        | {selective_sum(x, y) for x in a.left for y in b.left}
    )
    right = (
        {selective_sum(x, b) for x in a.right}
        | {selective_sum(a, y) for y in b.right}
        | {selective_sum(x, y) for x in a.right for y in b.right}
    )
    return canonical(Game(frozenset(left), frozenset(right)))
