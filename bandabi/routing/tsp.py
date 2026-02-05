"""TSP solver(s) for MVP.

Contract:
- Depot is always node 0.
- Input `points` is a list of (lat, lon) where points[0] is depot.
- Return is a list of node indices forming a round trip: [0, ..., 0].

We keep this intentionally simple to allow swapping implementations later
(metaheuristics, VRP, etc.).
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np


def solve_tsp(
    points: Sequence[Tuple[float, float]],
    dist_mat: Optional[np.ndarray] = None,
    *,
    method: str = "euclid_nn",
    improve_2opt: bool = False,
) -> List[int]:
    """Solve a small TSP-like sequencing problem.

    Args:
        points: Coordinates, where index 0 is depot.
        dist_mat: Optional (n,n) cost matrix in minutes. If provided and method
            is "time_nn", it will be used for nearest-neighbor selection.
        method: "euclid_nn" or "time_nn".
        improve_2opt: Apply a simple 2-opt improvement pass.

    Returns:
        Route including depot return, e.g. [0, 3, 1, 2, 0].
    """
    n = len(points)
    if n == 0:
        return []
    if n == 1:
        return [0, 0]

    if method not in {"euclid_nn", "time_nn"}:
        raise ValueError(f"Unknown routing method: {method}")

    if method == "time_nn":
        if dist_mat is None:
            raise ValueError("dist_mat is required for method='time_nn'")
        if dist_mat.shape != (n, n):
            raise ValueError(f"dist_mat shape must be ({n},{n}), got {dist_mat.shape}")

    unvisited = set(range(1, n))
    route: List[int] = [0]
    cur = 0

    while unvisited:
        if method == "euclid_nn":
            nxt = min(unvisited, key=lambda i: _euclid(points[cur], points[i]))
        else:
            nxt = min(unvisited, key=lambda i: float(dist_mat[cur, i]))
        route.append(nxt)
        unvisited.remove(nxt)
        cur = nxt

    route.append(0)

    if improve_2opt and len(route) > 4:
        route = _two_opt(route, dist_mat if method == "time_nn" else None, points)

    return route


def _euclid(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return float(np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2))


def _route_cost(route: Sequence[int], dist_mat: Optional[np.ndarray], points: Sequence[Tuple[float, float]]) -> float:
    cost = 0.0
    for a, b in zip(route[:-1], route[1:]):
        if dist_mat is not None:
            cost += float(dist_mat[a, b])
        else:
            cost += _euclid(points[a], points[b])
    return cost


def _two_opt(route: List[int], dist_mat: Optional[np.ndarray], points: Sequence[Tuple[float, float]]) -> List[int]:
    """Very small 2-opt improvement. O(n^2) per pass."""
    best = route
    best_cost = _route_cost(best, dist_mat, points)
    improved = True

    # keep depot fixed at both ends
    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                if j - i == 1:
                    continue
                cand = best[:i] + best[i:j][::-1] + best[j:]
                c = _route_cost(cand, dist_mat, points)
                if c + 1e-9 < best_cost:
                    best = cand
                    best_cost = c
                    improved = True
        
    return best
