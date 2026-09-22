"""Benchmarking utilities for algorithm evaluation."""


def benchmark_search(search_fn, cases):
    """Run a sequence of search tasks and return a list of results."""
    results = []
    for case in cases:
        result = search_fn(*case)
        results.append({"case": case, "result": result})
    return results
