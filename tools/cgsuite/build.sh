#!/usr/bin/env bash
# Build the CGSuite oracle: clone CGSuite, compile its core, compile the driver.
# See README.md for why each step is the way it is.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
build="$here/build"
cgsuite="$build/cgsuite"
scala_version="2.13.10"

# Java needs native paths. Under Git Bash a POSIX path such as /c/Users/... is
# silently not understood, which surfaces as "Could not find or load main class"
# and looks exactly like a build failure.
to_native() {
    if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s\n' "$1"; fi
}

# --- JDK 17 ---------------------------------------------------------------
# 21 cannot compile Scala 2.13.10: the compiler bridge fails to build.
if ! command -v javac >/dev/null 2>&1; then
    echo "error: javac not found. Set JAVA_HOME to a JDK 17 installation." >&2
    exit 1
fi
major="$(javac -version 2>&1 | sed -E 's/javac ([0-9]+).*/\1/')"
if [ "$major" != "17" ]; then
    echo "error: JDK 17 required, found $major." >&2
    echo "       Scala $scala_version cannot be compiled by JDK 21." >&2
    exit 1
fi

command -v mvn >/dev/null 2>&1 || { echo "error: mvn not found." >&2; exit 1; }

mkdir -p "$build"

# --- CGSuite source (not vendored: GPL, and pycgt is MIT) -----------------
if [ ! -d "$cgsuite/.git" ]; then
    echo "== cloning CGSuite"
    git clone --depth 1 https://github.com/aaron-siegel/cgsuite.git "$cgsuite"
fi

# --- compile only; `package` runs a PostBuildScript step that fails -------
echo "== compiling cgsuite-core"
mvn -q -f "$cgsuite/pom.xml" -pl lib/core compile

# --- classpath, from Maven (a dozen transitive jars) ----------------------
echo "== resolving classpath"
mvn -q -f "$cgsuite/pom.xml" -pl lib/core \
    dependency:build-classpath -Dmdep.outputFile="$build/deps.txt"

sep=":"
case "$(uname -s)" in MINGW* | MSYS* | CYGWIN*) sep=";" ;; esac
printf '%s%s%s\n' "$(cat "$build/deps.txt")" "$sep" \
    "$(to_native "$cgsuite/lib/core/target/classes")" > "$build/classpath.txt"

# --- the driver -----------------------------------------------------------
echo "== compiling driver"
m2="$(to_native "${HOME}/.m2/repository/org/scala-lang")"
scalac_cp="$m2/scala-compiler/$scala_version/scala-compiler-$scala_version.jar$sep$m2/scala-library/$scala_version/scala-library-$scala_version.jar$sep$m2/scala-reflect/$scala_version/scala-reflect-$scala_version.jar"
mkdir -p "$build/driver"
java -cp "$scalac_cp" scala.tools.nsc.Main \
    -classpath "$(cat "$build/classpath.txt")" \
    -d "$(to_native "$build/driver")" "$(to_native "$here/Evaluate.scala")"

echo
echo "ready. run queries with:  $here/run.sh <query-file>"
