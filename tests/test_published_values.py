"""Validation against values published in the literature and against CGSuite.

These are the most valuable tests here. Every expected value is either
(a) printed in a peer-reviewed paper, or (b) produced by CGSuite, Aaron
Siegel's system, which is the standard tool in the field. Nothing in this file
is a value this library computed and then enshrined.

Sources
-------
Berlekamp, "Blockbusting and Domineering", J. Combin. Theory A 49 (1988)
    67-116. Appendix B.1 gives exact values for the 2-wide by 2n-tall
    Domineering rectangle for n <= 3.
Guy, "Unsolved Problems in Combinatorial Games", Games of No Chance (1996),
    Problem 4, recording David Wolfe's computation of the 4x5 board.
Uiterwijk, "An update on Domineering on rectangular boards", arXiv:1305.3257,
    which prints the value of the 11x2 board.
CGSuite 2.2 beta 2 (github.com/aaron-siegel/cgsuite), run headlessly on
    game.grid.Domineering(Grid.Empty(r, c)).CanonicalForm and .Temperature
    and .Mean.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from pycgt import (
    add,
    game,
    integer,
    mean,
    miny,
    multiple,
    negate,
    number,
    parse,
    plus_minus,
    render,
    temperature,
    tiny,
)
from pycgt.rulesets import domineering
from pycgt.rulesets.grid import value

# --- Berlekamp 1988, Appendix B.1 ----------------------------------------
# G_n is the board 2 columns wide and 2n rows tall. He gives exact values
# only for n <= 3, and a "tight-ish" bound beyond.


def berlekamp_g(n: int):
    return domineering.rectangle(2 * n, 2)


def test_berlekamp_g1_is_plus_minus_one():
    assert berlekamp_g(1) == plus_minus(1)


def test_berlekamp_g2_is_tiny_two():
    """His "+_2 = G_2", where +_2 denotes tiny-two."""
    assert berlekamp_g(2) == tiny(2)


def test_berlekamp_g3_is_plus_minus_one_plus_two_tiny_two():
    """His "+-1 + +_2 + +_2 = G_3"."""
    expected = add(plus_minus(1), multiple(tiny(2), 2))
    assert berlekamp_g(3) == expected


def test_transposing_domineering_negates():
    """Left plays vertically and Right horizontally, so transposition swaps
    the players. This is why G_n = -value(2 x 2n)."""
    for rows in range(1, 5):
        for cols in range(1, 5):
            a = domineering.rectangle(rows, cols)
            b = domineering.rectangle(cols, rows)
            assert a == negate(b), f"{rows}x{cols}"


# --- Wolfe, via Guy's Problem 4 ------------------------------------------


def test_wolfe_four_by_five_is_one():
    assert domineering.rectangle(4, 5) == integer(1)


# --- Uiterwijk, arXiv:1305.3257 ------------------------------------------


def test_uiterwijk_eleven_by_two():
    """He prints |G_11,2| = {1 ||| 1/2 | -1 || -3/2 | -7/2}."""
    expected = parse("{1|{{1/2|-1}|{-3/2|-7/2}}}")
    assert domineering.rectangle(11, 2) == expected


# --- CGSuite: canonical forms of 2 x n -----------------------------------

CGSUITE_VALUES = {
    1: "1",
    2: "+-1",
    3: "{2|-1/2}",
    4: "Miny(2)",
    5: "1/2",
    7: "{3/2|-1/2}",
    9: "{{5/2|1/2}|{0|-3/2}}",
    13: "0",
}


@pytest.mark.parametrize("n, expected", sorted(CGSUITE_VALUES.items()))
def test_cgsuite_canonical_forms(n, expected):
    assert render(domineering.rectangle(2, n)) == expected


def test_two_by_six_matches_cgsuite():
    """CGSuite prints {1Miny(2)|-1}, i.e. {1 + miny-2 | -1}."""
    inner = add(integer(1), miny(2))
    expected = game({inner}, {integer(-1)})
    assert domineering.rectangle(2, 6) == expected


def test_two_by_eight_matches_cgsuite():
    """CGSuite prints {2Miny(2)|0||-1/2|-2}."""
    inner = add(integer(2), miny(2))
    expected = game({game({inner}, {integer(0)})}, {parse("{-1/2|-2}")})
    assert domineering.rectangle(2, 8) == expected


# --- CGSuite: temperatures and means of 2 x n ----------------------------

CGSUITE_TEMPERATURES = {
    2: "1",
    3: "5/4",
    4: "0",
    5: "-1/2",
    6: "1",
    7: "1",
    8: "9/8",
    9: "9/8",
    10: "19/16",
    11: "19/16",
    12: "0",
}

CGSUITE_MEANS = {
    1: "1",
    2: "0",
    3: "3/4",
    4: "0",
    5: "1/2",
    6: "0",
    7: "1/2",
    8: "-1/8",
    9: "3/8",
    10: "-5/16",
    11: "3/16",
    12: "-1/2",
}


@pytest.mark.parametrize("n, expected", sorted(CGSUITE_TEMPERATURES.items()))
def test_temperature_matches_cgsuite(n, expected):
    assert temperature(domineering.rectangle(2, n)) == Fraction(expected)


@pytest.mark.parametrize("n, expected", sorted(CGSUITE_MEANS.items()))
def test_mean_matches_cgsuite(n, expected):
    assert mean(domineering.rectangle(2, n)) == Fraction(expected)


def test_number_temperature_convention_matches_cgsuite():
    """CGSuite reports temperature -1 for 0 and -1/2 for 1/2."""
    assert temperature(number(0)) == Fraction(-1)
    assert temperature(number("1/2")) == Fraction(-1, 2)


# --- a published high-temperature position -------------------------------
# Mazur (2026), "A Domineering temperature counterexample": a 28-cell position
# inside an 11x8 rectangle with value {17/8 | -2*}. The hottest published
# Domineering value we are aware of, so it exercises both the value
# computation and the thermograph harder than anything else here.


def test_published_high_temperature_position_value(high_temperature_position):
    v = value(high_temperature_position, domineering.DOMINEERING)
    assert render(v) == "{17/8|-2*}"
    assert temperature(v) == Fraction(33, 16)
    assert mean(v) == Fraction(1, 16)


def test_isolated_cells_do_not_change_the_value(
    high_temperature_core, high_temperature_position
):
    """The value factors through the connected core."""
    ruleset = domineering.DOMINEERING
    assert value(high_temperature_core, ruleset) == value(
        high_temperature_position, ruleset
    )
