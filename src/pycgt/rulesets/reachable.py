"""Was this position reachable by legal play?

A *placement* game only ever covers empty cells and never moves or removes a
piece, so the cells filled in a position are exactly the shapes played to reach
it, and **those shapes never overlap**. Two consequences make reachability
decidable rather than a search over game trees:

1. Any partition of the filled region into legal shapes can be replayed in
   *any* order -- disjointness means no placement can be blocked by another.
2. Alternating play therefore constrains only the *counts*. A sequence of ``m``
   alternating moves beginning with Left uses ``ceil(m/2)`` of Left's shapes and
   ``floor(m/2)`` of Right's.

So the question "is this position reachable from that rectangle?" becomes
"does the filled region admit a partition into the players' shapes with the
right counts?" -- a constrained exact-cover problem, solved here by covering
the lexicographically-first uncovered cell at each step.

This matters for stating results. Some authors allow any finite region as a
Domineering position; a stricter reading requires the empty cells to be
reachable from a rectangle. A claim about "the maximum temperature in
Domineering" means different things under the two conventions, so a
reachability certificate is part of the claim.

>>> from pycgt.rulesets import domineering
>>> replay = reachable_from_rectangle(
...     Position.parse("..\\n.."), 2, 3, domineering.DOMINEERING)
>>> replay is not None and len(replay.moves)
1
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .grid import Cell, Position, Ruleset, Shape

__all__ = [
    "Move",
    "Replay",
    "partitions",
    "reachable_from_rectangle",
    "verify_replay",
]

LEFT = "Left"
RIGHT = "Right"


@dataclass(frozen=True, slots=True)
class Move:
    """One placement: which player, and which cells it covered."""

    player: str
    cells: tuple[Cell, ...]

    def __str__(self) -> str:
        spots = " ".join(f"({r},{c})" for r, c in sorted(self.cells))
        return f"{self.player}: {spots}"


@dataclass(frozen=True, slots=True)
class Replay:
    """A legal alternating sequence from ``start`` ending at ``target``."""

    start: Position
    moves: tuple[Move, ...]
    target: Position

    @property
    def first_player(self) -> str:
        return self.moves[0].player if self.moves else LEFT

    def counts(self) -> dict[str, int]:
        return {
            LEFT: sum(m.player == LEFT for m in self.moves),
            RIGHT: sum(m.player == RIGHT for m in self.moves),
        }

    def __str__(self) -> str:
        counts = self.counts()
        head = (
            f"{len(self.moves)} moves from {self.start.size} cells "
            f"({counts[LEFT]} Left, {counts[RIGHT]} Right)"
        )
        return "\n".join(
            [head] + [f"  {i + 1:>3}. {m}" for i, m in enumerate(self.moves)]
        )


def _placements_covering(
    region: frozenset[Cell], cell: Cell, shape: Shape
) -> Iterator[frozenset[Cell]]:
    """Every way of laying ``shape`` inside ``region`` so that it covers ``cell``."""
    r, c = cell
    for dr, dc in shape:
        # Anchor the shape so that this offset lands on `cell`.
        origin = (r - dr, c - dc)
        covered = frozenset((origin[0] + odr, origin[1] + odc) for odr, odc in shape)
        if covered <= region and cell in covered:
            yield covered


def partitions(
    region: frozenset[Cell],
    ruleset: Ruleset,
    left_count: int,
    right_count: int,
    limit: int = 1,
) -> list[list[tuple[str, frozenset[Cell]]]]:
    """Partitions of ``region`` into ``left_count`` + ``right_count`` shapes.

    Returns at most ``limit`` solutions, each a list of ``(player, cells)``.
    The search always covers the lexicographically-first uncovered cell, which
    makes it an exact-cover enumeration rather than a blind subset search.
    """
    found: list[list[tuple[str, frozenset[Cell]]]] = []
    shapes = {LEFT: ruleset.left_shapes, RIGHT: ruleset.right_shapes}

    def recurse(
        remaining: frozenset[Cell],
        budget: dict[str, int],
        chosen: list[tuple[str, frozenset[Cell]]],
    ) -> None:
        if len(found) >= limit:
            return
        if not remaining:
            if budget[LEFT] == 0 and budget[RIGHT] == 0:
                found.append(list(chosen))
            return
        if budget[LEFT] < 0 or budget[RIGHT] < 0:
            return

        cell = min(remaining)
        seen: set[tuple[str, frozenset[Cell]]] = set()
        for player in (LEFT, RIGHT):
            if budget[player] == 0:
                continue
            for shape in shapes[player]:
                for covered in _placements_covering(remaining, cell, shape):
                    key = (player, covered)
                    if key in seen:
                        continue
                    seen.add(key)
                    budget[player] -= 1
                    chosen.append((player, covered))
                    recurse(remaining - covered, budget, chosen)
                    chosen.pop()
                    budget[player] += 1
                    if len(found) >= limit:
                        return

    recurse(frozenset(region), {LEFT: left_count, RIGHT: right_count}, [])
    return found


def _interleave(
    pieces: list[tuple[str, frozenset[Cell]]], first: str
) -> tuple[Move, ...] | None:
    """Order the pieces into a strictly alternating sequence starting with ``first``."""
    pools: dict[str, list[frozenset[Cell]]] = {LEFT: [], RIGHT: []}
    for player, cells in pieces:
        pools[player].append(cells)

    order: list[Move] = []
    turn = first
    while pools[LEFT] or pools[RIGHT]:
        if not pools[turn]:
            return None
        order.append(Move(turn, tuple(sorted(pools[turn].pop()))))
        turn = RIGHT if turn == LEFT else LEFT
    return tuple(order)


def reachable_from_rectangle(
    target: Position,
    rows: int,
    cols: int,
    ruleset: Ruleset,
    first: str | None = None,
) -> Replay | None:
    """A legal alternating replay from the empty ``rows`` x ``cols`` board to
    ``target``, or None if there is none.

    ``first`` fixes who moves first; if omitted, both are tried.

    The returned replay is a certificate: :func:`verify_replay` re-checks it
    from scratch without trusting this search.
    """
    board = Position.rectangle(rows, cols)
    if not target.cells <= board.cells:
        return None

    filled = board.cells - target.cells
    sizes = {len(s) for s in ruleset.left_shapes + ruleset.right_shapes}
    if len(sizes) != 1:
        raise NotImplementedError(
            "reachability assumes every shape covers the same number of cells"
        )
    size = sizes.pop()
    if len(filled) % size:
        return None
    moves = len(filled) // size

    for candidate_first in [first] if first else [LEFT, RIGHT]:
        other = RIGHT if candidate_first == LEFT else LEFT
        counts = {candidate_first: (moves + 1) // 2, other: moves // 2}
        for pieces in partitions(filled, ruleset, counts[LEFT], counts[RIGHT], limit=1):
            order = _interleave(pieces, candidate_first)
            if order is not None:
                return Replay(start=board, moves=order, target=target)
    return None


def verify_replay(replay: Replay, ruleset: Ruleset) -> bool:
    """Re-check a replay from scratch: legality, alternation, and endpoint.

    Deliberately independent of :func:`reachable_from_rectangle`, so a
    certificate produced elsewhere -- by another program, or by hand -- can be
    audited here.
    """
    shapes = {LEFT: ruleset.left_shapes, RIGHT: ruleset.right_shapes}
    position = replay.start

    for index, move in enumerate(replay.moves):
        if move.player not in (LEFT, RIGHT):
            return False
        # Alternation.
        if index and move.player == replay.moves[index - 1].player:
            return False
        covered = frozenset(move.cells)
        # The cells must currently be empty.
        if not covered <= position.cells:
            return False
        # And must form one of that player's shapes, up to translation.
        if not _is_shape(covered, shapes[move.player]):
            return False
        position = Position(position.cells - covered)

    return position == replay.target


def _is_shape(cells: frozenset[Cell], shapes: tuple[Shape, ...]) -> bool:
    """Is ``cells`` a translate of one of ``shapes``?"""
    base_r = min(r for r, _ in cells)
    base_c = min(c for _, c in cells)
    normalised = frozenset((r - base_r, c - base_c) for r, c in cells)
    for shape in shapes:
        sr = min(r for r, _ in shape)
        sc = min(c for _, c in shape)
        if normalised == frozenset((r - sr, c - sc) for r, c in shape):
            return True
    return False
