import numpy as np
import pandas as pd


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    )
    return float(2 * R * np.arcsin(np.sqrt(a)))


def split_requests_into_buses(
    g: pd.DataFrame,
    center_lat: float,
    center_lon: float,
    cap: int,
    max_bus: int,
    lat_col: str,
    lon_col: str,
    strategy: str = "chunk",
    seed: int = 0,
):
    if len(g) == 0:
        return []

    df = g.copy().reset_index(drop=True)

    if strategy == "center_dist":
        dists = []
        for _, r in df.iterrows():
            d = _haversine_km(center_lat, center_lon, r[lat_col], r[lon_col])
            dists.append(d)
        df["center_dist"] = dists
        df = df.sort_values("center_dist").reset_index(drop=True)

    buses = []
    for i in range(0, len(df), cap):
        if len(buses) >= max_bus:
            break
        buses.append(df.iloc[i : i + cap].reset_index(drop=True))

    return buses
