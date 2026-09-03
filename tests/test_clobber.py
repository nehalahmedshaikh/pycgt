"""Clobber, the library's first non-placement ruleset.

Every expected value below was produced by CGSuite and confirmed by asking
CGSuite to adjudicate equality with our own output, so notation differences
(its ``v[2]`` against our ``{*|v}``) cannot hide a disagreement.
"""

from __future__ import annotations

import pytest

from pycgt import (
    DOWN,
    STAR,
    UP,
    is_infinitesimal,
    negate,
    render,
)
from pycgt.rulesets import clobber
from pycgt.rulesets.clobber import Board

#: board -> value, as rendered by pycgt and cross-checked against CGSuite.
CGSUITE_VALUES = {
    "x": "0",
    "xo": "*",
    "xxo": "^",
    "xoo": "v",
    "xoxo": "+-{*,^}",
    "xoox": "0",
    "xxoo": "0",
    "xoxox": "{*|v}",
    "xoxoxo": "0",
    "xxooxx": "0",
    "xo|ox": "*",
    "xx|oo": "0",
    "xo|xo": "0",
    "xox|oxo": "0",
    "xxo|oxx": "^",
    "xoxo|oxox": "*",
}


@pytest.mark.parametrize("text, expected", sorted(CGSUITE_VALUES.items()))
def test_values_match_cgsuite(text, expected):
    assert render(clobber.parse(text)) == expected


# --- structural properties -----------------------------------------------


@pytest.mark.parametrize("text", sorted(CGSUITE_VALUES))
def test_every_value_is_infinitesimal(text):
    """Clobber is all-small: Left can move exactly when Right can."""
    assert is_infinitesimal(clobber.parse(text))


@pytest.mark.parametrize(
    "text", ["xo", "xxo", "xoxo", "xoxox", "xo|ox", "xxo|oxx", "xoxo|oxox"]
)
def test_swapping_the_colours_negates(text):
    """Exchanging x and o exchanges the players, so the value negates."""
    swapped = text.replace("x", "?").replace("o", "x").replace("?", "o")
    assert clobber.parse(swapped) == negate(clobber.parse(text))


def test_a_lone_stone_has_no_moves():
    for text in ("x", "o", "xx", "oo", "x.o"):
        assert clobber.parse(text).is_zero


def test_a_single_adjacent_pair_is_star():
    """Whoever moves takes the other's stone and then wins."""
    assert clobber.parse("xo") == STAR
    assert clobber.parse("ox") == STAR
    assert clobber.parse("x\no") == STAR


def test_two_extra_friendly_stones_give_up_and_down():
    assert clobber.parse("xxo") == UP
    assert clobber.parse("xoo") == DOWN


def test_separated_groups_add():
    single = clobber.parse("xo")
    assert clobber.parse("xo.ox") == single + single
    assert clobber.parse("xo.ox").is_zero  # * + * = 0


# --- the board type -------------------------------------------------------


def test_board_rejects_a_cell_holding_both_colours():
    with pytest.raises(ValueError, match="both players"):
        Board(frozenset({(0, 0)}), frozenset({(0, 0)}))


def test_board_parses_and_renders_round_trip():
    b = clobber.board("xo|ox")
    assert str(b) == "xo\nox"
    assert b.size == 4


def test_board_rejects_unknown_characters():
    with pytest.raises(ValueError, match=r"expected 'x', 'o' or '\.'"):
        clobber.board("xyz")


def test_components_split_on_gaps():
    assert len(clobber.board("xo.ox").components()) == 2
    assert len(clobber.board("xoox").components()) == 1


def test_diagonal_stones_do_not_interact():
    """A capture is orthogonal, so diagonal neighbours are independent."""
    b = clobber.board("x.\n.o")
    assert len(b.components()) == 2
    assert clobber.value(b).is_zero


def test_moves_capture_and_advance():
    b = clobber.board("xo")
    after = b.moves("x")
    assert len(after) == 1
    assert after[0].left == frozenset({(0, 1)})
    assert after[0].right == frozenset()


def test_no_moves_without_an_adjacent_enemy():
    b = clobber.board("xx")
    assert b.moves("x") == []
    assert b.moves("o") == []


def test_normalise_is_invariant_under_the_dihedral_symmetries():
    """Both players move in all directions, so rotating or reflecting the
    board leaves the value unchanged."""
    horizontal = clobber.board("xoxo")
    vertical = clobber.board("x\no\nx\no")
    assert horizontal.normalise() == vertical.normalise()
    assert clobber.value(horizontal) == clobber.value(vertical)


def test_normalise_does_not_swap_colours():
    """Colour exchange negates, so it must not be normalised away."""
    assert clobber.board("xxo").normalise() != clobber.board("oox").normalise()
