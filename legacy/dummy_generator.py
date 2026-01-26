# dummy_generator 내용 여기 붙여넣기
# dummy_generator.py

from typing import List, Dict
import numpy as np
import pandas as pd


def generate_dummy_requests(
    centers: pd.DataFrame,
    cfg: Dict,
) -> pd.DataFrame:
    """
    centers: DataFrame with columns [center_id, center_name, lat, lon]
    returns: DataFrame with columns
        [req_id, lat, lon, bus_type, center_name, arrival_slot]
    """
    n = cfg["n_requests"]
    wheel_ratio = cfg["wheel_ratio"]
    timeslots: List[str] = cfg["timeslots"]
    rmin = cfg["radius_min_km"]
    rmax = cfg["radius_max_km"]
    seed = cfg["seed"]

    rng = np.random.default_rng(seed)
    rows = []

    centers = centers.reset_index(drop=True)

    for i in range(n):
        c = centers.sample(1, random_state=int(rng.integers(1, 1_000_000))).iloc[0]

        # 중심에서 rmin~rmax km 범위 랜덤 위치
        radius_km = rng.uniform(rmin, rmax)
        theta = rng.uniform(0, 2 * np.pi)

        dlat = (radius_km / 111.0) * np.cos(theta)
        dlon = (radius_km / (111.0 * np.cos(np.radians(c.lat)))) * np.sin(theta)

        lat = c.lat + dlat
        lon = c.lon + dlon

        bus_type = "WC" if rng.random() < wheel_ratio else "GEN"
        arrival_slot = rng.choice(timeslots)

        rows.append(
            {
                "req_id": f"req_{i:04d}",
                "lat": lat,
                "lon": lon,
                "bus_type": bus_type,
                "center_name": c.center_name,
                "arrival_slot": arrival_slot,
            }
        )

    df = pd.DataFrame(rows)
    return df
