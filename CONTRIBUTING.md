# Contributing

## Running the checks

Python 3.11 or newer is required. On Debian or Ubuntu, first install the
standard-library virtual-environment module:

```console
$ sudo apt install python3-venv
```

Create and activate an isolated environment:

```console
# Linux and macOS
$ python3 -m venv .venv
$ source .venv/bin/activate

# Windows PowerShell
> py -3.11 -m venv .venv
> .venv\Scripts\Activate.ps1
```

```console
$ python -m pip install -e ".[dev]"
$ pytest -q
$ pytest -q --doctest-modules src/pycgt
$ python examples/berlekamp_1988.py
$ python examples/misere_genus.py
$ ruff check src tests examples benchmarks
$ ruff format --check src tests examples benchmarks
$ mypy
```

These are the checks CI runs on Linux, Windows and macOS across Python
3.11–3.13.

## The one rule that matters

**Expected values come from outside this library.** Every value asserted in
`tests/test_published_values.py` is either printed in a paper or produced by
CGSuite. Nothing is a number this library computed and then enshrined as
correct.

If you add a value, cite where it came from in the docstring. If you cannot
cite it, derive it by hand in a comment. "The code says so" is not a source —
the values in this field are easy to get subtly wrong, and a self-confirming
test suite is worse than none.

## Adding a ruleset

Placement games on a grid need no new engine. Declare the shapes and let
`rulesets/grid.py` do the rest:

```python
DOMINEERING = Ruleset(
    name="Domineering",
    left_shapes=(((0, 0), (1, 0)),),    # vertical domino
    right_shapes=(((0, 0), (0, 1)),),   # horizontal domino
    transpose_invariant=False,          # transposing swaps the players
)
```

Set `transpose_invariant=True` only when both players have the same shapes; it
lets the memo table use all eight symmetries of the square, and it is wrong for
partizan rulesets like Domineering.

Then give the ruleset tests with an external anchor: published values, or a
known closed form (Nim sums are exclusive-or; Hackenbush strings are dyadic
rationals; impartial games satisfy `G == -G`).

## Things worth knowing before changing the core

**Every `Game` from the public API is canonical**, so `==` is value equality.
If you add a constructor, canonicalise in it.

**`<` and `>` are deliberately undefined.** Games are partially ordered, so
`not (G <= H)` does not imply `G > H`. Use `compare()`, which can return
`CONFUSED`.

**Do not compute temperature by cooling repeatedly until the result is a
number.** It looks right and is wrong: once the thermograph's boundaries cross,
the crossing value is lost and canonicalising gives the *simplest* number in
the overshoot instead of the mast. The symptom is non-monotone cooling. Use
`thermograph()`, which tracks the boundaries as exact piecewise-linear
functions. There is a regression test for this.

**No runtime dependencies.** The library must run unchanged under Pyodide.
`pytest`, `mypy` and `ruff` are dev-only.

## Provenance

This is a clean-room implementation from the published mathematics — *Winning
Ways*, Siegel's *Combinatorial Game Theory*, and Berlekamp (1988). CGSuite is
GPL; do not copy or port its code. Consulting its *output* as a test oracle is
fine and is what this project does.
