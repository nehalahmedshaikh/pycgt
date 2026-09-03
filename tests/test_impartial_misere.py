"""Validation of impartial games and misère play.

Every expected value here is external: either produced by CGSuite, or a closed
form, or a periodicity result published decades ago. Nothing in this file is a
value this library computed and then enshrined.

Sources
-------
CGSuite 2.2 beta 2 (github.com/aaron-siegel/cgsuite), run headlessly on
    ``game.heap.TakeAndBreak(code)(n)`` for ``.NimValue``,
    ``.MisereNimValue``, ``.Genus``, and ``.MisereCanonicalForm.IsTame``,
    plus ``.MisereCanonicalForm + *[2] + ...`` for the genus superscript.
Guy and Smith, "The G-values of various games", Proc. Cambridge Philos. Soc.
    52 (1956) 514-526, for the periodicity of Dawson's Chess and Kayles.
Conway, "On Numbers and Games", chapter 12, and Berlekamp, Conway and Guy,
    "Winning Ways", chapter 13, for misère Nim and genus theory.

A note on CGSuite's ``Genus``. It is the *extended* genus and prints a
superscript whose length carries information beyond the classical genus, so it
is not a function of the data this library computes. Kayles heaps 7, 10, 14 and
19 all have nim value 2 and the identical superscript sequence 2 0 2 0 ...
(checked to 17 terms), yet CGSuite prints ``2^2``, ``2^2``, ``2^2`` and
``2^20``. The tests below therefore compare the *sequence* exactly, and accept
CGSuite's symbol when it agrees, when it is the nim-position shorthand ``n``,
or when it is a prefix of ours because CGSuite stopped after one digit.
"""

from __future__ import annotations

import pytest

from pycgt.game import Outcome
from pycgt.impartial import (
    ENDGAME,
    Genus,
    add,
    birthday,
    genus,
    genus_sequence,
    impartial,
    is_tame,
    misere_nim_value,
    misere_outcome,
    multiple,
    nim_heap,
    nim_position_genera,
    nim_value,
    normal_outcome,
    normal_value,
)
from pycgt.notation import render
from pycgt.rulesets.heap import (
    DAWSONS_CHESS,
    GRUNDYS_GAME,
    KAYLES,
    OFFICERS,
    TREBLECROSS,
    heap,
    heaps,
    misere_nim_values,
    nim_values,
    octal,
    subtraction,
)

# ---------------------------------------------------------------------------
# CGSuite tables: (heap, nim value, misère nim value, genus, tame, 8 terms)
# ---------------------------------------------------------------------------

KAYLES_CGSUITE = [
    (0, 0, 1, "0", True, "12020202"),
    (1, 1, 0, "1", True, "03131313"),
    (2, 2, 2, "2", True, "20202020"),
    (3, 3, 3, "3", True, "31313131"),
    (4, 1, 0, "1", True, "03131313"),
    (5, 4, 1, "4^146", False, "14646464"),
    (6, 3, 3, "3", True, "31313131"),
    (7, 2, 2, "2^2", False, "20202020"),
    (8, 1, 1, "1^1", True, "13131313"),
    (9, 4, 0, "4^046", False, "04646464"),
    (10, 2, 2, "2^2", False, "20202020"),
    (11, 6, 4, "6^46", False, "46464646"),
    (12, 4, 0, "4^046", False, "04646464"),
    (13, 1, 1, "1^1", False, "13131313"),
    (14, 2, 2, "2^2", False, "20202020"),
    (15, 7, 5, "7^57", False, "57575757"),
    (16, 1, 1, "1^13", False, "13131313"),
    (17, 4, 6, "4^64", False, "64646464"),
    (18, 3, 3, "3^31", False, "31313131"),
    (19, 2, 2, "2^20", False, "20202020"),
    (20, 1, 0, "1^031", False, "03131313"),
    (21, 4, 6, "4^64", False, "64646464"),
    (22, 6, 4, "6^46", False, "46464646"),
    (23, 7, 5, "7^57", False, "57575757"),
    (24, 4, 6, "4^64", False, "64646464"),
    (25, 1, 7, "1^731", False, "73131313"),
]

