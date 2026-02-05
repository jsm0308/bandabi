# bandabi/road_network.py
from __future__ import annotations

import os
import math
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import networkx as nx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RoadGraphSpec:
    place: str
    network_type: str = "drive"
    cache_dir: str = "data/cache/osmnx"
    graphml_name: str = "seoul_drive.graphml"


def _lazy_import_osmnx():
    try:
        import osmnx as ox  # type: ignore
        return ox
    except Exception as e:
        raise RuntimeError(
            "OSMnx가 설치되어 있지 않습니다. 먼저 설치하세요:\n"
            "  pip install osmnx\n"
        ) from e


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _graphml_path(spec: RoadGraphSpec) -> str:
    return os.path.join(spec.cache_dir, spec.graphml_name)


def _normalize_highway_tag(hw: Any) -> str:
    """
    OSM 'highway' 태그는 str 또는 list일 수 있음.
    *_link 같은 파생 태그는 비교 편하게 정규화.
    """
    if hw is None:
        return "unknown"
    if isinstance(hw, (list, tuple)) and len(hw) > 0:
        hw = hw[0]
    if not isinstance(hw, str):
        hw = str(hw)
    hw = hw.strip().lower()
    if hw.endswith("_link"):
        hw = hw[: -len("_link")]
    return hw or "unknown"


def _parse_maxspeed_kph(val: Any) -> Optional[float]:
    """
    '50', '50;60', ['50', '60'], 'signals' 등 잡다한 형태를 최대한 안전하게 처리.
    숫자 하나라도 뽑히면 그걸 kph로 반환.
    """
    if val is None:
        return None
    if isinstance(val, (list, tuple)) and len(val) > 0:
        val = val[0]
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).lower().strip()
    # 흔한 구분자들 중 첫 숫자 토큰을 찾자
    for sep in [";", ",", "|"]:
        if sep in s:
            s = s.split(sep)[0].strip()
            break

    # "50 mph" 같은 케이스는 여기선 단순 처리(숫자만)
    num = ""
    for ch in s:
        if ch.isdigit() or ch == ".":
            num += ch
        elif num:
            break
    if not num:
        return None
    try:
        v = float(num)
    except ValueError:
        return None

    # mph 표기가 있으면 대충 변환(정확도보다 안정성)
    if "mph" in s:
        v = v * 1.60934
    return v


def load_or_build_seoul_graph(
    spec: RoadGraphSpec,
    *,
    force_download: bool = False,
) -> nx.MultiDiGraph:
    """
    - 서울 전체 drive 그래프를 GraphML로 캐시
    - 한 번 다운받아두면 이후 실험은 로드만
    """
    ox = _lazy_import_osmnx()
    _ensure_dir(spec.cache_dir)
    path = _graphml_path(spec)

    if (not force_download) and os.path.exists(path):
        logger.info("Loading cached graph: %s", path)
        return ox.load_graphml(path)

    logger.info("Downloading road network for: %s (type=%s)", spec.place, spec.network_type)
    # 전체 서울: place 기반
    G = ox.graph_from_place(spec.place, network_type=spec.network_type, simplify=True)

    # length 없으면 보강(버전 차이 대비)
    if not any("length" in data for _, _, _, data in G.edges(keys=True, data=True)):
        try:
            G = ox.distance.add_edge_lengths(G)  # type: ignore[attr-defined]
        except Exception:
            # 구버전 호환
            G = ox.add_edge_lengths(G)  # type: ignore[attr-defined]

    ox.save_graphml(G, path)
    logger.info("Saved cached graph: %s", path)
    return G


def ensure_base_speeds(
    G: nx.MultiDiGraph,
    *,
    speed_kph_by_highway: Dict[str, float],
    fallback_speed_kph: float = 25.0,
    prefer_maxspeed: bool = False,
) -> None:
    """
    각 edge에:
      - highway_norm
      - speed_kph_base
      - travel_time_sec_base  (multiplier=1 기준)
    를 보장한다.
    """
    for u, v, k, data in G.edges(keys=True, data=True):
        hw = _normalize_highway_tag(data.get("highway"))
        data["highway_norm"] = hw

        base_speed = None
        if prefer_maxspeed:
            base_speed = _parse_maxspeed_kph(data.get("maxspeed"))

        if base_speed is None:
            base_speed = float(speed_kph_by_highway.get(hw, fallback_speed_kph))

        base_speed = max(1.0, float(base_speed))
        data["speed_kph_base"] = base_speed

        length_m = float(data.get("length", 0.0))
        # length가 0이면 최소값 부여(예외 방지)
        length_m = max(1.0, length_m)

        # travel_time_sec_base = length / (speed(m/s))
        speed_mps = base_speed * 1000.0 / 3600.0
        data["travel_time_sec_base"] = length_m / max(1e-6, speed_mps)

    # 그래프 메타에 표시
    G.graph["has_speed_base"] = True


def apply_speed_profile(
    G: nx.MultiDiGraph,
    *,
    global_multiplier: float = 1.0,
    multiplier_by_highway: Optional[Dict[str, float]] = None,
    min_speed_kph: float = 3.0,
) -> None:
    """
    base(=speed_kph_base, travel_time_sec_base)에
    multiplier를 적용해:
      - speed_kph
      - travel_time_sec
    를 갱신한다.
    """
    multiplier_by_highway = multiplier_by_highway or {}
    gmul = float(global_multiplier)

    for u, v, k, data in G.edges(keys=True, data=True):
        hw = _normalize_highway_tag(data.get("highway_norm") or data.get("highway"))
        base_speed = float(data.get("speed_kph_base", 0.0))
        base_tt = float(data.get("travel_time_sec_base", 0.0))

        # base 보강(혹시 누락됐으면)
        if base_speed <= 0.0 or base_tt <= 0.0:
            length_m = float(data.get("length", 1.0))
            length_m = max(1.0, length_m)
            base_speed = max(1.0, base_speed) if base_speed > 0 else 25.0
            base_tt = length_m / (base_speed * 1000.0 / 3600.0)
            data["speed_kph_base"] = base_speed
            data["travel_time_sec_base"] = base_tt

        hmul = float(multiplier_by_highway.get(hw, 1.0))
        eff = max(1e-6, gmul * hmul)

        speed = max(min_speed_kph, base_speed * eff)
        data["speed_kph"] = speed

        # travel time은 multiplier에 반비례
        data["travel_time_sec"] = base_tt / eff

    G.graph["speed_profile"] = {
        "global_multiplier": gmul,
        "multiplier_by_highway": dict(multiplier_by_highway),
        "min_speed_kph": float(min_speed_kph),
    }
