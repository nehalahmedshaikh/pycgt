# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
