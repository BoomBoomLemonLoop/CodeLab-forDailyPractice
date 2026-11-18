"""Cell-centred FVM for -u'' = pi**2 sin(pi*x), u(0)=u(1)=0 (dimensionless)."""

import argparse
import json

import numpy as np


def solve(cells=40):
    """Return centres and solution using midpoint sources and half-cell wall distances."""
    if isinstance(cells, bool) or not isinstance(cells, int) or not 2 <= cells <= 2000:
        raise ValueError("cells must be an integer in [2, 2000]")
    h = 1.0 / cells
    x = (np.arange(cells) + 0.5) * h
    diagonal = np.full(cells, 2.0)
    diagonal[[0, -1]] = 3.0
    rhs = np.pi**2 * np.sin(np.pi * x) * h**2
    # Thomas elimination for a tridiagonal system: O(N) memory and time.
    for i in range(1, cells):
        factor = -1.0 / diagonal[i - 1]
        diagonal[i] += factor
        rhs[i] -= factor * rhs[i - 1]
    u = np.empty(cells)
    u[-1] = rhs[-1] / diagonal[-1]
    for i in range(cells - 2, -1, -1):
        u[i] = (rhs[i] + u[i + 1]) / diagonal[i]
    return x, u


def report(cells):
    x, u = solve(cells)
    error = u - np.sin(np.pi * x)
    return {
        "cells": cells,
        "l2_rms": float(np.sqrt(np.mean(error**2))),
        "linf": float(np.max(np.abs(error))),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cells", type=int, default=40)
    args = parser.parse_args()
    try:
        print(json.dumps(report(args.cells), indent=2))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
