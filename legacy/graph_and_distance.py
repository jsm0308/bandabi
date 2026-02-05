# graph_and_distance.py

from typing import Dict, Tuple, List
import numpy as np
import pandas as pd
import osmnx as ox


def build_osm_graph(place: str = "Seoul, South Korea"):
    """
    전체 서울 그래프 로드.
    Colab에서는 한번만 호출해서 재사용 추천.
    """
    print(f"[OSM] Loading graph for: {place}")
    G = ox.graph_from_place(place, network_type="drive")
    print(
        f"[OSM] graph loaded: nodes={G.number_of_nodes()}, edges={G.number_of_edges()}"
    )
    return G


def build_cluster_nodes(
    centers: pd.DataFrame,
    demand_df: pd.DataFrame,
    center_name: str,
    arrival_slot: str,
    bus_type: str,
    bus_id: int,
) -> Tuple[pd.DataFrame, Dict[int, Tuple[float, float]]]:
    """
    하나의 클러스터(센터+슬롯+버스타입+버스id)에 대해
    0: depot(센터), 1..N: 승객 으로 index 부여.
    반환:
      nodes_df: [node_idx, kind, req_id, lat, lon]
      idx_to_coord: {node_idx: (lat, lon)}
    """
    # 센터
    c_row = centers[centers["center_name"] == center_name].iloc[0]
    c_lat, c_lon = float(c_row.lat), float(c_row.lon)

    # 해당 버스 승객
    mask = (
        (demand_df["center_name"] == center_name)
        & (demand_df["arrival_slot"] == arrival_slot)
        & (demand_df["bus_type"] == bus_type)
        & (demand_df["bus_id"] == bus_id)
    )
    sub = demand_df[mask].reset_index(drop=True)

    rows = []
    rows.append(
        {"node_idx": 0, "kind": "depot", "req_id": None, "lat": c_lat, "lon": c_lon}
    )
    for i, row in sub.iterrows():
        rows.append(
            {
                "node_idx": i + 1,
                "kind": "passenger",
                "req_id": row.req_id,
                "lat": float(row.lat),
                "lon": float(row.lon),
            }
        )

    nodes_df = pd.DataFrame(rows)
    idx_to_coord = {
        int(r.node_idx): (float(r.lat), float(r.lon)) for _, r in nodes_df.iterrows()
    }

    return nodes_df, idx_to_coord


def compute_distance_matrix_osm(
    G,
    idx_to_coord: Dict[int, Tuple[float, float]],
) -> np.ndarray:
    """
    OSMnx shortest_path 기준 실제 도로 거리행렬 생성.
    dist_mat[i,j] = i -> j (미터)
    """
    node_idxs: List[int] = sorted(idx_to_coord.keys())
    n = len(node_idxs)
    dist_mat = np.zeros((n, n), dtype=np.float64)

    # 미리 OSM 노드 id 매핑
    osm_nodes: Dict[int, int] = {}
    for idx in node_idxs:
        lat, lon = idx_to_coord[idx]
        # nearest_nodes에 (x, y) = (lon, lat) 전달
        osm_nodes[idx] = ox.distance.nearest_nodes(G, lon, lat)

    for i in node_idxs:
        for j in node_idxs:
            if i == j:
                dist_mat[i, j] = 0.0
                continue
            try:
                path = ox.shortest_path(G, osm_nodes[i], osm_nodes[j], weight="length")
                if path is None:
                    dist_mat[i, j] = 1e9
                else:
                    length = 0.0
                    for k in range(len(path) - 1):
                        data = G.get_edge_data(path[k], path[k + 1], 0)
                        length += float(data.get("length", 0.0))
                    dist_mat[i, j] = length
            except Exception as e:
                # 경로 실패 시 큰 값
                print(f"[WARN] shortest_path fail {i}->{j}: {e}")
                dist_mat[i, j] = 1e9

    return dist_mat
