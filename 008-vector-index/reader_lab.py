"""Hand-wired layered-search illustration, not an HNSW index builder.

Standard library only; importing defines functions/data and performs no I/O.
Search follows paper Algorithms 2 and 5 on an invented graph. Sorted lists
replace priority queues. Distance comparisons are strict as in the paper;
IDs break selection/eviction/display ties, not admission or stopping ties.
"""

import argparse
from dataclasses import dataclass


POINTS = dict(zip("ABCDEFGH", (0, 2, 5, 8, 9, 12, 15, 20)))
UPPER = {"A": ("C",), "C": ("A", "H"), "H": ("C",)}
BOTTOM = {
    "A": ("B",), "B": ("A", "C"), "C": ("B", "D", "G"),
    "D": ("C", "F"), "E": ("H",), "F": ("D",),
    "G": ("C", "H"), "H": ("E", "G"),
}


@dataclass
class LayerResult:
    best: list
    evaluated: list
    expanded: list
    trace: list
    stop: str


def exact_gap_search(points, query, k):
    """Exhaustively rank all IDs by absolute gap, then alphabetical ID."""
    if not 1 <= k <= len(points):
        raise ValueError("require 1 <= k <= number of points")
    return sorted(points, key=lambda node: (abs(points[node] - query), node))[:k]


def search_layer(points, graph, query, entry, ef):
    """Algorithm 2 with one entry; evaluated and expanded are different sets.

    C (frontier) is NOT truncated when W (retained best) evicts an ID.
    Mark seen before admission, and compute each ID's gap once per layer.
    """
    if ef < 1:
        raise ValueError("ef must be positive")
    distances = {entry: abs(points[entry] - query)}
    evaluated, expanded, trace = [entry], [], []
    frontier, best = [entry], [entry]
    key = lambda node: (distances[node], node)
    stop = "frontier empty"
    while frontier:
        candidate = min(frontier, key=key)
        frontier.remove(candidate)
        worst = max(best, key=key)
        if distances[candidate] > distances[worst]:
            stop = (f"stop before expanding {candidate}: gap {distances[candidate]} "
                    f"> worst retained gap {distances[worst]}")
            trace.append(stop)
            break
        expanded.append(candidate)
        trace.append(f"expand {candidate} (gap {distances[candidate]})")
        for node in sorted(graph[candidate]):
            if node in distances:
                continue
            distances[node] = abs(points[node] - query)
            evaluated.append(node)
            worst = max(best, key=key)
            admitted = len(best) < ef or distances[node] < distances[worst]
            action = "reject"
            if admitted:
                frontier.append(node)
                best.append(node)
                action = "admit"
                if len(best) > ef:
                    evicted = max(best, key=key)
                    best.remove(evicted)
                    action += f", evict {evicted} from retained best only"
            trace.append(f"  evaluate {node}: gap {distances[node]}; {action}")
        trace.append("  retained: " + ",".join(sorted(best, key=key)))
    return LayerResult(sorted(best, key=key), evaluated, expanded, trace, stop)


def layered_search(ef, k=3, query=10):
    if not 1 <= k <= len(POINTS) or ef < k:
        raise ValueError("require 1 <= k <= 8 and ef >= k")
    upper = search_layer(POINTS, UPPER, query, "A", 1)
    lower = search_layer(POINTS, BOTTOM, query, upper.best[0], ef)
    return lower.best[:k], upper, lower


def neighbour_recall(found, truth):
    if not truth or len(set(truth)) != len(truth):
        raise ValueError("truth must contain distinct IDs and be nonempty")
    return len(set(found) & set(truth)) / len(truth)


def choose(rows, target, max_ms):
    """Rows are (label, recall fraction, ms); fastest qualifying row or None."""
    accepted = [row for row in rows if row[1] >= target and row[2] <= max_ms]
    return min(accepted, key=lambda row: (row[2], row[0]))[0] if accepted else None


