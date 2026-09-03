"""Short games: the core object, its order, its arithmetic, and canonical form.

A *short game* is a pair of finite sets of short games -- Left's options and
Right's options -- and nothing else. Everything in combinatorial game theory is
built from the empty game up, so nothing here is approximate: two games are
equal, or one is greater, or they are *confused* with each other. There is no
tolerance to set and no rounding to worry about.

The load-bearing operation is :func:`canonical`. Two games of the same value
have *identical* canonical forms, so once canonicalised, structural equality is
value equality and comparison becomes a dictionary lookup. Without it, the
values arising in real rulesets become unprintable and uncomparable within a
few moves.

**Invariant.** Every :class:`Game` returned by this package's public API is in
canonical form. ``==`` therefore means value equality for such games. If you
build a :class:`Game` by calling the constructor directly, that invariant is
yours to maintain -- use :func:`game`, which canonicalises, or call
:func:`equals` if unsure.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from functools import cache

__all__ = [
    "ZERO",
    "Game",
    "Outcome",
    "add",
    "birthday",
    "canonical",
    "compare",
    "confused",
    "equals",
    "game",
    "geq",
    "greater",
    "leq",
    "negate",
    "outcome",
]


@dataclass(frozen=True, slots=True)
class Game:
    """The game ``{left | right}``.

    Instances are hashable and immutable. Prefer the :func:`game` factory,
    which returns the canonical form.
    """

    left: frozenset[Game]
    right: frozenset[Game]

    # -- construction ----------------------------------------------------

    @staticmethod
    def of(left: Iterable[Game] = (), right: Iterable[Game] = ()) -> Game:
        """The canonical game with the given options. Alias of :func:`game`."""
        return game(left, right)

    # -- arithmetic ------------------------------------------------------

    def __neg__(self) -> Game:
        return negate(self)

    def __add__(self, other: Game) -> Game:
        return add(self, other)

    def __sub__(self, other: Game) -> Game:
        return add(self, negate(other))

    def __mul__(self, count: int) -> Game:
        """``n`` copies summed. Not the Norton or ordinal product."""
        if not isinstance(count, int):
            return NotImplemented
        return multiple(self, count)

    __rmul__ = __mul__

    # -- order -----------------------------------------------------------
    # Games are only partially ordered, so <= and >= are genuine but < and >
    # are deliberately *not* defined: "not (G <= H)" does not imply "G > H".
    # Use compare() for the four-way answer.

    def __le__(self, other: Game) -> bool:
        return leq(self, other)

    def __ge__(self, other: Game) -> bool:
        return geq(self, other)

    # -- display ---------------------------------------------------------

    def __str__(self) -> str:
        from .notation import render

        return render(self)

    def __repr__(self) -> str:
        return f"Game({self})"

    # -- convenience -----------------------------------------------------

    @property
    def canonical(self) -> Game:
        """The canonical form. A no-op for games from the public API."""
        return canonical(self)

    @property
    def birthday(self) -> int:
        return birthday(self)

    @property
    def outcome(self) -> Outcome:
        """Who wins under normal play."""
        return outcome(self)

    @property
    def is_zero(self) -> bool:
        return canonical(self) == ZERO


def game(left: Iterable[Game] = (), right: Iterable[Game] = ()) -> Game:
    """The canonical game ``{left | right}``."""
    return canonical(Game(frozenset(left), frozenset(right)))


#: The empty game. Second player wins.
ZERO = Game(frozenset(), frozenset())


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------
# Conway's definition: G >= H unless some H^L >= G, or some G^R <= H. The
# recursion terminates because every option is strictly simpler than its
# parent.

_geq_cache: dict[tuple[Game, Game], bool] = {}


def geq(g: Game, h: Game) -> bool:
    """``g >= h``: Left wins ``g - h`` moving second."""
    key = (g, h)
    cached = _geq_cache.get(key)
    if cached is not None:
        return cached
    result = not any(geq(hl, g) for hl in h.left) and not any(
        geq(h, gr) for gr in g.right
    )
    _geq_cache[key] = result
    return result


def leq(g: Game, h: Game) -> bool:
    """``g <= h``."""
    return geq(h, g)


def equals(g: Game, h: Game) -> bool:
    """Value equality, whether or not either argument is canonical."""
    return geq(g, h) and geq(h, g)


def greater(g: Game, h: Game) -> bool:
    """``g > h``: strictly greater."""
    return geq(g, h) and not geq(h, g)


def confused(g: Game, h: Game) -> bool:
    """Neither ``>=`` nor ``<=``: whoever moves first in ``g - h`` wins."""
    return not geq(g, h) and not geq(h, g)


class Outcome(Enum):
    """Who wins under normal play, where a player unable to move loses."""

    LEFT = "Left"
    RIGHT = "Right"
    FIRST = "first player"
    SECOND = "second player"

    def __str__(self) -> str:
        return self.value


def outcome(g: Game) -> Outcome:
    """Classify ``g`` as positive, negative, zero, or confused with zero."""
    positive, negative = geq(g, ZERO), geq(ZERO, g)
    if positive and negative:
        return Outcome.SECOND
    if positive:
        return Outcome.LEFT
    if negative:
        return Outcome.RIGHT
    return Outcome.FIRST


class Relation(Enum):
    """The four possible relations between two games."""

    EQUAL = "="
    GREATER = ">"
    LESS = "<"
    CONFUSED = "||"

    def __str__(self) -> str:
        return self.value


def compare(g: Game, h: Game) -> Relation:
    """The four-way comparison. Use this instead of ``<`` and ``>``."""
    ge, le = geq(g, h), leq(g, h)
    if ge and le:
        return Relation.EQUAL
    if ge:
        return Relation.GREATER
    if le:
        return Relation.LESS
    return Relation.CONFUSED


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------


@cache
def negate(g: Game) -> Game:
    """``-g``: the same game with the players' roles exchanged."""
    return Game(
        frozenset(negate(r) for r in g.right),
        frozenset(negate(l) for l in g.left),
    )


