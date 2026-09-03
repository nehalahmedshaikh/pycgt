"""Benchmarks, so performance claims are reproducible and regressions visible.

Wall-clock times depend on the machine and on whatever else it is doing, so
each workload also reports **work counters** taken from the memo tables. Those
are exact and load-independent: if a change makes the library do less work, the
counters fall whether or not the timing is noisy. Compare counters first and
treat times as corroboration.

    $ python benchmarks/run.py                  # run and print a table
    $ python benchmarks/run.py --save base.json # record a baseline
    $ python benchmarks/run.py --against base.json

Caches are cleared between workloads, so each figure is a cold-start cost and
workloads cannot flatter one another.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from importlib import import_module

# Fetched through importlib rather than `from pycgt import game`: the package
# exports functions called `game` and `stops`, which shadow the submodules of
# the same name, so the plain import silently yields a function.
game = import_module("pycgt.game")
values = import_module("pycgt.values")
stops = import_module("pycgt.stops")
reduced = import_module("pycgt.reduced")
thermal = import_module("pycgt.thermal")
notation = import_module("pycgt.notation")
impartial = import_module("pycgt.impartial")
grid = import_module("pycgt.rulesets.grid")
domineering = import_module("pycgt.rulesets.domineering")
cram = import_module("pycgt.rulesets.cram")
clobber = import_module("pycgt.rulesets.clobber")
graphs = import_module("pycgt.rulesets.graphs")
heap = import_module("pycgt.rulesets.heap")
nim = import_module("pycgt.rulesets.nim")
toads_and_frogs = import_module("pycgt.rulesets.toads_and_frogs")

MODULES = [
    game,
    values,
    stops,
    reduced,
    thermal,
    notation,
    impartial,
    grid,
    domineering,
    cram,
    clobber,
    graphs,
    heap,
    nim,
    toads_and_frogs,
]


def clear_caches() -> None:
    """Empty every memo table, so each workload starts cold.

    Discovered by walking the modules rather than listed by hand, so a cache
    added later is picked up without anyone remembering to come back here.
    """
    for module in MODULES:
        for name in dir(module):
            attribute = getattr(module, name, None)
            clear = getattr(attribute, "cache_clear", None)
            if clear is not None:
                clear()
    game._geq_cache.clear()
    impartial._interned.clear()


#: The headline metric. These three measure irreducible CGT computation and
#: mean the same thing in every version, so they stay comparable when caches
#: are added or removed elsewhere. A total over *all* caches would not: adding
#: a cache adds misses, which reads as a regression when it is an improvement.
CORE_WORK = ("game.canonical misses", "game._add_raw misses", "geq cache")


def counters() -> dict[str, int]:
    """Exact work counters: how many real computations each memo table did.

    A miss is one real computation, so misses are a load-independent measure of
    work. Hits are cheap lookups, reported to show reuse.

    Deduplicated by function identity. Walking modules alone counts
    ``canonical`` once for every module that imported it -- eight times, as it
    happens -- which inflated the total by roughly that factor.
    """
    out: dict[str, int] = {}
    seen: set[int] = set()
    for module in MODULES:
        for name in dir(module):
            attribute = getattr(module, name, None)
            info = getattr(attribute, "cache_info", None)
            if info is None or id(attribute) in seen:
                continue
            seen.add(id(attribute))
            stats = info()
            if not (stats.hits or stats.misses):
                continue
            # Label by where the function is *defined*, not where it was found.
            wrapped = getattr(attribute, "__wrapped__", None)
            home = getattr(wrapped, "__module__", module.__name__)
            label = f"{home.split('.')[-1]}.{name}"
            out[f"{label} misses"] = stats.misses
            out[f"{label} hits"] = stats.hits
    out["geq cache"] = len(game._geq_cache)
    return out


def core_work(counts: dict[str, int]) -> int:
    return sum(counts.get(key, 0) for key in CORE_WORK)


#: Each workload is cheap enough to run every time, and between them they cover
#: the grid engine, the CGT core, thermography, and the impartial/misère side.
WORKLOADS: list[tuple[str, Callable[[], object]]] = [
    ("domineering 2x8", lambda: domineering.rectangle(2, 8)),
    ("domineering 2x10", lambda: domineering.rectangle(2, 10)),
    ("domineering 2x12", lambda: domineering.rectangle(2, 12)),
    ("domineering 3x4", lambda: domineering.rectangle(3, 4)),
    ("domineering 4x5", lambda: domineering.rectangle(4, 5)),
    ("cram 3x4", lambda: cram.rectangle(3, 4)),
    ("clobber 3x3", lambda: clobber.parse("xox|oxo|xox")),
    ("toads-and-frogs len 6", lambda: toads_and_frogs.value("ttt.ff")),
    (
        "snort path 7",
        lambda: graphs.value(graphs.uncoloured(graphs.Graph.path(7)), graphs.SNORT),
    ),
    ("temperature of 2x11", lambda: thermal.temperature(domineering.rectangle(2, 11))),
    ("kayles nim values to 400", lambda: heap.nim_values(heap.KAYLES, 400)),
    ("kayles misere to 18", lambda: heap.misere_nim_values(heap.KAYLES, 18)),
    (
        "dawson genus to 18",
        lambda: [impartial.genus(heap.heap(heap.DAWSONS_CHESS, n)) for n in range(18)],
    ),
    ("nimbers to *40", lambda: [notation.render(values.nimber(n)) for n in range(41)]),
]


def run() -> dict[str, dict[str, float | dict[str, int]]]:
    results: dict[str, dict[str, float | dict[str, int]]] = {}
    for label, workload in WORKLOADS:
        clear_caches()
        start = time.perf_counter()
        workload()
        elapsed = time.perf_counter() - start
        counts = counters()
        results[label] = {"seconds": elapsed, "counters": counts}
        print(
            f"  {label:<28} {elapsed:8.3f}s   {core_work(counts):>9,} core ops",
            flush=True,
        )
    return results


def compare(now: dict, before: dict) -> None:
    print()
    print(f"  {'workload':<28} {'time':>18}   {'core ops':>24}")
    print("  " + "-" * 74)
    for label in now:
        if label not in before:
            print(f"  {label:<28} {'(new)':>18}")
            continue
        t_now = float(now[label]["seconds"])
        t_old = float(before[label]["seconds"])
        c_now = core_work(now[label]["counters"])
        c_old = core_work(before[label]["counters"])
        t_ratio = f"{t_old / t_now:.2f}x" if t_now > 0 else "-"
        c_ratio = f"{c_old / c_now:.2f}x" if c_now > 0 else "-"
        print(
            f"  {label:<28} {t_old:7.3f}->{t_now:7.3f} {t_ratio:>6}"
            f"   {c_old:>9,}->{c_now:>9,} {c_ratio:>6}"
        )
    print()
    print("  Above 1.00x is an improvement. Core ops are exact and comparable")
    print("  across versions; times move with whatever else the machine runs.")
    print("  Caches present in only one side are listed per workload in the JSON.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", type=Path, help="write results to this file")
    parser.add_argument("--against", type=Path, help="compare against this file")
    args = parser.parse_args()

    print(f"pycgt benchmarks (python {sys.version.split()[0]})")
    print()
    results = run()

    if args.save:
        args.save.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\n  saved to {args.save}")
    if args.against:
        compare(results, json.loads(args.against.read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