DAWSONS_CHESS_CGSUITE = [
    (0, 0, 1, "0", True, "12020202"),
    (1, 1, 0, "1", True, "03131313"),
    (2, 1, 0, "1", True, "03131313"),
    (3, 2, 2, "2", True, "20202020"),
    (4, 0, 1, "0", True, "12020202"),
    (5, 3, 3, "3", True, "31313131"),
    (6, 1, 0, "1", True, "03131313"),
    (7, 1, 0, "1", True, "03131313"),
    (8, 0, 1, "0", True, "12020202"),
    (9, 3, 1, "3^1431", False, "14313131"),
    (10, 3, 3, "3", True, "31313131"),
    (11, 2, 0, "2^0520", False, "05202020"),
    (12, 2, 2, "2", True, "20202020"),
    (13, 4, 1, "4^146", False, "14646464"),
    (14, 0, 1, "0", True, "12020202"),
    (15, 5, 0, "5^057", False, "05757575"),
    (16, 2, 0, "2^0520", False, "05202020"),
    (17, 2, 2, "2", True, "20202020"),
    (18, 3, 1, "3^1431", False, "14313131"),
    (19, 3, 3, "3", True, "31313131"),
    (20, 0, 0, "0^02", False, "02020202"),
    (21, 1, 0, "1^031", False, "03131313"),
    (22, 1, 1, "1^13", False, "13131313"),
    (23, 3, 1, "3^1431", False, "14313131"),
    (24, 0, 3, "0^31", False, "31313131"),
    (25, 2, 0, "2^0520", False, "05202020"),
]

GRUNDYS_GAME_CGSUITE = [
    (0, 0, 1, "0", True, "12020202"),
    (1, 0, 1, "0", True, "12020202"),
    (2, 0, 1, "0", True, "12020202"),
    (3, 1, 0, "1", True, "03131313"),
    (4, 0, 1, "0", True, "12020202"),
    (5, 2, 2, "2", True, "20202020"),
    (6, 1, 0, "1", True, "03131313"),
    (7, 0, 1, "0", True, "12020202"),
    (8, 2, 2, "2", True, "20202020"),
    (9, 1, 0, "1", True, "03131313"),
    (10, 0, 1, "0", True, "12020202"),
    (11, 2, 2, "2", True, "20202020"),
    (12, 1, 0, "1", True, "03131313"),
    (13, 3, 1, "3^1431", False, "14313131"),
    (14, 2, 2, "2", True, "20202020"),
    (15, 1, 0, "1", True, "03131313"),
    (16, 3, 1, "3^1431", False, "14313131"),
    (17, 2, 2, "2", True, "20202020"),
    (18, 4, 0, "4^0564", False, "05646464"),
    (19, 3, 1, "3^1431", False, "14313131"),
]

TREBLECROSS_CGSUITE = [
    (0, 0, 1, "0", True, "12020202"),
    (1, 0, 1, "0", True, "12020202"),
    (2, 0, 1, "0", True, "12020202"),
    (3, 1, 0, "1", True, "03131313"),
    (4, 1, 0, "1", True, "03131313"),
    (5, 1, 0, "1", True, "03131313"),
    (6, 2, 2, "2", True, "20202020"),
    (7, 2, 2, "2", True, "20202020"),
    (8, 0, 1, "0", True, "12020202"),
    (9, 3, 3, "3", True, "31313131"),
    (10, 3, 3, "3", True, "31313131"),
    (11, 1, 0, "1", True, "03131313"),
    (12, 1, 0, "1", True, "03131313"),
    (13, 1, 0, "1", True, "03131313"),
    (14, 0, 1, "0", True, "12020202"),
    (15, 4, 1, "4^146", False, "14646464"),
    (16, 3, 1, "3^1431", False, "14313131"),
    (17, 3, 3, "3", True, "31313131"),
    (18, 3, 3, "3", True, "31313131"),
    (19, 2, 0, "2^0520", False, "05202020"),
    (20, 2, 2, "2", True, "20202020"),
    (21, 2, 2, "2", True, "20202020"),
    (22, 4, 1, "4^146", False, "14646464"),
    (23, 4, 1, "4^146", False, "14646464"),
    (24, 0, 1, "0^1", False, "12020202"),
    (25, 5, 0, "5^057", False, "05757575"),
]

