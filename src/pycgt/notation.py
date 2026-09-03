"""Rendering games as text, and parsing them back.

A value this module cannot name is printed in brace notation rather than
guessed at. That is deliberate: an unfamiliar value is worth looking at, and a
renderer that quietly approximates would hide exactly the interesting cases.

Names follow CGSuite's conventions so that output can be compared directly:
``*``, ``*2``; ``^``, ``^^``, ``^3``, ``^4``; the same with a trailing ``*``;
``v`` for downs; ``Tiny(x)`` and ``Miny(x)``; ``+-x`` for switches; and a
number written straight onto an infinitesimal, as in ``1*`` or ``1Tiny(2)``.

Everything :func:`render` produces, :func:`parse` accepts.
"""

from __future__ import annotations

import re
from fractions import Fraction
from functools import cache

from .game import Game, add, canonical, game, negate
from .stops import number_part
from .values import (
    STAR,
    as_miny,
    as_nimber,
    as_number,
    as_tiny,
    as_up_multiple,
    miny,
    nimber,
    number,
    tiny,
    up_multiple,
)

__all__ = ["parse", "render"]


def _format(x: Fraction) -> str:
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


def _star_name(n: int) -> str:
    return "0" if n == 0 else "*" if n == 1 else f"*{n}"


def _up_name(count: int, star: bool) -> str:
    """CGSuite's spelling: one and two are repeated, three and up are counted."""
    letter = "^" if count > 0 else "v"
    size = abs(count)
    body = letter * size if size <= 2 else f"{letter}{size}"
    return body + ("*" if star else "")


@cache
def render(g: Game) -> str:
    """Readable notation for ``g``.

    Recognises numbers, nimbers, multiples of up and down, tinies and minies,
    switches, and a number plus any of those; anything else falls back to
    nested brace notation.

    >>> from pycgt.values import number, plus_minus, up_multiple
    >>> render(number("1/2"))
    '1/2'
    >>> render(plus_minus(1))
    '+-1'
    >>> render(up_multiple(3))
    '^3'
    """
    c = canonical(g)

    value = as_number(c)
    if value is not None:
        return _format(value)

    # Nimbers must come before the switch rule at the end, because every
    # nimber is its own negative and so matches that rule's pattern.
    star = as_nimber(c)
    if star is not None:
        return _star_name(star)

    # Multiples of up must come before tiny/miny: three ups *is* tiny-down, and
    # `^3` is the name for it that anyone would expect.
    ups = as_up_multiple(c)
    if ups is not None and ups[0] != 0:
        return _up_name(*ups)

    argument = as_tiny(c)
    if argument is not None:
        return f"Tiny({render(argument)})"
    argument = as_miny(c)
    if argument is not None:
        return f"Miny({render(argument)})"

    # A number written straight onto an infinitesimal: "1*", "1^^", "1Tiny(2)".
    # Only when the infinitesimal part has a name of its own -- gluing a number
    # onto a brace expression would be unreadable and would not parse back.
    part = number_part(c)
    if part is not None and part != 0:
        rest = render(canonical(add(c, negate(number(part)))))
        if "{" not in rest and rest != "0":
            return f"{_format(part)}{rest}"

    # A switch +-X, where Right's options are exactly the negatives of Left's.
    # This covers +-1 and also cases whose arguments are not numbers, such as
    # +-{*,^}, which is how Clobber's four-stone row prints.
    if c.left and c.right == frozenset(canonical(negate(x)) for x in c.left):
        inner = ",".join(sorted(render(x) for x in c.left))
        if len(c.left) > 1:
            return f"+-{{{inner}}}"
        # Parenthesise only where the text would otherwise run together, which
        # is CGSuite's rule: `+-1*` reads as the switch `+-1` plus a star when
        # `+-(1*)`, the switch between `1*` and `-1*`, is meant. A number needs
        # no help, and a brace expression already delimits itself, so
        # `+-{2|1}` stays as it is.
        if as_number(next(iter(c.left))) is not None or inner.startswith("{"):
            return f"+-{inner}"
        return f"+-({inner})"

    # An asymmetric switch between two numbers.
    if len(c.left) == 1 and len(c.right) == 1:
        (l,), (r,) = tuple(c.left), tuple(c.right)
        a, b = as_number(l), as_number(r)
        if a is not None and b is not None and a > b:
            return f"{{{_format(a)}|{_format(b)}}}"

    # Spacing follows CGSuite's convention, so output can be compared directly.
    left = ",".join(sorted(render(x) for x in c.left))
    right = ",".join(sorted(render(x) for x in c.right))
    return f"{{{left}|{right}}}"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _bar_runs(text: str) -> list[tuple[int, int]]:
    """Every run of ``|`` outside braces, as ``(start, length)``."""
    runs: list[tuple[int, int]] = []
    depth = index = 0
    while index < len(text):
        ch = text[index]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif ch == "|" and depth == 0:
            start = index
            while index < len(text) and text[index] == "|":
                index += 1
            runs.append((start, index - start))
            continue
        index += 1
    return runs


