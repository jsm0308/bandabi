# metrics.py
import numpy as np
import pandas as pd

def compute_kpis(events_df, routes_df, cfg):
    """KPI 계산"""
    kpis = {}
    
    if len(events_df) == 0:
        # 요청 없음
        return {
            "pickup_late_mean": 0,
            "pickup_late_p95": 0,
            "pickup_on_time_rate": 100.0,
            "center_late_mean": 0,
            "center_late_p95": 0,
            "center_on_time_rate": 100.0,
            "ride_time_mean": 0,
            "ride_time_p95": 0,
            "vehicles_used": 0,
            "total_travel_time": 0,
            "runtime_total_sec": 0
        }
    
    threshold = cfg["kpi"].get("on_time_threshold_min", 5)
    
    # 더미 KPI
    late_mins = np.random.randn(len(events_df)) * 5 + 2
    ride_times = np.random.uniform(15, 45, len(events_df))
    
    kpis["pickup_late_mean"] = float(np.mean(late_mins[late_mins > 0]))
    kpis["pickup_late_p95"] = float(np.percentile(late_mins[late_mins > 0], 95) if np.any(late_mins > 0) else 0)
    kpis["pickup_on_time_rate"] = float(np.mean(late_mins <= threshold) * 100)
    
    kpis["center_late_mean"] = float(np.mean(late_mins[late_mins > 0]))
    kpis["center_late_p95"] = float(np.percentile(late_mins[late_mins > 0], 95) if np.any(late_mins > 0) else 0)
    kpis["center_on_time_rate"] = float(np.mean(late_mins <= threshold) * 100)
    
    kpis["ride_time_mean"] = float(np.mean(ride_times))
    kpis["ride_time_p95"] = float(np.percentile(ride_times, 95))
    
    kpis["vehicles_used"] = len(routes_df) if len(routes_df) > 0 else 0
    kpis["total_travel_time"] = float(np.sum(ride_times))
    kpis["runtime_total_sec"] = 0.0
    
    return kpis

import numpy as np
import pandas as pd

def _summ(x):
    x = np.array(x, dtype=float)
    if len(x) == 0:
        return {"mean": 0, "p95": 0, "max": 0}
    return {
        "mean": float(np.mean(x)),
        "p95": float(np.percentile(x, 95)),
        "max": float(np.max(x)),
    }

def compute_kpis(events_df: pd.DataFrame, cfg: dict) -> dict:
    """
    events_df columns (min):
      - pickup_promise_min, pickup_actual_min
      - center_promise_min, center_actual_min
      - ride_time_min
      (drop leg이면 drop_promise/actual도 추가 가능)
    """
    thr = float(cfg["kpi"]["on_time_threshold_min"])

    pickup_late = events_df["pickup_actual_min"] - events_df["pickup_promise_min"]
    center_late = events_df["center_actual_min"] - events_df["center_promise_min"]

    out = {}
    out.update({f"pickup_late_{k}": v for k, v in _summ(pickup_late).items()})
    out.update({f"center_late_{k}": v for k, v in _summ(center_late).items()})

    out["pickup_on_time_rate"] = float(np.mean(pickup_late <= thr))
    out["center_on_time_rate"] = float(np.mean(center_late <= thr))

    out.update({f"ride_time_{k}": v for k, v in _summ(events_df["ride_time_min"]).items()})

    return out
