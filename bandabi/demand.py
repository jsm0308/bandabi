"""Demand generation.

Responsibilities
- Load sports-center locations from `centers.xlsx`.
- Sample passenger requests around selected centers.

Notes
- The project relies on reproducibility for fair experiment comparison.
  Randomness is therefore controlled by config seeds.
- By default, this module fails fast if input data is missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd

from .config import ConfigError


REQUIRED_CENTER_COLUMNS = [
    "SIGNGU_NM",
    "FCLTY_NM",
    "FCLTY_CRDNT_LA",
    "FCLTY_CRDNT_LO",
]


def load_centers(centers_xlsx: str, gu_list: List[str]) -> pd.DataFrame:
    """Load centers from Excel.

    Args:
        centers_xlsx: Path to centers.xlsx.
        gu_list: Either ["ALL"] or list of district names (SIGNGU_NM values).

    Raises:
        FileNotFoundError: If centers_xlsx does not exist.
        ConfigError: If required columns are missing.

    Returns:
        DataFrame of centers.
    """
    df = pd.read_excel(centers_xlsx)
    missing = [c for c in REQUIRED_CENTER_COLUMNS if c not in df.columns]
    if missing:
        raise ConfigError(
            f"centers.xlsx missing required columns: {missing}. "
            f"Available columns: {list(df.columns)}"
        )

    if gu_list != ["ALL"]:
        df = df[df["SIGNGU_NM"].isin(gu_list)].copy()

    df = df.dropna(subset=["FCLTY_CRDNT_LA", "FCLTY_CRDNT_LO"]).reset_index(drop=True)
    return df


def _sample_point_near(lat: float, lon: float, rmin_km: float, rmax_km: float, rng: np.random.Generator) -> Tuple[float, float]:
    """Sample a point in an annulus around (lat, lon).

    This uses a rough spherical approximation for small distances.
    """
    if rmin_km < 0 or rmax_km <= 0 or rmin_km > rmax_km:
        raise ConfigError(f"Invalid radius range: rmin_km={rmin_km}, rmax_km={rmax_km}")

    r = rng.uniform(rmin_km, rmax_km) / 111.0  # approx km -> degrees latitude
    theta = rng.uniform(0, 2 * np.pi)
    dlat = r * np.cos(theta)
    dlon = (r * np.sin(theta)) / max(1e-8, np.cos(np.deg2rad(lat)))
    return float(lat + dlat), float(lon + dlon)


@dataclass(frozen=True)
class DemandConfig:
    n_requests_per_timeslot: int
    wheel_ratio: float
    seed: int
    radius_min_km: float
    radius_max_km: float

    @staticmethod
    def from_cfg(cfg: dict, *, mode: str) -> "DemandConfig":
        dcfg = cfg.get("demand")
        if not isinstance(dcfg, dict):
            raise ConfigError("Missing 'demand' section in config")

        try:
            n = int(dcfg["n_requests_per_timeslot"])
            wheel_ratio = float(dcfg["wheel_ratio"])
            seed = int(dcfg.get("seed", 42))
            rmin = float(dcfg["radius_min_km"])
            rmax = float(dcfg["radius_max_km"])
        except KeyError as e:
            raise ConfigError(f"Missing demand config key: {e}") from e

        if n <= 0:
            raise ConfigError(f"n_requests_per_timeslot must be > 0 (got {n})")
        if not (0.0 <= wheel_ratio <= 1.0):
            raise ConfigError(f"wheel_ratio must be in [0,1] (got {wheel_ratio})")

        # mode-specific seed offset to keep deterministic but different distributions
        mode_offset = 0 if mode == "to_center" else 777
        return DemandConfig(
            n_requests_per_timeslot=n,
            wheel_ratio=wheel_ratio,
            seed=seed + mode_offset,
            radius_min_km=rmin,
            radius_max_km=rmax,
        )


def build_requests(
    centers_df: pd.DataFrame,
    timeslots: Iterable[str],
    cfg: dict,
    *,
    mode: str,
) -> pd.DataFrame:
    """Generate passenger requests.

    Args:
        centers_df: Output of load_centers().
        timeslots: Reservation slots.
        cfg: merged configuration dict.
        mode: "to_center" or "from_center".

    Returns:
        A DataFrame containing generated requests.

    Schema (minimum):
        req_id, timeslot, gu, center_id, center_name,
        center_lat, center_lon, pickup_lat, pickup_lon, drop_lat, drop_lon, bus_type
    """
    if mode not in {"to_center", "from_center"}:
        raise ConfigError(f"Invalid mode: {mode}")
    if centers_df.empty:
        return pd.DataFrame()

    dcfg = DemandConfig.from_cfg(cfg, mode=mode)
    rng = np.random.default_rng(dcfg.seed)

    reqs: List[dict] = []
    timeslots = list(timeslots)

    for ts in timeslots:
        for i in range(dcfg.n_requests_per_timeslot):
            cidx = int(rng.integers(0, len(centers_df)))
            c = centers_df.iloc[cidx]
            center_lat = float(c["FCLTY_CRDNT_LA"])
            center_lon = float(c["FCLTY_CRDNT_LO"])
            home_lat, home_lon = _sample_point_near(
                center_lat,
                center_lon,
                dcfg.radius_min_km,
                dcfg.radius_max_km,
                rng,
            )
            is_wc = bool(rng.random() < dcfg.wheel_ratio)

            if mode == "to_center":
                pickup_lat, pickup_lon = home_lat, home_lon
                drop_lat, drop_lon = center_lat, center_lon
            else:
                pickup_lat, pickup_lon = center_lat, center_lon
                drop_lat, drop_lon = home_lat, home_lon

            reqs.append(
                {
                    "req_id": f"{mode}_{ts}_{i}",
                    "timeslot": ts,
                    "gu": str(c["SIGNGU_NM"]),
                    "center_id": int(cidx),
                    "center_name": str(c["FCLTY_NM"]),
                    "center_lat": center_lat,
                    "center_lon": center_lon,
                    "pickup_lat": float(pickup_lat),
                    "pickup_lon": float(pickup_lon),
                    "drop_lat": float(drop_lat),
                    "drop_lon": float(drop_lon),
                    "bus_type": "WC" if is_wc else "GEN",
                }
            )

    return pd.DataFrame(reqs)
