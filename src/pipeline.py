# src/pipeline.py
# (본체) demand -> time_model -> route -> simulate -> metrics -> save
# 목적: 한 번의 실행(run)에서
#   1) 수요 생성
#   2) 이동시간 행렬 생성
#   3) 차량별 경로(TSP) 생성
#   4) 약속/실제 타임라인 생성
#   5) 이벤트/라우트 로그 저장 + KPI 계산
#
# 현재는 to_center(집 -> 센터)만 처리

import os
import time
import numpy as np
import pandas as pd
import inspect

from .demand import load_centers, build_requests
from .time_model import build_time_model
from .route_solver import solve_tsp
from .metrics import compute_kpis


# -------------------------
# Helper: (n,n) 이동시간 행렬 생성
# -------------------------
def _build_time_mat(points, time_model, sample: bool = False) -> np.ndarray:
    """
    points: [(lat, lon), ...] 0번은 센터(Depot), 1..k는 승객 위치
    sample=False: 평균 이동시간(약속 ETA용)
    sample=True : 샘플 이동시간(실제 도착용, 노이즈 포함)
    """
    n = len(points)
    mat = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a_lat, a_lon = points[i]
            b_lat, b_lon = points[j]
            if sample:
                mat[i, j] = float(time_model.sample_travel_min(a_lat, a_lon, b_lat, b_lon))
            else:
                mat[i, j] = float(time_model.mean_travel_min(a_lat, a_lon, b_lat, b_lon))
    return mat


# -------------------------
# Helper: 차량 분할
# -------------------------
def _split_vehicles_df(g: pd.DataFrame, cap: int, max_veh: int):
    """요청 DataFrame을 cap개씩 잘라 차량별 DataFrame 리스트로 반환"""
    vehicles = []
    for i in range(0, len(g), cap):
        if len(vehicles) >= max_veh:
            break
        vehicles.append(g.iloc[i:i+cap].reset_index(drop=True))
    return vehicles


# -------------------------
# Helper: route를 [0, ..., 0]으로 맞춤
# -------------------------
def _ensure_round_trip(route):
    """
    solve_tsp가 어떤 형태로 반환하든(노드만/0 포함/끝 0 없음) 항상 [0, ..., 0]으로 강제
    """
    r = list(route) if route is not None else []
    if len(r) == 0:
        return [0, 0]
    if r[0] != 0:
        r = [0] + r
    if r[-1] != 0:
        r = r + [0]
    return r


# -------------------------
# Helper: 타임라인 생성
# -------------------------
def _simulate_timeline(route_points, dist_mat, start_min=None, end_at=None):
    """
    route_points: [0, ..., 0]
    dist_mat: (n,n) 이동시간(분)

    - start_min: 출발 시각 고정
    - end_at: 마지막 도착 시각을 end_at로 맞추기 위해 start를 역산(약속 스케줄용)
    """
    seg = []
    for i in range(len(route_points) - 1):
        a = route_points[i]
        b = route_points[i + 1]
        seg.append(float(dist_mat[a, b]))
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


def _hhmm_to_min(hhmm: str) -> float:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


# -------------------------
# 핵심: solve_tsp 호출을 "네 route_solver.py 시그니처에 맞게" 자동 적응
# -------------------------
def _call_solve_tsp(nodes, dist_mat, cfg):
    """
    solve_tsp의 시그니처가 프로젝트마다 달라져도 돌아가게 만든 어댑터.
    가능한 형태들:
      1) solve_tsp(nodes, dist_mat)
      2) solve_tsp(nodes, dist_mat, method)
      3) solve_tsp(dist_mat)
      4) solve_tsp(points, time_model)  (예전 형태)
    """
    method = None
    try:
        method = cfg.get("routing", {}).get("method", None)
    except Exception:
        method = None

    try:
        sig = inspect.signature(solve_tsp)
        params = list(sig.parameters.values())
        n_params = len(params)
    except Exception:
        n_params = None

    # 1) 가장 흔한 형태: (nodes, dist_mat) 또는 (nodes, dist_mat, method)
    if n_params == 2:
        return solve_tsp(nodes, dist_mat)
    if n_params == 3:
        # 세 번째 인자가 keyword를 안 받는 경우가 많아서 positional로 전달
        return solve_tsp(nodes, dist_mat, method)

    # 2) (dist_mat) 형태
    if n_params == 1:
        return solve_tsp(dist_mat)

    # 3) 혹시 keyword method를 받는 구현이라면 시도
    try:
        return solve_tsp(nodes, dist_mat, method=method)
    except TypeError:
        pass

    # 4) 최후의 fallback: (nodes, dist_mat) 시도
    return solve_tsp(nodes, dist_mat)


