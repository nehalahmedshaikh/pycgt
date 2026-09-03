"""Clobber: pieces capture instead of being placed.

Left owns the ``x`` stones and Right the ``o`` stones. A move takes one of your
stones onto an orthogonally adjacent enemy stone, removing it. A player with no
adjacent enemy loses.

Architecturally this is the library's first non-placement ruleset. Placement
games only ever fill cells, so :mod:`pycgt.rulesets.grid` can treat a position
as a set of empty cells; here stones move and change the occupied set in both
directions, so the state is a colouring rather than a set.

Clobber is **all-small**: a move exists for Left exactly when some ``x`` is
adjacent to some ``o``, which is the same condition as for Right. So every
value is an infinitesimal, which makes it the natural home for atomic weight.

>>> from pycgt.notation import render
>>> render(parse("xo"))
'*'
>>> render(parse("xo|ox"))
'*'
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from ..game import ZERO, Game, add, canonical
from .grid import Cell

__all__ = ["Board", "parse", "row", "value"]

LEFT_STONE = "x"
RIGHT_STONE = "o"
EMPTY = "."


def _transform(cell: Cell, flip_r: bool, flip_c: bool, swap: bool) -> Cell:
    """One of the eight symmetries of the square, applied to a cell."""
    r, c = cell
    if flip_r:
        r = -r
    if flip_c:
        c = -c
    return (c, r) if swap else (r, c)


def _corner(cells: list[Cell]) -> Cell:
    """Top-left corner of the bounding box, used to translate to the origin."""
    return min(r for r, _ in cells), min(c for _, c in cells)


def _shift(cells: list[Cell], origin: Cell) -> tuple[Cell, ...]:
    return tuple(sorted((r - origin[0], c - origin[1]) for r, c in cells))


@dataclass(frozen=True, slots=True)
class Board:
    """Which cells hold Left's stones, and which hold Right's."""

    left: frozenset[Cell]
    right: frozenset[Cell]

    def __post_init__(self) -> None:
        if self.left & self.right:
            raise ValueError("a cell cannot hold both players' stones")

    @property
    def occupied(self) -> frozenset[Cell]:
        return self.left | self.right

    @property
    def size(self) -> int:
        return len(self.occupied)

    # -- moves -----------------------------------------------------------

    def moves(self, mover: str) -> list[Board]:
        """Positions after one capture by ``mover``."""
        mine, theirs = (
            (self.left, self.right) if mover == LEFT_STONE else (self.right, self.left)
        )
        out = []
        for r, c in sorted(mine):
            for target in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if target not in theirs:
                    continue
                moved_mine = (mine - {(r, c)}) | {target}
                moved_theirs = theirs - {target}
                out.append(
                    Board(moved_mine, moved_theirs)
                    if mover == LEFT_STONE
                    else Board(moved_theirs, moved_mine)
                )
        return out

    # -- decomposition ---------------------------------------------------

    def components(self) -> list[Board]:
        """Split into groups of stones that cannot reach each other.

        Stones interact only when orthogonally adjacent, and captures never
        create adjacency across a gap, so connected groups are independent.
        """
        remaining = set(self.occupied)
        out: list[Board] = []
        while remaining:
            stack = [remaining.pop()]
            group = set(stack)
            while stack:
                r, c = stack.pop()
                for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if nb in remaining:
                        remaining.remove(nb)
                        group.add(nb)
                        stack.append(nb)
            out.append(Board(self.left & group, self.right & group))
        return sorted(out, key=lambda b: sorted(b.occupied))

    def normalise(self) -> Board:
        """Canonical representative under translation and the eight symmetries.

        Both players move in every direction, so the dihedral symmetries of the
        square leave the value unchanged. Exchanging the *colours* does not --
        that negates -- so colour is preserved here.
        """
        if not self.occupied:
            return self
        best: tuple[tuple[Cell, ...], tuple[Cell, ...]] | None = None
        for flip_r in (False, True):
            for flip_c in (False, True):
                for swap in (False, True):
                    left = [_transform(x, flip_r, flip_c, swap) for x in self.left]
                    right = [_transform(x, flip_r, flip_c, swap) for x in self.right]
                    origin = _corner(left + right)
                    key = (_shift(left, origin), _shift(right, origin))
                    if best is None or key < best:
                        best = key
        assert best is not None
        return Board(frozenset(best[0]), frozenset(best[1]))

    # -- display ---------------------------------------------------------

    def __str__(self) -> str:
        if not self.occupied:
            return "(empty)"
        rows = [r for r, _ in self.occupied]
        cols = [c for _, c in self.occupied]
        lines = []
        for r in range(min(rows), max(rows) + 1):
            line = ""
            for c in range(min(cols), max(cols) + 1):
                if (r, c) in self.left:
                    line += LEFT_STONE
                elif (r, c) in self.right:
                    line += RIGHT_STONE
                else:
                    line += "."
            lines.append(line)
        return "\n".join(lines)


def parse(text: str) -> Game:
    """The value of a board written as rows of ``x``, ``o`` and ``.``.

    Rows may be separated by ``|`` or by newlines, matching CGSuite's notation.

    >>> from pycgt.notation import render
    >>> render(parse("xoxo"))
    '+-{*,^}'
    """
    return value(board(text))


def board(text: str) -> Board:
    """Read a :class:`Board` from rows of ``x``, ``o`` and ``.``."""
    left, right = set(), set()
    rows = text.replace("|", "\n").strip("\n").splitlines()
    for r, line in enumerate(rows):
        for c, ch in enumerate(line.strip()):
            if ch == LEFT_STONE:
                left.add((r, c))
            elif ch == RIGHT_STONE:
                right.add((r, c))
            elif ch != EMPTY:
                raise ValueError(f"expected 'x', 'o' or '.', found {ch!r}")
    return Board(frozenset(left), frozenset(right))


def row(pattern: str) -> Board:
    """A single row, e.g. ``row("xoxo")``."""
    return board(pattern)


def value(position: Board) -> Game:
    """The exact canonical value of a Clobber position."""
    components = position.components()
    if not components:
        return ZERO
    total = _component_value(components[0].normalise())
    for component in components[1:]:
        total = add(total, _component_value(component.normalise()))
    return total


@cache
def _component_value(position: Board) -> Game:
    """Value of one connected group, which must already be normalised."""
    left = frozenset(value(after) for after in position.moves(LEFT_STONE))
    right = frozenset(value(after) for after in position.moves(RIGHT_STONE))
    return canonical(Game(left, right))
