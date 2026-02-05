"""Core simulation pipeline.

Flow:
1) Demand generation (requests)
2) Build time model
3) Build routes (per center / slot / bus_type)
4) Simulate promised vs actual timelines
5) Emit artifacts:
   - events.csv
   - routes.csv            (vehicle-level summary, backward-compatible)
   - routes_stops.csv      (stop-level rows for map jump/highlight)
   - metrics.csv
   - map_data.json / map.html (optional)

The pipeline is purposely deterministic given config seeds.
"""

from __future__ import annotations

import os
import time
import json
from typing import List, Sequence, Tuple

import numpy as np
import pandas as pd

from .config import ConfigError
from .demand import build_requests, load_centers
from .metrics import compute_kpis
from .routing.tsp import solve_tsp
from .time_model import build_time_model

# ✅ cluster-first 분할 함수
from .clustering import split_requests_into_buses


def _hhmm_to_min(hhmm: str) -> float:
    try:
        h, m = hhmm.split(":")
        return float(int(h) * 60 + int(m))
    except Exception as e:
        raise ConfigError(f"Invalid HH:MM format: {hhmm}") from e


def _build_time_mat(points, time_model, *, sample: bool) -> np.ndarray:
    n = len(points)
    mat = np.zeros((n, n), dtype=float)
    for i in range(n):
        a_lat, a_lon = points[i]
        for j in range(n):
            if i == j:
                continue
            b_lat, b_lon = points[j]
            mat[i, j] = (
                float(time_model.sample_travel_min(a_lat, a_lon, b_lat, b_lon))
                if sample
                else float(time_model.mean_travel_min(a_lat, a_lon, b_lat, b_lon))
            )
    return mat


def _split_vehicles_df(g: pd.DataFrame, *, cap: int, max_veh: int) -> List[pd.DataFrame]:
    """기본(legacy) 분할: 그냥 cap씩 chunk."""
    if cap <= 0:
        raise ConfigError(f"capacity must be > 0 (got {cap})")
    if max_veh <= 0:
        raise ConfigError(f"max_vehicles_per_center_slot must be > 0 (got {max_veh})")

    vehicles: List[pd.DataFrame] = []
    for i in range(0, len(g), cap):
        if len(vehicles) >= max_veh:
            break
        vehicles.append(g.iloc[i : i + cap].reset_index(drop=True))
    return vehicles


def _simulate_timeline(
    route_points: Sequence[int],
    dist_mat: np.ndarray,
    *,
    start_min: float | None,
    end_at: float | None,
) -> List[float]:
    seg = [float(dist_mat[a, b]) for a, b in zip(route_points[:-1], route_points[1:])]
    total = float(sum(seg))

    if start_min is None and end_at is not None:
        start_min = float(end_at) - total
    if start_min is None:
        start_min = 0.0

    t = float(start_min)
    times = [t]
    for s in seg:
        t += s
        times.append(t)
    return times


def _render_leaflet_html(map_data: dict) -> str:
    """Render a tiny Leaflet HTML.

    - No extra Python deps.
    - Designed to be opened directly (or served) for quick visual sanity checks.
    """
    vehicles = map_data.get("vehicles") or []
    all_pts: List[Tuple[float, float]] = []
    for v in vehicles:
        for lat, lon in v.get("coords", []):
            try:
                all_pts.append((float(lat), float(lon)))
            except Exception:
                continue

    if all_pts:
        lat0 = sum(p[0] for p in all_pts) / len(all_pts)
        lon0 = sum(p[1] for p in all_pts) / len(all_pts)
    else:
        lat0, lon0 = 37.5665, 126.9780  # Seoul fallback

    payload = json.dumps(map_data, ensure_ascii=False)

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Bandabi Route Map</title>
    <link
      rel="stylesheet"
      href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
      crossorigin=""
    />
    <style>
      html, body, #map {{ height: 100%; margin: 0; }}
      .legend {{ position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.65); color: #fff; padding: 10px 12px; font: 12px/1.4 system-ui; border-radius: 10px; max-width: 360px; }}
      .legend code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
    </style>
  </head>
  <body>
    <div id="map"></div>
    <div class="legend">
      <div><strong>Bandabi Route Map</strong></div>
      <div style="opacity:.85">Straight-line polyline (not road graph)</div>
      <div style="margin-top:6px">vehicles: <code>{len(vehicles)}</code></div>
    </div>
    <script
      src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
      integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
      crossorigin=""
    ></script>
    <script>
      const MAP_DATA = {payload};
      const map = L.map('map').setView([{lat0}, {lon0}], 12);
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      }}).addTo(map);

      const colors = ['#00d0ff', '#00ffa2', '#ffd000', '#ff5c8a', '#a66bff', '#ffffff'];
      const bounds = [];

      (MAP_DATA.vehicles || []).forEach((v, idx) => {{
        const coords = (v.coords || []).map(p => [p[0], p[1]]);
        if (!coords.length) return;
        const color = colors[idx % colors.length];
        const line = L.polyline(coords, {{ color, weight: 4, opacity: 0.85 }}).addTo(map);
        line.bindTooltip(v.vehicle_id || `vehicle_${{idx}}`, {{ sticky: true }});
        coords.forEach((p, i) => {{
          const icon = i === 0 ? '🏁' : (i === coords.length - 1 ? '✅' : '📍');
          L.circleMarker(p, {{ radius: 5, weight: 1, opacity: 0.9, fillOpacity: 0.7 }}).addTo(map)
            .bindPopup(`${{icon}} ${{v.vehicle_id}}<br/>stop_seq=${{i}}`);
          bounds.push(p);
        }});
      }});

      if (bounds.length) {{
        map.fitBounds(bounds, {{ padding: [30, 30] }});
      }}
    </script>
  </body>
