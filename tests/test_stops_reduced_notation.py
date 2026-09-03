"""Stops, reduced canonical form, and the notation round trip."""

from __future__ import annotations

from fractions import Fraction

import pytest

from pycgt import (
    DOWN,
    STAR,
    UP,
    ZERO,
    add,
    confusion_interval,
    integer,
    is_hot,
    is_infinitesimal,
    is_reduced,
    is_tepid,
    ish,
    miny,
    nimber,
    number,
    number_part,
    parse,
    plus_minus,
    reduced_canonical_form,
    render,
    stops,
    tiny,
    up_multiple,
)
from pycgt.rulesets import domineering

# --- stops ----------------------------------------------------------------


def test_stops_of_a_number_are_the_number():
    assert stops(number("3/4")) == (Fraction(3, 4), Fraction(3, 4))


def test_stops_of_a_switch():
    assert stops(plus_minus(1)) == (Fraction(1), Fraction(-1))
    assert is_hot(plus_minus(1))


def test_known_infinitesimals_have_both_stops_zero():
    for g in (STAR, UP, DOWN, nimber(3), tiny(2), miny(5), up_multiple(3)):
        assert is_infinitesimal(g), render(g)
        assert stops(g) == (0, 0)


def test_numbers_are_not_infinitesimal_except_zero():
    assert is_infinitesimal(ZERO)
    assert not is_infinitesimal(number("1/1024"))


def test_number_part_finds_the_infinitesimally_close_number():
    assert number_part(add(number(1), UP)) == Fraction(1)
    assert number_part(add(number("-1/2"), STAR)) == Fraction(-1, 2)
    assert number_part(plus_minus(1)) is None


def test_tepid_means_shifted_from_a_number_but_not_a_number():
    assert is_tepid(STAR)
    assert is_tepid(add(number(1), STAR))
    assert not is_tepid(number(1))
    assert not is_tepid(plus_minus(1))


def test_confusion_interval_of_a_switch():
    assert confusion_interval(plus_minus(2)) == (Fraction(-2), Fraction(2))


def test_domineering_two_by_four_is_infinitesimal():
    """It is miny-2, so despite containing a 2 it is smaller than every
    positive number."""
    g = domineering.rectangle(2, 4)
    assert is_infinitesimal(g)
    assert g == miny(2)


# --- reduced canonical form ----------------------------------------------


def test_infinitesimals_reduce_to_zero():
    for g in (STAR, UP, DOWN, tiny(2), miny(3), up_multiple(2)):
        assert reduced_canonical_form(g).is_zero, render(g)


def test_a_number_plus_an_infinitesimal_reduces_to_the_number():
    for text in ("0", "1", "-3/4"):
        for small in (STAR, UP, tiny(2)):
            g = add(number(text), small)
            assert reduced_canonical_form(g) == number(text)


def test_numbers_and_switches_are_already_reduced():
    for g in (number("3/4"), integer(-2), plus_minus(1)):
        assert is_reduced(g), render(g)


def test_reduced_canonical_form_is_idempotent():
    for g in (STAR, plus_minus(1), domineering.rectangle(2, 6), tiny(2)):
        once = reduced_canonical_form(g)
        assert reduced_canonical_form(once) == once


def test_ish_is_always_infinitesimal():
    """The defining property, and the strongest cheap check on the reduction."""
    candidates = [
        STAR,
        UP,
        tiny(2),
        add(number(1), STAR),
        plus_minus(1),
        *(domineering.rectangle(2, n) for n in range(1, 9)),
    ]
    for g in candidates:
        assert is_infinitesimal(ish(g)), render(g)


def test_ish_is_zero_exactly_when_already_reduced():
    assert ish(number("1/2")).is_zero
    assert ish(plus_minus(1)).is_zero
    assert not ish(STAR).is_zero


def test_ish_of_domineering_two_by_four_is_the_whole_value():
    """Its reduced form is 0, so the entire value is infinitesimal."""
    g = domineering.rectangle(2, 4)
    assert reduced_canonical_form(g).is_zero
    assert ish(g) == g


# --- notation -------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    ["0", "1", "-1", "1/2", "-3/4", "*", "*2", "*3", "^", "v", "+-1", "+-1/2"],
)
def test_render_parse_round_trip(text):
    assert render(parse(text)) == text


def test_render_recognises_tiny_and_miny():
    assert render(tiny(2)) == "Tiny(2)"
    assert render(miny(2)) == "Miny(2)"
    assert render(tiny("1/2")) == "Tiny(1/2)"


def test_render_recognises_number_plus_infinitesimal():
    assert render(add(number(1), STAR)) == "1*"
    assert render(add(number("1/2"), UP)) == "1/2^"


def test_render_recognises_plus_minus_of_non_numbers():
    """A switch whose Right options are the negatives of its Left options is
    +-X, whatever X is. CGSuite prints Clobber's xoxo row this way."""
    assert render(parse("{*,^|*,v}")) == "+-{*,^}"
    assert render(parse("{1|-1}")) == "+-1"
    assert render(parse("{1/2|-1/2}")) == "+-1/2"


def test_up_against_down_collapses_to_star():
    """{^|v} is not a switch: both options reverse out to 0, leaving *."""
    assert parse("{^|v}") == STAR
    assert render(parse("{^|v}")) == "*"


def test_parse_accepts_plus_minus_with_a_braced_argument():
    assert parse("+-{*,^}") == parse("{*,^|*,v}")
    assert render(parse("+-{*,^}")) == "+-{*,^}"


def test_plus_minus_star_is_zero():
    """Not a rendering quirk: -* is *, so {*|*} really is 0."""
    assert parse("+-*").is_zero
    assert render(parse("+-*")) == "0"


def test_asymmetric_switches_still_print_in_braces():
    assert render(parse("{2|-1/2}")) == "{2|-1/2}"


def test_parse_accepts_nested_braces_and_option_lists():
    assert parse("{{2|0}|0}") == miny(2)
    assert parse("{0,*|1}") == parse("{0,*|1}")
    assert parse("{1|-1}") == plus_minus(1)


def test_parse_rejects_nonsense():
    with pytest.raises(ValueError):
        parse("")
    with pytest.raises(ValueError):
        parse("{1}")


def test_render_falls_back_to_braces_for_unnamed_values():
    """A value the renderer cannot name must still print readably."""
    g = domineering.rectangle(2, 3)
    assert render(g) == "{2|-1/2}"
