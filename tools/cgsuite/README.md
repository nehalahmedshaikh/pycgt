# The CGSuite oracle

Many external reference values in `pycgt`'s tests came from
[CGSuite](https://www.cgsuite.org/), Aaron Siegel's standard system for the
field. This directory contains a headless driver and its build recipe.

## Desktop application versus oracle

For interactive use, install CGSuite's official stable release (`.sh` on Linux
or `.exe` on Windows); it bundles a Java runtime. The desktop application has
no batch evaluator. Automated queries therefore use
`org.cgsuite.lang.System.evaluateOrException` through
[`Evaluate.scala`](Evaluate.scala), which reads one expression per line and
prints one `expression<TAB>result` line.

**CGSuite itself is deliberately not vendored here.** It is GPL and `pycgt` is
MIT, so its source must stay outside this repository. You clone and build it
yourself; `build.sh` does that into `build/`, which is git-ignored. Nothing in
`pycgt` links against it — it is a test oracle, run as a separate process, and
its implementation was never consulted beyond the API needed to invoke it.

## Build

The oracle build needs Git, Maven, Bash and a **JDK 17** (not just a JRE).

On 64-bit x86 Ubuntu:

```console
$ sudo apt install openjdk-17-jdk-headless maven
$ export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

On Windows, run the scripts from Git Bash after installing JDK 17 and Maven,
putting `mvn` on `PATH`, and setting `JAVA_HOME` to the JDK 17 directory. Use a
Git Bash path such as `/c/Program Files/Java/jdk-17` for `JAVA_HOME`.

`JAVA_HOME` selects JDK 17 even when a newer JDK is the system default. Both
scripts honor it directly, so changing the system-wide Java alternative is
unnecessary.

```console
$ ./build.sh
```

That clones CGSuite 2.2 beta 2, compiles its core, writes the classpath to
`build/classpath.txt`, and compiles the driver to `build/driver/`. The version
is pinned for reproducibility. Stable 2.1.1 supports core, thermography and
misère queries, but lacks the `game.graph` package used for this project's Col
and Snort fixtures; that package is present in 2.2 beta 2.

Four things about that build are not obvious, and each one cost real time:

1. **JDK 17 is required. JDK 21 does not work.** CGSuite is Scala 2.13.10, and
   the 2.13.10 compiler bridge fails to build under 21. Set `JAVA_HOME` to a 17
   installation; `build.sh` checks the version and stops if it is wrong.
2. **Stop at `compile`, not `package`.** CGSuite's `package` phase runs a
   `PostBuildScript` step that fails, and it is irrelevant to us. Build with
   `mvn -f lib/core/pom.xml compile` and run against
   `lib/core/target/classes`.
3. **The classpath must come from Maven**, via
   `mvn dependency:build-classpath`. There are a dozen transitive jars and
   guessing them is hopeless.
4. **The driver needs a warm-up query**, which is why `Evaluate.scala` runs one
   before the batch. CGSuite's `game` package resolves only after class loading
   has been triggered once, so a batch whose first line is `game.heap.Kayles(7)`
   fails with ``That variable is not defined: `game` ``. This looks exactly like
   a broken classpath and is not.

## Run

```console
$ ./run.sh queries.txt
```

`run.sh` handles each platform's path and classpath syntax and gives Java the
large stack CGSuite needs for deeper searches.

A query file is one CGScript expression per line; blank lines and `#` comments
are skipped.

```
# Domineering values
game.grid.Domineering(Grid.Empty(2,4)).CanonicalForm
game.grid.Domineering(Grid.Empty(2,3)).CanonicalForm.Temperature
# impartial and misère
game.heap.TakeAndBreak("0.77")(7).MisereNimValue
game.heap.TakeAndBreak("0.137")(9).Genus
```

Note `.Temperature` and `.Mean` live on the *canonical form*, not on the
position — `Domineering(...).Temperature` raises `Not a method or member
variable`.

## How to use it well

Two lessons the hard way.

**Ask CGSuite to adjudicate equality; do not compare rendered text.** The two
systems legitimately name the same value differently, and a textual diff of
Toads-and-Frogs values once produced 17 false failures. Instead emit a query
that asks CGSuite whether its value equals ours:

```
game.strip.ToadsAndFrogs("tfa").CanonicalForm == {0|*}
```

Used this way it has twice exposed a genuine gap in our renderer rather than a
phantom bug.

**Watch for values that collapse before you see them.** `*2+*2` in CGSuite is
*nimber* addition and evaluates to `*0`, so querying it tells you nothing about
misère play; the misère sum is `*[2]+*[2]`. A query can be well-formed, return
a confident answer, and answer a different question than you asked.

## Where the resulting data lives

Harvested values are embedded directly in the test files, next to a `Sources`
docstring naming their provenance — see
[`tests/test_impartial_misere.py`](../../tests/test_impartial_misere.py) and
[`tests/test_published_values.py`](../../tests/test_published_values.py). They
are not kept as loose data files, so the tests stay self-contained and readable.

Published results are preferred over the oracle wherever they exist: Guy and
Smith's periodicities, misère Nim's closed form, Berlekamp's Appendix B.1,
Wolfe's 4×5 Domineering value, the census counts, Sprague–Grundy.