OFFICERS_CGSUITE = [
    (0, 0, 1, "0", True, "12020202"),
    (1, 0, 1, "0", True, "12020202"),
    (2, 1, 0, "1", True, "03131313"),
    (3, 2, 2, "2", True, "20202020"),
    (4, 0, 1, "0", True, "12020202"),
    (5, 1, 0, "1", True, "03131313"),
    (6, 2, 2, "2", True, "20202020"),
    (7, 3, 1, "3^1431", False, "14313131"),
    (8, 1, 0, "1", True, "03131313"),
    (9, 2, 2, "2", True, "20202020"),
    (10, 3, 1, "3^1431", False, "14313131"),
    (11, 4, 0, "4^0564", False, "05646464"),
    (12, 0, 2, "0^20", False, "20202020"),
    (13, 3, 1, "3^1431", False, "14313131"),
    (14, 4, 0, "4^0564", False, "05646464"),
    (15, 2, 2, "2^20", False, "20202020"),
    (16, 1, 1, "1^13", False, "13131313"),
    (17, 3, 0, "3^0531", False, "05313131"),
    (18, 2, 2, "2^20", False, "20202020"),
    (19, 1, 1, "1^13", False, "13131313"),
    (20, 0, 0, "0^02", False, "02020202"),
    (21, 2, 2, "2^20", False, "20202020"),
    (22, 1, 1, "1^13", False, "13131313"),
    (23, 4, 0, "4^0564", False, "05646464"),
    (24, 5, 4, "5^475", False, "47575757"),
    (25, 1, 1, "1^13", False, "13131313"),
]

TABLES = [
    ("Kayles", KAYLES, KAYLES_CGSUITE),
    ("Dawson's Chess", DAWSONS_CHESS, DAWSONS_CHESS_CGSUITE),
    ("Grundy's Game", GRUNDYS_GAME, GRUNDYS_GAME_CGSUITE),
    ("Treblecross", TREBLECROSS, TREBLECROSS_CGSUITE),
    ("Officers", OFFICERS, OFFICERS_CGSUITE),
]

CASES = [
    pytest.param(ruleset, row, id=f"{name}-{row[0]}")
    for name, ruleset, table in TABLES
    for row in table
]


# ---------------------------------------------------------------------------
# The reason this module exists: canonical form destroys misère information
# ---------------------------------------------------------------------------


def test_normal_canonical_form_cannot_see_misere_play() -> None:
    """Two heaps of two is zero in normal play but not in misère play.

    This is why misère analysis needs its own uncanonicalised game type: a
    `Game` reduces this to the endgame, which has the opposite misère outcome.
    """
    two_and_two = add(nim_heap(2), nim_heap(2))

    # Indistinguishable under normal play.
    assert nim_value(two_and_two) == nim_value(ENDGAME) == 0
    assert render(normal_value(two_and_two)) == render(normal_value(ENDGAME)) == "0"

    # Opposite under misère play.
    assert misere_outcome(two_and_two) is Outcome.SECOND
    assert misere_outcome(ENDGAME) is Outcome.FIRST

    # And the raw trees are not equal, which is what preserves the difference.
    assert two_and_two != ENDGAME
    assert birthday(two_and_two) == 4


def test_sums_do_not_collapse() -> None:
    """Unlike `pycgt.game.add`, the impartial sum performs no reduction."""
    assert add(nim_heap(1), nim_heap(1)) != ENDGAME
    assert nim_value(add(nim_heap(1), nim_heap(1))) == 0
    # ... but adding the endgame really is the identity, structurally.
    assert add(ENDGAME, nim_heap(3)) is nim_heap(3)
    assert multiple(nim_heap(2), 0) is ENDGAME


