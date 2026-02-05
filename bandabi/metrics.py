"""KPI computation.

Contract (events.csv minimum columns):
- pickup_promise_min, pickup_actual_min
- center_promise_min, center_actual_min
- ride_time_min

Important: these KPIs are used for experiment comparison, so they must be
pure/deterministic given the input data.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd

from .config import ConfigError


def _summ(x: np.ndarray) -> Dict[str, float]:
    if x.size == 0:
        return {"mean": 0.0, "p95": 0.0, "max": 0.0}
    return {
        "mean": float(np.mean(x)),
        "p95": float(np.percentile(x, 95)),
        "max": float(np.max(x)),
    }


def compute_kpis(events_df: pd.DataFrame, cfg: dict) -> dict:
    """Compute KPIs from events.

    Rates are returned as fractions (0..1) to keep math stable.
    UI can render as percentage.
    """
    if events_df is None or len(events_df) == 0:
        return {
            "pickup_late_mean": 0.0,
            "pickup_late_p95": 0.0,
            "pickup_late_max": 0.0,
            "center_late_mean": 0.0,
            "center_late_p95": 0.0,
            "center_late_max": 0.0,
            "pickup_on_time_rate": 1.0,
            "center_on_time_rate": 1.0,
            "ride_time_mean": 0.0,
            "ride_time_p95": 0.0,
            "ride_time_max": 0.0,
        }

    kpi_cfg = cfg.get("kpi")
    if not isinstance(kpi_cfg, dict) or "on_time_threshold_min" not in kpi_cfg:
        raise ConfigError("Missing kpi.on_time_threshold_min in config")
    thr = float(kpi_cfg["on_time_threshold_min"])

    required = [
        "pickup_promise_min",
        "pickup_actual_min",
        "center_promise_min",
        "center_actual_min",
        "ride_time_min",
    ]
    missing = [c for c in required if c not in events_df.columns]
    if missing:
        raise ConfigError(f"events_df missing columns: {missing}. Available: {list(events_df.columns)}")

    pickup_late = (events_df["pickup_actual_min"] - events_df["pickup_promise_min"]).to_numpy(dtype=float)
    center_late = (events_df["center_actual_min"] - events_df["center_promise_min"]).to_numpy(dtype=float)
    ride_time = events_df["ride_time_min"].to_numpy(dtype=float)

    out: dict = {}
    out.update({f"pickup_late_{k}": v for k, v in _summ(pickup_late).items()})
    out.update({f"center_late_{k}": v for k, v in _summ(center_late).items()})

    out["pickup_on_time_rate"] = float(np.mean(pickup_late <= thr))
    out["center_on_time_rate"] = float(np.mean(center_late <= thr))

    out.update({f"ride_time_{k}": v for k, v in _summ(ride_time).items()})
    return out
