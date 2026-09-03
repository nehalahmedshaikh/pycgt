# pycgt

[![PyPI](https://img.shields.io/pypi/v/pycgt.svg)](https://pypi.org/project/pycgt/)
[![Python versions](https://img.shields.io/pypi/pyversions/pycgt.svg)](https://pypi.org/project/pycgt/)
[![CI](https://github.com/nehalahmedshaikh/pycgt/actions/workflows/ci.yml/badge.svg)](https://github.com/nehalahmedshaikh/pycgt/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Combinatorial game theory in pure Python — exact canonical forms, thermography, and game values.**

```python
>>> from pycgt import parse, render, temperature, mean
>>> from pycgt.rulesets import domineering

>>> render(domineering.rectangle(2, 4))
'Miny(2)'
>>> temperature(domineering.rectangle(2, 3))
Fraction(5, 4)
>>> render(parse("{1|-1}") + parse("{1|-1}"))
'0'
```

`pip install pycgt`. Python 3.11+, **no dependencies**.

---

## The one idea everything rests on

Short games are **exact objects built from the empty game up**. Two values are
equal, or one is greater, or they are *confused* with each other — there is no
tolerance to set, no rounding, and no floating point anywhere. Temperatures are
`Fraction`s found by bisection on an exact dyadic grid.

The operation that makes this usable is **canonical form**. Two games of the
same value reduce to *identical* canonical forms, so structural equality
becomes value equality and comparison becomes a dictionary lookup. Every `Game`
returned by this library is canonical, which is why `==` means what you want.

## Why it exists

[CGSuite](https://www.cgsuite.org/) is the established tool in this field and
is far more complete than this. But it is a Java desktop application: not
`pip install`-able, awkward to drive from a script, and unavailable in a
notebook or in CI. Getting it to answer one batch of questions headlessly took
a from-source Maven build and a JDK version pin.

`pycgt` is for when you want game values inside ordinary Python. It has no
dependencies, so it also runs unchanged under Pyodide in a browser.

## What's here

| | |
|---|---|
| **Core** | canonical form, the partial order, disjunctive sums, negation, birthdays |
| **Numbers** | dyadic rationals both ways, Conway's simplicity rule |
| **Named values** | `*`, `^`, `v`, nimbers, switches, `tiny`, `miny` |
| **Stops** | left/right stops, confusion intervals, infinitesimality, hot/tepid tests |
| **Reduced form** | reduced canonical form, and `ish` — the infinitesimal remainder |
| **Thermography** | heating, overheating, cooling, temperature, mean value |
| **Structure** | all-small games, maximal incentives, the census of games born by day *n* |
| **Notation** | render to readable text, and parse it back |
| **Rulesets** | Domineering, Cram, Clobber, Toads-and-Frogs, Col, Snort, Nim, Blue-Red Hackenbush |
| **Reachability** | was a position arrived at by legal alternating play? with replay certificates |
| **Drawing** | thermographs as dependency-free SVG, rendered inline in notebooks |

The rulesets span four different board shapes on purpose, because each one
stresses the core differently: grids of empty cells (Domineering, Cram), grids
of coloured stones that *move* (Clobber), directed strips (Toads-and-Frogs),
and arbitrary graphs (Col, Snort). Each needs its own notion of symmetry, and
getting that wrong silently corrupts the memo table.

Games are only **partially** ordered, so `<=` and `>=` are defined but `<` and
`>` deliberately are not — `not (G <= H)` does not imply `G > H`. Use
`compare()` for the four-way answer, which includes *confused*.

```python
>>> from pycgt import compare, STAR, ZERO
>>> compare(STAR, ZERO)
<Relation.CONFUSED: '||'>
```

## A worked example

[`examples/berlekamp_1988.py`](examples/berlekamp_1988.py) reproduces
Berlekamp's *Blockbusting and Domineering* (1988) — his Table III sequences,
their period-5/saltus-1 structure, and the overheating bound from Appendix B.1 —
and checks the results against the paper.

```console
$ python examples/berlekamp_1988.py
  period 5, saltus 1: holds
  x_1 is the only non-number: 1*
  ok    G_2 = tiny-2
  ok    G_3 = +-1 + 2*tiny-2
```

## Reachability

Some authors count any finite region as a Domineering position; a stricter
reading requires the empty cells to be **reachable from a rectangle** by legal
play. A claim about, say, the maximum temperature in Domineering means
different things under the two conventions, so reachability is part of the
statement — and it is not something CGSuite answers.

```python
>>> from pycgt.rulesets import Position, domineering, reachable_from_rectangle, verify_replay
>>> board = Position.rectangle(2, 3)
>>> target = Position(board.cells - {(0, 0), (1, 0)})
>>> replay = reachable_from_rectangle(target, 2, 3, domineering.DOMINEERING)
>>> print(replay)
1 moves from 6 cells (1 Left, 0 Right)
    1. Left: (0,0) (1,0)
>>> verify_replay(replay, domineering.DOMINEERING)
True
```

The search returns a **certificate**, and `verify_replay` re-checks it from
scratch — legality, alternation, and endpoint — without trusting the search.
So a replay produced elsewhere, by another program or by hand, can be audited
here.

It works for any placement ruleset, not just Domineering. The reduction that
makes it tractable: placements never overlap, so any partition of the filled
region into legal shapes can be replayed in *any* order, and alternation
constrains only the counts.

## Correctness

The interesting values in this field are easy to get subtly wrong, so nothing
here is trusted because it looks right. The test suite validates against
**external** sources:

- **CGSuite** — canonical forms, temperatures and means of Domineering 2×n
  boards, generated by driving CGSuite 2.2 headlessly.
- **Berlekamp (1988)**, *Blockbusting and Domineering*, Appendix B.1 — his
  exact values for the 2-wide Domineering rectangles, `G₂ = tiny-2` and
  `G₃ = ±1 + 2·tiny-2`.
- **Wolfe**, via Guy's Problem 4 in *Games of No Chance* — the 4×5 board is `1`.
- **Uiterwijk**, [arXiv:1305.3257](https://arxiv.org/pdf/1305.3257) — the
  value of the 11×2 board.
- **Closed forms** — Nim sums follow exclusive-or; Hackenbush strings give the
  expected dyadic rationals; Cram values are nimbers.

- **The census** — `born_by(2)` must be exactly 22, the published count. This
  is the strictest test here: 256 raw expressions have to collapse onto 22
  values, so any error in domination or reversibility changes the number.
- **Exhaustive comparison where it's affordable** — Toads-and-Frogs was checked
  against CGSuite on *every* position of length 1 to 5, all 363.

Plus internal laws that catch real bugs: `G + (−G) = 0`, transposing a
Domineering board negates its value, `ish(G)` is *always* infinitesimal,
canonical form is idempotent, and reversing a Toads-and-Frogs strip while
swapping colours negates it.

One methodological note. Comparing our output to CGSuite's *as text* produces
false disagreements whenever the two name the same value differently. So the
tests ask **CGSuite to adjudicate equality** with our output instead. That has
twice exposed a genuine gap in our renderer rather than a phantom bug.

## Provenance

Implemented clean-room from the mathematics — *Winning Ways*, Siegel's
*Combinatorial Game Theory*, and Berlekamp (1988). CGSuite is GPL; its source
was consulted **only** for the API needed to run it as a test oracle, and none
of its implementation was used or ported. This library is MIT.

## Limitations

Honest about scope:

- **Short games only.** No loopy games, stoppers, or `on`/`off`.
- **No misère theory** and no misère quotients.
- **Slower than CGSuite**, which is a JVM program with far more optimisation.
  Expect exact Domineering values up to about 2×16 comfortably.
- **The number-temperature convention** (a number with denominator `2**k` has
  temperature `−1/2**k`) is checked against CGSuite for `0` and `1/2` only.

## Licence

MIT.
