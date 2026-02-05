# bandabi/routing/road_router.py
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Tuple, Optional

import networkx as nx


def _lazy_import_osmnx():
    try:
        import osmnx as ox  # type: ignore
        return ox
    except Exception as e:
        raise RuntimeError(
            "OSMnx가 설치되어 있지 않습니다. 먼저 설치하세요:\n"
            "  pip install osmnx\n"
        ) from e


@dataclass
class RoadRouter:
    G: nx.MultiDiGraph

    def _nearest_node(self, lat: float, lon: float) -> int:
        ox = _lazy_import_osmnx()
        # nearest_nodes(G, X, Y) where X=lon, Y=lat
        return int(ox.distance.nearest_nodes(self.G, lon, lat))

    @lru_cache(maxsize=200_000)
    def _nearest_node_cached(self, lat_rounded: int, lon_rounded: int) -> int:
        # 캐시 키는 정밀도(소수 5자리 정도)로 라운딩한 정수
        lat = lat_rounded / 1e5
        lon = lon_rounded / 1e5
        return self._nearest_node(lat, lon)

    def node_of(self, lat: float, lon: float) -> int:
        return self._nearest_node_cached(int(round(lat * 1e5)), int(round(lon * 1e5)))

    @lru_cache(maxsize=500_000)
    def shortest_time_sec(self, u: int, v: int) -> float:
        try:
            return float(nx.shortest_path_length(self.G, u, v, weight="travel_time_sec"))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return float("inf")

    @lru_cache(maxsize=500_000)
    def shortest_distance_m(self, u: int, v: int) -> float:
        try:
            return float(nx.shortest_path_length(self.G, u, v, weight="length"))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return float("inf")

    def travel_time_min(self, a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
        u = self.node_of(a_lat, a_lon)
        v = self.node_of(b_lat, b_lon)
        sec = self.shortest_time_sec(u, v)
        if math.isinf(sec):
            # fallback: 아주 비상시 0 대신 큰 값
            return 99999.0
        return sec / 60.0

    def distance_km(self, a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
        u = self.node_of(a_lat, a_lon)
        v = self.node_of(b_lat, b_lon)
        m = self.shortest_distance_m(u, v)
        if math.isinf(m):
            return 99999.0
        return m / 1000.0
