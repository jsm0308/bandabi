import pandas as pd

from config import (
    CENTERS_CSV,
    DUMMY_CFG,
    GEN_CAPACITY,
    WC_CAPACITY,
    MAX_GEN_PER_SLOT,
    MAX_WC_PER_SLOT,
    OSM_PLACE,
    MAP_HTML,
)
from dummy_generator import generate_dummy_requests
from clustering import assign_bus_clusters
from graph_and_distance import (
    build_osm_graph,
    build_cluster_nodes,
    compute_distance_matrix_osm,
)
from routing import hybrid_route
from visualize_map import make_bandabi_map


def main():
    # 1. 센터 로딩
    print(f"DEBUG: CENTERS_CSV path in main.py: {CENTERS_CSV}")
    centers = pd.read_excel(CENTERS_CSV)
    centers = centers.rename(columns={
        "FCLTY_NM": "center_name",
        "FCLTY_CRDNT_LA": "lat",
        "FCLTY_CRDNT_LO": "lon",
    })
    # 2. 더미 승객 생성
    demand_df = generate_dummy_requests(centers, DUMMY_CFG)

    # 3. 클러스터링 (버스 배정)
    demand_df = assign_bus_clusters(
        demand_df,
        centers,
        gen_capacity=GEN_CAPACITY,
        wc_capacity=WC_CAPACITY,
        max_gen_per_slot=MAX_GEN_PER_SLOT,
        max_wc_per_slot=MAX_WC_PER_SLOT,
    )

    print("[INFO] demand head:")
    print(demand_df.head())

    # 4. OSM 그래프 로딩
    G = build_osm_graph(OSM_PLACE)

    # 5. 클러스터별 라우팅
    routes_for_map = []
    group_cols = ["center_name", "arrival_slot", "bus_type", "bus_id"]

    for key, g_idx in demand_df.groupby(group_cols).groups.items():
        cname, slot, btype, bid = key
        sub = demand_df.loc[g_idx].reset_index(drop=True)

        if len(sub) == 0:
            continue

        print(f"[CLUSTER] {cname} | {slot} | {btype}{bid} | n={len(sub)}")

        # 5-1. 노드 구성
        nodes_df, idx_to_coord = build_cluster_nodes(
            centers, demand_df, cname, slot, btype, bid
        )

        # 5-2. 거리행렬 계산
        dist_mat = compute_distance_matrix_osm(G, idx_to_coord)

        # 5-3. 고객 노드 리스트
        customer_nodes = [int(i) for i in nodes_df["node_idx"].tolist() if i != 0]

        # 5-4. 하이브리드 라우팅
        best_route = hybrid_route(customer_nodes, dist_mat)
        print("  route:", best_route)

        routes_for_map.append(
            {
                "center_name": cname,
                "arrival_slot": slot,
                "bus_type": btype,
                "bus_id": int(bid),
                "route": best_route,
                "idx_to_coord": idx_to_coord,
            }
        )

    # 6. 지도 시각화
    _ = make_bandabi_map(G, centers, demand_df, routes_for_map, MAP_HTML)


if __name__ == "__main__":
    main()
