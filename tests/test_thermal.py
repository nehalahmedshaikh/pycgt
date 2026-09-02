"""Heating, overheating, cooling, temperature and mean."""

from __future__ import annotations

from fractions import Fraction

import pytest

from pycgt import (
    STAR,
    UP,
    add,
    cool,
    heat,
    integer,
    is_number,
    mean,
    number,
    overheat,
    parse,
    plus_minus,
    render,
    temperature,
    thermograph,
)

# --- heating --------------------------------------------------------------


def test_heating_fixes_numbers():
    for text in ("0", "1", "-2", "1/2", "3/4"):
        g = number(text)
        assert heat(g, number("3/4")) == g


def test_heating_star_gives_a_switch():
    assert render(heat(STAR, number("3/4"))) == "+-3/4"
    assert heat(STAR, number(1)) == plus_minus(1)


def test_heating_is_linear_on_the_cases_berlekamp_uses():
    """Berlekamp states linearity for arguments that are numbers or number
    plus star, which is the regime his formulas live in."""
    t = number("3/4")
    pairs = [
        (STAR, STAR),
        (STAR, number(1)),
        (number("1/2"), STAR),
        (number(1), number("1/2")),
    ]
    for a, b in pairs:
        assert heat(add(a, b), t) == add(heat(a, t), heat(b, t))


# --- overheating ----------------------------------------------------------


@pytest.mark.parametrize("k", range(-3, 4))
def test_overheating_maps_integers_to_multiples_of_s(k):
    """Overheating stops at integers, sending n to n copies of s."""
    s = number("1/2")
    got = overheat(integer(k), s, add(s, STAR))
    assert got == number(Fraction(k, 2))


def test_overheating_differs_from_heating_on_non_integer_numbers():
    """Heating stops at any number; overheating only at integers. So they
    must disagree on 1/2."""
    half, t = number("1/2"), number("3/4")
    assert heat(half, t) == half
    assert overheat(half, half, t) != half


# --- cooling, temperature, mean -------------------------------------------


def test_cooling_a_switch_freezes_at_its_temperature():
    g = plus_minus(1)
    assert not is_number(cool(g, Fraction(1, 2)))
    assert cool(g, Fraction(1)).is_zero
    assert temperature(g) == 1
    assert mean(g) == 0


def test_temperature_and_mean_of_an_asymmetric_switch():
    """{2 | -1/2} freezes where 2 - t equals -1/2 + t, i.e. t = 5/4."""
    g = parse("{2|-1/2}")
    assert temperature(g) == Fraction(5, 4)
    assert mean(g) == Fraction(3, 4)


def test_infinitesimals_have_temperature_zero():
    for g in (STAR, UP, add(UP, STAR)):
        assert temperature(g) == 0
        assert mean(g) == 0


def test_numbers_are_cold():
    assert temperature(number(0)) == Fraction(-1)
    assert temperature(number(3)) == Fraction(-1)
    assert temperature(number("1/2")) == Fraction(-1, 2)
    assert temperature(number("3/4")) == Fraction(-1, 4)


def test_mean_of_a_number_is_itself():
    for text in ("0", "5", "-3/4"):
        assert mean(number(text)) == Fraction(text)


def test_cooling_rejects_negative_temperature():
    with pytest.raises(ValueError, match="non-negative"):
        cool(plus_minus(1), Fraction(-1))


def test_thermograph_boundaries_start_at_the_stops():
    graph = thermograph(plus_minus(1))
    assert graph.at(Fraction(0)) == (Fraction(1), Fraction(-1))


def test_thermograph_boundaries_meet_at_the_temperature():
    for g in (plus_minus(1), parse("{2|-1/2}"), parse("{{7/2|3/2}|{1|-1/2}}")):
        graph = thermograph(g)
        low, high = graph.at(graph.temperature)
        assert low == high == graph.mast, render(g)


def test_thermograph_stays_at_the_mast_beyond_the_temperature():
    """Cooling is monotone: once frozen, always frozen at the same value.

    Getting this wrong is exactly the bug that a naive cool-and-test loop
    produces, so it is pinned down here.
    """
    for g in (plus_minus(1), parse("{2|-1/2}"), parse("{{{7/2|3/2}|{1|-1/2}}|-1}")):
        graph = thermograph(g)
        for extra in ("0", "1/16", "1/2", "3", "100"):
            t = graph.temperature + Fraction(extra)
            assert graph.at(t) == (graph.mast, graph.mast), f"{render(g)} at {t}"
            assert cool(g, t) == number(graph.mast)


def test_cooling_is_monotone_in_temperature():
    g = parse("{{{7/2|3/2}|{1|-1/2}}|-1}")
    t = temperature(g)
    frozen = [cool(g, t + Fraction(k, 16)) for k in range(8)]
    assert all(f == frozen[0] for f in frozen)
    assert is_number(frozen[0])
