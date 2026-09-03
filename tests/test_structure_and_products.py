"""Structural properties, the Norton product, and the notation they exposed.

Every expected value here came from CGSuite, run through the harness in
``tools/cgsuite``. Two of them are recorded disagreements rather than
agreements, and both are explained where they appear.

Sources
-------
CGSuite 2.2, on ``CanonicalShortGame``: ``StopCount``, ``Companion``,
    ``Freeze``, ``Cool``, ``IsEvenTempered``, ``IsOddTempered``,
    ``NortonProduct``, ``FollowerCount``, ``Followers``; and on
    ``NormalValue``: ``IsNumberish``, ``IsNumberTiny``, ``IsIdempotent``.
CGSuite 2.2, on ``Game``: ``ConjunctiveSum``, ``SelectiveSum``.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from pycgt import (
    DOWN,
    STAR,
    UP,
    ZERO,
    add,
    as_up_multiple,
    canonical,
    conjunctive_sum,
    cool,
    follower_count,
    followers,
    freeze,
    integer,
    is_even_tempered,
    is_idempotent,
    is_integer,
    is_nimber,
    is_number_tiny,
    is_numberish,
    is_odd_tempered,
    miny,
    multiple,
    nimber,
    norton_product,
    number,
    parse,
    plus_minus,
    render,
    selective_sum,
    stop_count,
    switch,
    temperature,
    tiny,
    up_multiple,
)

# game, StopCount, IsEvenTempered, IsOddTempered, FollowerCount
CGSUITE_STRUCTURE = [
    ("0", ZERO, 1, True, False, 1),
    ("1", integer(1), 1, True, False, 2),
    ("2", integer(2), 1, True, False, 3),
    ("1/2", number(Fraction(1, 2)), 1, True, False, 3),
    ("-3/2", number(Fraction(-3, 2)), 1, True, False, 4),
    ("*", STAR, 2, False, True, 2),
    ("*2", nimber(2), 6, False, False, 3),
    ("*3", nimber(3), 18, False, False, 4),
    ("*4", nimber(4), 54, False, False, 5),
    ("^", UP, 3, False, False, 3),
    ("v", DOWN, 3, False, False, 3),
    ("^^", up_multiple(2), 5, False, False, 4),
    ("+-1", plus_minus(1), 2, False, True, 4),
    ("{2|-1/2}", parse("{2|-1/2}"), 2, False, True, 6),
    ("{2|0}", switch(2, 0), 2, False, True, 4),
    ("Tiny(2)", tiny(2), 3, False, False, 5),
    ("Miny(2)", miny(2), 3, False, False, 5),
    ("Tiny(1)", tiny(1), 3, False, False, 4),
]


@pytest.mark.parametrize(
    ("name", "game", "count", "even", "odd", "reachable"), CGSUITE_STRUCTURE
)
def test_structure_against_cgsuite(
    name: str, game: object, count: int, even: bool, odd: bool, reachable: int
) -> None:
    assert stop_count(game) == count, name  # type: ignore[arg-type]
    assert is_even_tempered(game) is even, name  # type: ignore[arg-type]
    assert is_odd_tempered(game) is odd, name  # type: ignore[arg-type]
    assert follower_count(game) == reachable, name  # type: ignore[arg-type]


def test_stop_count_follows_its_definition() -> None:
    """One for a number, else the total over every option."""
    assert stop_count(STAR) == stop_count(ZERO) + stop_count(ZERO)
    two = nimber(2)
    assert stop_count(two) == sum(
        stop_count(o) for o in list(two.left) + list(two.right)
    )


def test_no_game_is_both_even_and_odd_tempered() -> None:
    for _, game, *_ in CGSUITE_STRUCTURE:
        assert not (is_even_tempered(game) and is_odd_tempered(game))
    # And plenty are neither, which is the point worth remembering.
    assert not is_even_tempered(nimber(2)) and not is_odd_tempered(nimber(2))


def test_followers_are_the_reachable_values() -> None:
    """CGSuite's Followers, as sets."""
    assert sorted(render(x) for x in followers(up_multiple(2))) == [
        "*",
        "0",
        "^*",
        "^^",
    ]
    assert sorted(render(x) for x in followers(plus_minus(1))) == [
        "+-1",
        "-1",
        "0",
        "1",
    ]
    assert sorted(render(x) for x in followers(tiny(2))) == [
        "-1",
        "-2",
        "0",
        "Tiny(2)",
        "{0|-2}",
    ]
    # A game is always among its own followers, so the count is never zero.
    for _, game, *_ in CGSUITE_STRUCTURE:
        assert canonical(game) in followers(game)


