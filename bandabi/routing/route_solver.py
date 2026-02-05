import random
import numpy as np


def solve_tsp(points, dist_mat, improve_method="none", seed=0, tabu_iters=200):
    n = len(points)
    if n <= 1:
        return [0, 0]

    route = _nearest_neighbor(dist_mat)

    if improve_method in (None, "none"):
        return route
    if improve_method == "two_opt":
        return _two_opt(route, dist_mat)
    if improve_method == "tabu":
        return _tabu_search(route, dist_mat, seed=seed, iters=tabu_iters)
    return route


def _nearest_neighbor(dist_mat):
    n = dist_mat.shape[0]
    unvisited = set(range(1, n))
    cur = 0
    path = [0]
    while unvisited:
        nxt = min(unvisited, key=lambda j: dist_mat[cur, j])
        path.append(nxt)
        unvisited.remove(nxt)
        cur = nxt
    path.append(0)
    return path


def _route_cost(route, dist_mat):
    c = 0.0
    for i in range(len(route) - 1):
        c += float(dist_mat[route[i], route[i + 1]])
    return c


def _two_opt(route, dist_mat, max_passes=30):
    best = route[:]
    best_cost = _route_cost(best, dist_mat)
    n = len(best)
    improved = True
    passes = 0
    while improved and passes < max_passes:
        improved = False
        passes += 1
        for i in range(1, n - 3):
            for k in range(i + 1, n - 2):
                new = best[:i] + best[i : k + 1][::-1] + best[k + 1 :]
                c = _route_cost(new, dist_mat)
                if c + 1e-9 < best_cost:
                    best, best_cost = new, c
                    improved = True
    return best


def _tabu_search(route, dist_mat, seed=0, iters=200, tabu_tenure=20):
    rng = random.Random(seed)
    n = len(route)

    # small-n guard
    if n < 6:
        return _two_opt(route, dist_mat, max_passes=10)

    best = route[:]
    best_cost = _route_cost(best, dist_mat)
    cur = route[:]
    cur_cost = best_cost

    tabu = {}

    def neighbors(r):
        i = rng.randrange(1, n - 2)
        k = rng.randrange(1, n - 2)
        if i == k:
            return None, None
        if i > k:
            i, k = k, i
        rr = r[:]
        rr[i], rr[k] = rr[k], rr[i]
        move = (r[i], r[k])
        return rr, move

    for t in range(iters):
        cand, move = neighbors(cur)
        if cand is None:
            continue
        c = _route_cost(cand, dist_mat)

        is_tabu = move in tabu and tabu[move] > t
        if (not is_tabu) or (c < best_cost):
            cur, cur_cost = cand, c
            tabu[move] = t + tabu_tenure
            if cur_cost < best_cost:
                best, best_cost = cur[:], cur_cost

    return best