def _safe_compute_kpis(events_df: pd.DataFrame, routes_df: pd.DataFrame, cfg: dict) -> dict:
    """
    metrics.py 시그니처가 (events,cfg) or (events,routes,cfg) 여도 안전하게 호출
    """
    try:
        return compute_kpis(events_df, cfg)
    except TypeError:
        return compute_kpis(events_df, routes_df, cfg)


def _save_outputs(out_dir: str, events_df: pd.DataFrame, routes_df: pd.DataFrame, kpis: dict) -> None:
    os.makedirs(out_dir, exist_ok=True)
    events_df.to_csv(os.path.join(out_dir, "events.csv"), index=False, encoding="utf-8-sig")
    routes_df.to_csv(os.path.join(out_dir, "routes.csv"), index=False, encoding="utf-8-sig")
    pd.DataFrame([kpis]).to_csv(os.path.join(out_dir, "metrics.csv"), index=False, encoding="utf-8-sig")


# -------------------------
# 메인 파이프라인
# -------------------------
def run(cfg: dict, out_dir: str):
    t0 = time.time()
    os.makedirs(out_dir, exist_ok=True)

    centers = load_centers(cfg["paths"]["centers_xlsx"], cfg["area"]["gu_list"])
    if len(centers) == 0:
        raise RuntimeError("centers.xlsx에서 센터를 하나도 못 읽었습니다. 경로/컬럼 확인 필요")

    tm = build_time_model(cfg)

    # to_center 수요 생성
    to_slots = cfg["service"]["to_center_timeslots"]
    req_to = build_requests(centers, to_slots, cfg, mode="to_center")

    all_events = []
    route_rows = []

    # 요청 없으면 그래도 파일 생성
    if len(req_to) == 0:
        events_df = pd.DataFrame()
        routes_df = pd.DataFrame()
        kpis = _safe_compute_kpis(events_df, routes_df, cfg)
        kpis["runtime_total_sec"] = float(time.time() - t0)
        _save_outputs(out_dir, events_df, routes_df, kpis)
        return kpis

    # 컬럼 확인은 "파이썬 코드 안에서" 찍어야 함 (PowerShell에서 print치면 안됨)
    # print("[DEBUG] req_to columns:", list(req_to.columns))

    # 그룹핑: 같은 센터/슬롯/차량유형끼리 묶기
    for (center_id, ts, bus_type), g in req_to.groupby(["center_id", "timeslot", "bus_type"], dropna=False):
        g = g.reset_index(drop=True)

        cap = cfg["fleet"]["capacity_wc"] if bus_type == "WC" else cfg["fleet"]["capacity_gen"]
        max_veh = cfg["fleet"]["max_vehicles_per_center_slot"]

        vehicles = _split_vehicles_df(g, cap, max_veh)
        if not vehicles:
            continue

        center_lat = float(g.loc[0, "center_lat"])
        center_lon = float(g.loc[0, "center_lon"])
        center_promise_min = _hhmm_to_min(ts)  # 센터 도착 약속시간

        for v_idx, v_reqs in enumerate(vehicles):
            vehicle_id = f"v{center_id}_{ts}_{bus_type}_{v_idx}"

            # points 구성: 0=센터, 1..k=승객(픽업 위치)
            points = [(center_lat, center_lon)]

            # 컬럼 호환: home_lat/home_lon 있으면 사용, 없으면 pickup_lat/pickup_lon 사용
            if ("home_lat" in v_reqs.columns) and ("home_lon" in v_reqs.columns):
                lat_col, lon_col = "home_lat", "home_lon"
            elif ("pickup_lat" in v_reqs.columns) and ("pickup_lon" in v_reqs.columns):
                lat_col, lon_col = "pickup_lat", "pickup_lon"
            else:
                raise KeyError(
                    f"요청 데이터에 승객 좌표 컬럼이 없습니다. "
                    f"필요: (home_lat/home_lon) 또는 (pickup_lat/pickup_lon). 현재: {list(v_reqs.columns)}"
                )

            for _, r in v_reqs.iterrows():
                points.append((float(r[lat_col]), float(r[lon_col])))

            if len(points) <= 1:
                continue

            # 평균/실제 이동시간 행렬
            dist_mean = _build_time_mat(points, tm, sample=False)
            dist_act = _build_time_mat(points, tm, sample=True)

            # TSP 경로: 방문해야 할 노드 1..k
            nodes = list(range(1, len(points)))
            route = solve_tsp(points)
            route_points = _ensure_round_trip(route)

            # 타임라인 생성
            promise_times = _simulate_timeline(route_points, dist_mean, start_min=None, end_at=center_promise_min)
            actual_times = _simulate_timeline(route_points, dist_act, start_min=promise_times[0], end_at=None)

            # 방문 시각 맵
            promise_at = {node: promise_times[i] for i, node in enumerate(route_points)}
            actual_at = {node: actual_times[i] for i, node in enumerate(route_points)}

            # 이벤트 생성
            for node in route_points:
                if node == 0:
                    continue
                req_row = v_reqs.iloc[node - 1]

                # request_id 컬럼명이 바뀔 수 있어서 방어
                rid = None
                for cand in ["request_id", "req_id", "id"]:
                    if cand in v_reqs.columns:
                        rid = str(req_row[cand])
                        break
                if rid is None:
                    rid = f"{vehicle_id}_node{node}"

                all_events.append({
                    "center_id": center_id,
                    "timeslot": ts,
                    "bus_type": bus_type,
                    "vehicle_id": vehicle_id,
                    "request_id": rid,

                    "pickup_promise_min": float(promise_at[node]),
                    "pickup_actual_min": float(actual_at[node]),
                    "center_promise_min": float(promise_times[-1]),
                    "center_actual_min": float(actual_times[-1]),
                    "ride_time_min": float(actual_times[-1] - actual_at[node]),
                })

            # 라우트 로그
            route_rows.append({
                "vehicle_id": vehicle_id,
                "center_id": center_id,
                "timeslot": ts,
                "bus_type": bus_type,
                "route": ",".join(map(str, route_points)),
                "start_promise_min": float(promise_times[0]),
                "end_promise_min": float(promise_times[-1]),
                "start_actual_min": float(actual_times[0]),
                "end_actual_min": float(actual_times[-1]),
                "route_duration_actual_min": float(actual_times[-1] - actual_times[0]),
            })

    events_df = pd.DataFrame(all_events) if all_events else pd.DataFrame()
    routes_df = pd.DataFrame(route_rows) if route_rows else pd.DataFrame()

    # KPI 계산
    kpis = _safe_compute_kpis(events_df, routes_df, cfg)

    # 운영 KPI 추가
    kpis["vehicles_used"] = int(routes_df["vehicle_id"].nunique()) if not routes_df.empty and "vehicle_id" in routes_df.columns else 0
    kpis["total_travel_time_min"] = float(routes_df["route_duration_actual_min"].sum()) if not routes_df.empty and "route_duration_actual_min" in routes_df.columns else 0.0
    kpis["runtime_total_sec"] = float(time.time() - t0)

    _save_outputs(out_dir, events_df, routes_df, kpis)
    return kpis