def _split_top_level(text: str) -> tuple[str, str]:
    """Split the inside of a brace expression into its Left and Right halves.

    Handles the multi-bar convention, in which the *longest* run of bars is the
    outermost separator, so ``{A || B | C}`` means ``{A | {B | C}}``. This is
    how *Winning Ways* and CGSuite both write nested games, and being able to
    read it is what lets CGSuite's own output be fed straight back in.
    """
    runs = _bar_runs(text)
    if not runs:
        raise ValueError(f"no top-level '|' in {text!r}")
    widest = max(length for _, length in runs)
    outermost = [start for start, length in runs if length == widest]
    if len(outermost) != 1:
        raise ValueError(
            f"ambiguous separator in {text!r}: {len(outermost)} runs of "
            f"{widest} bars at the top level"
        )
    cut = outermost[0]
    left, right = text[:cut], text[cut + widest :]
    # A half that still holds bars is itself a game, written without braces
    # because the wider run already separated it.
    if widest > 1:
        left = f"{{{left}}}" if _bar_runs(left) else left
        right = f"{{{right}}}" if _bar_runs(right) else right
    return left, right


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


#: A leading dyadic rational, greedy so that "1/2" is one number rather than
#: the number 1 followed by nonsense.
_LEADING_NUMBER = re.compile(r"(-?\d+(?:/\d+)?)(.*)$", re.DOTALL)

#: Multiples of up or down: "^", "^^", "^3", "v4", each optionally plus a star.
#: The counted form is tried first so that "^3" is not read as "^" then "3".
_UPS = re.compile(r"(\^\d+|\^+|v\d+|v+)(\*?)$")

_TINY = re.compile(r"(Tiny|Miny)\((.*)\)$", re.DOTALL)


def parse(text: str) -> Game:
    """Parse brace notation, numbers, and the named values.

    Accepts everything :func:`render` produces: ``0``, ``3/4``, ``-2``, ``*``,
    ``*3``, ``^``, ``^^``, ``^3``, ``^3*``, ``v4``, ``Tiny(2)``, ``Miny(2)``,
    ``+-1``, a number glued onto an infinitesimal such as ``1*`` or
    ``1Tiny(2)``, and brace expressions such as ``{1|-1}`` or ``{{2|0}|0}``.
    Options may be comma-separated: ``{0,*|1}``.

    >>> parse("{1|-1}") == parse("+-1")
    True
    >>> render(parse("{{2|0}|0}"))
    'Miny(2)'
    >>> render(parse("^3*"))
    '^3*'
    >>> render(parse("1Tiny(2)"))
    '1Tiny(2)'
    """
    text = text.strip()
    if not text:
        raise ValueError("empty game expression")

    if text.startswith("{") and text.endswith("}"):
        left_text, right_text = _split_top_level(text[1:-1])
        return game(_parse_options(left_text), _parse_options(right_text))

    if text.startswith("+-"):
        argument = text[2:].strip()
        if argument.startswith("{") and argument.endswith("}"):
            options = _parse_options(argument[1:-1])
        elif argument.startswith("(") and argument.endswith(")"):
            options = [parse(argument[1:-1])]
        else:
            options = [parse(argument)]
        return game(options, [negate(o) for o in options])

    found = _TINY.fullmatch(text)
    if found is not None:
        inner = parse(found.group(2))
        return tiny(inner) if found.group(1) == "Tiny" else miny(inner)

    found = _UPS.fullmatch(text)
    if found is not None:
        run, star = found.group(1), found.group(2)
        size = int(run[1:]) if run[1:].isdigit() else len(run)
        count = size if run[0] == "^" else -size
        total = up_multiple(count)
        return canonical(add(total, STAR)) if star else total

    if text == "*":
        return STAR
    if text.startswith("*") and text[1:].isdigit():
        return nimber(int(text[1:]))

    # A number glued onto an infinitesimal, e.g. "1*" or "-1/2Tiny(1)". Bare
    # numbers fall through to the final line, since the remainder is empty.
    found = _LEADING_NUMBER.fullmatch(text)
    if found is not None and found.group(2):
        return canonical(add(number(Fraction(found.group(1))), parse(found.group(2))))

    return number(Fraction(text))
