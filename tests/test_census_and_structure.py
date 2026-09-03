"""The census, all-small games, and incentives.

The census is the deepest test in the suite. Getting 22 on day 2 needs
canonical form, the partial order, domination and reversibility all correct at
once: 256 raw expressions must collapse onto exactly 22 values, and any slip in
the reduction changes the count.
"""

from __future__ import annotations

import pytest

from pycgt import (
    DOWN,
    STAR,
    UP,
    ZERO,
    incentives,
    integer,
    is_all_small,
    is_infinitesimal,
    miny,
    nimber,
    number,
    parse,
    plus_minus,
    render,
    tiny,
    up_multiple,
)
from pycgt.census import CENSUS, born_by, born_on
from pycgt.rulesets import clobber, domineering, toads_and_frogs

# --- census ---------------------------------------------------------------


@pytest.mark.parametrize("day", [0, 1, 2])
def test_census_matches_the_published_counts(day):
    assert len(born_by(day)) == CENSUS[day]


def test_day_one_is_exactly_zero_one_minus_one_and_star():
    assert born_by(1) == {ZERO, integer(1), integer(-1), STAR}


def test_born_on_excludes_the_earlier_days():
    assert born_on(0) == {ZERO}
    assert born_on(1) == {integer(1), integer(-1), STAR}
    assert len(born_on(2)) == CENSUS[2] - CENSUS[1]


def test_each_day_contains_the_previous_one():
    assert born_by(0) < born_by(1) < born_by(2)


def test_birthdays_agree_with_the_day_they_appear():
    for day in (0, 1, 2):
        for g in born_on(day):
            assert g.birthday == day, render(g)


def test_the_census_is_closed_under_negation():
    for day in (0, 1, 2):
        games = born_by(day)
        assert {-g for g in games} == games


def test_day_three_is_refused_rather_than_attempted():
    """2**22 subsets per side; the published count is recorded instead."""
    with pytest.raises(ValueError, match="subsets per side"):
        born_by(3)
    assert CENSUS[3] == 1474


def test_negative_days_are_rejected():
    with pytest.raises(ValueError, match="no day before"):
        born_by(-1)


# --- all-small ------------------------------------------------------------


@pytest.mark.parametrize(
    "game, expected",
    [
        (ZERO, True),
        (STAR, True),
        (UP, True),
        (DOWN, True),
        (nimber(3), True),
        (up_multiple(2), True),
        (integer(1), False),
        (number("1/2"), False),
        (plus_minus(1), False),
        (tiny(2), False),
        (miny(2), False),
    ],
)
def test_is_all_small_matches_cgsuite(game, expected):
    assert is_all_small(game) is expected


def test_all_small_implies_infinitesimal():
    for day in (0, 1, 2):
        for g in born_by(day):
            if is_all_small(g):
                assert is_infinitesimal(g), render(g)


def test_infinitesimal_does_not_imply_all_small():
    """tiny-2 is the standard counterexample: the number -2 sits inside it."""
    assert is_infinitesimal(tiny(2))
    assert not is_all_small(tiny(2))


def test_clobber_is_all_small_and_toads_and_frogs_is_not():
    assert is_all_small(clobber.parse("xoxo"))
    assert not is_all_small(toads_and_frogs.value("t."))


def test_domineering_is_not_all_small():
    assert not is_all_small(domineering.rectangle(2, 2))


# --- incentives -----------------------------------------------------------


def rendered(game) -> set[str]:
    return {render(i) for i in incentives(game)}


@pytest.mark.parametrize(
    "text, expected",
    [
        ("0", set()),
        ("1", {"-1"}),
        ("1/2", {"-1/2"}),
        ("*", {"*"}),
        ("^", {"^*"}),
        ("+-1", {"{2|0}"}),
        ("+-2", {"{4|0}"}),
        ("{2|1}", {"{1|0}"}),
    ],
)
def test_incentives_match_cgsuite(text, expected):
    assert rendered(parse(text)) == expected


def test_equal_incentives_are_not_cancelled_against_each_other():
    """Regression. Both incentives of 1/2 equal -1/2 but arrive as distinct
    objects, from 0 - 1/2 and from 1/2 - 1. A maximality filter comparing by
    identity lets each eliminate the other and returns nothing."""
    assert rendered(number("1/2")) == {"-1/2"}
    assert rendered(parse("{2|1}")) == {"{1|0}"}


def test_a_game_with_no_options_has_no_incentives():
    assert incentives(ZERO) == frozenset()


def test_only_maximal_incentives_are_kept():
    """Up has Left incentive v and Right incentive ^*, and ^* dominates."""
    assert rendered(UP) == {"^*"}


def test_incentives_of_a_number_are_negative():
    """Moving in a number always loses ground, which is why numbers are cold."""
    for text in ("1", "1/2", "-3/4", "2"):
        for incentive in incentives(parse(text)):
            assert incentive <= ZERO, text