def self_check():
    """Deterministic semantic checks, especially the equal-distance frontier."""
    truth = exact_gap_search(POINTS, 10, 3)
    assert truth == ["E", "D", "F"]
    narrow, upper, low = layered_search(3)
    wide, _, high = layered_search(8)
    assert upper.best == ["C"]
    assert upper.evaluated == ["A", "C", "H"]
    assert upper.expanded == ["A", "C"]
    assert narrow == ["D", "F", "C"] and wide == truth
    assert low.evaluated == ["C", "B", "D", "G", "F", "H"]
    assert low.expanded == ["C", "D", "F", "G"]
    assert low.stop == "stop before expanding B: gap 8 > worst retained gap 5"
    assert high.evaluated == ["C", "B", "D", "G", "F", "H", "A", "E"]
    assert high.expanded == ["C", "D", "F", "G", "B", "A", "H", "E"]
    assert neighbour_recall(narrow, truth) == 2 / 3
    assert neighbour_recall(wide, truth) == 1
    assert len(low.evaluated) > 3 and len(low.expanded) > 3
    assert "E" not in set(upper.evaluated + low.evaluated)
    assert len(set(upper.evaluated + low.evaluated)) == 7
    assert sum(map(len, (upper.evaluated, low.evaluated))) == 9
    assert sum(map(len, (upper.evaluated, high.evaluated))) == 11
    for graph in (UPPER, BOTTOM):
        assert all(a in graph[b] for a in graph for b in graph[a])
    for k in range(1, 9):
        assert layered_search(8, k)[0] == exact_gap_search(POINTS, 10, k)
    try:
        layered_search(2)
    except ValueError:
        pass
    else:
        raise AssertionError("ef < k must be rejected")
    fresh = {"J": -4, "K": 1, "L": 6, "M": 10, "N": 13, "P": 18, "R": 25}
    assert exact_gap_search(fresh, 12, 4) == ["N", "M", "L", "P"]
    assert neighbour_recall(["N", "M", "P", "R"], ["N", "M", "L", "P"]) == .75
    practice = [("fast", .90, .20), ("balanced", .96, .45), ("deep", .99, .90)]
    assert choose(practice, .95, .50) == "balanced"
    assert choose(practice, .98, .50) is None
    small = [("exact", 1., .037), ("ef50", .956, .034),
             ("ef100", .993, .063), ("ef200", .999, .128)]
    assert choose(small, .99, .037) == "exact"
    assert choose(small[1:], .99, .037) is None
    assert choose(small, .95, .037) == "ef50"
    large = [("exact", 1., 1.848), ("ef400", .973, .658)]
    assert choose(large, .99, 1.) is None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="run deterministic assertions")
    args = parser.parse_args()
    if args.check:
        self_check()
        print("PASS: deterministic lab checks")
        return
    truth = exact_gap_search(POINTS, 10, 3)
    print("INVENTED hand-wired graph; no HNSW construction or timing benchmark.")
    print("Coordinates: " + " ".join(f"{n}={x}" for n, x in POINTS.items()))
    print("query=10; k=3; gap=abs(coordinate-query); ID order breaks ties")
    print("Exact top 3: " + ",".join(truth))
    for ef in (3, 8):
        found, upper, lower = layered_search(ef)
        print(f"\nef={ef}; upper ef=1:")
        print("\n".join(upper.trace))
        print("lower:")
        print("\n".join(lower.trace))
        for label, layer in (("upper", upper), ("lower", lower)):
            print(f"{label} evaluated ({len(layer.evaluated)}): {','.join(layer.evaluated)}")
            print(f"{label} expanded ({len(layer.expanded)}): {','.join(layer.expanded)}")
        unique = set(upper.evaluated + lower.evaluated)
        print(f"All layers: {len(unique)} unique IDs distance-evaluated; "
              f"{len(upper.evaluated) + len(lower.evaluated)} gap computations")
        print(f"Returned: {','.join(found)}; recall@3={neighbour_recall(found, truth):.6f}")
    print("\nPRACTICE (invented; answers in README): query=12, k=4")
    print("J=-4 K=1 L=6 M=10 N=13 P=18 R=25; returned N,M,P,R")
    print("Grid (recall, ms): fast=(90%,.20), balanced=(96%,.45), deep=(99%,.90)")
    print("Choose fastest with recall>=95%, ms<=.50; repeat with recall>=98%.")


if __name__ == "__main__":
    main()
