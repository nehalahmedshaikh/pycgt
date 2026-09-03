"""Drawing thermographs, as SVG.

CGSuite plots thermographs in its desktop interface. This does it as data: a
string of SVG with no dependencies, which Jupyter renders inline because the
returned object exposes ``_repr_svg_``.

The boundaries are already exact piecewise-linear functions
(:mod:`pycgt._piecewise`), so the picture is drawn from the real breakpoints
rather than sampled -- the lines are where the mathematics says they are.

Temperature increases **upward** and value increases to the **right**, so
Left's boundary -- the higher stop -- is the one on the right, and the mast is
where the two meet. Each boundary is labelled at its own foot rather than in a
corner, since putting "Left" in the top-left would place it over Right's line.

(Winning Ways draws the value axis increasing leftward. This goes the other
way, which is easier to read alongside ordinary plots; the shape is the same
either way.)

>>> from pycgt import parse
>>> svg = thermograph_svg(parse("{2|-1/2}"))
>>> svg.startswith("<svg")
True
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .game import Game
from .notation import render
from .thermal import Thermograph, thermograph

__all__ = ["Svg", "thermograph_svg"]


@dataclass(frozen=True, slots=True)
class Svg:
    """An SVG document that notebooks render inline."""

    source: str

    def _repr_svg_(self) -> str:
        return self.source

    def __str__(self) -> str:
        return self.source

    def startswith(self, prefix: str) -> bool:
        return self.source.startswith(prefix)

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(self.source)


def _boundary_points(
    graph: Thermograph, side: str, top: Fraction
) -> list[tuple[Fraction, Fraction]]:
    """``(value, temperature)`` pairs tracing one boundary from 0 up to ``top``."""
    line = graph.left if side == "left" else graph.right
    temperatures = [t for t in line.breakpoints if t <= top]
    if not temperatures or temperatures[0] != 0:
        temperatures.insert(0, Fraction(0))
    if temperatures[-1] != top:
        temperatures.append(top)
    return [(line(t), t) for t in temperatures]


def thermograph_svg(
    game: Game,
    width: int = 420,
    height: int = 320,
    margin: int = 46,
) -> Svg:
    """Draw the thermograph of ``game``.

    Temperature runs upward, value runs rightward, and the mast is marked.
    """
    graph = thermograph(game)
    temperature = graph.temperature
    # Numbers are cold (negative temperature); show a little above zero so the
    # picture is not degenerate.
    top = temperature if temperature > 0 else Fraction(1)
    headroom = top + top / 4

    left = _boundary_points(graph, "left", headroom)
    right = _boundary_points(graph, "right", headroom)

    values = [v for v, _ in left + right] + [graph.mast]
    low, high = min(values), max(values)
    if low == high:
        low, high = low - 1, high + 1
    span = high - low

    def x(value: Fraction) -> float:
        return margin + float((value - low) / span) * (width - 2 * margin)

    def y(t: Fraction) -> float:
        return height - margin - float(t / headroom) * (height - 2 * margin)

    def path(points: list[tuple[Fraction, Fraction]]) -> str:
        return " ".join(
            f"{'M' if i == 0 else 'L'}{x(v):.2f},{y(t):.2f}"
            for i, (v, t) in enumerate(points)
        )

    label = render(game)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" font-family="system-ui, sans-serif">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        # axes
        f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" '
        f'y2="{height - margin}" stroke="#999" stroke-width="1"/>',
        f'<line x1="{x(graph.mast):.2f}" y1="{height - margin}" '
        f'x2="{x(graph.mast):.2f}" y2="{margin / 2:.2f}" stroke="#ddd" '
        f'stroke-width="1" stroke-dasharray="3 3"/>',
        # boundaries
        f'<path d="{path(left)}" fill="none" stroke="#1f77b4" stroke-width="2.5"/>',
        f'<path d="{path(right)}" fill="none" stroke="#d62728" stroke-width="2.5"/>',
    ]

    if temperature > 0:
        parts.append(
            f'<circle cx="{x(graph.mast):.2f}" cy="{y(temperature):.2f}" r="3.5" '
            f'fill="#333"/>'
        )

    parts += [
        f'<text x="{width / 2:.0f}" y="{margin / 2 + 4:.0f}" text-anchor="middle" '
        f'font-size="14" fill="#222">{_escape(label)}</text>',
        f'<text x="{margin}" y="{height - margin + 16}" font-size="11" '
        f'fill="#666">value {_escape(str(low))}</text>',
        f'<text x="{width - margin}" y="{height - margin + 16}" '
        f'text-anchor="end" font-size="11" fill="#666">'
        f"{_escape(str(high))}</text>",
        f'<text x="{width / 2:.0f}" y="{height - 8}" text-anchor="middle" '
        f'font-size="11" fill="#666">'
        f"temperature {_escape(str(temperature))}, mean {_escape(str(graph.mast))}"
        f"</text>",
        # Anchor each label to the foot of its own boundary. Left's stop is
        # the higher value, so Left's line sits to the right -- labelling the
        # corners instead would put each name over the other's line.
        f'<text x="{x(left[0][0]):.2f}" y="{height - margin + 32}" '
        f'text-anchor="middle" font-size="11" fill="#1f77b4">Left</text>',
        f'<text x="{x(right[0][0]):.2f}" y="{height - margin + 32}" '
        f'text-anchor="middle" font-size="11" fill="#d62728">Right</text>',
        "</svg>",
    ]
    return Svg("\n".join(parts))


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
