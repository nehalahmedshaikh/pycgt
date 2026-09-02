"""Core algebra: order, arithmetic, canonical form, numbers, named values."""

from __future__ import annotations

from fractions import Fraction

import pytest

from pycgt import (
    DOWN,
    STAR,
    UP,
    ZERO,
    Outcome,
    Relation,
    add,
    as_number,
    birthday,
    canonical,
    compare,
    confused,
    equals,
    game,
    geq,
    greater,
    integer,
    is_number,
    miny,
    multiple,
    negate,
    nimber,
    number,
    outcome,
    plus_minus,
    simplest_between,
    tiny,
)

# --- order ----------------------------------------------------------------


def test_integers_are_totally_ordered():
    for n in range(-4, 5):
        for m in range(-4, 5):
            assert geq(integer(n), integer(m)) == (n >= m)


def test_star_is_confused_with_zero():
    assert confused(STAR, ZERO)
    assert outcome(STAR) is Outcome.FIRST


def test_up_is_positive_but_below_every_positive_number():
    assert greater(UP, ZERO)
    for n in range(1, 4):
        assert greater(integer(n), UP)
    assert greater(number("1/1024"), UP)


def test_down_is_the_negative_of_up():
    assert negate(UP) == DOWN
    assert add(UP, DOWN).is_zero


def test_compare_gives_all_four_relations():
    assert compare(integer(1), integer(1)) is Relation.EQUAL
    assert compare(integer(2), integer(1)) is Relation.GREATER
    assert compare(integer(1), integer(2)) is Relation.LESS
    assert compare(STAR, ZERO) is Relation.CONFUSED


def test_outcome_classifies_the_four_cases():
    assert outcome(integer(1)) is Outcome.LEFT
    assert outcome(integer(-1)) is Outcome.RIGHT
    assert outcome(ZERO) is Outcome.SECOND
    assert outcome(plus_minus(1)) is Outcome.FIRST


def test_strict_inequality_operators_are_not_defined():
    """Games are only partially ordered, so < and > would mislead."""
    with pytest.raises(TypeError):
        _ = STAR < ZERO


# --- arithmetic -----------------------------------------------------------


def test_game_plus_its_negative_is_zero():
    for g in (integer(3), number("3/4"), STAR, UP, nimber(3), plus_minus(2), tiny(2)):
        assert add(g, negate(g)).is_zero, g


def test_addition_is_commutative_and_associative():
    values = [ZERO, integer(1), STAR, UP, number("1/2"), nimber(2)]
    for a in values:
        for b in values:
            assert add(a, b) == add(b, a)
            for c in values:
                assert add(add(a, b), c) == add(a, add(b, c))


def test_integer_addition_matches_ordinary_addition():
    for n in range(-3, 4):
        for m in range(-3, 4):
            assert as_number(add(integer(n), integer(m))) == Fraction(n + m)


def test_nimbers_add_by_exclusive_or():
    for a in range(5):
        for b in range(5):
            assert add(nimber(a), nimber(b)) == nimber(a ^ b)


def test_switches_are_their_own_negatives():
    for x in ("1", "1/2", "3"):
        assert negate(plus_minus(x)) == plus_minus(x)
        assert add(plus_minus(x), plus_minus(x)).is_zero


def test_multiple_handles_negative_counts():
    assert multiple(integer(1), -3) == integer(-3)
    assert multiple(STAR, 2).is_zero
    assert multiple(UP, 0).is_zero


def test_operators_match_functions():
    a, b = number("1/2"), STAR
    assert a + b == add(a, b)
    assert a - b == add(a, negate(b))
    assert -a == negate(a)
    assert 3 * a == multiple(a, 3)


# --- canonical form -------------------------------------------------------


def test_canonical_is_idempotent():
    for g in (ZERO, STAR, UP, nimber(3), tiny(2), plus_minus(1)):
        assert canonical(g) == g


def test_equal_games_have_identical_canonical_forms():
    assert add(STAR, STAR) == ZERO
    assert equals(add(STAR, STAR), ZERO)


def test_dominated_options_are_removed():
    #  {0, -1 | } : Left would never choose -1 when 0 is available.
    assert game({ZERO, integer(-1)}, ()) == integer(1)


def test_reversible_option_is_bypassed():
    """miny-2 is {{2|0}|0}; its canonical form is not simplified away."""
    g = game({game({integer(2)}, {ZERO})}, {ZERO})
    assert g == miny(2)
    assert birthday(g) == 4


# --- numbers --------------------------------------------------------------


def test_simplest_between_prefers_zero_then_integers_then_dyadics():
    assert simplest_between(Fraction(-1), Fraction(1)) == 0
    assert simplest_between(None, None) == 0
    assert simplest_between(Fraction(0), None) == 1
    assert simplest_between(Fraction(3), None) == 4
    assert simplest_between(None, Fraction(-2)) == -3
    assert simplest_between(Fraction(0), Fraction(1)) == Fraction(1, 2)
    assert simplest_between(Fraction(1, 2), Fraction(1)) == Fraction(3, 4)


def test_number_round_trips():
    for text in ("0", "1", "-1", "1/2", "-3/4", "7/8", "5", "-11/16"):
        assert as_number(number(text)) == Fraction(text)


def test_number_rejects_non_dyadic():
    with pytest.raises(ValueError, match="dyadic"):
        number("1/3")


def test_halves_add_to_one():
    half = number("1/2")
    assert add(half, half) == integer(1)


def test_switches_and_star_are_not_numbers():
    assert not is_number(plus_minus(1))
    assert not is_number(STAR)
    assert is_number(number("3/4"))


def test_birthday_counts_days():
    assert birthday(ZERO) == 0
    assert birthday(integer(1)) == 1
    assert birthday(STAR) == 1
    assert birthday(integer(3)) == 3