def test_only_zero_is_idempotent_among_short_games() -> None:
    assert is_idempotent(ZERO)
    for _, game, *_ in CGSUITE_STRUCTURE:
        assert is_idempotent(game) == (canonical(game) == ZERO)


# ---------------------------------------------------------------------------
# Norton product
# ---------------------------------------------------------------------------

# multiplier, unit, CGSuite's answer as text it will itself accept back
CGSUITE_NORTON = [
    (integer(0), UP, "0"),
    (integer(1), UP, "^"),
    (integer(2), UP, "^^"),
    (integer(3), UP, "^3"),
    (integer(-1), UP, "v"),
    (integer(1), STAR, "*"),
    (integer(2), STAR, "0"),
    (integer(-2), STAR, "0"),
    (integer(1), up_multiple(2), "^^"),
    (number(Fraction(1, 2)), STAR, "^"),
    (number(Fraction(1, 2)), UP, "{^^*|v*}"),
    (number(Fraction(1, 4)), UP, "{^^*||0|v3}"),
    (STAR, STAR, "*"),
    (UP, UP, "{^^*||0|v4}"),
    (nimber(2), STAR, "*2"),
    (nimber(2), UP, "+-{^^*,{^4|0}}"),
    (plus_minus(1), STAR, "0"),
    (integer(1), plus_minus(1), "+-1"),
    (integer(2), switch(2, 0), "2"),
    (tiny(2), STAR, "^"),
]


@pytest.mark.parametrize(("multiplier", "unit", "expected"), CGSUITE_NORTON)
def test_norton_product_against_cgsuite(
    multiplier: object, unit: object, expected: str
) -> None:
    """Compared by value, not by text.

    CGSuite writes nested games with the multi-bar convention and pycgt with
    nested braces, so ``{^^*||0|v3}`` and ``{^^*|{0|v3}}`` are the same game
    spelled two ways. Parsing CGSuite's own output sidesteps that entirely.
    """
    assert norton_product(multiplier, unit) == parse(expected)  # type: ignore[arg-type]


def test_norton_product_by_an_integer_is_repeated_addition() -> None:
    """The integer case of the definition, checked against `multiple`."""
    for n in range(-4, 5):
        for unit in (UP, STAR, plus_minus(1), tiny(2), nimber(2)):
            assert norton_product(integer(n), unit) == multiple(unit, n)


# ---------------------------------------------------------------------------
# Thermography: freeze, and cooling exactly at the temperature
# ---------------------------------------------------------------------------


def test_cooling_at_the_temperature_keeps_the_infinitesimal() -> None:
    """Regression: cooling froze one step too early.

    ``cool`` short-circuited to the mast whenever ``t >= temperature``, which
    threw away the infinitesimal that survives *at* the temperature. Cooling
    ``+-1`` by exactly 1 leaves ``{0|0}``, which is ``*`` and not 0, and
    ``freeze`` evaluates at precisely that point -- so every frozen value came
    back a plain number.
    """
    assert render(cool(plus_minus(1), Fraction(1))) == "*"
    assert render(cool(parse("{2|-1/2}"), Fraction(5, 4))) == "3/4*"
    assert render(cool(tiny(2), Fraction(0))) == "Tiny(2)"
    assert render(cool(STAR, Fraction(0))) == "*"
    # Beyond the temperature it really does freeze at the mast.
    assert render(cool(plus_minus(1), Fraction(2))) == "0"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("+-1", "*"),
        ("{2|-1/2}", "3/4*"),
        ("*", "*"),
        ("0", "0"),
        ("1", "1"),
    ],
)
def test_freeze_against_cgsuite(text: str, expected: str) -> None:
    assert render(freeze(parse(text))) == expected


