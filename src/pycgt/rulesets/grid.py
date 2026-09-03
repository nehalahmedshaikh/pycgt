"""Placement games on a grid, and exact values for them.

A *placement game* gives each player a set of shapes; a move covers empty cells
with one of your shapes. Domineering and Cram are both of this form, differing
only in which shapes belong to whom, so one engine serves both.

Two things make this reach interesting board sizes:

1. **Decomposition.** A position splits into components that cannot interact,
   and its value is their sum, so the search never faces the whole board.
2. **Normalisation.** Components are memoised up to translation and whichever
   reflections the ruleset declares value-preserving.

Both are standard, and without them nothing past a handful of cells is
reachable.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache

from ..game import ZERO, Game, add, canonical

__all__ = ["Position", "Ruleset", "Shape", "value"]

Cell = tuple[int, int]
#: A shape is a set of cell offsets, e.g. a vertical domino is ((0,0),(1,0)).
Shape = tuple[Cell, ...]


@dataclass(frozen=True, slots=True)
class Position:
    """A set of empty cells. Frozen and hashable, so it can key a memo table."""

    cells: frozenset[Cell]

    @staticmethod
    def rectangle(rows: int, cols: int) -> Position:
        if rows < 0 or cols < 0:
            raise ValueError("dimensions must be non-negative")
        return Position(frozenset((r, c) for r in range(rows) for c in range(cols)))

    @staticmethod
    def parse(text: str) -> Position:
        """Read a position from ASCII art: ``.`` is empty, anything else filled.

        >>> Position.parse("..\\n.#").size
        3
        """
        cells = set()
        for r, line in enumerate(text.strip("\n").splitlines()):
            for c, ch in enumerate(line):
                if ch == ".":
                    cells.add((r, c))
        return Position(frozenset(cells))

    @property
    def size(self) -> int:
        return len(self.cells)

    def placements(self, shape: Shape) -> list[frozenset[Cell]]:
        """Every way of laying ``shape`` on empty cells."""
        out = []
        for r, c in _cells_in_order(self):
            covered = frozenset((r + dr, c + dc) for dr, dc in shape)
            if covered <= self.cells:
                out.append(covered)
        return out

    def remove(self, covered: Iterable[Cell]) -> Position:
        covered = frozenset(covered)
        if not covered <= self.cells:
            raise ValueError("those cells are not all empty")
        return Position(self.cells - covered)

    def components(self) -> list[Position]:
        """Split into orthogonally connected pieces.

        Cells matter to each other only if some shape could cover both; for
        shapes made of orthogonally adjacent cells, that is exactly orthogonal
        connectivity.

        Components come out ordered by their smallest cell. Seeding each search
        with ``min(remaining)`` gets that for free, where sorting afterwards
        cost a sort of every component's cells *per component* to build the
        key -- and gives the identical order, since disjoint components have
        distinct minima and the smallest cell is the first element of the
        sorted list either way.
        """
        remaining = set(self.cells)
        out: list[Position] = []
        while remaining:
            start = min(remaining)
            remaining.discard(start)
            stack = [start]
            group = [start]
            while stack:
                r, c = stack.pop()
                for nb in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                    if nb in remaining:
                        remaining.remove(nb)
                        group.append(nb)
                        stack.append(nb)
            out.append(Position(frozenset(group)))
        return out

    def normalise(self, *, transpose: bool = False) -> Position:
        """A canonical representative under translation and reflection.

        ``transpose`` should be true only for rulesets where swapping rows and
        columns preserves the value. For Domineering it does not -- transposing
        exchanges the players and negates -- so it defaults to false.
        """
        return _normalised(self, transpose)

    def __str__(self) -> str:
        if not self.cells:
            return "(empty)"
        rows = [r for r, _ in self.cells]
        cols = [c for _, c in self.cells]
        return "\n".join(
            "".join(
                "." if (r, c) in self.cells else " "
                for c in range(min(cols), max(cols) + 1)
            )
            for r in range(min(rows), max(rows) + 1)
        )


@cache
def _cells_in_order(position: Position) -> tuple[Cell, ...]:
    """The cells in a fixed order, computed once per position.

    Placement search needs a deterministic order so that replay certificates
    are reproducible, but re-sorting on every call was measurable.
    """
    return tuple(sorted(position.cells))


@cache
def _normalised(position: Position, transpose: bool) -> Position:
    """The canonical representative of ``position`` under its symmetries.

    Reflecting an axis maps its largest coordinate to zero, and not reflecting
    it means subtracting its smallest, so **the translation is known in advance**
    and no pass over the cells is needed to discover it. Computing it per
    variant instead -- two ``min`` calls and a second rebuild of the cell list --
    was the single largest cost in valuing a Domineering board.
    """
    cells = position.cells
    if not cells:
        return position
    lo_r = min(r for r, _ in cells)
    hi_r = max(r for r, _ in cells)
    lo_c = min(c for _, c in cells)
    hi_c = max(c for _, c in cells)
    best: tuple[Cell, ...] | None = None
    for flip_r in (False, True):
        for flip_c in (False, True):
            for swap in (False, True) if transpose else (False,):
                if swap:
                    key = tuple(
                        sorted(
                            (
                                (hi_c - c) if flip_c else (c - lo_c),
                                (hi_r - r) if flip_r else (r - lo_r),
                            )
                            for r, c in cells
                        )
                    )
                else:
                    key = tuple(
                        sorted(
                            (
                                (hi_r - r) if flip_r else (r - lo_r),
                                (hi_c - c) if flip_c else (c - lo_c),
                            )
                            for r, c in cells
                        )
                    )
                if best is None or key < best:
                    best = key
    assert best is not None
    return Position(frozenset(best))


@dataclass(frozen=True, slots=True)
class Ruleset:
    """Which shapes each player may place."""

    name: str
    left_shapes: tuple[Shape, ...]
    right_shapes: tuple[Shape, ...]
    #: True when swapping rows and columns leaves values unchanged, as for
    #: rulesets where both players have the same shapes.
    transpose_invariant: bool = False

    def left_moves(self, position: Position) -> list[frozenset[Cell]]:
        return [m for s in self.left_shapes for m in position.placements(s)]

    def right_moves(self, position: Position) -> list[frozenset[Cell]]:
        return [m for s in self.right_shapes for m in position.placements(s)]


@cache
def value(position: Position, ruleset: Ruleset) -> Game:
    """The exact canonical value of ``position`` under ``ruleset``.

    Memoised on the *raw* position, not just on normalised components. Without
    that, a position reached by several different move orders had its
    decomposition and normalisation redone in full every time, even though the
    component values behind it were already known.
    """
    components = position.components()
    if not components:
        return ZERO
    total = _component_value(
        components[0].normalise(transpose=ruleset.transpose_invariant), ruleset
    )
    for component in components[1:]:
        total = add(
            total,
            _component_value(
                component.normalise(transpose=ruleset.transpose_invariant), ruleset
            ),
        )
    return total


@cache
def _component_value(position: Position, ruleset: Ruleset) -> Game:
    """Value of one connected component, which must already be normalised."""
    left = frozenset(
        value(position.remove(m), ruleset) for m in ruleset.left_moves(position)
    )
    right = frozenset(
        value(position.remove(m), ruleset) for m in ruleset.right_moves(position)
    )
    return canonical(Game(left, right))
