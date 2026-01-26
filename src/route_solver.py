# src/route_solver.py
# 역할: 아주 단순한 TSP(경로 순서) 생성기
# 현재 MVP: Greedy Nearest Neighbor(최근접 이웃) 방식
# - 나중에 2-opt / OR-Tools / 메타휴리스틱 등을 추가해도
#   pipeline.py는 그대로 두고 여기만 교체하면 됨.

import numpy as np


def solve_tsp(points):
    """
    points: [(lat, lon), ...]
      - 0번은 depot(센터)
      - 1..k는 방문해야 할 승객 노드

    반환:
      - 예: [0, 3, 1, 2, 0] 처럼 depot 복귀까지 포함한 경로
    """
    n = len(points)
    if n == 0:
        return []
    if n == 1:
        return [0, 0]

    unvisited = set(range(1, n))
    route = [0]
    current = 0

    while unvisited:
        nearest = min(unvisited, key=lambda i: _dist(points[current], points[i]))
        route.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    route.append(0)  # depot 복귀
    return route


def _dist(p1, p2) -> float:
    # 유클리드 거리(좌표 평면 근사) - MVP용
    return float(np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2))
