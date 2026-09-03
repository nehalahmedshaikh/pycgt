"""The census: how many distinct games are born by day ``n``?

Build every game whose options are drawn from the games already born, reduce
each to canonical form, and count what survives. The answer is famous:

===  ==========================
day  distinct games born by then
===  ==========================
0    1
1    4
2    22
3    1474
===  ==========================

That sequence is a demanding end-to-end test. Getting 22 on day 2 requires
canonical form, the partial order, domination and reversibility all to be
right at once: 256 raw expressions collapse onto 22 values, and any error in
the reduction shows up immediately as a different count.

Day 3 is out of reach by this method -- its options range over subsets of the
22 day-2 games, so there are ``2**22`` choices on each side. The known value
of 1474 is recorded here for reference, not computed.

>>> [len(born_by(n)) for n in range(3)]
[1, 4, 22]
"""

from __future__ import annotations

import itertools
from functools import cache

from .game import ZERO, Game, canonical

__all__ = ["CENSUS", "born_by", "born_on"]

#: The published sequence, for reference and for testing what we can reach.
CENSUS: dict[int, int] = {0: 1, 1: 4, 2: 22, 3: 1474}

#: Beyond this the subset enumeration is hopeless, so refuse rather than hang.
_FEASIBLE_DAY = 2


@cache
def born_by(day: int) -> frozenset[Game]:
    """Every distinct game born on or before ``day``, in canonical form.

    Raises :class:`ValueError` past day 2, where the enumeration would need
    ``2**22`` subsets per side. The count for day 3 is in :data:`CENSUS`.
    """
    if day < 0:
        raise ValueError("there is no day before day 0")
    if day == 0:
        return frozenset({ZERO})
    if day > _FEASIBLE_DAY:
        raise ValueError(
            f"day {day} needs 2**{len(born_by(_FEASIBLE_DAY))} subsets per side; "
            f"see CENSUS for the published counts"
        )

    earlier = sorted(born_by(day - 1), key=str)
    subsets = [
        frozenset(combo)
        for size in range(len(earlier) + 1)
        for combo in itertools.combinations(earlier, size)
    ]
    return frozenset(
        canonical(Game(left, right)) for left in subsets for right in subsets
    )


def born_on(day: int) -> frozenset[Game]:
    """The games born exactly on ``day``: new arrivals, not cumulative.

    >>> sorted(str(g) for g in born_on(1))
    ['*', '-1', '1']
    """
    if day == 0:
        return frozenset({ZERO})
    return born_by(day) - born_by(day - 1)