</html>"""


def _save_outputs(
    out_dir: str,
    events_df: pd.DataFrame,
    routes_vehicle_df: pd.DataFrame,
    routes_stops_df: pd.DataFrame,
    kpis: dict,
    *,
    map_data: dict,
    write_map_data: bool,
    write_map_html: bool,
) -> None:
    os.makedirs(out_dir, exist_ok=True)
    events_df.to_csv(os.path.join(out_dir, "events.csv"), index=False, encoding="utf-8-sig")

    # ✅ 기존 호환: routes.csv = 차량(버스) 요약
    routes_vehicle_df.to_csv(os.path.join(out_dir, "routes.csv"), index=False, encoding="utf-8-sig")

    # ✅ 신규: 정류장(Stop) 단위 rows (Map jump/highlight용)
    routes_stops_df.to_csv(os.path.join(out_dir, "routes_stops.csv"), index=False, encoding="utf-8-sig")

    pd.DataFrame([kpis]).to_csv(os.path.join(out_dir, "metrics.csv"), index=False, encoding="utf-8-sig")

    if write_map_data:
        with open(os.path.join(out_dir, "map_data.json"), "w", encoding="utf-8") as f:
            json.dump(map_data, f, ensure_ascii=False, indent=2)

    if write_map_html:
        html = _render_leaflet_html(map_data)
        with open(os.path.join(out_dir, "map.html"), "w", encoding="utf-8") as f:
            f.write(html)


def run(cfg: dict, out_dir: str) -> dict:
    """Run one simulation and write artifacts."""
    t0 = time.time()
    os.makedirs(out_dir, exist_ok=True)

    # ---- validate minimal config ----
    try:
        centers_path = cfg["paths"]["centers_xlsx"]
        gu_list = cfg["area"]["gu_list"]
        to_slots = cfg["service"]["to_center_timeslots"]
        fleet_cfg = cfg["fleet"]
        routing_cfg = cfg.get("routing", {})
    except KeyError as e:
        raise ConfigError(f"Missing config key: {e}") from e

    centers = load_centers(centers_path, list(gu_list))
    tm = build_time_model(cfg)

    out_cfg = cfg.get("outputs", {}) if isinstance(cfg.get("outputs", {}), dict) else {}
    write_map_data = bool(out_cfg.get("write_map_data", True))
    write_map_html = bool(out_cfg.get("write_map_html", True))

    # MVP: to_center only
    req_to = build_requests(centers, to_slots, cfg, mode="to_center")

    all_events: List[dict] = []
    route_rows_vehicle: List[dict] = []
    route_rows_stops: List[dict] = []
    map_vehicles: List[dict] = []

    if req_to.empty:
        events_df = pd.DataFrame()
        routes_vehicle_df = pd.DataFrame()
        routes_stops_df = pd.DataFrame()
        kpis = compute_kpis(events_df, cfg)
        kpis["vehicles_used"] = 0
        kpis["total_travel_time_min"] = 0.0
        kpis["total_travel_time"] = 0.0
        kpis["runtime_total_sec"] = float(time.time() - t0)

        _save_outputs(
            out_dir,
            events_df,
            routes_vehicle_df,
            routes_stops_df,
            kpis,
            map_data={"vehicles": []},
            write_map_data=write_map_data,
            write_map_html=write_map_html,
        )
        return kpis

    # ✅ method를 run 전체에서 일관되게 사용
    method = str(routing_cfg.get("method", "euclid_nn"))
    improve_2opt = bool(routing_cfg.get("improve_2opt", False))

    # ✅ cluster_first면 내부 라우팅 설정을 따로 받음
    cluster_cfg = routing_cfg.get("cluster", {}) if isinstance(routing_cfg.get("cluster", {}), dict) else {}
    if method == "cluster_first":
        cluster_strategy = str(cluster_cfg.get("strategy", "center_dist"))  # "chunk" | "center_dist"
        cluster_seed = int(cluster_cfg.get("seed", 0))
        cluster_lat_col = str(cluster_cfg.get("lat_col", "pickup_lat"))
        cluster_lon_col = str(cluster_cfg.get("lon_col", "pickup_lon"))

        inner_method = str(cluster_cfg.get("inner_method", "time_nn"))
        inner_improve_2opt = bool(cluster_cfg.get("inner_improve_2opt", True))
    else:
        cluster_strategy = "chunk"
        cluster_seed = 0
        cluster_lat_col = "pickup_lat"
        cluster_lon_col = "pickup_lon"
        inner_method = method
        inner_improve_2opt = improve_2opt

    # group by center/slot/bus_type
    for (center_id, ts, bus_type), g in req_to.groupby(
        ["center_id", "timeslot", "bus_type"], dropna=False
    ):
        g = g.reset_index(drop=True)

        cap = int(fleet_cfg["capacity_wc"] if bus_type == "WC" else fleet_cfg["capacity_gen"])
        max_veh = int(fleet_cfg["max_vehicles_per_center_slot"])

        center_lat = float(g.loc[0, "center_lat"])
        center_lon = float(g.loc[0, "center_lon"])
        center_promise_min = _hhmm_to_min(str(ts))

        # ✅ 차량(버스) 분할
        if method == "cluster_first":
            vehicles = split_requests_into_buses(
                g,
                center_lat=center_lat,
                center_lon=center_lon,
                cap=cap,
                max_bus=max_veh,
                lat_col=cluster_lat_col,
                lon_col=cluster_lon_col,
                strategy=cluster_strategy,
                seed=cluster_seed,
            )
        else:
            vehicles = _split_vehicles_df(g, cap=cap, max_veh=max_veh)

        if not vehicles:
            continue

        # ✅ 각 vehicle group마다 TSP 실행
        for v_idx, v_reqs in enumerate(vehicles):
            vehicle_id = f"v{center_id}_{ts}_{bus_type}_{v_idx}"

            points: List[Tuple[float, float]] = [(center_lat, center_lon)]
            for _, r in v_reqs.iterrows():
                points.append((float(r["pickup_lat"]), float(r["pickup_lon"])))

            if len(points) <= 1:
                continue

            dist_mean = _build_time_mat(points, tm, sample=False)
            dist_act = _build_time_mat(points, tm, sample=True)

            # ✅ TSP 실행 방식 결정
            tsp_method = inner_method if method == "cluster_first" else method
            tsp_2opt = inner_improve_2opt if method == "cluster_first" else improve_2opt

            route_points = solve_tsp(
                points,
                dist_mean if tsp_method == "time_nn" else None,
                method=tsp_method,
                improve_2opt=tsp_2opt,
            )

            # ---- stop objects (for map_data + stop-level csv) ----
            stops = []
            for i, node in enumerate(route_points):
                is_first = i == 0
                is_last = i == (len(route_points) - 1)
                if int(node) == 0:
                    stop_type = "depot" if is_first else ("center" if is_last else "depot")
                    request_ids = ""
                else:
                    stop_type = "pickup"
                    req_row = v_reqs.iloc[int(node) - 1]
                    rid = str(req_row.get("req_id", req_row.get("request_id", f"{vehicle_id}_node{node}")))
                    request_ids = rid

                lat = float(points[int(node)][0])
                lon = float(points[int(node)][1])

                stops.append(
                    {
                        "stop_seq": int(i),
                        "node_idx": int(node),
                        "lat": lat,
                        "lon": lon,
                        "kind": stop_type,
                    }
                )

                # ✅ stop-level rows for routes_stops.csv
                route_rows_stops.append(
                    {
                        "vehicle_id": vehicle_id,
                        "center_id": int(center_id),
                        "timeslot": str(ts),
                        "bus_type": str(bus_type),
                        "stop_seq": int(i),
                        "node_idx": int(node),
                        "stop_type": stop_type,
                        "request_ids": request_ids,
                        "lat": lat,
                        "lon": lon,
                    }
                )

            map_vehicles.append(
                {
                    "vehicle_id": vehicle_id,
                    "center_id": int(center_id),
                    "timeslot": str(ts),
                    "bus_type": str(bus_type),
                    "coords": [[float(points[int(node)][0]), float(points[int(node)][1])] for node in route_points],
                    "stops": stops,
                }
            )

            promise_times = _simulate_timeline(route_points, dist_mean, start_min=None, end_at=center_promise_min)
            actual_times = _simulate_timeline(route_points, dist_act, start_min=promise_times[0], end_at=None)

            promise_at = {int(node): float(promise_times[i]) for i, node in enumerate(route_points)}
            actual_at = {int(node): float(actual_times[i]) for i, node in enumerate(route_points)}

            # events: request(승객) 단위
            for stop_seq, node in enumerate(route_points):
                if int(node) == 0:
                    continue
                req_row = v_reqs.iloc[int(node) - 1]
                rid = str(req_row.get("req_id", req_row.get("request_id", f"{vehicle_id}_node{node}")))

                pickup_lat, pickup_lon = points[int(node)]

                all_events.append(
                    {
                        "center_id": int(center_id),
                        "timeslot": str(ts),
                        "bus_type": str(bus_type),
                        "vehicle_id": vehicle_id,
                        "request_id": rid,
                        "node_idx": int(node),
                        "stop_seq": int(stop_seq),
                        "pickup_lat": float(pickup_lat),
                        "pickup_lon": float(pickup_lon),
                        "center_lat": float(center_lat),
                        "center_lon": float(center_lon),
                        "pickup_promise_min": float(promise_at[int(node)]),
                        "pickup_actual_min": float(actual_at[int(node)]),
                        "center_promise_min": float(promise_times[-1]),
                        "center_actual_min": float(actual_times[-1]),
                        "ride_time_min": float(actual_times[-1] - actual_at[int(node)]),
                    }
                )

            # routes.csv (vehicle-level summary)
            route_rows_vehicle.append(
                {
                    "vehicle_id": vehicle_id,
                    "center_id": int(center_id),
                    "timeslot": str(ts),
                    "bus_type": str(bus_type),
                    "route": ",".join(map(str, route_points)),
                    "center_lat": float(center_lat),
                    "center_lon": float(center_lon),
                    "stops_json": json.dumps(stops, ensure_ascii=False),
                    "start_promise_min": float(promise_times[0]),
                    "end_promise_min": float(promise_times[-1]),
                    "start_actual_min": float(actual_times[0]),
                    "end_actual_min": float(actual_times[-1]),
                    "route_duration_actual_min": float(actual_times[-1] - actual_times[0]),
                    # ✅ 디버깅/분석용
                    "routing_method": str(method),
                    "tsp_method": str(tsp_method),
                    "tsp_improve_2opt": bool(tsp_2opt),
                    "cluster_strategy": str(cluster_strategy) if method == "cluster_first" else "",
                }
            )

    events_df = pd.DataFrame(all_events) if all_events else pd.DataFrame()
    routes_vehicle_df = pd.DataFrame(route_rows_vehicle) if route_rows_vehicle else pd.DataFrame()
    routes_stops_df = pd.DataFrame(route_rows_stops) if route_rows_stops else pd.DataFrame()

    kpis = compute_kpis(events_df, cfg)
    vehicles_used = int(routes_vehicle_df["vehicle_id"].nunique()) if not routes_vehicle_df.empty else 0
    total_travel_time_min = float(routes_vehicle_df["route_duration_actual_min"].sum()) if not routes_vehicle_df.empty else 0.0

    kpis["vehicles_used"] = vehicles_used
    kpis["total_travel_time_min"] = total_travel_time_min
    # compatibility alias
    kpis["total_travel_time"] = total_travel_time_min
    kpis["runtime_total_sec"] = float(time.time() - t0)

    _save_outputs(
        out_dir,
        events_df,
        routes_vehicle_df,
        routes_stops_df,
        kpis,
        map_data={"vehicles": map_vehicles},
        write_map_data=write_map_data,
        write_map_html=write_map_html,
    )
    return kpis
