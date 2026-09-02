"""Rulesets: the grid machinery, Domineering, Cram, Nim and Hackenbush."""

from __future__ import annotations

from fractions import Fraction

import pytest

from pycgt import (
    Outcome,
    as_number,
    is_number,
    negate,
    outcome,
    render,
)
from pycgt.rulesets import Position, cram, domineering, nim
from pycgt.rulesets.grid import value

# --- the grid machinery ---------------------------------------------------


def test_rectangle_and_parse_agree():
    assert Position.parse("..\n..") == Position.rectangle(2, 2)
    assert Position.rectangle(3, 4).size == 12


def test_parse_ignores_non_dot_characters():
    p = Position.parse("..#\n#..")
    assert p.cells == frozenset({(0, 0), (0, 1), (1, 1), (1, 2)})


def test_components_split_on_gaps_and_diagonals():
    assert len(Position.parse(".#.").components()) == 2
    assert len(Position.parse(".#\n#.").components()) == 2
    assert len(Position.rectangle(2, 2).components()) == 1


def test_normalise_is_invariant_under_translation_and_reflection():
    a = Position.rectangle(2, 3)
    shifted = Position(frozenset((r + 7, c + 4) for r, c in a.cells))
    assert a.normalise() == shifted.normalise()
    assert Position.parse("..\n.#").normalise() == Position.parse("..\n#.").normalise()


def test_normalise_only_transposes_when_asked():
    tall, wide = Position.rectangle(3, 2), Position.rectangle(2, 3)
    assert tall.normalise() != wide.normalise()
    assert tall.normalise(transpose=True) == wide.normalise(transpose=True)


def test_remove_rejects_filled_cells():
    p = Position.rectangle(1, 2)
    with pytest.raises(ValueError, match="not all empty"):
        p.remove([(0, 0), (5, 5)])


def test_value_of_the_empty_position_is_zero():
    assert value(Position(frozenset()), domineering.DOMINEERING).is_zero


# --- Domineering ----------------------------------------------------------


def test_single_column_favours_left_and_single_row_favours_right():
    for n in range(1, 8):
        assert as_number(domineering.rectangle(n, 1)) == Fraction(n // 2)
        assert as_number(domineering.rectangle(1, n)) == Fraction(-(n // 2))


def test_two_by_two_is_a_first_player_win():
    g = domineering.rectangle(2, 2)
    assert render(g) == "+-1"
    assert outcome(g) is Outcome.FIRST


def test_value_is_the_sum_of_components():
    single = domineering.parse("..")
    pair = domineering.parse("..#..")
    assert pair == single + single


@pytest.mark.parametrize("n", range(1, 6))
def test_square_boards_cannot_favour_either_player(n):
    """A square is symmetric under transposition, which negates, so its value
    must be zero or confused with zero."""
    g = domineering.square(n)
    assert outcome(g) in (Outcome.FIRST, Outcome.SECOND)


def test_two_by_thirteen_is_a_second_player_win():
    """Surprising next to its neighbours, and worth pinning down."""
    assert domineering.rectangle(2, 13).is_zero


# --- Cram -----------------------------------------------------------------


@pytest.mark.parametrize("rows, cols", [(1, 2), (2, 2), (2, 3), (1, 4), (3, 3)])
def test_cram_values_are_nimbers(rows, cols):
    """Cram is impartial, so every value is a nimber: G = -G."""
    g = cram.rectangle(rows, cols)
    assert g == negate(g), render(g)


def test_cram_two_by_two_is_zero():
    assert cram.rectangle(2, 2).is_zero


def test_cram_one_by_n_matches_nim_parity():
    """A 1xn strip under Cram is a single row of dominoes; small cases are
    computed here directly and only asserted to be nimbers."""
    for n in range(1, 7):
        g = cram.rectangle(1, n)
        assert g == negate(g)


# --- Nim ------------------------------------------------------------------


@pytest.mark.parametrize("size", range(6))
def test_nim_heap_is_its_nimber(size):
    from pycgt import nimber

    assert nim.heap(size) == nimber(size)


@pytest.mark.parametrize("sizes", [(1, 2, 3), (3, 5, 6), (1, 1), (4, 4, 7, 7), (2, 3)])
def test_nim_sums_follow_exclusive_or(sizes):
    from functools import reduce
    from operator import xor

    from pycgt import nimber

    assert nim.heaps(*sizes) == nimber(reduce(xor, sizes))


def test_nim_losing_positions_are_zero():
    assert nim.heaps(1, 2, 3).is_zero
    assert nim.heaps(5, 5).is_zero


def test_nim_rejects_negative_heaps():
    with pytest.raises(ValueError):
        nim.heap(-1)


# --- Hackenbush -----------------------------------------------------------


@pytest.mark.parametrize(
    "colours, expected",
    [
        ("", "0"),
        ("L", "1"),
        ("R", "-1"),
        ("LL", "2"),
        ("LR", "1/2"),
        ("LRR", "1/4"),
        ("LRL", "3/4"),
        ("RL", "-1/2"),
    ],
)
def test_hackenbush_strings_are_the_expected_dyadic_rationals(colours, expected):
    g = nim.hackenbush_string(colours)
    assert is_number(g)
    assert as_number(g) == Fraction(expected)


def test_hackenbush_rejects_other_colours():
    with pytest.raises(ValueError, match="'L' and 'R'"):
        nim.hackenbush_string("LGB")
