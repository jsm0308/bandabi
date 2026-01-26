# visualize_map.py

from typing import Dict, Tuple, List
import folium
import osmnx as ox
import pandas as pd


def draw_osm_segment(
    G,
    origin: Tuple[float, float],
    dest: Tuple[float, float],
    fmap_or_fg,
    color="red",
    weight=4,
    opacity=0.8,
    tooltip_text="",
):
    o_lat, o_lon = origin
    d_lat, d_lon = dest
    try:
        o_node = ox.distance.nearest_nodes(G, o_lon, o_lat)
        d_node = ox.distance.nearest_nodes(G, d_lon, d_lat)
        path = ox.shortest_path(G, o_node, d_node, weight="length")
        if path is None:
            raise RuntimeError("no path")
        coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]
        folium.PolyLine(
            coords, color=color, weight=weight, opacity=opacity, tooltip=tooltip_text
        ).add_to(fmap_or_fg)
    except Exception as e:
        # fallback: 직선
        folium.PolyLine(
            [origin, dest],
            color=color,
            weight=2,
            opacity=0.5,
            dash_array="5,5",
            tooltip=f"(straight) {tooltip_text}",
        ).add_to(fmap_or_fg)


def make_bandabi_map(
    G,
    centers: pd.DataFrame,
    demand_df: pd.DataFrame,
    routes: List[Dict],
    output_html: str,
):
    """
    routes: 리스트
      각 원소: {
        "center_name": str,
        "arrival_slot": str,
        "bus_type": "GEN"/"WC",
        "bus_id": int,
        "route": [node_idx...],
        "idx_to_coord": {idx: (lat, lon)}
      }
    """
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=11, tiles="cartodb positron")

    # 센터 마커
    for _, row in centers.iterrows():
        folium.Marker(
            [row.lat, row.lon],
            tooltip=row.center_name,
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(m)

    # 승객 핀
    for _, r in demand_df.iterrows():
        color = "green" if r.bus_type == "GEN" else "purple"
        folium.CircleMarker(
            [r.lat, r.lon],
            radius=4,
            color=color,
            fill=True,
            fill_opacity=0.6,
            tooltip=f"{r.req_id} | {r.center_name} | {r.arrival_slot} | {r.bus_type}{r.bus_id}",
        ).add_to(m)

    # 버스 경로
    for rinfo in routes:
        cname = rinfo["center_name"]
        slot = rinfo["arrival_slot"]
        btype = rinfo["bus_type"]
        bid = rinfo["bus_id"]
        route = rinfo["route"]
        idx_to_coord = rinfo["idx_to_coord"]

        color = "#1f77b4" if btype == "GEN" else "#9467bd"
        tooltip = f"{cname} | {slot} | {btype}{bid}"

        for i in range(len(route) - 1):
            a = route[i]
            b = route[i + 1]
            coord_a = idx_to_coord[a]
            coord_b = idx_to_coord[b]
            draw_osm_segment(
                G,
                coord_a,
                coord_b,
                m,
                color=color,
                weight=5,
                opacity=0.9,
                tooltip_text=tooltip,
            )

    m.save(output_html)
    print(f"[MAP] saved to {output_html}")
    return m
