"""Impartial games and misère play: nim values, misère nim values, and the genus.

An *impartial* game gives both players the same options, so a position is just a
finite set of positions. Under normal play the theory is complete and easy:
every impartial game equals a nimber, and a sum is the exclusive-or of its parts
(Sprague--Grundy). Under *misère* play -- where the player who cannot move
**wins** -- almost all of that collapses, and what replaces it is the genus.

**Why this module needs its own game type.** :class:`~pycgt.game.Game` is
canonical by construction, and normal-play canonical form destroys exactly the
information misère play depends on. Two heaps of two are worth zero in normal
play, so a :class:`~pycgt.game.Game` cannot tell them apart from the endgame --
but they are a misère *loss* for the mover while the endgame is a *win*:

    >>> two = add(nim_heap(2), nim_heap(2))
    >>> nim_value(two), nim_value(ENDGAME)            # normal play: identical
    (0, 0)
    >>> misere_outcome(two), misere_outcome(ENDGAME)  # misère play: opposite
    (<Outcome.SECOND: 'second player'>, <Outcome.FIRST: 'first player'>)

So :class:`Impartial` applies **no** reduction at all. It is the raw game tree,
and :func:`add` is the structural sum. Nothing here may be routed through
:func:`~pycgt.game.canonical`.

**What the genus is.** The genus of ``G`` records the nim value of ``G``
together with the misère nim values of ``G``, ``G + *2``, ``G + *2 + *2``, ...
That sequence is eventually alternating, which is what makes a finite symbol
possible. See *Winning Ways* chapter 13, or Siegel's *Combinatorial Game
Theory* chapter V.2.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache

from .game import Game, Outcome

__all__ = [
    "ENDGAME",
    "Genus",
    "Impartial",
    "add",
    "birthday",
    "genus",
    "genus_sequence",
    "impartial",
    "is_tame",
    "misere_nim_value",
    "misere_outcome",
    "multiple",
    "nim_heap",
    "nim_position_genera",
    "nim_value",
    "normal_outcome",
    "normal_value",
]


#: Every distinct game tree is built exactly once and shared. Interning is not
#: an optimisation detail here: without reduction these trees are deep, and
#: comparing or hashing two of them structurally costs time proportional to
#: their size. Sharing makes structural equality *identity*, which turns both
#: into constant-time operations. Measured on Kayles heaps, the structural
#: version cost about 3.6x more per heap size and became unusable around 20;
#: interned, the whole table to 40 is immediate.
_interned: dict[frozenset[Impartial], Impartial] = {}


class Impartial:
    """An impartial short game: the set of positions either player may move to.

    Deliberately **not** reduced. Two instances are equal only when their game
    trees are identical, which is far finer than equality in either normal or
    misère play. Use :func:`nim_value` for normal-play equality and the
    :func:`genus` for misère information.

    Instances are interned, so equal trees are the same object and ``==`` is a
    pointer comparison. Construct them with :func:`impartial`, :func:`nim_heap`
    or :func:`add`.
    """

    __slots__ = ("_hash", "options")

    options: frozenset[Impartial]
    _hash: int

    def __new__(cls, options: Iterable[Impartial] = ()) -> Impartial:
        key = options if type(options) is frozenset else frozenset(options)
        shared = _interned.get(key)
        if shared is not None:
            return shared
        self = object.__new__(cls)
        self.options = key
        # Sound only because every instance is interned: distinct objects are
        # never equal, so a counter is a perfectly good hash.
        self._hash = len(_interned)
        _interned[key] = self
        return self

    def __init__(self, options: Iterable[Impartial] = ()) -> None:
        # All the work happens in __new__; this exists so that passing the
        # argument through is not an error.
        pass

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: object) -> bool:
        return self is other

    def __add__(self, other: Impartial) -> Impartial:
        return add(self, other)

    def __mul__(self, count: int) -> Impartial:
        if not isinstance(count, int):
            return NotImplemented
        return multiple(self, count)

    __rmul__ = __mul__

    def __str__(self) -> str:
        if not self.options:
            return "0"
        return "{" + ",".join(sorted(str(o) for o in self.options)) + "}"

    def __repr__(self) -> str:
        return f"Impartial({self})"

    @property
    def birthday(self) -> int:
        return birthday(self)

    @property
    def nim_value(self) -> int:
        return nim_value(self)

    @property
    def misere_nim_value(self) -> int:
        return misere_nim_value(self)

    @property
    def genus(self) -> Genus:
        return genus(self)


#: The game with no moves. Under normal play the mover loses; under misère play
#: the mover wins. This single sign flip is the whole of misère theory's
#: difficulty.
ENDGAME = Impartial(frozenset())


def impartial(options: Iterable[Impartial] = ()) -> Impartial:
    """The impartial game with the given options, with no reduction applied."""
    return Impartial(frozenset(options))


@cache
def nim_heap(size: int) -> Impartial:
    """A Nim heap of ``size`` tokens: move to any smaller heap.

    >>> nim_value(nim_heap(7))
    7
    >>> misere_nim_value(nim_heap(7))
    7
    >>> misere_nim_value(nim_heap(1))     # the one heap misère play reverses
    0
    """
    if size < 0:
        raise ValueError("a heap cannot have negative size")
    return Impartial(frozenset(nim_heap(k) for k in range(size)))


@cache
def add(g: Impartial, h: Impartial) -> Impartial:
    """The disjunctive sum, built structurally and **not** reduced.

    Contrast :func:`pycgt.game.add`, which canonicalises: there, two heaps of
    two collapse to zero. Here nothing collapses, because misère play can tell
    the two apart.

    >>> nim_value(add(nim_heap(2), nim_heap(2)))
    0
    >>> add(nim_heap(2), nim_heap(2)) == ENDGAME
    False
    """
    return Impartial(
        frozenset(
            [add(x, h) for x in g.options] + [add(g, y) for y in h.options],
        )
    )


def multiple(g: Impartial, count: int) -> Impartial:
    """``count`` copies of ``g`` summed. There are no inverses in misère play,
    so ``count`` must not be negative."""
    if count < 0:
        raise ValueError("impartial games have no additive inverses in misère play")
    total = ENDGAME
    for _ in range(count):
        total = add(total, g)
    return total


@cache
def birthday(g: Impartial) -> int:
    """The day ``g`` is born: 0 for the endgame, else one past its options."""
    return 1 + max((birthday(o) for o in g.options), default=-1)


def _mex(values: frozenset[int]) -> int:
    """The minimum excludant: the least non-negative integer not in ``values``."""
    m = 0
    while m in values:
        m += 1
    return m


# ---------------------------------------------------------------------------
# Normal play
# ---------------------------------------------------------------------------


@cache
def nim_value(g: Impartial) -> int:
    """The nim value (Grundy value) ``g(G) = mex{g(G') : G' in G}``.

    Under normal play ``G`` equals the nimber ``*g(G)``, so this is a complete
    answer: a sum is a loss for the mover exactly when the exclusive-or of its
    parts' nim values is zero.

    >>> nim_value(ENDGAME)
    0
    >>> nim_value(add(nim_heap(3), nim_heap(5)))
    6
    """
    return _mex(frozenset(nim_value(o) for o in g.options))


def normal_value(g: Impartial) -> Game:
    """``g`` as a normal-play :class:`~pycgt.game.Game`, always a nimber.

    This is a lossy bridge, and deliberately so -- it is the step that discards
    the misère information.

    >>> from pycgt.notation import render
    >>> render(normal_value(add(nim_heap(3), nim_heap(5))))
    '*6'
    """
    from .values import nimber

    return nimber(nim_value(g))


def normal_outcome(g: Impartial) -> Outcome:
    """Who wins under normal play, where a player unable to move loses."""
    return Outcome.SECOND if nim_value(g) == 0 else Outcome.FIRST


# ---------------------------------------------------------------------------
# Misère play
# ---------------------------------------------------------------------------


@cache
def misere_nim_value(g: Impartial) -> int:
    """The misère nim value ``g⁻(G)``.

    Defined by ``g⁻(G) = 1`` when ``G`` has no options, and
    ``g⁻(G) = mex{g⁻(G') : G' in G}`` otherwise. Equivalently it is the unique
    ``m`` with ``G + *m`` a loss for the mover -- but note that, unlike normal
    play, this does **not** mean ``G`` equals ``*m`` in misère play, and misère
    nim values are **not** additive.

    The single base case ``g⁻(0) = 1`` is the whole difference from
    :func:`nim_value`, and it is why misère Nim swaps the roles of heaps of
    size one:

    >>> [misere_nim_value(nim_heap(n)) for n in range(6)]
    [1, 0, 2, 3, 4, 5]
    """
    if not g.options:
        return 1
    return _mex(frozenset(misere_nim_value(o) for o in g.options))


@cache
def _misere_mover_wins(g: Impartial) -> bool:
    """Whether the player to move in ``g`` wins under misère play.

    Computed straight from the rules -- a player unable to move wins -- so it
    is independent of :func:`misere_nim_value` and can check it.
    """
    if not g.options:
        return True
    return any(not _misere_mover_wins(o) for o in g.options)


def misere_outcome(g: Impartial) -> Outcome:
    """Who wins under misère play, where a player unable to move **wins**.

    >>> misere_outcome(nim_heap(1))
    <Outcome.SECOND: 'second player'>
    >>> misere_outcome(ENDGAME)
    <Outcome.FIRST: 'first player'>
    """
    return Outcome.FIRST if _misere_mover_wins(g) else Outcome.SECOND


# ---------------------------------------------------------------------------
# The genus
# ---------------------------------------------------------------------------

#: Default number of superscript terms computed when looking for the
#: alternation, and how many of them must confirm it. Every position examined
#: while building this module settled within three terms; the budget is well
#: clear of that, and :func:`genus` raises rather than guess if it is exceeded.
_GENUS_TERMS = 10
_GENUS_CONFIRM = 4


def genus_sequence(g: Impartial, terms: int = _GENUS_TERMS) -> tuple[int, ...]:
    """The misère nim values of ``g``, ``g + *2``, ``g + *2 + *2``, ...

    This is the raw content of the genus superscript, before any decision about
    how to write it down.

    >>> genus_sequence(ENDGAME, 6)
    (1, 2, 0, 2, 0, 2)
    >>> genus_sequence(nim_heap(1), 6)
    (0, 3, 1, 3, 1, 3)
    """
    if terms < 1:
        raise ValueError("need at least one term")
    two = nim_heap(2)
    values, running = [], g
    for _ in range(terms):
        values.append(misere_nim_value(running))
        running = add(running, two)
    return tuple(values)


@dataclass(frozen=True, slots=True)
class Genus:
    """A genus symbol: a nim value and a superscript.

    The superscript is the sequence of misère nim values of ``G + k·*2``, which
    is eventually alternating between some ``d`` and ``d XOR 2``. It is stored
    as the terms before the alternation followed by exactly two terms showing
    the alternating pair, so ``superscript`` always has length at least two and
    determines the whole infinite sequence via :meth:`term`.

    >>> genus(nim_heap(0))
    Genus(0^120)
    >>> genus(nim_heap(2))
    Genus(2^20)
    >>> print(genus(nim_heap(1)))
    1^031
    """

    nim_value: int
    superscript: tuple[int, ...]

    def __post_init__(self) -> None:
        if len(self.superscript) < 2:
            raise ValueError("a superscript must show both alternating terms")

    def term(self, k: int) -> int:
        """The ``k``-th superscript term, for any ``k`` however large.

        >>> g = genus(nim_heap(0))
        >>> [g.term(k) for k in range(7)]
        [1, 2, 0, 2, 0, 2, 0]
        """
        if k < 0:
            raise ValueError("term index must not be negative")
        first = len(self.superscript) - 2
        if k < first:
            return self.superscript[k]
        return self.superscript[first + (k - first) % 2]

    def __str__(self) -> str:
        return f"{self.nim_value}^" + "".join(str(t) for t in self.superscript)

    def __repr__(self) -> str:
        return f"Genus({self})"


def genus(
    g: Impartial,
    terms: int = _GENUS_TERMS,
    confirm: int = _GENUS_CONFIRM,
) -> Genus:
    """The genus of ``g``: its nim value, and its misère nim value sequence.

    The superscript is cut at the first point from which the sequence
    alternates between ``d`` and ``d XOR 2``, and two terms are then written so
    the alternating pair is visible. On Nim heaps this reproduces the
    traditional symbols ``0^120``, ``1^031``, ``2^20``, ``3^31``, ``4^46``.

    ``terms`` values are computed and the alternation must hold over at least
    ``confirm`` of them. That the sequence alternates eventually is a theorem;
    that it does so within ``terms`` is not, so a position that has not settled
    raises :exc:`ValueError` rather than being reported on partial evidence.

    .. warning::
       CGSuite's ``Genus`` is the *extended* genus and is not the same object.
       It prints a superscript whose length carries information beyond the
       classical genus: Kayles heaps 7 and 19 have the same nim value and the
       same superscript sequence (checked to 17 terms), yet CGSuite prints
       ``2^2`` and ``2^20``. Where CGSuite prints two or more superscript
       digits, this function agrees with it.

    >>> print(genus(nim_heap(3)))
    3^31
    >>> print(genus(add(nim_heap(2), nim_heap(2))))
    0^02
    """
    if confirm < 2:
        raise ValueError("need at least two terms to see the alternating pair")
    sequence = genus_sequence(g, terms)
    for start in range(len(sequence) - confirm + 1):
        pair = (sequence[start], sequence[start] ^ 2)
        if all(
            value == pair[(index - start) % 2]
            for index, value in enumerate(sequence[start:], start)
        ):
            return Genus(nim_value(g), tuple(sequence[:start]) + pair)
    raise ValueError(
        f"superscript {sequence} has not begun to alternate within {terms} terms; "
        "raise `terms` if the position really is this slow to settle"
    )


def nim_position_genera(nim_value: int) -> frozenset[Genus]:
    """Every genus a Nim position of this nim value can have.

    A Nim position holding a heap of two or more behaves in misère play exactly
    as it does in normal play, giving genus ``v^{v,v XOR 2}``. The only other
    cases are positions whose heaps are all of size one, which reduce to the
    endgame's ``0^120`` or a single heap's ``1^031``.

    >>> sorted(str(x) for x in nim_position_genera(0))
    ['0^02', '0^120']
    >>> sorted(str(x) for x in nim_position_genera(3))
    ['3^31']
    """
    if nim_value < 0:
        raise ValueError("nim values are not negative")
    genera = {Genus(nim_value, (nim_value, nim_value ^ 2))}
    if nim_value == 0:
        genera.add(Genus(0, (1, 2, 0)))
    if nim_value == 1:
        genera.add(Genus(1, (0, 3, 1)))
    return frozenset(genera)


def is_tame(g: Impartial) -> bool:
    """Whether ``g`` has the genus of a Nim position.

    *Winning Ways* calls such games **tame** and all others **wild**. A tame
    game can be played by misère Nim's own rules, so this is the dividing line
    of classical misère theory. Note that a tame game need not have the genus
    of a single Nim *heap*: two heaps of two have genus ``0^02``, which is the
    genus of the Nim position ``{2,2}`` and not of any heap.

    .. warning::
       This is the genus-based notion. It is strictly **weaker** than CGSuite's
       ``IsTame``, which also asks that the misère canonical form be that of a
       Nim position. Kayles heap 7 has exactly the genus of ``*2`` -- nim value
       2, superscript ``2^20`` -- so it is tame here, while CGSuite reports
       ``IsTame`` as false. Every game CGSuite calls tame is tame here; the
       converse fails.

    >>> is_tame(nim_heap(5)), is_tame(add(nim_heap(2), nim_heap(2)))
    (True, True)
    >>> is_tame(nim_heap(0))
    True
    """
    symbol = genus(g)
    return symbol in nim_position_genera(symbol.nim_value)
