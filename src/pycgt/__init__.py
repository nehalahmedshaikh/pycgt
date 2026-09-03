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

from . import impartial
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
    incentives,
    is_all_small,
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
    is_number_tiny,
    is_numberish,
    is_tepid,
    left_stop,
    number_part,
    right_stop,
    stops,
)
from .structure import (
    conjunctive_sum,
    follower_count,
    followers,
    is_even_tempered,
    is_idempotent,
    is_odd_tempered,
    selective_sum,
    stop_count,
)
from .thermal import cool, freeze, heat, mean, overheat, temperature, thermograph
from .values import (
    DOWN,
    STAR,
    UP,
    as_miny,
    as_nimber,
    as_number,
    as_tiny,
    as_up_multiple,
    integer,
    is_integer,
    is_nimber,
    is_number,
    miny,
    nimber,
    norton_product,
    number,
    plus_minus,
    simplest_between,
    switch,
    tiny,
    up_multiple,
)

__version__ = "0.3.0"

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
    "incentives",
    "is_all_small",
    # numbers and named values
    "number",
    "integer",
    "as_number",
    "is_number",
    "is_integer",
    "simplest_between",
    "STAR",
    "UP",
    "DOWN",
    "nimber",
    "as_nimber",
    "is_nimber",
    "up_multiple",
    "as_up_multiple",
    "switch",
    "plus_minus",
    "tiny",
    "miny",
    "as_tiny",
    "as_miny",
    "norton_product",
    # stops
    "left_stop",
    "right_stop",
    "stops",
    "confusion_interval",
    "is_infinitesimal",
    "is_hot",
    "is_tepid",
    "is_numberish",
    "is_number_tiny",
    "number_part",
    # structure
    "stop_count",
    "is_even_tempered",
    "is_odd_tempered",
    "followers",
    "follower_count",
    "is_idempotent",
    "conjunctive_sum",
    "selective_sum",
    # reduced canonical form
    "reduced_canonical_form",
    "ish",
    "is_reduced",
    # thermography
    "heat",
    "overheat",
    "cool",
    "freeze",
    "temperature",
    "mean",
    "thermograph",
    # notation
    "render",
    "parse",
    # impartial games and misère play, kept as a module because misère needs
    # its own uncanonicalised game type and its own `add`
    "impartial",
]
