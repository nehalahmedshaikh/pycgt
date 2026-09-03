# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — 2026-09-03

### Added

- **Reachability** (`pycgt.rulesets.reachable`): decide whether a placement-game
  position could have been arrived at from a rectangle by legal alternating
  play, and return a replay certificate. `verify_replay` re-checks a
  certificate from scratch — legality, alternation and endpoint — so replays
  produced elsewhere can be audited. Works for any ruleset whose shapes all
  cover the same number of cells.
- `partitions`, exposing the underlying constrained exact-cover search.
- A published 28-cell Domineering position of temperature 33/16 in the test
  suite, exercising the value computation, the thermograph, and the
  reachability search on a 60-cell filled region.
- **Clobber** (`pycgt.rulesets.clobber`), the first ruleset where pieces move
  and capture rather than being placed. It needs its own board type — a
  colouring rather than a set of empty cells — which generalises the library
  beyond placement games. Clobber is all-small, so every value is an
  infinitesimal. All sixteen test values were produced by CGSuite, which was
  then asked to adjudicate equality with our own output, so notation
  differences could not mask a disagreement.

- **Toads-and-Frogs** (`pycgt.rulesets.toads_and_frogs`), a partizan strip
  game and the library's third board shape: a one-dimensional word whose
  pieces have a *direction*, so neither reflection nor colour exchange alone is
  a symmetry — reversing the strip and swapping the colours is. Validated
  against CGSuite on **every** position of length 1 to 5, all 363 of them.
- **Thermograph drawing** (`pycgt.draw`): thermographs as dependency-free SVG,
  rendered inline in Jupyter. Drawn from the exact breakpoints rather than
  sampled, so the lines are where the mathematics puts them.
- **Col and Snort** (`pycgt.rulesets.graphs`), partizan colouring games on an
  arbitrary graph — a fourth board shape. The two rules differ in one word:
  Col forbids colouring next to your *own* colour, Snort next to your
  *opponent's*. Col comes out cold, Snort hot. All ten Snort values and nine
  Col values match CGSuite.
- **The census** (`pycgt.census`): every distinct game born by day *n*.
  `born_by(2)` gives **22**, matching the published sequence 1, 4, 22, 1474 —
  the most demanding test here, since 256 raw expressions must collapse onto
  exactly 22 values and any slip in domination or reversibility changes the
  count. Day 3 is refused rather than attempted; it needs `2**22` subsets a
  side.
- `is_all_small`: whether Left can move exactly when Right can, in every
  subposition. All-small implies infinitesimal but not conversely — `tiny-2`
  is the standard counterexample.
- `incentives`: the maximal Left and Right incentives, matching CGSuite's
  convention.

### Changed

- `render` now recognises `+-X` for any `X`, not just numbers: a switch whose
  Right options are exactly the negatives of its Left options prints as
  `+-{*,^}` rather than `{*,^|*,v}`, matching CGSuite. `parse` accepts the
  braced form.

## [0.1.0] — 2026-09-03

First release.

### Added

- **Core** (`pycgt.game`): `Game`, canonical form, the partial order with a
  four-way `compare`, disjunctive sums, negation, integer multiples,
  birthdays, and normal-play outcome classes.
- **Numbers and named values** (`pycgt.values`): dyadic rationals in both
  directions via Conway's simplicity rule, plus `*`, `^`, `v`, nimbers,
  switches, `plus_minus`, `tiny` and `miny`.
- **Stops** (`pycgt.stops`): left and right stops, confusion intervals, and
  finite tests for infinitesimality, hotness and tepidity.
- **Reduced canonical form** (`pycgt.reduced`): the simplest game
  infinitesimally close to a given one, and `ish` for the infinitesimal
  remainder.
- **Thermography** (`pycgt.thermal`): heating, overheating, cooling,
  temperature and mean value, all in exact arithmetic.
- **Notation** (`pycgt.notation`): rendering to readable text and parsing it
  back.
- **Rulesets** (`pycgt.rulesets`): a generic grid placement engine with
  component decomposition and symmetry-aware memoisation, instantiated for
  Domineering and Cram; plus Nim and Blue-Red Hackenbush.
- Validation against CGSuite output, Berlekamp (1988) Appendix B.1, Wolfe's
  4×5 Domineering value, and Uiterwijk's 11×2 value.
