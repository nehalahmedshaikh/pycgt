"""Rendering games as text, and parsing them back.

A value this module cannot name is printed in brace notation rather than
guessed at. That is deliberate: an unfamiliar value is worth looking at, and a
renderer that quietly approximates would hide exactly the interesting cases.
"""

from __future__ import annotations

from fractions import Fraction
from functools import cache

from .game import ZERO, Game, add, canonical, game, negate
from .values import DOWN, STAR, UP, as_number, nimber, number, tiny

__all__ = ["parse", "render"]


def _format(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


@cache
def _named() -> dict[Game, str]:
    """Small library of values with conventional names."""
    table: dict[Game, str] = {}
    for n in range(6):
        name = "0" if n == 0 else "*" if n == 1 else f"*{n}"
        table[canonical(nimber(n))] = name
    table[canonical(UP)] = "^"
    table[canonical(DOWN)] = "v"
    table[canonical(add(UP, STAR))] = "^*"
    table[canonical(add(DOWN, STAR))] = "v*"
    table[canonical(add(UP, UP))] = "^^"
    table[canonical(add(DOWN, DOWN))] = "vv"
    return table


def _as_tiny(g: Game) -> Game | None:
    """If ``g`` is ``tiny-X``, return ``X``; else None."""
    if len(g.left) != 1 or len(g.right) != 1:
        return None
    if next(iter(g.left)) != ZERO:
        return None
    inner = next(iter(g.right))
    if len(inner.left) != 1 or len(inner.right) != 1:
        return None
    if next(iter(inner.left)) != ZERO:
        return None
    candidate = canonical(negate(next(iter(inner.right))))
    return candidate if g == canonical(tiny(candidate)) else None


def _as_miny(g: Game) -> Game | None:
    inner = _as_tiny(canonical(negate(g)))
    return inner


@cache
def render(g: Game) -> str:
    """Readable notation for ``g``.

    Recognises numbers, small nimbers, ups and downs, tinies and minies,
    switches, and a number plus any of those; anything else falls back to
    nested brace notation.

    >>> from pycgt.values import number, plus_minus
    >>> render(number("1/2"))
    '1/2'
    >>> render(plus_minus(1))
    '+-1'
    """
    c = canonical(g)

    value = as_number(c)
    if value is not None:
        return _format(value)

    names = _named()
    if c in names:
        return names[c]

    # tiny / miny, whose arguments are often themselves interesting
    argument = _as_tiny(c)
    if argument is not None:
        return f"Tiny({render(argument)})"
    argument = _as_miny(c)
    if argument is not None:
        return f"Miny({render(argument)})"

    # a number plus a named infinitesimal, e.g. "1*" or "1/2^"
    for named_game, name in names.items():
        if named_game == ZERO:
            continue
        rest = as_number(canonical(c - named_game))
        if rest is not None:
            return f"{_format(rest)}{name}"

    # a switch: one option each side, both numbers, Left's above Right's
    if len(c.left) == 1 and len(c.right) == 1:
        (l,), (r,) = tuple(c.left), tuple(c.right)
        a, b = as_number(l), as_number(r)
        if a is not None and b is not None and a > b:
            if a == -b:
                return f"+-{_format(a)}"
            return f"{{{_format(a)}|{_format(b)}}}"

    # Spacing follows CGSuite's convention, so output can be compared directly.
    left = ",".join(sorted(render(x) for x in c.left))
    right = ",".join(sorted(render(x) for x in c.right))
    return f"{{{left}|{right}}}"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _split_top_level(text: str) -> tuple[str, str]:
    """Split ``a|b`` on the bar outside any braces."""
    depth = 0
    for i, ch in enumerate(text):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == "|" and depth == 0:
            return text[:i], text[i + 1 :]
    raise ValueError(f"no top-level '|' in {text!r}")


def _parse_options(text: str) -> list[Game]:
    text = text.strip()
    if not text:
        return []
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(text):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return [parse(p) for p in parts]


def parse(text: str) -> Game:
    """Parse brace notation, numbers, and the common named values.

    Accepts ``0``, ``3/4``, ``-2``, ``*``, ``*3``, ``^``, ``v``, ``+-1``, and
    brace expressions such as ``{1|-1}`` or ``{{2|0}|0}``. Options may be
    comma-separated: ``{0,*|1}``.

    >>> parse("{1|-1}") == parse("+-1")
    True
    >>> render(parse("{{2|0}|0}"))
    'Miny(2)'
    >>> render(parse("{0|{0|-2}}"))
    'Tiny(2)'
    """
    text = text.strip()
    if not text:
        raise ValueError("empty game expression")

    if text.startswith("{") and text.endswith("}"):
        left_text, right_text = _split_top_level(text[1:-1])
        return game(_parse_options(left_text), _parse_options(right_text))

    if text.startswith("+-"):
        from .values import plus_minus

        return plus_minus(text[2:].strip())

    if text == "*":
        return STAR
    if text.startswith("*"):
        return nimber(int(text[1:]))
    if text == "^":
        return UP
    if text == "v":
        return DOWN

    return number(Fraction(text))
