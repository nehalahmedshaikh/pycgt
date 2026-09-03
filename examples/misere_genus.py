"""Misère play in two classical heap games, checked against published results.

Runs three things and asserts each:

1. The genus table for Kayles and Dawson's Chess, marking the wild positions.
2. Guy and Smith's periodicity (1956): the nim values of Dawson's Chess have
   period 34, failing only at n = 14, 16, 31, 34, 51, and Kayles becomes
   periodic with period 12 from n = 72.
3. Misère Nim's closed form, on every position with up to four heaps.

Sources
-------
Guy and Smith, "The G-values of various games", Proc. Cambridge Philos. Soc.
    52 (1956) 514-526.
Berlekamp, Conway and Guy, "Winning Ways", chapter 13, for genus theory.
"""

from __future__ import annotations

from pycgt.game import Outcome
from pycgt.impartial import (
    ENDGAME,
    add,
    genus,
    is_tame,
    misere_nim_value,
    misere_outcome,
    nim_heap,
    nim_value,
)
from pycgt.rulesets.heap import DAWSONS_CHESS, KAYLES, heap, nim_values


def genus_table(name: str, ruleset: object, upto: int) -> None:
    print(f"{name}: genus of each heap, * marks wild")
    print(f"  {'n':>3}  {'nim':>3}  {'misere':>6}  {'genus':<8}")
    for size in range(upto):
        position = heap(ruleset, size)  # type: ignore[arg-type]
        wild = "" if is_tame(position) else "  *"
        print(
            f"  {size:>3}  {nim_value(position):>3}"
            f"  {misere_nim_value(position):>6}  {genus(position)!s:<8}{wild}"
        )
    print()


def check_periodicity() -> None:
    print("Guy and Smith (1956), periodicity of the nim values")

    values = nim_values(DAWSONS_CHESS, 1000)
    exceptions = [n for n in range(1000 - 34) if values[n] != values[n + 34]]
    assert exceptions == [14, 16, 31, 34, 51], exceptions
    print(f"  ok    Dawson's Chess has period 34, failing only at {exceptions}")

    values = nim_values(KAYLES, 500)
    assert all(values[n] == values[n + 12] for n in range(72, 500 - 12))
    assert any(values[n] != values[n + 12] for n in range(72))
    print("  ok    Kayles has period 12 from n = 72, and not before")
    print()


def check_misere_nim() -> None:
    """Misère Nim: with every heap of size one the mover loses on an odd
    count, and otherwise the misère outcome matches the normal one."""
    print("misère Nim against its closed form")
    checked = 0
    for a in range(5):
        for b in range(a + 1):
            for c in range(b + 1):
                for d in range(c + 1):
                    sizes = [s for s in (a, b, c, d) if s > 0]
                    position = ENDGAME
                    for size in sizes:
                        position = add(position, nim_heap(size))
                    if all(s <= 1 for s in sizes):
                        loses = len(sizes) % 2 == 1
                    else:
                        total = 0
                        for size in sizes:
                            total ^= size
                        loses = total == 0
                    expected = Outcome.SECOND if loses else Outcome.FIRST
                    assert misere_outcome(position) is expected, sizes
                    checked += 1
    print(f"  ok    all {checked} positions of up to four heaps agree")
    print()


def main() -> None:
    genus_table("Kayles (0.77)", KAYLES, 20)
    genus_table("Dawson's Chess (0.137)", DAWSONS_CHESS, 20)
    check_periodicity()
    check_misere_nim()

    # The point of the whole module, in two lines.
    two_heaps = add(nim_heap(2), nim_heap(2))
    assert nim_value(two_heaps) == nim_value(ENDGAME) == 0
    assert misere_outcome(two_heaps) is Outcome.SECOND
    assert misere_outcome(ENDGAME) is Outcome.FIRST
    print("two heaps of two is zero in normal play, and a misère loss;")
    print("the endgame is zero in normal play, and a misère win.")


if __name__ == "__main__":
    main()
