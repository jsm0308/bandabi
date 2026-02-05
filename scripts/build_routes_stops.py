from __future__ import annotations

import argparse
import json
from pathlib import Path
import pandas as pd


def build_routes_stops_for_variant(variant_dir: Path) -> Path:
    routes_csv = variant_dir / "routes.csv"
    out_csv = variant_dir / "routes_stops.csv"

    if out_csv.exists():
        return out_csv  # 이미 있으면 스킵(원하면 --overwrite로 바꿀 수 있게 확장 가능)

    if not routes_csv.exists():
        raise FileNotFoundError(routes_csv)

    df = pd.read_csv(routes_csv)
    if df.empty or "stops_json" not in df.columns:
        raise RuntimeError(f"{routes_csv} must contain stops_json")

    rows = []
    for _, r in df.iterrows():
        vehicle_id = str(r.get("vehicle_id", ""))
        center_id = r.get("center_id", None)
        timeslot = str(r.get("timeslot", ""))
        bus_type = str(r.get("bus_type", ""))

        stops = json.loads(r.get("stops_json", "[]") or "[]")
        for st in stops:
            rows.append(
                {
                    "vehicle_id": vehicle_id,
                    "center_id": int(center_id) if pd.notna(center_id) else None,
                    "timeslot": timeslot,
                    "bus_type": bus_type,
                    "stop_seq": int(st.get("stop_seq", -1)),
                    "node_idx": int(st.get("node_idx", -1)),
                    "stop_type": str(st.get("kind", "")),  # depot/pickup/center
                    "lat": float(st.get("lat")) if st.get("lat") is not None else None,
                    "lon": float(st.get("lon")) if st.get("lon") is not None else None,
                }
            )

    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values(["vehicle_id", "stop_seq"])

    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    return out_csv


def iter_experiments(runs_dir: Path, prefix: str | None) -> list[Path]:
    exps = [p for p in runs_dir.iterdir() if p.is_dir() and not p.name.startswith("_")]
    if prefix:
        exps = [p for p in exps if p.name.startswith(prefix)]
    return sorted(exps)


def iter_variants(exp_dir: Path) -> list[Path]:
    return sorted([p for p in exp_dir.iterdir() if p.is_dir() and p.name.startswith("v_")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-dir", default="runs")
    ap.add_argument("--exp-tag", default="", help="특정 exp만 돌리고 싶으면 지정. 비우면 여러 exp 처리.")
    ap.add_argument("--prefix", default="base18__", help="exp-tag 비었을 때 처리할 exp 폴더 prefix. 예: base18__")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir)
    if not runs_dir.exists():
        raise FileNotFoundError(runs_dir)

    if args.exp_tag:
        exp_dirs = [runs_dir / args.exp_tag]
    else:
        exp_dirs = iter_experiments(runs_dir, args.prefix if args.prefix else None)

    total_variants = 0
    total_written = 0

    for exp_dir in exp_dirs:
        if not exp_dir.exists():
            continue
        vdirs = iter_variants(exp_dir)
        if not vdirs:
            continue

        for vdir in vdirs:
            total_variants += 1
            try:
                out = build_routes_stops_for_variant(vdir)
                print(f"[ok] {out}")
                total_written += 1
            except Exception as e:
                print(f"[skip] {vdir} ({e})")

    print(f"[done] variants processed={total_variants}, routes_stops written={total_written}")


if __name__ == "__main__":
    main()
