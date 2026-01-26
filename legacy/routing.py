# routing.py
# Hybrid Route Optimization
# Regret-2 → 2-opt → Tabu Search → GA

import numpy as np
import random


def route_cost(route, dist_mat):
    total = 0.0
    for i in range(len(route) - 1):
        total += dist_mat[route[i], route[i + 1]]
    return total


def regret_insert(nodes, dist_mat):
    """
    nodes: 방문해야 할 고객 리스트 (예: [3,5,7,9])
    dist_mat: 실제 도로 기반 거리행렬
    depot = 0 자동 포함
    """
    unvisited = nodes.copy()
    route = [0, 0]  # depot → depot

    if len(unvisited) == 1:
        route.insert(1, unvisited[0])
        return route

    best_pair = None
    best_cost = np.inf
    for a in unvisited:
        for b in unvisited:
            if a == b:
                continue
            cost = dist_mat[0, a] + dist_mat[a, b] + dist_mat[b, 0]
            if cost < best_cost:
                best_cost = cost
                best_pair = (a, b)

    route = [0, best_pair[0], best_pair[1], 0]
    unvisited.remove(best_pair[0])
    unvisited.remove(best_pair[1])

    while unvisited:
        best_node = None
        best_pos = None
        best_regret = -np.inf

        for c in unvisited:
            costs = []
            positions = []

            for pos in range(1, len(route)):
                a = route[pos - 1]
                b = route[pos]
                delta = dist_mat[a, c] + dist_mat[c, b] - dist_mat[a, b]
                costs.append(delta)
                positions.append(pos)

            sorted_costs = sorted(costs)
            if len(sorted_costs) > 1:
                regret = sorted_costs[1] - sorted_costs[0]
            else:
                regret = sorted_costs[0]

            if regret > best_regret:
                best_regret = regret
                best_node = c
                best_pos = positions[costs.index(min(costs))]

        route.insert(best_pos, best_node)
        unvisited.remove(best_node)

    return route


def two_opt(route, dist_mat):
    improved = True
    best = route.copy()

    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                new_route = best[:i] + best[i : j + 1][::-1] + best[j + 1 :]
                if route_cost(new_route, dist_mat) < route_cost(best, dist_mat):
                    best = new_route
                    improved = True

    return best


def tabu_search(route, dist_mat, max_iter=40, tabu_size=10):
    best = route.copy()
    best_cost = route_cost(best, dist_mat)
    current = route.copy()
    tabu = []

    for _ in range(max_iter):
        neighbors = []

        for i in range(1, len(current) - 1):
            for j in range(i + 1, len(current) - 1):
                if (i, j) in tabu:
                    continue
                nr = current.copy()
                nr[i], nr[j] = nr[j], nr[i]
                neighbors.append((nr, route_cost(nr, dist_mat), (i, j)))

        if not neighbors:
            break

        neighbors.sort(key=lambda x: x[1])
        best_nr, cost, move = neighbors[0]

        current = best_nr.copy()
        if cost < best_cost:
            best = current.copy()
            best_cost = cost

        tabu.append(move)
        if len(tabu) > tabu_size:
            tabu.pop(0)

    return best


def ga_optimize(route, dist_mat, generations=30, pop_size=20, mutation_rate=0.1):
    def crossover(p1, p2):
        a, b = sorted(random.sample(range(1, len(p1) - 1), 2))
        child = [-1] * len(p1)
        child[a:b] = p1[a:b]

        fill = [x for x in p2 if x not in child]
        idx = 1
        for v in fill:
            while child[idx] != -1:
                idx += 1
            child[idx] = v
        child[0], child[-1] = 0, 0
        return child

    def mutate(r):
        if random.random() < mutation_rate:
            i, j = random.sample(range(1, len(r) - 1), 2)
            r[i], r[j] = r[j], r[i]
        return r

    population = [route.copy()]
    for _ in range(pop_size - 1):
        r = route.copy()
        i, j = random.sample(range(1, len(r) - 1), 2)
        r[i], r[j] = r[j], r[i]
        population.append(r)

    for _ in range(generations):
        population.sort(key=lambda r: route_cost(r, dist_mat))
        new_pop = population[:5]

        while len(new_pop) < pop_size:
            p1, p2 = random.sample(population[:10], 2)
            child = mutate(crossover(p1, p2))
            new_pop.append(child)

        population = new_pop

    population.sort(key=lambda r: route_cost(r, dist_mat))
    return population[0]


def hybrid_route(nodes, dist_mat):
    """
    nodes: [고객 index 리스트], depot=0 자동
    dist_mat: 실제 도로 기반 거리행렬 (i→j 최단경로)
    """
    r1 = regret_insert(nodes, dist_mat)
    r2 = two_opt(r1, dist_mat)
    r3 = tabu_search(r2, dist_mat)
    if len(nodes) <= 4 or len(r3) <6:
      return r3
    r4 = ga_optimize(r3, dist_mat)
    return r4
