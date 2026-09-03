"""Col and Snort on graphs.

Every expected value came from CGSuite. Snort is the informative one -- its
values on paths run through ``*``, ``+-1``, ``+-2``, ``+-{2|1}`` and
``+-{1,{3|0}}`` -- while Col is 0 on every symmetric board tested, which still
exercises the machinery but discriminates less.
"""

from __future__ import annotations

import pytest

from pycgt import is_all_small, is_number, negate, render
from pycgt.rulesets.graphs import COL, SNORT, Colouring, Graph, uncoloured, value

SNORT_PATHS = {1: "*", 2: "+-1", 3: "+-2", 4: "+-{2|1}", 5: "+-{1,{3|0}}", 6: "*"}
SNORT_CYCLES = {3: "+-2", 4: "0", 5: "*", 6: "0"}
COL_PATHS = {1: "*", 2: "0", 3: "0", 4: "0", 5: "0"}
COL_CYCLES = {3: "0", 4: "0", 5: "0", 6: "0"}


@pytest.mark.parametrize("order, expected", sorted(SNORT_PATHS.items()))
def test_snort_on_paths_matches_cgsuite(order, expected):
    assert render(value(uncoloured(Graph.path(order)), SNORT)) == expected


@pytest.mark.parametrize("order, expected", sorted(SNORT_CYCLES.items()))
def test_snort_on_cycles_matches_cgsuite(order, expected):
    assert render(value(uncoloured(Graph.cycle(order)), SNORT)) == expected


@pytest.mark.parametrize("order, expected", sorted(COL_PATHS.items()))
def test_col_on_paths_matches_cgsuite(order, expected):
    assert render(value(uncoloured(Graph.path(order)), COL)) == expected


@pytest.mark.parametrize("order, expected", sorted(COL_CYCLES.items()))
def test_col_on_cycles_matches_cgsuite(order, expected):
    assert render(value(uncoloured(Graph.cycle(order)), COL)) == expected


# --- the rules differ in exactly one word --------------------------------


def test_col_forbids_your_own_colour_next_door():
    graph = Graph.path(2)
    after = Colouring(graph, left=frozenset({0}))
    assert not after.can_colour(1, "Left", COL)
    assert after.can_colour(1, "Right", COL)


def test_snort_forbids_your_opponents_colour_next_door():
    graph = Graph.path(2)
    after = Colouring(graph, left=frozenset({0}))
    assert after.can_colour(1, "Left", SNORT)
    assert not after.can_colour(1, "Right", SNORT)


def test_a_coloured_vertex_cannot_be_recoloured():
    graph = Graph.path(2)
    after = Colouring(graph, left=frozenset({0}))
    assert not after.can_colour(0, "Right", SNORT)
    assert not after.can_colour(0, "Left", SNORT)


def test_an_isolated_vertex_is_star_under_both_rules():
    """Either player takes it, after which nobody can move."""
    for rule in (COL, SNORT):
        assert render(value(uncoloured(Graph.path(1)), rule)) == "*"


# --- structure ------------------------------------------------------------


def test_col_values_are_cold_and_snort_values_are_not():
    """Col comes out a number or a number plus star; Snort runs hot."""
    col = value(uncoloured(Graph.path(4)), COL)
    snort = value(uncoloured(Graph.path(4)), SNORT)
    assert is_number(col)
    assert not is_number(snort)


def test_neither_game_is_all_small():
    """Colouring can hand one player a free move, unlike Clobber."""
    assert not is_all_small(value(uncoloured(Graph.path(3)), SNORT))


def test_swapping_the_colours_negates():
    for order in (2, 3, 4):
        graph = Graph.path(order)
        one_sided = Colouring(graph, left=frozenset({0}))
        mirrored = Colouring(graph, right=frozenset({0}))
        for rule in (COL, SNORT):
            assert value(one_sided, rule) == negate(value(mirrored, rule))


def test_disjoint_components_add():
    """Two separate edges are worth twice one edge."""
    single = value(uncoloured(Graph.path(2)), SNORT)
    doubled = Graph.of(4, [(0, 1), (2, 3)])
    assert value(uncoloured(doubled), SNORT) == single + single


def test_an_empty_graph_is_zero():
    assert value(uncoloured(Graph.of(0, [])), SNORT).is_zero


# --- the graph type -------------------------------------------------------


def test_path_and_cycle_have_the_expected_sizes():
    assert Graph.path(4).order == 4
    assert len(Graph.path(4).edges) == 3
    assert len(Graph.cycle(4).edges) == 4
    assert len(Graph.complete(4).edges) == 6
    assert len(Graph.star(3).edges) == 3


def test_neighbours():
    assert Graph.path(3).neighbours(1) == frozenset({0, 2})
    assert Graph.path(3).neighbours(0) == frozenset({1})
    assert Graph.cycle(3).neighbours(0) == frozenset({1, 2})


def test_components_split_a_disjoint_union():
    graph = Graph.of(4, [(0, 1), (2, 3)])
    assert len(graph.components()) == 2
    assert len(Graph.path(4).components()) == 1


def test_a_cycle_needs_three_vertices():
    with pytest.raises(ValueError, match="at least three"):
        Graph.cycle(2)


def test_edges_must_join_two_known_vertices():
    with pytest.raises(ValueError, match="unknown vertex"):
        Graph(frozenset({0}), frozenset({frozenset({0, 5})}))
    with pytest.raises(ValueError, match="two distinct"):
        Graph(frozenset({0}), frozenset({frozenset({0})}))


def test_a_vertex_cannot_carry_both_colours():
    with pytest.raises(ValueError, match="both colours"):
        Colouring(Graph.path(2), frozenset({0}), frozenset({0}))


def test_colouring_renders_readably():
    position = Colouring(Graph.path(3), left=frozenset({0}), right=frozenset({2}))
    assert str(position) == "0L 1. 2R"
    assert position.uncoloured == frozenset({1})
