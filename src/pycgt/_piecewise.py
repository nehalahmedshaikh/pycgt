"""Exact piecewise-linear functions on ``[0, inf)``.

Internal support for :mod:`pycgt.thermal`. A thermograph boundary is a
piecewise-linear function of the cooling temperature, so computing
temperatures exactly means doing exact arithmetic on such functions: pointwise
maxima and minima, shifts by ``+-t``, and analytic intersections.

Breakpoints, values and slopes are all :class:`~fractions.Fraction`, so nothing
here is approximate. Every operation preserves that.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from fractions import Fraction

__all__ = ["PiecewiseLinear"]

#: ``(start, value_at_start, slope_after_start)``. The final segment runs to
#: infinity; the first must start at 0.
Segment = tuple[Fraction, Fraction, Fraction]


@dataclass(frozen=True, slots=True)
class PiecewiseLinear:
    """A continuous piecewise-linear function defined for ``t >= 0``."""

    segments: tuple[Segment, ...]

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError("a piecewise-linear function needs a segment")
        if self.segments[0][0] != 0:
            raise ValueError("the first segment must start at t = 0")

    # -- construction ----------------------------------------------------

    @staticmethod
    def constant(value: Fraction) -> PiecewiseLinear:
        return PiecewiseLinear(((Fraction(0), Fraction(value), Fraction(0)),))

    # -- evaluation ------------------------------------------------------

    def _segment_at(self, t: Fraction) -> Segment:
        chosen = self.segments[0]
        for segment in self.segments:
            if segment[0] <= t:
                chosen = segment
            else:
                break
        return chosen

    def __call__(self, t: Fraction) -> Fraction:
        start, value, slope = self._segment_at(t)
        return value + slope * (t - start)

    def slope_at(self, t: Fraction) -> Fraction:
        """The slope just after ``t``."""
        return self._segment_at(t)[2]

    @property
    def breakpoints(self) -> tuple[Fraction, ...]:
        return tuple(s[0] for s in self.segments)

    @property
    def final_value(self) -> Fraction:
        return self.segments[-1][1]

    # -- shifts ----------------------------------------------------------

    def minus_t(self) -> PiecewiseLinear:
        """``f(t) - t``."""
        return PiecewiseLinear(
            tuple(
                (start, value - start, slope - 1)
                for start, value, slope in self.segments
            )
        )

    def plus_t(self) -> PiecewiseLinear:
        """``f(t) + t``."""
        return PiecewiseLinear(
            tuple(
                (start, value + start, slope + 1)
                for start, value, slope in self.segments
            )
        )

    def negated(self) -> PiecewiseLinear:
        return PiecewiseLinear(
            tuple((start, -value, -slope) for start, value, slope in self.segments)
        )

    # -- combination -----------------------------------------------------

    def _crossings_with(self, other: PiecewiseLinear) -> list[Fraction]:
        """Where the two functions cross, as extra breakpoints."""
        points = sorted(set(self.breakpoints) | set(other.breakpoints))
        found: list[Fraction] = []
        for i, a in enumerate(points):
            b = points[i + 1] if i + 1 < len(points) else None
            fa, fs = self(a), self.slope_at(a)
            ga, gs = other(a), other.slope_at(a)
            if fs == gs:
                continue
            t = a + (ga - fa) / (fs - gs)
            if t > a and (b is None or t < b):
                found.append(t)
        return found

    def _combine(
        self, other: PiecewiseLinear, choose: Callable[[Fraction, Fraction], Fraction]
    ) -> PiecewiseLinear:
        points = sorted(
            set(self.breakpoints)
            | set(other.breakpoints)
            | set(self._crossings_with(other))
        )
        segments: list[Segment] = []
        for i, a in enumerate(points):
            b = points[i + 1] if i + 1 < len(points) else None
            # Decide which function wins on the open interval by probing
            # inside it, which sidesteps ties at the endpoints.
            probe = (a + b) / 2 if b is not None else a + 1
            winner = self if choose(self(probe), other(probe)) == self(probe) else other
            segments.append((a, winner(a), winner.slope_at(a)))
        return PiecewiseLinear(_simplify(tuple(segments)))

    def maximum(self, other: PiecewiseLinear) -> PiecewiseLinear:
        return self._combine(other, max)

    def minimum(self, other: PiecewiseLinear) -> PiecewiseLinear:
        return self._combine(other, min)

    def minus(self, other: PiecewiseLinear) -> PiecewiseLinear:
        """``self - other``, exactly."""
        points = sorted(set(self.breakpoints) | set(other.breakpoints))
        segments = tuple(
            (a, self(a) - other(a), self.slope_at(a) - other.slope_at(a))
            for a in points
        )
        return PiecewiseLinear(_simplify(segments))

    @staticmethod
    def max_of(functions: Iterable[PiecewiseLinear]) -> PiecewiseLinear:
        result: PiecewiseLinear | None = None
        for f in functions:
            result = f if result is None else result.maximum(f)
        if result is None:
            raise ValueError("max_of needs at least one function")
        return result

    @staticmethod
    def min_of(functions: Iterable[PiecewiseLinear]) -> PiecewiseLinear:
        result: PiecewiseLinear | None = None
        for f in functions:
            result = f if result is None else result.minimum(f)
        if result is None:
            raise ValueError("min_of needs at least one function")
        return result

    # -- freezing --------------------------------------------------------

    def frozen_from(self, tau: Fraction, value: Fraction) -> PiecewiseLinear:
        """Follow ``self`` below ``tau``, then hold ``value`` forever.

        This is what forms the mast of a thermograph.
        """
        kept = [s for s in self.segments if s[0] < tau]
        if not kept:
            return PiecewiseLinear(((Fraction(0), value, Fraction(0)),))
        return PiecewiseLinear(_simplify((*kept, (tau, value, Fraction(0)))))

    def first_at_or_below(self, other: PiecewiseLinear) -> Fraction:
        """The least ``t >= 0`` with ``self(t) <= other(t)``.

        Used to find where a thermograph's two boundaries meet, which is the
        temperature.
        """
        difference = self.minus(other)
        for i, (start, value, slope) in enumerate(difference.segments):
            if value <= 0:
                return start
            end = (
                difference.segments[i + 1][0]
                if i + 1 < len(difference.segments)
                else None
            )
            if slope < 0:
                crossing = start + value / -slope
                if end is None or crossing <= end:
                    return crossing
        raise ArithmeticError("boundaries never meet; not a short game?")


def _simplify(segments: tuple[Segment, ...]) -> tuple[Segment, ...]:
    """Drop breakpoints that do not actually break anything."""
    out: list[Segment] = []
    for segment in segments:
        if out:
            prev_start, prev_value, prev_slope = out[-1]
            start, value, slope = segment
            continuous = prev_value + prev_slope * (start - prev_start) == value
            if prev_slope == slope and continuous:
                continue
        out.append(segment)
    return tuple(out)