@cache
def _add_raw(g: Game, h: Game) -> Game:
    return Game(
        frozenset(
            [_add_raw(gl, h) for gl in g.left] + [_add_raw(g, hl) for hl in h.left]
        ),
        frozenset(
            [_add_raw(gr, h) for gr in g.right] + [_add_raw(g, hr) for hr in h.right]
        ),
    )


def add(g: Game, h: Game) -> Game:
    """Disjunctive sum, canonicalised.

    Canonicalising here rather than lazily matters: letting raw sums
    accumulate makes the trees explode, and summing many components is the
    common case.
    """
    return canonical(_add_raw(g, h))


def multiple(g: Game, count: int) -> Game:
    """``count`` copies of ``g`` summed, for any integer ``count``."""
    total = ZERO
    for _ in range(abs(count)):
        total = add(total, g)
    return negate(total) if count < 0 else total


# ---------------------------------------------------------------------------
# Canonical form
# ---------------------------------------------------------------------------


def _undominated_left(options: frozenset[Game]) -> frozenset[Game]:
    """Left never needs an option that another of Left's options beats."""
    return frozenset(
        l for l in options if not any(o is not l and geq(o, l) for o in options)
    )


def _undominated_right(options: frozenset[Game]) -> frozenset[Game]:
    return frozenset(
        r for r in options if not any(o is not r and leq(o, r) for o in options)
    )


def _bypass_left(options: frozenset[Game], g: Game) -> frozenset[Game]:
    """Replace each reversible Left option by what it reverses to.

    If Left moves to ``G^L`` and Right can answer ``G^L -> G^{LR}`` with
    ``G^{LR} <= G``, Right will always take that answer, so the detour is
    worth nothing and Left's real choices are those available after it.
    """
    out: set[Game] = set()
    for l in options:
        reverser = next((lr for lr in l.right if leq(lr, g)), None)
        if reverser is None:
            out.add(l)
        else:
            out.update(reverser.left)
    return frozenset(out)


def _bypass_right(options: frozenset[Game], g: Game) -> frozenset[Game]:
    out: set[Game] = set()
    for r in options:
        reverser = next((rl for rl in r.left if geq(rl, g)), None)
        if reverser is None:
            out.add(r)
        else:
            out.update(reverser.right)
    return frozenset(out)


@cache
def canonical(g: Game) -> Game:
    """The unique simplest game of the same value.

    Options are canonicalised first, then dominated options are dropped and
    reversible ones bypassed, repeatedly, until nothing changes. The result is
    unique: two games are equal in value precisely when their canonical forms
    are identical.
    """
    left = frozenset(canonical(x) for x in g.left)
    right = frozenset(canonical(x) for x in g.right)
    while True:
        current = Game(left, right)
        new_left = _undominated_left(_bypass_left(left, current))
        new_right = _undominated_right(_bypass_right(right, current))
        if new_left == left and new_right == right:
            return current
        left, right = new_left, new_right


@cache
def is_all_small(g: Game) -> bool:
    """True if, in every subposition, Left can move exactly when Right can.

    All-small games never hand either player a free move, so they are
    infinitesimal. The converse fails: ``tiny-2`` is infinitesimal but not
    all-small, because the number ``-2`` sits inside it and offers Right a move
    where Left has none.

    >>> from pycgt.values import STAR, UP, number, tiny
    >>> is_all_small(STAR), is_all_small(UP)
    (True, True)
    >>> is_all_small(number(1)), is_all_small(tiny(2))
    (False, False)
    """
    if bool(g.left) != bool(g.right):
        return False
    return all(is_all_small(option) for option in list(g.left) + list(g.right))


@cache
def incentives(g: Game) -> frozenset[Game]:
    """The maximal incentives of ``g``.

    A *Left incentive* is ``G^L - G`` and a *Right incentive* is ``G - G^R``:
    what a player gains by moving there. Only the maximal ones bear on play, so
    only those are returned, which is also the convention CGSuite reports.

    >>> from pycgt.notation import render
    >>> from pycgt.values import plus_minus
    >>> sorted(render(i) for i in incentives(plus_minus(1)))
    ['{2|0}']
    >>> incentives(ZERO)
    frozenset()
    """
    candidates = [add(l, negate(g)) for l in g.left]
    candidates += [add(g, negate(r)) for r in g.right]
    # Deduplicate by *value* before filtering. Two incentives can be equal
    # while being distinct objects -- 1/2 has Left incentive 0 - 1/2 and Right
    # incentive 1/2 - 1, both -1/2, built from different sums -- and an
    # identity-based filter would let each eliminate the other, returning
    # nothing. The option sets inside `canonical` are frozensets, so they
    # cannot contain equal-but-distinct members and are unaffected.
    distinct = set(candidates)
    return frozenset(
        c for c in distinct if not any(o != c and geq(o, c) for o in distinct)
    )


@cache
def birthday(g: Game) -> int:
    """The day ``g`` is born: 0 for the empty game, else one past its options."""
    options = list(g.left) + list(g.right)
    return 1 + max((birthday(x) for x in options), default=-1)
