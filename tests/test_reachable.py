"""Reachability: was a position arrived at by legal alternating play?

Small hand-checkable cases, adversarial cases for the verifier, and one large
published position as a stress test.
"""

from __future__ import annotations

import pytest

from pycgt.rulesets import Position, cram, domineering
from pycgt.rulesets.reachable import (
    Move,
    Replay,
    partitions,
    reachable_from_rectangle,
    verify_replay,
)

DOM = domineering.DOMINEERING


# --- the basics -----------------------------------------------------------


def test_a_full_rectangle_is_reachable_by_doing_nothing():
    board = Position.rectangle(3, 3)
    replay = reachable_from_rectangle(board, 3, 3, DOM)
    assert replay is not None
    assert replay.moves == ()
    assert verify_replay(replay, DOM)


def test_one_domino_removed_is_reachable():
    """A 2x3 board with one vertical domino taken out: exactly one Left move."""
    board = Position.rectangle(2, 3)
    target = Position(board.cells - frozenset({(0, 0), (1, 0)}))
    replay = reachable_from_rectangle(target, 2, 3, DOM, first="Left")
    assert replay is not None
    assert len(replay.moves) == 1
    assert replay.moves[0].player == "Left"
    assert verify_replay(replay, DOM)


def test_a_single_right_move_is_reachable():
    board = Position.rectangle(2, 3)
    target = Position(board.cells - frozenset({(0, 0), (0, 1)}))
    replay = reachable_from_rectangle(target, 2, 3, DOM, first="Right")
    assert replay is not None
    assert len(replay.moves) == 1
    assert replay.moves[0].player == "Right"
    assert verify_replay(replay, DOM)


def test_a_left_shaped_hole_is_unreachable_for_left_only_play():
    """A horizontal gap cannot be made by a vertical domino."""
    board = Position.rectangle(2, 3)
    target = Position(board.cells - frozenset({(0, 0), (0, 1)}))
    assert reachable_from_rectangle(target, 2, 3, DOM, first="Left") is None


def test_odd_number_of_filled_cells_is_unreachable():
    """Dominoes cover two cells, so an odd filled count cannot be tiled."""
    board = Position.rectangle(2, 2)
    target = Position(frozenset(list(board.cells)[:3]))  # one cell filled
    assert reachable_from_rectangle(target, 2, 2, DOM) is None


def test_target_outside_the_board_is_unreachable():
    target = Position.parse("..\n..")
    assert reachable_from_rectangle(target, 1, 1, DOM) is None


def test_alternation_counts_are_balanced():
    """An even number of moves splits evenly between the players."""
    target = Position(
        Position.rectangle(4, 4).cells
        - Position.parse("..\n..").cells
        - frozenset({(2, 2), (2, 3), (3, 2), (3, 3)})
    )
    replay = reachable_from_rectangle(target, 4, 4, DOM)
    if replay is not None:
        counts = replay.counts()
        assert abs(counts["Left"] - counts["Right"]) <= 1


@pytest.mark.parametrize("first", ["Left", "Right"])
def test_first_player_is_respected(first):
    board = Position.rectangle(4, 4)
    target = Position(board.cells - frozenset({(0, 0), (1, 0), (0, 1), (0, 2)}))
    replay = reachable_from_rectangle(target, 4, 4, DOM, first=first)
    if replay is not None:
        assert replay.moves[0].player == first
        assert verify_replay(replay, DOM)


# --- the verifier must actually reject things -----------------------------


def test_verifier_rejects_a_non_alternating_replay():
    board = Position.rectangle(4, 4)
    bad = Replay(
        start=board,
        moves=(
            Move("Left", ((0, 0), (1, 0))),
            Move("Left", ((0, 1), (1, 1))),
        ),
        target=Position(board.cells - frozenset({(0, 0), (1, 0), (0, 1), (1, 1)})),
    )
    assert not verify_replay(bad, DOM)


def test_verifier_rejects_overlapping_placements():
    board = Position.rectangle(4, 4)
    bad = Replay(
        start=board,
        moves=(
            Move("Left", ((0, 0), (1, 0))),
            Move("Right", ((0, 0), (0, 1))),
        ),
        target=Position(board.cells - frozenset({(0, 0), (1, 0), (0, 1)})),
    )
    assert not verify_replay(bad, DOM)


def test_verifier_rejects_the_wrong_shape_for_the_player():
    """Left plays vertically; a horizontal domino is not Left's to play."""
    board = Position.rectangle(4, 4)
    bad = Replay(
        start=board,
        moves=(Move("Left", ((0, 0), (0, 1))),),
        target=Position(board.cells - frozenset({(0, 0), (0, 1)})),
    )
    assert not verify_replay(bad, DOM)


def test_verifier_rejects_a_wrong_endpoint():
    board = Position.rectangle(4, 4)
    bad = Replay(
        start=board,
        moves=(Move("Left", ((0, 0), (1, 0))),),
        target=board,  # nothing removed, but a move was played
    )
    assert not verify_replay(bad, DOM)


def test_verifier_accepts_what_the_search_produces():
    for rows, cols in [(3, 3), (4, 4), (2, 5)]:
        board = Position.rectangle(rows, cols)
        target = Position(board.cells - frozenset({(0, 0), (1, 0), (0, 1), (0, 2)}))
        replay = reachable_from_rectangle(target, rows, cols, DOM)
        if replay is not None:
            assert verify_replay(replay, DOM), f"{rows}x{cols}"


# --- partitions -----------------------------------------------------------


def test_partitions_respects_the_requested_counts():
    region = Position.rectangle(2, 2).cells
    both = partitions(region, DOM, left_count=1, right_count=1, limit=5)
    assert both == []  # a 2x2 splits into two verticals or two horizontals
    verticals = partitions(region, DOM, left_count=2, right_count=0, limit=5)
    assert len(verticals) == 1
    horizontals = partitions(region, DOM, left_count=0, right_count=2, limit=5)
    assert len(horizontals) == 1


def test_partitions_returns_nothing_for_an_untileable_region():
    lonely = frozenset({(0, 0)})
    assert partitions(lonely, DOM, 1, 0, limit=1) == []


# --- works for other rulesets too ----------------------------------------


def test_reachability_applies_to_cram():
    """Both players have both orientations, so more targets are reachable."""
    board = Position.rectangle(2, 2)
    target = Position(board.cells - frozenset({(0, 0), (0, 1)}))
    replay = reachable_from_rectangle(target, 2, 2, cram.CRAM)
    assert replay is not None
    assert verify_replay(replay, cram.CRAM)


# --- a large published position, as a stress test -------------------------
# Its value lives in test_published_values.py; here it exercises the search on
# a 60-cell filled region under a balanced-count constraint.


def test_search_scales_to_a_sixty_cell_filled_region(high_temperature_position):
    """28 empty cells in an 11x8 board leaves 30 dominoes to place."""
    assert high_temperature_position.size == 28
    replay = reachable_from_rectangle(
        high_temperature_position, 8, 11, DOM, first="Left"
    )
    assert replay is not None, "no legal replay found"
    assert len(replay.moves) == 30
    assert replay.counts() == {"Left": 15, "Right": 15}
    assert verify_replay(replay, DOM), "the replay we found does not audit"


def test_the_published_position_has_three_components(high_temperature_position):
    """A connected core plus two isolated cells."""
    assert len(high_temperature_position.components()) == 3
