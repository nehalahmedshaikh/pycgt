"""Col and Snort: partizan colouring games on a graph.

Both are played by colouring an uncoloured vertex with your own colour. They
differ in one word:

* **Col** forbids colouring a vertex adjacent to your **own** colour.
* **Snort** forbids colouring a vertex adjacent to your **opponent's** colour.

That single change alters everything. Col is a "cold" game whose values are
numbers or numbers plus star; Snort is hot, and its values on paths run
``*``, ``+-1``, ``+-2``, ``+-{2|1}``, ``+-{1,{3|0}}``.

This is the library's fourth board shape, after grids of empty cells, grids of
coloured stones, and directed strips: an arbitrary graph.

>>> from pycgt.notation import render
>>> render(value(uncoloured(Graph.path(2)), SNORT))
'+-1'
>>> render(value(uncoloured(Graph.path(2)), COL))
'0'
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from ..game import ZERO, Game, add, canonical

__all__ = ["COL", "SNORT", "Colouring", "Graph", "Rule", "uncoloured", "value"]

Vertex = int
Edge = frozenset[Vertex]

LEFT = "Left"
RIGHT = "Right"


@dataclass(frozen=True, slots=True)
class Graph:
    """An undirected simple graph on integer vertices."""

    vertices: frozenset[Vertex]
    edges: frozenset[Edge]

    def __post_init__(self) -> None:
        for edge in self.edges:
            if len(edge) != 2:
                raise ValueError(f"an edge joins two distinct vertices: {set(edge)}")
            if not edge <= self.vertices:
                raise ValueError(f"edge {set(edge)} uses an unknown vertex")

    # -- constructors ----------------------------------------------------

    @staticmethod
    def of(vertices: int, edges: list[tuple[Vertex, Vertex]]) -> Graph:
        return Graph(
            frozenset(range(vertices)),
            frozenset(frozenset(e) for e in edges),
        )

    @staticmethod
    def path(order: int) -> Graph:
        """``order`` vertices in a line, so ``order - 1`` edges."""
        return Graph.of(order, [(i, i + 1) for i in range(order - 1)])

    @staticmethod
    def cycle(order: int) -> Graph:
        if order < 3:
            raise ValueError("a cycle needs at least three vertices")
        return Graph.of(order, [(i, (i + 1) % order) for i in range(order)])

    @staticmethod
    def complete(order: int) -> Graph:
        return Graph.of(
            order, [(i, j) for i in range(order) for j in range(i + 1, order)]
        )

    @staticmethod
    def star(leaves: int) -> Graph:
        """One centre joined to ``leaves`` others."""
        return Graph.of(leaves + 1, [(0, i + 1) for i in range(leaves)])

    # -- queries ---------------------------------------------------------

    @cache  # noqa: B019 - Graph is frozen, so caching per-instance is sound
    def neighbours(self, vertex: Vertex) -> frozenset[Vertex]:
        return frozenset(
            other for edge in self.edges if vertex in edge for other in edge - {vertex}
        )

    @property
    def order(self) -> int:
        return len(self.vertices)

    def components(self) -> list[Graph]:
        remaining = set(self.vertices)
        out: list[Graph] = []
        while remaining:
            stack = [remaining.pop()]
            group = set(stack)
            while stack:
                current = stack.pop()
                for other in self.neighbours(current):
                    if other in remaining:
                        remaining.remove(other)
                        group.add(other)
                        stack.append(other)
            out.append(
                Graph(
                    frozenset(group),
                    frozenset(e for e in self.edges if e <= group),
                )
            )
        return out


@dataclass(frozen=True, slots=True)
class Rule:
    """Which neighbours block a move.

    ``blocked_by_own`` gives Col; ``blocked_by_opponent`` gives Snort.
    """

    name: str
    blocked_by_own: bool
    blocked_by_opponent: bool


#: Col: you may not colour next to your own colour.
COL = Rule(name="Col", blocked_by_own=True, blocked_by_opponent=False)

#: Snort: you may not colour next to your opponent's colour.
SNORT = Rule(name="Snort", blocked_by_own=False, blocked_by_opponent=True)


@dataclass(frozen=True, slots=True)
class Colouring:
    """A graph together with the vertices each player has claimed."""

    graph: Graph
    left: frozenset[Vertex] = frozenset()
    right: frozenset[Vertex] = frozenset()

    def __post_init__(self) -> None:
        if self.left & self.right:
            raise ValueError("a vertex cannot carry both colours")
        if not (self.left | self.right) <= self.graph.vertices:
            raise ValueError("a coloured vertex is not in the graph")

    @property
    def uncoloured(self) -> frozenset[Vertex]:
        return self.graph.vertices - self.left - self.right

    def can_colour(self, vertex: Vertex, player: str, rule: Rule) -> bool:
        if vertex not in self.uncoloured:
            return False
        mine, theirs = (
            (self.left, self.right) if player == LEFT else (self.right, self.left)
        )
        neighbours = self.graph.neighbours(vertex)
        if rule.blocked_by_own and neighbours & mine:
            return False
        return not (rule.blocked_by_opponent and neighbours & theirs)

    def colour(self, vertex: Vertex, player: str) -> Colouring:
        if player == LEFT:
            return Colouring(self.graph, self.left | {vertex}, self.right)
        return Colouring(self.graph, self.left, self.right | {vertex})

    def moves(self, player: str, rule: Rule) -> list[Colouring]:
        return [
            self.colour(vertex, player)
            for vertex in sorted(self.uncoloured)
            if self.can_colour(vertex, player, rule)
        ]

    def __str__(self) -> str:
        marks = []
        for vertex in sorted(self.graph.vertices):
            mark = "L" if vertex in self.left else "R" if vertex in self.right else "."
            marks.append(f"{vertex}{mark}")
        return " ".join(marks)


def uncoloured(graph: Graph) -> Colouring:
    """The opening position: nothing claimed."""
    return Colouring(graph)


def value(position: Colouring, rule: Rule) -> Game:
    """The exact canonical value of a colouring position.

    Disjoint components of the graph are valued separately and summed. There is
    no finer decomposition: colouring a vertex constrains its neighbours
    without removing any edge, so a component stays entangled until it is full.
    """
    components = position.graph.components()
    if len(components) > 1:
        total = ZERO
        for component in components:
            total = add(
                total,
                _value(
                    Colouring(
                        component,
                        position.left & component.vertices,
                        position.right & component.vertices,
                    ),
                    rule,
                ),
            )
        return total
    return _value(position, rule)


@cache
def _value(position: Colouring, rule: Rule) -> Game:
    left = frozenset(_value(after, rule) for after in position.moves(LEFT, rule))
    right = frozenset(_value(after, rule) for after in position.moves(RIGHT, rule))
    return canonical(Game(left, right))
