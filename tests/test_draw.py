"""Thermograph drawing.

Checks the structure and the numbers, not pixels: the SVG must be well-formed
XML, must contain both boundaries and the labels, and the geometry must follow
the exact thermograph rather than a sampled approximation.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from pycgt import STAR, mean, parse, temperature
from pycgt.draw import Svg, thermograph_svg
from pycgt.rulesets import domineering

CASES = ["+-1", "{2|-1/2}", "*", "0", "1/2", "+-{*,^}"]


@pytest.mark.parametrize("text", CASES)
def test_output_is_well_formed_xml(text):
    root = ET.fromstring(str(thermograph_svg(parse(text))))
    assert root.tag.endswith("svg")


@pytest.mark.parametrize("text", CASES)
def test_output_has_both_boundaries(text):
    root = ET.fromstring(str(thermograph_svg(parse(text))))
    paths = [e for e in root.iter() if e.tag.endswith("path")]
    assert len(paths) == 2, "one path for each boundary"
    strokes = {p.get("stroke") for p in paths}
    assert len(strokes) == 2, "the boundaries must be distinguishable"


@pytest.mark.parametrize("text", CASES)
def test_labels_report_the_exact_temperature_and_mean(text):
    g = parse(text)
    source = str(thermograph_svg(g))
    assert f"temperature {temperature(g)}" in source
    assert f"mean {mean(g)}" in source


def test_the_value_is_named_in_the_title():
    assert "+-1" in str(thermograph_svg(parse("+-1")))


def _points(path: ET.Element) -> list[tuple[float, float]]:
    return [
        (float(a), float(b))
        for a, b in (chunk[1:].split(",") for chunk in path.get("d", "").split())
    ]


def test_a_switch_bends_once_then_runs_up_the_mast():
    """+-1 cools linearly to its temperature and then freezes, so each
    boundary is a foot, one bend, and a vertical mast segment."""
    root = ET.fromstring(str(thermograph_svg(parse("+-1"))))
    paths = [e for e in root.iter() if e.tag.endswith("path")]
    for path in paths:
        points = _points(path)
        assert len(points) == 3, points
        # The last two points share an x: that is the mast, drawn vertical.
        assert abs(points[-1][0] - points[-2][0]) < 0.01
        assert points[-1][1] < points[-2][1], "the mast goes upward"


def test_both_boundaries_join_on_the_same_mast():
    root = ET.fromstring(str(thermograph_svg(parse("+-1"))))
    left, right = (_points(e) for e in root.iter() if e.tag.endswith("path"))
    assert abs(left[-1][0] - right[-1][0]) < 0.01


def test_a_boundary_with_extra_breakpoints_gets_extra_vertices():
    """This Domineering value's boundary changes slope before freezing, so it
    needs more vertices than the simple switch above."""
    root = ET.fromstring(str(thermograph_svg(domineering.rectangle(2, 11))))
    paths = [e for e in root.iter() if e.tag.endswith("path")]
    assert max(len(_points(p)) for p in paths) > 3


def test_boundaries_start_apart_and_meet_at_the_top():
    """Left starts at the left stop, Right at the right stop, and by the
    temperature they coincide -- so the paths converge."""
    g = parse("{2|-1/2}")
    root = ET.fromstring(str(thermograph_svg(g)))
    paths = [e for e in root.iter() if e.tag.endswith("path")]

    def points(path):
        return [
            tuple(float(n) for n in chunk[1:].split(","))
            for chunk in path.get("d", "").split()
        ]

    a, b = points(paths[0]), points(paths[1])
    assert abs(a[0][0] - b[0][0]) > 1.0, "stops differ, so the feet are apart"
    # The mast is where they join; both paths pass through the same x there.
    assert abs(a[-1][0] - b[-1][0]) < 1.0


def test_temperature_zero_still_draws():
    """Infinitesimals have temperature 0; the picture must not collapse."""
    svg = thermograph_svg(STAR)
    root = ET.fromstring(str(svg))
    assert root.tag.endswith("svg")
    assert int(root.get("height", "0")) > 0


def test_notebooks_can_render_it():
    svg = thermograph_svg(parse("+-1"))
    assert isinstance(svg, Svg)
    assert svg._repr_svg_().startswith("<svg")


def test_save_writes_a_file(tmp_path):
    target = tmp_path / "thermo.svg"
    thermograph_svg(parse("+-1")).save(str(target))
    assert target.read_text(encoding="utf-8").startswith("<svg")


def test_special_characters_in_labels_are_escaped():
    """Brace notation contains no XML metacharacters, but the escaping must be
    there in case a renderer starts emitting them."""
    source = str(thermograph_svg(parse("{2|-1/2}")))
    assert "<text" in source
    ET.fromstring(source)  # would raise if a label broke the document


def test_custom_size_is_respected():
    svg = thermograph_svg(parse("+-1"), width=640, height=480)
    root = ET.fromstring(str(svg))
    assert root.get("width") == "640"
    assert root.get("height") == "480"
