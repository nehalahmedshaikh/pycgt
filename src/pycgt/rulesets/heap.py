"""Impartial games played on heaps: octal (take-and-break) games and friends.

A position is a multiset of heap sizes, and a move acts on one heap. These
rulesets exist here because they are the classical testbed for misère theory:
the nim-value and genus tables of Kayles and Dawson's Chess are published, so a
whole implementation can be checked against them rather than against itself.

The positions built here are :class:`~pycgt.impartial.Impartial`, not
:class:`~pycgt.game.Game`, because misère analysis cannot survive normal-play
canonical form. See :mod:`pycgt.impartial`.

>>> from pycgt.impartial import nim_value, misere_nim_value
>>> [nim_value(heap(KAYLES, n)) for n in range(12)]
[0, 1, 2, 3, 1, 4, 3, 2, 1, 4, 2, 6]
>>> misere_nim_value(heap(DAWSONS_CHESS, 5))
3
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache
from typing import Protocol, runtime_checkable

from ..impartial import ENDGAME, Impartial, add, impartial

__all__ = [
    "DAWSONS_CHESS",
    "GRUNDYS_GAME",
    "KAYLES",
    "OFFICERS",
    "TREBLECROSS",
    "GrundysGame",
    "HeapRuleset",
    "Octal",
    "Subtraction",
    "heap",
    "heaps",
    "misere_nim_values",
    "nim_values",
    "octal",
    "subtraction",
]


@runtime_checkable
class HeapRuleset(Protocol):
    """A ruleset whose positions are heaps of tokens.

    ``heap_options(n)`` returns, for a heap of ``n`` tokens, one tuple of heap
    sizes per legal move -- the position that move leaves behind. Implementations
    must be hashable, since positions are memoised on the ruleset, which is why
    the ones here are frozen dataclasses.
    """

    def heap_options(self, n: int) -> Iterable[tuple[int, ...]]: ...

    def __hash__(self) -> int: ...


@dataclass(frozen=True, slots=True)
class Octal:
    """A take-and-break game in the standard octal notation ``d0.d1d2d3...``.

    Digit ``d_k`` says what a player may do when removing exactly ``k`` tokens
    from a heap, by its bits:

    ==== ==========================================================
    bit  meaning
    ==== ==========================================================
    1    may take the whole heap, leaving nothing
    2    may take ``k`` tokens and leave the rest as one heap
    4    may take ``k`` tokens and split the rest into two heaps
    ==== ==========================================================

    ``d_0`` governs moves that remove nothing, so only its ``4`` bit means
    anything -- taking nothing and leaving one heap would be a null move.

    Build these with :func:`octal`, which parses the notation.
    """

    digits: tuple[int, ...]

    def heap_options(self, n: int) -> Iterable[tuple[int, ...]]:
        for taken, digit in enumerate(self.digits):
            if taken > n:
                break
            rest = n - taken
            # Removing nothing and leaving one heap is a move to the same
            # position, so bits 1 and 2 are meaningless for d_0.
            if taken > 0 and digit & 1 and rest == 0:
                yield ()
            if taken > 0 and digit & 2 and rest > 0:
                yield (rest,)
            if digit & 4:
                for part in range(1, rest // 2 + 1):
                    yield (part, rest - part)

    def __str__(self) -> str:
        head, *tail = self.digits
        return f"{head}." + "".join(str(d) for d in tail)


def octal(code: str) -> Octal:
    """Parse octal-game notation such as ``"0.77"`` (Kayles).

    A leading ``d_0`` is optional and defaults to ``0``.

    >>> str(octal("0.77")), str(octal(".137"))
    ('0.77', '0.137')
    >>> octal("0.77").digits
    (0, 7, 7)
    """
    head, _, tail = code.partition(".")
    if not _:
        raise ValueError(f"octal code needs a '.', got {code!r}")
    head = head or "0"
    if not (head + tail).isdigit() or any(c not in "01234567" for c in head + tail):
        raise ValueError(f"octal code must be octal digits, got {code!r}")
    if len(head) != 1:
        raise ValueError(
            f"octal code needs exactly one digit before the '.', got {code!r}"
        )
    return Octal((int(head), *(int(c) for c in tail)))


@dataclass(frozen=True, slots=True)
class Subtraction:
    """A subtraction game: remove any of ``sizes`` tokens from a heap.

    >>> from pycgt.impartial import nim_value
    >>> game = subtraction([1, 2])
    >>> [nim_value(heap(game, n)) for n in range(7)]
    [0, 1, 2, 0, 1, 2, 0]
    """

    sizes: frozenset[int]

    def heap_options(self, n: int) -> Iterable[tuple[int, ...]]:
        for size in sorted(self.sizes):
            if size <= n:
                yield () if size == n else (n - size,)

    def __str__(self) -> str:
        return "Subtraction(" + ",".join(str(s) for s in sorted(self.sizes)) + ")"


def subtraction(sizes: Iterable[int]) -> Subtraction:
    """A subtraction game. Every size must be a positive integer."""
    frozen = frozenset(sizes)
    if not frozen or any(s <= 0 for s in frozen):
        raise ValueError("subtraction sizes must be positive and non-empty")
    return Subtraction(frozen)


@dataclass(frozen=True, slots=True)
class GrundysGame:
    """Grundy's Game: split one heap into two heaps of **different** sizes.

    Not an octal game -- nothing is ever removed, and the split is constrained --
    which is why it is worth having alongside them.

    >>> from pycgt.impartial import nim_value
    >>> [nim_value(heap(GRUNDYS_GAME, n)) for n in range(10)]
    [0, 0, 0, 1, 0, 2, 1, 0, 2, 1]
    """

    def heap_options(self, n: int) -> Iterable[tuple[int, ...]]:
        for part in range(1, (n + 1) // 2):
            yield (part, n - part)

    def __str__(self) -> str:
        return "GrundysGame"


#: Kayles: knock down one or two adjacent pins from a row, splitting it.
KAYLES = octal("0.77")

#: Dawson's Chess, as the octal game ``0.137``.
DAWSONS_CHESS = octal("0.137")

#: Treblecross, as the octal game ``0.007``.
TREBLECROSS = octal("0.007")

#: Officers, as the octal game ``0.6``.
OFFICERS = octal("0.6")

#: Grundy's Game: split a heap into two unequal heaps.
GRUNDYS_GAME = GrundysGame()


@cache
def heap(ruleset: HeapRuleset, n: int) -> Impartial:
    """A single heap of ``n`` tokens under ``ruleset``, as a raw game tree."""
    if n < 0:
        raise ValueError("a heap cannot have negative size")
    options = []
    for parts in ruleset.heap_options(n):
        total = ENDGAME
        for part in parts:
            total = add(total, heap(ruleset, part))
        options.append(total)
    return impartial(options)


def heaps(ruleset: HeapRuleset, *sizes: int) -> Impartial:
    """A sum of heaps under ``ruleset``.

    >>> from pycgt.impartial import misere_outcome
    >>> misere_outcome(heaps(KAYLES, 3, 3))
    <Outcome.SECOND: 'second player'>
    """
    total = ENDGAME
    for size in sizes:
        total = add(total, heap(ruleset, size))
    return total


def nim_values(ruleset: HeapRuleset, upto: int) -> tuple[int, ...]:
    """Nim values of heaps ``0`` through ``upto - 1``.

    Computed by the classical recurrence on integers, never building a game
    tree: Sprague--Grundy says a sum's nim value is the exclusive-or of its
    parts', so a move's value follows from the table so far. That makes this
    linear in the number of moves, where going through
    :func:`~pycgt.impartial.nim_value` on a raw tree is exponential. The tests
    check the two against each other wherever both are affordable.

    Note this shortcut is available only for **normal** play. Misère nim values
    are not additive, so :func:`misere_nim_values` has to build the trees.

    >>> nim_values(DAWSONS_CHESS, 14)
    (0, 1, 1, 2, 0, 3, 1, 1, 0, 3, 3, 2, 2, 4)
    >>> nim_values(KAYLES, 12)
    (0, 1, 2, 3, 1, 4, 3, 2, 1, 4, 2, 6)
    """
    if upto < 0:
        raise ValueError("`upto` must not be negative")
    table: list[int] = []
    for n in range(upto):
        reachable = set()
        for parts in ruleset.heap_options(n):
            total = 0
            for part in parts:
                total ^= table[part]
            reachable.add(total)
        m = 0
        while m in reachable:
            m += 1
        table.append(m)
    return tuple(table)


def misere_nim_values(ruleset: HeapRuleset, upto: int) -> tuple[int, ...]:
    """Misère nim values of heaps ``0`` through ``upto - 1``.

    >>> misere_nim_values(KAYLES, 10)
    (1, 0, 2, 3, 0, 1, 3, 2, 1, 0)
    """
    from ..impartial import misere_nim_value

    return tuple(misere_nim_value(heap(ruleset, n)) for n in range(upto))
