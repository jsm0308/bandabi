from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, Optional

import numpy as np

# NOTE: road 모델 쓸 때만 import되게(없어도 기존 모델은 작동)
try:
    import osmnx as ox
    import networkx as nx
except Exception:
    ox = None
    nx = None


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    import math

    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


@dataclass
class EuclidTimeModel:
    default_speed_kmh: float
    speed_multiplier: float
    detour_factor: float
    noise_sigma: float
    seed: int = 123

    def __post_init__(self):
        self.rng = np.random.default_rng(self.seed)

    def mean_travel_min(self, a_lat, a_lon, b_lat, b_lon) -> float:
        dist_km = haversine_km(a_lat, a_lon, b_lat, b_lon) * self.detour_factor
        speed = max(1e-6, self.default_speed_kmh * self.speed_multiplier)
        return float((dist_km / speed) * 60.0)

    def sample_travel_min(self, a_lat, a_lon, b_lat, b_lon) -> float:
        mu = self.mean_travel_min(a_lat, a_lon, b_lat, b_lon)
        if self.noise_sigma <= 0:
            return float(mu)
        noise = self.rng.lognormal(mean=-0.5 * self.noise_sigma**2, sigma=self.noise_sigma)
        return float(mu * noise)


class RoadTimeModel:
    """
    OSMnx 그래프 기반 최단시간(분).

    핵심 안정화:
    - travel_time_sec를 edge에 보장
    - 그래프를 largest connected component로 잘라서 NoPath 확률 대폭 감소
    - 그래도 NoPath면 undirected fallback
    - 그래도 실패면 haversine fallback (실험이 죽지 않게)
    """

    def __init__(
        self,
        graphml_path: str,
        speed_multiplier: float,
        cfg: dict | None = None,
        seed: int = 123,
    ):
        if ox is None or nx is None:
            raise RuntimeError("RoadTimeModel requires osmnx + networkx.")

        self.cfg: Dict[str, Any] = cfg or {}
        self.graphml_path = str(graphml_path)
        self.speed_multiplier = float(speed_multiplier)
        self.seed = int(seed)

        # --- read config (support both time_model.road and sim.road) ---
        tm_cfg = self.cfg.get("time_model", {}) if isinstance(self.cfg.get("time_model", {}), dict) else {}
        sim_cfg = self.cfg.get("sim", {}) if isinstance(self.cfg.get("sim", {}), dict) else {}

        tm_road_cfg = tm_cfg.get("road", {}) if isinstance(tm_cfg.get("road", {}), dict) else {}
        sim_road_cfg = sim_cfg.get("road", {}) if isinstance(sim_cfg.get("road", {}), dict) else {}

        # 병합 우선순위: time_model.road > sim.road
        road_cfg: Dict[str, Any] = dict(sim_road_cfg)
        road_cfg.update(dict(tm_road_cfg))

        self.detour_factor = float(sim_cfg.get("detour_factor", 1.0))
        self.fallback_speed_kph = float(road_cfg.get("fallback_speed_kph", 25.0))
        self.prefer_maxspeed = bool(road_cfg.get("prefer_maxspeed", False))
        self.multiplier_by_highway = dict(road_cfg.get("multiplier_by_highway", {}))
        self.min_speed_kph = float(road_cfg.get("min_speed_kph", 3.0))

        # 기본 속도 맵 (네가 YAML로 덮어씀)
        self.speed_kph_by_highway = {
            "motorway": 80,
            "trunk": 70,
            "primary": 50,
            "secondary": 40,
            "tertiary": 30,
            "residential": 25,
            "living_street": 15,
            "service": 15,
            "unclassified": 30,
            "road": 30,
            "unknown": 25,
        }
        if isinstance(road_cfg.get("speed_kph_by_highway"), dict):
            self.speed_kph_by_highway = dict(road_cfg["speed_kph_by_highway"])

        # --- load graph ---
        self.G = ox.load_graphml(self.graphml_path)

        # (선택) nearest_nodes 안정성을 위해 project_graph 시도
        # unprojected(위경도)에서 nearest_nodes가 환경에 따라 sklearn을 요구하는 경우가 있음.
        try:
            self.G = ox.project_graph(self.G)
        except Exception:
            # project 실패해도 계속 진행 (sklearn이 설치되어 있으면 괜찮음)
            pass

        # --- ensure travel_time_sec ---
        self._ensure_travel_time()

        # --- connectivity fix: keep largest component ---
        self.G = self._keep_largest_connected_component(self.G)

        # undirected fallback graph
        self.G_u = nx.Graph(self.G)

    def _edge_speed_kph(self, data: dict) -> float:
        # 1) maxspeed 우선(옵션)
        if self.prefer_maxspeed:
            ms = data.get("maxspeed")
            if ms:
                try:
                    if isinstance(ms, list):
                        ms = ms[0]
                    s = str(ms).split()[0]
                    v = float(s)
                    return max(self.min_speed_kph, v)
                except Exception:
                    pass

        # 2) highway 타입 기반
        hw = data.get("highway")
        if isinstance(hw, list) and hw:
            hw = hw[0]
        hw = str(hw) if hw is not None else "unknown"
        # *_link 정규화
        if hw.endswith("_link"):
            hw = hw.replace("_link", "")

        base = float(self.speed_kph_by_highway.get(hw, self.fallback_speed_kph))

        # 3) 도로타입 추가 배수(옵션)
        mult = float(self.multiplier_by_highway.get(hw, 1.0))
        return max(self.min_speed_kph, base * mult)

    def _ensure_travel_time(self) -> None:
        # 각 edge에 travel_time_sec를 보장
        for _, _, _, data in self.G.edges(keys=True, data=True):
            length_m = float(data.get("length", 0.0))
            speed_kph = self._edge_speed_kph(data) * self.speed_multiplier
            speed_mps = max(0.1, speed_kph * 1000.0 / 3600.0)
            data["travel_time_sec"] = float(length_m / speed_mps)

    def _keep_largest_connected_component(self, G):
        # DiGraph이면 strongly가 가장 안전하지만 너무 쪼개질 수 있음 → weakly fallback
        try:
            comps = list(nx.strongly_connected_components(G))
            comps.sort(key=len, reverse=True)
            if comps:
                keep = comps[0]
                # 너무 작으면 weakly로 한번 더
                if len(keep) >= max(1000, int(0.05 * G.number_of_nodes())):
                    return G.subgraph(keep).copy()
        except Exception:
            pass

        try:
            comps = list(nx.weakly_connected_components(G))
            comps.sort(key=len, reverse=True)
            keep = comps[0] if comps else set(G.nodes)
            return G.subgraph(keep).copy()
        except Exception:
            return G

    @lru_cache(maxsize=200_000)
    def _nearest_node(self, lat_r: int, lon_r: int) -> int:
        lat = lat_r / 1e5
        lon = lon_r / 1e5
        # osmnx expects X=lon, Y=lat (regardless of projection it handles)
        return int(ox.distance.nearest_nodes(self.G, X=float(lon), Y=float(lat)))

    def _node(self, lat: float, lon: float) -> int:
        return self._nearest_node(int(round(lat * 1e5)), int(round(lon * 1e5)))

    @lru_cache(maxsize=400_000)
    def _od_time_min(self, u: int, v: int) -> float:
        # 1) directed
        try:
            sec = nx.shortest_path_length(self.G, u, v, weight="travel_time_sec")
            return float(sec) / 60.0
        except Exception:
            pass

        # 2) undirected fallback
        try:
            sec = nx.shortest_path_length(self.G_u, u, v, weight="travel_time_sec")
            return float(sec) / 60.0
        except Exception:
            return float("nan")

    def mean_travel_min(self, a_lat, a_lon, b_lat, b_lon) -> float:
        a_lat = float(a_lat)
        a_lon = float(a_lon)
        b_lat = float(b_lat)
        b_lon = float(b_lon)

        u = self._node(a_lat, a_lon)
        v = self._node(b_lat, b_lon)
        if u == v:
            return 0.1

        t = self._od_time_min(u, v)
        if np.isfinite(t):
            return float(t)

        # 3) final fallback: haversine 기반
        km = haversine_km(a_lat, a_lon, b_lat, b_lon) * float(self.detour_factor)
        speed_kph = max(1.0, float(self.fallback_speed_kph) * float(self.speed_multiplier))
        return float((km / speed_kph) * 60.0)

    def sample_travel_min(self, a_lat, a_lon, b_lat, b_lon) -> float:
        # 지금은 mean==sample (노이즈는 시나리오에서 처리)
        return self.mean_travel_min(a_lat, a_lon, b_lat, b_lon)


def build_time_model(cfg: dict):
    tm = cfg.get("time_model", {}) if isinstance(cfg.get("time_model", {}), dict) else {}
    kind = str(tm.get("kind", "euclid")).lower()  # "euclid" | "road"

    if kind == "road":
        graph_path = str(tm.get("graphml_path", "data/cache/osmnx/seoul_drive.graphml"))
        speed_mult = float(tm.get("speed_multiplier", 1.0))
        seed = int((cfg.get("sim", {}) or {}).get("seed", 123))
        return RoadTimeModel(graphml_path=graph_path, speed_multiplier=speed_mult, cfg=cfg, seed=seed)

    # default: euclid
    base = tm if isinstance(tm, dict) else {}
    sim = cfg.get("sim", {}) if isinstance(cfg.get("sim", {}), dict) else {}
    return EuclidTimeModel(
        default_speed_kmh=float(base.get("default_speed_kmh", 18.0)),
        speed_multiplier=float(base.get("speed_multiplier", 1.0)),
        detour_factor=float(sim.get("detour_factor", 1.25)),
        noise_sigma=float(sim.get("travel_time_noise_sigma", 0.25)),
        seed=int(sim.get("seed", 123)),
    )
