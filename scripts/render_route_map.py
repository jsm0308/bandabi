"""Render an interactive map for a run variant.

Why this exists
- You want to *see* the output route to trust it.
- This script generates (or regenerates) `map_data.json` + `map.html` inside a variant folder.

Usage
  python scripts/render_route_map.py --exp <exp_id> --variant <variant_id>
  python scripts/render_route_map.py --variant-dir runs/<exp_id>/<variant_id>

Notes
- The map uses Leaflet + OpenStreetMap tiles.
- It draws straight-line polylines between stops (because this project is not using a road graph yet).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd


def _render_leaflet_html(map_data: Dict[str, Any]) -> str:
    vehicles = map_data.get("vehicles") or []
    all_pts: List[Tuple[float, float]] = []
    for v in vehicles:
        for lat, lon in v.get("coords", []):
            try:
                all_pts.append((float(lat), float(lon)))
            except Exception:
                continue

    if all_pts:
        lat0 = sum(p[0] for p in all_pts) / len(all_pts)
        lon0 = sum(p[1] for p in all_pts) / len(all_pts)
    else:
        lat0, lon0 = 37.5665, 126.9780  # Seoul fallback

    payload = json.dumps(map_data, ensure_ascii=False)

    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Bandabi Route Map</title>
    <link
      rel=\"stylesheet\"
      href=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.css\"
      integrity=\"sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=\"
      crossorigin=\"\"
    />
    <style>
      html, body, #map {{ height: 100%; margin: 0; }}
      .legend {{ position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.65); color: #fff; padding: 10px 12px; font: 12px/1.4 system-ui; border-radius: 10px; max-width: 360px; }}
      .legend code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
    </style>
  </head>
  <body>
    <div id=\"map\"></div>
    <div class=\"legend\">
      <div><strong>Bandabi Route Map</strong></div>
      <div style=\"opacity:.85\">Straight-line polyline (not road graph)</div>
      <div style=\"margin-top:6px\">vehicles: <code>{{len(vehicles)}}</code></div>
    </div>
    <script
      src=\"https://unpkg.com/leaflet@1.9.4/dist/leaflet.js\"
      integrity=\"sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=\"
      crossorigin=\"\"
    ></script>
    <script>
      const MAP_DATA = {payload};
      const map = L.map('map').setView([{lat0}, {lon0}], 12);
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      }}).addTo(map);

      const colors = ['#00d0ff', '#00ffa2', '#ffd000', '#ff5c8a', '#a66bff', '#ffffff'];
      const bounds = [];

      (MAP_DATA.vehicles || []).forEach((v, idx) => {{
        const coords = (v.coords || []).map(p => [p[0], p[1]]);
        if (!coords.length) return;
        const color = colors[idx % colors.length];
        const line = L.polyline(coords, {{ color, weight: 4, opacity: 0.85 }}).addTo(map);
        line.bindTooltip(v.vehicle_id || `vehicle_${{idx}}`, {{ sticky: true }});
        coords.forEach((p, i) => {{
          const icon = i === 0 ? '🏁' : (i === coords.length - 1 ? '✅' : '📍');
          L.circleMarker(p, {{ radius: 5, weight: 1, opacity: 0.9, fillOpacity: 0.7 }}).addTo(map)
            .bindPopup(`${{icon}} ${{v.vehicle_id}}<br/>stop_seq=${{i}}`);
          bounds.push(p);
        }});
      }});

      if (bounds.length) {{
        map.fitBounds(bounds, {{ padding: [30, 30] }});
      }}
    </script>
  </body>
</html>"""


def _build_map_data_from_events(routes_csv: Path, events_csv: Path) -> Dict[str, Any]:
    if not routes_csv.exists() or not events_csv.exists():
        raise FileNotFoundError("routes.csv and events.csv are required")

    routes = pd.read_csv(routes_csv)
    events = pd.read_csv(events_csv)

    required_cols = {"vehicle_id", "stop_seq", "pickup_lat", "pickup_lon", "center_lat", "center_lon"}
    if not required_cols.issubset(set(events.columns)):
        missing = sorted(list(required_cols - set(events.columns)))
        raise ValueError(
            "events.csv is missing columns needed for map rendering: " + ", ".join(missing)
        )

    vehicles = []
    for vehicle_id, g in events.groupby("vehicle_id"):
        g = g.sort_values("stop_seq")
        center_lat = float(g.iloc[0]["center_lat"])
        center_lon = float(g.iloc[0]["center_lon"])
        coords = [[center_lat, center_lon]]
        for _, r in g.iterrows():
            coords.append([float(r["pickup_lat"]), float(r["pickup_lon"])])
        coords.append([center_lat, center_lon])

        row = routes.loc[routes["vehicle_id"] == vehicle_id].iloc[0] if "vehicle_id" in routes.columns and (routes["vehicle_id"] == vehicle_id).any() else None
        vehicles.append(
            {
                "vehicle_id": str(vehicle_id),
                "center_id": int(row["center_id"]) if row is not None and "center_id" in row else None,
                "timeslot": str(row["timeslot"]) if row is not None and "timeslot" in row else None,
                "bus_type": str(row["bus_type"]) if row is not None and "bus_type" in row else None,
                "coords": coords,
            }
        )

    return {"vehicles": vehicles}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--variant-dir", type=str, default=None, help="Path to a variant folder (runs/<exp>/<variant>)")
    p.add_argument("--exp", type=str, default=None, help="Experiment id under runs/")
    p.add_argument("--variant", type=str, default=None, help="Variant folder name under runs/<exp>/")
    p.add_argument("--run-root", type=str, default="runs", help="Runs root directory")
    args = p.parse_args()

    if args.variant_dir:
        vdir = Path(args.variant_dir)
    else:
        if not args.exp or not args.variant:
            raise SystemExit("Provide either --variant-dir OR both --exp and --variant")
        vdir = Path(args.run_root) / args.exp / args.variant

    if not vdir.exists():
        raise SystemExit(f"Variant dir not found: {vdir}")

    map_json = vdir / "map_data.json"
    map_html = vdir / "map.html"

    if map_json.exists():
        map_data = json.loads(map_json.read_text(encoding="utf-8"))
    else:
        # Try to reconstruct from events/routes (requires the new columns).
        map_data = _build_map_data_from_events(vdir / "routes.csv", vdir / "events.csv")

    map_json.write_text(json.dumps(map_data, ensure_ascii=False, indent=2), encoding="utf-8")
    map_html.write_text(_render_leaflet_html(map_data), encoding="utf-8")

    print(f"OK: wrote {map_json}")
    print(f"OK: wrote {map_html}")


if __name__ == "__main__":
    main()
