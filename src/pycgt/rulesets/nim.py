"""Nim, and Blue-Red Hackenbush strings: the two textbook sanity checks.

Nim exists here because its answer is known in closed form -- the value of a
position is the exclusive-or of its heap sizes -- which makes it a strong test
of :func:`~pycgt.game.add` and :func:`~pycgt.values.nimber`.

>>> from pycgt.values import nimber
>>> heaps(3, 5, 6) == nimber(3 ^ 5 ^ 6)
True
>>> heaps(1, 2, 3).is_zero
True
"""

from __future__ import annotations

from functools import reduce

from ..game import ZERO, Game, add, game

__all__ = ["hackenbush_string", "heap", "heaps"]


def heap(size: int) -> Game:
    """One Nim heap, computed from the rules rather than assumed to be a nimber."""
    if size < 0:
        raise ValueError("a heap cannot have negative size")
    if size == 0:
        return ZERO
    options = [heap(k) for k in range(size)]
    return game(options, options)


def heaps(*sizes: int) -> Game:
    """A sum of Nim heaps."""
    return reduce(add, (heap(s) for s in sizes), ZERO)


def hackenbush_string(colours: str) -> Game:
    """A Blue-Red Hackenbush string, read from the ground up.

    ``L`` is a Left (blue) edge, ``R`` a Right (red) edge. Cutting an edge
    removes it and everything above it, so the value is a dyadic rational.

    >>> from pycgt.notation import render
    >>> render(hackenbush_string("L"))
    '1'
    >>> render(hackenbush_string("LR"))
    '1/2'
    """
    for ch in colours:
        if ch not in "LR":
            raise ValueError(f"expected only 'L' and 'R', found {ch!r}")

    def build(rest: str) -> Game:
        if not rest:
            return ZERO
        # Cutting the i-th edge leaves the first i edges.
        left_options = [build(rest[:i]) for i, ch in enumerate(rest) if ch == "L"]
        right_options = [build(rest[:i]) for i, ch in enumerate(rest) if ch == "R"]
        return game(left_options, right_options)

    return build(colours)
