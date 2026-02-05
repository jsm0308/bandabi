from __future__ import annotations
from pathlib import Path

import osmnx as ox

def main():
    out = Path("data/cache/osmnx/seoul_drive.graphml")
    out.parent.mkdir(parents=True, exist_ok=True)

    print("[1/2] Downloading OSM graph for Seoul...")
    G = ox.graph_from_place("Seoul, South Korea", network_type="drive")

    print("[2/2] Saving graphml...")
    ox.save_graphml(G, out)
    print(f"[DONE] {out}")

if __name__ == "__main__":
    main()