def test_interning_makes_equal_trees_identical() -> None:
    """Equal trees are the same object, so `==` is a pointer comparison."""
    a = add(nim_heap(2), nim_heap(3))
    b = add(nim_heap(3), nim_heap(2))
    assert a is b
    assert impartial([ENDGAME, nim_heap(1)]) is nim_heap(2)


# ---------------------------------------------------------------------------
# Definitions and closed forms, needing no oracle
# ---------------------------------------------------------------------------


def test_misere_nim_value_base_case_is_the_whole_difference() -> None:
    """`g⁻(0) = 1` where `g(0) = 0`; everything else follows."""
    assert nim_value(ENDGAME) == 0
    assert misere_nim_value(ENDGAME) == 1
    # Which is what swaps the role of a heap of one.
    assert [misere_nim_value(nim_heap(n)) for n in range(8)] == [1, 0, 2, 3, 4, 5, 6, 7]
    assert [nim_value(nim_heap(n)) for n in range(8)] == list(range(8))


def test_sprague_grundy_on_sums_of_heaps() -> None:
    """Normal play: a sum's nim value is the exclusive-or of its parts'."""
    for a in range(5):
        for b in range(5):
            for c in range(4):
                total = add(add(nim_heap(a), nim_heap(b)), nim_heap(c))
                assert nim_value(total) == a ^ b ^ c


def _misere_nim_is_loss_for_mover(sizes: tuple[int, ...]) -> bool:
    """The classical closed form for misère Nim.

    With every heap of size one, the mover loses exactly when the number of
    heaps is odd; otherwise the misère outcome matches the normal one.
    """
    live = [s for s in sizes if s > 0]
    if all(s <= 1 for s in live):
        return len(live) % 2 == 1
    total = 0
    for s in live:
        total ^= s
    return total == 0


def test_misere_nim_matches_its_closed_form() -> None:
    """Check every Nim position with up to four heaps of at most four tokens."""
    checked = 0
    for a in range(5):
        for b in range(a + 1):
            for c in range(b + 1):
                for d in range(c + 1):
                    sizes = (a, b, c, d)
                    position = ENDGAME
                    for size in sizes:
                        position = add(position, nim_heap(size))
                    expected = (
                        Outcome.SECOND
                        if _misere_nim_is_loss_for_mover(sizes)
                        else Outcome.FIRST
                    )
                    assert misere_outcome(position) is expected, sizes
                    checked += 1
    assert checked == 70


def test_two_independent_misere_outcome_computations_agree() -> None:
    """`misere_outcome` walks the rules; `misere_nim_value` computes a mex.

    They share no code, so agreement is a real check on both.
    """
    positions = [heap(KAYLES, n) for n in range(14)]
    positions += [heap(DAWSONS_CHESS, n) for n in range(16)]
    positions += [heaps(KAYLES, a, b) for a in range(5) for b in range(a + 1)]
    for position in positions:
        by_rules = misere_outcome(position) is Outcome.SECOND
        by_value = misere_nim_value(position) == 0
        assert by_rules == by_value


def test_normal_outcome_agrees_with_nim_value() -> None:
    for n in range(12):
        position = heap(KAYLES, n)
        assert (normal_outcome(position) is Outcome.SECOND) == (
            nim_value(position) == 0
        )


# ---------------------------------------------------------------------------
# The genus
# ---------------------------------------------------------------------------


def test_nim_heap_genera_are_the_traditional_symbols() -> None:
    """Winning Ways' symbols for Nim heaps, which our convention reproduces."""
    expected = ["0^120", "1^031", "2^20", "3^31", "4^46", "5^57", "6^64", "7^75"]
    assert [str(genus(nim_heap(n))) for n in range(8)] == expected


def test_genus_superscript_determines_the_infinite_sequence() -> None:
    symbol = genus(nim_heap(0))
    assert [symbol.term(k) for k in range(9)] == [1, 2, 0, 2, 0, 2, 0, 2, 0]
    assert genus_sequence(nim_heap(0), 9) == (1, 2, 0, 2, 0, 2, 0, 2, 0)
    # Every term the symbol reports must match a directly computed one.
    for n in range(6):
        symbol = genus(nim_heap(n))
        sequence = genus_sequence(nim_heap(n), 9)
        assert tuple(symbol.term(k) for k in range(9)) == sequence