def test_freeze_of_a_number_is_itself() -> None:
    """Numbers have negative temperature here, so `cool` cannot be called.

    A number is already frozen, and CGSuite agrees: ``Freeze`` of ``1`` is
    ``1``.
    """
    for text in ["0", "1", "-3/2", "1/2"]:
        assert freeze(parse(text)) == parse(text)
        assert temperature(parse(text)) < 0


def test_freeze_is_cooling_by_the_temperature() -> None:
    for text in ["+-1", "{2|-1/2}", "*", "^", "Tiny(2)", "{2|0}"]:
        game = parse(text)
        assert freeze(game) == cool(game, temperature(game))


# ---------------------------------------------------------------------------
# Predicates
# ---------------------------------------------------------------------------


def test_numberish_and_number_tiny_against_cgsuite() -> None:
    numberish = [
        (add(integer(1), UP), True),
        (STAR, True),
        (tiny(2), True),
        (plus_minus(1), False),
        (switch(2, 0), False),
        (parse("{2|-1/2}"), False),
    ]
    for game, expected in numberish:
        assert is_numberish(game) is expected, render(game)

    number_tiny = [
        (tiny(2), True),
        (miny(2), True),
        (integer(1), True),
        (add(integer(1), tiny(2)), True),
        (add(integer(1), miny(2)), True),
        (tiny(number(Fraction(1, 2))), True),
        (tiny(plus_minus(1)), True),
        (add(integer(1), STAR), False),
        (add(tiny(2), tiny(2)), False),
        (STAR, False),
        (UP, False),
        (tiny(STAR), False),
    ]
    for game, expected in number_tiny:
        assert is_number_tiny(game) is expected, render(game)


def test_up_is_tiny_zero_but_not_number_tiny() -> None:
    """``tiny-0`` really is ``^``, which is why the argument needs a stop.

    The tiny family only counts when its argument has a positive Left stop.
    Without that, ``^`` would be reported as number-tiny, and CGSuite says it
    is not.
    """
    assert tiny(0) == UP
    assert not is_number_tiny(UP)
    assert is_number_tiny(tiny(2))


def test_integer_and_nimber_predicates() -> None:
    assert is_integer(integer(3)) and is_integer(ZERO)
    assert not is_integer(number(Fraction(1, 2)))
    assert not is_integer(STAR)
    assert is_nimber(ZERO) and is_nimber(STAR) and is_nimber(nimber(9))
    assert not is_nimber(UP) and not is_nimber(integer(1))


# ---------------------------------------------------------------------------
# Sums that are not disjunctive
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (UP, UP, "^"),
        (integer(1), integer(1), "1"),
        (STAR, STAR, "*"),
        (integer(2), integer(1), "1"),
        (ZERO, integer(1), "0"),
        (plus_minus(1), plus_minus(1), "+-1"),
        (UP, STAR, "*"),
        (number(Fraction(1, 2)), integer(1), "1"),
        (integer(2), integer(2), "2"),
        (STAR, integer(1), "1"),
    ],
)
def test_conjunctive_sum_against_cgsuite(
    left: object, right: object, expected: str
) -> None:
    assert conjunctive_sum(left, right) == parse(expected)  # type: ignore[arg-type]


def test_conjunctive_sum_stops_when_either_component_does() -> None:
    for other in (UP, STAR, integer(3), plus_minus(1), tiny(2)):
        assert conjunctive_sum(ZERO, other) == ZERO
        assert conjunctive_sum(other, ZERO) == ZERO


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (integer(1), integer(1), "2"),
        (STAR, STAR, "*2"),
        (integer(2), integer(1), "3"),
        (ZERO, integer(1), "1"),
        (number(Fraction(1, 2)), integer(1), "3/2"),
        (integer(2), integer(2), "4"),
        (STAR, integer(1), "1*"),
    ],
)
def test_selective_sum_where_cgsuite_agrees(
    left: object, right: object, expected: str
) -> None:
    assert selective_sum(left, right) == parse(expected)  # type: ignore[arg-type]


