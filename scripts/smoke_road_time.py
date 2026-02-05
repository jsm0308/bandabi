from bandabi.road_network import RoadGraphSpec, load_or_build_seoul_graph, ensure_base_speeds, apply_speed_profile
from bandabi.routing.road_router import RoadRouter

def main():
    spec = RoadGraphSpec(place="Seoul, South Korea", cache_dir="data/cache/osmnx", graphml_name="seoul_drive.graphml")
    G = load_or_build_seoul_graph(spec, force_download=False)

    speed_map = {
        "motorway":80, "trunk":60, "primary":50, "secondary":45, "tertiary":40,
        "residential":25, "service":15, "unclassified":30, "road":30, "unknown":25
    }
    ensure_base_speeds(G, speed_kph_by_highway=speed_map, fallback_speed_kph=25.0, prefer_maxspeed=False)

    router = RoadRouter(G)

    # 강남역 -> 시청역 대충 좌표(스모크용)
    a_lat, a_lon = 37.4979, 127.0276
    b_lat, b_lon = 37.5665, 126.9780

    for mult in [0.8, 1.0, 1.2]:
        apply_speed_profile(G, global_multiplier=mult)
        tmin = router.travel_time_min(a_lat, a_lon, b_lat, b_lon)
        dkm  = router.distance_km(a_lat, a_lon, b_lat, b_lon)
        print(f"mult={mult:.1f}  dist_km={dkm:.2f}  time_min={tmin:.2f}")

if __name__ == "__main__":
    main()