def test_genus_superscript_always_shows_the_alternating_pair() -> None:
    for n in range(8):
        symbol = genus(nim_heap(n))
        assert len(symbol.superscript) >= 2
        last, previous = symbol.superscript[-1], symbol.superscript[-2]
        assert last == previous ^ 2
    with pytest.raises(ValueError):
        Genus(0, (1,))


def test_nim_position_genera_are_exactly_the_tame_ones() -> None:
    """Every Nim position's genus must be listed for its nim value."""
    for a in range(4):
        for b in range(a + 1):
            for c in range(b + 1):
                position = add(add(nim_heap(a), nim_heap(b)), nim_heap(c))
                symbol = genus(position)
                assert symbol in nim_position_genera(symbol.nim_value)
                assert is_tame(position)


def test_tame_and_wild() -> None:
    assert is_tame(nim_heap(5))
    assert is_tame(add(nim_heap(2), nim_heap(2)))
    # Dawson's Chess heap 9 is the smallest wild position in that ruleset.
    assert not is_tame(heap(DAWSONS_CHESS, 9))
    assert str(genus(heap(DAWSONS_CHESS, 9))) == "3^1431"


def test_genus_refuses_to_guess_when_it_has_not_settled() -> None:
    """A budget too small to see the alternation must raise, not report."""
    with pytest.raises(ValueError, match="has not begun to alternate"):
        genus(heap(DAWSONS_CHESS, 9), terms=3, confirm=3)
    with pytest.raises(ValueError):
        genus(nim_heap(0), confirm=1)


# ---------------------------------------------------------------------------
# CGSuite agreement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("ruleset", "row"), CASES)
def test_against_cgsuite(ruleset: object, row: tuple) -> None:
    size, expected_nim, expected_misere, symbol, tame, sequence = row
    position = heap(ruleset, size)  # type: ignore[arg-type]

    assert nim_value(position) == expected_nim
    assert misere_nim_value(position) == expected_misere

    # The superscript sequence is compared exactly -- it is the invariant part.
    assert genus_sequence(position, 8) == tuple(int(c) for c in sequence)

    # CGSuite's printed symbol is the *extended* genus, so it is accepted three
    # ways: an exact match, its shorthand `n` for a nim-position genus, or a
    # prefix of ours where it stopped after a single superscript digit.
    ours = str(genus(position))
    if symbol == ours:
        pass
    elif symbol == str(expected_nim):
        assert is_tame(position), f"{symbol} is shorthand but we call it wild"
    else:
        digits = symbol.partition("^")[2]
        assert len(digits) == 1 and ours.startswith(symbol), (
            f"unexplained genus: CGSuite {symbol}, ours {ours}"
        )

    # CGSuite's IsTame is finer than the genus notion, so it implies ours.
    if tame:
        assert is_tame(position)


def test_cgsuite_tameness_is_strictly_finer() -> None:
    """Record the gap rather than pretend the two notions agree.

    Kayles heap 7 has exactly the genus of ``*2``, so classical misère theory
    calls it tame; CGSuite calls it wild because its misère canonical form is
    not a Nim position's.
    """
    assert is_tame(heap(KAYLES, 7))
    assert str(genus(heap(KAYLES, 7))) == str(genus(nim_heap(2))) == "2^20"
    # These are the positions in the CGSuite tables where the notions differ.
    differing = [
        (name, size)
        for name, ruleset, table in TABLES
        for size, _, _, _, tame, _ in table
        if not tame and is_tame(heap(ruleset, size))
    ]
    assert differing == [
        ("Kayles", 7),
        ("Kayles", 10),
        ("Kayles", 13),
        ("Kayles", 14),
        ("Kayles", 16),
        ("Kayles", 18),
        ("Kayles", 19),
        ("Kayles", 20),
        ("Dawson's Chess", 20),
        ("Dawson's Chess", 21),
        ("Dawson's Chess", 22),
        ("Treblecross", 24),
        ("Officers", 15),
        ("Officers", 16),
        ("Officers", 18),
        ("Officers", 19),
        ("Officers", 20),
        ("Officers", 21),
        ("Officers", 22),
        ("Officers", 25),
    ]