def test_selective_sum_diverges_from_cgsuite() -> None:
    """A recorded disagreement, not an agreement.

    A selective sum stays selective, so a move in both components of
    ``1/2 or 1/2`` leaves ``1 or 1`` = 2 -- a poor move for Right, leaving the
    value 1. CGSuite returns 3/4, which is what results from treating a
    move in both components as passing to the *conjunctive* sum ``1 and 1`` =
    1. CGSuite's own documentation states the selective formula, so this looks
    like an implementation slip there rather than a difference of convention.

    Pinned so that a future change to either side is noticed.
    """
    half = number(Fraction(1, 2))
    assert render(selective_sum(half, half)) == "1"
    assert render(selective_sum(STAR, UP)) == "{^|*,*2}"
    # What CGSuite reports instead, for the record.
    assert render(parse("3/4")) == "3/4"
    assert render(parse("^*")) == "^*"


def test_selective_sum_of_zero_is_the_identity() -> None:
    for other in (UP, STAR, integer(3), plus_minus(1), nimber(2)):
        assert selective_sum(ZERO, other) == canonical(other)
        assert selective_sum(other, ZERO) == canonical(other)


# ---------------------------------------------------------------------------
# Notation that this work exposed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", range(1, 13))
def test_up_multiples_are_named_and_recognised(n: int) -> None:
    expected = "^" * n if n <= 2 else f"^{n}"
    assert render(up_multiple(n)) == expected
    assert render(up_multiple(-n)) == expected.replace("^", "v")
    assert parse(expected) == up_multiple(n)
    with_star = canonical(add(up_multiple(n), STAR))
    assert render(with_star) == expected + "*"
    assert parse(expected + "*") == with_star
    assert as_up_multiple(up_multiple(n)) == (n, False)
    assert as_up_multiple(with_star) == (n, True)


def test_three_ups_is_tiny_down_and_prefers_the_up_name() -> None:
    """The same value under two names; ``^3`` is the one to print.

    ``tiny-v`` and three ups are the same game, and the tiny check used to win,
    so ``3 . ^`` printed as ``Tiny(v)``.
    """
    assert tiny(DOWN) == up_multiple(3)
    assert render(up_multiple(3)) == "^3"
    assert render(norton_product(integer(3), UP)) == "^3"


def test_multi_bar_notation_parses() -> None:
    """``{A||B|C}`` means ``{A|{B|C}}``, which is how CGSuite prints."""
    assert parse("{0||0|-2}") == tiny(2)
    assert parse("{0||0|-2}") == parse("{0|{0|-2}}")
    assert parse("{{2|0}||0}") == miny(2)
    assert parse("{^^*||0|v3}") == parse("{^^*|{0|v3}}")
    assert parse("{0|||0||0|-2}") == parse("{0|{0|{0|-2}}}")
    with pytest.raises(ValueError, match="ambiguous separator"):
        parse("{0||1||2}")


def test_switch_argument_is_parenthesised_unless_it_is_a_number() -> None:
    """``+-1*`` would read as ``+-1`` plus a star; CGSuite writes ``+-(1*)``."""
    assert render(plus_minus(1)) == "+-1"
    assert render(parse("{1*|-1*}")) == "+-(1*)"
    assert parse("+-(1*)") == parse("{1*|-1*}")
    # -(2 ups + *) is 2 downs + *, so this is the switch between them.
    assert parse("+-(^^*)") == parse("{^^*|vv*}")


@pytest.mark.parametrize(
    "text",
    [
        "0",
        "1",
        "-2",
        "3/4",
        "*",
        "*2",
        "*7",
        "*40",
        "^",
        "^^",
        "^3",
        "^4",
        "^3*",
        "^*",
        "^^*",
        "v",
        "vv",
        "v3",
        "v4*",
        "Tiny(2)",
        "Miny(2)",
        "+-1",
        "+-(1*)",
        "+-{*,^}",
        "{2|-1/2}",
        "1*",
        "1^",
        "1^^",
        "1/2*",
        "1Tiny(2)",
        "-3/2*",
    ],
)
def test_render_parse_round_trip_for_everything_we_name(text: str) -> None:
    assert render(parse(text)) == text
