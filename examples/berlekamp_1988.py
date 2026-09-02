"""Berlekamp's 1988 Blockbusting results, reproduced with pycgt.

*Blockbusting and Domineering*, J. Combin. Theory A 49 (1988) 67-116.

This is the library's flagship worked example: a real published result, with
overheating operators and all, rebuilt from the paper and checked against it.
Run it directly:

    python examples/berlekamp_1988.py

What it reproduces
------------------
**Table III** -- the blockbusting sequences x, y, z, defined by

    x_0 = 1;  y_0 = z_0 = 0;  z_1 = z_2 = 0;  z_3 = 1/2
    x_n = {x_(n-1) | y_(n-1) + 1}          for n > 0
    y_n = {y_(n-1) | z_(n-1) + 1}          for n > 0
    z_n = {y_(n-3) - 1/4 | z_(n-3) + 1}    for n > 3

Berlekamp notes they have *period 5 and saltus 1*, and that every value except
x_1 = 1* is a number. Both are checked below.

**Appendix B.1** -- the "tight-ish" lower bound on the value of the Domineering
rectangle two columns wide and 2n rows tall:

    G_n >= n/4 + [n odd] * heat(*, 3/4) - heat(overheat(w_n, 1/2, 1/2*), 3/4)

where w_0 = 0 and w_(n+1) = {w_n | y_n + 1}. He gives *exact* values only for
n <= 3; from n = 4 on, only this bound.
"""

from __future__ import annotations

from fractions import Fraction
from functools import cache

from pycgt import (
    STAR,
    as_number,
    game,
    geq,
    heat,
    multiple,
    number,
    overheat,
    plus_minus,
    render,
    tiny,
)
from pycgt.rulesets import domineering

ONE = number(1)


# --- Table III -------------------------------------------------------------


@cache
def x(n: int):
    if n == 0:
        return ONE
    return game({x(n - 1)}, {y(n - 1) + ONE})


@cache
def y(n: int):
    if n == 0:
        return number(0)
    return game({y(n - 1)}, {z(n - 1) + ONE})


@cache
def z(n: int):
    if n in (0, 1, 2):
        return number(0)
    if n == 3:
        return number("1/2")
    return game({y(n - 3) - number("1/4")}, {z(n - 3) + ONE})


@cache
def w(n: int):
    """From Appendix B.1. Berlekamp records w_1 = 1/2 and w_n = x_n for n > 1."""
    if n == 0:
        return number(0)
    return game({w(n - 1)}, {y(n - 1) + ONE})


# --- Appendix B.1 ----------------------------------------------------------

THREE_QUARTERS = number("3/4")
HALF = number("1/2")


def berlekamp_bound(n: int):
    """The Appendix B.1 lower bound on G_n.

    The ``heat(*, 3/4)`` term appears only for odd n. That is linearity:
    n copies of heat(*, t) is heat(n * *, t), and n * * is 0 for even n. It
    matches his displayed rows, where the column is filled for n = 1, 3 and
    blank for n = 2, 4.
    """
    linear = number(Fraction(n, 4))
    if n % 2 == 1:
        linear = linear + heat(STAR, THREE_QUARTERS)
    correction = heat(overheat(w(n), HALF, HALF + STAR), THREE_QUARTERS)
    return linear - correction


def G(n: int):  # noqa: N802 - matches the paper's notation
    """His G_n: the Domineering board 2 columns wide and 2n rows tall."""
    return domineering.rectangle(2 * n, 2)


def main() -> None:
    print(__doc__.split("What it reproduces")[0].strip())
    print()

    print("Table III")
    print(f"  {'n':>3}  {'x_n':>8}  {'y_n':>8}  {'z_n':>8}  {'w_n':>8}")
    for n in range(12):
        print(
            f"  {n:>3}  {render(x(n)):>8}  {render(y(n)):>8}"
            f"  {render(z(n)):>8}  {render(w(n)):>8}"
        )

    print()
    print("  period 5, saltus 1:", end=" ")
    ok = all(
        as_number(y(n + 5)) == as_number(y(n)) + 1
        and as_number(z(n + 5)) == as_number(z(n)) + 1
        for n in range(3, 15)
    )
    print("holds" if ok else "FAILS")
    print(f"  x_1 is the only non-number: {render(x(1))}")

    print()
    print("Appendix B.1: exact value against the tight-ish bound")
    print(f"  {'n':>3}  {'bound holds?':<13}  {'exact G_n':<28}  bound")
    for n in range(1, 7):
        exact, bound = G(n), berlekamp_bound(n)
        status = (
            "tight" if exact == bound else ("ok" if geq(exact, bound) else "VIOLATED")
        )
        print(f"  {n:>3}  {status:<13}  {render(exact)[:28]:<28}  {render(bound)[:30]}")

    print()
    print("His exact values, for the three n where he gives them")
    checks = [
        ("G_1 = +-1", G(1) == plus_minus(1)),
        ("G_2 = tiny-2", G(2) == tiny(2)),
        ("G_3 = +-1 + 2*tiny-2", G(3) == plus_minus(1) + multiple(tiny(2), 2)),
    ]
    for label, holds in checks:
        print(f"  {'ok  ' if holds else 'FAIL'}  {label}")

    print()
    print("From n = 4 on he gives no exact value. Ours:")
    for n in (4, 5, 6):
        print(f"  G_{n} = {render(G(n))}")


if __name__ == "__main__":
    main()
