# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **The CGSuite oracle is now part of the repository** (`tools/cgsuite/`): a
  headless driver and a build script, with every non-obvious step recorded.
  CGSuite itself is not vendored — it is GPL and this library is MIT — so the
  script clones it into a git-ignored directory. Every expected value in the
  test suite traces back to this harness, which previously existed only in a
  scratch directory.
- **Benchmarks** (`benchmarks/run.py`), so performance claims are reproducible.
  Reports wall-clock time alongside exact work counters taken from the memo
  tables, because timings move with machine load while counters do not.
- **Structure** (`pycgt.structure`): `stop_count`, `is_even_tempered` and
  `is_odd_tempered`, `followers` and `follower_count`, `is_idempotent`, and the
  two sums that are not the disjunctive one — `conjunctive_sum` (move in both
  components) and `selective_sum` (move in either or both).
- **The Norton product** `norton_product(g, unit)`: `g` copies of `unit` for
  integer `g`, and otherwise overheating in disguise, with the unit replacing 1
  as the step play moves by. All twenty cases checked against CGSuite.
- **`freeze`**: a game cooled by its own temperature, always infinitesimally
  close to its mean.
- Predicates to match CGSuite's: `is_integer`, `is_nimber`, `is_numberish`,
  `is_number_tiny`; and the recognisers behind them, `as_nimber`, `as_tiny`,
  `as_miny` and `as_up_multiple`.
- **Notation** now names every multiple of up and down — `^`, `^^`, `^3`,
  `v4`, with or without a trailing `*` — recognised structurally, so there is
  no bound. It also reads the **multi-bar convention**, where `{A||B|C}` means
  `{A|{B|C}}`, which is how *Winning Ways* and CGSuite both write nested games;
  CGSuite's own output can now be parsed straight back in. Switch arguments are
  parenthesised where the text would otherwise run together, so `{1*|-1*}`
  prints as `+-(1*)` rather than the ambiguous `+-1*`. Everything `render`
  produces, `parse` accepts.

### Changed

- **Placement games are about twice as fast**, with no change to any computed
  value — the benchmark's core-operation counts are identical before and after.
  Profiling showed the board-geometry layer, not the game theory, dominated:
  `normalise` alone was 58% of the cost of valuing a Domineering board while
  the comparison core was 12%. Three fixes:
  - `value` is memoised on the raw position. Previously only component values
    were cached, so a position reachable by several move orders had its
    decomposition and normalisation redone in full every time.
  - `normalise` no longer searches for each variant's translation. Reflecting
    an axis sends its largest coordinate to zero and not reflecting it means
    subtracting its smallest, so the offset is known in advance; the old code
    made two `min` passes and rebuilt the cell list per variant.
  - `components` orders its output by seeding each search with the smallest
    remaining cell, rather than sorting afterwards with a key that sorted every
    component's cells. The resulting order is identical.

  Measured: Domineering 2×12 2.06×, 4×5 1.98×, Cram 3×4 5.72×, Clobber 3×3
  2.22×, the temperature of 2×11 1.55×. Roughly 2× is the ceiling for this
  workload — geometry was 58% of it — so going further means reducing the
  game-theoretic work itself.
- CI lints `benchmarks` as well as `src`, `tests` and `examples`.

## [0.3.0] — 2026-09-03

### Added

- **Impartial games and misère play** (`pycgt.impartial`). Misère play — where
  the player who cannot move *wins* — needs its own game type, because
  normal-play canonical form destroys exactly the information it depends on:
  two Nim heaps of two are worth zero in normal play, yet they are a misère
  loss for the mover while the endgame is a win. `Impartial` therefore applies
  no reduction at all, and its `add` is the structural sum. Provides
  `nim_value`, `misere_nim_value`, `misere_outcome`, `normal_outcome`, and
  `normal_value` as the lossy bridge back to a `Game`.
- **The genus** (`genus`, `genus_sequence`, `Genus`): a game's nim value
  together with the misère nim values of `G`, `G + *2`, `G + *2 + *2`, ... The
  superscript is cut where the sequence starts alternating and written so the
  alternating pair shows, which reproduces the traditional *Winning Ways*
  symbols `0^120`, `1^031`, `2^20`, `3^31`, `4^46`. `Genus.term(k)` gives any
  term of the infinite sequence.
- `is_tame` and `nim_position_genera`: the classical tame/wild division, being
  whether a game has the genus of some Nim position.
- **Heap rulesets** (`pycgt.rulesets.heap`): octal (take-and-break) games in
  the standard `d0.d1d2...` notation, subtraction games, and Grundy's Game,
  with Kayles, Dawson's Chess, Treblecross and Officers named. `nim_values`
  uses the classical integer recurrence rather than building trees, since
  Sprague--Grundy makes that sound for normal play; misère nim values have no
  such shortcut and are computed from the trees.
- Interning of impartial game trees, so equal trees are the same object.
  Without it, structural hashing of unreduced trees cost about 3.6x more per
  Kayles heap size and became unusable around 20.
- `examples/misere_genus.py`, printing the genus tables for Kayles and Dawson's
  Chess and checking Guy and Smith's periodicity and misère Nim's closed form.

### Fixed

- **`cool` froze one step too early.** It jumped to the mast whenever
  `t >= temperature`, discarding the infinitesimal that survives *at* the
  temperature: cooling `+-1` by exactly 1 leaves `{0|0}`, which is `*`, not 0.
  Only strictly beyond the temperature is the value a plain number. `freeze`
  evaluates at precisely that point, which is how the bug surfaced, and three
  tests had encoded the wrong behaviour.
- `freeze` raised on numbers. A number has negative temperature under this
  library's convention and `cool` refuses a negative amount, so the case needs
  handling rather than falling out; a number is already frozen.
- `render` printed every nimber above `*5` as a switch: the named-value table
  stopped at `*5`, and since every nimber is its own negative, the ones past it
  matched the `+-X` rule added in 0.2.0, so `*6` came out as
  `+-{*,*2,*3,*4,*5,0}`. Nimbers are now recognised structurally and without a
  bound, and a number plus *any* nimber prints correctly too (`3/4*6`).
- CI now lints `examples` as well as `src` and `tests`. `RELEASING.md` had
  always checked it, so a lint error in an example could have reached `main`.

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
