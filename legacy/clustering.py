# clustering.py

import numpy as np
import pandas as pd


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    )
    c = 2 * np.arcsin(np.sqrt(a))
    return float(R * c)


def assign_bus_clusters(
    demand_df: pd.DataFrame,
    centers: pd.DataFrame,
    gen_capacity: int,
    wc_capacity: int,
    max_gen_per_slot: int,
    max_wc_per_slot: int,
) -> pd.DataFrame:
    """
    demand_df: [req_id, lat, lon, bus_type, center_name, arrival_slot]
    centers:   [center_name, lat, lon]
    반환: demand_df + [bus_id]
    """

    centers_map = {
        row.center_name: (row.lat, row.lon) for _, row in centers.iterrows()
    }

    demand_df = demand_df.copy()
    demand_df["bus_id"] = -1

    for (cname, slot, btype), group_idx in demand_df.groupby(
        ["center_name", "arrival_slot", "bus_type"]
    ).groups.items():
        idxs = list(group_idx)
        if len(idxs) == 0:
            continue

        c_lat, c_lon = centers_map[cname]
        sub = demand_df.loc[idxs].copy()

        # 센터와 거리 계산
        dists = []
        for i, row in sub.iterrows():
            d = _haversine_km(c_lat, c_lon, row.lat, row.lon)
            dists.append(d)
        sub["center_dist"] = dists

        # 가까운 순 정렬
        sub = sub.sort_values("center_dist").reset_index()

        cap = gen_capacity if btype == "GEN" else wc_capacity
        max_bus = max_gen_per_slot if btype == "GEN" else max_wc_per_slot

        # 버스 번호 할당
        bus_ids = []
        current_bus = 1
        count_in_bus = 0

        for _i, r in sub.iterrows():
            if current_bus > max_bus:
                # 더 태울 수 있는 버스가 없으면 마지막 버스에 몰아넣기
                bus_ids.append(max_bus)
                continue
            bus_ids.append(current_bus)
            count_in_bus += 1
            if count_in_bus >= cap:
                current_bus += 1
                count_in_bus = 0

        sub["bus_id"] = bus_ids

        # 원본에 반영
        demand_df.loc[sub["index"], "bus_id"] = sub["bus_id"].values

    return demand_df
