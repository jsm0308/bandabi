# demand.py
import numpy as np
import pandas as pd

def load_centers(centers_xlsx: str, gu_list):
    """더미: centers_xlsx 파일이 없으면 샘플 데이터 생성"""
    try:
        df = pd.read_excel(centers_xlsx)
        if gu_list != ["ALL"]:
            df = df[df["SIGNGU_NM"].isin(gu_list)].copy()
        df = df.dropna(subset=["FCLTY_CRDNT_LA", "FCLTY_CRDNT_LO"])
        return df.reset_index(drop=True)
    except:
        # 더미 데이터
        return pd.DataFrame({
            "center_id": [1, 2, 3],
            "center_name": ["Center A", "Center B", "Center C"],
            "FCLTY_CRDNT_LA": [37.4979, 37.5665, 37.6411],
            "FCLTY_CRDNT_LO": [126.9628, 126.9780, 127.0995],
            "SIGNGU_NM": ["강남구", "종로구", "송파구"]
        })

def build_requests(centers, timeslots, cfg, mode="to_center"):
    """요청(픽업/드롭) 생성"""
    rows = []
    np.random.seed(42)
    
    for _, center in centers.iterrows():
        center_id = center.get("center_id", center.name)
        center_lat = center["FCLTY_CRDNT_LA"]
        center_lon = center["FCLTY_CRDNT_LO"]
        
        # timeslot마다 5~10명 요청
        for ts in timeslots:
            n_req = np.random.randint(5, 11)
            for _ in range(n_req):
                # 센터 주변 1km 랜덤 포인트
                lat = center_lat + np.random.randn() * 0.01
                lon = center_lon + np.random.randn() * 0.01
                
                bus_type = "WC" if np.random.random() < 0.2 else "GEN"
                
                rows.append({
                    "request_id": f"{center_id}_{ts}_{len(rows)}",
                    "center_id": center_id,
                    "center_lat": center_lat,
                    "center_lon": center_lon,
                    "home_lat": lat,
                    "home_lon": lon,
                    "timeslot": ts,
                    "bus_type": bus_type,
                    "mode": mode
                })
    
    return pd.DataFrame(rows)

import numpy as np
import pandas as pd

def load_centers(centers_xlsx: str, gu_list):
    df = pd.read_excel(centers_xlsx)
    if gu_list != ["ALL"]:
        df = df[df["SIGNGU_NM"].isin(gu_list)].copy()
    df = df.dropna(subset=["FCLTY_CRDNT_LA", "FCLTY_CRDNT_LO"])
    df = df.reset_index(drop=True)
    return df

def _sample_point_near(lat, lon, rmin_km, rmax_km, rng):
    # 간단 구면근사: 반경 랜덤 + 각도 랜덤
    r = rng.uniform(rmin_km, rmax_km) / 111.0  # 대략 deg 변환
    theta = rng.uniform(0, 2*np.pi)
    dlat = r * np.cos(theta)
    dlon = r * np.sin(theta) / np.cos(np.deg2rad(lat))
    return float(lat + dlat), float(lon + dlon)

def build_requests(centers_df: pd.DataFrame, timeslots, cfg: dict, mode: str):
    """
    mode: "to_center" or "from_center"
    to_center: pickup=home, drop=center
    from_center: pickup=center, drop=home
    """
    dcfg = cfg["demand"]
    rng = np.random.default_rng(dcfg["seed"] + (0 if mode=="to_center" else 777))
    n = int(dcfg["n_requests_per_timeslot"])
    wheel_ratio = float(dcfg["wheel_ratio"])

    reqs = []
    for ts in timeslots:
        for i in range(n):
            cidx = int(rng.integers(0, len(centers_df)))
            c = centers_df.iloc[cidx]
            center_lat, center_lon = float(c["FCLTY_CRDNT_LA"]), float(c["FCLTY_CRDNT_LO"])
            home_lat, home_lon = _sample_point_near(center_lat, center_lon, dcfg["radius_min_km"], dcfg["radius_max_km"], rng)
            is_wc = (rng.random() < wheel_ratio)

            if mode == "to_center":
                pickup_lat, pickup_lon = home_lat, home_lon
                drop_lat, drop_lon = center_lat, center_lon
            else:
                pickup_lat, pickup_lon = center_lat, center_lon
                drop_lat, drop_lon = home_lat, home_lon

            reqs.append({
                "req_id": f"{mode}_{ts}_{i}",
                "timeslot": ts,                 # 예약 기준 슬롯(센터도착 or 센터출발)
                "gu": c["SIGNGU_NM"],
                "center_id": cidx,
                "center_name": c["FCLTY_NM"],
                "center_lat": center_lat,
                "center_lon": center_lon,
                "pickup_lat": pickup_lat,
                "pickup_lon": pickup_lon,
                "drop_lat": drop_lat,
                "drop_lon": drop_lon,
                "bus_type": "WC" if is_wc else "GEN",
            })
    return pd.DataFrame(reqs)
