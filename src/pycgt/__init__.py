"""pycgt: combinatorial game theory in pure Python.

Short games are exact objects built from the empty game up, so nothing here
approximates: two values are equal, or one is greater, or they are *confused*
with each other. There is no tolerance to set and no rounding.

    >>> from pycgt import parse, render
    >>> render(parse("{1|-1}") + parse("{1|-1}"))
    '0'
    >>> from pycgt.rulesets import domineering
    >>> render(domineering.rectangle(2, 4))
    'Miny(2)'
    >>> from pycgt import temperature
    >>> temperature(domineering.rectangle(2, 3))
    Fraction(5, 4)

Every :class:`Game` returned by this package is in canonical form, so ``==``
means value equality.
"""

from .game import (
    ZERO,
    Game,
    Outcome,
    Relation,
    add,
    birthday,
    canonical,
    compare,
    confused,
    equals,
    game,
    geq,
    greater,
    leq,
    multiple,
    negate,
    outcome,
)
from .notation import parse, render
from .reduced import is_reduced, ish, reduced_canonical_form
from .stops import (
    confusion_interval,
    is_hot,
    is_infinitesimal,
    is_tepid,
    left_stop,
    number_part,
    right_stop,
    stops,
)
from .thermal import cool, heat, mean, overheat, temperature, thermograph
from .values import (
    DOWN,
    STAR,
    UP,
    as_number,
    integer,
    is_number,
    miny,
    nimber,
    number,
    plus_minus,
    simplest_between,
    switch,
    tiny,
    up_multiple,
)

__version__ = "0.1.0"

__all__ = [
    # core
    "Game",
    "Outcome",
    "Relation",
    "ZERO",
    "game",
    "canonical",
    "add",
    "negate",
    "multiple",
    "birthday",
    # order
    "geq",
    "leq",
    "equals",
    "greater",
    "confused",
    "compare",
    "outcome",
    # numbers and named values
    "number",
    "integer",
    "as_number",
    "is_number",
    "simplest_between",
    "STAR",
    "UP",
    "DOWN",
    "nimber",
    "up_multiple",
    "switch",
    "plus_minus",
    "tiny",
    "miny",
    # stops
    "left_stop",
    "right_stop",
    "stops",
    "confusion_interval",
    "is_infinitesimal",
    "is_hot",
    "is_tepid",
    "number_part",
    # reduced canonical form
    "reduced_canonical_form",
    "ish",
    "is_reduced",
    # thermography
    "heat",
    "overheat",
    "cool",
    "temperature",
    "mean",
    "thermograph",
    # notation
    "render",
    "parse",
]
