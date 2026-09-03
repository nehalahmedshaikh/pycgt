#!/usr/bin/env bash
# Run a query file through the CGSuite oracle. One expression per line;
# blank lines and '#' comments are skipped. Output is "expression<TAB>result".
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
build="$here/build"

[ $# -ge 1 ] || { echo "usage: run.sh <query-file>" >&2; exit 2; }
[ -f "$build/classpath.txt" ] || { echo "error: run build.sh first." >&2; exit 1; }

sep=":"
case "$(uname -s)" in MINGW* | MSYS* | CYGWIN*) sep=";" ;; esac

# Java needs native paths. Under Git Bash a POSIX path such as /c/Users/... is
# silently not understood, which surfaces as "Could not find or load main class
# Evaluate" and looks exactly like a build failure.
to_native() {
    if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s\n' "$1"; fi
}

# -Xss1g is not optional: CGSuite recurses deeply and the default stack
# overflows on larger positions. Logback chatter goes to stdout, so drop it.
java -Xss1g -Xmx6g \
    -cp "$(cat "$build/classpath.txt")$sep$(to_native "$build/driver")" \
    Evaluate "$(to_native "$1")" | grep -v '^\['
