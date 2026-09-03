"""Toads-and-Frogs: a partizan strip game.

Our implementation was compared against CGSuite on **every** position of length
1 to 5 -- 363 in all -- and agreed on all of them, textually. Pinned below is
one representative for each of the 26 distinct values that occur in that range,
which covers every value class without a 363-line literal.
"""

from __future__ import annotations

import itertools

import pytest

from pycgt import integer, negate, render
from pycgt.rulesets import toads_and_frogs as taf

#: One position per distinct value occurring at length <= 5, from CGSuite.
CGSUITE_VALUES = {
    "t": "0",
    "t.": "1",
    "tt.": "2",
    "ttt.": "3",
    "tt..": "4",
    "tt.t.": "5",
    "ttt..": "6",
    ".f": "-1",
    ".ff": "-2",
    ".fff": "-3",
    "..ff": "-4",
    ".f.ff": "-5",
    "..fff": "-6",
    "t.f": "*",
    "t.tff": "^",
    "ttf.f": "v",
    "t.tf": "1/2",
    "tf.f": "-1/2",
    "tt.f.": "3/2",
    ".t.ff": "-3/2",
    "tt.tf": "1*",
    "tf.ff": "-1*",
    "tt.f": "{1/2|0}",
    "t.ff": "{0|-1/2}",
    "ttt.f": "{1*|0}",
    "t.fff": "{0|-1*}",
}


@pytest.mark.parametrize("board, expected", sorted(CGSUITE_VALUES.items()))
def test_values_match_cgsuite(board, expected):
    assert render(taf.value(board)) == expected


def test_all_twenty_six_value_classes_are_covered():
    """Guards the table against silently shrinking."""
    assert len(set(CGSUITE_VALUES.values())) == 26


# --- the rules, checked one at a time -------------------------------------


def test_a_toad_steps_right_into_an_empty_square():
    assert taf.left_moves("t.") == (".t",)


def test_a_frog_steps_left_into_an_empty_square():
    assert taf.right_moves(".f") == ("f.",)


def test_pieces_never_move_backwards():
    assert taf.left_moves(".t") == ()
    assert taf.right_moves("f.") == ()


def test_a_toad_jumps_over_one_frog():
    assert taf.left_moves("tf.") == (".ft",)


def test_a_frog_jumps_over_one_toad():
    assert taf.right_moves(".tf") == ("ft.",)


def test_a_piece_does_not_jump_its_own_colour():
    """tt. offers only the front toad's step, never a jump over a toad."""
    assert taf.left_moves("tt.") == ("t.t",)


def test_a_jump_needs_the_landing_square_empty():
    assert taf.left_moves("tff") == ()
    assert taf.right_moves("ttf") == ()


def test_a_jump_spans_exactly_one_piece():
    """A toad cannot clear two frogs at once."""
    assert taf.left_moves("tff.") == ()


def test_face_to_face_pieces_are_stuck():
    assert taf.left_moves("tf") == ()
    assert taf.right_moves("tf") == ()
    assert taf.value("tf").is_zero


# --- symmetry -------------------------------------------------------------


def test_reverse_and_swap_negates_exhaustively():
    """Reversing alone is not a symmetry, since pieces have a direction, but
    reversing and exchanging the colours negates the value. Checked on every
    position up to length 4."""
    for length in range(1, 5):
        for combo in itertools.product("tf.", repeat=length):
            board = "".join(combo)
            assert taf.value(taf.reverse_and_swap(board)) == negate(taf.value(board)), (
                board
            )


def test_reverse_and_swap_is_an_involution():
    for board in ("tt.f", "t.f", ".ttf.", "tf"):
        assert taf.reverse_and_swap(taf.reverse_and_swap(board)) == board


def test_reverse_and_swap_example():
    assert taf.reverse_and_swap("tt.f") == "t.ff"


# --- values are not confined to infinitesimals ---------------------------


def test_a_free_toad_is_worth_a_whole_move():
    """Unlike Clobber, this game is not all-small: with no frogs, Right has no
    move at all and the value is a positive integer."""
    assert taf.value("t.") == integer(1)
    assert taf.value("t..") == integer(2)
    assert taf.value("t...") == integer(3)


def test_an_empty_or_frogless_strip_is_zero_when_nobody_can_move():
    for board in ("t", "f", ".", "", "tt", "ff"):
        assert taf.value(board).is_zero


# --- input handling -------------------------------------------------------


def test_rejects_unknown_characters():
    with pytest.raises(ValueError, match="expected only"):
        taf.value("txf")


def test_table_helper_returns_every_position_of_a_length():
    values = taf.table(2)
    assert len(values) == 9
    assert values["t."] == "1"
    assert values["tf"] == "0"