# ---------------------------------------------------------------------------
# Published periodicity, owing nothing to CGSuite
# ---------------------------------------------------------------------------


def test_dawsons_chess_has_period_34() -> None:
    """Guy and Smith (1956): the nim values of ``.137`` have period 34.

    The exceptions are the five values below, after which it never fails again.
    """
    values = nim_values(DAWSONS_CHESS, 1000)
    exceptions = [n for n in range(1000 - 34) if values[n] != values[n + 34]]
    assert exceptions == [14, 16, 31, 34, 51]


def test_kayles_has_period_12_from_seventy_two() -> None:
    """Guy and Smith (1956): ``0.77`` becomes periodic with period 12."""
    values = nim_values(KAYLES, 500)
    assert all(values[n] == values[n + 12] for n in range(72, 500 - 12))
    # And it is genuinely not periodic before then.
    assert any(values[n] != values[n + 12] for n in range(72))


def test_nim_values_recurrence_agrees_with_the_raw_trees() -> None:
    """The fast integer recurrence must match walking the unreduced tree."""
    for ruleset, upto in [
        (KAYLES, 22),
        (DAWSONS_CHESS, 26),
        (GRUNDYS_GAME, 20),
        (TREBLECROSS, 22),
        (OFFICERS, 20),
        (subtraction([1, 2, 3]), 20),
    ]:
        table = nim_values(ruleset, upto)
        assert table == tuple(nim_value(heap(ruleset, n)) for n in range(upto))


# ---------------------------------------------------------------------------
# Rulesets
# ---------------------------------------------------------------------------


def test_octal_notation_round_trips() -> None:
    assert octal("0.77").digits == (0, 7, 7)
    assert octal(".137").digits == (0, 1, 3, 7)
    assert str(octal("0.137")) == "0.137"
    assert KAYLES == octal("0.77")
    for bad in ["77", "0.98", "12.7", "0.7x", ""]:
        with pytest.raises(ValueError):
            octal(bad)


def test_subtraction_games_are_periodic() -> None:
    """Subtraction by {1, ..., k} has nim value n mod (k + 1)."""
    for k in range(1, 6):
        table = nim_values(subtraction(range(1, k + 1)), 40)
        assert table == tuple(n % (k + 1) for n in range(40))
    with pytest.raises(ValueError):
        subtraction([])
    with pytest.raises(ValueError):
        subtraction([0, 1])


def test_grundys_game_splits_into_unequal_heaps() -> None:
    assert sorted(GRUNDYS_GAME.heap_options(7)) == [(1, 6), (2, 5), (3, 4)]
    assert sorted(GRUNDYS_GAME.heap_options(8)) == [(1, 7), (2, 6), (3, 5)]
    assert list(GRUNDYS_GAME.heap_options(2)) == []


def test_kayles_moves_are_take_one_or_two_and_split() -> None:
    assert sorted(KAYLES.heap_options(1)) == [()]
    assert sorted(KAYLES.heap_options(2)) == [(), (1,)]
    assert sorted(KAYLES.heap_options(4)) == [(1, 1), (1, 2), (2,), (3,)]


def test_misere_nim_values_table() -> None:
    assert misere_nim_values(KAYLES, 10) == (1, 0, 2, 3, 0, 1, 3, 2, 1, 0)
    assert misere_nim_values(DAWSONS_CHESS, 10) == (1, 0, 0, 2, 1, 3, 0, 0, 1, 1)


def test_heaps_of_negative_size_are_rejected() -> None:
    with pytest.raises(ValueError):
        nim_heap(-1)
    with pytest.raises(ValueError):
        heap(KAYLES, -1)
    with pytest.raises(ValueError):
        multiple(nim_heap(1), -1)
    with pytest.raises(ValueError):
        genus_sequence(ENDGAME, 0)
